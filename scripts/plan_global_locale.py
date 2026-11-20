"""Prepare an explicit, fail-closed Core-wide language overlay for CyberPanel.

The developer MUST run this against the *actual installed version* after source
parity inspection. No Core file is touched: outputs are written to an empty
staging directory. Existing CyberPanel middleware, routes, theme and icons
are preserved. This is the FOUNDATION for full-template/gettext translation,
not a claim that every old AngularJS string already has a Persian catalog.

Usage:
  python3 scripts/plan_global_locale.py --core /usr/local/CyberCP \
      --output /var/tmp/cybermaster-global-locale-preview

Review the manifest, Django check, static HTML/JS coverage, browser EN/FA and
owner-approved rollback BEFORE deploying any generated Core file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import sys

SETTINGS = "CyberCP/settings.py"
URLS = "CyberCP/urls.py"
SHELL = "baseTemplate/templates/baseTemplate/index.html"
TARGETS = (SETTINGS, URLS, SHELL)
MAX_BYTES = 200000


def guarded_read(root: Path, rel: str) -> str:
    target = root / rel
    s = target.lstat()
    if not stat.S_ISREG(s.st_mode) or not 0 < s.st_size <= MAX_BYTES:
        raise ValueError("invalid_core_target:" + rel)
    return target.read_text(encoding="utf-8")


def replace_once(text: str, original: str, replacement: str, name: str) -> str:
    if text.count(original) != 1:
        raise ValueError("unexpected_installed_core_version:" + name)
    return text.replace(original, replacement, 1)


def patch_settings(text: str) -> str:
    text = replace_once(
        text,
        "'django.middleware.locale.LocaleMiddleware'",
        "'master_extensions.product_locale.EnglishFirstLocaleMiddleware'",
        "locale_middleware",
    )
    if not re.search(r"(?m)^LANGUAGE_CODE\s*=\s*['\"]en['\"]\s*$", text):
        raise ValueError("English must remain the Core default language")
    if re.search(r"\(\s*['\"]fa['\"]\s*,", text):
        raise ValueError("Persian already registered: manual reconciliation required")
    text = replace_once(text, "LANGUAGES = (\n",
                        "LANGUAGES = (\n    ('fa', _('Persian')),\n",
                        "language_registration")
    if "USE_I18N = True" not in text or "LOCALE_PATHS" not in text:
        raise ValueError("gettext not configured in current Core")
    # Secure global preference cookie; no GET-based language switch.
    flags = {
        "LANGUAGE_COOKIE_SECURE": "True",
        "LANGUAGE_COOKIE_HTTPONLY": "True",
        "LANGUAGE_COOKIE_SAMESITE": "'Lax'",
        "LANGUAGE_COOKIE_PATH": "'/'",
    }
    for option, value in flags.items():
        if re.search(rf"(?m)^\s*{re.escape(option)}\s*=", text):
            raise ValueError("language cookie setting exists: manual parity review required")
        text += f"\n{option} = {value}\n"
    # We deliberately preserve all existing Core languages, database and secrets.
    return text


def patch_urls(text: str) -> str:
    text = replace_once(
        text, "urlpatterns = [\n",
        "from django.views.i18n import set_language as cybermaster_set_language\n\n"
        "urlpatterns = [\n"
        "    path('hoosh/language/', cybermaster_set_language, "
        "name='cybermaster_set_language'),\n",
        "language_route",
    )
    return text


LANGUAGE_SWITCH = """    <!-- Global CyberPanel Master language preference: native CSRF-protected POST. -->
    <form class="cp-product-language" action="{% url 'cybermaster_set_language' %}"
          method="post" aria-label="{% trans 'Panel language' %}">
        {% csrf_token %}
        <input type="hidden" name="next" value="{{ request.get_full_path|default:'/' }}">
        <button class="theme-toggle" type="submit" name="language" value="en"
                lang="en" dir="ltr" aria-pressed="{% if LANGUAGE_CODE == 'en' %}true{% else %}false{% endif %}">EN</button>
        <button class="theme-toggle" type="submit" name="language" value="fa"
                lang="fa" dir="rtl" aria-pressed="{% if LANGUAGE_CODE == 'fa' %}true{% else %}false{% endif %}">فا</button>
    </form>
