"""English and Persian labels scoped to new modules; never switch core UI globally."""
LANGUAGES = ("en", "fa")
COOKIE = "cybermaster_lang"
LABELS = {
 "en": {
  "brand":"CyberPanel Master","agent":"Cyber Agent","agent_subtitle":"Hosting intelligence and safe operations",
  "overview":"Overview","health":"Hosting health","parsa":"PARSA executor",
  "server_agent":"Hoosh CyberAgent","gateway":"AI Gateway","router":"PARSA AI Router","backup":"Smart Backup",
  "issues":"Confirmed incidents","disk":"Disk usage","ram":"Available memory",
  "check":"Health check","status":"Status","inspection":"Recommended next step",
  "ok":"Healthy","failed":"Needs attention","unknown":"Not verified","idle":"Idle",
  "connected":"Connected","offline":"Offline","waiting":"Waiting for telemetry",
  "no_actions":"Monitoring only. Changes require separate owner approval.",
  "gateway_desc":"Routes AI requests to approved providers; it does not execute server commands.",
  "router_desc":"Local model router. Healthy status does not prove access to the public AI Gateway.",
  "agent_desc":"Monitors infrastructure and proposes safe operations; no direct web-to-root access.",
  "parsa_desc":"Plans and executes approved missions through its separate executor.",
  "gateway_unverified":"Gateway live connection not verified",
  "agent_unverified":"CyberAgent production deployment not verified",
  "go_back":"Back to CyberPanel","language":"Language","english":"English","persian":"فارسی",
  "read_only":"Read-only dashboard","available":"Available","not_ready":"Not configured",
  "count":"Total","date":"Date","size":"Size (GB)","checksums":"Checksum recorded",
  "last_update":"Last updated","local_backups":"Local backup inventory",
  "backup_warning":"Inventory does not prove that restoring a backup will succeed.",
  "core_version":"CyberPanel core","master_version":"Master extension",
  "billing_heading":"Billing & WHMCS","billing_desc":"Open WHMCS with its own identity and 2FA. This is a link, not single sign-on.",
  "billing_open":"Open WHMCS admin","billing_not_ready":"WHMCS admin URL is not configured",
  "commerce_heading":"WHMCS Commerce Center",
  "commerce_intro":"A single admin workspace for the commercial roadmap: billing, products, hosting, affiliates, marketing, Linux and servers.",
  "commerce_warning":"Roadmap only. No live WHMCS connection, payment or provisioning is implied.",
  "commerce_stage":"Target release",
  "commerce_note":"These features are not connected until each integration passes staging and owner approval."},
 "fa": {
  "brand":"سایبرپنل مستر","agent":"ایجنت سایبر","agent_subtitle":"هوشمندی میزبانی و عملیات امن",
  "overview":"نمای کلی","health":"سلامت میزبانی","parsa":"عامل اجرایی پارسا",
  "server_agent":"ایجنت سرور هوش","gateway":"درگاه هوش مصنوعی","router":"مسیریاب داخلی پارسا","backup":"بکاپ هوشمند",
  "issues":"رخدادهای تأییدشده","disk":"مصرف دیسک","ram":"حافظه آزاد",
  "check":"بررسی سلامت","status":"وضعیت","inspection":"اقدام پیشنهادی",
  "ok":"سالم","failed":"نیازمند بررسی","unknown":"تأییدنشده","idle":"آماده‌به‌کار",
  "connected":"متصل","offline":"آفلاین","waiting":"در انتظار داده",
  "no_actions":"این صفحه فقط وضعیت را نمایش می‌دهد. تغییرات به تأیید مستقل مالک نیاز دارند.",
  "gateway_desc":"درخواست هوش مصنوعی را به ارائه‌دهنده مجاز هدایت می‌کند، اما فرمان سرور اجرا نمی‌کند.",
  "router_desc":"مسیریاب مدل‌های داخلی؛ سالم بودن آن به معنی اتصال درگاه عمومی نیست.",
  "agent_desc":"منابع سرور را پایش و راهکار امن پیشنهاد می‌کند؛ از وب به Root دسترسی مستقیم ندارد.",
  "parsa_desc":"مأموریت‌ها را برنامه‌ریزی و از طریق عامل مستقل و با تأیید اجرا می‌کند.",
  "gateway_unverified":"اتصال زنده درگاه هنوز تأیید نشده است",
  "agent_unverified":"استقرار عملیاتی ایجنت سرور هنوز تأیید نشده است",
  "go_back":"بازگشت به سایبرپنل","language":"زبان","english":"English","persian":"فارسی",
  "read_only":"داشبورد فقط‌خواندنی","available":"در دسترس","not_ready":"پیکربندی‌نشده",
  "count":"تعداد کل","date":"تاریخ","size":"حجم (گیگابایت)","checksums":"ثبت چک‌سام",
  "last_update":"آخرین بروزرسانی","local_backups":"آرشیو بکاپ محلی",
  "backup_warning":"وجود فایل بکاپ موفقیت بازیابی را ثابت نمی‌کند.",
  "core_version":"هسته سایبرپنل","master_version":"افزونه مستر",
  "billing_heading":"فروش و صورتحساب WHMCS","billing_desc":"ورود به بخش مدیریت WHMCS با احراز هویت و تأیید دومرحله‌ای خود آن انجام می‌شود؛ این فقط یک لینک امن است.",
  "billing_open":"ورود به مدیریت WHMCS","billing_not_ready":"نشانی مدیریت WHMCS هنوز تنظیم نشده است",
  "commerce_heading":"مرکز مدیریت تجاری WHMCS",
  "commerce_intro":"محیط واحد مدیریت نقشه توسعه مالی، محصولات، پکیج هاست، افیلیت، بازاریابی، لینوکس و سرورها.",
  "commerce_warning":"این بخش نقشه توسعه است؛ اتصال زنده، پرداخت یا ساخت سرویس هنوز از این صفحه انجام نمی‌شود.",
  "commerce_stage":"نسخه هدف",
  "commerce_note":"هر قابلیت فقط پس از تست مرحله‌ای و تأیید مالک به اتصال عملیاتی ارتقا پیدا می‌کند."}
}
def resolve_language(query: str | None, cookie: str | None) -> str:
    if query in LANGUAGES: return query
    if cookie in LANGUAGES: return cookie
    return "en"
