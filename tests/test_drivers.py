import tempfile
import unittest
from pathlib import Path
from winiso_toolkit.iso.drivers import DriverInjector


class TestDrivers(unittest.TestCase):
    def test_find_driver_files(self) -> None:
        injector = DriverInjector()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "net").mkdir()
            (tmp_path / "net" / "wifi.inf").write_text("[Version]\nSignature=$Windows NT$")
            (tmp_path / "storage.INF").write_text("[Version]\nSignature=$Windows NT$")

            infs = injector.find_driver_files(tmp_path)
            self.assertEqual(len(infs), 2)
            names = [f.name.lower() for f in infs]
            self.assertIn("wifi.inf", names)
            self.assertIn("storage.inf", names)
