"""Cloudflare Turnstile server-side siteverify; never accept a client-only CAPTCHA."""
from __future__ import annotations
import json
import urllib.parse
import urllib.request
import urllib.error
from dataclasses import dataclass

SITEVERIFY = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
MAX_TOKEN_LEN = 2048

@dataclass(frozen=True)
class TurnstileResult:
    ok: bool
    reason: str

def verify_token(token: str, secret: str, *, hostname: str,
                 action: str = "cyberpanel_login", remote_ip: str | None = None,
                 timeout: float = 4.0, opener=None) -> TurnstileResult:
    if not isinstance(token, str) or not 1 <= len(token) <= MAX_TOKEN_LEN or token.strip() != token:
        return TurnstileResult(False, "missing_or_invalid_token")
    if not isinstance(secret, str) or not secret:
        return TurnstileResult(False, "missing_secret")
    if not isinstance(hostname, str) or not hostname or any(c.isspace() for c in hostname):
        return TurnstileResult(False, "invalid_hostname_config")
    payload = {"secret": secret, "response": token}
    if remote_ip:
        payload["remoteip"] = remote_ip
    req = urllib.request.Request(SITEVERIFY,
        data=urllib.parse.urlencode(payload).encode("utf-8"),
        method="POST", headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"})
    try:
        sender = opener or urllib.request.urlopen
        with sender(req, timeout=max(1.0, min(float(timeout), 10.0))) as response:
            if getattr(response, "status", 200) != 200:
                return TurnstileResult(False, "upstream_unavailable")
            raw = response.read(4097)
            if len(raw) > 4096:
                return TurnstileResult(False, "invalid_provider_response")
            result = json.loads(raw)
    except (OSError, ValueError, TypeError, urllib.error.HTTPError, json.JSONDecodeError):
        return TurnstileResult(False, "upstream_unavailable")
    if not isinstance(result, dict) or result.get("success") is not True:
        return TurnstileResult(False, "challenge_failed")
    if result.get("hostname") != hostname or result.get("action") != action:
        return TurnstileResult(False, "invalid_challenge_scope")
    return TurnstileResult(True, "verified")
