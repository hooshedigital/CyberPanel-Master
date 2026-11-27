"""Admin-only read-only planning page, independent of native site creation."""
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from master_extensions.web_engine_plan import plan
from master_extensions.web_engine_panel import panel_context
from plogical.acl import ACLManager


@never_cache
@require_http_methods(["GET", "POST"])
@csrf_protect
def private_engine_plan(request):
    try:
        uid = request.session["userID"]
        acl = ACLManager.loadedACL(uid)
        if not isinstance(acl, dict) or acl.get("admin") not in (True, 1):
            return HttpResponseForbidden("Administrator required.")
    except Exception:
        return HttpResponseForbidden("Administrator required.")
    metrics = panel_context(acl) or {}
    # CLI independently validates live capacity, filesystem and enrollment state.
    capacity_ok = (metrics.get("available") is True and metrics.get("ram", 0) >= 1536
                   and metrics.get("swap", 0) >= 1024 and metrics.get("disk", 0) >= 12288
                   and 0 <= metrics.get("cpu", 100) < 40 and 0 <= metrics.get("memory", 100) < 5)
    context = {"capacity_ok": capacity_ok, "metrics": metrics, "form": {
        "engine": "apache", "account": "", "domain": "", "persistent": False}}
    status = 200
    if request.method == "POST":
        fields = {"engine", "account", "domain", "persistent", "csrfmiddlewaretoken"}
        try:
            if set(request.POST) - fields or any(len(request.POST.getlist(k)) != 1 for k in request.POST):
                raise ValueError("Invalid request fields.")
            persistent = request.POST.get("persistent", "")
            if persistent not in ("", "on"):
                raise ValueError("Invalid boot preference.")
            context["form"] = {"engine": request.POST.get("engine", ""),
                               "account": request.POST.get("account", "")[:31],
                               "domain": request.POST.get("domain", "")[:253],
                               "persistent": persistent == "on"}
            context["plan"] = plan(request.POST.get("engine", ""), request.POST.get("account", ""),
                                   request.POST.get("domain", ""), persistent == "on",
                                   capacity_ok=capacity_ok)
        except ValueError as exc:
            context["error"] = str(exc)
            status = 400
    return render(request, "websiteFunctions/hoosh_private_engine_plan.html", context, status=status)
