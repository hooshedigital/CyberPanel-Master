# ممیزی عملکرد و بهینه‌سازی منابع — ۲۶ نوامبر ۲۰۲۶

## مقایسه تاریخی (نمونه دارای delta CPU، میانه)
| بازه UTC | n | MemAvailable MiB | SwapUsed MiB | CPU PSI60 | Memory PSI60 | IO PSI60 | Major faults/s |
|---|---:|---:|---:|---:|---:|---:|---:|
| 13:05–13:15 |11|1221.47|2426.55|60.60|0.41|0.86|0.88|
| 16:15–16:32 |18|1931.01|1582.71|24.97|0.01|0.38|0.79|
| 19:25–19:42 |18|1772.17|926.68|31.20|0.00|0.23|0.20|
مقایسه دوره‌های workload متفاوت است، اثر مستقل تغییر یا benchmark سرعت سایت نیست. بوت در فاصله دو دوره رخ داده. نسبت به baseline: RAM available +45.1%، swap used -61.8%، CPU pressure -48.5%، IO pressure -73.3%، major faults/s -77.3%. فضای آزاد میانه 7.77→9.85GiB؛ دیسک همچنان 90% پر.
 
## تأیید اجرای واقعی
Kernel 6.8.0-149-generic، MGLRU 0x0007، ZSWAP enabled Y/zsmalloc/lzo/max_pool15/shrinker Y، 204733 صفحه معادل حدود 799.7MiB و pool 230146048 bytes (~219.5MiB)، نسبت تقریبی 3.64:1، pool_limit_hit=0، reject_alloc_fail=0، reject_reclaim_fail=242، written_back_pages=33342. آمار لحظه‌ای؛ کاهش نسبت به صفحات خام 72.5% به معنای افزایش RAM فیزیکی نیست. swap اضطراری 1GiB بدون مصرف. تغییر ZSTD یا swappiness پیشنهاد نشد چون شواهد فعلی فشار حافظه کم را نشان می‌دهند.
OLS1.9.4 LSQUIC4.11.1، PHP8.4.28/8.5.13، Docker29.1.3/Compose5.5.1/Buildx0.30.1، cgroup2، live restore=true، Restic0.19.1. 18 کانتینر فعال. Docker log defaults=10m/3؛ فقط دو کانتینر فعلی دارای همین max-size/max-file در metadata هستند؛ تغییر daemon به کانتینر قبلی retroactive نیست.
Canary خصوصی: پنج درخواست TLS معتبر HTTP200، ttfb/total میانه حدود 27.18/27.38ms. حافظه چهار cgroup موتور/edge/gateway/relay مجموع 43905024 bytes حدود41.9MiB، NRestarts=0 در هر چهار. مانیتور فعال و جدیدترین sample local_https_ok=true/public_https_verified=false؛ credential absent؛ DNS/public TLS/renewal/boot persistence مسیر آزمایشی هنوز تکمیل نیست. زمان پاسخ benchmark سایت واقعی یا اینترنت نیست.

## تغییر جدید Production
- CPUWeight سرویس hoosh-github-maintenance.service از 50 به 25 با systemctl set-property دائمی، بدون تغییر PID 1028 یا restart. هدف اولویت نسبی تحت رقابت CPU، نه نصف شدن مصرف CPU. poll=20s حفظ شد. مصرف مشاهده‌شده سرویس حدود3% یک هسته قبل از تغییر.
- drop-in 90-hoosh-resource-budget.conf برای hoosh-resource-monitor.service: MemoryHigh=64M، MemoryMax=128M، TasksMax=32، IOWeight=25. systemd verify و اجرای واقعی موفق، sample تازه، timer فعال. 18 شناسه کانتینر دقیقاً ثابت. خدمات اصلی فعال.
- دو نمونه فوری پس از تغییر: RAM 1738.7، swap945.68، CPU PSI60 30.45، memory0.10، IO2.29. این نمونه‌ها کوتاه و شامل بار ممیزی هستند؛ برای این تغییر تازه ادعای درصد بهبود مستقل نمی‌شود. بررسی 24 ساعت و سنجش workload مشابه لازم است.
- rollback: CPUWeight=50 و حذف فقط drop-in جدید سپس daemon-reload. backup root-only. هیچ reboot یا حذف فایل/تصویر/volume و هیچ تغییر Feast انجام نشد.

## گلوگاه دیسک و برنامه مرحله بعد
Docker system df: image size32.43GB، reclaimable23.02GB (تخمین و shared layers؛ نه فضای قطعی آزادشدنی). 46 containers/18 active. image ls -a metadata شمار 111 شناسه (شامل intermediate/untagged)، 33 دارای reference دقیق container و 78 بدون reference container، از آنها 30 tagged و 48 untagged. این شمار با docker system df (80 images) هم‌تعریف نیست و بدون بررسی manifest/layer/retention/rollback هیچ شناسه‌ای کاندید قطعی حذف نیست. بکاپ‌های /var/backups 3.4G، broker 2.8G، apt archives197M، journal114M. اولویت audit retention و مقصد بکاپ مستقل، سپس انتخاب صریح موارد امن با تأیید جداگانه. 
14 container healthcheck با interval های 5s تا60s؛ تقریباً75 check/min بر اساس interval nominal بدون زمان اجرا. در staging امکان بازبینی interval با حفظ SLA و تست کنترل‌شده وجود دارد؛ نیازمند recreate/مستندات compose و مجوز مستقل. بدون تغییر کانتینرهای موجود. هیچ تنظیمات سایت کارآموز تغییر نکرد. 
هدف 24h: سنجش PSI، major fault، OOM، throttling و latency واقعی تحت بار قابل مقایسه؛ بهینه‌سازی بیشتر بر اساس شواهد نه تغییر بی‌هدف.
