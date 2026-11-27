# پاک‌سازی انتخابی و اندازه‌گیری دیسک — ۲۷ نوامبر ۲۰۲۶
مجوز مستقل مالک برای حذف فقط cache بازتولیدپذیر و staging image با بازیابی مستقل تأیید شد. قبل: disk available 11524886528 bytes، APT archives 211861504 bytes، 51 deb، Docker 18 running/46 total. 51 فایل با SHA256 متادیتای محلی مطابقت داشتند. 9 فایل با بیشترین حجم علاوه بر تطبیق هش فایل محلی، از HTTPS مخزن رسمی مجدداً کامل stream شدند و اندازه و SHA256/SHA512 دقیق تأیید شد. قفل fcntl آرشیو APT گرفته شد و فایل‌ها با O_NOFOLLOW، uid0، regular file، nlink1 و بررسی inode حذف شدند. هیچ بسته نصب‌شده حذف نشد.

| مرحله | فایل‌های کش حذف‌شده | allocated bytes | delta disk available bytes |
|---|---:|---:|---:|
| PHP dbg + modules source |4|154193920|154189824|
| PHP84/85 base, Apache binary, binutils-x86-64, Docker Buildx |5|49262592|49262592|
| مجموع |9|203456512|203452416|

آرشیو APT بعد 8404992 bytes (کاهش حدود 96%)، 42 deb باقی، disk available 11723468800 bytes (10.92GiB)؛ df 88% (قبل 89%). اختلاف snapshot کل 198582272 bytes به علت فعالیت هم‌زمان سیستم با مجموع delta دقیق مراحل یکسان نیست. dpkg --audit خالی؛ PHP8.4.28/8.5.13 و Buildx0.30.1 ثابت. تمام 18 کانتینر فعال و 46 کانتینر کل همان ID قبلی، سرویس‌های اصلی و مانیتورها فعال. بدون reboot، حذف backup/volume/image یا تغییر Feast. دو فایل باینری index APT عمداً حفظ شدند چون regenerating CPU هزینه دارد. بازیابی cache: apt-get download exact package versions؛ دسترس‌پذیری آینده تضمین نیست ولی در زمان حذف full hash verified بود. گزارش بدون ادعای افزایش سرعت سایت.

Docker system df: 23.02GB reclaimable تخمینی، نه ظرفیت قطعی. شش staging image دارای RepoDigest محلی بدون رجیستری خارجی تأییدشده؛ نگهداری شد. حذف پرخطر برای بازیابی نسخه‌ها مجاز نیست. حدود 6.1GiB پشتیبان محلی و broker نیز حفظ شدند. مرحله بعد مقصد مستقل خصوصی برای archive و آزمون restore، سپس حذف دقیق با مجوز مستقل. Policy Engine و مانیتورها ادامه دارند.
