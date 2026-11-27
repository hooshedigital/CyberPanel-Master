# مدیر ثبت و راه‌اندازی خصوصی موتورهای وب

ابزار مستقل root-only hoosh-engine-provision برای حساب اختصاصی از پیش ایجاد شده و برنامه بررسی‌شده. هنوز نصب/اجرای این نسخه روی سرور و اتصال به پنل انجام نشده است. هیچ دسترسی web-to-root، ایجاد حساب خودکار، DNS، TLS یا مسیر عمومی ندارد.

- قفل سراسری، journal قبل از ایجاد enrollment، کنترل UID/GID و shell، مسیر root-owned و mode 0750، رد فایل symlink/hardlink/ACL/قابل نوشتن توسط دیگران، سقف 20000 ورودی و رد mount دیگر. محتوای برنامه و رفتار PHP همچنان باید از پیش بررسی شود؛ این audit جای sandbox جامع نیست.
- حداقل RAM آزاد 1536MiB، Swap آزاد 1024MiB، دیسک available 12GiB (8GiB ذخیره اضطراری + 4GiB حاشیه پشتیبان) و PSI60 CPU<40/memory<5. روی این میزبان فقط یک enrollment خصوصی وب؛ سایر cache ها جدا هستند.
- فایل ثابت و بررسی‌شده hoosh-health.txt باید دقیقاً حاوی HOOSH_ENGINE_READY و newline باشد؛ آزمون از حساب پروژه، نه root. آزمون static فقط readiness حمل HTTP است، نه سلامت کامل اپلیکیشن.
- plan: بررسی بدون تغییر سایت (دایرکتوری journal و lock محلی ایجاد می‌شود)، apply: enrollment + start + health و در صورت درخواست explicit --persistent ثبت boot dependency. rollback: توقف واحدهای همان پروژه و حذف enrollment/config ایجاد شده؛ فایل برنامه، حساب و DB حذف نمی‌شوند.
- journal root-only؛ در failure یا crash، در صورت باقی ماندن journal، rollback با همان حساب بررسی شود. این قفل فقط عملیات همین ابزار را serialize می‌کند؛ تغییر همزمان دستی توسط root ممنوع است.
- CLI نمونه: hoosh-engine-provision plan example-account --engine frankenphp --domain example.test
- برای apply/rollback فقط پس از بازبینی مالک و آزمون در محیط مجزا. هنوز اتصال Create Website و public proxy مجاز نیست. آزمون‌های CI قرارداد و ترتیب rollback را بررسی می‌کنند، نه استقرار production.

