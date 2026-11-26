# HooshDigital Infrastructure 2027 — وضعیت استقرار و شروط پایان

۲۶ نوامبر ۲۰۲۶. انتشار توسعه‌ای؛ اجزای نصب‌شده و آماده، با اجزای هنوز غیرعملیاتی تفکیک شده‌اند.

## تکمیل‌شده
- ZSWAP allocator از zbud به zsmalloc در زمان اجرا تغییر یافت؛ بدون swapoff و reboot. صفحات قبلی به تدریج آزاد می‌شوند. LZO و سقف 15% حفظ شدند؛ ZSTD هنوز فعال نیست. فایل GRUB drop-in و grub-script-check موفق، سه کرنل حفظ شدند.
- OpenLiteSpeed 1.9.4، Docker Live Restore، Buildx 0.30.1/BuildKit 0.26.2 و پایش منابع عملیاتی.
- FrankenPHP 1.14.0 و Valkey 8.1.12 به صورت نسخه‌بندی‌شده و templateهای محدودیت منابع نصب شدند. اجرای خصوصی مصنوعی تأیید؛ پروژه واقعی هنوز منتقل نشده.
- GHCR: GitHub Actions run 45859372070 و همه مراحل build/smoke/publish موفق. Image: ghcr.io/hooshedigital/cyberpanel-master/valkey-cache:8.1.12-jammy-amd64؛ digest sha256:cf7969167686deab32a7c005aea6ac1ddf4cc1bedac0371cf1a5bf4d37432913. داده یا credential تولید در Image نیست. انتشار Image تأیید شد؛ دسترسی pull از سرور و visibility بسته هنوز تأیید نشده.
- دو کرنل منسوخ پاک شدند؛ کرنل جاری 5.15.0-202، جایگزین 5.15.0-204 و HWE 6.8.0-149 حفظ.

## مقایسه نمونه‌های پایش
ابتدا 13:05–13:15 UTC (11 نمونه) در برابر 16:15–16:32 UTC (17 نمونه)، میانه RAM available 1206.64→1930.58 MiB؛ Swap used 2426.30→1582.71 MiB؛ CPU some PSI60 60.60→25.28؛ memory PSI60 0.33→0.01؛ IO PSI60 0.72→0.37. OOM صفر. بار کاری یکسان نبوده؛ این داده‌ها اثبات benchmark سرعت یا اثر مستقل zsmalloc نیستند.

## موانع پایان
1. HWE نصب‌شده هنوز boot نشده؛ برای MGLRU و ZSWAP shrinker نیاز به پنجره ریبوت و تأیید کنسول مستقل ارائه‌دهنده است. SSH و MCP وابسته به سلامت OS هستند.
2. PHP 8.4/8.5: simulation شامل 31 ارتقا و صفر حذف/نصب جدید؛ مسیر بررسی‌شده بسته‌های بازگشت lsphp84 8.4.25 و lsphp85 8.5.10 HTTP404 داد. هیچ ارتقای PHP انجام نشد؛ بازیابی معتبر و سازگاری افزونه‌ها لازم.
3. Hybrid Apache/FrankenPHP: مسیر خصوصی HTTP آزموده شده، اما production provisioning، سوکت/ACL lifecycle، TLS/SNI، header trust، isolation و فرم عملیاتی هنوز تکمیل نشده‌اند. قابلیت Premium تغییر نکرده؛ فرم فقط گزارش آمادگی است.
4. مهاجرت Valkey و پروژه واقعی نیازمند انتخاب workload و rollback مستقل؛ Redis تولید بدون تغییر.
5. ZSTD پس از اندازه‌گیری workload روی دو CPU؛ مهاجرت Ubuntu جدید فقط با میزبان/مسیر مستقل. دیسک هنوز حدود 89% اشغال است.
6. هیچ تغییر عمومی DNS، حذف بکاپ مشتری یا rollout بدون تأیید انجام نشده است.

این سند اعلام اتمام همه ارتقاها نیست؛ شرایط لازم برای پایان مشخص شده‌اند.
