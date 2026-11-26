"""Deterministic, staging-only config renderer; never writes or runs commands.

Caller must be a trusted staging adapter. Numeric identities, filesystem
ownership, namespace setup, and runtime authorization remain external gates.
Do not execute the generated FPM files as root or use on a live listener.
"""
from dataclasses import dataclass
import hashlib
import json
import re

from .web_engine import domain_name

ROOT_RE = re.compile(r"/var/tmp/hoosh-engine-render-[a-z0-9]{1,32}\Z")
PROFILES = {"eco": (1, 32), "balanced": (2, 32)}
PORTS = (18883, 18884)


@dataclass(frozen=True)
class Tenant:
    domain: str
    slot: int
    uid: int
    profile: str = "eco"


def render(root, tenants, *, role, used_domains=(), used_uids=()):
    """Return config text plus SHA256 manifest, not a provisioning transaction."""
    if role != "admin":
        raise PermissionError("admin_required")
    if type(root) is not str or not ROOT_RE.fullmatch(root):
        raise ValueError("staging_root_required")
    if type(tenants) not in (list, tuple) or not 1 <= len(tenants) <= 2:
        raise ValueError("one_or_two_stage_tenants")
    domains = set(domain_name(d) for d in used_domains)
    uids = set(used_uids)
    slots = set()
    items = []
    for t in tenants:
        if type(t) is not Tenant:
            raise ValueError("invalid_tenant")
        domain = domain_name(t.domain)
        if not domain.endswith(".test"):
            raise ValueError("synthetic_test_domain_required")
        if type(t.slot) is not int or t.slot not in (1, 2) or t.slot in slots:
            raise ValueError("slot_conflict")
        if type(t.uid) is not int or not 62000 <= t.uid <= 62999 or t.uid in uids:
            raise ValueError("uid_conflict")
        if type(t.profile) is not str or t.profile not in PROFILES or domain in domains:
            raise ValueError("profile_or_domain_conflict")
        slots.add(t.slot)
        uids.add(t.uid)
        domains.add(domain)
        items.append(Tenant(domain, t.slot, t.uid, t.profile))
    items.sort(key=lambda t: t.slot)
    a, o = PORTS
    files = {}
    apache = f"""ServerRoot "{root}"
ServerName rejected.test
Listen 127.0.0.1:{a}
PidFile "{root}/apacherun/httpd.pid"
ErrorLog "{root}/apacherun/error.log"
LogLevel warn
"""
    for name in ("mpm_event", "authz_core", "dir", "mime", "proxy", "proxy_fcgi"):
        apache += f"LoadModule {name}_module /usr/lib/apache2/modules/mod_{name}.so\n"
    apache += f"""User www-data
Group www-data
StartServers 1
ServerLimit 1
ThreadLimit 16
ThreadsPerChild 8
MaxRequestWorkers 8
MinSpareThreads 2
MaxSpareThreads 10
TypesConfig /etc/mime.types
ProxyRequests Off
ProxyFCGIBackendType FPM
<Directory />
 AllowOverride None
 Require all denied
</Directory>
<FilesMatch "^\\.">
 Require all denied
</FilesMatch>
<FilesMatch "(?i)\\.(?:phtml|phar|php[0-9]+|php\\..+|bak|old|sql|ini|log)$">
 Require all denied
</FilesMatch>
<VirtualHost 127.0.0.1:{a}>
 ServerName rejected.test
 DocumentRoot "{root}/empty"
 <Location />
  Require all denied
 </Location>
</VirtualHost>
"""
    olsroot = root + "/ols"
    ols = f"""serverName hoosh-stage
user www-data
group www-data
autoRestart 0
enableChroot 0
inMemBufSize 8M
swappingDir /tmp/lshttpd/swap
mime conf/mime.properties
disableWebAdmin 1
httpdWorkers 1
errorlog logs/error.log {{
 logLevel WARN
 rollingSize 1M
}}
accessLog logs/access.log {{
 rollingSize 1M
}}
tuning {{
 maxConnections 32
 maxSSLConnections 8
 connTimeout 10
 keepAliveTimeout 2
 quicEnable 0
 totalInMemCacheSize 1M
 totalMMapCacheSize 1M
}}
"""
    mappings = []
    layout = []
    for t in items:
        n = f"tenant{t.slot}"
        p = f"{root}/{n}"
        children, memory = PROFILES[t.profile]
        # Root-owned document-root and config are mandatory for this fixture.
        apache += f"""<VirtualHost 127.0.0.1:{a}>
 ServerName {t.domain}
 DocumentRoot "{p}/public"
 DirectoryIndex index.php
 <Directory "{p}/public">
  Options -Indexes -FollowSymLinks -SymLinksIfOwnerMatch
  AllowOverride None
  Require all granted
 </Directory>
 <FilesMatch "\\.php$">
  SetHandler "proxy:unix:{p}/run/php.sock|fcgi://localhost/"
 </FilesMatch>
</VirtualHost>
"""
        # FPM is launched under an externally verified nonroot UID/GID, not root.
        files[f"{n}/fpm.conf"] = f"""[global]
pid = {p}/run/fpm.pid
error_log = {p}/run/error.log
daemonize = no
[tenant]
listen = {p}/run/php.sock
listen.mode = 0660
pm = ondemand
pm.max_children = {children}
pm.process_idle_timeout = 5s
pm.max_requests = 100
clear_env = yes
security.limit_extensions = .php
php_admin_value[memory_limit] = {memory}M
php_admin_value[cgi.fix_pathinfo] = 0
php_admin_flag[display_errors] = off
"""
        ols += f"""virtualhost {n} {{
 vhRoot {olsroot}/{n}/
 configFile {olsroot}/conf/{n}/vhost.conf
 allowSymbolLink 0
 enableScript 0
 restrained 1
}}
"""
        files[f"ols/conf/{n}/vhost.conf"] = f"""docRoot {olsroot}/{n}/
vhDomain {t.domain}
extprocessor backend {{
 type proxy
 address 127.0.0.1:{a}
 maxConns 8
 initTimeout 5
 retryTimeout 0
 respBuffer 0
}}
context / {{
 type proxy
 handler backend
 addDefaultCharset off
}}
"""
        mappings.append(f" map {n} {t.domain}\n")
        layout.append({"domain": t.domain, "slot": t.slot, "uid": t.uid,
                       "gid": t.uid, "socket_gid": 33, "profile": t.profile,
                       "socket_mode": "0660", "socket_directory_mode": "2750",
                       "private_directory_mode": "0700", "root_owned_public": True})
    ols += f"listener stage {{\n address 127.0.0.1:{o}\n secure 0\n" + "".join(mappings) + "}\n"
    files["httpd.conf"] = apache
    files["ols/conf/httpd_config.conf"] = ols
    files = dict(sorted(files.items()))
    manifest = {
        "schema": 1, "staging_only": True, "execution_authorized": False,
        "production_changes": False, "public_cache_enabled": False,
        "private_cache_enabled": False, "htaccess_enabled": False,
        "root": root, "ports": list(PORTS), "tenants": layout,
        "sha256": {p: hashlib.sha256(s.encode("utf-8")).hexdigest() for p, s in files.items()},
        "gates": ["verify_unused_uid_gid_and_ports", "verify_path_ownership_no_symlinks",
                  "nonroot_fpm", "private_pid_network_and_tmp", "runtime_configtest",
                  "owner_approval", "https_host_header_cache_privacy", "rollback"],
    }
    return {"files": files, "manifest": manifest,
            "manifest_sha256": hashlib.sha256(json.dumps(
                manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}
