"""Plan a fail-closed, server-local full-shell language overlay for CyberPanel.

Affects the *actual* baseTemplate shell, root URLconf and Django settings.
Source is never uploaded to GitHub, and production is never changed by this tool.
The English original remains the default; Persian is an additional option.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import os
import re
import stat

ROOT = Path("/usr/local/CyberCP")
TEMPLATE = "baseTemplate/templates/baseTemplate/index.html"
SETTINGS = "CyberCP/settings.py"
URLS = "CyberCP/urls.py"
MAX_SIZE = 250_000
STAMP = "HOOSH_GLOBAL_I18N_V020"
LANGUAGE_FORM = """<!-- HOOSH_GLOBAL_I18N_V020 -->
<form method="post" action="{% url 'hooshMasterSetLanguage' %}"
      class="hm-global-language" aria-label="Interface language">
  {% csrf_token %}
  <input type="hidden" name="next" value="{{ request.path }}">
  <span class="hm-global-language__label">{% trans "Language" %}</span>
  <button type="submit" name="language" value="en" lang="en" dir="ltr"
          class="hm-lang-option{% if LANGUAGE_CODE == 'en' %} is-active{% endif %}"
          aria-pressed="{% if LANGUAGE_CODE == 'en' %}true{% else %}false{% endif %}">English</button>
  <button type="submit" name="language" value="fa" lang="fa" dir="rtl"
          class="hm-lang-option{% if LANGUAGE_CODE == 'fa' %} is-active{% endif %}"
          aria-pressed="{% if LANGUAGE_CODE == 'fa' %}true{% else %}false{% endif %}">فارسی</button>
</form>
<!-- /HOOSH_GLOBAL_I18N_V020 -->"""
HEAD_CSS = """<!-- HOOSH_GLOBAL_I18N_V020 HEAD -->
<link rel="stylesheet" href="{% static 'baseTemplate/css/hoosh-master-shell.css' %}?v=0.2.0">
<!-- /HOOSH_GLOBAL_I18N_V020 HEAD -->"""
SETTINGS_BLOCK = """
# HOOSH_GLOBAL_I18N_V020
# Preserve all original CyberPanel language choices and default English.
if LANGUAGE_CODE != 'en' or not USE_I18N:
    raise RuntimeError('Hoosh Master i18n: unexpected CyberPanel base settings')
if not any(code == 'fa' for code, _ in LANGUAGES):
    LANGUAGES = tuple(LANGUAGES) + (('fa', _('Persian')),)
LOCALE_PATHS = (os.path.join(BASE_DIR, 'master_extensions', 'locale'),) + tuple(LOCALE_PATHS)
# /HOOSH_GLOBAL_I18N_V020
"""
URL_BLOCK = """    # HOOSH_GLOBAL_I18N_V020: Django's CSRF-guarded official language view
    path('master/i18n/set-language/', set_language, name='hooshMasterSetLanguage'),
    # /HOOSH_GLOBAL_I18N_V020
