# CyberPanel Master — عملیات لینوکس، فضای دیسک، پاک‌سازی و مدیریت Agent

**مرحله ۱ (این PR):** UI فارسی/انگلیسی، مدل نمایش داده‌های پاک‌سازی و دیسک و ایجنت به‌صورت **فقط‌خواندنی**. بدون اجرا، جابه‌جایی، حذف، root یا اتصال SFTP. منبع داده باید telemetry ریشه‌دارِ از پیش تولیدشده باشد؛ در غیاب آن UI باید «تأییدنشده» نشان دهد، نه عدد حدسی.

## اولویت‌های فنی

### ۱. مدیریت فضا
- نمایش مصرف کل/آزاد، دسته‌بندی websites/databases/backups/logs/containers/cache/mail/system/other، روند ۷/۳۰ روز، inode usage، هشدار threshold.
- برای مرورگر فایل شبیه SFTP: virtual filesystem **محدود به ریشه‌های صریحاً مجاز**؛ paginated stat/list با max entries، ممنوعیت symlink escape و traversal، RBAC، audit و مالکیت فایل.
- انتقال فایل **فقط در آینده**: طرح دو مرحله‌ای (dry-run → approval → atomic move/verified copy)، بررسی source/destination، quota، available bytes، checksum، collision، permissions، rollback. جابه‌جایی cross-filesystem باید copy+fsync+verify+rename و پاک‌سازی مبدأ فقط بعد از تأیید مستقل باشد.
- فایل‌های دیتابیس فعال، docker overlay2/volumes، mail spool، بکاپ‌های لازم، `/etc`، `/var/lib` و هسته CyberPanel خارج از محدوده عملیات مستقیم UI باشند.

### ۲. پاک‌سازی زوائد
- ابتدا **inventory/dry-run** و تخمین reclaimable bytes؛ هیچ `rm -rf` یا حذف خودکار.
- کاندیدهای بررسی: apt download cache، journal archives قدیمی با سیاست retention، temp files قدیمی که باز نیستند، application cache با owner شناخته‌شده، build artifacts غیرلازم.
- **حذف ممنوع پیش‌فرض:** Docker volumes/images in use، دیتابیس، backup snapshots، log جاری، session/cache مرتبط با login، mail، فایل‌های مشتری و systemd state.
- ثبت علت، backup/rollback، میزان آزادشده واقعی و امکان مشاهده سابقه؛ پاک‌سازی باید approval و scoped executor مستقل داشته باشد.
- به‌علت مصرف فعلی دیسک **۹۲٪**، حتی تولید بکاپ محلی ممکن است خطرناک باشد؛ اول ظرفیت offsite را بسنجید.

### ۳. مدیریت ایجنت نصب‌شده
- سه موجودیت را قاطی نکنید: `hoosh-cyberagent.service` (سرویس OS)، Parsa executor (اجرای مأموریت)، AI Gateway (مسیر مدل).
- صفحه عملیات: status, heartbeat freshness, queue pending/completed/failed, last run, approval requests, policy, audit trail, error categories, safe diagnostics.
- **عمل واقعی فقط با approval مستقل Auth0/Owner Broker و executor محدود**؛ API web نباید arbitrary command/root shell را بپذیرد.
- شرایط توقف: stale telemetry، role mismatch، disk pressure، root approval expired، drift config، failed healthcheck.
- وضعیت اتصال MCP در این جلسه read-only بود و root step-up معتبر نبود؛ کار اجرایی سرور انجام نشده است.

### ۴. ظاهر و تجربه کاربری
- کلاس‌های `panel`, `panel-body`, `cp-tile-grid`, `cp-tile`, `cp-tile-ic` و آیکون‌های FontAwesome موجود؛ هیچ تغییر CSS هسته یا منوی upstream.
- برچسب‌های en/fa با RTL/LTR جدا و ثابت؛ هیچ عدد/مسیر جعلی یا placeholder وانمودشده به داده واقعی.
- تست رگرسیون زبان، مجوز، داده ناقص/قدیمی، mobile viewport و screenshot قبل از انتشار.

## منبع داده و قرارداد امن

سه گزارش JSON جداگانه `disk-inventory.json`، `cleanup-candidates.json`، `agent-operations.json` در مسیر root-owned status از قبل موجود. هر گزارش باید `schema:1` و `generated_utc` داشته باشد؛ `master_view._report` آن‌ها را با سقف حجم، عدم symlink و freshness کنترل می‌کند. **Producer این گزارش‌ها هنوز طراحی/نصب نشده**؛ UI تا آن زمان فقط پیام «در انتظار تله‌متری» نشان می‌دهد. هیچ مرور فایل از web worker و هیچ اجرای فرمانی اضافه نشده است.

## کنترل استقرار
- PR پیش‌نیاز: #17؛ سپس بررسی Source↔Production، تست مرورگر و بکاپ offsite.
- استقرار مرحله‌ای فقط پس از مرور مالک و داشتن rollback.


## مرحله ۲ — تولیدکننده تله‌متری بدون عملیات تخریبی

فایل `master_extensions/ops_collector.py` با کتابخانه استاندارد Python نوشته شده و تنها metadata فایل‌ها و `statvfs` را می‌خواند. گزارش‌ها با `bridge.emit` به‌صورت اتمیک در مسیر root-owned موجود ذخیره می‌شوند؛ بدون نام فایل/مسیر حساس، محتوای مشتری، subprocess، API ورودی وب یا حذف واقعی. **کد جدید تا نصب و فعال‌سازی آگاهانه، روی سرور اجرا نمی‌شود.**

- `disk-inventory.json`: آمار دقیق پارتیشن اصلی، درصد واقعی مشابه `df` (فضای قابل استفاده بدون reserved blocks)، inode و نمونه محدود دسته‌بندی سایت/دیتابیس/بکاپ/لاگ/Docker/کش/ایمیل/سیستم.
- `cleanup-candidates.json`: فقط تخمین قابل بررسی از فایل‌های `.deb` در apt cache، آرشیو ژورنال بالای ۳۰ روز و فایل‌های عادی قدیمی در `/var/tmp`. هیچ فایل مبدأ در خروجی منتشر نمی‌شود.
- بودجه اسکن حداکثر ۶ ثانیه، ۳۰۰۰ مدخل برای هر ریشه دسته‌بندی و ۲۵۰۰ مدخل برای هر گروه پاک‌سازی؛ برخورد با mountpoint و symlink متوقف/رد می‌شود؛ فایل hardlink دوباره حساب نمی‌شود.
- **مهم:** بخش `coverage=sampled` و `category_scans.complete` یعنی حجم دسته‌بندی‌ها فقط *نمونه* است و حتی `complete=true` به معنی شمارش کل پارتیشن نیست. موجودی کامل یا SFTP مرورگر فایل هنوز پیاده نشده.
- نمونه‌های پرونده‌های ظاهراً زائد، حتی با سن بالا، مجوز پاک‌سازی نیستند: ممکن است process آن‌ها را باز داشته یا سرویس به آن‌ها نیاز داشته باشد.

برای نصب آینده از unit/timer پیشنهادی `deploy/systemd/hoosh-cybermaster-ops.service` و `deploy/systemd/hoosh-cybermaster-ops.timer` فقط پس از بررسی در staging و انطباق مسیر checkout استفاده شود. فایل سرویس را بدون بررسی و تأیید مالک به production منتقل نکنید.
