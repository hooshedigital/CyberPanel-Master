"""Read-only status bridge from deployed Hoosh CyberAgent and configured AI Gateway.

Runs in a restricted root-owned systemd oneshot; NOT in Django/HTTP workers.
Never exports raw logs, tokens, prompts, commands, customer data or credentials.
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
import urllib.request
import urllib.error
import urllib.parse

STATUS_DIR = Path("/var/lib/hoosh-cyber-agent")
CONFIG = Path("/etc/hoosh-cybermaster/bridge.json")
CORE_VERSION_FILES = (
    Path("/usr/local/CyberCP/version.txt"),
    Path("/usr/local/CyberCP/version"),
)
_ALLOWED_GATEWAY = {"supabase.hooshedigital.ir", "127.0.0.1", "localhost"}

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None

def iso():
    return datetime.now(timezone.utc).isoformat()

def safe_config():
    try:
        if CONFIG.is_symlink() or not CONFIG.is_file() or CONFIG.stat().st_size > 8192:
            return {}
        if CONFIG.stat().st_mode & 0o007:
            return {}
        cfg = json.loads(CONFIG.read_text())
        return cfg if isinstance(cfg, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}

def core_version():
    for p in CORE_VERSION_FILES:
        try:
            if p.is_symlink() or not p.is_file() or p.stat().st_size > 100:
                continue
            value = p.read_text(encoding="utf-8").strip()
            if p.suffix == ".txt":
                try:
                    parsed = json.loads(value)
                    v = parsed.get("version") if isinstance(parsed, dict) else None
                    b = parsed.get("build") if isinstance(parsed, dict) else None
                    if isinstance(v, str) and re.fullmatch(r"[0-9]+(?:\\.[0-9]+){1,3}", v) and type(b) is int and 0 <= b <= 99999:
                        return f"{v} Build {b}"
                except (ValueError, TypeError):
                    pass
            if re.fullmatch(r"[0-9]+(?:\\.[0-9]+){1,3}(?:[-. ]?(?:build|b)[ ]?[0-9]+)?",value,re.I):
                return value
        except (OSError,ValueError):
            continue
    return None

def unit_status():
    name = "hoosh-cyberagent.service"
    try:
        p = subprocess.run(
            ["/usr/bin/systemctl", "show", name, "--property=LoadState,ActiveState,SubState"],
            capture_output=True,text=True,timeout=3)
        fields=dict(line.split("=",1) for line in p.stdout.splitlines() if "=" in line)
        live=(p.returncode==0 and fields.get("LoadState")=="loaded" and fields.get("ActiveState")=="active")
        return {"schema":1,"generated_utc":iso(),"connected":live,
                "state":"active" if live else "unverified",
                "verified_core_version":core_version()}
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return {"schema":1,"generated_utc":iso(),"connected":False,
                "state":"unverified","verified_core_version":core_version()}

def gateway_status():
    result={"schema":1,"generated_utc":iso(),"connected":False,
            "provider_count":None, "state":"unverified"}
    cfg=safe_config().get("gateway",{})
    if not isinstance(cfg,dict) or cfg.get("enabled") is not True:
        return result
    url=cfg.get("status_url","")
    if not isinstance(url,str):return result
    parsed=urllib.parse.urlsplit(url)
    if (parsed.hostname not in _ALLOWED_GATEWAY
        or parsed.username or parsed.password or parsed.fragment
        or parsed.query or parsed.scheme not in ("https","http")
        or (parsed.scheme=="http" and parsed.hostname not in ("localhost","127.0.0.1"))
        or not (parsed.path == "/functions/v1/ai-gateway/api/status"
                or (parsed.hostname in ("localhost","127.0.0.1") and parsed.path=="/health"))):
        return result
    try:
        opener=urllib.request.build_opener(_NoRedirect)
        request=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"CyberPanelMasterStatus/0.1"})
        with opener.open(request,timeout=4) as res:
            if res.status!=200:return result
            payload=res.read(4097)
            if len(payload)>4096:return result
            body=json.loads(payload)
            if not isinstance(body,dict):return result
            # Only explicit machine-readable health passes, never HTTP200 alone.
            live=(body.get("ok") is True or body.get("status") in ("healthy","ok","operational"))
            result["connected"]=live
            result["state"]="healthy" if live else "unverified"
            if type(body.get("provider_count")) is int and 0<=body["provider_count"]<=10000:
                result["provider_count"]=body["provider_count"]
    except (OSError,ValueError,TypeError,urllib.error.HTTPError):
        pass
    return result

def emit(name,report):
    assert name in ("gateway-status.json","server-agent-status.json")
    STATUS_DIR.mkdir(mode=0o755,parents=True,exist_ok=True)
    owner=STATUS_DIR.stat()
    if STATUS_DIR.is_symlink() or owner.st_uid!=0 or owner.st_mode & 0o022:
        raise RuntimeError("unsafe state directory")
    data=json.dumps(report,ensure_ascii=False,separators=(",",":"),allow_nan=False).encode()
    if len(data)>4096:raise RuntimeError("report too large")
    fd,temp=tempfile.mkstemp(dir=str(STATUS_DIR),prefix=".cybermaster-")
    try:
        with os.fdopen(fd,"wb") as f:
            f.write(data);f.flush();os.fsync(f.fileno())
        os.chown(temp,0,0);os.chmod(temp,0o644)
        os.replace(temp,STATUS_DIR/name)
    finally:
        if os.path.exists(temp):os.unlink(temp)

if __name__=="__main__":
    emit("server-agent-status.json",unit_status())
    emit("gateway-status.json",gateway_status())
