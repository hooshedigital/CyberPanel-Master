"""Regress the actual native CyberAgent screen and language-transport overlay."""
from pathlib import Path
import tempfile
import unittest

from master_extensions.agent_console_i18n import CHECK_FA, LABELS, labels, localized_check
from scripts.stage_agent_console import prepare

class CyberAgentConsoleTests(unittest.TestCase):
    def test_bilingual_keys_and_real_check_glossary(self):
        self.assertEqual(set(LABELS["en"]),set(LABELS["fa"]))
        self.assertGreaterEqual(len(CHECK_FA),18)
        self.assertEqual(labels("fa")["title"],"سایبر ایجنت · مرکز مدیریت زیرساخت")
        check={"label":"CyberPanel","state":"ok",
               "next_step":"Inspect lscpd health and panel logs."}
        fa=localized_check(check,"fa")
        self.assertEqual(fa["display_label"],"سایبرپنل")
        self.assertEqual(fa["state"],"ok")
        self.assertEqual(check["label"],"CyberPanel")
        en=localized_check(check,"en")
        self.assertEqual(en["display_label"],"CyberPanel")
        with self.assertRaises(ValueError):
            labels("ar")

    def test_template_is_native_responsive_card_design(self):
        path=Path(__file__).resolve().parents[2] / "master_extensions/templates/backup/cyber_agent.html"
        txt=path.read_text()
        self.assertIn('{% extends "baseTemplate/index.html" %}',txt)
        self.assertIn('class="ha-summary"',txt)
        self.assertIn('class="ha-check-grid"',txt)
        self.assertIn('class="ha-cols"',txt)
        self.assertIn('{% for item in cyber_agent.checks %}',txt)
        self.assertIn('lang="{{ lang }}"',txt)
        self.assertIn('aria-current=',txt)
        self.assertNotIn('subprocess',txt)
        self.assertNotIn('sudo ',txt)
        self.assertNotIn('<script',txt)

    def test_overlay_preserves_acl_and_stages_only(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp)
            core=base/"core"
            out=base/"preview"
            controller=core/"backup/cyber_agent.py"
            template=core/"backup/templates/backup/cyber_agent.html"
            controller.parent.mkdir(parents=True,exist_ok=True)
            template.parent.mkdir(parents=True,exist_ok=True)
            source='''from django.http import HttpResponseForbidden
def dashboard(request):
    if not request.session.get("userID"):
        return HttpResponseForbidden("login")
    return httpProc(request,"backup/cyber_agent.html",dashboard_context(),"admin").render()
'''
            controller.write_text(source)
            template.write_text("old agent console")
            manifest=prepare(core,out)
            self.assertEqual(manifest["production_changes"],0)
            self.assertTrue(manifest["preserves_installed_admin_acl"])
            staged=(out/"backup/cyber_agent.py").read_text()
            self.assertIn('request.session.get("userID")',staged)
            self.assertIn('django_language',staged)
            self.assertIn('localized_check(item, lang)',staged)
            self.assertNotIn('csrf_exempt',staged)
            self.assertEqual(controller.read_text(),source)
            self.assertEqual(template.read_text(),"old agent console")
            with self.assertRaises(ValueError):
                prepare(core,out)

if __name__=="__main__":
    unittest.main()
