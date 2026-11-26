import runpy
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2] / "infra/runtime"
M = runpy.run_path(str(ROOT / "hoosh-edge-check"))
G = M["check"].__globals__

class EdgeTests(unittest.TestCase):
    def test_bad_account_or_engine(self):
        for engine, name in (("bad","tenant"),("apache","root"),("frankenphp","../x"),("apache","hoosh-web-edge")):
            self.assertFalse(M["check"](engine,name))

    def test_exact_engine_and_id_bound_marker(self):
        u=SimpleNamespace(pw_uid=62010,pw_gid=62010)
        e=SimpleNamespace(pw_uid=999,pw_gid=999)
        calls=[]
        def read(p,expected):
            calls.append((str(p),expected))
            return True
        with patch.dict(G, {"identity":lambda name:e if name=="hoosh-web-edge" else u,"read_marker":read}), patch("os.getuid",return_value=62010), patch("os.getgid",return_value=62010):
            self.assertTrue(M["check"]("apache","tenant"))
        self.assertEqual(calls[0],("/etc/hoosh-runtimes/apache-accounts/tenant",b"tenant:62010:62010\n"))
        self.assertEqual(calls[1],("/etc/hoosh-runtimes/edge-accounts/apache-tenant",b"apache:tenant:62010:62010:999:999\n"))

    def test_units_do_not_publish_tcp_or_shared_uid(self):
        for engine in ("apache","frankenphp"):
            sock=(ROOT/f"hoosh-edge-{engine}@.socket").read_text()
            service=(ROOT/f"hoosh-edge-{engine}@.service").read_text()
            self.assertIn(f"ListenStream=/run/hoosh-edge-{engine}-%i.sock",sock)
            self.assertIn("SocketUser=hoosh-web-edge",sock)
            self.assertIn("SocketMode=0600",sock)
            self.assertIn("User=%i",service)
            self.assertIn("RestrictAddressFamilies=AF_UNIX",service)
            self.assertIn("--connections-max=8",service)
            self.assertNotIn("nobody",sock+service)
            self.assertNotIn("[Install]",sock+service)
