import unittest
from winiso_toolkit.iso.analyzer import WIMImageInfo, parse_wiminfo_output


class TestAnalyzer(unittest.TestCase):
    def test_parse_wiminfo_output(self) -> None:
        sample_wiminfo = """
Index: 1
Name: Windows 11 Pro
Description: Windows 11 Pro Edition
Total Bytes: 5368709120

Index: 2
Name: Windows 11 Home
Description: Windows 11 Home Edition
Total Bytes: 4831838208
"""
        images = parse_wiminfo_output(sample_wiminfo, 10000000000)
        self.assertEqual(len(images), 2)
        self.assertEqual(images[0].index, 1)
        self.assertEqual(images[0].name, "Windows 11 Pro")
        self.assertEqual(images[0].size_bytes, 5368709120)
        self.assertEqual(images[1].index, 2)
        self.assertEqual(images[1].name, "Windows 11 Home")
