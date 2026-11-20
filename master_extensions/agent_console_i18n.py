"""Scoped bilingual text for the actual installed CyberAgent dashboard.

No network calls or fake operational results. Never translate machine status
values in the data model; translate only presentation text.
"""
from __future__ import annotations

LABELS = {
"en": {
 "title":"CyberAgent · Infrastructure control","subtitle":"Verified hosting diagnostics and agent telemetry inside CyberPanel Master",
 "fresh":"Recent sample","stale":"Live health evidence unavailable","incidents":"Confirmed incidents",
 "parsa":"PARSA brain","linked":"Connected","unverified":"Unverified","agent":"Hoosh CyberAgent",
 "checks":"Checks reported","gateway":"AI Gateway","status":"Status","health":"Service health",
 "read_only":"Read-only monitoring","details":"Investigate before changes",
 "check":"Check","recommendation":"Recommended inspection","updated":"Last report",
 "container":"Container status","sites":"Websites","ssl":"TLS certificates","database":"MariaDB authentication","mail":"Mail queue",
 "site_checked":"Sites checked","site_failed":"Sites failing","expiring":"Expiring in 30 days",
 "untrusted":"Untrusted","missing":"Missing","queue_deferred":"Deferred","queue_total":"Queued",
 "denied":"Denied logins (15m)","ram":"Available RAM","disk":"Disk use",
 "panel":"Panel response","resources":"Resources","diagnostics":"Hosting diagnostics",
 "checks_heading":"Detailed health checks","ok":"Healthy","failed":"Needs review",
 "unknown":"Not verified","ready":"Active","no_actions":"This view does not restart services, delete files or issue root commands.",
 "ops_link":"Open Operations Center","backup_link":"Smart Backup","language":"Language",
 "safe_note":"SSL and mail queue warnings require review; a warning does not by itself prove an outage.",
 "checks_pending":"Waiting for a verified diagnostics sample",
 "next":"Suggested next step","all_checks":"No checks reported",
 "version":"Reported version","queue":"PARSA missions","live":"Live only if verified",
},
"fa": {
 "title":"سایبر ایجنت · مرکز مدیریت زیرساخت","subtitle":"عیب‌یابی سرویس‌ها و پایش واقعی ایجنت در سایبرپنل مستر",
 "fresh":"گزارش تازه","stale":"اطلاعات معتبر پایش در دسترس نیست","incidents":"رخدادهای تأییدشده",
 "parsa":"مغز پارسا","linked":"متصل","unverified":"تأییدنشده","agent":"ایجنت سرور هوش",
 "checks":"بررسی‌های گزارش‌شده","gateway":"درگاه هوش مصنوعی","status":"وضعیت","health":"سلامت سرویس‌ها",
 "read_only":"پایش فقط‌خواندنی","details":"پیش از تغییر، بررسی کنید",
 "check":"بررسی","recommendation":"بررسی پیشنهادی","updated":"آخرین گزارش",
 "container":"وضعیت کانتینرها","sites":"وب‌سایت‌ها","ssl":"گواهی‌های TLS","database":"احراز هویت MariaDB","mail":"صف ایمیل",
 "site_checked":"سایت بررسی‌شده","site_failed":"سایت دارای خطا","expiring":"انقضا تا ۳۰ روز",
 "untrusted":"نامعتبر","missing":"مفقود","queue_deferred":"معوق","queue_total":"در صف",
 "denied":"ورود ناموفق (۱۵ دقیقه)","ram":"RAM آزاد","disk":"مصرف دیسک",
 "panel":"زمان پاسخ پنل","resources":"منابع","diagnostics":"عیب‌یابی میزبانی",
 "checks_heading":"فهرست بررسی‌های سلامت","ok":"سالم","failed":"نیازمند بررسی",
 "unknown":"تأییدنشده","ready":"فعال","no_actions":"از این صفحه دستور Root، حذف فایل یا راه‌اندازی مجدد سرویس صادر نمی‌شود.",
 "ops_link":"ورود به مرکز عملیات","backup_link":"بکاپ هوشمند","language":"زبان",
 "safe_note":"هشدارهای SSL و صف ایمیل نیازمند بررسی‌اند؛ هشدار به‌تنهایی اثبات قطعی اختلال نیست.",
 "checks_pending":"در انتظار گزارش معتبر بررسی‌ها",
 "next":"اقدام پیشنهادی","all_checks":"بررسی‌ای ثبت نشده",
 "version":"نسخه گزارش‌شده","queue":"مأموریت‌های پارسا","live":"تنها وضعیت تأییدشده",
}
}

