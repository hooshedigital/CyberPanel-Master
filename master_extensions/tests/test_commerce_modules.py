import unittest

from master_extensions.commerce_modules import modules_for, status_note


class CommerceModulesTests(unittest.TestCase):
    def test_modules_cover_commerce_and_linux(self):
        ids = [item["id"] for item in modules_for("en")]
        self.assertEqual(len(ids), len(set(ids)))
        for key in ["billing", "packages", "catalog", "affiliates", "campaigns", "provisioning", "identity", "linux", "vps"]:
            self.assertIn(key, ids)

    def test_language_parity_and_disconnected_status(self):
        english = modules_for("en")
        persian = modules_for("fa")
        self.assertEqual([m["id"] for m in english], [m["id"] for m in persian])
        self.assertTrue(all(m["status"] == "Planned / not connected" for m in english))
        self.assertTrue(all(m["status"] == "برنامه‌ریزی‌شده / متصل نیست" for m in persian))
        self.assertTrue(all(m["stage"] in ("v1", "v2") for m in english))

    def test_no_live_links_or_privileged_operations_in_registry(self):
        for item in modules_for("en"):
            self.assertEqual(set(item), {"id", "name", "description", "stage", "status", "icon"})
            self.assertNotIn("url", item)
            self.assertNotIn("api_key", item)
            self.assertNotIn("root_password", item)
            self.assertIn(item["icon"], {"fa-heartbeat", "fa-brain", "fa-server", "fa-project-diagram", "fa-route"})
        self.assertIn("no live WHMCS access", status_note("en"))

    def test_invalid_language_rejected(self):
        with self.assertRaises(ValueError):
            modules_for("../fa")
        with self.assertRaises(ValueError):
            status_note("unknown")


if __name__ == "__main__":
    unittest.main()
