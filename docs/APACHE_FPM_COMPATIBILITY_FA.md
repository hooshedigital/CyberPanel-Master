# Apache/FPM مستقل، حالت سازگاری

Apache نصب‌شده Ubuntu و PHP-FPM استخراج‌شده از بسته‌های رسمی 8.1.2-1ubuntu2.29. این نسخه فقط برای سازگاری است و PHP پیش‌فرض یا انتخاب پیشنهادی پروژه‌های جدید نیست. بسته استخراج‌شده خودکار از apt به‌روز نمی‌شود؛ چرخه بررسی امنیتی و جایگزینی نسخه لازم است.

حساب اختصاصی بدون login و گروه هم‌نام، public path تحت /srv/hoosh-apache/ACCOUNT/public با محتوای root-reviewed و مسیرهای root-owned. اجرای root-only: hoosh-apache-config prepare ACCOUNT canonical.domain سپس systemctl start hoosh-apache-http@ACCOUNT.socket. سوکت 0600 در /run/hoosh-apache-http-ACCOUNT.sock؛ درخواست از همان حساب curl --unix-socket. Backend با socket activation و private network و سقف منابع آغاز می‌شود. هیچ TCP عمومی یا اتصال خودکار OLS و DNS وجود ندارد. برای توقف هر سه واحد socket، relay و backend را متوقف کنید. تنظیمات root-owned، enrollment، فایل‌های پروژه و rollback باید مستقل مدیریت شوند.

AllowOverrideList فقط دستورهای rewrite را مجاز می‌کند؛ فایل‌های app باید immutable و بررسی‌شده باشند. این حالت هنوز برای سایت عمومی یا CMS با storage/DB و شبکه خارجی آماده نیست. کنترل کامل symlink، tenant isolation، lifecycle مجوز سوکت frontend، TLS و انتخاب موتور پنل باقی است. هیچ قابلیت تجاری CyberPanel تغییر نمی‌کند.