"""


def patch_shell(text: str) -> str:
    if text.count("{% get_current_language as LANGUAGE_CODE %}") != 1:
        raise ValueError("installed shell lacks canonical Django i18n tag")
    text = replace_once(
        text,
        '<html class="cp-evergreen" lang="en" ng-app="CyberCP">',
        '<html class="cp-evergreen" lang="{{ LANGUAGE_CODE }}"'
        ' dir="{% if LANGUAGE_CODE == \'fa\' %}rtl{% else %}ltr{% endif %}" ng-app="CyberCP">',
        "global_language_and_direction",
    )
    text = replace_once(
        text, "{% block title %}CyberPanel{% endblock %}",
        "{% block title %}CyberPanel Master{% endblock %}", "whole_product_brand"
    )
    anchor = '            <button id="theme-toggle" class="theme-toggle"'
    text = replace_once(text, anchor, LANGUAGE_SWITCH + anchor,
                        "native_global_header_language_switch")
    # Browser text direction follows language, preserving all existing CSS/layout.
    # Full RTL regression must be approved before live Core shell deployment.
    return text


def plan(root: Path, output: Path) -> dict:
    root, output = root.resolve(), output.absolute()
    if not root.is_dir() or output.exists():
        raise ValueError("invalid core or output already exists")
    if output == root or root in output.parents:
        raise ValueError("staging output must be outside Core root")
    builders = {SETTINGS: patch_settings, URLS: patch_urls, SHELL: patch_shell}
    originals = {p: guarded_read(root, p) for p in TARGETS}
    replacements = {p: builders[p](originals[p]) for p in TARGETS}
    # A Core locale middleware patch MUST include its imported module and
    # compiled translation catalogs, or the login UI can fail on import.
    repo = Path(__file__).resolve().parents[1]
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    from scripts.compile_controlled_locale import load_simple_po, compile_mo
    module = "master_extensions/product_locale.py"
    catalog_po = "locale/fa/LC_MESSAGES/django.po"
    catalog_mo = "locale/fa/LC_MESSAGES/django.mo"
    source_module = guarded_read(repo, module).encode("utf-8")
    source_catalog = guarded_read(repo, catalog_po).encode("utf-8")
    compiled_catalog = compile_mo(load_simple_po(source_catalog.decode("utf-8")))
    dependencies = {module: source_module, catalog_po: source_catalog,
                    catalog_mo: compiled_catalog}
    for rel in dependencies:
        if (root / rel).exists() or (root / rel).is_symlink():
            raise ValueError("existing installed locale asset needs manual parity review:" + rel)
    # All preflight checks complete before writing anything.
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    changes = []
    for path in TARGETS:
        item = output / path
        item.parent.mkdir(parents=True, exist_ok=True)
        item.write_text(replacements[path], encoding="utf-8")
        changes.append({
            "path": path,
            "installed_sha256": hashlib.sha256(originals[path].encode()).hexdigest(),
            "staged_sha256": hashlib.sha256(replacements[path].encode()).hexdigest(),
            "source_lines": originals[path].count("\n") + 1,
            "locale_scope": "Core framework / shell only; catalog completion required",
        })
    for rel, payload in dependencies.items():
        dest = output / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(payload)
        changes.append({
            "path": rel, "installed_sha256": None,
            "staged_sha256": hashlib.sha256(payload).hexdigest(),
            "source_lines": None,
            "locale_scope": "Required Python middleware and compiled Persian catalog",
        })
    result = {
        "product": "CyberPanel Master",
        "default_language": "en", "additional_language": "fa",
        "full_translation_complete": False,
        "production_modified": False,
        "requires_owner_approval": True,
        "changes": changes,
    }
    (output / "manifest.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--core", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = plan(args.core, args.output)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
