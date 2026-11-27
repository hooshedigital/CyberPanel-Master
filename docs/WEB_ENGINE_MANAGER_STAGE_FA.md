# Hoosh Web Engine Manager — مرحله اول آزمایشی

این نسخه برنامه‌ریز مستقل منابع و پیش‌نمایش فرم است؛ هنوز هیچ موتور جدیدی از فرم ایجاد نمی‌شود. مسیر قبلی ساخت سایت و شرط تجاری Premium بدون تغییر می‌مانند.

OpenLiteSpeed Native پیش‌فرض است. Apache فقط برای نیاز واقعی سازگاری با listener محدود به loopback، PHP-FPM مستقل هر سایت و reverse proxy کنترل‌شده بررسی می‌شود. FrankenPHP و Docker برای برنامه‌های سازگار در نظر گرفته شده‌اند. هیچ بسته‌ای نصب یا فعال نمی‌شود.

برنامه‌ریز صرفاً با نقش مدیر و اطلاعات منابع و آمادگی از سمت سرور کار می‌کند. ظرفیت‌های حافظه برآورد طراحی هستند، نه محدودیت اعمال‌شده. حاشیه RAM و Swap و دیسک و PSI بررسی می‌شود. کش عمومی تنها پس از آزمون سازگاری و محرمانگی؛ کش خصوصی غیرفعال.

## آزمون
`python3 -m unittest master_extensions.tests.test_web_engine -v`
`python3 scripts/stage_web_engine_form.py --source /path/to/createWebsite.html --output /path/to/new-preview.html`

فایل خروجی فقط پیش‌نمایش است؛ گزینه‌ها تا اتصال واقعی غیرفعال هستند. هیچ endpoint اجرایی، shell یا تغییر Production وجود ندارد.

## معیار پذیرش مرحله بعد
- Apache ایزوله: loopback، عدم دسترسی بین سایت‌ها، PHP-FPM اختصاصی، configtest و مصرف منابع.
- OpenLiteSpeed proxy: Host/SNI، headers، timeout، HTTPS، rewrite و عدم تداخل با سایت‌های موجود.
- کش با دو نشست مستقل: login/cart/checkout/admin/API و صفحات خصوصی؛ عدم نشت داده.
- اتصال فرم با اعتبارسنجی سمت سرور، RBAC/CSRF، تراکنش ساخت سایت، rollback و تأیید مالک.
- مقایسه منابع و latency تحت بار یکسان. کرنل، سیستم‌عامل و Valkey مسیرهای جداگانه‌اند.

هیچ license flag یا کد تجاری بازنویسی نمی‌شود.
