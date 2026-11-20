"""Full-product English-first language middleware (staging integration).

Use this INSTEAD OF django.middleware.locale.LocaleMiddleware in CyberCP.settings
after verifying the installed Core's middleware ordering. English is the default
regardless of browser Accept-Language. Persian is set via Django's standard,
CSRF-protected POST set_language view and the django_language cookie.

This middleware changes NO language preference by GET, URL query, browser
headers or arbitrary HTML injection. It leaves API payloads and raw HTTP
responses unmodified. Translation catalogs must be installed separately.
"""
from __future__ import annotations

from django.conf import settings
from django.middleware.locale import LocaleMiddleware
from django.utils import translation

PRODUCT_LANGUAGES = ("en", "fa")


def selected_language(cookie_value: object) -> str:
    """Accept only an explicitly selected supported language, default EN."""
    return cookie_value if isinstance(cookie_value, str) and cookie_value in PRODUCT_LANGUAGES else "en"


class EnglishFirstLocaleMiddleware(LocaleMiddleware):
    def process_request(self, request):
        cookie_name = settings.LANGUAGE_COOKIE_NAME
        language = selected_language(request.COOKIES.get(cookie_name))
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()

    # LocaleMiddleware.process_response applies Content-Language and Vary.
    # Delegating to it keeps normal Django cache and language headers intact.
