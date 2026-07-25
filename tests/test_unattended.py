import unittest
from winiso_toolkit.iso.unattended import BypassOptions, UnattendedGenerator


class TestUnattended(unittest.TestCase):
    def test_unattended_default_xml(self) -> None:
        generator = UnattendedGenerator()
        xml = generator.generate_xml()
        self.assertIn('xmlns="urn:schemas-microsoft-com:unattend"', xml)
        self.assertIn('BypassTPMCheck', xml)
        self.assertIn('BypassSecureBootCheck', xml)
        self.assertIn('BypassRAMCheck', xml)
        self.assertIn('BypassCPUCheck', xml)
        self.assertIn('BypassNRO', xml)

    def test_unattended_custom_user(self) -> None:
        opts = BypassOptions(username="AdminTech", computer_name="Custom-PC", bypass_tpm=False)
        generator = UnattendedGenerator(opts)
        xml = generator.generate_xml()
        self.assertIn("<Name>AdminTech</Name>", xml)
        self.assertIn("<ComputerName>Custom-PC</ComputerName>", xml)
        self.assertNotIn("BypassTPMCheck", xml)
