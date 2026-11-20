# CyberPanel Master — Linux Storage & CyberAgent Operations V1

**تاریخ:** ۲۰ نوامبر ۲۰۲۶ — **وضعیت:** سورس و آزمون‌های GitHub / Draft PR؛ بدون استقرار در Production.

## تصمیم اصلی

نیازی به بازسازی تمام فایل‌منیجر CyberPanel نیست. **فایل‌منیجر وب‌سایت** در هسته رایگان CyberPanel از قبل امکان browse/edit/move دارد. این پروژه یک **Storage Operations Center** جدید برای تحلیل فضای کلی لینوکس، پیش‌نمایش پاک‌سازی، مانیتور ایجنت موجود و «مرورگر محدود فایل‌های مدیریتی» در ظاهر بومی CyberPanel اضافه می‌کند. SSLهای پیکربندی‌شده مالک و تنظیمات فعلی vhost، DNS، API و LiteSpeed تغییر نمی‌کنند.

## وضعیت شاهدهای زنده

- `df -hT` مورخ ۲۰ نوامبر: پارتیشن اصلی ۹۴GB، مصرف ۸۲GB، آزاد ۷٫۴GB؛ حدود ۹۲٪.
- `lscpd` و `lshttpd` active؛ سرویس `hoosh-cyberagent.service` در فهرست سرویس‌های درحال اجرا دیده شده است. **فعال بودن سرویس اثبات سلامت همه مأموریت‌ها نیست.**
- فایل واقعی ایجنت طبق `hoosh-cyberagent/src/hoosh_cyberagent/runtime.py`: `/run/hoosh-cyberagent/status.json` با `updated_at_unix`, `version`, `status`, `checks_total` و چند فیلد محدود. نسخه سورس Agent در `pyproject.toml` برابر 0.9.0 است؛ نسخه نصب‌شده باید در سرور جدا تأیید شود.
- طبق `deploy/hooshedigital.production.json` در مخزن ایجنت، `auto_remediation=false`, `managed_repair.enabled=false`, `privileged_helper.enabled=false` و `cyberpanel_api.enabled=false` هستند. این فایل **تنظیمات ثبت‌شده در GitHub** است؛ با تنظیمات فعال فعلی سرور یکسان فرض نمی‌شود.
- اجرای CLI موجود: `ops-status`، `resource-status`، `ops-once --dry-run`، `doctor` و ...؛ از اجرای دستورات مخرب از طریق Django جلوگیری شده است.

## قسمت‌های جدید در Master

| کد | قابلیت | الان چه می‌کند | چه چیزی عمداً انجام نمی‌دهد |
|---|---|---|---|
| `operations_center.py` | فضای واقعی روت، inode، گزارش دسته‌بندی، cleanup preview و heartbeat | خواندن کم‌هزینه وضعیت دیسک + فایل‌های JSON کوچک با حد تازگی | بدون shell، scan سنگین در request، حذف/پاک‌سازی |
| `storage_probe.py` | تحلیل دسته‌های logs/cache/containers/backup | اسکن اختیاری با O_NOFOLLOW و سقف ۲۰هزار entry/۳ ثانیه برای هر root؛ گزارش partial اگر ناقص | **به صورت daemon یا cron نصب نشده**؛ مجموع پوشه‌ها لزوماً برابر `df` نیست |
| `cleanup_preview.py` | نامزدهای کش قابل‌بررسی | فقط `.deb`های قدیمی `/var/cache/apt/archives` و `.tmp` قدیمی مسیر اختصاصی ما؛ بدون بازگشت اسم فایل | هیچ `rm`، journal vacuum، apt clean، Docker prune، حذف volume یا backup ندارد |
| `workspace_browser.py` | مرور فایل شبیه SFTP در فضای کاری محدود | فقط listing زیر `/var/lib/hoosh-cybermaster/workspaces`، حداکثر ۸۰ entry، حداکثر عمق ۶، جلوگیری از traversal/symlink/mount | هیچ root filesystem explorer، دانلود secret، انتقال یا حذف بدون broker |
| `agent_workflow.py` | قرارداد اجرای ایجنت واقعی | فرمان‌های موجود Agent را برای worker مستقل با identity `hooshagent` allowlist می‌کند و نتیجه را sanitize می‌کند | **Django آن را اجرا نمی‌کند**؛ تأیید Owner/Bridge اختصاصی پیش از فعال‌سازی لازم است |
| `master_view.py` / `i18n.py` / `cyberpanel_master.html` | رابط بومی en/fa | استفاده از `cp-tile-grid/cp-tile` و آیکون‌های موجود؛ URLهای قدیمی بدون تغییر | دست‌کاری قالب Core، CSS global و routeهای اصلی |

## Collector آماده برای استقرار آزمایشی (فعلاً غیرفعال)

- `master_extensions/storage_publisher.py` گزارش‌های `storage-report.json` و `cleanup-preview.json` را در دایرکتوری مدیریت‌شده با نگارش اتمیک، `O_NOFOLLOW`، بررسی مالکیت و `fsync` تولید می‌کند.
- فایل‌های `master_extensions/systemd/hoosh-cybermaster-storage.service` و `.timer` نمونه استقرار غیرروت (`User=hooshagent`) با محدودیت RAM ۱۲۸MB، CPUQuota ۵٪، IOWeight ۱۰ و هر حدود ده دقیقه یک بار هستند.
- **هیچ سرویسی در این مرحله نصب یا فعال نشده است**. قبل از فعال‌سازی، وجود مفسر `/usr/bin/python3`، UID/GID `hooshagent`، دسترسی به مسیرهای اسکن، SELinux/AppArmor/permissions، دسترسی Django به خروجی، ارتباط mountها و صحت فایل‌های source با نسخه نصب‌شده بررسی شوند.
- اگر `hooshagent` اجازه خواندن `/var/lib/docker` را نداشته باشد، در UI باید «تأییدنشده / تخمین ناقص» نمایش داده شود؛ به هیچ وجه برای تکمیل نمودار، root غیرضروری یا permission گسترده داده نشود.
- پیش‌نمایش فقط اعداد و دسته‌ها را منتشر می‌کند. هیچ نام فایل حساس، مسیر کامل، داده مشتری یا فهرست backup در report عمومی قرار نمی‌گیرد.

