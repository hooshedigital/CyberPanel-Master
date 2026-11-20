# ممیزی سورس، ظاهر و هویت CyberPanel Master — ۲۰ نوامبر ۲۰۲۶

> **وضعیت:** ممیزی سورس GitHub، گزارش استقرار ۱۸ نوامبر، فهرست‌خوانی DNS و سرویس‌ها؛ **نه پذیرش نهایی UI در مرورگر و نه استقرار روی Production**.

## نسخه‌ها و تمایز شواهد

| زیرسیستم | شاهد معتبر | نتیجه/محدودیت |
|---|---|---|
| CyberPanel Core | گزارش خواندن فایل نسخه در ۱۸ نوامبر | **3.0 Build 4**؛ بدون خواندن مجدد همان فایل در این ممیزی تأیید زنده نیست |
| CyberPanel Master extension | `master_extensions/version.py` در شاخه #2 | **0.1.0** نسخه افزونه است، نه لزوماً نسخه Core |
| WHMCS | ممیزی گزارش‌شده ۶ نوامبر | **8.13.5** تاریخ‌دار؛ نسخه فعلی و مسیر live جدید باید بررسی شود |
| Smart Backup | سورس `summary()` | **1.0.0-staging** فقط برچسب موتور بکاپ؛ نشانه انتشار Production نیست |
| Agent / AI Gateway | سرویس‌ها و گزارش تله‌متری | معیار `systemctl active` به‌تنهایی اثبات صحت اتصال UI/API نیست |

**نکته عدم‌تطابق واقعی:** `master_extensions/captcha_context.py` در GitHub قبل از این شاخه دارای public sitekey متفاوت با widget تأییدشده در گزارش ۱۸ نوامبر بود. این خطا در سورس این شاخه اصلاح شد؛ **نسخه نصب‌شده روی سرور با این شاخه برابر فرض نمی‌شود**.

## CAPTCHA / Login

- شواهد ۱۸ نوامبر: Cloudflare Turnstile با `manage.hooshedigital.ir`، مسیر `/verifyLogin`، ارسال `captcha_token` و HTTP 403 برای توکن جعلی/غایب فعال گزارش شده است.
- هنوز آزمون **موفق** با توکن واقعی، login، password check، CSRF و 2FA در مرورگر انجام/ثبت نشده است.
- پرونده `docs/DEPLOYMENT_GATES.md` اشتباهاً هم‌زمان می‌گفت widget فعال نیست؛ تناقض زمانی اصلاح شد.
- context branch اکنون فقط برای `CYBERMASTER_CAPTCHA.enabled = true`، marker معتبر، آدرس واقعی مدیریت و sitekey مطابق تنظیم/گزارش، widget را فعال اعلام می‌کند. نیاز به QA پیش از نصب دارد.
- هرگز `login_captcha.py` یا قالب ورود را بدون تطبیق نسخه نصب‌شده و آزمایش lockout/rollback جایگزین نکنید.

## ظاهر و زبان

- قالب اصلی CyberPanel، CSS هسته، منوها، ساختار navigation و icon pack **دست نخورده است**.
- کارت‌های جدید WHMCS در شاخه قبلی `row/col`، inline CSS و markup متفاوت داشتند. در این ممیزی به `cp-tile-grid` / `cp-tile` / `cp-tile-ic` / `cp-tile-title` / `cp-tile-sub` موجود در Master تبدیل شدند؛ فقط آیکون‌های FontAwesome از پیش استفاده‌شده به کار رفتند.
- لینک‌های انتخاب زبان `lang=en/dir=ltr` و `lang=fa/dir=rtl` دارند؛ ریشه قالب همچنان `dir="{{ direction }}"` است.
- کلیدهای ترجمه `en/fa` و نمونه صفحات Master/Smart Backup با تست مستقل بررسی می‌شوند؛ برچسب `Snapshot` از دو قالب بکاپ حذف و معادل دو زبانه دارد.
- **ترجمه تمام هسته CyberPanel هنوز انجام نشده است.** این کار نیازمند استخراج متن‌های upstream و templateهای نصب‌شده، i18n/gettext و screenshot/browser regression در چند نقش (admin/reseller/client) است. ترجمه خودکار و گسترده HTML ممنوع است.
- اسکریپت `brand_core.py` با SHA سخت‌گیرانه و مقدار version/footer ثابت در سورس قبلی موجود است؛ بدون بررسی هش نسخه نصب‌شده، تغییر یا اجرا نمی‌شود.

## ردپای اتصال قدیمی WHMCS–CyberPanel

طبق سوابق اکتبر، یک پیاده‌سازی مستقل `cp-whmcs` با پوشه‌های `core`، `integrations/WHMCS`، `integrations/CyberPanel`، `storage`، `tests` و `whmcs-module` روی سرور گزارش شده بود. **در این جلسه بایت‌های سورس آن خوانده نشده‌اند.** دامنه `cp-whmcs.hooshedigital.ir` در گزارش ۲۶ اکتبر صفحه placeholder داشت، نه API منتشرشده اثبات‌شده. در DNS فعلی Cloudflare رکورد صریح آن دیده نشد؛ وجود wildcard یا vhost مستقل بررسی نشده است.

WHMCS در گزارش ۶ نوامبر دارای ماژول سفارشی `hooshcloud` و ماژول پرداخت زرین‌پال بود؛ وضعیت عملیاتی/نسخه فعلی از طریق ابزار فعلی بازرسی نشده است. **قبل از ساخت API جدید، سورس قبلی و ماژول WHMCS با هم قراردادسنجی شوند**. اطلاعات حساس مسیرها، کلیدها و `configuration.php` را داخل مخزن عمومی نگذارید.

مرجع پیگیری: [Issue #10](https://github.com/hooshedigital/CyberPanel-Master/issues/10).

## زیرساخت و توقف انتشار

- خواندن سرویس‌ها در ۲۰ نوامبر: `lscpd`، `lshttpd`، `hoosh-cyberagent.service` فعال؛ این صرفاً وضعیت systemd است.
- `df -hT` حدود **۹۲٪ فضای مصرف‌شده** روی پارتیشن اصلی نشان داد؛ قبل از هر بکاپ، ظرفیت offsite و فضای کافی بررسی شود.
- DNS تغییر نکرد. سایت‌ها و WordPress تغییر نکردند. Root request، restart، migration، WHMCS payment/provisioning اجرا نشده‌اند.
- تست‌های GitHub Actions صرفاً unit/source contract هستند؛ نمای دسکتاپ/موبایل، تغییر زبان مرورگر و ورود موفق واقعی هنوز نیازمند پذیرش هستند.

## Release Gate

۱. Inventory دقیق از نسخه نصب‌شده، فایل‌های تغییر یافته و SHA همراه snapshot رمزگذاری‌شده خارج‌سروری.
۲. مقایسه CSS/icon/navigation قبل و بعد، تست بصری در ۳ عرض (موبایل، تبلت، دسکتاپ) و دو زبان، بدون تغییر هسته.
۳. تست successful CAPTCHA login + 2FA و fail cases؛ تأیید عدم lockout.
۴. تطبیق API موجود و WHMCS/زرین‌پال در staging با قرارداد سازگار.
۵. تأیید مستقل مالک، برنامه rollback و سپس استقرار مرحله‌ای.
