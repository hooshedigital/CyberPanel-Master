"""Regression tests for a genuine Core-wide (not per-add-on) i18n rollout."""
import gettext
import io
from pathlib import Path
import tempfile
import unittest

from scripts.compile_po import compile_file, parse_po
from scripts.stage_global_i18n import (
    SETTINGS, TEMPLATE, URLS, build_overlay, patch_settings, patch_shell,
    patch_urls,
)

SAMPLE_SETTINGS = """import os
from django.utils.translation import gettext_lazy as _
BASE_DIR = '/opt/mock/CyberCP'
LANGUAGE_CODE = 'en'
USE_I18N = True
LANGUAGES = (('en', _('English')),)
LOCALE_PATHS = (os.path.join(BASE_DIR, 'locale'),)
MIDDLEWARE = ['django.contrib.sessions.middleware.SessionMiddleware',
              'django.middleware.locale.LocaleMiddleware']
"""

SAMPLE_URLS = """from django.urls import path, re_path, include
urlpatterns = [
    path('', include('loginSystem.urls')),
]
"""

SAMPLE_SHELL = """{% load i18n %}
{% get_current_language as LANGUAGE_CODE %}
<html class="cp-evergreen" lang="en" ng-app="CyberCP">
<head>{% block header_scripts %}{% endblock %}</head>
<body>
<header class="native-header"><div class="native-tools"><div class="social-icons"><a href="#">Social</a></div></div></header>
<nav id="sidebar"><div class="sidebar-logo">Brand</div>
<div class="sidebar-search">Search</div></nav>
</body></html>
"""


