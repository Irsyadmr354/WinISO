import unittest
from winiso_toolkit.iso.verifier import ISOVerifier, KNOWN_OFFICIAL_HASHES


class TestVerifier(unittest.TestCase):
    def test_known_hashes(self) -> None:
        verifier = ISOVerifier()
        # Verify Windows 11 23H2 hash match logic
        hash_23h2 = "9c788600183141b7d14d8ed1702e5a60e060014b2d35eb18080f589886a11e03"
        self.assertIn(hash_23h2, KNOWN_OFFICIAL_HASHES)
        self.assertEqual(KNOWN_OFFICIAL_HASHES[hash_23h2], "Windows 11 23H2 (x64) English")
