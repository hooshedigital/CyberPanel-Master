"""Guarded Turnstile middleware for the single, inspected CyberPanel login route.

Disabled until the exact production POST endpoint and client payload are
verified. Never bypass Django/CyberPanel authentication or existing CSRF.
"""
from __future__ import annotations
import ipaddress
import json
from pathlib import Path
from .turnstile_core import verify_token

def _config():
    from django.conf import settings
    return getattr(settings, "CYBERMASTER_CAPTCHA", {})

def _read_secret(filename):
    path = Path(filename)
    if path.is_symlink() or not path.is_file():
        raise ValueError("invalid secret path")
    st = path.stat()
    if st.st_mode & 0o007 or not 4 <= st.st_size <= 256:
        raise ValueError("insecure secret file")
    return path.read_text(encoding="utf-8").strip()

def _extract_token(request):
    content_type = request.META.get("CONTENT_TYPE","").split(";",1)[0]
    if content_type == "application/json":
        raw = request.body
        if len(raw) > 16*1024:
            return None
        try:
            data = json.loads(raw)
        except (TypeError,UnicodeError,ValueError):
            return None
        return data.get("captcha_token") if isinstance(data,dict) else None
    return request.POST.get("cf-turnstile-response") or request.POST.get("captcha_token")

def _request_ip(request):
    try:
        return str(ipaddress.ip_address(request.META.get("REMOTE_ADDR","")))
    except ValueError:
        return None

class TurnstileLoginMiddleware:
    def __init__(self,get_response):
        self.get_response = get_response

    def __call__(self,request):
        conf = _config()
        if not conf.get("enabled",False):
            return self.get_response(request)
        endpoint = conf.get("login_post_path","")
        if not isinstance(endpoint,str) or not endpoint.startswith("/") or endpoint.startswith("//"):
            return self._deny()
        if request.method != "POST" or request.path != endpoint:
            return self.get_response(request)
        try:
            secret = _read_secret(conf.get("secret_file",""))
            hostname = conf.get("hostname","manage.hooshedigital.ir")
            if request.get_host().split(":")[0].lower() != hostname:
                return self._deny()
            result = verify_token(_extract_token(request),secret,hostname=hostname,
                                  action=conf.get("action","cyberpanel_login"),
                                  remote_ip=_request_ip(request),timeout=4.0)
        except (OSError,ValueError,TypeError):
            return self._deny()
        if not result.ok:
            return self._deny()
        return self.get_response(request)

    @staticmethod
    def _deny():
        from django.http import JsonResponse
        response = JsonResponse({"captcha_required":True,"error":"captcha_verification_failed"},status=403)
        response["Cache-Control"]="no-store"
        return response
