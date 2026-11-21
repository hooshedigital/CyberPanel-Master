import unittest
from master_extensions.whmcs_workspace import whmcs_workspace, TABS


class WHMCSWorkspaceTests(unittest.TestCase):
    def test_bilingual_tabs_and_safe_selection(self):
        for lang in ("en", "fa"):
            result = whmcs_workspace(lang, "affiliates", "https://billing.hooshedigital.ir/admin/")
            self.assertEqual(result["selected_id"], "affiliates")
            self.assertEqual(len(result["tabs"]), 6)
            self.assertTrue(result["admin_url_configured"])
            self.assertFalse(result["integration_verified"])
            self.assertFalse(result["operations_enabled"])
            self.assertNotIn("https://", str(result))
            self.assertNotIn("password", str(result).lower())
            self.assertEqual({x["id"] for x in result["tabs"]}, set(TABS))

    def test_unknown_and_malicious_query_select_defaults_safely(self):
        for selected in (None, 42, ["billing"], "../admin", "<script>", "root", ""):
            self.assertEqual(whmcs_workspace("fa", selected, None)["selected_id"], "billing")

    def test_configured_url_not_proof_of_api_or_sso(self):
        result = whmcs_workspace("en", "billing", "https://billing.hooshedigital.ir/admin/")
        self.assertTrue(result["admin_url_configured"])
        self.assertFalse(result["integration_verified"])
        self.assertFalse(result["operations_enabled"])
