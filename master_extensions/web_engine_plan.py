"""Read-only private engine plan; never calls the shell or writes server state."""
import re

ENGINES = {"apache": "hoosh-apache", "frankenphp": "hoosh-frankenphp"}
DENIED = {"root", "ubuntu", "admin", "nobody", "www-data", "mysql", "redis", "cyberpanel"}


def plan(engine, account, domain, persistent, *, capacity_ok):
    if type(engine) is not str or engine not in ENGINES:
        raise ValueError("Invalid engine.")
    if (type(account) is not str or not re.fullmatch(r"[a-z][a-z0-9_-]{0,30}", account)
            or account in DENIED):
        raise ValueError("Enter a dedicated account name (lowercase ASCII).")
    if type(domain) is not str or not domain.isascii() or len(domain) > 253:
        raise ValueError("Invalid domain.")
    labels = domain.split(".")
    if (len(labels) < 2 or not re.fullmatch(r"[a-z][a-z0-9-]{0,62}", labels[-1])
            or any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", x) for x in labels)):
        raise ValueError("Enter a canonical lowercase domain without a scheme or port.")
    if type(persistent) is not bool:
        raise ValueError("Invalid boot preference.")
    prefix = ENGINES[engine]
    command = f"/usr/local/libexec/hoosh-engine-provision plan {account} --engine {engine} --domain {domain}"
    if persistent:
        command += " --persistent"
    return {"engine": engine, "account": account, "domain": domain,
            "persistent": persistent, "capacity_ok": capacity_ok is True,
            "project_root": f"/srv/{prefix}/{account}/public",
            "owner_preflight": command, "state": "review_required",
            "execution_authorized": False, "public_routing": False}
