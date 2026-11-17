import socket
import struct

from .server import local_address


def wifi_ip():
    try:
        import fcntl
    except ImportError:
        return None
    # Android can deny netlink enumeration; query known Wi-Fi interfaces directly.
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
        for interface in (b"wlan0", b"wlan1", b"wifi0"):
            try:
                result = fcntl.ioctl(connection.fileno(), 0x8915, struct.pack("256s", interface))
                address = socket.inet_ntoa(result[20:24])
                if local_address(address):
                    return address
            except OSError:
                continue
    return None


def route_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
        connection.connect(("1.1.1.1", 443))
        return connection.getsockname()[0]


def detect_ip():
    address = wifi_ip()
    if address:
        return address, "wifi"
    address = route_ip()
    if not local_address(address):
        raise ValueError("Aucune adresse locale utilisable. Connectez le téléphone au Wi-Fi.")
    return address, "route"
