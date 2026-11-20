/* Public-site code: no secrets, user sessions, provisioning calls, or card details. */
(() => {
  "use strict";
  const warning = document.getElementById("integration-state");
  const login = document.getElementById("client-login");
  const domain = document.getElementById("domain-order");
  const orders = Array.from(document.querySelectorAll("[data-product]"));

  function validBase(input) {
    if (typeof input !== "string" || !input) return null;
    try {
      const url = new URL(input);
      const name = url.hostname.toLowerCase();
      if (url.protocol !== "https:" || url.port || url.username || url.password ||
          url.search || url.hash || !(name === "hooshedigital.ir" ||
          name.endsWith(".hooshedigital.ir"))) return null;
      if (!url.pathname.endsWith("/")) url.pathname += "/";
      return url;
    } catch (_) { return null; }
  }

  function orderLink(base, id) {
    if (!Number.isSafeInteger(id) || id <= 0) return null;
    const url = new URL("cart.php", base);
    url.searchParams.set("a", "add");
    url.searchParams.set("pid", String(id));
    return url.href;
  }

  function activate(node, url) {
    if (!node || !url) return;
    node.href = url;
    node.removeAttribute("aria-disabled");
    node.setAttribute("rel", "noopener noreferrer");
  }

  function configure(config) {
    if (!config || config.schemaVersion !== 1) return;
    const base = validBase(config.billingBaseUrl);
    if (!base) return;
    activate(login, new URL("clientarea.php", base).href);
    const domainUrl = new URL("cart.php", base);
    domainUrl.searchParams.set("a", "add");
    domainUrl.searchParams.set("domain", "register");
    activate(domain, domainUrl.href);
    const products = config.products || {};
    orders.forEach((link) => {
      const product = products[link.dataset.product];
      activate(link, orderLink(base, product && product.pid));
    });
    warning.textContent = "پیش‌نمایش توسعه: لینک‌های سفارش به WHMCS تنظیم شده‌اند؛ پرداخت و تحویل خودکار تنها پس از تأیید آزمون نهایی فعال اعلام می‌شوند.";
  }

  fetch("./public-config.json", { cache: "no-store", credentials: "omit" })
    .then((response) => {
      if (!response.ok) throw new Error("No public configuration");
      return response.json();
    })
    .then(configure)
    .catch(() => { warning.textContent = "پیش‌نمایش سایت؛ پیکربندی فروش هنوز اعمال نشده است."; });
})();
