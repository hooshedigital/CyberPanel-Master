import unittest
from master_extensions.ops_overview import disk_overview, cleanup_candidates, agent_overview


class OperationsOverviewTests(unittest.TestCase):
    def test_disk_valid_summary_and_category_allowlist(self):
        data = disk_overview({"schema": 1, "total_bytes": 100_000_000_000,
                              "used_bytes": 92_000_000_000, "available_bytes": 7_400_000_000,
                              "categories": {"backups": 10_000_000_000,
                                             "secret_path": 5000000000}})
        self.assertTrue(data["verified"])
        self.assertEqual(data["used_pct"], 92)
        self.assertEqual(data["categories"], [{"key": "backups", "size_gb": 10}])
        self.assertNotIn("secret_path", str(data))

    def test_disk_rejects_invalid_types_and_inconsistent_bytes(self):
        for data in ({"schema": 1, "total_bytes": True, "used_bytes": 0, "available_bytes": 0},
                     {"schema": 1, "total_bytes": 10, "used_bytes": 20, "available_bytes": 0},
                     {"schema": 2, "total_bytes": 10, "used_bytes": 5, "available_bytes": 5},
                     {"schema": 1, "total_bytes": 10, "used_bytes": -1, "available_bytes": 1}):
            self.assertFalse(disk_overview(data)["verified"])

    def test_cleanup_is_dry_run_and_deduplicated(self):
        result = cleanup_candidates({"schema": 1, "candidates": [
            {"kind": "apt_download_cache", "reclaimable_bytes": 2500000000,
             "path": "/etc/shadow", "command": "rm -rf /"},
            {"kind": "apt_download_cache", "reclaimable_bytes": 3000000000},
            {"kind": "docker_volumes", "reclaimable_bytes": 99999999999},
            {"kind": "application_cache", "reclaimable_bytes": -1},
            {"kind": ["apt_download_cache"], "reclaimable_bytes": 3000},
        ]})
        self.assertEqual(result, [{"kind": "apt_download_cache",
                                   "reclaimable_gb": 2.5, "requires_review": True}])
        self.assertNotIn("/etc/shadow", str(result))
        self.assertNotIn("rm -rf", str(result))

    def test_agent_status_filters_raw_commands(self):
        result = agent_overview({"schema": 1, "state": "waiting_approval",
                                 "pending": 2, "completed": 8, "failed": 0,
                                 "command": "sudo su", "token": "SECRET"})
        self.assertEqual(result["state"], "waiting_approval")
        self.assertEqual(result["pending"], 2)
        self.assertNotIn("SECRET", str(result))
        self.assertFalse(agent_overview({"schema": 1, "state": "root"})["verified"])
