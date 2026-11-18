"""Guarded, additive CyberPanel Core branding patch. No login or auth changes."""
from __future__ import annotations
import argparse,hashlib,os,tempfile
from pathlib import Path

LIVE=Path("/usr/local/CyberCP/baseTemplate/templates/baseTemplate/index.html")
EXPECTED="4b0e859cd9c88ec601b795b10ae265f73504bf9b10463acafc15bfb0b8b66d1d"
CHANGES=[
    ('<div class="brand">CyberPanel</div>',
     '<div class="brand">CyberPanel Master</div>',2),
    ('<div class="tagline">Web Hosting Panel</div>',
     '<div class="tagline">CyberPanel Core {{ CYBERPANEL_VERSION }} Build {{ CYBERPANEL_BUILD }} · Master v0.1.0</div>',2),
    ("        <a href=\"{% url 'hooshCyberAgentDashboard' %}\" class=\"menu-item\">",
     """        <a href="{% url 'hooshCyberPanelMaster' %}" class="menu-item">
            <div class="icon-wrapper"><i class="fas fa-brain"></i></div>
            <span>CyberPanel Master</span>
        </a>
        <a href="{% url 'hooshCyberAgentDashboard' %}" class="menu-item">""",1),
    ("{% if admin %}{l:'Cyber Agent', h:'{% url \"hooshCyberAgentDashboard\" %}'",
     "{% if admin %}{l:'CyberPanel Master', h:'{% url \"hooshCyberPanelMaster\" %}', i:'fa-brain', g:'Administration'},{% endif %}\n            {% if admin %}{l:'Cyber Agent', h:'{% url \"hooshCyberAgentDashboard\" %}'",1),
]

def render(original):
    h=hashlib.sha256(original).hexdigest()
    if h!=EXPECTED:raise RuntimeError("UNEXPECTED_SOURCE_HASH:"+h)
    text=original.decode("utf-8")
    for old,new,count in CHANGES:
        if text.count(old)!=count:raise RuntimeError("UNEXPECTED_ANCHOR:"+str(count)+":"+old[:48])
        text=text.replace(old,new)
    if text.count("hooshCyberPanelMaster")!=2:
        raise RuntimeError("MASTER_NAV_COUNT_UNEXPECTED")
    return text.encode("utf-8")

def main():
    p=argparse.ArgumentParser();p.add_argument("--apply",action="store_true")
    args=p.parse_args()
    original=LIVE.read_bytes();result=render(original)
    if not args.apply:
        print("PREVIEW_OK",len(original),len(result),hashlib.sha256(result).hexdigest());return
    st=LIVE.stat()
    fd,tmp=tempfile.mkstemp(prefix=".cybermaster-base-",dir=str(LIVE.parent))
    try:
        with os.fdopen(fd,"wb") as f:
            f.write(result);f.flush();os.fsync(f.fileno())
        os.chown(tmp,st.st_uid,st.st_gid)
        os.chmod(tmp,st.st_mode&0o777)
        # Concurrent edits must not be silently overwritten.
        if hashlib.sha256(LIVE.read_bytes()).hexdigest()!=EXPECTED:
            raise RuntimeError("SOURCE_CHANGED_BEFORE_REPLACE")
        os.replace(tmp,LIVE)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    print("BRANDING_APPLIED",hashlib.sha256(LIVE.read_bytes()).hexdigest())

if __name__=="__main__":main()