## ابزار پاک‌سازی واقعی — برنامه ایمن

1. نمایش درصد دیسک + inode + دسته‌های حجم با بازه زمانی و **وضعیت ناقص/کامل**.
2. شناسایی موارد قابل پاک‌سازی تنها در allowlist اختصاصی، همراه با تعداد، سایز واقعی block و مدت عمر.
3. **No-op preview** با فهرست candidate و تجمیع حذف پیشنهادی؛ بررسی وضعیت بکاپ خارج‌سروری، capacity و retention policy.
4. دو مرحله تأیید توسط مالک/اپراتور مجاز با نقش، nonce، expiry، scope، challenge token و reason؛ ثبت audit immutability.
5. عملیات فقط در سرویس جدا با UID غیرروت یا کارگزار root دارای تایید مستقل، guard hash/inode و امکان quarantining/rollback. هیچ `rm -rf` یا دستور دلخواه.
6. صرفاً پس از آزمون restore و پذیرش دستی، اجرای محدود فعال می‌شود؛ پاک‌سازی فایل‌های backup، database، Docker volume، maildir و فایل‌های سایت در فاز V1 ممنوع است.

**اهمیت:** پاک‌سازی journal یا Docker build cache بدون بررسی وابستگی‌ها ممکن است خدمت را خراب کند. اسکن preview به‌تنهایی مجوز حذف نیست.

## فایل‌منیجر و جابه‌جایی

- فایل‌منیجر خود CyberPanel برای فایل‌های **وب‌سایت مشتری** باقی می‌ماند؛ این قابلیت در Core رایگان است.
- Workspace browser فعلاً فقط برای directory allowlist مدیریتی در سرور است. اگر فضای کاری هنوز ساخته نشده باشد، UI «پیکربندی‌نشده» نمایش می‌دهد.
- برای Move بین مسیرهای مجاز، فاز بعد باید `source_id/destination_id` را در رابط انتخاب کند، طرح با inode/owner/mode/space/overwrite=false بگیرد، از Owner Broker اجازه بگیرد و توسط service-account در همان FS با no-overwrite atomic semantics اجرا کند. انتقال cross-device، root/system, DB, symlink و backup باید جداگانه طراحی/ممنوع شوند.
- این فاز **هنوز drag/drop عملیاتی ندارد**؛ ظاهر native اولیه برای نمایش و navigation آماده شده است.

## مرکز فرمان ایجنت

- از ایجنت فعلی `hoosh-cyberagent` و PARSA، نه سرویس جدید و تکراری استفاده می‌کنیم.
- حالت‌های Agent از heartbeat واقعی یا **unverified**؛ اگر report timestamp/syntax معتبر نباشد، Connected جعلی نمایش نمی‌دهیم.
- نمایش نسخه، تعداد check و link به نمای قبلی CyberAgent.
- برای عملیات فعال بعدی: approval broker، request queue امضاشده و worker جدا؛ ticket یک‌بارمصرف، TTL، audit، allowlist، no-billable action default.
- موجودی فعلی root و permission به معنی دسترسی مدیریتی خودکار از مرورگر نیست.
- دستورهای `ops-status`, `resource-status`, `ops-once --dry-run` در آداپتور پشتیبانی شده‌اند ولی از خود پنل **هنوز به worker وصل نیستند**؛ هیچ دکمه جعلی نمایش داده نشده است.

## تست و Rollout

```sh
python3 -m compileall -q master_extensions
python3 -m unittest discover -s master_extensions/tests -v
node --test storefront/tests/*.test.cjs
```

**الزام قبل از استقرار:** source ↔ live SHA parity، تست Django route reverse/template compile، 390/768/1440px و en/fa، مشاهده واقعی فایل heartbeat با user lscpd، آزمون CSRF/RBAC/Guest، capacity برای اسکن و اطمینان از بکاپ قابل‌بازیابی در خارج سرور. فعال‌سازی collector جدا با cgroup/IOWeight/timeout و اجرای read-only. در صورت failure، تمام ماژول‌های جدید fail closed می‌شوند و عملکرد هسته اصلی حفظ می‌شود.

## منابع رسمی

- [CyberPanel Website Management](https://cyberpanel.net/KnowledgeBase/home/website-management-2/) — سایت، File Manager موجود و نکات بکاپ.
- [CyberPanel Backup & Restore](https://cyberpanel.net/KnowledgeBase/home/1-backup-restore/) — توصیه بکاپ خارج سرور.
- [CyberPanel Core vs Premium](https://cyberpanel.net/CyberPanel-addons) — فایل‌منیجر معمولی رایگان، Root File Manager تجاری.

**امنیت:** پروژه CyberPanel-Master مخزن public است؛ هیچ token، دیتابیس مشتری، نام فایل محرمانه یا سرور configuration به آن وارد نشده است.
