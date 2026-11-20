# CyberPanel Master — HooshDigital

> **Product scope correction (20 November 2026):** CyberPanel Master is the **entire customized CyberPanel distribution**. The page `/backup/master/` is only its **Operations Center**, not the product itself. English is the original/default language and Persian is the additional Core-wide language.
>
> **Current installed version:** Core 3.0 Build 4 / custom Master 0.1.0 (last independently verified). **Next development version:** Master 0.2.0-dev in [Draft PR #34](https://github.com/hooshedigital/CyberPanel-Master/pull/34), **not deployed**. Contains global Django language selector proposal, 168 initial Persian gettext strings, visual redesign, and independent static WordPress scanner source. Do not claim the full Core is localized or the scanner live until the exact production source and browser acceptance gates pass. [Full scope and release plan](docs/CYBERPANEL_MASTER_V020_GLOBAL_SCOPE_FA.md).

**Status:** CyberPanel Master v0.1.0 **partially deployed and server-verified** on CyberPanel Core **3.0 Build 4** (18 November 2026). Native branding, Master dashboard, English/Persian Smart Backup, read-only status bridge and Cloudflare Turnstile are present on the live server. Browser-positive login/2FA test and public AI Gateway repair remain open. Read the [exact production verification report](docs/PRODUCTION_VERIFICATION_20261118_FA.md).

CyberPanel Master is an independent extension layer over the installed open-source CyberPanel, **not** a commercial Premium license unlock or a full fork. Its goal is to deliver a professional bilingual hosting panel with a secure login CAPTCHA, actionable monitoring, Smart Backup and integrations with PARSA, Hoosh CyberAgent and AI Gateway while retaining CyberPanel's native design.

## Source included in this repository

- `master_extensions/turnstile_core.py`: fail-closed Cloudflare Turnstile server-side token verification (validates hostname and action).
- `master_extensions/login_captcha.py`: guarded Django login middleware; **the repository branch has a proposed root-controlled feature flag not yet installed verbatim**. The production middleware is already connected to `/verifyLogin` and rejected missing/invalid tokens with HTTP 403. Do not deploy the branch variant over the live version without separate acceptance testing.
- `master_extensions/i18n.py`: scoped English/فارسی labels and RTL/LTR preference.
- `master_extensions/master_view.py`: native admin-only, read-only Master portal for PARSA, Hoosh CyberAgent, hosting health and AI Gateway status, each with distinct verified availability.
- `master_extensions/templates/backup/cyberpanel_master.html`: CyberPanel base-template page with **five** cards including a separate verified PARSA AI Router, plus bilingual labels and version footer.
- `master_extensions/version.py`: Master v0.1.0, separate from the verified installed CyberPanel Core version.
- `master_extensions/tests/`: isolated security/localization tests, run automatically by GitHub Actions.

## Security and installation

No passwords, AI provider keys, API secrets, backup archives, customer data, root command execution or CyberPanel commercial license bypasses are included. **The live Turnstile is active** with its secret stored server-side only; invalid/missing token tests passed, but a successful interactive login token and 2FA still require real-browser verification. Public AI Gateway was HTTP 503 on read-only checks; local PARSA AI Router remains distinct and healthy.

Read [the Persian architecture guide](docs/ARCHITECTURE_FA.md) and [deployment gates](docs/DEPLOYMENT_GATES.md). A GitHub repository commit is not proof of production installation.

## Upstream and customization versions

The installed **CyberPanel Core 3.0 Build 4** was verified from `/usr/local/CyberCP/version.txt` and exposed in the Master UI. Custom extension version is **CyberPanel Master v0.1.0**. Core and extension versions remain separately displayed.

---

## WHMCS under CyberPanel Master — Commerce Center (development)

**Repository ownership decision (20 Nov 2026):** WHMCS integrations, product and package factory, affiliate/partner marketing, invoice/payment lifecycle, hosted services, Linux/VPS provider adapters, and identity work are all managed under **CyberPanel-Master**. WHMCS remains the billing source of truth; CyberPanel controls real hosting accounts and a separate provider handles VPS resources.

- [WHMCS subsystem boundaries](whmcs/README.md)
- [Persian commerce and Premium-compatible development roadmap](whmcs/ROADMAP_FA.md)
- [Existing CyberPanel API audit plan](whmcs/API_EXISTING_AUDIT_FA.md)
- [Main storefront and safe WHMCS checkout contract](docs/WEBSITE_COMMERCE_V1_FA.md)
- [GitHub issues #4–#11](https://github.com/hooshedigital/CyberPanel-Master/issues)

A **read-only, admin-only WHMCS Commerce Center section** is staged in the CyberPanel Master native template and displays planned modules. Until the real WHMCS installation and previously built CyberPanel API are verified, it displays no fabricated data, billing API state or working provisioning control. The current WHMCS admin link opens a separately authenticated login. **There is no root impersonation, premium license bypass, or production installation in this branch.**

## 2026-11-20 source/UI/i18n/CAPTCHA audit (staging only)

Before any new live deployment, consult the [Core/UI/i18n/CAPTCHA audit](docs/CORE_UI_I18N_AUDIT_20261120_FA.md) and [license-safe independent premium feature roadmap](docs/PREMIUM_FEATURE_PARITY_20261120_FA.md).

- Repo source and installed panel **are not guaranteed identical**; historical Core version is **3.0 Build 4** while the Master extension is **0.1.0**.
- New WHMCS Commerce tiles use the existing CyberPanel Master CSS classes and *already-used* icon classes, not another CSS framework. The source branch does not change base navigation.
- Existing scoped English/Persian translations gained template direction and backup status fixes; full upstream Core translation is still an **open task**.
- The Turnstile public sitekey in the source was inconsistent with the 18 Nov production report; the staging source now uses the documented public key and supports root-managed configuration. Actual browser login + 2FA and source parity still must pass **before rollout**.
- Historical `cp-whmcs` and `hooshcloud` module evidence was recovered, but API source was **not read live** in this review; no duplicate integration is authorized until inventory.
- Disk use was around **92%** by server `df` on 20 Nov. Backups need a validated offsite destination and rollback.
- Pending release gates: [core/UI #13](https://github.com/hooshedigital/CyberPanel-Master/issues/13), [en/fa Core #14](https://github.com/hooshedigital/CyberPanel-Master/issues/14), [CAPTCHA #15](https://github.com/hooshedigital/CyberPanel-Master/issues/15), [Premium counterparts #16](https://github.com/hooshedigital/CyberPanel-Master/issues/16), [old API #10](https://github.com/hooshedigital/CyberPanel-Master/issues/10).

**All source changes are on an isolated review branch. No live WordPress, WHMCS, CyberPanel or DNS configuration was changed.**

## Linux Storage & CyberAgent Operations (staged 2026-11-20)

A native bilingual CyberPanel Master operations page now includes low-cost root filesystem/inode indicators, bounded asynchronous disk-category reports, safe cache cleanup previews, an admin-only confined workspace navigator, and status from the **existing** `hoosh-cyberagent` heartbeat contract. No global theme/icon/core layout modifications were made.

- [Architecture, limitations and staged acceptance (فارسی)](docs/LINUX_STORAGE_AGENT_OPERATIONS_V1_FA.md)
- [Disk inventory #23](https://github.com/hooshedigital/CyberPanel-Master/issues/23), [cleanup broker #24](https://github.com/hooshedigital/CyberPanel-Master/issues/24), [file moves #25](https://github.com/hooshedigital/CyberPanel-Master/issues/25), [agent worker bridge #26](https://github.com/hooshedigital/CyberPanel-Master/issues/26)

The nonroot systemd collector is a **disabled deployment proposal**, not installed. File moves, deletions and web-triggered agent commands remain unavailable until Owner Broker, audit, rollback, and production source/parity review have passed. The current hosting website File Manager and SSL configuration are untouched.

## Original project roadmap


Professional deployment, configuration, testing, automation and WHMCS integration project for CyberPanel-based hosting infrastructure.

## Goal

Build a secure, repeatable and documented CyberPanel hosting infrastructure that can later be automated and integrated with WHMCS.

## Roadmap

### Phase 0 — Git & GitHub
- Git configuration
- GitHub SSH authentication
- Repository structure
- VS Code Remote SSH
- Git workflow

### Phase 1 — CyberPanel Installation
- Server preparation
- System requirements verification
- CyberPanel installation
- Initial access verification

### Phase 2 — Configuration
- Security
- Firewall
- DNS
- SSL
- Web services
- Database
- Email
- Backup
- Performance

### Phase 3 — Testing
- Service testing
- DNS testing
- SSL testing
- Security testing
- Performance testing
- Backup and recovery testing

### Phase 4 — Automation
- Installation scripts
- Configuration automation
- Templates
- Testing automation
- Versioned releases

### Phase 5 — WHMCS
- WHMCS installation
- Server integration
- Provisioning
- Service automation

### Phase 6 — Open Source
- Documentation
- Contribution guidelines
- Issues
- Releases
- Community development

## Repository Structure

```text
CyberPanel-Master/
├── README.md
├── .gitignore
├── docs/
├── scripts/
├── config/
├── tests/
└── whmcs/
```
