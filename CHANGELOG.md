# CyberPanel Master — Changelog

## 0.2.0-dev.1 — 2026-11-20 (source prerelease, NOT deployed)

### Product architecture
- CyberPanel Master is the name of the entire hosting panel; the nested `/backup/master/` page becomes **Operations Center**.
- Core version is tracked separately from the product version. Installed read-only dashboard remains the prior version until gated rollout.

### Core-wide internationalization (foundation, not complete)
- English-first `LocaleMiddleware` implementation and native POST+CSRF language selection in the global Core shell.
- Strict staging overlay builder including settings, URLconf, base HTML, middleware module and compiled Persian locale (no blind live replacements).
- 142 source-audited Persian translations of the upstream stable shared navigation shell.
- Full upstream Core audit: 34 modules / 2,241 HTML+JS files / 6,233 existing translation tags / 30,559 possible unwrapped UI strings (heuristic, **not distinct confirmed missing translations**).
- Core-wide page content and JS translations are **not yet complete**.

### Agent experience
- More legible native status-grid cards, with actual `hoosh-cyberagent` heartbeat, severity counts, allowed service labels in English and Persian, and mobile-responsive scoped CSS.
- Mission execution from the browser is **not yet enabled**; Owner Broker approval and audit remain required.

### Independent WordPress security scanning
- Local read-only bounded PHP threat-triage scanner; true Quick and Full resource profiles, bilingual explanations and human-review recommendations.
- Never invokes paid CyberPersons API, never runs PHP, never modifies files. AI inference and live website ACL/job scheduler remain **not connected**.

### Security and rollout
- 67 Python tests and 4 JavaScript storefront tests expected on the branch (verify the current CI run for the exact final test count).
- No Core login, Turnstile, 2FA, DNS, SSL, hosting customer files or production site state changed by this prerelease branch.
- Source review: [PR #31](https://github.com/hooshedigital/CyberPanel-Master/pull/31).
- Technical acceptance: [Full product blueprint](docs/CYBERPANEL_MASTER_FULL_PRODUCT_REBUILD_FA.md).

## 0.1.0 — previously installed read-only extension

- Scoped Master dashboard, Smart Backup inventory, existing agent heartbeat and basic storage report views.
- This version did **not** provide full Core translation or an operational independent AI Scanner.