"""
HTML_OPEN = re.compile(r'<html(?P<attrs>[^>]*?)lang="en"(?P<tail>[^>]*)>',re.I)


def read_regular(root: Path, relative: str) -> str:
    path = root / relative
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size == 0 or info.st_size > MAX_SIZE:
        raise ValueError(f"unsafe source: {relative}")
    return path.read_text("utf-8")


def unique_replace(src: str, old: str, new: str, path: str) -> str:
    if src.count(old) != 1:
        raise ValueError(f"unknown live layout: {path} anchor {old[:64]!r}")
    return src.replace(old, new, 1)


def patch_shell(template: str) -> str:
    if STAMP in template:
        raise ValueError("shell already patched; do not double-install")
    if not re.search(r'{%\s*load\s+[^%]*i18n\b',template):
        raise ValueError("shell is missing Django i18n tags")
    if not re.search(r'{%\s*get_current_language\s+as\s+LANGUAGE_CODE\s*%}',template):
        raise ValueError("shell is missing current language token")
    matches = list(HTML_OPEN.finditer(template))
    if len(matches) != 1:
        raise ValueError("cannot locate unique original HTML language")
    m=matches[0]
    newer = '<html'+m.group('attrs')+'lang="{{ LANGUAGE_CODE|default:\'en\' }}" dir="{% if LANGUAGE_CODE == \'fa\' %}rtl{% else %}ltr{% endif %}"'+m.group('tail')+'>'
    template = template[:m.start()] + newer + template[m.end():]
    # Inject form only in the native sidebar, after its existing branding.
    anchor = '<div class="sidebar-search">'
    if template.count(anchor) != 1 or '<nav id="sidebar"' not in template:
        raise ValueError("unexpected sidebar layout")
    template = unique_replace(template,anchor,LANGUAGE_FORM+'\n'+anchor,TEMPLATE)
    template = unique_replace(template,'{% block header_scripts %}',HEAD_CSS+'\n{% block header_scripts %}',TEMPLATE)

    # CyberPanel Master is already the installed shell brand. The second
    # navigation entry with the same title is only its Operations Center.
    # Do not replace the brand itself or other upstream page names.
    native_panel = '<span>CyberPanel Master</span>'
    if template.count(native_panel):
        template = unique_replace(template, native_panel,
                                  '<span>{% trans "Operations Center" %}</span>', TEMPLATE)
    command_label = "l:'CyberPanel Master'"
    if template.count(command_label):
        template = unique_replace(template, command_label,
                                  "l:'{% trans \"Operations Center\" %}'", TEMPLATE)

    # Native header version must reflect the installed custom Master, while
    # upstream Core version retains its own source of truth.
    if template.count('Master v0.1.0'):
        if template.count('Master v0.1.0') != 2:
            raise ValueError('unexpected Master version tag placement')
        template = template.replace('Master v0.1.0', 'Master v0.2.0-dev')
    default_title = '{% block title %}CyberPanel{% endblock %}'
    if default_title in template:
        template = unique_replace(template,default_title,
                                  '{% block title %}CyberPanel Master{% endblock %}',TEMPLATE)
    return template


def patch_settings(source: str) -> str:
    if STAMP in source:
        raise ValueError("settings already patched")
    required=(r"(?m)^LANGUAGE_CODE\s*=\s*['\"]en['\"]\s*$",
              r"(?m)^USE_I18N\s*=\s*True\s*$",
              r"(?m)^LOCALE_PATHS\s*=",
              r"django\.middleware\.locale\.LocaleMiddleware")
    if not all(re.search(expr,source) for expr in required):
        raise ValueError("unexpected i18n settings; inspect exact installed version first")
    if 'LANGUAGES' not in source or 'from django.utils.translation import gettext_lazy as _' not in source:
        raise ValueError("unsupported locale configuration")
    return source.rstrip()+'\n'+SETTINGS_BLOCK


def patch_urls(source: str) -> str:
    if STAMP in source or 'hooshMasterSetLanguage' in source:
        raise ValueError("URLconf already patched")
    source = unique_replace(source, "urlpatterns = [",
                            "urlpatterns = [" + chr(10) + URL_BLOCK, URLS)
    if 'from django.urls import path, re_path, include' not in source:
        raise ValueError("unsupported CyberCP URLconf")
    return unique_replace(source, "from django.urls import path, re_path, include",
                          "from django.urls import path, re_path, include" + chr(10)
                          + "from django.views.i18n import set_language", URLS)


def build_overlay(root: Path, output: Path) -> dict:
    """Stage modified files only. Never open a customer db or write Core paths."""
    if output.exists():
        raise ValueError("overlay output exists; do not overwrite reviews")
    original={p:read_regular(root,p) for p in (SETTINGS,URLS,TEMPLATE)}
    changed={SETTINGS:patch_settings(original[SETTINGS]),
             URLS:patch_urls(original[URLS]),
             TEMPLATE:patch_shell(original[TEMPLATE])}
    for rel,body in changed.items():
        if rel.endswith(".py"):
            compile(body,rel,"exec")
        if not body or body==original[rel]:
            raise ValueError("patch unexpectedly empty/no-op")
    output.mkdir(mode=0o700,parents=False)
    os.chmod(output,0o700)
    changes=[]
    for rel,body in changed.items():
        path=output/rel
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(body,"utf-8")
        changes.append({"path":rel,
                        "before_sha256":hashlib.sha256(original[rel].encode()).hexdigest(),
                        "after_sha256":hashlib.sha256(body.encode()).hexdigest(),
                        "status":"staging_only"})
    manifest={"version":"0.2.0-dev","global_language_default":"en",
              "additional_language":"fa","production_changes":0,
              "file_count":len(changes),"files":changes}
    # Ship the two static/locale resources alongside the three source overlays.
    # Works both as a CLI (python scripts/stage_global_i18n.py) and imported
    # package module (python -m unittest / python -m scripts.stage_global_i18n).
    if __package__:
        from .compile_po import compile_file
    else:
        from compile_po import compile_file
    project = Path(__file__).resolve().parents[1]
    css_src = project / "master_extensions/static/master_extensions/global-shell.css"
    css_dest = output / "baseTemplate/static/baseTemplate/css/hoosh-master-shell.css"
    css_dest.parent.mkdir(parents=True, exist_ok=True)
    css_dest.write_bytes(css_src.read_bytes())
    po_src = project / "master_extensions/locale/fa/LC_MESSAGES/django.po"
    po_dest = output / "master_extensions/locale/fa/LC_MESSAGES/django.po"
    mo_dest = output / "master_extensions/locale/fa/LC_MESSAGES/django.mo"
    po_dest.parent.mkdir(parents=True, exist_ok=True)
    po_dest.write_bytes(po_src.read_bytes())
    translations_count = compile_file(po_dest, mo_dest)
    for dest in (css_dest, po_dest, mo_dest):
        rel = str(dest.relative_to(output))
        changes.append({"path":rel,"before_sha256":None,
                        "after_sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
                        "status":"staging_only"})
    manifest["file_count"] = len(changes)
    manifest["translated_shell_messages"] = translations_count
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2))
    return manifest


if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--core",type=Path,default=ROOT)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(build_overlay(args.core,args.output)))
