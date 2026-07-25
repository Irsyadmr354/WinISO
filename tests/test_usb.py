import unittest
from winiso_toolkit.usb.creator import USBCreator
from winiso_toolkit.usb.detector import USBDevice, parse_size


class TestUSB(unittest.TestCase):
    def test_parse_size_units(self) -> None:
        self.assertEqual(parse_size("14.9G"), int(14.9 * (1024**3)))
        self.assertEqual(parse_size("512M"), 512 * (1024**2))
        self.assertEqual(parse_size("1000K"), 1000 * 1024)

    def test_validate_capacity(self) -> None:
        creator = USBCreator()
        ok, msg = creator.validate_capacity(16 * (1024**3), 5 * (1024**3))
        self.assertTrue(ok)
        self.assertEqual(msg, "")

        ok, msg = creator.validate_capacity(4 * (1024**3), 6 * (1024**3))
        self.assertFalse(ok)
        self.assertIn("Your USB is 4.0 GB", msg)
