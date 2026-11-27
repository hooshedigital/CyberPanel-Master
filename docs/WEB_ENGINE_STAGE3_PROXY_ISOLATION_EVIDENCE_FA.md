# Hoosh Web Engine Manager — شواهد مرحله سوم (۲۶ نوامبر ۲۰۲۶)

## وضعیت
زنجیره کامل OpenLiteSpeed 1.9.4 → Apache MPM Event → PHP-FPM در محیط موقت و جداشده برای دو سایت مصنوعی پاسخ موفق داد. این آزمون نه نصب Production است و نه پیاده‌سازی provisioning. نسخه اصلی OpenLiteSpeed 1.9.2 بدون تغییر باقی ماند.

## دو مستأجر
- دو UID/GID عددی بلااستفاده 62001 و 62002 بدون ساخت حساب دائمی؛ اجرای غیر root با setpriv و clear-groups.
- دو FPM مستقل، Unix socket با مالک مستأجر و گروه proxy (33)، mode 0660؛ پوشه سوکت 2750، فایل خصوصی 0600 و پوشه خصوصی 0700.
- Apache با www-data، MPM event، vhostهای جداگانه و default deny. FPM از بسته Ubuntu 8.1 آزمایشی استخراج شد.
- آزمون نهایی مستقیم Apache: هر دو سایت فایل خصوصی خودشان را خواندند، خواندن فایل خصوصی دیگری و اتصال به سوکت دیگری رد شد، rewrite موفق، .htaccess با 403 رد شد، Host ناشناخته 403.
- دو تلاش نخست با اشکال قالب‌بندی اسکریپت تست متوقف شدند؛ تکرار نهایی تمام assertionهای فوق را گذراند. systemd مستقیماً UID بدون حساب را نپذیرفت؛ setpriv در واحد transient جایگزین شد.

## زنجیره کامل
- بسته openlitespeed 1.9.4-3+jammy از مخزن LiteSpeed دریافت، SHA256 با metadata apt تطبیق و فقط استخراج شد. بسته نصب نشد.
- مسیر Production از sandbox غیرقابل دسترس، PID و شبکه خصوصی، /tmp و /run و /dev/shm مجزا، اجرای غیر root. Apache و OLS در یک شبکه خصوصی و FPM با سوکت یونیکس.
- OLS listener خصوصی، دو Host آزمایشی به Apache backend واحد و vhostهای مستقل هدایت شدند.
- FULL_PROXY_CHAIN_TWO_TENANTS_OK: پاسخ صحیح PHP برای هر دو نام دامنه، رد خواندن فایل و سوکت مستأجر دیگر؛ PROXY_DOTFILE_DENIED: 403 برای .htaccess هر دو.
- هشدارهای runtime: تلاش ایجاد فایل پشتیبان config در filesystem فقط‌خواندنی رد شد؛ هشدار حداقل UID/GID ریشه vhost در محیط آزمایشی. configtest با خروجی صفر اما همراه پیام عدم مجوز usermod و نوشتن فایل پایان یافت. این هشدارها باید برای پیکربندی نهایی رفع شوند؛ موفقیت HTTP مستقل از آن‌ها مشاهده شد.
- سقف آزمایشی: دو واحد FPM هرکدام 96 MiB و 20% یک CPU، واحد Apache+OLS 256 MiB و 35% یک CPU. این‌ها سقف هستند، نه مصرف اندازه‌گیری‌شده یا benchmark.
- پس از آزمون، توقف واحدها، نبود listener میزبان، سوکت و پردازش هر دو UID تأیید و تمام fixtureهای موقت حذف شدند. سرویس‌ها و سلامت سایت‌های مانیتورشده برقرار بودند؛ OOM ثبت‌شده صفر.

## شروط انتشار
این نتایج صرفاً جداسازی فایل و socket در fixture و مسیر HTTP را اثبات می‌کنند. نیازمند آزمون isolation با فایل‌های واقعی/گروه و symlink، پروفایل PHP پشتیبانی‌شده، Host و SNI نامعتبر در OLS، headerهای قابل جعل، HTTPS، کش و دو نشست، load test، RBAC/CSRF و عملیات تراکنشی ساخت/حذف سایت و rollback. فرم فعلی هنوز پیش‌نمایش غیرفعال است. هیچ قابلیت تجاری یا license flag دستکاری نشده است.

مرجع رسمی reverse proxy: https://docs.openlitespeed.org/config/reverseproxy/
