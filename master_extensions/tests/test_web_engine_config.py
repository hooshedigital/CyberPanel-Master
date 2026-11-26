import hashlib
import json
import unittest
from master_extensions.web_engine_config import render, Tenant

ROOT = "/var/tmp/hoosh-engine-render-fixture"
A = Tenant("a.tenant.test", 1, 62001)
B = Tenant("b.tenant.test", 2, 62002, "balanced")


class ConfigTests(unittest.TestCase):
    def plan(self, tenants=(A, B), **kw):
        return render(ROOT, tenants, role="admin", **kw)

    def test_reproducible(self):
        a = self.plan()
        self.assertEqual(a, self.plan((B, A)))
        m = a["manifest"]
        for p, data in a["files"].items():
            self.assertEqual(m["sha256"][p], hashlib.sha256(data.encode()).hexdigest())
        self.assertEqual(a["manifest_sha256"], hashlib.sha256(json.dumps(
            m, sort_keys=True, separators=(",", ":")).encode()).hexdigest())

    def test_stage_only(self):
        m = self.plan()["manifest"]
        self.assertTrue(m["staging_only"])
        for k in ("execution_authorized", "production_changes", "public_cache_enabled",
                  "private_cache_enabled", "htaccess_enabled"):
            self.assertFalse(m[k])

    def test_role_and_paths(self):
        with self.assertRaises(PermissionError):
            render(ROOT, [A], role="customer")
        for root in ("/usr/local/lsws", ROOT+"/../x", ROOT+"\nListen 0.0.0.0:80", ROOT+"/"):
            with self.subTest(root=root), self.assertRaises(ValueError):
                render(root, [A], role="admin")

    def test_domain_conflicts(self):
        for tenants in ((A, Tenant("A.TENANT.TEST", 2, 62002)),
                        (A, Tenant("b.tenant.test", 1, 62002)),
                        (A, Tenant("b.tenant.test", 2, 62001))):
            with self.assertRaises(ValueError):
                self.plan(tenants)
        with self.assertRaises(ValueError):
            self.plan(used_domains=["A.tenant.test"])
        with self.assertRaises(ValueError):
            self.plan(used_uids=[62001])

    def test_bad_inputs(self):
        for t in (Tenant("live.example.com",1,62001), Tenant("a.test\nx",1,62001),
                  Tenant("a.test",True,62001), Tenant("a.test",1,0),
                  Tenant("a.test",1,62001,"performance"), Tenant("a.test",1,62001,[])):
            with self.subTest(t=t), self.assertRaises(ValueError):
                self.plan([t])

    def test_isolated_socket_and_routes(self):
        f = self.plan()["files"]
        a = f["httpd.conf"]
        self.assertIn("Listen 127.0.0.1:18883", a)
        self.assertIn("ServerName rejected.test", a)
        self.assertIn("Require all denied", a)
        self.assertIn("ProxyRequests Off", a)
        self.assertNotIn("AllowOverride FileInfo", a)
        self.assertIn("Options -Indexes -FollowSymLinks -SymLinksIfOwnerMatch", a)
        for i in (1,2):
            s = f"{ROOT}/tenant{i}/run/php.sock"
            self.assertIn("proxy:unix:"+s, a)
            self.assertIn("listen = "+s, f[f"tenant{i}/fpm.conf"])
            self.assertIn("security.limit_extensions = .php", f[f"tenant{i}/fpm.conf"])
            self.assertIn("clear_env = yes", f[f"tenant{i}/fpm.conf"])
        self.assertIn("pm.max_children = 1", f["tenant1/fpm.conf"])
        self.assertIn("pm.max_children = 2", f["tenant2/fpm.conf"])
        self.assertIn("address 127.0.0.1:18884", f["ols/conf/httpd_config.conf"])
        self.assertIn("map tenant1 a.tenant.test", f["ols/conf/httpd_config.conf"])
        self.assertIn("map tenant2 b.tenant.test", f["ols/conf/httpd_config.conf"])

    def test_bound(self):
        for tenants in ([], [A,B,A], [{"domain":"a.test"}]):
            with self.assertRaises(ValueError):
                self.plan(tenants)


if __name__ == "__main__":
    unittest.main()
