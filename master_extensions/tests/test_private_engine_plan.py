import unittest
from master_extensions.web_engine_plan import plan


class PrivatePlanTests(unittest.TestCase):
    def test_plan_no_execution(self):
        p = plan("frankenphp", "sample", "example.test", True, capacity_ok=True)
        self.assertFalse(p["execution_authorized"])
        self.assertFalse(p["public_routing"])
        self.assertEqual(p["state"], "review_required")
        self.assertEqual(p["project_root"], "/srv/hoosh-frankenphp/sample/public")
        self.assertTrue(p["owner_preflight"].endswith("--persistent"))

    def test_reject_injection(self):
        for engine, user, domain, boot in (
            ("native", "sample", "example.test", False),
            ("apache", "root", "example.test", False),
            ("apache", "cyberpanel", "example.test", False),
            ("apache", "a;id", "example.test", False),
            ("apache", "sample", "x.test;id", False),
            ("apache", "sample", "https://x.test", False),
            ("apache", "sample", "127.0.0.1", False),
            ("apache", "sample", "x.test", "true"),
        ):
            with self.subTest(domain=domain), self.assertRaises(ValueError):
                plan(engine, user, domain, boot, capacity_ok=True)

    def test_unknown_capacity_fail_closed(self):
        self.assertFalse(plan("apache", "sample", "example.test", False, capacity_ok=None)["capacity_ok"])
