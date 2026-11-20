# بررسی رسمی قابلیت‌های CyberPanel Premium — نقشه جایگزین مستقل مجاز

**تاریخ مرور:** ۲۰ نوامبر ۲۰۲۶. مرجع: [CyberPanel official add-ons](https://cyberpanel.net/CyberPanel-addons)، [features](https://cyberpanel.net/features)، [Docker Manager](https://cyberpanel.net/docker-manager)، [Roundcube](https://cyberpanel.net/roundcube). ترکیب بسته‌های Premium در صفحات بازاریابی متفاوت ممکن است تغییر کند؛ قبل از تصمیم نهایی دوباره استعلام شود.

## اصل مهم

هدف ساخت امکاناتی **مستقل** و مطابق APIهای آزاد، با طراحی و کد خودمان است؛ نه کپی کد تجاری، دستکاری license flags، unlock کردن Premium یا استفاده از نسخه توزیع‌شده بدون مجوز. **Docker Manager در فهرست رسمی رایگان است** و نباید دوباره به‌عنوان قابلیت Premium ساخته شود. فروش VPS خودِ CyberPanel نیست و به API تأمین‌کننده واقعی نیاز دارد.

| قابلیت دیده‌شده در وب‌سایت رسمی | طرح مستقل CyberPanel Master | اولویت/محدودیت |
|---|---|---|
| SSL V2 | ACME, DNS-01, certificate inventory/expiry alarms, renewal smoke tests | P1؛ فقط با دامنه و DNS مجاز، بدون جایگزینی ناگهانی گواهی |
| WordPress Manager Pro | مدیریت WordPress سایت‌های **مشتریان هاست**، staging, checksum, updates و rollback | P2؛ ربطی به بازگرداندن وردپرس به سایت اصلی HooshDigital ندارد |
| Backup V2 | restic/encrypted offsite, retention, integrity and **restore drill** | P0؛ backup فعلی read-only را با اجرای نامطمئن قاطی نکنید |
| Email Debugger | تله‌متری SMTP/MX/SPF/DKIM/DMARC و خلاصه خطاها با حذف PII | P1؛ بدون افشای متن پیام/نشانی‌ها |
| Root File Manager | فایل‌منیجر محدود با allowlist, RBAC و step-up؛ **نه مرور همه فایل‌های root از وب** | P3؛ ریسک بالا، اجرای root browser ممنوع |
| Rspamd Manager | status/rules/quarantine through supported Rspamd admin API | P2؛ جلوگیری از دورزدن anti-spam و افشای پیام |
| Roundcube integration | Webmail login / link، تنظیم امن proxy، SSO فقط در صورت پشتیبانی و بررسی رسمی | P2؛ بسته ممکن است در تبلیغات به صورت مستقل فهرست شود |

## امکانات دیگر مرتبط با پنل

- **Docker Manager:** طبق صفحه رسمی جزو امکانات رایگان Core است؛ اول آن را با امکانات نصب‌شده مقایسه کنیم.
- **CloudLinux:** بسته به نسخه/میزبان و لایسنس خودش، نه یک بازکردن ساده Premium؛ مدیریت محدودیت منابع با جایگزین‌های قانونی مثل cgroups و isolation مستقل برنامه‌ریزی شود.
- **Server/VPS sales:** ماژول WHMCS و آداپتور Proxmox/Libvirt/Provider، capacity reservation و idempotent lifecycle؛ هیچ hypervisor فرضی در CyberPanel ایجاد نشود.
- **.htaccess compatibility / LiteSpeed Enterprise:** وابستگی و لایسنس متفاوت دارند؛ هرگونه تغییر وب‌سرور جداگانه ارزیابی می‌شود.

## طراحی مشترک

تمام امکانات آینده در `CyberPanel-Master` توسعه داده می‌شوند، با افزونه‌های قابل‌نصب و feature flags. UI از navigation، spacing، tokenها و icon pack فعلی CyberPanel تبعیت می‌کند. در هر افزونه جداسازی نقش مدیر/فروشنده/مشتری، audit logs، backup/restore، تست regression، no-shell-in-browser و جلوگیری از تغییر هم‌زمان تنظیمات فعلی ضروری است.

**Release status:** فقط Research / Roadmap. هیچ قابلیت Premium مجازی یا ماژولی فعال نشده است.
