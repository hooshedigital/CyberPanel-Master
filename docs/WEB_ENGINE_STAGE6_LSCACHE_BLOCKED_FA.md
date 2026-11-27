# مرحله ششم — LSCache: مانع انتشار (۲۶ نوامبر ۲۰۲۶)

## روش
OLS 1.9.4 از بسته تأییدشده، صرفاً استخراج و در PID/network/tmp خصوصی با کاربر غیر root اجرا شد. مسیر OLS تولید غیرقابل دسترس بود. Backend آزمایشی Python با شمارنده درخواست و پاسخ مصنوعی، جایگزین PHP در این آزمون خاص بود. هیچ WordPress یا داده مشتری به کار نرفت. تنظیمات موجود تولید تغییر نکردند.

ماژول cache، private cache خاموش، qsCache/reqCookieCache/respCookieCache/ignoreReqCacheCtrl/ignoreRespCacheCtrl همگی 0، TTL 60s. فعال‌سازی عمومی محدود به /public با rewrite و هدر صریح Backend آزمایش شد. ابتدا فقط MISS دیده شد؛ افزودن rewrite موجب MISS سپس HIT و ثبات شمارنده Backend شد. تلاش بعد با شروط مثبت و منفی rewrite و تنظیم cache در vhost نیز نتوانست bypass نشست را تضمین کند.

## ماتریس نهایی
پس از warm شدن /public، ۱۰ از ۱۴ آزمون bypass موفق و ۴ مورد ناموفق شدند:
- ناموفق: دو Cookie مستقل، Authorization، درخواست Cache-Control: no-cache. هر چهار مورد HIT و شمارنده پاسخ عمومی اولیه را دریافت کردند.
- موفق: query، POST، /cart، /checkout، /my-account، /wp-admin، /wp-login.php، /wp-json، /private، /set-cookie. این مسیرهای مصنوعی به Backend رسیدند و no-store داشتند.

**این نتیجه فقط درباره fixture و قواعد آزمایش‌شده است، نه اثبات نقص عمومی محصول یا نشت اطلاعات مشتریان تولید.** پاسخ عمومی به درخواست دارای نشست، مانع پذیرش است. امنیت ذخیره پاسخ خصوصی یا Set-Cookie تحت تمام شرایط نیز هنوز ثابت نشده است. هیچ benchmark CPU/RAM/latency معتبر برای WordPress انجام نشده.

## تصمیم
کش ترکیبی همچنان ممنوع؛ renderer کش عمومی/خصوصی را غیرفعال نگه می‌دارد و admission planner از قبل درخواست public cache برای موتور ols-apache را رد می‌کند. هیچ تغییری در تنظیمات کش تولید داده نشد. رفع boundary درخواست، تست plugin واقعی WordPress/WooCommerce و warm-cache regression کامل باید قبل از فعال‌سازی انجام شوند. بررسی علت قطعی failure هنوز باقی است. مستند رسمی: https://docs.openlitespeed.org/config/lscache/ و https://docs.openlitespeed.org/config/reverseproxy/lscache/

## پاک‌سازی
واحد transient در پایان بعضی آزمون‌ها exit غیرصفر و وضعیت stopping داشت؛ فقط همان واحد تأییدشده خاتمه یافت. نبود process و listener میزبان تأیید و fixture حذف شد. سرویس‌های OLS، Docker، MariaDB و monitor فعال، سلامت سایت‌های پایش‌شده برقرار، OOM صفر. دیسک 87% همچنان warning.
