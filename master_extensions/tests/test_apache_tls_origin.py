import runpy
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2] / "infra/runtime"
A = runpy.run_path(str(ROOT / "hoosh-apache-config"))
P = runpy.run_path(str(ROOT / "hoosh-engine-provision"))

class ApacheTLSOriginTests(unittest.TestCase):
    def test_explicit_mode_only(self):
        normal = A["render"]("tenant", "site.example")["httpd.conf"]
        tls = A["render"]("tenant", "site.example", True)["httpd.conf"]
        self.assertNotIn("ProxyFCGISetEnvIf", normal)
        self.assertIn('ProxyFCGISetEnvIf "true" HTTPS "on"', tls)
        self.assertIn('ProxyFCGISetEnvIf "true" SERVER_PORT "443"', tls)
        self.assertIn("RequestHeader unset X-Forwarded-Proto", tls)
        self.assertNotIn('req("X-Forwarded-Proto")', tls)

    def test_renderer_injection(self):
        for name, domain in (("x;id", "site.example"), ("tenant", "x.test\nListen 443")):
            with self.assertRaises(ValueError):
                A["render"](name, domain, True)

    def test_apply_uses_explicit_origin_mode(self):
        events=[]
        record={"engine":"apache","account":"tenant","domain":"site.example","tls_origin":True,"persistent":False,"state":"pending"}
        with patch.dict(P["apply"].__globals__,{"save":lambda *a:None,"run":lambda *a,**k:events.append(a),"health":lambda *a:None}):
            P["apply"](Path("/unused"),record)
        self.assertEqual(events[0],("/usr/local/libexec/hoosh-apache-config","prepare","tenant","site.example","--tls-origin"))
