"""Isolated read-only control-plane prototype; deliberately no CyberPanel SSH/API calls.

Python stdlib WSGI application suitable for an offline/test environment. This
prototype does not establish production authentication or authorization.
"""
from __future__ import annotations

import json
import os
import secrets
from typing import Callable, Iterable

ALLOWED_PATHS = {
    "/health": {"status": "ok", "service": "parsa-control-plane-prototype"},
    "/v1/capabilities": {
        "capabilities": [
            {"name": "sites.inventory", "state": "not_connected", "mode": "read_only"},
            {"name": "ssl.inventory", "state": "not_connected", "mode": "read_only"},
            {"name": "backup.inventory", "state": "not_connected", "mode": "read_only"},
        ],
        "production_connected": False,
    },
}

def create_app(token: str | None = None) -> Callable:
    """Build a no-network WSGI app. Inject fake token in tests only."""
    secret = token if token is not None else os.environ.get("CONTROL_PLANE_READ_TOKEN", "")

    def app(environ: dict, start_response: Callable) -> Iterable[bytes]:
        method = environ.get("REQUEST_METHOD", "GET")
        path = environ.get("PATH_INFO", "")
        headers = [("Content-Type", "application/json; charset=utf-8"),
                   ("Cache-Control", "no-store"),
                   ("X-Content-Type-Options", "nosniff")]
        status = "200 OK"
        if method != "GET":
            status, body = "405 Method Not Allowed", {"error": "method_not_allowed"}
        elif path not in ALLOWED_PATHS:
            status, body = "404 Not Found", {"error": "not_found"}
        elif path != "/health":
            bearer = environ.get("HTTP_AUTHORIZATION", "")
            provided = bearer[7:] if bearer.startswith("Bearer ") else ""
            if not secret:
                status, body = "503 Service Unavailable", {"error": "not_configured"}
            elif not provided or not secrets.compare_digest(provided, secret):
                status, body = "401 Unauthorized", {"error": "unauthorized"}
            else:
                body = ALLOWED_PATHS[path]
        else:
            body = ALLOWED_PATHS[path]
        start_response(status, headers)
        return [json.dumps(body, ensure_ascii=False).encode("utf-8")]

    return app

app = create_app()

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    # Loopback only. Never bind this prototype to public interfaces.
    with make_server("127.0.0.1", 8088, app) as server:
        print("Prototype at http://127.0.0.1:8088; no CyberPanel connection")
        server.serve_forever()
