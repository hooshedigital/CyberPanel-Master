"""Static contract tests for UI consistency and license-safe source parity.

These tests intentionally do not import Django or access a live panel.
A green result does NOT replace browser QA or production source attestation.
"""
from pathlib import Path
import re
import unittest

from master_extensions.captcha_context import (
    VERIFIED_PUBLIC_SITEKEY_20261118, sitekey_for,
)
from master_extensions.i18n import LABELS, BACKUP_LABELS, context_for
from master_extensions.backup_i18n import LABELS as LEGACY_BACKUP_LABELS
from master_extensions.commerce_modules import modules_for


ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "master_extensions" / "templates" / "backup"


class NativeUIAndI18NAudit(unittest.TestCase):
    def test_turnstile_key_is_reported_key_and_overridable(self):
        # Public sitekey only; private siteverify secret is never in source.
        self.assertEqual(VERIFIED_PUBLIC_SITEKEY_20261118,
                         "0x4AAAAAAGG-PjEcCDvWgNdr")
        self.assertEqual(sitekey_for({}), VERIFIED_PUBLIC_SITEKEY_20261118)
        self.assertEqual(sitekey_for({"sitekey": "0x4AAAAAAGG-PjEcCDvWgNdr"}),
                         VERIFIED_PUBLIC_SITEKEY_20261118)
        self.assertEqual(sitekey_for({"sitekey": "unsafe\nvalue"}), "")
        self.assertEqual(sitekey_for({"sitekey": None}), "")
        self.assertEqual(sitekey_for(None), "")

    def test_language_registry_parity_and_directions(self):
        self.assertEqual(set(LABELS["fa"]), set(LABELS["en"]))
        self.assertEqual(set(BACKUP_LABELS["fa"]), set(BACKUP_LABELS["en"]))
        self.assertEqual(set(LEGACY_BACKUP_LABELS["fa"]),
                         set(LEGACY_BACKUP_LABELS["en"]))
        self.assertEqual(context_for("fa")["direction"], "rtl")
        self.assertEqual(context_for("en")["direction"], "ltr")
        self.assertNotEqual(LABELS["fa"]["commerce_heading"],
                            LABELS["en"]["commerce_heading"])
        self.assertNotEqual(BACKUP_LABELS["fa"]["snapshot"],
                            BACKUP_LABELS["en"]["snapshot"])

    def test_master_uses_exact_same_native_tile_markup_as_existing(self):
        html = (TEMPLATES / "cyberpanel_master.html").read_text()
        self.assertIn('id="whmcs-center"', html)
        commerce = html.split('id="whmcs-center"', 1)[1].split("</section>", 1)[0]
        self.assertIn('class="cp-tile-grid"', commerce)
        self.assertIn('class="cp-tile"', commerce)
        self.assertIn('class="cp-tile-ic"', commerce)
        self.assertIn('class="cp-tile-title"', commerce)
        self.assertIn('class="cp-tile-sub"', commerce)
        self.assertNotIn("style=", commerce)
        self.assertNotIn("<style", commerce)
        self.assertNotIn("<script", commerce)
        # The original Master cards also use the same native icon wrapper.
        self.assertIn('class="cp-tile-ic"', html.split('id="whmcs-center"', 1)[0])
        self.assertIn('dir="{{ direction }}"', html)
        self.assertNotIn('dir="rtl" lang="en"', html)

    def test_icons_reuse_existing_classes_only(self):
        cards = modules_for("en")
        html = (TEMPLATES / "cyberpanel_master.html").read_text()
        self.assertIn('class="fas {{ module.icon }}"', html)
        head = html.split('id="whmcs-center"', 1)[0]
        for item in cards:
            self.assertIn(item["icon"], head)
            self.assertNotIn('url', item)

    def test_english_and_persian_links_are_explicitly_directional(self):
        for template in ("cyberpanel_master.html", "hoosh_smart.html",
                         "hoosh_smart_bilingual.html"):
            html = (TEMPLATES / template).read_text()
            self.assertIn('lang="en" dir="ltr">English</a>', html)
            self.assertIn('lang="fa" dir="rtl">فارسی</a>', html)
            self.assertNotIn('Snapshot:', html)

    def test_all_master_label_references_exist(self):
        html = (TEMPLATES / "cyberpanel_master.html").read_text()
        used = set(re.findall(r"{{\s*t\.(\w+)\s*}}", html))
        self.assertFalse(used - set(LABELS["en"]), used - set(LABELS["en"]))
        self.assertFalse(used - set(LABELS["fa"]), used - set(LABELS["fa"]))
        for template, mapping, name in [
            ("hoosh_smart.html", LEGACY_BACKUP_LABELS, "b"),
            ("hoosh_smart_bilingual.html", BACKUP_LABELS, "backup_t"),
        ]:
            html = (TEMPLATES / template).read_text()
            used = set(re.findall(r"{{\s*" + name + r"\.(\w+)\s*}}", html))
            self.assertFalse(used - set(mapping["en"]), used - set(mapping["en"]))
            self.assertFalse(used - set(mapping["fa"]), used - set(mapping["fa"]))


if __name__ == "__main__":
    unittest.main()
