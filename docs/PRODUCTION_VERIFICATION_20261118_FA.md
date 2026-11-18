# گزارش استقرار واقعی و مرز امکانات CyberPanel Master

تاریخ ممیزی: ۱۸ نوامبر ۲۰۲۶. مبنا: دسترسی Root موقت و مستقل با تأیید مالک؛ بررسی مستقیم CyberPanel/Django، Cloudflare و GitHub. این گزارش فاقد رمز و محتوای کاربران است.

## نسخه و پنل

- هسته نصب‌شده و خوانده‌شده از `/usr/local/CyberCP/version.txt`: **CyberPanel 3.0 Build 4**.
- لایه توسعه اختصاصی: **CyberPanel Master v0.1.0**؛ عنوان در هدر و منوی اصلی، نسخه جداگانه Core/Extension، دسترسی از `/backup/master/` و command palette.
- مسیر افزونه نصب‌شده: `/usr/local/CyberCP/master_extensions/`؛ نسخه تو در تو و بدون مرجع `backup/master_extensions/` پس از ممیزی حذف شد.
- قالب جدید و Smart Backup با English پیش‌فرض و فارسی اختیاری در دامنه افزودنی‌ها؛ گسترش ترجمه به تمام صفحات هسته هنوز انجام نشده است.
- صفحه Master فقط برای مدیر با ACL اصلی CyberPanel؛ کاربر بدون ورود از /backup/master/ و /backup/smart/ با HTTP 302 به login منتقل می‌شود.
- `lscpd` پس از هر تغییر محدود و تست Django به‌طور موفق reload/restart شد؛ مسیرهای عمومی 443/8090 HTTP 200 ماندند. هیچ restart سراسری OpenLiteSpeed انجام نشد.
- نسخه‌های قبل از تغییر در آرشیو محافظت‌شده Owner Broker نگهداری می‌شوند؛ هنگام بازگشت باید uid/gid/mode اصلی حفظ شوند.

## CAPTCHA فعال

- Cloudflare Turnstile managed اختصاصی دامنه `manage.hooshedigital.ir` فعال در login: Site Key عمومی `0x4AAAAAAGG-PjEcCDvWgNdr`.
- Secret مرتبط در سرور در `/etc/hoosh-cybermaster/turnstile.secret` با دسترسی محدود است؛ تطابق Secret و widget از طریق digest بررسی شد؛ **خود Secret در این مخزن یا گزارش درج نشده**.
- Django middleware به POST واقعی `/verifyLogin` وصل است؛ در فرم AngularJS توکن `captcha_token` ارسال می‌شود و توکن برای تلاش بعدی reset می‌شود.
- آزمون زنده با CSRF معتبر و نام کاربری ساختگی: درخواست بدون توکن HTTP 403؛ درخواست با توکن جعلی HTTP 403، هر دو `captcha_verification_failed`.
- آزمون ورود موفق با توکن واقعی Turnstile و اجرای کامل 2FA در مرورگر کاربر هنوز انجام نشده است. اگر مشکلی پیش آمد با دسترسی اضطراری SSH باید مسیر بازیابی امن اجرا شود.
- یک ویجت آزمایشی اضافه که در جریان همین کار ساخته شده بود، پس از اثبات عدم استفاده و حفظ زوج فعال Site Key/Secret حذف شد.

## مغز و Gateway

- PARSA Heartbeat واقعی و وضعیت Executor در گزارش read-only موجود است.
- کانتینر `parsa-agent-executor` Healthy؛ `parsa-ai-router-pilot` Healthy؛ `http://127.0.0.1:4045/health` پاسخ 200 و درخواست ناشناس `/v1/models` پاسخ 401. این Router خصوصی را نباید با AI Gateway عمومی یکی فرض کرد.
- یک کارت مجزا برای Router داخلی به همراه وضعیت واقعی در Master افزوده شد (فارسی و انگلیسی).
- سرویس مستقل `hoosh-cyberagent.service` در systemd نصب‌شده تشخیص داده نشد. GitHub داشتن سورس 0.9.0 را نباید استقرار فعال فرض کرد.
- AI Gateway مستند در `aigateway` با مبدأ `supabase.hooshedigital.ir` هنگام بررسی از مسیرهای status و models پاسخ **503** می‌داد؛ بنابراین ادعای اتصال عملیاتی یا فعال بودن مدل‌ها نشده است.
- تایمر `hoosh-cybermaster-bridge.timer` برای مشاهده امن و بدون دسترسی Root در مرورگر فعال شده است. هیچ ابزار اجرای دلخواه shell یا درخواست Root در UI ایجاد نشده است.

## تست‌ها و GitHub

- Django URL reverse، compile قالب‌های اصلی، context هر دو زبان، نمایش نسخه و پرچم سلامت Router بررسی شدند.
- GitHub Actions در انتهای ممیزی پس از اصلاح تست‌های فعال‌سازی کپچا موفق شد. PR توسعه: `https://github.com/hooshedigital/CyberPanel-Master/pull/2`.
- **توجه به parity:** سورس `master_extensions/login_captcha.py` در شاخه توسعه شامل مکانیزم علامت فعال‌سازی Root-controlled آزمایشی است؛ نسخه نصب‌شده فعلی مسیر فعال‌سازی متفاوت دارد. PR عمداً Draft باقی می‌ماند تا تطبیق Source↔Production و تست مرورگر نهایی شود.

## ریسک‌ها و تکمیل نهایی

۱. کاربر با مرورگر واقعی یک ورود موفق به صفحه اصلی و اگر فعال است 2FA را آزمایش کند.
۲. Gateway عمومی 503 عیب‌یابی سرویس‌به‌سرویس و پیکربندی Supabase/Cloudflare می‌خواهد؛ نیازی به دسترسی Root مستقیم به مرورگر نیست.
۳. استقرار مستقل Hoosh CyberAgent باید بعد از بررسی نیاز منابع و قرارداد دسترسی آن انجام شود. منابع سرور محدود و مصرف دیسک در گزارش SSH تقریباً **۹۱٪** بود.
۴. HTTP پورت 80 در ممیزی پیشین هنوز به HTTPS هدایت نمی‌شد؛ اصلاح آن به رفع خطاهای موجود vhost OpenLiteSpeed و یک تغییر مستقل نیاز دارد.
۵. اطمینان از تمدید خودکار گواهی manage و تست بصری واقعی مرورگر همچنان در فهرست پذیرش است.

هیچ اطلاعات حساس، رمز مشتری، رمز Turnstile یا snapshot پایگاه داده در مخزن عمومی بارگذاری نشده است.
