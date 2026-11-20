import json
import os
from pathlib import Path
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from master_extensions import ops_telemetry as tm


class RootOwnedTelemetryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.name = "cleanup-candidates.json"
        self.patch_dir = patch.object(tm, "ROOT_DIR", self.root)
        self.patch_uid = patch.object(tm, "EXPECTED_UID", os.getuid())
        self.patch_dir.start()
        self.patch_uid.start()
        self.addCleanup(self.patch_dir.stop)
        self.addCleanup(self.patch_uid.stop)

    def _report(self, stamp=None):
        obj = {"schema": 1,
               "generated_utc": stamp or datetime.now(timezone.utc).isoformat(),
               "candidates": [{"kind": "apt_download_cache",
                               "reclaimable_bytes": 1000}]}
        path = self.root / self.name
        path.write_text(json.dumps(obj))
        path.chmod(0o644)
        return path

    def test_accepts_fresh_valid_owned_json(self):
        self._report()
        self.assertEqual(tm.read_fresh_report(self.name)["schema"], 1)

    def test_rejects_stale_future_and_invalid_names(self):
        self._report((datetime.now(timezone.utc) - timedelta(hours=2)).isoformat())
        self.assertEqual(tm.read_fresh_report(self.name), {})
        self._report((datetime.now(timezone.utc) + timedelta(hours=2)).isoformat())
        self.assertEqual(tm.read_fresh_report(self.name), {})
        self.assertEqual(tm.read_fresh_report("../secrets"), {})
        self.assertEqual(tm.read_fresh_report("server-agent-status.json"), {})

    def test_rejects_symlink_file_and_directory(self):
        file = self._report()
        (self.root / self.name).unlink()
        target = self.root / "private.json"
        target.write_text(file.name)
        (self.root / self.name).symlink_to(target)
        self.assertEqual(tm.read_fresh_report(self.name), {})
        with tempfile.TemporaryDirectory() as other:
            with patch.object(tm, "ROOT_DIR", Path(other) / "link"):
                (Path(other) / "link").symlink_to(self.root, target_is_directory=True)
                self.assertEqual(tm.read_fresh_report(self.name), {})

    def test_rejects_world_writable_state_and_file(self):
        file = self._report()
        file.chmod(0o666)
        self.assertEqual(tm.read_fresh_report(self.name), {})
        file.chmod(0o644)
        self.root.chmod(0o777)
        try:
            self.assertEqual(tm.read_fresh_report(self.name), {})
        finally:
            self.root.chmod(0o700)

    def test_rejects_invalid_json_and_age_parameter(self):
        path = self.root / self.name
        path.write_text("{")
        self.assertEqual(tm.read_fresh_report(self.name), {})
        self._report()
        self.assertEqual(tm.read_fresh_report(self.name, max_age=True), {})

    def test_smart_backup_view_uses_safe_reader_and_sanitized_candidates(self):
        source = (Path(__file__).resolve().parents[1] / "integration" /
                  "hoosh_smart_bilingual.py").read_text()
        self.assertIn('read_fresh_report("cleanup-candidates.json"', source)
        self.assertIn("cleanup_candidates(cleanup_report)", source)
        self.assertNotIn("os.remove(", source)
        self.assertNotIn("shutil.rmtree(", source)


if __name__ == "__main__":
    unittest.main()
