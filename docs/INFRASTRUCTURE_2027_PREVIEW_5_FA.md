# Infrastructure 2027 — Preview 5

۲۶ نوامبر ۲۰۲۶ — کاهش فضای مصرفی و آماده‌سازی Valkey.

- حذف دقیق شش بسته image/modules/modules-extra متعلق به دو کرنل قدیمی 5.15.0-190 و 5.15.0-191 پس از simulation؛ بدون reboot، بدون تغییر سرویس‌های سایت. فضای آزاد از 10329382912 به 11550490624 bytes رسید (+1221107712 bytes، حدود 1.14 GiB). سه کرنل 5.15.0-202 (running)، 5.15.0-204 (fallback)، 6.8.0-149 (installed) و initramfsهای آن‌ها حفظ شدند. grub-script-check موفق. بازیابی نسخه‌های حذف‌شده وابسته به موجود بودن بسته رسمی است.
- HWE هنوز boot نشده. کنسول مستقل ارائه‌دهنده تأیید نشده؛ SSH و MCP به سلامت سیستم‌عامل وابسته‌اند. پیش از reboot، دسترسی کنسول و پنجره نگهداری تأیید شوند. پس از boot ابتدا MGLRU و ZSWAP shrinker، فشار منابع و سلامت سرویس‌ها سنجیده شود؛ سپس zsmalloc و ZSTD جداگانه بررسی شوند. در این مرحله allocator و compressor تغییر نکردند.
- GitHub Actions workflow جدید .github/workflows/valkey-standalone.yml برای ساخت Valkey 8.1.12 از commit رسمی 38316e6c481cc6d265ab52482223c68f63f0ac30 روی runner Ubuntu 22.04، socket smoke test و artifact دارای SHA256. بدون push به registry یا deploy؛ نتیجه build هنوز تأیید نشده. Docker Hub قبلاً 403 داده است. Redis فعلی بدون تغییر.
- وضعیت پس از عملیات: سرویس‌های اصلی فعال، مانیتور سایت‌ها healthy، OOM صفر، RAM available 1946MiB، Swap free 1458MiB، دیسک حدود 11GiB آزاد و 89% پر. Swap اضطراری 1GiB بدون مصرف.
- این نسخه Preview است. provisioning موتور ترکیبی، TLS/cache privacy، migration Valkey و FrankenPHP، reboot و تست جامع هنوز باقی مانده‌اند. هیچ قابلیت تجاری تغییر نکرده است.