def context_for(lang: str) -> dict:
    if lang not in LANGUAGES: raise ValueError("unknown language")
    return {"lang":lang,"direction":"rtl" if lang=="fa" else "ltr","t":LABELS[lang]}

# Dedicated legacy Smart Backup page labels; English is the default UI language.
BACKUP_LABELS = {
 "en": {
  "title":"Smart Backup · HooshDigital",
  "subtitle":"Secure, low-resource, read-only backup inventory inside CyberPanel",
  "local":"Local full-backup archives","retention":"Current retention: 7 days",
  "daily_size":"Daily backup volume","archive_note":"Archive sum; not actual Restic storage usage",
  "disk_free":"Available server disk space","disk_used":"Disk used",
  "engine":"Backup engine V1","local_recent":"Recent local archives",
  "date":"Date","size":"Archive size","checksum":"Checksum file",
  "recorded":"Recorded; not verified in real time","missing":"Not available",
  "empty":"No displayable backups found","cp_backups":"CyberPanel Backups",
  "schedule":"Configure Schedule","refresh":"Refresh Status",
  "warning":"The V1 engine remains disabled until restore testing and an encrypted destination are configured. No backup, delete or restore commands run from this page. A checksum file does not by itself prove integrity.",
  "footer":"Independent of commercial CyberPanel features; original site and service routes remain unchanged.",
  "language":"Language"
 },
 "fa": {
  "title":"پشتیبان‌گیری هوشمند · هوش دیجیتال",
  "subtitle":"نمای امن، کم‌مصرف و فقط‌خواندنی آرشیوهای پشتیبان در سایبرپنل",
  "local":"بکاپ‌های کامل محلی","retention":"دوره نگهداری فعلی: ۷ روز",
  "daily_size":"حجم بکاپ‌های روزانه","archive_note":"جمع حجم آرشیوها، نه مصرف واقعی Restic",
  "disk_free":"فضای آزاد سرور","disk_used":"مصرف دیسک",
  "engine":"وضعیت موتور بکاپ V1","local_recent":"نسخه‌های محلی اخیر",
  "date":"تاریخ","size":"حجم آرشیو","checksum":"فایل checksum",
  "recorded":"ثبت‌شده؛ هنوز بررسی لحظه‌ای نشده","missing":"موجود نیست",
  "empty":"بکاپ قابل نمایش یافت نشد","cp_backups":"بکاپ‌های CyberPanel",
  "schedule":"تنظیم زمان‌بندی","refresh":"تازه‌سازی وضعیت",
  "warning":"موتور V1 تا پایان آزمون بازیابی و تنظیم مقصد رمزگذاری‌شده فعال نمی‌شود. از این صفحه دستور بکاپ، حذف یا بازیابی اجرا نمی‌شود؛ ثبت فایل checksum به‌تنهایی سلامت آن را ثابت نمی‌کند.",
  "footer":"این ابزار مستقل از امکانات تجاری CyberPanel است؛ مسیرهای اصلی سایت و سرویس‌ها تغییر نکرده‌اند.",
  "language":"زبان"
 }
}
