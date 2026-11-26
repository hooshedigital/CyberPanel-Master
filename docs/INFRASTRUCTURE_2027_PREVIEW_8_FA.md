# Infrastructure 2027 — Preview 8

۲۶ نوامبر ۲۰۲۶ — قالب عملیاتی FrankenPHP مستقل برای هر حساب پروژه.

- فایل‌های hoosh-frankenphp@.service، hoosh-frankenphp.slice، frankenphp.Caddyfile و hoosh-frankenphp-account-check از commit 3687a75f04fbc63e5ca11d83b5007b3f0a3f0669 روی سرور نصب شدند. systemd-analyze verify و Caddy adapt موفق؛ daemon-reload بدون restart سرویس‌های اصلی.
- Runtime نسخه 1.14.0 با PHP 8.6.0؛ حساب اختصاصی root-enrolled، public path با parentهای root-owned، محیط فقط‌خواندنی، private network، admin API و TCP خاموش؛ HTTP از Unix socket در دایرکتوری 0700.
- سقف هر instance RAM 256MiB/CPU 35% یک هسته، مجموع slice 384MiB/50% یک هسته؛ دو thread. محدودیت ظرفیت تضمین‌شده نیست.
- آزمون واقعی با حساب مصنوعی no-login: PHP از سوکت پاسخ صحیح، حساب nobody از سوکت محروم، /.env و /index.php.bak و /wp-config.php هر سه HTTP403. MemoryCurrent=38305792 bytes (~36.53MiB)، نمونه کوچک و نه benchmark واقعی. مقادیر cgroup بررسی شدند. حساب، گروه، enrollment، پروژه و socket موقت حذف شدند.
- هیچ instance دائمی، سایت واقعی یا مسیر عمومی راه‌اندازی نشد. reverse proxy، دسترسی امن به سوکت، TLS/header trust، writable app storage، DB اتصال، سازگاری PHP و tenant isolation جامع هنوز باقی‌اند. قواعد مسیر فقط آزمون اولیه هستند؛ امنیت همه فایل‌ها و symlinkها تأیید نشده است.
- هشدارهای قدیمی systemd شامل KillMode=none برای lshttpd دست‌نخورده ماندند. سرویس‌های اصلی فعال؛ RAM available 1930MiB، Swap free 1489MiB، دیسک تقریباً 11GiB آزاد (89%).
- HWE 6.8 همچنان boot نشده؛ Valkey مستقل، Apache hybrid، GHCR، provisioning و فرم Create Website به صورت کامل عملیاتی نشده‌اند. نسخه توسعه‌ای است، نه تأیید انتشار پایدار نهایی.
