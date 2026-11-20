"""Prepare CyberPanel Master v0.2 Operations Center overlay from LIVE v0.1.

Read-only staging. Integrates the new dashboard and bounded agent checks while
preserving installed ACL, bridge data contracts, and local Core customizations.
Never patches public login, SSL, billing API, vhosts or the real server here.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import json
import os
import runpy
import stat

CORE=Path("/usr/local/CyberCP")
REPO=Path(__file__).resolve().parents[1]
LIMIT=250_000

def read_file(root:Path, rel:str)->str:
    p=root/rel
    info=p.lstat()
    if not stat.S_ISREG(info.st_mode) or not 0<info.st_size<=LIMIT:
        raise ValueError("invalid live/repo file: "+rel)
    return p.read_text("utf-8")

def replace_once(data:str, old:str, new:str, label:str)->str:
    if data.count(old)!=1:
        raise ValueError("unknown source layout: "+label)
    return data.replace(old,new,1)

def stage(core:Path, output:Path)->dict:
    if output.exists() or output.is_symlink():
        raise ValueError("refuse to overwrite existing review overlay")
    controller="master_extensions/master_view.py"
    lang_file="master_extensions/i18n.py"
    operations="master_extensions/operations_center.py"
    version="master_extensions/version.py"
    template="backup/templates/backup/cyberpanel_master.html"
    initial={path:read_file(core,path) for path in (controller,lang_file,operations,version,template)}
    source={path:read_file(REPO,path) for path in (lang_file,operations,version,
                                                 "master_extensions/commerce_modules.py",
                                                 "master_extensions/billing_links.py",
                                                 "master_extensions/templates/backup/cyberpanel_master.html")}

    # Extend installed controller rather than assuming the GitHub variant is identical.
    view=initial[controller]
    if 'from .billing_links import trusted_billing_admin_url' not in view:
        view=replace_once(
            view, 'from .workspace_browser import browse as browse_workspace',
            'from .workspace_browser import browse as browse_workspace\n'
            'from .billing_links import trusted_billing_admin_url\n'
            'from .commerce_modules import modules_for, status_note',
            controller)
    marker='"ops":{**operations_context(lang), "workspace":browse_workspace(folder)}'
    if marker not in view:
        marker='"ops":{**operations_context(lang),"workspace":browse_workspace(folder)}'
    if marker not in view:
        raise ValueError("cannot locate live master ops context")
    view=replace_once(view,marker,
        '"billing_admin_url":trusted_billing_admin_url(),\n'
        '        "commerce_modules":modules_for(lang),\n'
        '        "commerce_note":status_note(lang),\n'
        '        '+marker,controller)
    # A single shared Django language cookie takes precedence for the whole Core.
    old='resolve_language(request.GET.get("lang"),request.COOKIES.get(COOKIE))'
    new='resolve_language(request.GET.get("lang"),request.COOKIES.get("django_language") or request.COOKIES.get(COOKIE))'
    view=replace_once(view,old,new,controller)
    view=replace_once(view,
        'result.set_cookie(COOKIE,lang,max_age=180*86400,secure=True,httponly=True,samesite="Lax",path="/backup/")',
        'result.set_cookie("django_language",lang,max_age=180*86400,secure=True,httponly=True,samesite="Lax",path="/")',
        controller)
    compile(view,controller,"exec")

    # Translate only missing/changed Master dictionary keys, retaining local
    # historical i18n source and English default behavior.
    current=runpy.run_path(str(core/lang_file))["LABELS"]
    proposed=runpy.run_path(str(REPO/lang_file))["LABELS"]
    if set(current)!={"en","fa"} or set(proposed)!={"en","fa"}:
        raise ValueError("unsupported Master locales")
    merged=initial[lang_file]
    for language in ("en","fa"):
        updates={k:v for k,v in proposed[language].items()
                 if k not in current[language] or (k=="brand" and v!=current[language][k])}
        merged+='\nLABELS['+repr(language)+'].update('+repr(updates)+')\n'
    compile(merged,lang_file,"exec")
    merged_labels=runpy.run_path(str(REPO/lang_file))["LABELS"]
    staged_ui=source["master_extensions/templates/backup/cyberpanel_master.html"]
    import re
    used=set(re.findall(r"{{\s*t\.(\w+)\s*}}",staged_ui))
    for language in ("en","fa"):
        final={**current[language],**{k:v for k,v in proposed[language].items()
                                         if k not in current[language] or k=="brand"}}
        if used-set(final):
            raise ValueError("missing UI keys for "+language+":"+str(used-set(final)))
    if not source[version].count('MASTER_VERSION = "0.2.0-dev"')==1:
        raise ValueError("unexpected v0.2-dev source version")
    files={
       controller:(initial[controller],view),
       lang_file:(initial[lang_file],merged),
       operations:(initial[operations],source[operations]),
       version:(initial[version],source[version]),
       template:(initial[template],staged_ui),
       "master_extensions/commerce_modules.py":(None,source["master_extensions/commerce_modules.py"]),
       "master_extensions/billing_links.py":(None,source["master_extensions/billing_links.py"]),
    }
    if any((core/path).exists() for path in files if files[path][0] is None):
        raise ValueError("new module path already present on server")
    output.mkdir(mode=0o700,parents=False)
    os.chmod(output,0o700)
    items=[]
    for rel,(prior,content) in files.items():
        p=output/rel
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(content,"utf-8")
        if rel.endswith(".py"):
            compile(content,rel,"exec")
        items.append({"path":rel,
                      "before_sha256":hashlib.sha256(prior.encode()).hexdigest() if prior else None,
                      "after_sha256":hashlib.sha256(content.encode()).hexdigest()})
    manifest={"schema":1,"version":"0.2.0-dev",
              "product":"CyberPanel Master, entire Core distribution",
              "view":"Operations Center",
              "production_changes":0,
              "preserves_admin_acl":True,
              "files":items}
    (output/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    return manifest

if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--core",type=Path,default=CORE)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(stage(args.core,args.output)))
