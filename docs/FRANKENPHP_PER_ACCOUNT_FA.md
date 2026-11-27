# FrankenPHP مستقل — قالب اجرای خصوصی

Runtime 1.14.0 با PHP 8.6.0، برای پروژه جدید سازگار، نه پیش‌فرض وردپرس. سرویس فقط برای حساب اختصاصی root-enrolled با UID/GID معتبر، سوکت HTTP محلی در /run/hoosh-frankenphp-ACCOUNT/http.sock و دایرکتوری سوکت 0700، بدون TCP یا admin API. سقف هر instance 256MiB/35% یک CPU، مجموع slice 384MiB/50% یک CPU. دو thread؛ GOMAXPROCS=1. این‌ها سقف‌اند نه ظرفیت تضمین‌شده.

Root باید مسیر /srv/hoosh-frankenphp/ACCOUNT/public را با محتوای بررسی‌شده و مالکیت root ایجاد کند؛ parentها root-owned و غیرقابل نوشتن توسط سایر کاربران. حساب اختصاصی بدون login و enrollment root-owned با ACCOUNT:UID:GID و newline نهایی در /etc/hoosh-runtimes/frankenphp-accounts/ACCOUNT. فایل 0644. برنامه فقط‌خواندنی است؛ اتصال شبکه خصوصی، داده پایدار و مسیرهای قابل نوشتن برنامه هنوز فراهم نیست. systemctl start hoosh-frankenphp@ACCOUNT.service و curl --unix-socket برای همان حساب؛ stop برای rollback. نه API خودکار و نه اتصال عمومی. این template عمداً Install section ندارد. بدون اعتماد به هدر ورودی یا مسیر arbitrary.

قواعد Caddyfile صرفاً حفاظت اولیه برخی مسیرهای حساس است؛ امنیت کامل app، symlink، مالکیت همه فایل‌ها، PHP extensions، SNI و header trust نیازمند آزمون جداست. اجرای عمومی و reverse proxy به دلیل سوکت خصوصی حساب فعلاً مسدود است. هیچ سایت تولید یا Premium تغییر نمی‌کند.
