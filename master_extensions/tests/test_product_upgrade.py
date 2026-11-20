"""Offline regression tests for whole-product i18n and independent WP scanner."""
from __future__ import annotations

from pathlib import Path
import os
import tempfile
import unittest
from types import SimpleNamespace

from scripts.plan_global_locale import plan, patch_shell, patch_settings
from scripts.audit_core_localization import inspect_tree
from master_extensions.wordpress_security_scan import scan_wordpress


def make_core(root: Path):
    (root / "CyberCP").mkdir()
    (root / "baseTemplate/templates/baseTemplate").mkdir(parents=True)
    (root / "CyberCP/settings.py").write_text(
        "LANGUAGE_CODE = 'en'\nUSE_I18N = True\nLOCALE_PATHS = ('locale',)\n"
        "MIDDLEWARE = ['django.middleware.locale.LocaleMiddleware']\n"
        "LANGUAGES = (\n    ('en', _('English')),\n)\n", encoding="utf-8")
    (root / "CyberCP/urls.py").write_text(
        "from django.urls import path\nurlpatterns = [\n]\n", encoding="utf-8")
    (root / "baseTemplate/templates/baseTemplate/index.html").write_text(
        '{% load i18n %}\n{% get_current_language as LANGUAGE_CODE %}\n'
        '<html class="cp-evergreen" lang="en" ng-app="CyberCP">\n'
        '<title>{% block title %}CyberPanel{% endblock %}</title>\n'
        '<button id="theme-toggle" class="theme-toggle"></button>\n</html>',
        encoding="utf-8")


class FullProductLocaleTests(unittest.TestCase):
    def test_global_overlay_changes_core_middleware_header_url_and_languages(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, out = Path(tmp) / "core", Path(tmp) / "new"
            make_core(root)
            result = plan(root, out)
            self.assertFalse(result["production_modified"])
            self.assertFalse(result["full_translation_complete"])
            self.assertEqual(len(result["changes"]), 3)
            self.assertEqual((root / "CyberCP/settings.py").read_text().count("EnglishFirstLocaleMiddleware"), 0)
            settings = (out / "CyberCP/settings.py").read_text()
            shell = (out / "baseTemplate/templates/baseTemplate/index.html").read_text()
            urls = (out / "CyberCP/urls.py").read_text()
            self.assertIn("EnglishFirstLocaleMiddleware", settings)
            self.assertIn("('fa', _('Persian'))", settings)
            self.assertIn('LANGUAGE_CODE = \'en\'', settings)
            self.assertIn("dir=\"{% if LANGUAGE_CODE == 'fa' %}rtl", shell)
            self.assertIn('name="language" value="fa"', shell)
            self.assertIn("{% csrf_token %}", shell)
            self.assertIn("cybermaster_set_language", urls)
            self.assertEqual((root / "CyberCP/urls.py").read_text().count("cybermaster_set_language"), 0)

    def test_missing_or_changed_installed_core_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, out = Path(tmp) / "core", Path(tmp) / "preview"
            make_core(root)
            src = root / "CyberCP/settings.py"
            src.write_text(src.read_text().replace("'django.middleware.locale.LocaleMiddleware'",
                                                   "'custom.CompanyLocaleMiddleware'"))
            with self.assertRaises(ValueError):
                plan(root, out)
            self.assertFalse(out.exists())

    def test_language_choice_is_post_only_not_query_based(self):
        from pathlib import Path
        s = (Path(__file__).resolve().parents[2] / "master_extensions" /
             "product_locale.py").read_text()
        self.assertIn("request.COOKIES.get(cookie_name)", s)
        self.assertNotIn("request.GET.get", s)
        self.assertNotIn("request.META.get('HTTP_ACCEPT_LANGUAGE'", s)
        self.assertIn("EnglishFirstLocaleMiddleware", s)

    def test_gettext_catalog_is_compilable_and_truly_translates_common_nav(self):
        from scripts.compile_controlled_locale import compile_mo, load_simple_po
        import gettext
        import io
        root = Path(__file__).resolve().parents[2]
        po = (root / "locale" / "fa" / "LC_MESSAGES" / "django.po").read_text("utf-8")
        messages = load_simple_po(po)
        self.assertGreaterEqual(len(messages), 140)
        catalog = gettext.GNUTranslations(io.BytesIO(compile_mo(messages)))
        self.assertEqual(catalog.gettext("Dashboard"), "داشبورد")
        self.assertEqual(catalog.gettext("AI Scanner"), "اسکنر هوشمند")
        self.assertEqual(catalog.gettext("Manage SSL"), "مدیریت SSL")
        self.assertEqual(catalog.gettext("Websites"), "وب‌سایت‌ها")
        self.assertEqual(catalog.gettext("Not a source string"), "Not a source string")

    def test_existing_agent_checks_are_sanitized_bilingual(self):
        from datetime import datetime, timezone
        from master_extensions.operations_center import agent_summary
        now = datetime.now(timezone.utc)
        report = {"version": "0.9.0", "updated_at_unix": now.timestamp(),
                  "status": "warning", "checks_total": 3,
                  "checks": [
                      {"name": "service:lscpd.service", "status": "ok"},
                      {"name": "disk:/", "status": "warning"},
                      {"name": "token_PRIVATE", "status": "critical", "secret": "DO_NOT_LEAK"},
                      {"name": "disk:/", "status": "warning"},
                  ]}
        en = agent_summary(report=report, now=now, lang="en")
        fa = agent_summary(report=report, now=now, lang="fa")
        self.assertEqual(len(en["checks"]), 2)
        self.assertEqual(fa["checks"][0]["label"], "رابط CyberPanel")
        self.assertEqual(en["check_health"]["warning"], 1)
        self.assertEqual(en["check_health"]["ok"], 1)
        self.assertNotIn("PRIVATE", str(en))
        self.assertNotIn("DO_NOT_LEAK", str(en))
        self.assertFalse(en["operations_enabled"])

    def test_source_tree_audit_is_not_faked_translation_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "websiteFunctions/templates").mkdir(parents=True)
            (root / "websiteFunctions/templates/list.html").write_text(
                '<p>{% trans "Websites" %}</p><button>Delete Website</button>',
                encoding="utf-8")
            (root / "websiteFunctions/a.js").write_text(
                'const msg="Delete this website now";', encoding="utf-8")
            report = inspect_tree(root)
            self.assertEqual(report["scope"], "full_cyberpanel_source_tree")
            self.assertFalse(report["coverage_is_verified"])
            self.assertGreater(report["summary"]["possible_untranslated_display_strings"], 0)
            self.assertIn("websiteFunctions", report["modules"])


