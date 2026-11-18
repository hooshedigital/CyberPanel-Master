# معماری CyberPanel Master و AI Gateway

مبنای واقعی بررسی: مخازن hooshedigital/CyberPanel-Master، hoosh-cyberagent، aigateway و hoosh-mcp-source. مستندات repository الزاماً اثبات سرویس زنده نیستند.

## اجزای مستقل

- **CyberPanel Core**: کنترل هاست، کاربران، SSL، ایمیل و دسترسی‌ها. احراز هویت فعلی آن دست‌نخورده می‌ماند.
- **CyberPanel Master v0.1.0**: لایه افزوده روی قالب اصلی و مجوزهای خود CyberPanel، بدون Fork هسته.
- **PARSA**: عامل اجرای مأموریت‌ها، وضعیت Heartbeat و تأیید مالک؛ اکنون نمایش فقط‌خواندنی Heartbeat در Cyber Agent وجود دارد.
- **Hoosh CyberAgent**: پروژه هوش دیجیتال با diagnostics, healing, gateway, watchdog, privileged helper. README نسخه 0.9.0 تصریح کرده نصب Production آن در زمان انتشار اثبات نشده است؛ فقط با تست زنده آن را Online اعلام می‌کنیم.
- **AI Gateway**: مخزن جداگانه React/Supabase برای مدیریت Providerها، مدل‌ها، مسیریابی، failover، لاگ، هزینه و توکن. قراردادی که Repository توضیح می‌دهد OpenAI Chat Completions compatible است. candidate endpoint مستند health: /functions/v1/ai-gateway/api/status، models: /functions/v1/ai-gateway/v1/models، chat: /functions/v1/ai-gateway/v1/chat/completions، در https://supabase.hooshedigital.ir. پورت آزمایشی 4045 PARSA AI Router با این Gateway یکی فرض نمی‌شود.

## مسیر آینده قابلیت ایجنت

۱. مشاهده سلامت سایت‌ها و منابع سرور با منابع telemetry قابل اتکا. ۲. تحلیل مشکلات با مدل‌های Gateway و Runbook. ۳. پیشنهاد راه‌حل با تخمین ریسک، اثر و روش بازگشت. ۴. تأیید مستقل مالک در Root Broker. ۵. اجرای محدود در عامل اجرایی و ثبت audit. اتصال مستقیم Browser به Root یا اجرای دلخواه Shell ممنوع است.

## UI با قالب خود CyberPanel

چهار کارت: Hosting Health، PARSA، Hoosh CyberAgent، AI Gateway. Gateway و CyberAgent در نبود telemetry تازه وضعیت Not verified دارند. بخش Operations آینده برای کارهای نیازمند تأیید خواهد بود؛ وضعیت Read-only با دکمه اجرایی اشتباه گرفته نمی‌شود.

## چندزبانه‌سازی

English پیش‌فرض و فارسی اختیاری، با انتخاب زبان برای هر کاربر؛ فقط بخش‌های اختصاصی HooshDigital در مرحله اول RTL می‌شوند و تم/ناوبری CyberPanel به‌هم نمی‌ریزند. Smart Backup و صفحه Cyber Agent فعلی نیز بعد از بازرسی دقیق قالب زنده به همین adapter متصل می‌شوند. ترجمه کامل Core در مرحله بعد با gettext و بررسی regression انجام می‌شود.

نسخه Footer باید جدا باشد: CyberPanel Master v0.1.0 و CyberPanel Core با نسخه واقعی خوانده‌شده از نصب. تا زمان تأیید مقدار هسته از عبارت Not verified استفاده می‌شود.

## ایمنی

پیش از اتصال AI Gateway باید خطرات تاریخی credential ثابت در سند hoosh-cyberagent/docs/INTEGRATION_CONTRACTS_FA.md دوباره ممیزی و در صورت لزوم رفع شوند. کلیدها و متن مأموریت‌ها نباید به HTML یا GitHub عمومی منتقل شوند. هر نصب نسخه‌پشتیبان، تطبیق SHA، حفظ mode/owner و آزمون HTTP login دارد.
