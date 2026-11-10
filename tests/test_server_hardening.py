"""Uji penguatan keamanan backend/server.py (CSP, CSRF, Origin, akses admin).

Jalankan dari root proyek: python -m unittest tests.test_server_hardening -v
"""
import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

# Alihkan DB ke file sementara SEBELUM import server (path DB dihitung saat import).
TMPDIR = tempfile.mkdtemp(prefix="pangan_test_")
os.environ["PANGAN_DB_PATH"] = os.path.join(TMPDIR, "app.sqlite3")

import backend.server as server  # noqa: E402


class TestHardening(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.httpd.daemon_threads = True
        cls.port = cls.httpd.server_address[1]
        cls._thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls._thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def req(self, path, method="GET", body=None, headers=None):
        url = f"http://127.0.0.1:{self.port}{path}"
        data = body.encode("utf-8") if isinstance(body, str) else body
        request = urllib.request.Request(url, data=data, method=method)
        for key, value in (headers or {}).items():
            request.add_header(key, value)
        try:
            with urllib.request.urlopen(request, timeout=10) as resp:
                return resp.status, dict(resp.headers), resp.read()
        except urllib.error.HTTPError as exc:
            return exc.code, dict(exc.headers), exc.read()

    def csrf_token(self):
        _status, headers, _body = self.req("/")
        cookie = headers.get("Set-Cookie", "")
        for part in cookie.split(","):
            part = part.strip()
            if part.startswith("pangan_csrf="):
                return part[len("pangan_csrf="):].split(";")[0]
        return ""

    def test_index_returns_html_and_security_headers(self):
        status, headers, body = self.req("/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", headers.get("Content-Type", ""))
        self.assertIn("frame-ancestors 'none'", headers.get("Content-Security-Policy", ""))
        self.assertEqual(headers.get("X-Frame-Options"), "DENY")
        self.assertIn("pangan_csrf=", headers.get("Set-Cookie", ""))

    def test_no_inline_script_in_html(self):
        _status, _headers, body = self.req("/")
        html = body.decode("utf-8", errors="replace")
        self.assertNotIn("onclick=", html)
        self.assertNotIn("<script>", html)

    def test_mutating_post_without_csrf_rejected(self):
        status, _h, _b = self.req(
            "/api/feedback", method="POST", body=json.dumps({"consent_anonymous_feedback": True})
        )
        self.assertEqual(status, 403)

    def test_mutating_post_with_wrong_csrf_rejected(self):
        status, _h, _b = self.req(
            "/api/feedback", method="POST", body="{}",
            headers={"X-CSRF-Token": "salah001"},
        )
        self.assertEqual(status, 403)

    def test_csrf_passes_then_auth_blocks(self):
        token = self.csrf_token()
        self.assertTrue(token)
        status, _h, _b = self.req(
            "/api/feedback", method="POST", body=json.dumps({}),
            headers={"X-CSRF-Token": token},
        )
        # Token diterima, tapi belum login -> 401, bukan 403.
        self.assertEqual(status, 401)

    def test_webhook_exempt_from_csrf(self):
        # Tanpa token CSRF, tapi karena ini webhook (auth sendiri) bukan 403 melainkan 503 (belum dikonfigurasi).
        status, _h, _b = self.req(
            "/api/webhook/xendit", method="POST", body=json.dumps({"external_id": "x"}),
        )
        self.assertNotEqual(status, 403)

    def test_origin_mismatch_rejected(self):
        token = self.csrf_token()
        status, _h, _b = self.req(
            "/api/feedback", method="POST", body="{}",
            headers={"Origin": "http://evil.example", "X-CSRF-Token": token},
        )
        self.assertEqual(status, 403)

    def test_admin_endpoint_gated_without_login(self):
        status, _h, _b = self.req("/api/evaluation")
        self.assertIn(status, (401, 403))

    def test_login_without_oauth_redirects_config_error(self):
        status, _h, _b = self.req("/auth/login")
        self.assertEqual(status, 302)
        self.assertIn("auth_error=config", _h.get("Location", ""))


if __name__ == "__main__":
    unittest.main()
