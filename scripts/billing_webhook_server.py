"""Minimal webhook server for Stripe billing events (stdlib only).

Runs a small HTTP server on localhost that accepts Stripe webhooks and
applies them to the billing store. No third-party dependency.

Env vars:
  BILLING_DB      path to the sqlite database (default: data/app_users.sqlite3)
  STRIPE_WEBHOOK_SECRET  Stripe webhook signing secret (required for POSTs)
  BILLING_PORT     port to listen on (default: 8503)

Endpoints:
  GET  /health            -> "ok"
  POST /webhook/stripe    -> verify signature, dispatch event
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "src"))

from pangan_forecast.billing import handle_webhook, initialize_billing  # noqa: E402

DATABASE = Path(os.environ.get("BILLING_DB", str(ROOT / "data" / "app_users.sqlite3")))
SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
PORT = int(os.environ.get("BILLING_PORT", "8503"))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # silence default logging
        return

    def _reply(self, code: int, body: str) -> None:
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._reply(200, json.dumps({"status": "ok", "time": datetime.now(timezone.utc).isoformat()}))
        else:
            self._reply(404, json.dumps({"error": "not found"}))

    def do_POST(self) -> None:
        if self.path != "/webhook/stripe":
            self._reply(404, json.dumps({"error": "not found"}))
            return
        if not SECRET:
            self._reply(503, json.dumps({"error": "webhook secret not configured"}))
            return
        length = int(self.headers.get("Content-Length", 0))
        payload = self.rfile.read(length) if length else b""
        signature = self.headers.get("Stripe-Signature", "")
        try:
            outcome = handle_webhook(DATABASE, payload, signature, SECRET)
            self._reply(200, json.dumps({"status": "ok", "handled": outcome}))
        except ValueError as exc:
            self._reply(400, json.dumps({"error": str(exc)}))


if __name__ == "__main__":
    initialize_billing(DATABASE)
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Webhook server berjalan di http://127.0.0.1:{PORT}/webhook/stripe")
    server.serve_forever()
