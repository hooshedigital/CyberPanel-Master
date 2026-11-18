# CyberPanel Master — HooshDigital

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