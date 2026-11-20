"""Stage a bilingual, native CyberAgent console against EXACT installed Core files.

Runs in staging only, preserving ACL, upstream customizations and all hosting data.
Never writes /usr/local/CyberCP or changes any live service. A final separately
approved release copies only SHA-verified diff artifacts after browser testing.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat

ROOT=Path("/usr/local/CyberCP")
REPO=Path(__file__).resolve().parents[1]
LIMIT=160000

def source(root: Path, rel: str) -> str:
    path=root/rel
    info=path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size>LIMIT or info.st_size<=0:
        raise ValueError("unsafe or oversized source: "+rel)
    return path.read_text("utf-8")

def replace_once(src: str, old: str, new: str, rel: str) -> str:
    if src.count(old)!=1:
        raise ValueError("installed controller drift: "+rel)
    return src.replace(old,new,1)

def prepare(core: Path, output: Path) -> dict:
    if output.exists() or output.is_symlink():
        raise ValueError("staging output already exists")
    controller="backup/cyber_agent.py"
    template="backup/templates/backup/cyber_agent.html"
    before=source(core,controller)
    previous_template=source(core,template)
    next_template=source(REPO,"master_extensions/templates/backup/cyber_agent.html")
    i18n=source(REPO,"master_extensions/agent_console_i18n.py")
    anchor='    return httpProc(request,"backup/cyber_agent.html",dashboard_context(),"admin").render()'
    updated = replace_once(before,anchor,'''    from master_extensions.agent_console_i18n import labels, localized_check
    from master_extensions.i18n import resolve_language
    from django.utils.translation import get_language
    # The global Django language cookie is authoritative throughout Core.
    language_cookie = request.COOKIES.get("django_language")
    lang = resolve_language(request.GET.get("lang"), language_cookie or get_language())
    context = dashboard_context()
    context["cyber_agent"]["checks"] = [
        localized_check(item, lang) for item in context["cyber_agent"]["checks"]
    ]
    context.update({"lang":lang,"direction":"rtl" if lang=="fa" else "ltr",
                    "a":labels(lang)})
    result = httpProc(request,"backup/cyber_agent.html",context,"admin").render()
    if request.GET.get("lang") in ("en","fa"):
        result.set_cookie("django_language",lang,max_age=180*86400,
                          secure=True,httponly=True,samesite="Lax",path="/")
    return result''',controller)
    compile(updated,controller,"exec")
    compile(i18n,"master_extensions/agent_console_i18n.py","exec")
    # Do not allow accidental mixing of legacy HTML and new context keys.
    if 'lang="{{ lang }}"' not in next_template or '{{ a.title }}' not in next_template:
        raise ValueError("unexpected new console template")
    artifacts={
        controller:(before,updated),
        template:(previous_template,next_template),
        "master_extensions/agent_console_i18n.py":(None,i18n),
    }
    output.mkdir(mode=0o700,parents=False)
    os.chmod(output,0o700)
    changes=[]
    for rel,(prior,body) in artifacts.items():
        target=output/rel
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(body,"utf-8")
        changes.append({
            "path":rel,
            "before_sha256":hashlib.sha256(prior.encode()).hexdigest() if prior is not None else None,
            "after_sha256":hashlib.sha256(body.encode()).hexdigest(),
        })
    manifest={
        "schema":1,"version":"0.2.0-dev",
        "ui":"CyberAgent native bilingual",
        "production_changes":0,
        "preserves_installed_admin_acl":True,
        "global_language_cookie":"django_language",
        "files":changes,
    }
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2))
    return manifest

if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--core",type=Path,default=ROOT)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(prepare(args.core,args.output)))
