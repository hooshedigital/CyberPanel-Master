import unittest
from pathlib import Path
from unittest.mock import patch
from master_extensions import bridge

class BridgeTests(unittest.TestCase):
    def test_gateway_disabled_does_not_contact_network(self):
        with patch.object(bridge,"safe_config",return_value={}), patch.object(bridge.urllib.request,"build_opener") as opener:
            result=bridge.gateway_status()
            self.assertFalse(result["connected"])
            opener.assert_not_called()

    def test_gateway_rejects_remote_plain_http(self):
        bad={"gateway":{"enabled":True,"status_url":"http://supabase.hooshedigital.ir/functions/v1/ai-gateway/api/status"}}
        with patch.object(bridge,"safe_config",return_value=bad), patch.object(bridge.urllib.request,"build_opener") as opener:
            self.assertFalse(bridge.gateway_status()["connected"])
            opener.assert_not_called()

    def test_gateway_rejects_status_prefix_impostor(self):
        bad={"gateway":{"enabled":True,"status_url":"https://supabase.hooshedigital.ir/functions/v1/ai-gateway/api/status.attacker"}}
        with patch.object(bridge,"safe_config",return_value=bad), patch.object(bridge.urllib.request,"build_opener") as opener:
            self.assertFalse(bridge.gateway_status()["connected"])
            opener.assert_not_called()

    def test_gateway_rejects_credentials_in_url(self):
        bad={"gateway":{"enabled":True,"status_url":"https://evil@supabase.hooshedigital.ir/functions/v1/ai-gateway/api/status"}}
        with patch.object(bridge,"safe_config",return_value=bad), patch.object(bridge.urllib.request,"build_opener") as opener:
            self.assertFalse(bridge.gateway_status()["connected"])
            opener.assert_not_called()

    def test_actual_cyberpanel_json_version(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            v=Path(d)/"version.txt"
            v.write_text('{"version":"3.0","build":4}')
            with patch.object(bridge,"CORE_VERSION_FILES",(v,)):
                self.assertEqual(bridge.core_version(),"3.0 Build 4")

    def test_core_version_never_guessed(self):
        with patch.object(bridge,"CORE_VERSION_FILES",(Path("/nonexistent/cyberpanel/version"),)):
            self.assertIsNone(bridge.core_version())

    def test_unit_unavailable_is_not_reported_online(self):
        from types import SimpleNamespace
        p=SimpleNamespace(returncode=0,stdout="LoadState=not-found\nActiveState=inactive\nSubState=dead\n")
        with patch.object(bridge.subprocess,"run",return_value=p),patch.object(bridge,"core_version",return_value=None):
            self.assertFalse(bridge.unit_status()["connected"])

    def test_report_emitter_has_strict_filename_allowlist(self):
        with self.assertRaises(ValueError):
            bridge.emit("../../etc/shadow", {"schema": 1})
        with self.assertRaises(ValueError):
            bridge.emit("agent-operations.json", {"schema": 1})

    def test_default_output_safe(self):
        for f in (bridge.gateway_status(),):
            self.assertEqual(f["schema"],1)
            self.assertFalse(f["connected"])
            self.assertNotIn("secret",f)
            self.assertNotIn("token",f)

if __name__=="__main__":unittest.main()
