# Infrastructure 2027 — Preview 9

۲۶ نوامبر ۲۰۲۶ — اتصال HTTP از OpenLiteSpeed به FrankenPHP از طریق Unix socket.

- بسته OLS 1.9.4-3+jammy فقط در fixture استخراج و SHA256 با metadata رسمی تطبیق داده شد. سرویس اصلی تغییر نکرد.
- سرویس FrankenPHP از template نصب‌شده Preview 8، حساب مصنوعی اختصاصی و root enrollment موقت، بدون TCP و با private network اجرا شد.
- OLS آزمایشی با www-data در PID/network/tmp خصوصی، مسیر OLS اصلی غیرقابل دسترس، MemoryMax=192MiB و CPUQuota=30% یک هسته. ACL فقط روی سوکت و دایرکتوری runtime مصنوعی، دسترسی www-data موفق، nobody رد شد. کاربر worker اصلی OLS تولید nobody است؛ هیچ مجوز جدیدی به آن داده نشد.
- آدرس extprocessor از نوع proxy با uds://run/hoosh-frankenphp-hoosh-proxy-fixture/http.sock و Host مصنوعی franken.tenant.test. اجرای PHP و حفظ Host از OLS موفق؛ /.env پاسخ 403؛ unknown.test پاسخ 404 بدون محتوای fixture. نتیجه probe exit=0.
- هشدار کپی config0 در filesystem فقط‌خواندنی و missing accessLog در پیکربندی حداقلی آزمایشی ثبت شد. اولین درخواست readiness قبل از شروع listener connection refused بود؛ آزمون بعدی موفق شد.
- همه حساب‌ها، enrollment، ACL، socket، پروژه و فایل‌های موقت حذف شدند؛ listener و پردازش آزمایشی باقی نماند. سایت‌های پایش‌شده healthy و OOM صفر؛ RAM available 1904MiB، Swap free 1489MiB، دیسک حدود 11GiB آزاد، 89% پر. تمام سرویس‌های اصلی فعال.
- نتیجه فقط قابلیت transport را ثابت می‌کند. هنوز مجوزدهی دائمی سوکت و بازتولید ACL بعد از restart، جداسازی کامل مشتریان در برابر shared proxy identity، HTTPS/SNI، هدرهای forwarded، symlink، writable application storage، DB، provisioning تراکنشی و فرم عملیاتی Create Website تأیید نشده‌اند. کش و مسیر عمومی FrankenPHP فعال نشده‌اند.
- HWE 6.8 هنوز boot نشده؛ ریبوت نیازمند پنجره نگهداری و مسیر بازیابی مستقل است. Preview توسعه‌ای، نه نسخه پایدار.
