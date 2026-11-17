import contextlib
import io
import os
import unittest
from unittest.mock import patch

from liminalguard.terminal import Terminal


class Tty(io.StringIO):
    def isatty(self):
        return True


class TerminalTests(unittest.TestCase):
    def test_redirected_output_has_no_escape_codes(self):
        stream = io.StringIO()
        terminal = Terminal(stream=stream)
        terminal.banner()
        terminal.stage(100, "Prêt")
        terminal.identity("192.168.1.25", "wifi")
        self.assertNotIn("\033", stream.getvalue())
        self.assertIn("by RZU Informatique", stream.getvalue())

    def test_no_color_respected(self):
        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            self.assertFalse(Terminal(stream=Tty()).color)

    def test_explicit_color(self):
        self.assertIn("\033[", Terminal("always", stream=io.StringIO()).paint("ready"))

    def test_phone_width(self):
        terminal = Terminal(stream=io.StringIO())
        terminal.columns = 40
        terminal.stage(65, "DNS UDP vérifié")
        self.assertLessEqual(len(terminal.render()), 40)
        self.assertNotIn("DNS UDP", terminal.render())

    def test_progress_thread_stops_and_finish_is_idempotent(self):
        terminal = Terminal("never", stream=Tty())
        terminal.start()
        terminal.stage(40, "Démarrage")
        terminal.finish()
        terminal.finish()
        self.assertFalse(terminal.thread.is_alive())

    def test_route_warning_does_not_claim_wifi_detection(self):
        stream = io.StringIO()
        Terminal(stream=stream, details=True).identity("10.1.2.3", "route")
        self.assertIn("Wi-Fi non identifié", stream.getvalue())

    def test_default_identity_has_no_technical_details(self):
        stream = io.StringIO()
        Terminal(stream=stream).identity("192.168.1.25", "route")
        self.assertEqual(stream.getvalue().strip(), "Identifiant du téléphone : 192.168.1.25")

    def test_default_redirected_progress_prints_only_completion(self):
        stream = io.StringIO()
        terminal = Terminal(stream=stream)
        terminal.stage(20, "Adresse locale détectée")
        terminal.stage(65, "DNS UDP vérifié")
        self.assertEqual(stream.getvalue(), "")
        terminal.stage(100, "Prêt")
        self.assertEqual(len(stream.getvalue().splitlines()), 1)
        self.assertNotIn("Prêt", stream.getvalue())

    def test_details_show_stage_names(self):
        stream = io.StringIO()
        Terminal(stream=stream, details=True).stage(65, "DNS UDP vérifié")
        self.assertIn("DNS UDP", stream.getvalue())

    def test_interactive_banner_clears_previous_package_output(self):
        stream = Tty()
        with patch.dict(os.environ, {"TERM": "xterm"}):
            Terminal(stream=stream).banner()
        self.assertTrue(stream.getvalue().startswith("\033[2J\033[H"))
