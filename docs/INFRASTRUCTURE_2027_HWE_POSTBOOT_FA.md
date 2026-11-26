# نتیجه استقرار کرنل HWE و اعتبارسنجی پس از بوت

۲۶ نوامبر ۲۰۲۶، ۱۷:۵۱ UTC. بوت جدید در ۱۷:۱۳:۰۲ UTC تأیید شد.

- کرنل 6.8.0-149-generic واقعاً در حال اجراست؛ شناسه بوت با قبل متفاوت است. MGLRU enabled=0x0007؛ ZSWAP enabled=Y، zpool=zsmalloc، compressor=lzo، max_pool_percent=15، shrinker_enabled=Y.
- هر ۱۸ کانتینر با همان شناسه قبل از بوت برگشتند؛ ۱۴ مورد healthy و چهار مورد running بدون وضعیت healthcheck. هر ۹ بررسی سرویس/تایمر اصلی فعال، صفر failed unit، dpkg --audit خالی.
- مانیتور سایت ۷ مسیر HTTP200. بررسی عمومی سه سایت نمونه بعد از دائمی کردن GRUB نیز HTTP200. زمان درخواست‌های نمونه 0.249s، 1.417s، 0.633s؛ benchmark بار یکسان نیست.
- Valkey سایت واقعی: PONG و WordPress external object cache فعال. هشدار قبلی ionCube تکراری در PHP 8.1 باقی است.
- RAM available=1634MiB از 3922MiB، Swap used=725MiB از 3071MiB؛ reserve 1GiB بدون مصرف. Memory PSI some avg60=0.00، CPU PSI some avg60=38.90، IO PSI some avg60=0.31. دیسک حدود 11GiB آزاد و 89% اشغال. مقایسه کاهش مصرف Swap بعد از reboot اثبات بهبود پایدار تحت workload یکسان نیست.
- پس از تأیید معیارها، GRUB_DEFAULT به entry 6.8 تغییر یافت، update-grub و grub-script-check موفق. دو کرنل 5.15.0-202 و 5.15.0-204 با initramfs و menu entry حفظ شدند. منوی بازیابی پنج ثانیه. بکاپ تنظیمات قبلی محلی موجود است. ریبوت دوم انجام نشد؛ انتخاب پیش‌فرض تأیید شده ولی بوت دوم با این default هنوز آزموده نشده.
- پایان مرحله فعال‌سازی HWE و بهینه‌سازی پایه حافظه؛ نه پایان همه توسعه‌های Web Engine Manager. اتصال عمومی Apache/FrankenPHP، provisioning از Create Website، TLS و جداسازی عمومی، ارزیابی ZSTD، مهاجرت Ubuntu، و بررسی چرخه امنیتی PHP-FPM 8.1 باقی‌اند. هشدار مصرف دیسک همچنان برقرار است. نسخه شاخه توسعه‌ای است؛ هیچ merge به main یا انتشار پایدار نهایی انجام نشده.
