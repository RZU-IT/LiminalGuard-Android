import concurrent.futures
import ipaddress
import select
import socket
import struct
import threading
import time

from .dns import MAX_QUERY, response, validate_query, validate_reply

NETWORKS = tuple(ipaddress.ip_network(value) for value in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"))


def local_address(value, loopback=False):
    try:
        address = ipaddress.IPv4Address(value)
        return any(address in net for net in NETWORKS) or (loopback and address.is_loopback)
    except ipaddress.AddressValueError:
        return False


def receive_exact(connection, length):
    result = bytearray()
    while len(result) < length:
        part = connection.recv(length - len(result))
        if not part:
            raise EOFError
        result.extend(part)
    return bytes(result)


class Server:
    def __init__(self, host, port, upstream, allow_loopback=False, workers=12):
        if not local_address(host, allow_loopback):
            raise ValueError("Choose the phone's private Wi-Fi IPv4 address")
        self.upstream = upstream
        self.host, self.port = host, port
        self.allow_loopback = allow_loopback
        self.stopped = threading.Event()
        self.slots = threading.BoundedSemaphore(workers)
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=workers)
        self.counts = {"answered": 0, "failed": 0, "dropped": 0}
        self.lock = threading.Lock()
        self.rates = {}
        self.udp = self.tcp = None

    def bind(self):
        try:
            self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp.bind((self.host, self.port))
            self.port = self.udp.getsockname()[1]
            self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp.bind((self.host, self.port))
            self.tcp.listen(16)
        except BaseException:
            self.close()
            raise

    def permitted(self, peer):
        if not local_address(peer, self.allow_loopback):
            return False
        now = int(time.monotonic())
        previous, count = self.rates.get(peer, (now, 0))
        self.rates = {key: item for key, item in self.rates.items() if item[0] == now}
        if previous != now:
            count = 0
        if len(self.rates) >= 256 and peer not in self.rates:
            return False
        self.rates[peer] = (now, count + 1)
        return count < 30

    def increment(self, key):
        with self.lock:
            self.counts[key] += 1

    def resolve(self, query):
        validate_query(query)
        try:
            reply = validate_reply(query, self.upstream(query))
            self.increment("answered")
            return reply
        except Exception:
            self.increment("failed")
            return response(query)

    def submit(self, function, *args):
        if not self.slots.acquire(blocking=False):
            self.increment("dropped")
            return False
        def run():
            try:
                function(*args)
            finally:
                self.slots.release()
        self.pool.submit(run)
        return True

    def udp_query(self, query, peer):
        try:
            reply = self.resolve(query)
            if len(reply) > 512:
                reply = response(query, code=0, truncated=True)
            self.udp.sendto(reply, peer)
        except (OSError, ValueError):
            self.increment("dropped")

    def tcp_query(self, connection):
        with connection:
            connection.settimeout(3)
            try:
                size = struct.unpack("!H", receive_exact(connection, 2))[0]
                if size < 12 or size > MAX_QUERY:
                    return
                reply = self.resolve(receive_exact(connection, size))
                connection.sendall(struct.pack("!H", len(reply)) + reply)
            except (OSError, EOFError, ValueError):
                self.increment("dropped")

    def serve(self):
        while not self.stopped.is_set():
            try:
                ready, _, _ = select.select([self.udp, self.tcp], [], [], 0.3)
            except (OSError, ValueError):
                if self.stopped.is_set():
                    return
                raise
            for listener in ready:
                if listener is self.udp:
                    try:
                        query, peer = self.udp.recvfrom(MAX_QUERY + 1)
                    except OSError:
                        if self.stopped.is_set():
                            return
                        raise
                    if self.permitted(peer[0]):
                        self.submit(self.udp_query, query, peer)
                    else:
                        self.increment("dropped")
                else:
                    try:
                        connection, peer = self.tcp.accept()
                    except OSError:
                        if self.stopped.is_set():
                            return
                        raise
                    if not self.permitted(peer[0]) or not self.submit(self.tcp_query, connection):
                        connection.close()

    def close(self):
        self.stopped.set()
        for listener in (self.udp, self.tcp):
            if listener:
                listener.close()
        self.pool.shutdown(wait=True)
