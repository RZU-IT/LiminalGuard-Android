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
        self.assertNotIn("DNS de votre console", out)
        self.assertIn("Android refuse", err)

    def test_busy_port_never_announces_ready(self):
        result, out, err = self.invoke(OSError(errno.EADDRINUSE, "busy"))
        self.assertEqual(result, 1)
        self.assertNotIn("DNS de votre console", out)
        self.assertIn("déjà utilisé", err)

    def test_public_bind_address_rejected(self):
        with patch.object(sys, "argv", ["liminalguard", "--ip", "8.8.8.8"]), \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(), 1)
