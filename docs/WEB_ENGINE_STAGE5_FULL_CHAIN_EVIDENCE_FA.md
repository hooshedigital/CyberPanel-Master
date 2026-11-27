# شواهد مرحله پنجم — ۲۶ نوامبر ۲۰۲۶

## نتیجه
تمام زنجیره با شش فایل پیکربندی تولیدشده توسط renderer نسخه 3be5a0898c0a1b792112c096a38b3b4aef7a0f94 اجرا شد. این یک آزمون مستقل staging است، نه تغییر Production.

- هفت آزمون هدفمند renderer موفق؛ SHA256 تمام فایل‌های تولیدشده قبل از اجرا کنترل شد.
- بسته‌های Ubuntu PHP-FPM 8.1 و OpenLiteSpeed 1.9.4 دریافت و هش هر دو با metadata محلی apt تطبیق داده شد. فقط استخراج؛ بدون نصب یا اجرای maintainer scripts.
- Apache و دو FPM configtest موفق؛ اجرای غیر root، UIDهای مستقل، socket mode 0660، شبکه و PID خصوصی، مسیر OLS اصلی غیرقابل دسترس، /tmp و /run و shm جدا، سقف منابع واحدهای transient.
- برای هر دو Host آزمایشی، مسیر OLS → Apache → FPM درست، خواندن فایل خصوصی خودش موفق، خواندن فایل و اتصال به سوکت مستأجر دیگر رد شد.
- دو Cookie مصنوعی مستقل برای هر Host، پاسخ متناسب با Cookie، Cache-Control: private, no-store حفظ شد. کش در renderer غیرفعال است؛ این آزمون امنیت کش فعال را اثبات نمی‌کند.
- .htaccess، source.php.bak و symlink آزمایشی از طریق OLS برای هر دو سایت HTTP 403؛ Host ناشناخته HTTP 404 بدون داده خصوصی.
- درخواست Host=a.tenant.test همراه X-Forwarded-Host=b.tenant.test به tenant A رسید؛ Host اصلی حفظ شد. این تست فقط عدم تغییر مسیریابی در همین حالت را اثبات می‌کند، نه پاکسازی یا اعتبارسنجی همه forwarded headers.
- ریشه vhostهای fixture با UID مناسب تنظیم شد؛ هشدار حداقل UID/GID مرحله سوم در اجرای نهایی مشاهده نشد. هشدار تلاش کپی config به conf0 در filesystem فقط‌خواندنی همچنان وجود داشت؛ پاسخ HTTP مستقل از هشدار موفق بود.
- پس از آزمون تمام واحدهای FPM، socket، listener و پردازش UIDهای آزمایشی بررسی و fixture حذف شد. OLS اصلی 1.9.2 بدون تغییر؛ سایت‌های مانیتورشده سالم، OOM صفر.
- نمونه نهایی RAM قابل استفاده 1737 MiB، swap آزاد 1536 MiB از 3071 MiB، ذخیره 1 GiB بدون مصرف؛ دیسک 87% همچنان warning. این نمونه benchmark قبل/بعد موتور نیست.

## موانع انتشار
HTTPS/SNI و header trust boundary، کش فعال و محرمانگی نشست‌ها، قواعد محدود rewrite برای htaccess، PHP پشتیبانی‌شده و سازگار، مالکیت tenant واقعی، load benchmark، تراکنش provisioning و rollback، RBAC/CSRF و اتصال فرم هنوز باقی مانده‌اند. هیچ entitlement تجاری یا تنظیمات سایت موجود تغییر نکرده است.
