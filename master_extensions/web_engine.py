"""Independent admission planner; preview only, no deployment or shell access."""
from dataclasses import dataclass
import math
import re

ENGINES = ("ols-native", "ols-apache", "frankenphp", "container")
PROFILES = ("eco", "balanced", "performance")
# Planning estimates, not enforced limits.
MEMORY_MIB = {"ols-native": (0, 0, 0), "ols-apache": (192, 384, 768),
              "frankenphp": (256, 512, 1024), "container": (256, 512, 1024)}
REQUIRED = {
    "ols-native": ("native_verified",),
    "ols-apache": ("apache_installed", "apache_loopback_verified",
                   "php_isolation_verified", "proxy_verified"),
    "frankenphp": ("frankenphp_verified", "php_isolation_verified", "proxy_verified"),
    "container": ("container_verified", "container_isolation_verified", "proxy_verified"),
}
READINESS = frozenset(k for keys in REQUIRED.values() for k in keys) | {
    "public_cache_verified", "object_cache_verified"
}


@dataclass(frozen=True)
class Resources:
    available_mib: int
    swap_free_mib: int
    disk_free_mib: int
    cpu_psi60: float
    memory_psi60: float

    def validate(self):
        for v in (self.available_mib, self.swap_free_mib, self.disk_free_mib):
            if type(v) is not int or v < 0:
                raise ValueError("invalid_resources")
        for v in (self.cpu_psi60, self.memory_psi60):
            if type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 100:
                raise ValueError("invalid_pressure")


def domain_name(value):
    if type(value) is not str or not 1 <= len(value) <= 253 or not value.isascii():
        raise ValueError("invalid_domain")
    labels = value.lower().split(".")
    if len(labels) < 2 or not re.fullmatch("[a-z][a-z0-9-]{0,62}", labels[-1]):
        raise ValueError("invalid_domain")
    if any(not re.fullmatch("[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", x)
           for x in labels):
        raise ValueError("invalid_domain")
    return ".".join(labels)


def preview(payload, *, role, resources, readiness):
    """Trusted adapter must supply role, resources and readiness; never browser data."""
    if role != "admin":
        raise PermissionError("admin_required")
    if type(payload) is not dict or set(payload) - {
        "domain", "engine", "profile", "public_cache", "object_cache"
    }:
        raise ValueError("invalid_request")
    domain = domain_name(payload.get("domain"))
    engine = payload.get("engine", "ols-native")
    profile = payload.get("profile", "balanced")
    if type(engine) is not str or engine not in ENGINES:
        raise ValueError("invalid_engine")
    if type(profile) is not str or profile not in PROFILES:
        raise ValueError("invalid_profile")
    cache = payload.get("public_cache", False)
    obj = payload.get("object_cache", False)
    if type(cache) is not bool or type(obj) is not bool:
        raise ValueError("invalid_cache_request")
    if type(readiness) is not dict or set(readiness) - READINESS or any(
            type(v) is not bool for v in readiness.values()):
        raise ValueError("invalid_readiness")
    if not isinstance(resources, Resources):
        raise ValueError("invalid_resources")
    resources.validate()
    envelope = MEMORY_MIB[engine][PROFILES.index(profile)]
    blockers = [key for key in REQUIRED[engine] if readiness.get(key) is not True]
    if resources.available_mib < 1024 + envelope:
        blockers.append("ram_headroom")
    if resources.swap_free_mib < 1024:
        blockers.append("swap_headroom")
    if resources.disk_free_mib < 8192:
        blockers.append("disk_headroom")
    if resources.cpu_psi60 >= 40:
        blockers.append("cpu_pressure")
    if resources.memory_psi60 >= 5:
        blockers.append("memory_pressure")
    if cache and (engine != "ols-native" or not readiness.get("public_cache_verified")):
        blockers.append("public_cache_compatibility")
    if obj and not readiness.get("object_cache_verified"):
        blockers.append("object_cache_integration")
    return {"domain": domain, "engine": engine, "profile": profile,
            "additional_memory_envelope_mib": envelope,
            "public_cache_requested": cache, "object_cache_requested": obj,
            "private_cache_enabled": False,
            "status": "blocked" if blockers else "eligible_for_staging_review",
            "blockers": blockers, "production_changes": False,
            "execution_authorized": False,
            "required_gates": ["tenant_isolation", "configuration_validation",
                               "local_smoke", "cache_privacy", "rollback", "owner_approval"]}
