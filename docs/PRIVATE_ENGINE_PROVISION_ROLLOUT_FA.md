# استقرار مدیر ثبت موتور خصوصی

۲۶ نوامبر ۲۰۲۶. ابزار hoosh-engine-provision از commit b5f5f75b364fa4c9ce7135d2f7953cfbe8156d73 و Git blob 33443cfc8cd4fe3201cc47db5f2d645a3dbf5640 دریافت، اعتبارسنجی و در /usr/local/libexec نصب شد. CI run 45874364567 موفق بود.

- Apache: plan، apply، پاسخ PHP fpm-fcgi از سوکت اختصاصی، ثبت وابستگی boot و rollback موفق. symlink ورودی رد شد. کاربر دیگر به سوکت دسترسی نداشت.
- FrankenPHP: plan، apply، PHP از سوکت خصوصی، ثبت وابستگی boot و rollback موفق. کاربر دیگر رد شد.
- شکست کنترل‌شده: marker با mode 0600 متعلق به root، preflight موفق اما HTTP health شکست خورد؛ rollback خودکار journal، enrollment، config، socket و boot dependency را حذف کرد. فایل برنامه و حساب توسط rollback حذف نشدند؛ fixture جداگانه پاک شد.
- هیچ enrollment یا پروژه دائمی جدید باقی نماند؛ دایرکتوری state 0700 و lock 0600. هر 18 کانتینر و سرویس‌های اصلی فعال. RAM available 1685MiB، swap free 2250MiB، دیسک حدود 11GiB آزاد.
- ابزار برای ثبت خصوصی حساب و محتوای از پیش بررسی‌شده است. پیش‌فرض یک enrollment خصوصی روی این میزبان؛ نه عمومی‌سازی، نه ساخت حساب از پنل. آزمون boot dependency به معنای reboot واقعی نیست. health check فقط marker ثابت است؛ برای app واقعی readiness، TLS، reverse proxy، tenant isolation جامع، writable storage و database لازم است. هیچ تغییر سایت تولید، entitlement، DNS یا reboot انجام نشد.
- قبل از اتصال عمومی باید بررسی‌های امنیتی تکمیل شوند، از جمله جلوگیری از تأثیر تنظیمات curl حساب بر health probe و بررسی mountهای bind. این نسخه توسعه‌ای است و UI هنوز به provisioner متصل نیست.
