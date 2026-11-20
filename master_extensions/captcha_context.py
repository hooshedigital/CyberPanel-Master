"""Public Turnstile site key for the inspected login origin (no secret data).

Important: this *source* and the installed production middleware are not yet
verified byte-for-byte identical. Do not deploy without a separate, positive
browser login/2FA acceptance test and rollback plan.
"""
from __future__ import annotations

import re
from .login_captcha import flag_enabled

# Public key last verified in the 2026-11-18 installation report.
# This is a fallback for legacy installs; prefer CYBERMASTER_CAPTCHA["sitekey"]
# from the owner's root-managed runtime settings when rotating widgets.
VERIFIED_PUBLIC_SITEKEY_20261118 = "0x4AAAAAAGG-PjEcCDvWgNdr"
_MANAGED_KEY = re.compile(r"0x[A-Za-z0-9_-]{16,128}\Z")


def sitekey_for(config: object) -> str:
    if not isinstance(config, dict):
        return ""
    raw = config.get("sitekey", VERIFIED_PUBLIC_SITEKEY_20261118)
    return raw if isinstance(raw, str) and _MANAGED_KEY.fullmatch(raw) else ""


def captcha_context(request):
    from django.conf import settings

    config = getattr(settings, "CYBERMASTER_CAPTCHA", {})
    public_key = sitekey_for(config)
    if not isinstance(config, dict):
        config = {}
    expected_host = config.get("hostname", "manage.hooshedigital.ir")
    try:
        requested_host = request.get_host().split(":", 1)[0].lower()
    except (ValueError, TypeError):
        requested_host = ""

    # A rendered widget must correspond to an actually enabled middleware,
    # the exact application host and a valid public key.
    enabled = (
        config.get("enabled") is True
        and expected_host == "manage.hooshedigital.ir"
        and requested_host == expected_host
        and bool(public_key)
        and flag_enabled()
    )
    return {
        "cybermaster_captcha_enabled": bool(enabled),
        "cybermaster_turnstile_sitekey": public_key if enabled else "",
    }
