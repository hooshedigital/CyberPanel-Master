# ممیزی API قبلی CyberPanel — فقط‌خواندنی، پیش از توسعه

مالک اعلام کرده API مربوط به CyberPanel قبلاً در یک وب‌سایت ایجاد شده است. در این مرحله URL و سورس دقیق API **تأیید نشده‌اند**؛ نمی‌خواهیم adapter موازی بسازیم.

## داده‌های لازم برای پیدا کردن API از محیط مجاز

- مخزن و commit/branch واقعی یا مسیر deployment.
- version/build، مالکیت endpoint و contract (OpenAPI/Swagger/MCP/API documentation).
- فهرست endpointهای read-only و mutation با پاسخ و خطاهای سانیتایز شده (بدون محتوای مشتری).
- مکانیزم authentication با حداقل scope، idempotency keys، logging، TTL و certificate validation.
- ماتریس فرمان: WHMCS invoice/order/catalog/affiliate؛ CyberPanel website/quota/SSL؛ provider VPS capacity.
- آیا ماژول از امکانات Premium یا لایسنس خارجی استفاده می‌کند؟ نسخه و حق استفاده بررسی شود.
- تطبیق status health و timeout/retry behavior در staging.

## محدودیت مهم

نام API یا سرویس براساس حدس انتخاب نشود. برای سلامت سرویس‌ها فقط read-only و بدون دستکاری Root، WHMCS DB یا Docker socket اقدام شود. روی یک سرور تولیدی با مصرف دیسک بالا، backup حجیم در همان volume ممنوع است تا مقصد مناسب بررسی شود.

پیگیری: [Issue #10](https://github.com/hooshedigital/CyberPanel-Master/issues/10).
