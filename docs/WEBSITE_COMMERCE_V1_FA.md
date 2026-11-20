# HooshDigital — Website UI/UX + WHMCS + CyberPanel | v1 acceptance plan

**Scope:** safe staging source on branch \`feat/hoosh-storefront-whmcs-ux-v1-20261120\` of \`hooshedigital/CyberPanel-Master\`. **NOT production release.**

## Confirmed observations vs unknowns (2026-11-20)

- Confirmed in owner's Cloudflare account: \`hooshedigital.ir\` has an **active** zone and A records for \`hooshedigital.ir\`, \`www.hooshedigital.ir\` and \`manage.hooshedigital.ir\`. No zone for \`hoshdigital.ir\` was listed in this connected account. **No DNS edits performed**.
- Existing CyberPanel Master staged PR #2 documents v0.1.0, native Persian/English admin dashboard, security-related middleware and some past production verification. Do not replace installed modules with source from this new branch until source-vs-production parity is tested.
- WHMCS host URL, license/version, actual products/PIDs, registered domain seller, CyberPanel provisioning module compatibility, payment gateway and successful transaction **not independently verified live**.
- Historical recovery notes say WHMCS was newly installed, prices intended in **toman**, and **Zarinpal** chosen; this is not current proof of working checkout.
- Production is reported to have high disk usage; **do not take large unplanned local backups** or blindly restart LiteSpeed/Django.

## Responsibility boundaries (the critical decision)

| Component | Owns | Explicitly does not own |
| --- | --- | --- |
| Public website \`storefront/\` | Marketing, product discovery, accessible responsive UI, safe checkout navigation | Client credentials, invoices, card details, payment verification, direct root/shell, real server provisioning |
| WHMCS | Product/currency/tax catalog, verified invoices, checkout/payment gateway, clients, domain registrar, eligible provisioning triggers | Web hosting operating-system administration |
| CyberPanel and its scoped WHMCS server module | Create/suspend/unsuspend hosting accounts per authorized and paid service; service status | Billing truth, direct creation of VPS inventory, registration of domains |
| VPS/cloud provider integration (later) | Creation/allocation of actual VPS resources after confirmed order | Arbitrary shell access from website |
| CyberPanel Master admin | Read-only health + navigation to separately authenticated WHMCS admin | Cross-system admin impersonation or shared super-admin cookies |

**No database merging, shared login passwords, exposing WHMCS API credentials to Javascript, or direct browser-to-root operations.**

## Source delivered

- \`storefront/index.html\`: dedicated Persian RTL front page, responsive service cards (hosting/VPS/domain), clear order path and disclaimers.
- \`storefront/styles.css\`: design system with dark layout, contrast, keyboard focus and reduced motion.
- \`storefront/app.js\`: **only** HTTPS links to configured WHMCS on an allowlisted \`hooshedigital.ir\` host; verified integer product ids; no API secret; no payment process in browser.
- \`storefront/public-config.json\`: safe fail-closed default with no live links. **Deploy this only after correct host and product IDs are confirmed**. Values in this repository are intentionally disabled, not made-up prices.
- \`master_extensions/billing_links.py\` and Master view: optional CyberPanel admin-only navigation to WHMCS admin (env: \`HOOSH_WHMCS_ADMIN_URL\`), **not SSO**. WHMCS handles its own admin authentication and 2FA.
- Unit and contract tests; no network calls and no real transactions.

### Public storefront configuration example — do not assume the URL exists

After verifying an actual HTTPS WHMCS deployment and DNS, configure \`storefront/public-config.json\` on the release branch or via a secured deployment override:

\`\`\`json
{
  "schemaVersion": 1,
  "billingBaseUrl": "https://billing.hooshedigital.ir/",
  "products": {
    "hosting": { "pid": 17 },
    "vps": { "pid": 44 }
  }
}
\`\`\`

Values \`17\`, \`44\`, and this billing hostname **are examples, not confirmed production facts**. Never publish actual customer data or secret tokens in public config. The checkout price remains authoritative **only** in WHMCS. Domain registration goes to \`cart.php?a=add&domain=register\` (availability checked at registrar during WHMCS flow), not a fabricated public DNS lookup.

## Integration plan (in dependency order)

1. **Inventory / safe snapshot:** record live site WordPress version/themes/plugins, content/pages/media, permanent links, current origin/vhost/document root, HTTPS/redirects, cron, WHMCS version/license/URL/payment module/product IDs/currency, CyberPanel version, current services and secret locations. Read only.
2. **Backups / rollback:** independent encrypted offsite backups and verified restore of WordPress DB+uploads+config, WHMCS DB+config+attachments+cron (secrets protected), web server configs, DNS export, certificate metadata. Keep original owners/modes and checksum manifests. Verify restore in an isolated environment; define exact traffic cutback steps.
3. **Build preview:** host code at a separate protected staging hostname, not on \`hooshedigital.ir\`. Disable indexing. Configure catalog PIDs only from WHMCS; do not expose WHMCS API identifier or secret in \`public-config.json\`.
4. **WHMCS payment:** audit current gateway module and WHMCS version compatibility. Configure Zarinpal **inside WHMCS** (or a licensed reviewed gateway), with merchant secret stored server-side. Validate toman vs rial, taxes, callback signature/provider verification, unique transaction IDs, duplicate callbacks, paid/unpaid state, refunds, and failed/cancelled payments. Only a *verified paid* invoice should lead to provisioning. Do not rely on browser success redirect.
5. **CyberPanel provisioning:** audit the current official/community CyberPanel WHMCS provisioning module source and compatibility on staging. Set up non-root credentials/scope, server groups, hosting package map, SSL validation, IP restrictions, logs, idempotent create, suspend/unsuspend, quota sync. **Disable automatic termination until a separately approved policy exists.** Do not use CyberPanel as a VPS hypervisor.
6. **Domain selling:** configure accredited reseller/registrar integration in WHMCS with TLD cost/availability, transfer/renewal EPP/IDN rules and currency, then test registration in the provider-approved sandbox. A DNS zone alone cannot sell domain names.
7. **Identity:** for v1 keep WHMCS client login as source of truth. If true single sign-on is desired later, implement verified Auth0/OIDC account linkage and WHMCS \`CreateSsoToken\` **only for a cryptographically authenticated user matched to the exact WHMCS client**, with CSRF, audit and single-use expiry. WHMCS SSO tokens must never be created for an unverified browser identity. Staff entry from CyberPanel Master currently uses a safe link + **separate login/2FA**; never issue customer SSO to impersonate WHMCS admins.
8. **SEO/WordPress cutover:** export complete URL inventory and analytics/search console baselines; map legacy URLs 1:1 to new routes (301); preserve canonical, metadata, sitemap.xml, robots.txt, structured data and original media; verify 404s and top inbound links. Migrate at low traffic with health-check rollback switch. **Do not delete WordPress until proof of restored content, order/pay/provision flow and rollback is signed off.** After retention and approved cutover, retire its code/database and isolate final encrypted archive; remove unused PHP/WordPress routes but **never uninstall global PHP/MySQL** that WHMCS or other sites need.

## Acceptance gates for v1

- [ ] Browser & mobile: navigation, accessibility and RTL layout QA; no placeholder/test prices, no dead checkout URLs.
- [ ] WHMCS test user registration/login and password recovery/2FA pass; admin has distinct scoped access.
- [ ] Hosting order > verified invoice > exactly one CyberPanel hosting account > service details > suspension/renewal test > no unexpected deletion.
- [ ] Domain purchase/transfer sandbox or explicitly approved real low-cost transaction verified end-to-end (not only cart UI).
- [ ] VPS products only offered as automatic if actual provider adapter is tested; otherwise clearly manual provisioning.
- [ ] Zarinpal callback duplicate/failure/cancel/amount+unit/forged status and refund reconciliation pass.
- [ ] SSL + DNS checks, SEO URL comparison and redirection coverage; performance and security scans accepted.
- [ ] Offsite restore verified; exact rollback owner, trigger, route and execution time agreed.
- [ ] Existing admin CyberPanel login and Turnstile/2FA work on supported browser without regression.
- [ ] Independent owner approval for production traffic switch and permanent WordPress retirement.

## Technical test commands (development checkout only)

\`\`\`sh
node --test storefront/tests/*.test.cjs
python3 -m compileall -q master_extensions
python3 -m unittest discover -s master_extensions/tests -v
python3 -m http.server 8080 --directory storefront
\`\`\`

The HTTP server is for **local preview only**, not production. Do not point the main domain at it.

References: WHMCS documented checkout \`cart.php?a=add&pid=X\`, domain registration \`cart.php?a=add&domain=register\`, server module Create/Suspend/Unsuspend/Terminate lifecycle, and SSO \`CreateSsoToken\`. Check pinned WHMCS version docs before installation.

**This staging branch makes NO production DNS, WordPress, payment, WHMCS account, or CyberPanel provisioning changes.**
