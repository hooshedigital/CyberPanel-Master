# CyberPanel Master v0.1.0 — safety and rollout gates

This public repository contains add-on code only. No private host files, server passwords, API keys, or CyberPanel license bypasses.

## CAPTCHA
- Verify exact current login POST route and JSON field names on the live installation first.
- Cloudflare Turnstile requires a dedicated managed widget for manage.hooshedigital.ir.
- Siteverify is mandatory server side. Verify success, hostname, and action. Challenge response is single-use.
- Keep secret in root-owned group-readable file with no world read; never pass as command-line arg to Owner Broker or GitHub.
- Patch existing login Javascript to forward captcha_token, and add widget without replacing password, session or CSRF checks.
- Test expired, missing, invalid, cross-domain and correct tokens on isolated staging; verify successful admin login, failed password, and rollback access.
- Turnstile middleware remains disabled until all checks pass. Do not lock out admin.

## Agent
- PARSA pilot Heartbeat exists; Hoosh CyberAgent deployment not assumed from GitHub README.
- AI Gateway source documents candidate endpoints, not verified live. Never send Provider/Gateway keys to browser.
- Read-only diagnosis is distinct from approved execution. No Web-to-Root API endpoint.

## Languages
- Default English, optional Persian per-user for HooshDigital add-ons.
- Keep CyberPanel original theme/navigation and independent core version label.
- Connect the current Smart Backup/Cyber Agent templates after inspecting exact live versions.
- Core-wide translations require gettext and a separate tested rollout.

## Operations
- Before modifying source, verify installed hashes/versions and backup bytes plus mode, uid, gid.
- After changing only approved files, smoke direct and domain HTTPS on 443/8090; verify guest redirect, 403 for non-admin, valid form login.
- Do not restart LSWS broadly while unrelated OpenHands vhost configuration check fails.
- Code in this branch is NOT automatically deployed.

## Dedicated Cloudflare Turnstile widget provisioned

**Chronology correction (20 Nov 2026):** The 18 Nov server verification report records that the managed widget for `manage.hooshedigital.ir` was **embedded and active** with public sitekey `0x4AAAAAAGG-PjEcCDvWgNdr`; missing/invalid tokens against `/verifyLogin` returned HTTP 403. The report does **not** demonstrate a successful real-browser login or completion of 2FA. The source-branch public key was different and is corrected in the audit branch, but installed source ↔ repository parity is still unverified. The private Siteverify secret remains server-only and must never be copied into GitHub, logs, argv, or chat. Do not redeploy CAPTCHA until browser-positive valid-token/login, lockout/CSRF/MFA, and owner recovery-path tests succeed.
