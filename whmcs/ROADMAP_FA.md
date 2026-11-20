# نقشه توسعه تجاری CyberPanel Master — WHMCS و Linux/VPS

تاریخ شروع: ۱۴۰۵/۰۸/۲۹ (۲۰۲۶-۱۱-۲۰)

## تصمیم مالکیت پروژه

**تمام توسعه‌های WHMCS زیرمجموعه مخزن `hooshedigital/CyberPanel-Master` است.**
WHMCS همچنان سامانه اجرایی مالی و مشتریان باقی می‌ماند. CyberPanel Master یک محیط مدیریتی واحد روی آن ارائه می‌دهد، نه نسخه کپی‌شده سیستم مالی.

| مرحله | موضوع | Issue | معیار تحویل |
|---|---|---|---|
| P0 | ممیزی API قبلی CyberPanel | [#10](https://github.com/hooshedigital/CyberPanel-Master/issues/10) | شناسایی مسیر/سورس/نسخه/مجوز قبل از دوباره‌نویسی |
| V1.0 | WHMCS Command Center | [#4](https://github.com/hooshedigital/CyberPanel-Master/issues/4) | بخش مدیریتی Admin-only با تفکیک وضعیت و ورود مستقل |
| V1.0 | ساخت پکیج و نگاشت پلن‌ها | [#5](https://github.com/hooshedigital/CyberPanel-Master/issues/5) | draft → staging → validation → owner approval → publish |
| V1.0 | افیلیت و فروش مشارکتی | [#6](https://github.com/hooshedigital/CyberPanel-Master/issues/6) | استناد به پورسانت native WHMCS و تطبیق ارجاعات |
| V1.0 | پرداخت و صورتحساب | [#8](https://github.com/hooshedigital/CyberPanel-Master/issues/8) | callback معتبر، مدیریت ریال/تومان، رفتار تکرار و refund |
| V1.x | دامنه، SSL، کمپین و فروش مکمل | [#9](https://github.com/hooshedigital/CyberPanel-Master/issues/9) | کاتالوگ واحد و ردیابی منبع خرید |
| V1.x | هویت کارکنان، مشتریان و SSO | [#11](https://github.com/hooshedigital/CyberPanel-Master/issues/11) | احراز هویت معتبر، 2FA و role mapping، بدون root impersonation |
| V2.0 | مدیریت Linux، فروش VPS و سرور | [#7](https://github.com/hooshedigital/CyberPanel-Master/issues/7) | آداپتور تأمین‌کننده واقعی، جداسازی tenant، تست lifecycle |

## طراحی بخش WHMCS داخل سایبرپنل مستر

«WHMCS Command Center» در داشبورد فعلی یک بخش جدید می‌شود. ۹ کارت راهبردی برای مالی، پکیج‌سازی، محصولات، افیلیت، کمپین، ساخت هاست، هویت، لینوکس و VPS نشان می‌دهد. تا وقتی API و نسخه سرور واقعاً بررسی نشده‌اند، تمام کارت‌ها «برنامه‌ریزی‌شده / متصل نیست» هستند. لینک مدیریتی موجود تنها به صفحه امن ورود WHMCS می‌رود؛ ورود خودکار Root یا جایگزین MFA ساخته نمی‌شود.

## زیرسیستم API

ابتدا سورس API موجود را پیدا و بر حسب قرارداد واقعی مرور می‌کنیم؛ قرارداد اتصال جدید نباید پیش‌فرض‌هایی درباره اسم endpoint، ساختار رمز یا پورت بزند. درگاه server-side فقط از least-privilege identity استفاده می‌کند، خطا و rate-limit را مدیریت می‌کند، و هیچ داده مشتری به JS عمومی برنمی‌گرداند.

## امکانات Premium

برخی قابلیت‌های CyberPanel Premium تحت مجوز هستند. هدف، **بازآفرینی قانونی قابلیت‌های مفید با APIهای آزاد و مستند** یا تهیه مجوز رسمی هنگام نیاز است، نه unlock/bypass. فروش VPS نیازمند hypervisor/provider جداست؛ CyberPanel به‌تنهایی VM نمی‌سازد. مرحله نخست طراحی ماژول Linux read-only، package allocator و VPS provision contract است.

## ترتیب قابل اجرا

۱. ممیزی API، موجودی سرویس‌ها، WHMCS فعلی، پرداخت و نسخه Premium/License؛ هیچ اطلاعات محرمانه در GitHub منتشر نشود.
۲. قراردادهای read-only با fixture ساختگی و تست‌های GitHub Actions.
۳. استقرار آزمایشی مرکز مدیریت و read-only adapter با ACL و audit.
۴. پکیج‌سازی و نگاشت نسخه‌دار در staging؛ نمایش تفاوت‌ها.
۵. gateway و affiliate attribution end-to-end روی WHMCS واقعی (با مجوز، test mode).
۶. فعال‌سازی تدریجی اتوماسیون بعد از receipt verified paid.
۷. Linux/VPS با تأمین‌کننده انتخاب‌شده و snapshot/rollback؛ سپس cutover سایت اختصاصی و بازنشستگی وردپرس.

## مرز انتشار

افزودن Issue، Branch، کد UI و آزمون GitHub **به معنی استقرار در Production نیست**. پیش از هر نصب/تغییر، بکاپ خارج از سرور، مانور بازیابی، ماتریس ریسک، تأیید مالک و تست خرید/بازگشت ضروری است.
