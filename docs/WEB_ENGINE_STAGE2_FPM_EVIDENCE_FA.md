# Hoosh Web Engine Manager — شواهد مرحله دوم (۲۶ نوامبر ۲۰۲۶)

## وضعیت
آزمون runtime ایزوله Apache و PHP-FPM موفق؛ هنوز ماژول provisioning، reverse proxy OpenLiteSpeed و فرم اجرایی آماده انتشار نیستند. هیچ بسته‌ای نصب نشده و هیچ فایل پیکربندی یا سرویس تولید تغییر نکرد.

## روش و شواهد
- Apache بومی 2.4.52 (بسته توزیع Ubuntu)؛ mod_proxy_fcgi و MPM event.
- بسته PHP-FPM 8.1.2-1ubuntu2.29 از مخزن Ubuntu دریافت، SHA256 با metadata محلی apt تطبیق داده و صرفاً با dpkg-deb -x استخراج شد. این نسخه فقط fixture آزمون است، نه نسخه پیشنهادی تولید.
- Apache و FPM با حساب‌های غیر root جداگانه و واحدهای transient systemd در شبکه خصوصی اجرا شدند؛ سقف حافظه هر واحد 128 MiB، سهم CPU هر واحد 25% یک هسته.
- سوکت یونیکس mode 0660 و دسترسی گروهی محدود؛ FPM با pm=ondemand، max_children=2، idle_timeout=5s، memory_limit=32M برای fixture.
- CONFIG_SYNTAX_OK، FPM_HTTP_OK، PHP_EXECUTION_OK، PRIVATE_FILE_DENIED، HTACCESS_REWRITE_OK، DOTFILE_403_OK، MISSING_PHP_404_OK.
- آزمون اول بیکاری پس از 6 ثانیه هنوز دو task نشان داد. در تکرار، قبل از درخواست یک task، بعد از درخواست دو task و پس از 12 ثانیه دوباره یک task ثبت شد.
- حافظه cgroup در نمونه دوم: Apache حدود 2.64 MiB؛ FPM قبل و بعد بیکاری 3.16 MiB، بعد درخواست 3.73 MiB. این ارقام فقط نمونه کوتاه اجرای ساده با PHP بدون افزونه هستند؛ مصرف سایت واقعی، سقف ظرفیت یا benchmark سرعت نیستند.
- پس از توقف واحدها، نبود سوکت/شنونده میزبان بررسی شد؛ فایل‌های موقت حذف شدند. سلامت سرویس‌ها و سایت‌های مانیتورشده برقرار بود.

## موانع و مرحله بعد
- فایل خصوصی fixture با مالکیت root قابل خواندن نبود؛ این آزمون به معنی اثبات جداسازی کامل دو مشتری نیست. آزمون دو مستأجر، مالکیت فایل، گروه‌ها، سوکت‌ها، symlink و جداسازی document root ضروری است.
- OLS موجود در پاسخ به بررسی گزینه‌های اجرا اعلام کرد نمونه اصلی در حال اجراست. نمونه دوم اجرا نشد. محیط مستقل با PID، مسیرهای موقت، shm، config، listener و شبکه جداگانه ضروری است. مرجع رسمی: https://docs.openlitespeed.org/config/reverseproxy/
- PHP پشتیبانی‌شده و سازگار با برنامه، proxy headers و Host، HTTPS، cache privacy، RBAC/CSRF، ایجاد/حذف تراکنشی سایت، rollback و load test باید قبل از فعال‌سازی فرم تکمیل شوند.
- هیچ entitlement تجاری یا شرط Premium دستکاری نشده است.
