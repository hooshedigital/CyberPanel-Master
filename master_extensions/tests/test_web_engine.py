import unittest
from pathlib import Path
import runpy
from master_extensions.web_engine import preview, Resources, REQUIRED

ROOT = Path(__file__).resolve().parents[2]
R = Resources(1800, 1500, 12000, 20, 1)
READY = {key: True for keys in REQUIRED.values() for key in keys}
READY.update(public_cache_verified=True, object_cache_verified=True)


class EngineTests(unittest.TestCase):
    def plan(self, **kw):
        return preview({"domain": "example.test", **kw}, role="admin",
                       resources=R, readiness=READY)

    def test_native(self):
        p = self.plan()
        self.assertEqual(p["engine"], "ols-native")
        self.assertEqual(p["status"], "eligible_for_staging_review")
        self.assertFalse(p["execution_authorized"])
        self.assertFalse(p["production_changes"])

    def test_hybrid_requires_readiness(self):
        self.assertEqual(self.plan(engine="ols-apache")["additional_memory_envelope_mib"], 384)
        p = preview({"domain": "example.test", "engine": "ols-apache"}, role="admin",
                    resources=R, readiness={})
        self.assertEqual(p["status"], "blocked")
        self.assertIn("php_isolation_verified", p["blockers"])

    def test_resource_limits(self):
        p = preview({"domain": "example.test", "engine": "ols-apache"}, role="admin",
                    resources=Resources(1300, 800, 7000, 60, 10), readiness=READY)
        self.assertEqual(set(p["blockers"]), {"ram_headroom", "swap_headroom",
                                            "disk_headroom", "cpu_pressure", "memory_pressure"})

    def test_role(self):
        with self.assertRaises(PermissionError):
            preview({"domain": "example.test"}, role="customer", resources=R, readiness=READY)

    def test_domain_injection(self):
        for domain in ["x.test\nListen 0.0.0.0:80", "../x.test", "x.test:80",
                       "https://x.test", "127.0.0.1", "x..test", "-x.test", "İ.test"]:
            with self.subTest(domain=domain), self.assertRaises(ValueError):
                self.plan(domain=domain)

    def test_invalid_inputs(self):
        for data in [{"engine": []}, {"profile": "turbo"}, {"public_cache": "true"},
                     {"readiness": READY}, {"role": "admin"}, {"command": "test"}]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                self.plan(**data)

    def test_cache(self):
        self.assertIn("public_cache_compatibility",
                      self.plan(engine="ols-apache", public_cache=True)["blockers"])
        self.assertFalse(self.plan(public_cache=True)["private_cache_enabled"])
        p = preview({"domain": "example.test", "object_cache": True}, role="admin",
                    resources=R, readiness={})
        self.assertIn("object_cache_integration", p["blockers"])

    def test_nan(self):
        with self.assertRaises(ValueError):
            preview({"domain": "example.test"}, role="admin",
                    resources=Resources(1800, 1500, 12000, float("nan"), 1), readiness=READY)


class OverlayTests(unittest.TestCase):
    def test_preserves_original(self):
        ns = runpy.run_path(str(ROOT / "scripts/stage_web_engine_form.py"))
        original = ns["ANCHOR"] + "\n{% if test_domain_data %}premium{% endif %}"
        fragment = ns["FRAGMENT"].read_text()
        result = ns["overlay"](original, fragment)
        self.assertEqual(result.replace(fragment + "\n", ""), original)
        self.assertNotIn("ng-model", fragment)
        self.assertNotIn('name="', fragment)
        self.assertEqual(fragment.count("disabled"), 4)
        with self.assertRaises(ValueError):
            ns["overlay"](result, fragment)

    def test_anchor_mismatch(self):
        ns = runpy.run_path(str(ROOT / "scripts/stage_web_engine_form.py"))
        for s in ["nothing", ns["ANCHOR"] * 2]:
            with self.assertRaises(ValueError):
                ns["overlay"](s, ns["FRAGMENT"].read_text())


if __name__ == "__main__":
    unittest.main()
