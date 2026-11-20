"""Offline security and behavior tests for the operations center."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from master_extensions.cleanup_preview import CleanupPolicy, preview, snapshot as cleanup_snapshot
from master_extensions.operations_center import (
    _read_bounded_json, agent_summary, breakdown, cleanup_summary,
    disk_summary, operations_context,
)
from master_extensions.storage_probe import scan_tree, snapshot as storage_snapshot
from master_extensions.workspace_browser import browse, valid_relative
from master_extensions.i18n import LABELS


NOW = datetime(2026, 11, 20, 17, 0, tzinfo=timezone.utc)


class OperationsContracts(unittest.TestCase):
    def test_disk_metrics_not_invented(self):
        g = 1024 ** 3
        got = disk_summary(SimpleNamespace(total=100 * g, used=92 * g, free=8 * g))
        self.assertEqual(got["used_percent"], 92)
        self.assertEqual(got["free_gib"], 8)
        self.assertFalse(disk_summary(SimpleNamespace(total=0, used=0, free=0))["ready"])

    def test_storage_freshness_limits_and_partial_scan(self):
        data = {"schema": 1, "generated_utc": NOW.isoformat(),
                "groups": [{"category": "cache", "allocated_bytes": 2 * 1024 ** 3, "complete": False},
                           {"category": "logs", "allocated_bytes": 1024 ** 3, "complete": True}]}
        result = breakdown("fa", report=data, now=NOW)
        self.assertTrue(result["ready"])
        self.assertTrue(result["partial"])
        self.assertEqual(result["groups"][0]["name"], "کش‌ها")
        self.assertEqual(result["groups"][0]["size_gib"], 2)
        self.assertFalse(breakdown("en", report=data, now=NOW + timedelta(hours=1))["ready"])

    def test_invalid_or_untrusted_storage_entries_ignored(self):
        report = {"schema": 1, "generated_utc": NOW.isoformat(),
                  "groups": [
                      {"category": "../../etc", "allocated_bytes": 1, "complete": True},
                      {"category": "logs", "allocated_bytes": -7, "complete": True},
                      {"category": "cache", "allocated_bytes": 4, "complete": "yes"},
                      {"category": "backup", "allocated_bytes": 9, "complete": True},
                  ]}
        result = breakdown("en", report=report, now=NOW)
        self.assertEqual([x["id"] for x in result["groups"]], ["backup"])

    def test_actual_agent_0_9_timestamp_contract(self):
        report = {"updated_at_unix": NOW.timestamp(), "version": "0.9.0",
                  "status": "warning", "checks_total": 6, "production_service_changes": 0}
        good = agent_summary(report=report, now=NOW)
        self.assertTrue(good["fresh"])
        self.assertEqual(good["version"], "0.9.0")
        self.assertEqual(good["checks_total"], 6)
        self.assertFalse(good["operations_enabled"])
        bad = agent_summary(report=report, now=NOW + timedelta(minutes=9))
        self.assertFalse(bad["fresh"])
        self.assertIsNone(bad["version"])

    def test_agent_status_never_claims_execution_from_malformed_report(self):
        result = agent_summary(report={"updated_at_unix": NOW.timestamp(),
                                       "version": "<img src=x>", "status": "root",
                                       "checks_total": 999999}, now=NOW)
        self.assertTrue(result["fresh"])
        self.assertIsNone(result["version"])
        self.assertIsNone(result["status"])
        self.assertIsNone(result["checks_total"])
        self.assertFalse(result["operations_enabled"])

    def test_cleanup_preview_contract_only_valid_categories(self):
        inp = {"schema": 1, "generated_utc": NOW.isoformat(), "items": [
            {"category": "apt_archives", "allocated_bytes": 1024 ** 3, "count": 2},
            {"category": "docker_volumes", "allocated_bytes": 200, "count": 99},
            {"category": "hoosh_temp", "allocated_bytes": 0, "count": 0},
        ]}
        got = cleanup_summary(report=inp, now=NOW)
        self.assertEqual([x["id"] for x in got["items"]], ["apt_archives", "hoosh_temp"])
        self.assertEqual(got["total_gib"], 1)
        self.assertFalse(cleanup_summary(report=inp, now=NOW + timedelta(days=2))["ready"])

    def test_reports_are_bounded_no_symlink_reads(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "secret.json"
            target.write_text('{"secret":"private"}')
            link = root / "report.json"
            link.symlink_to(target)
            self.assertEqual(_read_bounded_json(link), {})
            regular = root / "regular.json"
            regular.write_text('{"schema":1}')
            self.assertEqual(_read_bounded_json(regular)["schema"], 1)
            regular.write_bytes(b"x" * 70000)
            self.assertEqual(_read_bounded_json(regular), {})

    def test_workspace_path_validation(self):
        for bad in ["../passwd", "/etc", "a//b", "./a", "a/../b", "a\\b",
                    "a/../../root", "x" * 400]:
            self.assertIsNone(valid_relative(bad))
        self.assertEqual(valid_relative("f1/f2"), ["f1", "f2"])

    def test_workspace_browser_cannot_follow_symlinks(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base) / "managed"
            root.mkdir()
            (root / "safe").mkdir()
            (root / "safe" / "note.txt").write_text("hello")
            (root / "outside").symlink_to("/etc")
            top = browse(root=root)
            self.assertTrue(top["ready"])
            self.assertEqual(next(x for x in top["items"] if x["name"] == "outside")["kind"], "blocked")
            self.assertFalse(browse("outside", root=root)["ready"])
            self.assertFalse(browse("../", root=root)["ready"])
            inner = browse("safe", root=root)
            self.assertEqual(inner["items"][0]["kind"], "file")
            self.assertEqual(inner["parent"], "")

    def test_scan_tree_never_follows_symlink_and_marks_partial(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            (root / "a.bin").write_bytes(b"x" * 5000)
            (root / "secret_link").symlink_to("/etc")
            (root / "sub").mkdir()
            (root / "sub" / "b.bin").write_bytes(b"y" * 2000)
            complete = scan_tree(root, max_entries=1000, max_seconds=10)
            self.assertTrue(complete["complete"])
            self.assertGreaterEqual(complete["allocated_bytes"], 0)
            partial = scan_tree(root, max_entries=1, max_seconds=10)
            self.assertFalse(partial["complete"])

    def test_scanner_snapshot_is_non_destructive_and_structured(self):
        report = storage_snapshot(roots=[("cache", "/nonexistent")],
                                  scan=lambda _: {"allocated_bytes": 34, "complete": False}, now=NOW)
        self.assertEqual(report["schema"], 1)
        self.assertFalse(report["groups"][0]["complete"])
        self.assertNotIn("path", report["groups"][0])

    def test_cleanup_scan_only_candidates_and_no_removal(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            old = root / "old.deb"
            old.write_bytes(b"a" * 5000)
            fresh = root / "new.deb"
            fresh.write_bytes(b"a" * 5000)
            unrelated = root / "database.sqlite"
            unrelated.write_bytes(b"a" * 3000)
            (root / "linked.deb").symlink_to(old)
            old_epoch = NOW.timestamp() - 40 * 86400
            os.utime(old, (old_epoch, old_epoch))
            policy = CleanupPolicy("apt_archives", root, ".deb", 30)
            result = preview(policy, now_epoch=NOW.timestamp())
            self.assertEqual(result["count"], 1)
            self.assertFalse(result["deleted"])
            self.assertEqual(unrelated.stat().st_size, 3000)
            self.assertEqual(fresh.stat().st_size, 5000)
            self.assertTrue(old.exists())
            self.assertFalse(cleanup_snapshot(policies=[policy], now=NOW,
                               scan=lambda _: result)["execution_enabled"])

    def test_language_parity_and_template_scoping(self):
        self.assertEqual(set(LABELS["en"]), set(LABELS["fa"]))
        for key in ("storage_heading", "cleanup_heading", "workspace_heading", "agent_ops_heading"):
            self.assertNotEqual(LABELS["en"][key], LABELS["fa"][key])
        template = (Path(__file__).resolve().parents[2] / "master_extensions" /
                    "templates" / "backup" / "cyberpanel_master.html").read_text()
        for section in ('id="linux-storage"', 'id="safe-cleanup"',
                        'id="managed-files"', 'id="agent-operations"'):
            self.assertIn(section, template)
        self.assertNotIn("sudo ", template)
        self.assertNotIn("rm -rf", template)
        self.assertNotIn("<script", template)


if __name__ == "__main__":
    unittest.main()