class WordPressSecurityScannerTests(unittest.TestCase):
    def test_real_local_php_scan_detects_indicator_without_leaking_php_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "wp-content").mkdir()
            (root / "wp-content" / "sample.php").write_text(
                "<?php $x = eval(base64_decode('c2FtcGxl')); ?>"
            )
            (root / "index.php").write_text("<?php echo 'Safe test file';")
            result = scan_wordpress(root)
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["files_scanned"], 2)
            self.assertEqual(len(result["findings"]), 1)
            self.assertEqual(result["findings"][0]["rule_id"], "PHP_EVAL_BASE64")
            self.assertNotIn("c2FtcGxl", str(result))
            self.assertEqual(result["files_modified"], 0)
            self.assertFalse(result["ai_analysis_performed"])
            self.assertTrue((root / "wp-content" / "sample.php").exists())

    def test_symlinks_to_other_site_are_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            own, other = base / "own", base / "other"
            own.mkdir()
            other.mkdir()
            (other / "outside.php").write_text("<?php eval(base64_decode('test'));")
            (own / "outside.php").symlink_to(other / "outside.php")
            (own / "external").symlink_to(other, target_is_directory=True)
            result = scan_wordpress(own)
            self.assertEqual(result["files_scanned"], 0)
            self.assertEqual(result["findings"], [])
            self.assertEqual((other / "outside.php").stat().st_size,
                             len("<?php eval(base64_decode('test'));"))

    def test_resource_bounds_mark_partial_and_block_uncontrolled_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i in range(4):
                (root / f"f{i}.php").write_text("<?php echo 'ok';")
            result = scan_wordpress(root, max_files=1)
            self.assertFalse(result["complete"])
            self.assertEqual(result["status"], "partial")
            self.assertEqual(result["files_scanned"], 1)
            with self.assertRaises(ValueError):
                scan_wordpress(root, max_files=9999999)
            with self.assertRaises(ValueError):
                scan_wordpress(Path("relative/website"))

    def test_root_symlink_is_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site = root / "site"
            site.mkdir()
            link = root / "site-link"
            link.symlink_to(site, target_is_directory=True)
            got = scan_wordpress(link)
            self.assertEqual(got["status"], "unavailable")

    def test_no_auto_fix_no_paid_api_and_no_exec(self):
        from pathlib import Path
        code = (Path(__file__).resolve().parents[2] / "master_extensions" /
                "wordpress_security_scan.py").read_text()
        self.assertNotIn("subprocess", code)
        self.assertNotIn("requests.post", code)
        self.assertNotIn("os.system(", code)
        self.assertNotIn("os.remove(", code)
        self.assertNotIn("unlink(", code)
        self.assertIn("O_NOFOLLOW", code)


if __name__ == "__main__":
    unittest.main()
