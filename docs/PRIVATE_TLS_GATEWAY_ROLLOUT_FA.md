# استقرار Gateway خصوصی TLS

۲۶ نوامبر ۲۰۲۶. commit 0fdefaea6630947352ba5868ad1781b9da9966bf نصب شد. فایل‌های gateway-config و systemd template و provisioner با Git blob تطبیق داده شدند؛ systemd-analyze verify و CI خصوصی 45879299122 موفق.

- Nginx مستقل با هویت hoosh-web-edge، PrivateNetwork، AF_UNIX، مسیر runtime 0700؛ هیچ TCP listener جدید، تغییر Nginx/OLS فعلی، DNS یا تونل MCP انجام نشد.
- FrankenPHP: اتصال با گواهی self-signed مصنوعی و CA validation موفق؛ Host/SNI اشتباه 421، TRACE 405، Upgrade 400، .env 403؛ TLS 1.1 و دسترسی nobody/www-data/tenant رد شدند. هدرهای جعلی X-Forwarded و X-Hoosh-Attack حذف، Host و scheme صحیح، Cookie و POST body سالم. MemoryCurrent=2818048 bytes، سه درخواست گرم 0.030533/0.032722/0.025240s. این اعداد فقط fixture هستند.
- Apache: TLS transport، Host/SNI، TRACE، .env، Cookie و POST body موفق. اما PHP مقادیر HTTPS و HTTP_X_FORWARDED_PROTO را خالی دریافت کرد؛ application HTTPS-awareness=False. مانع انتشار عمومی Apache تا اصلاح قرارداد scheme و تست redirect/session.
- Provisioner در حضور Gateway rollback را رد کرد؛ همه gateway/edge/backend fixtureها با ترتیب صحیح revoke و پاک شدند. هیچ certificate یا حساب آزمایشی دائمی باقی نماند.
- ۱۸ کانتینر و سرویس‌های اصلی فعال. RAM available=1800MiB، swap free=2183MiB، دیسک 9.6GiB آزاد (90% اشغال). Feast طبق دستور مالک خارج از محدوده تغییر و بررسی سایت است؛ هیچ دسترسی به فایل، دیتابیس، کش اختصاصی یا HTTP آن انجام نشد.
- مرحله بعد: انتخاب یک hostname مستقل برای canary عمومی و مسیر ingress با connector اختصاصی (بدون مجوز مشترک nobody، دستکاری MCP tunnel یا اتصال خودکار سایت موجود)، گواهی معتبر/renewal، lifecycle اجرایی و آزمون برنامه واقعی. گواهی آزمایشی به معنای TLS عمومی معتبر نیست. مجوز Root فعلی محدود به provisioning خصوصی است. هیچ ریبوت انجام نشد.
