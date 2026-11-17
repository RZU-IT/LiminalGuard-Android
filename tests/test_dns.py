import socket
import struct
import threading
import unittest
from unittest.mock import patch

from liminalguard.checks import check_server
from liminalguard.dns import addresses, question, response, validate_query, validate_reply
from liminalguard.server import Server, local_address, receive_exact


def query(name="example.org", identifier=123):
    name = b"".join(bytes([len(label)]) + label.encode() for label in name.split(".")) + b"\0"
    return struct.pack("!HHHHHH", identifier, 0x100, 1, 0, 0, 0) + name + struct.pack("!HH", 1, 1)


def answer(packet, address=b"\x5d\xb8\xd8\x22", padding=0):
    base = bytearray(response(packet, code=0))
    struct.pack_into("!H", base, 6, 1)
    return bytes(base) + b"\xc0\x0c" + struct.pack("!HHIH", 1, 1, 60, 4) + address + bytes(padding)


def upstream(packet):
    name = question(packet)[0][0]
    return answer(packet, bytes(4) if name == (b"ad", b"doubleclick", b"net") else b"\x5d\xb8\xd8\x22")


class PacketTests(unittest.TestCase):
    def test_question_and_reply(self):
        packet = query()
        self.assertEqual(validate_query(packet)[0], ((b"example", b"org"), 1, 1))
        self.assertEqual(addresses(validate_reply(packet, answer(packet))), [b"\x5d\xb8\xd8\x22"])

    def test_malformed_queries(self):
        for packet in (b"", bytes(12), query()[:-1], query() + bytes(4096),
                       struct.pack("!HHHHHH", 1, 0, 1, 0, 0, 0) + b"\xc0\x0c\0\1\0\1"):
            with self.subTest(size=len(packet)), self.assertRaises(ValueError):
                validate_query(packet)

    def test_rejects_response_as_query(self):
        with self.assertRaises(ValueError):
            validate_query(answer(query()))

    def test_rejects_mismatched_id_or_question(self):
        for reply in (answer(query(identifier=44)), answer(query("other.org")), query()):
            with self.assertRaises(ValueError):
                validate_reply(query(), reply)

    def test_truncated_response_has_no_answer(self):
        packet = response(query(), code=0, truncated=True)
        self.assertTrue(packet[2] & 2)
        self.assertEqual(addresses(packet), [])

    def test_truncated_record_rejected(self):
        with self.assertRaises(ValueError):
            addresses(answer(query())[:-1])

    def test_private_ipv4_only(self):
        for address in ("192.168.1.2", "10.0.0.3", "172.16.1.2"):
            self.assertTrue(local_address(address))
        for address in ("0.0.0.0", "127.0.0.1", "8.8.8.8", "::1", "169.254.1.1"):
            self.assertFalse(local_address(address))


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.server = Server("127.0.0.1", 0, upstream, allow_loopback=True)
        self.server.bind()
        self.errors = []
        def serve():
            try:
                self.server.serve()
            except BaseException as error:
                self.errors.append(error)
        self.thread = threading.Thread(target=serve)
        self.thread.start()

    def tearDown(self):
        self.server.close()
        self.thread.join(2)
        self.assertFalse(self.thread.is_alive())
        self.assertEqual(self.errors, [])

    def udp(self, packet):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
            client.settimeout(2)
            client.sendto(packet, (self.server.host, self.server.port))
            return client.recv(65535)

    def tcp(self, packet):
        with socket.create_connection((self.server.host, self.server.port), timeout=2) as client:
            data = struct.pack("!H", len(packet)) + packet
            client.sendall(data[:1])
            client.sendall(data[1:])
            length = struct.unpack("!H", receive_exact(client, 2))[0]
            return receive_exact(client, length)

    def test_udp_and_tcp_answers(self):
        for send in (self.udp, self.tcp):
            self.assertEqual(addresses(send(query())), [b"\x5d\xb8\xd8\x22"])

    def test_blocked_domain(self):
        self.assertEqual(addresses(self.udp(query("ad.doubleclick.net"))), [bytes(4)])

    def test_local_health_check(self):
        check_server(self.server.host, self.server.port)

    def test_upstream_failure_returns_servfail(self):
        def fail(packet):
            raise OSError("offline")
        self.server.upstream = fail
        self.assertEqual(self.udp(query())[3] & 15, 2)

    def test_mismatched_upstream_reply_returns_servfail(self):
        self.server.upstream = lambda packet: answer(query(identifier=100))
        self.assertEqual(self.tcp(query())[3] & 15, 2)

    def test_udp_large_reply_is_truncated(self):
        self.server.upstream = lambda packet: answer(packet, padding=600)
        reply = self.udp(query())
        self.assertTrue(reply[2] & 2)
        self.assertLessEqual(len(reply), 512)

    def test_port_conflict_cleans_up(self):
        other = Server(self.server.host, self.server.port, upstream, allow_loopback=True)
        with self.assertRaises(OSError):
            other.bind()

    def test_public_client_refused(self):
        self.assertFalse(self.server.permitted("8.8.8.8"))

    def test_rate_limit(self):
        with patch("liminalguard.server.time.monotonic", return_value=100):
            self.assertTrue(all(self.server.permitted("192.168.1.3") for _ in range(30)))
            self.assertFalse(self.server.permitted("192.168.1.3"))


if __name__ == "__main__":
    unittest.main()
