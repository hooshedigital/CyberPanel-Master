"""Offline contract tests: no production resources are contacted."""
import json
import unittest
from control_plane.app import create_app

def call(app, path, method="GET", bearer=""):
    statuses = []
    def start(status, headers):
        statuses.append(status)
    environ = {"REQUEST_METHOD": method, "PATH_INFO": path,
               "HTTP_AUTHORIZATION": f"Bearer {bearer}" if bearer else ""}
    response = json.loads(b"".join(app(environ, start)).decode())
    return statuses[0], response

class ControlPlaneTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(token="local-testing-only")

    def test_public_health(self):
        status, body = call(self.app, "/health")
        self.assertEqual(status, "200 OK")
        self.assertEqual(body["status"], "ok")

    def test_read_only_authentication(self):
        self.assertEqual(call(self.app, "/v1/capabilities")[0], "401 Unauthorized")
        self.assertEqual(call(self.app, "/v1/capabilities", bearer="wrong")[0], "401 Unauthorized")
        status, body = call(self.app, "/v1/capabilities", bearer="local-testing-only")
        self.assertEqual(status, "200 OK")
        self.assertEqual(body["production_connected"], False)

    def test_no_token_fails_closed(self):
        self.assertEqual(call(create_app(token=""), "/v1/capabilities")[0], "503 Service Unavailable")

    def test_no_writes_or_unknown_endpoints(self):
        self.assertEqual(call(self.app, "/v1/capabilities", "POST", bearer="local-testing-only")[0], "405 Method Not Allowed")
        self.assertEqual(call(self.app, "/v1/sites", bearer="local-testing-only")[0], "404 Not Found")

if __name__ == "__main__":
    unittest.main()
