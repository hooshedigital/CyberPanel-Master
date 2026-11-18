"""Scoped translations for the optional Hoosh Smart Backup panel."""
LABELS = {
  "en": {
    "title": "Smart Backup · HooshDigital",
    "subtitle": "Secure, resource-conscious, read-only inventory inside CyberPanel",
    "full_backups": "Local daily backups",
    "retention": "Current retention: 7 days",
    "size_daily": "Daily backup archive size",
    "size_note": "Sum of recorded archive sizes, not actual Restic usage",
    "free": "Free server disk space",
    "disk_used": "Disk used",
    "engine": "Backup engine V1",
    "local": "Recent local backups",
    "date": "Date", "archive": "Archive size", "checksum": "Checksum file",
    "checksum_present": "Recorded; not verified now",
    "checksum_missing": "Not recorded",
    "none": "No backups in the current sanitized inventory",
    "core_backups": "CyberPanel backups",
    "schedule": "Backup schedules",
    "refresh": "Refresh",
    "warning": "Backup engine V1 remains disabled until restore testing and encrypted destination setup are complete. This page cannot run backups, deletion or restoration. A recorded checksum does not confirm integrity.",
    "footer": "An independent HooshDigital add-on; CyberPanel's commercial license features are unchanged.",
    "lang": "Language"
  },
  "fa": {
    "title": "پشتیبان‌گیری هوشمند · هوش دیجیتال",
    "subtitle": "نمای مدیریتی امن، کم‌مصرف و فقط‌خواندنی در داخل سایبرپنل",
    "full_backups": "بکاپ‌های روزانه محلی",
    "retention": "دوره نگهداری فعلی: ۷ روز",
    "size_daily": "حجم آرشیوهای روزانه",
    "size_note": "مجموع حجم ثبت‌شده آرشیوها؛ نه مصرف واقعی Restic",
    "free": "فضای آزاد دیسک سرور",
    "disk_used": "فضای مصرف‌شده",
    "engine": "وضعیت موتور بکاپ V1",
    "local": "نسخه‌های محلی اخیر",
    "date": "تاریخ", "archive": "حجم آرشیو", "checksum": "فایل چک‌سام",
    "checksum_present": "ثبت شده؛ فعلاً بررسی نشده",
    "checksum_missing": "ثبت نشده",
    "none": "بکاپ قابل نمایشی در فهرست فعلی پیدا نشد",
    "core_backups": "بکاپ‌های سایبرپنل",
    "schedule": "زمان‌بندی بکاپ",
    "refresh": "تازه‌سازی",
    "warning": "موتور V1 تا تکمیل آزمون بازیابی و تنظیم مقصد رمزگذاری‌شده فعال نمی‌شود. این صفحه امکان ایجاد، حذف یا بازیابی بکاپ ندارد. ثبت چک‌سام به معنی تأیید سلامت آن نیست.",
    "footer": "افزونه مستقل هوش دیجیتال؛ امکانات تجاری دارای لایسنس سایبرپنل تغییر نمی‌کنند.",
    "lang": "زبان"
  }
}
def labels(lang):
    if lang not in LABELS:
        raise ValueError("unsupported language")
    return LABELS[lang]
