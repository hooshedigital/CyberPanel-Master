"""Read-only, admin-only resource preview for native Create Website."""
from pathlib import Path
import re
import shutil

def _psi(name):
    text = Path("/proc/pressure/" + name).read_text(encoding="ascii")
    return float(re.search(r"(?m)^some .*?avg60=([0-9.]+)", text).group(1))

def panel_context(acl):
    if not isinstance(acl, dict) or acl.get("admin") not in (True, 1):
        return None
    result = {"available": False, "engines": [
        {"name": "OpenLiteSpeed Native", "state": "Existing site creation"},
        {"name": "OpenLiteSpeed + Apache", "state": "Staging only"},
        {"name": "FrankenPHP", "state": "Not provisioned"},
        {"name": "Docker Application", "state": "Separate deployment workflow"},
    ]}
    try:
        text = Path("/proc/meminfo").read_text(encoding="ascii")
        mem = {k: int(re.search(r"(?m)^"+k+r":\s+(\d+)\s+kB$",text).group(1))//1024
               for k in ("MemAvailable","SwapFree")}
        disk = shutil.disk_usage("/").free//1048576
        cpu, memory = _psi("cpu"), _psi("memory")
        result.update(available=True, ram=mem["MemAvailable"], swap=mem["SwapFree"],
                      disk=disk, cpu=cpu, memory=memory,
                      capacity_ok=mem["MemAvailable"]>=1408 and mem["SwapFree"]>=1024
                      and disk>=8192 and 0<=cpu<40 and 0<=memory<5)
    except (OSError, ValueError, AttributeError, OverflowError):
        pass
    return result
