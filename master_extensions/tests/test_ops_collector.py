"""No privileged system access required; filesystem fixtures are temporary."""
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from master_extensions import ops_collector


class OperationsCollectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def _write(self, relative, size=8192, old_days=None):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"x" * size)
        if old_days is not None:
            old = time.time() - old_days * 86400
            os.utime(path, (old, old))
        return path

    def test_root_stats_and_disjoint_categories(self):
        site = self._write("home/www/site.txt", 8192)
        backup = self._write("home/backup/important.sql", 16384)
        # No symlink traversal; hardlinks counted once within their category.
        os.symlink(backup, self.root / "home" / "www" / "external-link")
        os.link(site, self.root / "home" / "www" / "duplicate-hardlink")
        result = ops_collector.collect_disk(
            roots={"websites": (str(self.root / "home"),),
                   "backups": (str(self.root / "home" / "backup"),)},
            mounts=set())
        self.assertEqual(result["schema"], 1)
        self.assertGreater(result["total_bytes"], result["available_bytes"])
        self.assertEqual(result["coverage"], "sampled")
        self.assertEqual(result["categories"]["websites"],
                         site.stat().st_blocks * 512)
        self.assertEqual(result["categories"]["backups"],
                         backup.stat().st_blocks * 512)
        self.assertTrue(result["category_scans"]["websites"]["complete"])
        self.assertNotIn(str(backup), str(result))
        self.assertNotIn(str(site), str(result))

    def test_mount_boundary_and_missing_mountinfo_are_fail_closed(self):
        mount_file = self._write("home/excluded/volume.txt")
        self._write("home/regular.txt")
        result = ops_collector.collect_disk(
            roots={"websites": (str(self.root / "home"),)},
            mounts={str(mount_file.parent)})
        self.assertEqual(result["categories"]["websites"],
                         (self.root / "home/regular.txt").stat().st_blocks * 512)
        with patch.object(ops_collector, "_mountpoints", return_value=None):
            missing = ops_collector.collect_disk(
                roots={"websites": (str(self.root / "home"),)})
        self.assertEqual(missing["categories"], {})

    def test_entry_budget_marks_category_incomplete(self):
        self._write("home/a.bin")
        self._write("home/b.bin")
        with patch.object(ops_collector, "MAX_ENTRIES_PER_ROOT", 1):
            result = ops_collector.collect_disk(
                roots={"websites": (str(self.root / "home"),)}, mounts=set())
        self.assertFalse(result["category_scans"]["websites"]["complete"])

    def test_cleanup_reports_estimates_not_paths_or_commands(self):
        deb = self._write("apt/pkg.deb", 12000, old_days=5)
        self._write("apt/lock", 24000, old_days=5)
        archived = self._write("journal/system@abc.journal", 8000, old_days=40)
        self._write("journal/system.journal", 8000, old_days=40)
        old = self._write("tmp/old.tmp", 5000, old_days=40)
        self._write("tmp/recent.tmp", 5000, old_days=1)
        out = ops_collector.collect_cleanup(
            paths={
                "apt_download_cache": (str(self.root / "apt"), ".deb", 1, False),
                "journal_archives": (str(self.root / "journal"), None, 30, True),
                "old_temp_files": (str(self.root / "tmp"), None, 30, False),
            }, mounts=set())
        candidates = {item["kind"]: item for item in out["candidates"]}
        self.assertEqual(candidates["apt_download_cache"]["reclaimable_bytes"],
                         deb.stat().st_blocks * 512)
        self.assertEqual(candidates["journal_archives"]["reclaimable_bytes"],
                         archived.stat().st_blocks * 512)
        self.assertEqual(candidates["old_temp_files"]["reclaimable_bytes"],
                         old.stat().st_blocks * 512)
        self.assertTrue(out["analysis_complete"])
        self.assertNotIn(str(self.root), str(out))
        self.assertNotIn("command", str(out))
        self.assertTrue(all(x["estimate_only"] for x in candidates.values()))

    def test_no_symlink_candidate_and_no_uploads(self):
        external = self._write("private/key.deb", 8192, old_days=90)
        (self.root / "apt").mkdir()
        os.symlink(external, self.root / "apt" / "fake.deb")
        result = ops_collector.collect_cleanup(
            paths={"apt_download_cache": (str(self.root / "apt"), ".deb", 1, False)},
            mounts=set())
        self.assertEqual(result["candidates"], [])

    def test_untrusted_roots_cannot_be_scanned_as_arbitrary_categories(self):
        self._write("home/x.txt")
        result = ops_collector.collect_disk(
            roots={"secrets": (str(self.root / "home"),)}, mounts=set())
        self.assertEqual(result["categories"], {})


if __name__ == "__main__":
    unittest.main()