class GlobalCoreLanguageTests(unittest.TestCase):
    def test_core_patch_integrates_global_shell_not_only_master_page(self):
        shell = patch_shell(SAMPLE_SHELL)
        self.assertIn('lang="{{ LANGUAGE_CODE', shell)
        self.assertIn("dir=\"{% if LANGUAGE_CODE == 'fa' %}rtl", shell)
        self.assertIn('hooshMasterSetLanguage', shell)
        self.assertIn('name="language" value="en"', shell)
        self.assertIn('name="language" value="fa"', shell)
        self.assertIn('csrf_token', shell)
        self.assertIn('baseTemplate/css/hoosh-master-shell.css', shell)
        self.assertIn('nav id="sidebar"', shell)
        self.assertLess(shell.index("hm-global-language"), shell.index('class="social-icons"'))
        self.assertLess(shell.index('class="social-icons"'), shell.index('nav id="sidebar"'))

    def test_requires_unique_verified_social_header(self):
        missing = SAMPLE_SHELL.replace('class="social-icons"', 'class="utility-other"')
        with self.assertRaisesRegex(ValueError, "native social header"):
            patch_shell(missing)
        duplicate = SAMPLE_SHELL.replace('</header>',
            '<div class="social-icons"></div></header>')
        with self.assertRaisesRegex(ValueError, "native social header"):
            patch_shell(duplicate)

    def test_brand_stays_whole_panel_and_duplicate_menu_becomes_ops_center(self):
        shell = SAMPLE_SHELL.replace(
            '<div class="sidebar-logo">Brand</div>',
            '<div class="sidebar-logo">CyberPanel Master</div>'
            '<span>CyberPanel Master</span>'
            "l:'CyberPanel Master'",
        )
        updated = patch_shell(shell)
        self.assertIn('<div class="sidebar-logo">CyberPanel Master</div>', updated)
        self.assertIn('<span>{% trans "Operations Center" %}</span>', updated)
        self.assertIn('l:\'{% trans "Operations Center" %}\'', updated)

    def test_settings_preserve_english_default_and_existing_languages(self):
        updated = patch_settings(SAMPLE_SETTINGS)
        compile(updated, SETTINGS, "exec")
        self.assertIn("LANGUAGE_CODE != 'en'", updated)
        self.assertIn("LANGUAGES = tuple(LANGUAGES)", updated)
        self.assertIn('master_extensions', updated)
        self.assertIn('LOCALE_PATHS', updated)
        self.assertIn('LANGUAGE_COOKIE_SECURE = True', updated)
        self.assertIn('LANGUAGE_COOKIE_HTTPONLY = True', updated)
        self.assertIn("LANGUAGE_COOKIE_SAMESITE = 'Lax'", updated)

    def test_language_post_uses_django_official_csrf_guarded_view(self):
        updated = patch_urls(SAMPLE_URLS)
        compile(updated, URLS, "exec")
        self.assertIn('from django.views.i18n import set_language', updated)
        self.assertIn("path('master/i18n/set-language/', set_language", updated)
        self.assertIn("include('loginSystem.urls')", updated)

    def test_core_i18n_overlay_is_staging_only_and_gettext_works(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "core"
            out = Path(tmp) / "staged"
            for path, value in ((SETTINGS,SAMPLE_SETTINGS),
                                (URLS,SAMPLE_URLS),(TEMPLATE,SAMPLE_SHELL)):
                file = root / path
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text(value)
            manifest = build_overlay(root,out)
            self.assertEqual(manifest["file_count"],6)
            self.assertEqual(manifest["production_changes"],0)
            self.assertEqual(manifest["global_language_default"],"en")
            self.assertGreaterEqual(manifest["translated_shell_messages"],150)
            self.assertEqual((root / TEMPLATE).read_text(), SAMPLE_SHELL)
            mo = out / "master_extensions/locale/fa/LC_MESSAGES/django.mo"
            with mo.open("rb") as handle:
                translation = gettext.GNUTranslations(handle)
            self.assertEqual(translation.gettext("Dashboard"), "داشبورد")
            self.assertEqual(translation.gettext("AI Scanner"), "اسکنر امنیتی هوشمند")
            self.assertEqual(translation.gettext("Untranslated label"), "Untranslated label")

    def test_unknown_or_already_patched_core_fails_closed(self):
        with self.assertRaises(ValueError):
            patch_shell("<html lang='en'></html>")
        with self.assertRaises(ValueError):
            patch_shell(patch_shell(SAMPLE_SHELL))
        with self.assertRaises(ValueError):
            patch_settings("LANGUAGE_CODE = 'fa'")
        with self.assertRaises(ValueError):
            patch_urls("urlpatterns = []")

    def test_static_locale_coverage_audit_reports_untranslated_core_pages(self):
        from scripts.audit_core_i18n import scan_translation_coverage
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "baseTemplate/templates/baseTemplate/index.html"
            template.parent.mkdir(parents=True)
            template.write_text('{% trans "Dashboard" %} {% trans "New Text" %}')
            report = scan_translation_coverage(root, {"Dashboard": "داشبورد"})
            self.assertEqual(report["unique_source_keys"], 2)
            self.assertEqual(report["translated_keys"], 1)
            self.assertEqual(report["coverage_percent"], 50)
            self.assertFalse(report["deployment_ready"])

    def test_overlay_builder_direct_cli_invocation(self):
        import subprocess
        import sys
        script = Path(__file__).resolve().parents[2] / "scripts/stage_global_i18n.py"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "core"
            out = Path(tmp) / "overlay"
            for path, source in ((SETTINGS, SAMPLE_SETTINGS),
                                 (URLS, SAMPLE_URLS), (TEMPLATE, SAMPLE_SHELL)):
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(source)
            run = subprocess.run(
                [sys.executable, str(script), "--core", str(root),
                 "--output", str(out)],
                cwd=tmp, capture_output=True, text=True, timeout=20,
            )
            self.assertEqual(run.returncode, 0, run.stderr[-1000:])
            self.assertTrue((out / "master_extensions/locale/fa/LC_MESSAGES/django.mo").is_file())
            self.assertEqual(
                __import__("json").loads(run.stdout)["file_count"], 6
            )

    def test_compiler_rejects_duplicate_and_fuzzy_entries(self):
        data = 'msgid ""\nmsgstr "Content-Type: text/plain; charset=UTF-8\\n"\n'
        with self.assertRaises(ValueError):
            parse_po(data + '\nmsgid "x"\nmsgstr "A"\n\nmsgid "x"\nmsgstr "B"\n')
        with self.assertRaises(ValueError):
            parse_po(data + '\n#, fuzzy\nmsgid "test"\nmsgstr "آزمایش"\n')

if __name__ == "__main__":
    unittest.main()
