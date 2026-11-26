# فرم برنامه‌ریزی موتور خصوصی — استقرار روی پنل

۲۶ نوامبر ۲۰۲۶. اصلاحات امنیتی Provisioner در commit 4615d60bd3e7d0a23a76122e2a6de401325216ac: محیط پاک curl، غیرفعال کردن curlrc، پروتکل HTTP محدود، رد bind mount از mountinfo و گروه‌های اضافی؛ CI run 45876734674 موفق. blob bf1318ea740ab49f8aece1445cb69ca1d11acf4d روی سرور جایگزین شد و چرخه plan/apply/PHP/rollback FrankenPHP موفق بود. هیچ enrollment ماندگار ایجاد نشد.

پنل: پنج فایل از commit 26e9c424d9da15e04b25d7f2a57436a44e03badb با Git blob بررسی شدند. ماژول planner، view، panel context و دو template روی سرور نصب شدند؛ route مستقل /websites/hooshPrivateEnginePlan به websiteFunctions/urls.py اضافه شد. scripts/stage_private_engine_route.py همان تغییر را به شکل review copy تولید می‌کند. لینک صفحه در بخش Hoosh Web Engine Manager در Create Website قرار دارد. انتخاب Apache یا FrankenPHP، نام حساب اختصاصی موجود، دامنه و درخواست اجرای پس از بوت؛ خروجی فقط برنامه و دستور preflight است. هیچ فرمان root از Django اجرا نمی‌شود. فرم اصلی و منطق قابلیت‌های تجاری CyberPanel دست‌نخورده‌اند.

CI safety run 45876947480 و private engine run 45876947471 موفق. Django RequestFactory با ACL شبیه‌سازی‌شده: مدیر GET/POST معتبر 200، غیرمدیر و بدون CSRF 403، ورودی تزریقی 400، reverse/resolve درست. پس از restart صرفاً lscpd، مسیر بدون ورود HTTP302 و سرویس‌های اصلی فعال. نشست واقعی مدیر در مرورگر بررسی نشده است. این فرم ثبت درخواست اجرایی، صف یا ساخت خودکار سایت عمومی نیست. root باید پروژه بررسی‌شده و حساب اختصاصی را آماده و CLI preflight/apply را جداگانه اجرا کند.

بازگشت: بکاپ root-only سه فایل موجود؛ در صورت نیاز restore آنها و حذف سه فایل جدید و restart lscpd. تغییر DNS/TLS/سایت تولید یا reboot انجام نشد. مسیر عمومی و TLS، storage/DB و lifecycle کامل frontend، و ظرفیت بیش از یک deployment خصوصی همچنان باز هستند.
