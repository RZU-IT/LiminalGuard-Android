"""Opt-in network check. Uses loopback and leaves system DNS unchanged."""
import threading

from liminalguard.checks import check_server
from liminalguard.server import Server
from liminalguard.upstream import AdGuardDNS


server = Server("127.0.0.1", 0, AdGuardDNS(), allow_loopback=True)
server.bind()
thread = threading.Thread(target=server.serve)
thread.start()
try:
    check_server(server.host, server.port)
    print("PASS: real AdGuard HTTPS, normal DNS over UDP/TCP, blocked control domain")
finally:
    server.close()
    thread.join(2)
