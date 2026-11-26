# استقرار و آزمون لایه اتصال خصوصی موتورهای وب

۲۶ نوامبر ۲۰۲۶. commit 701b64eaf1b9e811ecaacbd9a63d5ec3b1d4cf6a و اصلاح warm relay در 316133b514e50738044ffeec1a7c97382e1af74a.

- حساب اختصاصی no-login hoosh-web-edge، پوشه enrollment خالی root-owned، checker، دو جفت unit socket/service و slice نصب شدند؛ systemd-analyze verify موفق. فایل provisioner از Git blob بررسی و جایگزین شد. مجوز جدید برای nobody یا www-data داده نشد.
- اولین درخواست Apache با timeout=8s شکست خورد و fixture پاک شد؛ retry با سقف 22s موفق و cold request 8.929s. PHP fpm-fcgi، سوکت ورودی 0600، سه حساب غیرمجاز رد، .env پاسخ 403، rollback تا زمان revoke رد و پس از حذف marker و توقف relay موفق.
- خروج پس از 30s بیکاری از هر دو relay حذف شد و فایل‌های جدید نصب شدند؛ سقف منابع و اتصال‌ها حفظ شد. FrankenPHP cold request 9.455s، سه warm request مصنوعی 0.006328s / 0.006136s / 0.001661s، MemoryCurrent=1282048 bytes، NRestarts=0. PHP، منع سه حساب، .env=403 و revoke/rollback موفق. نگه‌داری warm بعد از بیکاری طولانی هنوز اندازه‌گیری نشده؛ اعداد benchmark سایت عمومی نیستند. پیش‌گرم‌کردن قبل از فعال‌سازی frontend ضروری است.
- CI نهایی private engine 45878434313، safety 45878434427، UI 45878434464 و storefront 45878434308 موفق؛ Valkey standalone در زمان ثبت هنوز در جریان بود.
- تمام fixtureها پاک شدند، صفر enrollment Apache/FrankenPHP/edge و صفر journal پروژه؛ 18 کانتینر و سرویس‌های اصلی فعال. Kernel 6.8.0-149، RAM available=1774MiB، swap free=2214MiB، دیسک 9.6GiB آزاد و 90% اشغال.
- یک سایت وردپرسی قبلاً دارای Valkey در بررسی جدید به setup-config.php تغییر مسیر داد و HTTP500 گرفت؛ wp-config.php و object-cache.php در docroot فعلی وجود ندارند، نصب فعلی وردپرس و اتصال کش تأیید نشدند. Valkey مستقل PONG داد. بررسی فقط خواندنی بود؛ هیچ بازیابی یا تغییر برنامه/DB انجام نشد. دو سایت عمومی دیگر HTTP200 و site-health هفت مسیر healthy بودند. نباید سلامت تمام سایت‌ها یا اتصال فعلی همه کش‌ها اعلام شود.
- این لایه raw Unix transport است، نه public reverse proxy کامل. frontend اختصاصی، Host/header validation، TLS/SNI، lifecycle ثبت/لغو خودکار و integration پنل، storage/DB و بررسی امنیت عمومی همچنان لازم‌اند. محدودیت یک private deployment حفظ شده. هیچ سایت عمومی یا DNS تغییر نکرد و reboot انجام نشد.
