"""CyberPanel Master commerce module registry (read-only, no remote calls).

WHMCS remains the authoritative billing/clients/affiliate engine.
CyberPanel remains hosting account control plane. VPS requires a separate provider.
This registry is *a UI roadmap*, not an assertion of production integrations.
"""
from __future__ import annotations
from typing import TypedDict


class CommerceModule(TypedDict):
    id: str
    name: str
    description: str
    stage: str
    status: str


# Implementation deliberately contains no API key, credential, URL, server action, or premium code.
_MODULES = (
    ("billing", "Billing & invoices", "صورتحساب و پرداخت",
     "WHMCS invoices, verified gateway callbacks, renewals and reconciliation",
     "فاکتورهای WHMCS، بازگشت تأییدشده درگاه، تمدید و مغایرت‌گیری", "v1"),
    ("packages", "Hosting package factory", "کارخانه پکیج هاست",
     "Versioned package templates, quotas and WHMCS-to-CyberPanel mapping",
     "قالب‌های نسخه‌دار، سهمیه‌ها و نگاشت پکیج بین WHMCS و CyberPanel", "v1"),
    ("catalog", "Product catalog", "کاتالوگ محصولات",
     "Hosting, domains, SSL, backups, add-ons and bundles",
     "هاست، دامنه، SSL، بکاپ، افزونه‌ها و بسته‌های ترکیبی", "v1"),
    ("affiliates", "Affiliates & partners", "افیلیت و همکاران فروش",
     "WHMCS-native referrals, commissions, partner programs and payouts",
     "معرف‌های WHMCS، پورسانت، نمایندگی و تسویه همکاران", "v1"),
    ("campaigns", "Promotions & growth", "کمپین و بازاریابی",
     "Promotions, coupons, cross-selling and attribution",
     "کدهای تخفیف، فروش مکمل و ردیابی کمپین", "v1"),
    ("provisioning", "Hosting provisioning", "ساخت و تحویل هاست",
     "After-payment hosting lifecycle through a scoped CyberPanel API",
     "ایجاد و مدیریت چرخه هاست پس از پرداخت با API محدود سایبرپنل", "v1"),
    ("identity", "Identity & access", "ورود و سطح دسترسی",
     "Staff/client identity, admin 2FA, scoped roles and audit",
     "هویت مشتری و مدیر، ورود دومرحله‌ای، نقش‌های محدود و ممیزی", "v1"),
    ("linux", "Linux management", "مدیریت لینوکس",
     "Approved server diagnostics and role-restricted runbooks; no web root shell",
     "عیب‌یابی امن و عملیات محدود دارای مجوز؛ بدون شل روت در وب", "v2"),
    ("vps", "VPS & dedicated servers", "فروش VPS و سرور اختصاصی",
     "Provider-backed capacity and VM lifecycle; not a built-in CyberPanel hypervisor",
     "ظرفیت و چرخه ماشین مجازی با تأمین‌کننده واقعی؛ مستقل از هسته سایبرپنل", "v2"),
)

_STATES = {
    "en": ("Planned / not connected", "Draft catalog; no live WHMCS access or provisioning"),
    "fa": ("برنامه‌ریزی‌شده / متصل نیست", "کاتالوگ اولیه؛ بدون دسترسی زنده به WHMCS یا ساخت سرویس"),
}


def modules_for(lang: str) -> list[CommerceModule]:
    if lang not in ("en", "fa"):
        raise ValueError("unsupported language")
    output: list[CommerceModule] = []
    for identifier, en, fa, en_description, fa_description, stage in _MODULES:
        output.append({
            "id": identifier,
            "name": en if lang == "en" else fa,
            "description": en_description if lang == "en" else fa_description,
            "stage": stage,
            "status": _STATES[lang][0],
        })
    return output


def status_note(lang: str) -> str:
    if lang not in _STATES:
        raise ValueError("unsupported language")
    return _STATES[lang][1]
