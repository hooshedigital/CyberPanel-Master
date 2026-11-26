import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "infra/runtime"
M = runpy.run_path(str(ROOT / "hoosh-gateway-config"))

class GatewayTests(unittest.TestCase):
    def test_strict_tls_and_headers(self):
        s=M["render"]("apache","tenant","site.example")
        self.assertIn("listen unix:/run/hoosh-gateway-tenant/https.sock ssl;",s)
        self.assertIn("ssl_protocols TLSv1.2 TLSv1.3;",s)
        self.assertIn('if ($ssl_server_name != "site.example")',s)
        self.assertIn('if ($host != "site.example")',s)
        self.assertIn("proxy_pass_request_headers off;",s)
        self.assertIn("proxy_set_header X-Forwarded-Proto https;",s)
        self.assertNotIn("$http_x_forwarded",s)
        self.assertNotIn("listen 443",s)
        self.assertIn("proxy_cache off;",s)

    def test_invalid_inputs(self):
        for e,a,d in (("bad","tenant","x.test"),("apache","root","x.test"),("apache","x;id","x.test"),("frankenphp","tenant","x.test;listen"),("apache","tenant","127.0.0.1")):
            with self.assertRaises(ValueError):
                M["render"](e,a,d)

    def test_service_is_private(self):
        s=(ROOT/"hoosh-web-gateway@.service").read_text()
        self.assertIn("User=hoosh-web-edge",s)
        self.assertIn("RuntimeDirectoryMode=0700",s)
        self.assertIn("PrivateNetwork=yes",s)
        self.assertIn("RestrictAddressFamilies=AF_UNIX",s)
        self.assertNotIn("[Install]",s)
