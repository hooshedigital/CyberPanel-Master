"""WHMCS management workspace PRESENTATION only.

WHMCS remains the sole authority for clients, invoices, payment and orders.
No iframe, undocumented WHMCS endpoint, secret, impersonation or SSO is used.
The admin launch opens its existing independently authenticated interface.
"""
from __future__ import annotations

from master_extensions.commerce_modules import modules_for

TABS = ("billing", "catalog", "packages", "provisioning", "affiliates", "identity")


def whmcs_workspace(lang: str, selected: object, admin_url: str | None) -> dict:
    """Stable localized internal tab selection; never derive external URLs."""
    if lang not in ("en", "fa"):
        raise ValueError("unsupported language")
    modules = {module["id"]: module for module in modules_for(lang)}
    current = selected if isinstance(selected, str) and selected in TABS else "billing"
    return {
        "selected_id": current,
        "selected": modules[current],
        "tabs": [modules[key] for key in TABS],
        "admin_url_configured": bool(admin_url),
        # HTTPS admin URL configuration is NOT a live network/auth check.
        "integration_verified": False,
        "operations_enabled": False,
    }
