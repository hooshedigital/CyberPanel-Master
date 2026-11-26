import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
M = runpy.run_path(str(ROOT / "infra/runtime/hoosh-engine-provision"))
G = M["apply"].__globals__


class ProvisionTests(unittest.TestCase):
    def test_validation(self):
        M["validate"]("apache", "test-account", "example.test")
        M["validate"]("frankenphp", "account2", "a.example.test")
        for engine, user, domain in (
            ("native", "account", "example.test"),
            ("apache", "root", "example.test"),
            ("apache", "../a", "example.test"),
            ("frankenphp", "a", "bad.test\nHost: injected"),
            ("frankenphp", "a", "127.0.0.1"),
            ("apache", "a", "x.test:80"),
            ("apache", "a", "X.test"),
        ):
            with self.subTest(domain=domain), self.assertRaises(ValueError):
                M["validate"](engine, user, domain)

    def test_fixed_layout(self):
        a = M["layout"]("apache", "sample")
        f = M["layout"]("frankenphp", "sample")
        self.assertEqual(a["units"][0], "hoosh-apache-http@sample.socket")
        self.assertEqual(f["units"][0], "hoosh-frankenphp@sample.service")
        self.assertEqual(str(a["public"]), "/srv/hoosh-apache/sample/public")
        self.assertEqual(f["socket"], "/run/hoosh-frankenphp-sample/http.sock")

    def test_apply_success_order(self):
        events = []
        r = {"engine": "apache", "account": "sample", "domain": "example.test",
             "persistent": True, "state": "pending"}
        with patch.dict(G, {
            "save": lambda p, record: events.append(("journal", record["state"])),
            "run": lambda *a, **k: events.append(a),
            "health": lambda record: events.append(("health",)),
        }):
            M["apply"](Path("/unused"), r)
        self.assertEqual(events[0], ("journal", "pending"))
        self.assertEqual(events[1][0], "/usr/local/libexec/hoosh-apache-config")
        self.assertEqual(events[2][1], "start")
        self.assertEqual(events[3], ("health",))
        self.assertEqual(events[4][1], "add-wants")
        self.assertEqual(events[5], ("journal", "active"))

    def test_apply_failure_rolls_back(self):
        events = []
        r = {"engine": "apache", "account": "sample", "domain": "example.test",
             "persistent": False, "state": "pending"}
        def fail(record):
            raise ValueError("health")
        with patch.dict(G, {
            "save": lambda p, record: events.append("journal"),
            "run": lambda *a, **k: events.append(a[0]),
            "health": fail,
            "rollback": lambda p, record: events.append("rollback"),
        }):
            with self.assertRaises(ValueError):
                M["apply"](Path("/unused"), r)
        self.assertEqual(events[-1], "rollback")
        self.assertEqual(r["state"], "pending")

    @unittest.skipUnless(os.geteuid() == 0, "root-owned file test")
    def test_symlink_hardlink_and_writable_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "file"
            p.write_text("ok")
            p.chmod(0o644)
            M["trusted_file"](p)
            link = Path(tmp) / "link"
            link.symlink_to(p)
            with self.assertRaises(ValueError):
                M["trusted_file"](link)
            link.unlink()
            os.link(p, link)
            with self.assertRaises(ValueError):
                M["trusted_file"](p)
            link.unlink()
            p.chmod(0o666)
            with self.assertRaises(ValueError):
                M["trusted_file"](p)


    def test_mountinfo_and_same_device_bind(self):
        points = M["mount_points"](
            "29 1 8:1 / / rw - ext4 /dev/root rw\n"
            "30 29 8:1 /elsewhere /srv/hoosh-apache/sample/public/a\\040b rw - ext4 /dev/root rw\n"
        )
        self.assertIn(Path("/srv/hoosh-apache/sample/public/a b"), points)
        with self.assertRaises(ValueError):
            M["reject_project_mounts"](Path("/srv/hoosh-apache/sample/public"), points)
        M["reject_project_mounts"](Path("/srv/hoosh-apache/other/public"), points)

    def test_health_ignores_user_curl_configuration(self):
        calls = []
        def run(*args, **kwargs):
            calls.append(args)
            return M["MARKER"]
        with patch.dict(G, {"run": run}):
            M["health"]({"engine": "apache", "account": "sample", "domain": "example.test"})
        argv = calls[0]
        self.assertEqual(argv[:5], ("/usr/sbin/runuser", "-u", "sample", "--", "/usr/bin/env"))
        self.assertIn("-i", argv)
        self.assertEqual(argv[argv.index("/usr/bin/curl") + 1], "--disable")
        self.assertIn("=http", argv)
