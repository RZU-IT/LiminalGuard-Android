import contextlib
import errno
import io
import sys
import unittest
from unittest.mock import patch

from liminalguard.__main__ import main


class CliTests(unittest.TestCase):
    def invoke(self, error):
        out, err = io.StringIO(), io.StringIO()
        with patch.object(sys, "argv", ["liminalguard", "--ip", "192.168.1.25"]), \
             patch("liminalguard.__main__.Server.bind", side_effect=error), \
             contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            result = main()
        return result, out.getvalue(), err.getvalue()

    def test_permission_denied_never_announces_ready(self):
        result, out, err = self.invoke(PermissionError(errno.EACCES, "denied"))
        self.assertEqual(result, 1)
        self.assertNotIn("Identifiant du téléphone", out)
        self.assertNotIn("100%", out)
        self.assertIn("Android refuse", err)

    def test_busy_port_never_announces_ready(self):
        result, out, err = self.invoke(OSError(errno.EADDRINUSE, "busy"))
        self.assertEqual(result, 1)
        self.assertNotIn("Identifiant du téléphone", out)
        self.assertIn("déjà utilisé", err)

    def test_public_bind_address_rejected(self):
        with patch.object(sys, "argv", ["liminalguard", "--ip", "8.8.8.8"]), \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(), 1)

    def test_failed_health_check_never_announces_ready(self):
        with patch.object(sys, "argv", ["liminalguard", "--check", "--ip", "192.168.1.25"]), \
             patch("liminalguard.__main__.check_server", side_effect=ValueError("offline")), \
             contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(), 1)
        self.assertNotIn("Identifiant du téléphone", out.getvalue())
        self.assertNotIn("100%", out.getvalue())

    def test_check_displays_identity_without_starting_a_service(self):
        with patch.object(sys, "argv", ["liminalguard", "--check"]), \
             patch("liminalguard.__main__.detect_ip", return_value=("192.168.1.25", "wifi")), \
             patch("liminalguard.__main__.check_server"), \
             patch("liminalguard.__main__.Server") as factory, \
             contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(), 0)
        factory.assert_not_called()
        text = out.getvalue()
        self.assertIn("Identifiant du téléphone : 192.168.1.25", text)
        self.assertIn("100%", text)
        self.assertNotIn("Filtrage actif", text)
        self.assertNotIn("console", text)

    def test_startup_and_interrupt_cleanup(self):
        from test_dns import upstream
        from liminalguard.server import Server
        from liminalguard.checks import check_server
        server = Server("127.0.0.1", 0, upstream, allow_loopback=True)
        def check(host, port, progress=None):
            check_server(server.host, server.port, progress=progress)
        with patch.object(sys, "argv", ["liminalguard", "--ip", "192.168.1.25"]), \
             patch("liminalguard.__main__.Server", return_value=server), \
             patch("liminalguard.__main__.check_server", side_effect=check), \
             patch("liminalguard.__main__.shutil.which", return_value=None), \
             patch("liminalguard.__main__.wait_for_shutdown", side_effect=KeyboardInterrupt), \
             contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(), 0)
        self.assertIn("Identifiant du téléphone : 192.168.1.25", out.getvalue())
        self.assertIn("Relais arrêté", out.getvalue())
        self.assertEqual(server.udp.fileno(), -1)
        self.assertEqual(server.tcp.fileno(), -1)
