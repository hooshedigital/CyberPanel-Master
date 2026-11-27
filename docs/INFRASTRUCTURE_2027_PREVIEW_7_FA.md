# Infrastructure 2027 — Preview 7

۲۶ نوامبر ۲۰۲۶ — قالب عملیاتی Valkey Object Cache مستقل برای هر حساب پروژه.

- فایل‌های hoosh-valkey@.service، hoosh-valkey.slice و hoosh-valkey-account-check از commit 4684f7ff1eada4dc5afb5715b527efb41c6594cc روی سرور نصب و daemon-reload انجام شد، بدون restart سرویس‌های اصلی.
- حساب‌های مشترک/مدیریتی، enrollment نامعتبر، مالکیت ناامن و UID/GID نامطابق رد می‌شوند. enrollment فقط توسط مالک root و پس از بررسی اختصاصی بودن حساب انجام می‌شود.
- TCP خاموش، سوکت 0700، private network، ذخیره پایدار غیرفعال، maxmemory داده 32MiB، MemoryMax سرویس 96MiB و CPUQuota 20% یک هسته، محدودیت مشترک slice 192MiB و 30% یک هسته. این سقف‌ها ظرفیت تضمین‌شده نیستند.
- آزمون واقعی template با حساب مصنوعی no-login و enrollment موقت: PING/SET/GET موفق، کاربر nobody از سوکت محروم، MemoryCurrent 2715648 bytes (حدود 2.59MiB در نمونه cgroup). مقادیر cgroup بررسی شدند؛ benchmark workload نیست. حساب، گروه، enrollment، socket و پردازش موقت حذف شدند.
- قالب آماده ثبت دستی پروژه اختصاصی است؛ هنوز هیچ سایت تولید به Valkey متصل نشده، Redis اصلی تغییر نکرده و instance دائمی فعال نیست. برای داده پایدار/نشست استفاده نشود.
- systemd-analyze verify موفق؛ هشدارهای پیشین واحدهای دیگر (از جمله KillMode=none در lshttpd) ثبت شدند؛ عمداً در این مرحله تغییر نکردند.
- سرویس‌های اصلی فعال، RAM available 1898MiB، Swap free 1489MiB و دیسک تقریباً 11GiB آزاد. GHCR پاسخ 401 داد (شبکه قابل دسترس؛ مجوز انتشار/دریافت تأیید نشده).
- HWE 6.8 همچنان boot نشده؛ zpool و compressor تغییر نکردند تا کرنل جدید و مسیر بازیابی مستقل تأیید شوند. Apache/FrankenPHP provisioning و اتصال عملیاتی فرم، مهاجرت کش پروژه واقعی و تست جامع باقی مانده‌اند.

نسخه توسعه‌ای، نه انتشار پایدار نهایی.
