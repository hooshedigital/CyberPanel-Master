import unittest
import json
import os
import tempfile
from pathlib import Path
from urllib.parse import parse_qs

from master_extensions.turnstile_core import verify_token, SITEVERIFY
from master_extensions.i18n import resolve_language, context_for, LABELS
from master_extensions.version import label, MASTER_VERSION
from master_extensions.login_captcha import _extract_token, _read_secret, TurnstileLoginMiddleware
from master_extensions import login_captcha
from master_extensions.turnstile_core import TurnstileResult
from unittest.mock import patch

class FakeResponse:
    status = 200
    def __init__(self, value): self.value = json.dumps(value).encode()
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self,n): return self.value[:n]

class MasterSecurityTests(unittest.TestCase):
    def test_turnstile_scope(self):
        def result(value):
            def opener(req, timeout):
                self.assertEqual(req.full_url, SITEVERIFY)
                self.assertEqual(parse_qs(req.data.decode())["secret"], ["test-secret"])
                return FakeResponse(value)
            return verify_token("test-token","test-secret",
                                hostname="manage.hooshedigital.ir",opener=opener)
        self.assertTrue(result({"success":True,"hostname":"manage.hooshedigital.ir","action":"cyberpanel_login"}).ok)
        for value in (
            {"success":False}, {"success":True,"hostname":"elsewhere.invalid","action":"cyberpanel_login"},
            {"success":True,"hostname":"manage.hooshedigital.ir","action":"other"}
        ):
            self.assertFalse(result(value).ok)

    def test_fail_closed_timeout(self):
        def fail(*args,**kwargs): raise TimeoutError()
        self.assertFalse(verify_token("token","secret",hostname="manage.hooshedigital.ir",opener=fail).ok)
        self.assertFalse(verify_token("", "secret",hostname="manage.hooshedigital.ir").ok)
        self.assertFalse(verify_token("x"*2049,"secret",hostname="manage.hooshedigital.ir").ok)

    def test_secret_permissions(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"secret"
            p.write_text("dummy-secret")
            os.chmod(p,0o644)
            with self.assertRaises(ValueError): _read_secret(str(p))
            os.chmod(p,0o640)
            self.assertEqual(_read_secret(str(p)),"dummy-secret")

    def test_login_payload(self):
        class Request:
            META={"CONTENT_TYPE":"application/json"}
            POST={}
            body=b'{"captcha_token":"test-token","password":"no-log"}'
        self.assertEqual(_extract_token(Request()),"test-token")
        class Bad(Request):
            body=b'{"password":"no-token"}'
        self.assertIsNone(_extract_token(Bad()))
        class TooLong(Request):
            body=b"x"*20000
        self.assertIsNone(_extract_token(TooLong()))

    def test_disabled_captcha_never_changes_login(self):
        class Request:
            method="POST"
            path="/verifyLogin"
        with patch.object(login_captcha,"_config",return_value={"enabled":False}):
            result=TurnstileLoginMiddleware(lambda r:"normal-login")(Request())
        self.assertEqual(result,"normal-login")

    def test_enabled_captcha_invalid_route_denies_posts_not_get(self):
        class Request:
            path="/verifyLogin"
            method="POST"
        middleware=TurnstileLoginMiddleware(lambda r:"normal-login")
        with patch.object(login_captcha,"_config",return_value={"enabled":True,"login_post_path":"broken"}), patch.object(login_captcha,"flag_enabled",return_value=True), patch.object(TurnstileLoginMiddleware,"_deny",return_value="blocked"):
            self.assertEqual(middleware(Request()),"blocked")
            Request.method="GET"
            self.assertEqual(middleware(Request()),"normal-login")

    def test_enabled_valid_login_post_requires_verified_token(self):
        class Request:
            session={}
            method="POST"
            path="/verifyLogin"
            META={"REMOTE_ADDR":"127.0.0.1","CONTENT_TYPE":"application/json"}
            body=b'{"captcha_token":"test-challenge"}'
            def get_host(self): return "manage.hooshedigital.ir"
        conf={"enabled":True,"login_post_path":"/verifyLogin","hostname":"manage.hooshedigital.ir","secret_file":"/private/test"}
        middleware=TurnstileLoginMiddleware(lambda r:"authenticated-by-core")
        with patch.object(login_captcha,"_config",return_value=conf), patch.object(login_captcha,"flag_enabled",return_value=True), patch.object(login_captcha,"_read_secret",return_value="secret"), patch.object(login_captcha,"verify_token",return_value=TurnstileResult(False,"challenge_failed")),patch.object(TurnstileLoginMiddleware,"_deny",return_value="blocked"):
            self.assertEqual(middleware(Request()),"blocked")
        with patch.object(login_captcha,"_config",return_value=conf), patch.object(login_captcha,"flag_enabled",return_value=True), patch.object(login_captcha,"_read_secret",return_value="secret"), patch.object(login_captcha,"verify_token",return_value=TurnstileResult(True,"verified")):
            self.assertEqual(middleware(Request()),"authenticated-by-core")

    def test_enabled_without_root_marker_preserves_existing_login(self):
        class Request:
            method="POST"
            path="/verifyLogin"
        with patch.object(login_captcha,"_config",return_value={"enabled":True}), patch.object(login_captcha,"flag_enabled",return_value=False):
            self.assertEqual(TurnstileLoginMiddleware(lambda r:"existing-login")(Request()),"existing-login")

    def test_authenticated_session_skips_revalidation(self):
        class Request:
            method="POST"
            path="/verifyLogin"
            session={"userID": 12}
        conf={"enabled":True,"login_post_path":"/verifyLogin"}
        with patch.object(login_captcha,"_config",return_value=conf), patch.object(login_captcha,"flag_enabled",return_value=True):
            self.assertEqual(TurnstileLoginMiddleware(lambda r:"already-authenticated")(Request()),"already-authenticated")

    def test_i18n(self):
        self.assertEqual(resolve_language(None,None),"en")
        self.assertEqual(resolve_language("fa","en"),"fa")
        self.assertEqual(resolve_language("../fa","en"),"en")
        self.assertEqual(context_for("fa")["direction"],"rtl")
        self.assertEqual(context_for("en")["direction"],"ltr")
        self.assertEqual(set(LABELS["en"]),set(LABELS["fa"]))

    def test_versions_separate(self):
        value=label("3.0 build 4")
        self.assertIn("CyberPanel Master v"+MASTER_VERSION,value)
        self.assertIn("CyberPanel Core 3.0 build 4",value)

if __name__=="__main__":unittest.main()
