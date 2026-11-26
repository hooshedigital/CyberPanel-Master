"""Read-only, admin-only resource preview for native Create Website."""
from pathlib import Path
import re
import shutil
import stat

FRANKENPHP = Path('/opt/hoosh-runtimes/frankenphp/1.14.0/frankenphp')

def _frankenphp_state():
    try:
        for p in (FRANKENPHP, *FRANKENPHP.parents):
            st = p.lstat()
            if st.st_uid != 0 or st.st_mode & 0o022 or stat.S_ISLNK(st.st_mode):
                return 'Installation not verified'
            if p == FRANKENPHP:
                if not stat.S_ISREG(st.st_mode) or not st.st_mode & 0o111:
                    return 'Installation not verified'
            elif not stat.S_ISDIR(st.st_mode):
                return 'Installation not verified'
        return '1.14.0 installed; provisioning pending'
    except OSError:
        return 'Not provisioned'

def _psi(name):
    text = Path("/proc/pressure/" + name).read_text(encoding="ascii")
    return float(re.search(r"(?m)^some .*?avg60=([0-9.]+)", text).group(1))

def panel_context(acl):
    if not isinstance(acl, dict) or acl.get("admin") not in (True, 1):
        return None
    result = {"available": False, "engines": [
        {"name": "OpenLiteSpeed Native", "state": "Existing site creation"},
        {"name": "OpenLiteSpeed + Apache", "state": "Staging only"},
        {"name": "FrankenPHP", "state": _frankenphp_state()},
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
