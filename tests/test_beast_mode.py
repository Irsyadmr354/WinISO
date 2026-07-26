import tempfile
import unittest
from pathlib import Path

from winiso_toolkit.iso.debloat import DebloatOptions, WIMDebloater
from winiso_toolkit.iso.pebuilder import WinPERescueBuilder
from winiso_toolkit.iso.scraper import MicrosoftISOScraper
from winiso_toolkit.iso.updates import UpdateSlipstreamer


class TestBeastMode(unittest.TestCase):
    def test_debloat_script_generation(self) -> None:
        opts = DebloatOptions(remove_appx=True, disable_onedrive=True)
        debloater = WIMDebloater(opts)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            script = debloater.generate_debloat_script(tmp_path)
            self.assertTrue(script.is_file())
            content = script.read_text(encoding="utf-8")
            self.assertIn("Microsoft.BingNews", content)
            self.assertIn("OneDrive", content)

    def test_update_scanner(self) -> None:
        slipstreamer = UpdateSlipstreamer()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "KB12345.msu").write_text("dummy update")
            (tmp_path / "KB67890.cab").write_text("dummy update")
            pkgs = slipstreamer.find_update_packages(tmp_path)
            self.assertEqual(len(pkgs), 2)

    def test_scraper_releases(self) -> None:
        scraper = MicrosoftISOScraper()
        releases = scraper.list_available_releases()
        self.assertGreaterEqual(len(releases), 2)
        self.assertIn("Windows 11", releases[0].name)

    def test_pe_rescue_builder(self) -> None:
        builder = WinPERescueBuilder()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            ok = builder.build_rescue_media(tmp_path)
            self.assertTrue(ok)
            rescue = tmp_path / "WinISO_Rescue_Tools"
            self.assertTrue((rescue / "README_RESCUE.txt").is_file())
            self.assertTrue((rescue / "START_RESCUE.cmd").is_file())
            self.assertTrue((rescue / "tools_manifest.json").is_file())
            self.assertTrue((rescue / "Tools" / "7-Zip" / "Launch_7-Zip.cmd").is_file())
            self.assertTrue((tmp_path / "sources" / "winiso_rescue_launcher.cmd").is_file())