# Exact names from the installed CyberPanel 3.0 Build 4 CHECKS registry.
CHECK_FA = {
"CyberPanel":("سایبرپنل","وضعیت سرویس lscpd و لاگ‌های پنل را بررسی کنید."),
"LiteSpeed":("لایت‌اسپید","وب‌سرور و پاسخ‌دهی سایت‌های مشخص را بررسی کنید."),
"Docker":("داکر","سلامت اجرای کانتینرها را بررسی کنید؛ داده‌گاه‌ها را حفظ کنید."),
"MariaDB":("ماریا‌دی‌بی","اتصال و لاگ‌های دیتابیس را بررسی کنید؛ تعمیر خودکار جدول انجام ندهید."),
"Postfix":("پست‌فیکس","وضعیت سرویس SMTP را مستقل از تحویل واقعی ایمیل بررسی کنید."),
"Dovecot":("داوکت","وضعیت IMAP را بررسی کنید."),
"Site availability":("دسترسی سایت‌ها","گزارش پایش سایت‌ها را بررسی و دامنه دارای خطا را پیدا کنید."),
"SSL governance":("مدیریت گواهی SSL","پیش از تمدید، گواهی‌های مفقود، منقضی، نامعتبر و تعارض مالکیت را بررسی کنید."),
"Database authentication":("احراز هویت پایگاه‌داده","مبدأ تلاش‌های ناموفق را مشخص کنید؛ رمزها را بدون تحلیل تغییر ندهید."),
"Mail queue":("صف ارسال ایمیل","صف‌های معوق و maildrop را بدون حذف یا ارسال مجدد بررسی کنید."),
"Cron":("کران","زمان‌بند و شواهد اجرای وظایف را بررسی کنید."),
"Panel HTTP":("دسترسی HTTP پنل","HTTPS محلی و صفحه ورود را بررسی کنید."),
"Panel latency":("تأخیر پاسخ پنل","پیش از تغییر تنظیمات، مسیر کند را پروفایل کنید."),
"Disk space":("فضای دیسک","رشد مصرف و فایل‌های قابل‌حذفِ تأییدشده را بررسی کنید و نسخه بازیابی را حفظ کنید."),
"Memory":("حافظه","فشار حافظه و سقف منابع کانتینرها را بررسی کنید."),
"Backup inventory":("فهرست بکاپ‌ها","آخرین بکاپ موفق، یکپارچگی و شواهد آزمون بازیابی را بررسی کنید."),
"PARSA":("پارسا","قلب تپنده ایجنت و صف مأموریت‌ها را بررسی کنید؛ راه‌اندازی خودکار انجام ندهید."),
"PARSA executor":("عامل اجرایی پارسا","بررسی سلامت Docker مربوط به اجراکننده را ببینید."),
"PARSA router":("مسیریاب پارسا","بررسی سلامت Docker مسیریاب را ببینید."),
"Medical staging":("آزمایشی پزشکی","اجرای کانتینر بدون healthcheck اثبات خرابی نیست."),
"Portainer":("پورتینر","اجرای کانتینر بدون healthcheck اثبات خرابی نیست."),
}

def labels(lang: str) -> dict[str,str]:
    if lang not in LABELS:
        raise ValueError("unknown CyberAgent language")
    return LABELS[lang]

def localized_check(row: dict, lang: str) -> dict:
    if not isinstance(row,dict) or lang not in LABELS:
        raise ValueError("invalid check data or language")
    result=dict(row)
    name=row.get("label")
    translations=CHECK_FA.get(name) if lang=="fa" else None
    result["display_label"]=translations[0] if translations else name
    result["display_next"]=translations[1] if translations else row.get("next_step","")
    return result
