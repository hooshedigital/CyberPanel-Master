#!/usr/bin/python3
"""Create review copies, never edit live panel files."""
import ast
import argparse
from pathlib import Path

def once(source,old,new):
    if source.count(old)!=1 or new in source:raise ValueError("unexpected source anchor")
    return source.replace(old,new,1)

def central_view(s):
    s=once(s,"from .operations_center import operations_context\n","from .operations_center import operations_context\nfrom .capacity_panel import capacity_context\n")
    return once(s,'"health_fresh":bool(health),"incidents":count,','"health_fresh":bool(health),"incidents":count,\n        "capacity":capacity_context(lang),')

def central_template(s):
    marker='      <section class="hm-panel" id="linux-storage" aria-labelledby="linux-storage-heading">'
    return once(s,marker,'      {% include "backup/hoosh_capacity_summary.html" with capacity=master.capacity %}\n'+marker)

def website_view(s):
    s=once(s,'import stat\n','import stat\nfrom .capacity_panel import capacity_context\n')
    return once(s,'result = {"available": False, "engines": [','result = {"available": False, "capacity": capacity_context(), "engines": [')

def website_template(s):
    marker='  <dl>\n'
    return once(s,marker,'  {% include "backup/hoosh_capacity_summary.html" with capacity=hoosh_engine_status.capacity %}\n'+marker)

OPS={"central_view":central_view,"central_template":central_template,"website_view":website_view,"website_template":website_template}
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("kind",choices=OPS)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    if a.source.is_symlink() or not a.source.is_file() or a.source.stat().st_size>500000:raise ValueError("invalid source")
    result=OPS[a.kind](a.source.read_text())
    if a.kind.endswith("_view"):ast.parse(result)
    with a.output.open("x") as f:f.write(result)
