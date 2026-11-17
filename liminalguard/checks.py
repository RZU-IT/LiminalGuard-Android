import secrets
import socket
import struct

from .dns import addresses, validate_reply
from .server import receive_exact


def query(name):
    labels = b"".join(bytes([len(part)]) + part.encode("ascii") for part in name.split("."))
    return secrets.token_bytes(2) + struct.pack("!HHHHH", 0x0100, 1, 0, 0, 0) + labels + b"\0\0\1\0\1"


def ask(host, port, packet, tcp=False):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM if tcp else socket.SOCK_DGRAM) as connection:
        connection.settimeout(9)
        connection.connect((host, port))
        if tcp:
            connection.sendall(struct.pack("!H", len(packet)) + packet)
            size = struct.unpack("!H", receive_exact(connection, 2))[0]
            reply = receive_exact(connection, size)
        else:
            connection.send(packet)
            reply = connection.recv(65535)
    return validate_reply(packet, reply)


def check_server(host, port):
    for tcp in (False, True):
        reply = ask(host, port, query("example.org"), tcp=tcp)
        if reply[3] & 15 or not addresses(reply):
            raise ValueError("La résolution DNS normale échoue")
    reply = ask(host, port, query("ad.doubleclick.net"))
    blocked = reply[3] & 15 == 3 or (bool(addresses(reply)) and all(not any(value) for value in addresses(reply)))
    if not blocked:
        raise ValueError("Le domaine de contrôle publicitaire n'est pas bloqué")
