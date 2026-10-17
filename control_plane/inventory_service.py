"""Optional read-only inventory WSGI entry point for the CyberPanel prototype.

No upstream network access is performed. Use the default disconnected adapter
unless a test explicitly injects the synthetic fixture adapter.
"""
from __future__ import annotations

import json
import os
import secrets
from wsgiref.simple_server import make_server

from control_plane.app import create_app
from control_plane.inventory import DisconnectedAdapter

ROUTES = {
    "/v1/inventory/sites": "sites",
    "/v1/inventory/ssl": "ssl",
    "/v1/inventory/backups": "backups",
}


def create_inventory_service(token=None, adapter=None):
    """Extend the existing WSGI prototype without changing CyberPanel core."""
    secret = token if token is not None else os.environ.get("CONTROL_PLANE_READ_TOKEN", "")
    reader = adapter if adapter is not None else DisconnectedAdapter()
    fallback = create_app(token=secret)

    def service(environ, start_response):
        path = environ.get("PATH_INFO", "")
        if path not in ROUTES:
            return fallback(environ, start_response)

        headers = [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Cache-Control", "no-store"),
            ("X-Content-Type-Options", "nosniff"),
        ]
        method = environ.get("REQUEST_METHOD", "GET")
        bearer = environ.get("HTTP_AUTHORIZATION", "")
        provided = bearer[7:] if bearer.startswith("Bearer ") else ""
        if method != "GET":
            status, body = "405 Method Not Allowed", {"error": "method_not_allowed"}
        elif not secret:
            status, body = "503 Service Unavailable", {"error": "not_configured"}
        elif not provided or not secrets.compare_digest(provided, secret):
            status, body = "401 Unauthorized", {"error": "unauthorized"}
        else:
            try:
                kind = ROUTES[path]
                snapshot = reader.inventory(kind)
                if snapshot.kind != kind or snapshot.production_connected:
                    raise ValueError("unsafe inventory adapter response")
                if snapshot.source not in ("not_connected", "synthetic"):
                    raise ValueError("unexpected inventory source")
                body = snapshot.as_json()
                status = "200 OK"
            except Exception:
                status, body = "503 Service Unavailable", {"error": "inventory_unavailable"}
        start_response(status, headers)
        return [json.dumps(body, ensure_ascii=False).encode("utf-8")]

    return service


app = create_inventory_service()

if __name__ == "__main__":
    # Explicitly loopback-only. This is not a production administration service.
    with make_server("127.0.0.1", 8089, app) as server:
        print("Offline inventory prototype on 127.0.0.1:8089")
        server.serve_forever()
