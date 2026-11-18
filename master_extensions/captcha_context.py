"""Public sitekey and per-request root-controlled activation state; never expose secret."""
from .login_captcha import flag_enabled
SITEKEY = "0x4AAAAAAGHZEUWLE0vYhl2W"

def captcha_context(request):
    return {
        "cybermaster_captcha_enabled": flag_enabled(),
        "cybermaster_turnstile_sitekey": SITEKEY,
    }
