"""Read bounded root-owned aggregate reports; never call Docker or root helpers."""
import datetime as dt
import json
import math
import os
from pathlib import Path
import stat

CAPACITY=Path("/var/lib/hoosh-capacity-advisor/latest.json")
RETENTION=Path("/var/lib/hoosh-docker-retention/latest.json")
UTC=dt.timezone.utc
CODES={
"monitor_stale":("Monitor data stale","داده پایش قدیمی است"),
"insufficient_samples":("Insufficient samples","نمونه کافی نیست"),
"ram_below_1536_mib":("RAM below threshold","حافظه کمتر از حد مجاز"),
"swap_below_1024_mib":("Swap below threshold","فضای Swap ناکافی"),
"disk_below_8_gib":("Disk below threshold","فضای دیسک ناکافی"),
"disk_backup_reserve":("New workloads need 12 GiB free including backup reserve","برای بارهای جدید حداقل ۱۲ GiB فضای آزاد با احتساب ذخیره پشتیبان لازم است"),
"cpu_pressure_high":("High CPU pressure","فشار بالای CPU"),
"memory_pressure_high":("High memory pressure","فشار بالای حافظه"),
"disk_headroom_warning":("Low disk headroom","هشدار ظرفیت دیسک"),
"ram_headroom_warning":("Low RAM headroom","هشدار ظرفیت حافظه"),
"cpu_contention_warning":("CPU contention","رقابت پردازشی"),
"io_contention_warning":("I/O contention","فشار ورودی/خروجی"),
"monitor_data_unavailable":("Monitor data unavailable","داده پایش در دسترس نیست"),
}

def read_report(path,max_age):
    try:
        for parent in path.parents:
            s=parent.lstat()
            if s.st_uid!=0 or not stat.S_ISDIR(s.st_mode) or s.st_mode&0o022:return {}
        fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        with os.fdopen(fd,"rb") as f:
            s=os.fstat(f.fileno())
            if (s.st_uid!=0 or not stat.S_ISREG(s.st_mode) or s.st_mode&0o022
                    or s.st_nlink!=1 or s.st_size>16384):return {}
            raw=f.read(16385)
        if len(raw)>16384:return {}
        d=json.loads(raw)
        if not isinstance(d,dict):return {}
        stamp=dt.datetime.fromisoformat(d["time_utc"])
        if stamp.tzinfo is None:return {}
        age=(dt.datetime.now(UTC)-stamp).total_seconds()
        if not 0<=age<=max_age:return {}
        if d.get("execution_authorized") is not False or d.get("automatic_actions") is not False:return {}
        return d
    except (OSError,ValueError,TypeError,KeyError,OverflowError):return {}

def metric(v,low=0,high=1000000000):
    return round(v,2) if type(v) in (int,float) and math.isfinite(v) and low<=v<=high else None

def capacity_context(lang="en"):
    fa=lang=="fa"
    d=read_report(CAPACITY,900)
    decision=d.get("decision")
    states={"thresholds_met":("Thresholds met; approval required","آستانه‌ها برقرار؛ نیازمند تأیید"),
            "review_required":("Capacity review required","نیازمند بازبینی ظرفیت"),
            "blocked":("Deployment not advised","استقرار توصیه نمی‌شود")}
    result={"ready":decision in states,"state":states.get(decision,("Unavailable or stale","ناموجود یا قدیمی"))[fa],
            "decision":decision if decision in states else "unavailable",
            "capacity_reasons":[],"retention":{"ready":False}}
    if result["ready"]:
        for key in ("blockers","warnings"):
            values=d.get(key,[])
            if not isinstance(values,list) or any(type(x) is not str or x not in CODES for x in values):
                result["ready"]=False;result["decision"]="unavailable";result["state"]="ناموجود یا قدیمی" if fa else "Unavailable or stale";break
            result["capacity_reasons"] += [CODES[x][fa] for x in values]
        m=d.get("median_30m",{})
        if not isinstance(m,dict):m={}
        result.update(ram=metric(m.get("ram_mib")),swap=metric(m.get("swap_free_mib")),
                      cpu=metric(m.get("cpu_psi60"),high=100),memory=metric(m.get("memory_psi60"),high=100),
                      disk=metric(d.get("disk_free_gib")),used=metric(d.get("disk_used_percent"),high=100),
                      delta=metric(d.get("disk_free_median_delta_hour_gib"),low=-1000000),
                      samples=metric(d.get("samples_30m"),high=10000),updated=d.get("time_utc"))
    budget=d.get("storage_budget")
    if (result["ready"] and isinstance(budget,dict)
            and budget.get("independent_recovery_required") is True
            and budget.get("automatic_actions") is False
            and type(budget.get("target_met")) is bool):
        target=metric(budget.get("target_free_gib"),low=1)
        gap=metric(budget.get("gap_gib"))
        if target is not None and gap is not None and gap<=target:
            result["storage_budget"]={"target":target,"gap":gap,"met":budget["target_met"]}
    policy=d.get("workload_policy")
    if (result["ready"] and isinstance(policy,dict) and type(policy.get("version")) is int
            and policy["version"]==1 and policy.get("execution_authorized") is False
            and policy.get("local_build") in ("defer","review")
            and policy.get("new_runtime") in ("defer","review")
            and policy.get("retention_review") in ("prioritize","routine")
            and policy.get("existing_services")=="preserve"
            and policy.get("backup_and_health")=="preserve"):
        names={"defer":("Defer","به تعویق بیفتد"),"review":("Review first","ابتدا بازبینی"),
               "prioritize":("Prioritize review","بازبینی در اولویت"),"routine":("Routine review","بازبینی معمول")}
        result["policy"]={k:names[policy[k]][fa] for k in ("local_build","new_runtime","retention_review")}
    r=read_report(RETENTION,5400)
    keys=("unique_images","referenced","tagged_unreferenced","untagged_unreferenced","containers")
    if (r.get("status")=="review_only" and r.get("deletion_approved")==0
            and all(type(r.get(k)) is int and 0<=r[k]<=500 for k in keys)
            and r["unique_images"]==r["referenced"]+r["tagged_unreferenced"]+r["untagged_unreferenced"]):
        result["retention"]={"ready":True,**{k:r[k] for k in keys}}
    return result
