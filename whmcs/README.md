# WHMCS — subsystem of CyberPanel Master

**Project owner:** `hooshedigital/CyberPanel-Master`.

Everything related to WHMCS product management, hosting-package mapping, affiliate marketing, reseller roles, automation, payment-gateway contract, customer integration and related admin UI belongs to this repository and its `whmcs/` directory.

## Architecture rule

- **CyberPanel Master:** the unified operator-facing navigation, monitoring, scoped orchestration and security approval.
- **WHMCS:** system of record for customers, product IDs, billing, invoices, paid state, affiliate referrals, campaigns, domain registrar integration and renewals.
- **CyberPanel:** system of record for real web hosting quotas/accounts/domains/SSL and lifecycle of approved services.
- **VPS provider:** source of truth for server/VM resources. Selling VPS is not equivalent to creating a CyberPanel website.
- **Public storefront:** product exploration and secure redirection to verified WHMCS checkout, not a shadow financial DB.

## Directory ownership and future components

```text
CyberPanel-Master/
├── whmcs/
│   ├── README.md                  # ownership, boundaries
│   ├── ROADMAP_FA.md              # staged features and issue links
│   └── API_EXISTING_AUDIT_FA.md   # discovery tasks for existing API
├── master_extensions/
│   ├── commerce_modules.py        # admin UI roadmap registry, not live sync
│   ├── billing_links.py           # HTTPS-allowlisted WHMCS admin login navigation
│   ├── master_view.py             # admin-only central dashboard
│   └── templates/backup/cyberpanel_master.html
├── storefront/                    # public site and safe WHMCS checkout links
└── docs/
    └── WEBSITE_COMMERCE_V1_FA.md  # delivery gates and WordPress migration
```

Develop future integration in `whmcs/integrations/`, `whmcs/contracts/`, `whmcs/tests/` **only after inspecting existing code and compatibility**. Do not fork WHMCS core, import customer's private records, or publish vendor-licensed packages.

## Security & access

Linux root and WHMCS admin are **not the same identity**. Never inject admin cookies, share passwords, use root as application impersonation, or use client `CreateSsoToken` to bypass WHMCS staff login. A CyberPanel admin can navigate to the separately authenticated WHMCS Admin Area via the allowlisted HTTPS link. Future federation, if WHMCS version/provider supports it, requires separately reviewed MFA, role mapping, expiry and audit. If no supported admin federation exists, keep distinct logins and surface approved read-only APIs in Master.

### Important operational boundary

Source / GitHub checklist items marked `planned` or `not connected` are **not running functionality**. No WHMCS API, invoice, affiliate or payment events are invoked by the new UI. No permission to change live production, licensing or financial records is implied.

See [roadmap](ROADMAP_FA.md), [existing API audit](API_EXISTING_AUDIT_FA.md), and issues [#4](https://github.com/hooshedigital/CyberPanel-Master/issues/4)–[#11](https://github.com/hooshedigital/CyberPanel-Master/issues/11).
