import runpy
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
M=runpy.run_path(str(ROOT/"infra/ingress/hoosh-canary-health"))
G=M["collect"].__globals__

class CanaryHealthTests(unittest.TestCase):
    def collect(self,token="absent",connector="inactive",ok=True,cert=0):
        with patch.dict(G,{"service":lambda u: connector if "connector" in u else "active",
                           "credential_state":lambda:token,"run":lambda *a:(cert,b""),
                           "probe":lambda:(ok,0.02)}):
            return M["collect"]()
    def test_local_pending(self):
        r=self.collect()
        self.assertEqual(r["state"],"local_ready_token_pending")
        self.assertFalse(r["public_https_verified"])
        self.assertFalse(r["dns_changes"])
    def test_never_claim_public(self):
        r=self.collect(token="present",connector="active")
        self.assertEqual(r["state"],"connector_running_external_unverified")
        self.assertFalse(r["public_https_verified"])
    def test_fail_closed(self):
        self.assertEqual(self.collect(ok=False)["state"],"local_not_ready")
        self.assertEqual(self.collect(cert=1)["state"],"certificate_review_required")
    def test_exact_marker(self):
        with patch.dict(G,{"run":lambda *a:(0,M["MARKER"]+b"\n200\n")}):
            self.assertTrue(M["probe"]()[0])
        with patch.dict(G,{"run":lambda *a:(0,M["MARKER"]+b"\n302\n")}):
            self.assertFalse(M["probe"]()[0])
