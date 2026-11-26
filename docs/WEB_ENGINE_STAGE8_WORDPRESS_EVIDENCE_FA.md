# مرحله هشتم — WordPress / WooCommerce واقعی، ۲۶ نوامبر ۲۰۲۶

## روش
نسخه‌های دریافتی از API رسمی WordPress.org: WordPress 7.1.5، WooCommerce 11.3.1، LiteSpeed Cache 7.9.4. checksum هسته 3783 فایل، WooCommerce 5454 و LiteSpeed Cache 321 فایل تأیید شد؛ برای فایل ترجمه افزونه LiteSpeed یکی از چند هش منتشرشده مطابقت داشت. فایل‌های اضافه یا نامطابق در دو افزونه مشاهده نشد. بسته‌های Ubuntu FPM 8.1.2-1ubuntu2.29 و افزونه‌های PHP و OLS 1.9.4-3+jammy با metadata محلی apt تطبیق و صرفاً استخراج شدند. نسخه FPM فقط آزمایشی است؛ برای تولید انتخاب نشده است.

MariaDB 10.11.19 موجود به صورت نمونه مستقل با datadir و Unix socket جدید، شبکه خصوصی، skip-networking، innodb-buffer-pool-size=32M، سقف 256MiB و زمان اجرای حداکثر 5min اجرا شد. تلاش اول init به علت /tmp فقط‌خواندنی رد شد، تکرار با tmp خصوصی موفق. پایگاه داده و کاربر تصادفی مستقل، داده مصنوعی، هیچ اتصال به DB تولید. WP-CLI با PHP 8.4 موجود در محیط غیر root و شبکه خصوصی اجرا شد. نصب هسته و فعال‌سازی هر دو افزونه موفق. مسیرهای تولید در runtime HTTP غیرقابل دسترس. OLS و Apache و FPM در PID/network/tmp خصوصی با سقف کلی 384MiB و 55% یک CPU. اجرای FPM ondemand، max_children=2. هیچ بسته نصب و هیچ سایت عملیاتی تغییر نکرد.

## HTTP بدون کش
صفحه اصلی حاوی عنوان مصنوعی، wp-login.php 200، REST محصولات WooCommerce 200 (آرایه خالی)، REST cart 200 (JSON)، wp-config.php 403. این فقط smoke test است.

## کش واقعی افزونه
در wp-config آزمایشی ثابت‌های LITESPEED_SERVER_TYPE=OLS، LITESPEED_ALLOWED=true و LSWCP_ESI_SUPPORT=false به صورت server-owned تنظیم شدند؛ Apache هدرهای ورودی X-LSCACHE و X-LSCACHE-VARY-VALUE را حذف کرد. این کار اثبات پاکسازی همه هدرها نیست. تنظیمات افزونه با CLI: cache-priv/rest/page_login/guest/esi=0، cache=1. OLS سیاست مرحله هفتم را فقط برای GET / بدون Cookie، Authorization، query، Cache-Control، Pragma اجرا کرد؛ بقیه modcache=0. بدون اجبار TTL در rewrite. صفحه اصلی پس از readiness (که کش را گرم کرده بود) دو بار HIT و HTTP200، اندازه 75435 bytes. 8/8 smoke bypass: دو Cookie مصنوعی، Authorization مصنوعی، no-cache، query، login، REST products و cart، همگی بدون HIT و HTTP200. REST و login هدر no-cache/no-store داشتند. پاسخ صفحه عمومی در bypass هدر اختصاصی public,max-age=604800 داشت؛ TTL واقعی کش و سازوکار ابطال باید جداگانه اندازه‌گیری و محدود شوند؛ default TTL ما تضمین سقف نیست.

## محدودیت‌ها
Cookie مصنوعی و Authorization مصنوعی جایگزین ورود واقعی دو کاربر نیستند؛ cart خالی، بدون محصول، checkout، تراکنش یا تغییر قیمت/محتوا. هیچ آزمون purge/invalidation، cache key چندمستأجره، benchmark واقعی CPU/RAM/latency، TLS/SNI، یا امنیت کامل انجام نشد. کش ترکیبی همچنان در renderer و admission planner مسدود است. فرم Create Website هنوز عملیاتی نیست. اجرای اول download command به خاطر INVALID_TIMEOUT قبل از اجرا رد شد؛ محدودیت زمان رعایت و مراحل جدا شدند. هش ترجمه افزونه با بررسی همه هش‌ها رفع شد. readiness اولیه ممکن است connection refused بدهد؛ HTTP نهایی و cache probe exit=0 بودند.

## پاک‌سازی
همه transientها، socketها، listenerهای میزبان و پردازش‌ها بررسی؛ MariaDB آزمایشی متوقف و تمام fixture حذف شد. وضعیت ساعت 14:50:40 UTC: RAM available 1802MiB، Swap free 1459MiB از 3071MiB، ذخیره 1GiB بدون مصرف، دیسک 87%. نمونه پایش 14:50:02: OOM صفر، سایت‌های پایش‌شده سالم، memory PSI60=0.30%، CPU PSI60=40.57% (نمونه لحظه‌ای و نه benchmark). خدمات OLS/Docker/MariaDB/monitor فعال.

مرحله بعد: آزمون ورود واقعی، cart دو نشست با محصولات مصنوعی، purge/invalidation و سقف TTL، TLS و امنیت هدر، benchmark کنترل‌شده، provisioning/rollback و اتصال فرم با RBAC/CSRF. Draft؛ عدم merge/deploy تا تکمیل شروط. هیچ entitlement تجاری تغییر نکرد.
