# HooshDigital Infrastructure 2027 — نسخه توسعه‌ای

این شاخه توسعه برای انتشار سورس و بررسی مستقل آماده شده است؛ انتشار کد به معنی نصب همه موتورها یا تأیید Production نیست.

## مسیر ارتقا
- Web Engine Manager: برنامه‌ریز منابع و renderer آزمایشی مستقل برای OpenLiteSpeed، Apache/PHP-FPM و مسیر توسعه سایر runtimeها. نتایج ۸ مرحله در مستندات WEB_ENGINE_STAGE ثبت شده‌اند. provisioning، مالکیت tenant، RBAC/CSRF و rollback اجرایی هنوز شرط انتشار عملیاتی هستند.
- Linux: Ubuntu 22.04 HWE 6.8؛ MGLRU، ZSWAP shrinker، cgroups v2. فعال شدن کرنل جدید وابسته به بوت برنامه‌ریزی‌شده و بررسی کنسول بازیابی است.
- Memory: حفظ Swap و فشرده‌سازی کم‌مصرف؛ تغییر allocator به zsmalloc روی کرنل مناسب، ZSTD پس از مقایسه بار CPU. بدون swapoff اجباری.
- Web: OpenLiteSpeed 1.9.4، نسخه بازگشت و پشتیبان تنظیمات پیش از تغییر. PHP پشتیبانی‌شده و مهاجرت مرحله‌ای هر سایت. Apache فقط در صورت نیاز، FrankenPHP برای برنامه‌های سازگار.
- Cache: سیاست fail-closed. کش خصوصی خاموش، allowlist دقیق، modcache=0 برای درخواست حساس، بدون اجبار TTL. آزمون‌های واقعی ورود، cart، purge و سقف TTL هنوز لازم‌اند.
- Docker: live-restore، گردش لاگ، BuildKit/multi-stage، registry و نگهداری تصاویر با digests و rollback. هیچ حذف خودکار یا prune در این release.
- Database: حفظ MariaDB پایدار؛ مهاجرت Valkey نیازمند نسخه سازگار، backup و سنجش workload.
- Storage: استفاده از Restic موجود، مقصد مستقل و encrypted backup؛ retention فقط بعد از تأیید مقصد و بازیابی.
- OS: Ubuntu LTS جدید از مسیر مهاجرت مستقل، نه ارتقای بی‌برنامه سرور Production.

`python3 scripts/infra_inventory.py` گزارشی فقط‌خواندنی و بدون اطلاعات مشتری یا secrets از نسخه‌ها، ظرفیت و وضعیت Docker ارائه می‌کند؛ از root استفاده نکنید مگر برای عملیات دیگری که مجوز مستقل دارد.

## سیاست انتشار
این نسخه توسعه‌ای برای بررسی کد است. هیچ نصب خودکار، دستکاری Premium، انتشار کلید یا داده مشتری، یا فعال‌سازی خودکار موتور ترکیبی ندارد. تست جامع به مرحله بعد منتقل شده است؛ کنترل حداقلی سلامت و rollback پیش از هر تغییر واقعی لازم است.
