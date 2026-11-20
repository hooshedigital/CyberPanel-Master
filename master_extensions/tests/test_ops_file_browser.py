"""Future SFTP-like explorer: confinement contract with no live HTTP route."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from master_extensions import ops_file_browser as fb


class FileBrowserTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.roots = {"scope": str(self.root)}
        self.mounts = patch.object(fb, "_mountpoints", return_value=set())
        self.mounts.start()
        self.addCleanup(self.mounts.stop)

    def test_sorted_paginated_metadata_with_explicit_readonly(self):
        (self.root / "b.txt").write_bytes(b"abc")
        (self.root / "a.txt").write_bytes(b"abcd")
        (self.root / "c.txt").write_bytes(b"abcde")
        page1 = fb.list_directory("scope", page_size=2, roots=self.roots)
        self.assertEqual([i["name"] for i in page1["items"]], ["a.txt", "b.txt"])
        self.assertEqual(page1["next_after"], "b.txt")
        self.assertTrue(page1["read_only"])
        self.assertEqual(page1["items"][0]["size_bytes"], 4)
        page2 = fb.list_directory("scope", after=page1["next_after"],
                                  page_size=2, roots=self.roots)
        self.assertEqual([i["name"] for i in page2["items"]], ["c.txt"])
        self.assertIsNone(page2["next_after"])

    def test_rejects_absolute_traversal_and_unknown_root(self):
        for path in ("../private", "/etc", "a/../b", "a//b",
                     "a/./b", "a\\b", "a/\x00b", "a/\nb"):
            with self.subTest(path=repr(path)):
                with self.assertRaises(fb.FileBrowserError):
                    fb.list_directory("scope", path, roots=self.roots)
        with self.assertRaises(fb.FileBrowserError):
            fb.list_directory("etc", roots=self.roots)
        with self.assertRaises(fb.FileBrowserError):
            fb.list_directory("scope", page_size=True, roots=self.roots)

    def test_symlink_is_visible_but_never_navigable(self):
        (self.root / "inside").mkdir()
        os.symlink("/etc", self.root / "shortcut")
        items = fb.list_directory("scope", roots=self.roots)["items"]
        shortcut = next(item for item in items if item["name"] == "shortcut")
        self.assertEqual(shortcut["kind"], "symlink")
        self.assertFalse(shortcut["navigable"])
        with self.assertRaises(fb.FileBrowserError):
            fb.list_directory("scope", "shortcut", roots=self.roots)

    def test_nested_mount_is_blocked_even_on_same_device(self):
        nested = self.root / "bound"
        nested.mkdir()
        with patch.object(fb, "_mountpoints", return_value={str(nested)}):
            with self.assertRaises(fb.FileBrowserError):
                fb.list_directory("scope", "bound", roots=self.roots)

    def test_directory_listing_budget_marks_incomplete(self):
        for name in ("a", "b", "c"):
            (self.root / name).write_text(name)
        with patch.object(fb, "MAX_ITEMS_SCANNED", 1):
            result = fb.list_directory("scope", page_size=1, roots=self.roots)
        self.assertTrue(result["incomplete"])
        self.assertIsNone(result["next_after"])

    def test_missing_mount_information_fails_closed(self):
        with patch.object(fb, "_mountpoints", return_value=None):
            with self.assertRaises(fb.FileBrowserError):
                fb.list_directory("scope", roots=self.roots)


if __name__ == "__main__":
    unittest.main()
