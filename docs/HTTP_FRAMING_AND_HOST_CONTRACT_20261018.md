# HTTP/1.1 framing and Host boundary — offline contract (2026-10-18)

Scope: isolated read-only CyberPanel control-plane prototype only. This document does not approve any deployment or claim that FastAPI v3.4 is canonical.

## Fail-closed requirements

- Reject missing, duplicate, folded, non-loopback or wrong-port Host fields at the local test listener.
- Reject duplicate Content-Length, any Transfer-Encoding, and especially simultaneous TE/CL.
- Reject nonzero or malformed Content-Length; accept a single zero-length field.
- Reject TE, Trailer, Expect, Upgrade, Proxy-Connection, ambiguous Connection tokens.
- Reject duplicate Authorization and caller-supplied identity/forwarding headers before WSGI normalization.
- Preserve bodyless GET /health and authorized read-only /v1/capabilities; reject write methods.
- Do not reflect bearer tokens or client-controlled identity data in errors.

## Limitations and owner acceptance

This is a Python stdlib loopback **reference**, not an Nginx/Traefik policy. It cannot prove the absence of request smuggling across intermediary proxies. Header whitespace can be normalized by Python before validation.

Run offline tests with `python -m unittest discover -s tests -v` after applying the separately delivered code patch. No CI claim applies to this documentation-only commit.

Before any staging consideration, the owner must validate the exact source SHA, every ingress hop, duplicate Host/CL/TE/Authorization rejection at the *first* proxy, sanitized logs, RBAC, rollback, and absence of request desynchronization. NO-GO if canonical source, proxy configuration, exact-SHA CI, or rollback evidence is missing.

No merge, deploy, production access, or credential rotation was performed.