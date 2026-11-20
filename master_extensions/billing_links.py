"""Strict allowlisted navigation only: NEVER generates a WHMCS login session.

A CyberPanel administrator may open the existing WHMCS admin sign-in page.
This link does not bypass WHMCS authentication, 2FA, CSRF or IP restrictions.
"""
from __future__ import annotations

import os
from urllib.parse import urlsplit


def trusted_billing_admin_url(raw: str | None = None) -> str | None:
    """Return only an HTTPS URL on our owned domain or its subdomains.

    The path can be a nonstandard WHMCS admin directory; do not assume /admin.
    Authentication must be performed independently by WHMCS / approved IdP.
    """
    raw = os.environ.get("HOOSH_WHMCS_ADMIN_URL", "") if raw is None else raw
    if not isinstance(raw, str) or not raw or len(raw) > 2048 or raw != raw.strip():
        return None
    try:
        parsed = urlsplit(raw)
        host = (parsed.hostname or "").lower()
        # Do not allow tricks involving userinfo, nonstandard ports or query/fragment.
        if (parsed.scheme != "https" or not host or
            not (host == "hooshedigital.ir" or host.endswith(".hooshedigital.ir")) or
            parsed.username is not None or parsed.password is not None or
            parsed.port not in (None, 443) or parsed.query or parsed.fragment or
            any(ord(ch) < 32 for ch in raw) or "\\" in raw or
            "//" in parsed.path):
            return None
        return raw
    except (ValueError, TypeError, AttributeError):
        return None
