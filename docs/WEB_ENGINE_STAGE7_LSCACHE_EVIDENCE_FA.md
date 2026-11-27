# مرحله هفتم — اصلاح آزمایشی Cache Bypass و Storage Policy

۲۶ نوامبر ۲۰۲۶. هیچ تنظیم Production یا entitlement تجاری تغییر نکرد. بسته OLS 1.9.4-3+jammy با SHA256 مطابق apt استخراج شد؛ نصب نشد. محیط private PID/network/tmp، user غیر root، مسیر OLS اصلی غیرقابل دسترس و سقف 256 MiB / 35% یک CPU داشت. Backend مصنوعی Python با شمارنده و 15ms تأخیر ثابت؛ WordPress/WooCommerce واقعی نیست.

## علت و اصلاح
در سورس رسمی نسخه v1.9.4 تابع checkAssignHandler مسیر modcache=0 برای خاموش کردن hookهای کش دارد. isReqCacheable و lookup در تمام مسیرها یکسان اعمال نمی‌شوند. بنابراین صرف reqCookieCache=0 و cache-control:no-cache در fixture قبلی کافی نبود. مرجع: https://github.com/litespeedtech/openlitespeed/blob/v1.9.4/src/modules/cache/cache.cpp و https://docs.openlitespeed.org/config/lscache/

آزمون allowlist دقیق GET /public بدون Cookie، Authorization، query، Cache-Control و Pragma؛ سایر درخواست‌ها modcache=0. اولین نسخه با اجبار max-age=60 از Rewrite، ماتریس warm-cache را 15/15 گذراند، ولی در آزمون cold-cache پاسخ استاندارد no-store بدون X-LiteSpeed-Cache-Control کش شد. آزمون Set-Cookie همان دور تحت اثر entry قبلی بود، پس شکست مستقل Set-Cookie محسوب نمی‌شود. در کش تازه Set-Cookie ذخیره نشد. راهکار نهایی حذف اجبار TTL در Rewrite و سپردن سیاست ذخیره به پاسخ صریح Origin بود.

## نتیجه نهایی
- 15/15 آزمون bypass گرم: دو Cookie، Authorization، query، POST، Cache-Control، Pragma، cart، checkout، my-account، wp-admin، wp-login.php، wp-json، private، set-cookie.
- کش سرد: private با هدر اختصاصی no-cache، no-store فقط با هدر استاندارد، Set-Cookie با پاسخ ظاهراً عمومی؛ شمارنده هر دو درخواست متفاوت و هیچ HIT نبود. سپس پاسخ عمومی cache hit، سپس درخواست ترکیبی Cookie+Authorization bypass شد. پنج assertion گروهی موفق.
- پاسخ عمومی بعد از درخواست حساس همچنان عمومی و HIT بود.
- 12 نمونه هر حالت در اجرای نهایی: median HIT 1.387ms، bypass 18.880ms. اجرای پیشین با اجبار TTL: 1.545ms و 18.307ms. این ارقام تنها fixture مصنوعی با 15ms delay هستند؛ نه benchmark سایت واقعی یا کاهش اندازه‌گیری‌شده CPU/RAM.
- بعضی اولین probeهای readiness، 503 یا connection refused داشتند؛ اجرای نهایی transient exit=0، assertionها موفق.
- تنظیمات اصلی renderer و admission planner بدون تغییر؛ cache ترکیبی در آن‌ها همچنان مسدود است. فایل fixture فقط نمونه تحقیق قابل بازتولید است و هیچ مسیر نصب یا اجرای خودکار ندارد.

## باقی‌مانده
WordPress/WooCommerce واقعی، plugin و رفتار purge/invalidation و تغییر محتوای عمومی به خصوصی، درخواست‌های متنوع و چندمستأجره، HTTPS/SNI/header trust، benchmark واقعی، provisioning/rollback، RBAC/CSRF و انتشار تأییدشده. تکیه بر هدر اختصاصی Origin نیازمند trust boundary است. هیچ مجوز فعال‌سازی Production از این آزمون نتیجه نمی‌شود.
