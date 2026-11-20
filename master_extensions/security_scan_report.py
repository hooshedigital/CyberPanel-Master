"""Independent WordPress scan profiles and deterministic, bilingual findings.

No paid CyberPersons API, model hallucinations, file modification or secret
exfiltration. Full scans are still resource-capped and may be reported partial.
The frontend must not call this directly; a future ACL-bound per-site worker
owns scheduling and runs under the site's constrained service identity.
"""
from __future__ import annotations

from .wordpress_security_scan import RULES, scan_wordpress

PROFILE_LIMITS = {
    "quick": {"max_files": 300, "max_bytes": 2 * 1024 * 1024,
              "seconds": 4.0, "max_depth": 4},
    "full": {"max_files": 1500, "max_bytes": 8 * 1024 * 1024,
             "seconds": 12.0, "max_depth": 7},
}

ADVICE = {
    "PHP_EVAL_BASE64": {
        "en": "Review code provenance and installed plugin/theme checksums. Do not delete the file automatically.",
        "fa": "اصالت کد و چک‌سام افزونه یا پوسته را بررسی کنید؛ فایل خودکار حذف نشود.",
    },
    "PHP_EVAL_GZINFLATE": {
        "en": "Investigate compressed code and compare with a trusted release before any restoration.",
        "fa": "کد فشرده را بررسی و پیش از بازیابی با نسخه معتبر مقایسه کنید.",
    },
    "PHP_INPUT_COMMAND": {
        "en": "Treat as potentially dangerous shell injection; isolate the site and review execution paths.",
        "fa": "خطر احتمالی تزریق فرمان پوسته را بررسی و مسیرهای اجرا را ایمن‌سازی کنید.",
    },
    "PHP_ASSERT_INPUT": {
        "en": "Review direct input handling and update affected custom PHP components.",
        "fa": "بررسی ورودی مستقیم و به‌روزرسانی اجزای PHP سفارشی پیشنهاد می‌شود.",
    },
}
RULE_INDEX = {rule.id: rule for rule in RULES}


def scan_with_profile(authorized_root, scan_type: str) -> dict:
    if scan_type not in PROFILE_LIMITS:
        raise ValueError("unsupported scanner profile")
    report = scan_wordpress(authorized_root, **PROFILE_LIMITS[scan_type])
    return {**report, "scan_type": scan_type, "provider_cost": 0,
            "execution": "local_read_only"}


def explain_report(report: dict, language: str) -> dict:
    if language not in ("en", "fa"):
        raise ValueError("unsupported report language")
    if not isinstance(report, dict) or report.get("engine") != "static-indicators-v1":
        raise ValueError("unrecognized scanner report")
    records = report.get("findings")
    if not isinstance(records, list) or len(records) > 80:
        raise ValueError("unbounded scanner findings")
    output = []
    for finding in records:
        if not isinstance(finding, dict):
            continue
        rule_id = finding.get("rule_id")
        rule = RULE_INDEX.get(rule_id)
        if rule is None or finding.get("severity") != rule.severity:
            continue
        relative_path = finding.get("relative_path")
        digest = finding.get("evidence_sha256")
        if not isinstance(relative_path, str) or not 1 <= len(relative_path) <= 180:
            continue
        if (not isinstance(digest, str) or len(digest) != 64
                or any(c not in "0123456789abcdef" for c in digest)):
            continue
        # Security boundaries: content is never returned, only authorized
        # relative filename/digest/rule. The consumer must use HTML escaping.
        output.append({
            "rule_id": rule_id, "severity": rule.severity,
            "title": rule.description_fa if language == "fa" else rule.description_en,
            "relative_path": relative_path,
            "evidence_sha256": digest,
            "recommended_review": ADVICE[rule_id][language],
            "action": "review_only",
        })
    return {
        "engine": "static-indicators-v1",
        "language": language,
        "scan_type": report.get("scan_type") if report.get("scan_type") in PROFILE_LIMITS else None,
        "status": report.get("status") if report.get("status") in ("partial", "completed", "unavailable") else "unverified",
        "files_scanned": report.get("files_scanned") if type(report.get("files_scanned")) is int else None,
        "findings": output,
        "ai_analysis_performed": False,
        "automatic_remediation": False,
    }
