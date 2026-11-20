"""No simulated AI results: verify actual local read-only scanner behavior."""
import os
from pathlib import Path
import tempfile
import time
import unittest

from master_extensions.security_inspector import inspect_site

class IndependentSiteScannerTests(unittest.TestCase):
    def make_site(self, parent):
        root = Path(parent) / "public_html"
        (root / "wp-includes").mkdir(parents=True)
        (root / "wp-content" / "uploads").mkdir(parents=True)
        (root / "index.php").write_text("<?php echo 'hello'; ?>")
        return root

    def test_clean_site_readonly_never_promises_malware_free(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_site(tmp)
            before = (root / "index.php").read_bytes()
            report = inspect_site(root, allowed_roots=(root,))
            self.assertTrue(report["ready"])
            self.assertEqual(report["findings"], [])
            self.assertEqual(report["files_modified"], 0)
            self.assertFalse(report["ai_provider_used"])
            self.assertEqual((root / "index.php").read_bytes(), before)
            self.assertNotIn("malware_free", report)

    def test_upload_php_and_obfuscation_detected_without_file_leaks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_site(tmp)
            payload = "<?php eval(base64_decode('Zm9v')); ?>"
            p = root / "wp-content" / "uploads" / "a.php"
            p.write_text(payload)
            report = inspect_site(root, allowed_roots=(root,))
            rules = {f["rule"] for f in report["findings"]}
            self.assertIn("PHP_IN_UPLOADS", rules)
            self.assertIn("PHP_OBFUSCATED_EVAL", rules)
            self.assertNotIn(payload, str(report))
            self.assertNotIn(str(root), str(report))
            self.assertEqual(report["files_modified"], 0)

    def test_rejects_unapproved_roots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_site(tmp)
            with self.assertRaises(PermissionError):
                inspect_site(root, allowed_roots=())
            with self.assertRaises(PermissionError):
                inspect_site(root, allowed_roots=(Path(tmp) / "not_approved",))
            link = Path(tmp) / "site_link"
            link.symlink_to(root, target_is_directory=True)
            with self.assertRaises(PermissionError):
                inspect_site(link, allowed_roots=(root,))

    def test_symlink_ignored_even_if_it_targets_suspicious_php(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_site(tmp)
            outside = Path(tmp) / "outside.php"
            outside.write_text("<?php eval(base64_decode('xyz')); ?>")
            (root / "wp-content" / "uploads" / "outside.php").symlink_to(outside)
            report = inspect_site(root, allowed_roots=(root,))
            self.assertEqual(report["finding_count"], 0)

    def test_bounded_scan_marks_partial_without_deleting(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_site(tmp)
            for i in range(20):
                (root / f"file{i}.php").write_text("<?php echo 1; ?>")
            report = inspect_site(root, allowed_roots=(root,), max_entries=2)
            self.assertTrue(report["partial"])
            self.assertLessEqual(report["scanned_entries"], 2)
            self.assertTrue((root / "file19.php").exists())

    def test_non_wordpress_returns_not_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = inspect_site(root, allowed_roots=(root,))
            self.assertFalse(report["ready"])
            self.assertEqual(report["reason"], "not_a_verified_wordpress_tree")

    def test_resource_budget_limits_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_site(tmp)
            with self.assertRaises(ValueError):
                inspect_site(root, allowed_roots=(root,),max_entries=9999999)
            with self.assertRaises(ValueError):
                inspect_site(root, allowed_roots=(root,),max_seconds=999)
            with self.assertRaises(ValueError):
                inspect_site(root, allowed_roots=(root,),max_read=-1)

if __name__ == "__main__":
    unittest.main()
