"""Admin-only native CyberPanel Master dashboard. No privileged web actions."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from loginSystem.views import loadLoginPage
from plogical.acl import ACLManager
from plogical.httpProc import httpProc
from .i18n import COOKIE,context_for,resolve_language
from .version import MASTER_VERSION,label
from .billing_links import trusted_billing_admin_url
from .commerce_modules import modules_for, status_note
from .ops_overview import disk_overview, cleanup_candidates, agent_overview

BASE = Path("/var/lib/hoosh-cyber-agent")
ALLOW = {"health.json","gateway-status.json","server-agent-status.json",
         "disk-inventory.json","cleanup-candidates.json","agent-operations.json"}

def _report(name,max_age=300):
    if name not in ALLOW: return {}
    p = BASE/name
    try:
        if p.is_symlink() or not p.is_file() or p.stat().st_size>65536:
            return {}
        value=json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(value,dict) or value.get("schema")!=1:return {}
        stamp=datetime.fromisoformat(value["generated_utc"])
        age=(datetime.now(timezone.utc)-stamp).total_seconds()
        return value if stamp.tzinfo is not None and 0<=age<=max_age else {}
    except (OSError,ValueError,KeyError,TypeError,OverflowError):
        return {}

def display_context(lang):
    health=_report("health.json",600)
    gateway=_report("gateway-status.json")
    agent=_report("server-agent-status.json")
    # Timer cadence is ~10m with jitter; 30m TTL tolerates bounded delay.
    disk_report=_report("disk-inventory.json",1800)
    cleanup_report=_report("cleanup-candidates.json",1800)
    ops_report=_report("agent-operations.json",300)
    parsa=health.get("parsa",{})
    if not isinstance(parsa,dict):parsa={}
    checks=health.get("checks",{})
    if not isinstance(checks,dict):checks={}
    count=sum(isinstance(v,dict) and v.get("incident") is True for v in checks.values())
    resources=health.get("resources",{})
    if not isinstance(resources,dict):resources={}
    counts=parsa.get("mission_counts",{})
    if not isinstance(counts,dict):counts={}
    containers=health.get("containers",{})
    if not isinstance(containers,dict):containers={}
    # The gateway/server agent are never marked connected without fresh evidence.
    try:
        from cyberpanel_version import VERSION, BUILD
        core = f"{VERSION} Build {BUILD}"
    except (ImportError, AttributeError, TypeError, ValueError):
        core = agent.get("verified_core_version") if isinstance(agent.get("verified_core_version"),str) else None
    return {**context_for(lang),"master":{
        "version":MASTER_VERSION,"version_label":label(core),
        "health_fresh":bool(health),"incidents":count,
        "parsa_connected":parsa.get("connected") is True and parsa.get("brain")=="PARSA",
        "parsa_state":str(parsa.get("executor_state","unknown"))[:24],
        "parsa_counts":{k:v for k,v in counts.items() if isinstance(k,str) and type(v) is int and 0<=v<=100000},
        "disk_used":resources.get("disk_pct"),
        "gateway_connected":gateway.get("connected") is True,
        "router_healthy":containers.get("parsa-ai-router-pilot")=="ok",
        "cyberagent_connected":agent.get("connected") is True,
        "cyberagent_state":str(agent.get("state","unknown"))[:24],
        "updated":health.get("generated_utc"),
        "billing_admin_url":trusted_billing_admin_url(),
        "commerce_modules":modules_for(lang),
        "commerce_note":status_note(lang),
        "disk_inventory":disk_overview(disk_report),
        "cleanup_candidates":cleanup_candidates(cleanup_report),
        "cleanup_verified":cleanup_report.get("schema")==1,
        "cleanup_complete":cleanup_report.get("analysis_complete") is True,
        "agent_operations":agent_overview(ops_report)
    }}

@never_cache
@require_GET
def dashboard(request):
    uid=request.session.get("userID")
    if uid is None:return redirect(loadLoginPage)
    try:
        acl=ACLManager.loadedACL(uid)
        if not isinstance(acl,dict) or not acl.get("admin"):
            return HttpResponseForbidden("Administrator access required")
    except Exception:
        return HttpResponseForbidden("Access denied")
    lang=resolve_language(request.GET.get("lang"),request.COOKIES.get(COOKIE))
    result=httpProc(request,"backup/cyberpanel_master.html",display_context(lang),"admin").render()
    if request.GET.get("lang") in ("en","fa"):
        result.set_cookie(COOKIE,lang,max_age=180*86400,secure=True,httponly=True,samesite="Lax",path="/backup/")
    return result
