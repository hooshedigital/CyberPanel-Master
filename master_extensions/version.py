"""Keep custom extension and upstream versions distinct."""
MASTER_VERSION = "0.2.0-dev"

def label(core_version: str | None) -> str:
    core = (core_version or "not verified").strip()[:60]
    return f"CyberPanel Master v{MASTER_VERSION} · CyberPanel Core {core}"
