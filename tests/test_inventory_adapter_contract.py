"""Offline inventory adapter contract tests."""
import unittest
from control_plane.inventory import DisconnectedAdapter, SyntheticAdapter

class InventoryContractTests(unittest.TestCase):
    def test_disconnected_adapter_does_not_fabricate_assets(self):
        for kind in ("sites", "ssl", "backups"):
            snapshot = DisconnectedAdapter().inventory(kind)
            self.assertEqual(snapshot.kind, kind)
            self.assertEqual(snapshot.source, "not_connected")
            self.assertFalse(snapshot.production_connected)
            self.assertEqual(snapshot.as_json()["items"], [])

    def test_synthetic_adapter_is_explicitly_labeled(self):
        for kind in ("sites", "ssl", "backups"):
            snapshot = SyntheticAdapter().inventory(kind)
            self.assertEqual(snapshot.kind, kind)
            self.assertEqual(snapshot.source, "synthetic")
            self.assertFalse(snapshot.production_connected)
            self.assertTrue(snapshot.as_json()["items"])
            self.assertTrue(all(item["state"] == "fixture" for item in snapshot.as_json()["items"]))

    def test_invalid_inventory_kinds_are_rejected(self):
        for adapter in (DisconnectedAdapter(), SyntheticAdapter()):
            for kind in ("", "users", "../sites", "Sites"):
                with self.assertRaises(ValueError):
                    adapter.inventory(kind)

if __name__ == "__main__":
    unittest.main()
