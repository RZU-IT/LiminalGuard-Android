import socket
import unittest
from unittest.mock import patch

from liminalguard.network import detect_ip, wifi_ip


class NetworkTests(unittest.TestCase):
    def test_wifi_preferred_over_mobile_route(self):
        with patch("liminalguard.network.wifi_ip", return_value="192.168.1.10"), \
             patch("liminalguard.network.route_ip") as route:
            self.assertEqual(detect_ip(), ("192.168.1.10", "wifi"))
            route.assert_not_called()

    def test_fallback_is_identified_as_route(self):
        with patch("liminalguard.network.wifi_ip", return_value=None), \
             patch("liminalguard.network.route_ip", return_value="10.1.2.3"):
            self.assertEqual(detect_ip(), ("10.1.2.3", "route"))

    def test_public_route_is_not_a_phone_identity(self):
        with patch("liminalguard.network.wifi_ip", return_value=None), \
             patch("liminalguard.network.route_ip", return_value="8.8.8.8"):
            with self.assertRaises(ValueError):
                detect_ip()

    def test_missing_network_is_reported(self):
        with patch("liminalguard.network.wifi_ip", return_value=None), \
             patch("liminalguard.network.route_ip", side_effect=OSError("offline")):
            with self.assertRaises(OSError):
                detect_ip()

    @unittest.skipUnless(__import__("sys").platform.startswith("linux"), "Linux ioctl only")
    def test_ioctl_selects_the_wifi_address(self):
        data = bytes(20) + socket.inet_aton("192.168.1.4") + bytes(232)
        with patch("fcntl.ioctl", return_value=data):
            self.assertEqual(wifi_ip(), "192.168.1.4")

    @unittest.skipUnless(__import__("sys").platform.startswith("linux"), "Linux ioctl only")
    def test_ioctl_permission_denied_allows_fallback(self):
        with patch("fcntl.ioctl", side_effect=PermissionError("Android restriction")):
            self.assertIsNone(wifi_ip())
