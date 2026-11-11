"""Local HTML interface and JSON API for PanganLaba.

Run with ``python -m backend.server`` from the project root, then open http://127.0.0.1:8000.
Frontend files live in ``frontend/``. Python API, data, auth, and ML code stays in the backend.
"""
from __future__ import annotations

import base64, csv, hashlib, hmac, io, ipaddress, json, math, os, re, secrets, shutil, sys, threading, time
import tomllib, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
sys.path.insert(0, str(ROOT / "backend" / "src"))
from pangan_forecast.accounts import start_or_get_account
from pangan_forecast.billing import (
    check_account_access, complete_provider_payment,
    confirm_manual_payment_by_id, get_plan, get_subscription,
    list_admin_payments, list_incomplete_subscriptions, list_plans, record_payment,
    set_subscription,
)
from pangan_forecast.data import load_and_merge
from pangan_forecast.pihps_excel import inspect_pihps_excel, extract_pihps_series
from pangan_forecast.recommend import make_recommendation, simulate_purchase_policy
from pangan_forecast.service import (
    append_umkm_feedback, build_current_forecasts, project_paths,
)
from pangan_forecast.business import compute_current_profit_report

HOST = os.environ.get("PANGAN_HOST", "127.0.0.1")
PORT = int(os.environ.get("PANGAN_PORT") or os.environ.get("PORT", "8000"))
PATHS = project_paths(ROOT)
DB = PATHS["db"]
TRAIN_JOBS: dict[str, dict] = {}
TRAIN_LOCK = threading.Lock()
OAUTH_STATES: dict[str, float] = {}
OAUTH_CACHE: dict[str, dict] = {}
# Cache id Price Stripe per plan (dibuat otomatis sekali).
PRICE_CACHE: dict[str, str] = {}
PLAN_CAP = {"starter": None}
# Token CSRF double-submit: dibaca JavaScript dari cookie lalu dikirim via header.
CSRF_TOKEN = secrets.token_urlsafe(32)


def read_secrets() -> dict:
    path = ROOT / ".streamlit" / "secrets.toml"
    config = {}
    if path.exists():
        try:
            config = tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            config = {}

    auth = config.setdefault("auth", {})
    google = auth.setdefault("google", {})
    billing = config.setdefault("billing", {})
    google.setdefault(
        "server_metadata_url",
        "https://accounts.google.com/.well-known/openid-configuration",
    )
    environment_values = (
        (auth, "redirect_uri", "PANGAN_OAUTH_REDIRECT_URI"),
        (auth, "cookie_secret", "PANGAN_COOKIE_SECRET"),
        (google, "client_id", "PANGAN_GOOGLE_CLIENT_ID"),
        (google, "client_secret", "PANGAN_GOOGLE_CLIENT_SECRET"),
        (google, "server_metadata_url", "PANGAN_GOOGLE_METADATA_URL"),
        (billing, "provider", "PANGAN_BILLING_PROVIDER"),
        (billing, "xendit_api_key", "PANGAN_XENDIT_API_KEY"),
        (billing, "xendit_webhook_token", "PANGAN_XENDIT_WEBHOOK_TOKEN"),
        (billing, "bank_name", "PANGAN_BANK_NAME"),
        (billing, "bank_number", "PANGAN_BANK_NUMBER"),
        (billing, "bank_account_name", "PANGAN_BANK_ACCOUNT_NAME"),
        (billing, "payment_instructions", "PANGAN_PAYMENT_INSTRUCTIONS"),
        (billing, "support_url", "PANGAN_SUPPORT_URL"),
    )
    for section, key, variable in environment_values:
        value = os.environ.get(variable, "").strip()
        if value:
            section[key] = value
    return config


SECRETS = read_secrets()
AUTH = SECRETS.get("auth", {})
GOOGLE = AUTH.get("google", {})
BILLING = SECRETS.get("billing", {})
ADMIN_CONFIG = SECRETS.get("admin", {})
def _configured(value) -> bool:
    value = str(value or "").strip()
    return bool(value) and not any(
        token in value.casefold() for token in ("ganti", "your_", "placeholder", "change_me")
    )


def _auth_config_ready() -> bool:
    redirect = urllib.parse.urlparse(str(AUTH.get("redirect_uri") or ""))
    local_callback = redirect.hostname in {"localhost", "127.0.0.1", "::1"}
    cookie_secret = str(AUTH.get("cookie_secret") or "")
    client_id = str(GOOGLE.get("client_id") or "")
    return bool(
        (redirect.scheme == "https" or (redirect.scheme == "http" and local_callback))
        and redirect.hostname
        and redirect.path == "/auth/callback"
        and len(cookie_secret) >= 32
        and _configured(cookie_secret)
        and client_id.endswith(".apps.googleusercontent.com")
        and _configured(client_id)
        and _configured(GOOGLE.get("client_secret"))
        and str(GOOGLE.get("server_metadata_url") or "").startswith("https://")
    )


AUTH_READY = _auth_config_ready()
COOKIE_SECRET = str(AUTH.get("cookie_secret") or "")


def json_bytes(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, default=str, separators=(",", ":")).encode("utf-8")


def read_table(path: Path, dates=()) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path)
    for col in dates:
        if col in frame:
            frame[col] = pd.to_datetime(frame[col], errors="coerce")
    return frame


def frames():
    return read_table(PATHS["metrics"]), read_table(PATHS["forecast"], ("origin_date", "target_date"))


def _host(handler) -> str:
    return str(handler.headers.get("Host", "")).split(":", 1)[0].strip("[]").lower()


def _loopback(handler) -> bool:
    # Jangan percaya header Host untuk memutuskan asal lokal: bisa dipalsukan
    # dan akan membuka preview premium anonim (F1). Pakai alamat socket peer.
    try:
        return ipaddress.ip_address(handler.client_address[0]).is_loopback
    except (ValueError, TypeError, IndexError):
        return False


def _oauth_matches_host(handler) -> bool:
    callback = urllib.parse.urlparse(str(AUTH.get("redirect_uri", "")))
    if not (AUTH_READY and callback.hostname):
        return False
    wanted = callback.hostname.lower()
    got = str(handler.headers.get("Host", "")).split(":", 1)[0].strip("[]").lower()
    # Di lokal, terima alias loopback manapun supaya buka via localhost atau
    # 127.0.0.1 sama-sama jalan. Produksi tetap harus cocok persis.
    if wanted in {"localhost", "127.0.0.1", "::1"}:
        return got in {"localhost", "127.0.0.1", "::1"}
    return got == wanted


def _cookie(handler, name: str) -> str:
    from http import cookies
    jar = cookies.SimpleCookie()
    try:
        jar.load(handler.headers.get("Cookie", ""))
        return jar[name].value if name in jar else ""
    except cookies.CookieError:
        return ""


def _session_cookie(email: str, name: str, exp: int) -> str:
    payload = base64.urlsafe_b64encode(json_bytes({"email": email, "name": name, "exp": exp})).decode().rstrip("=")
    signature = hmac.new(COOKIE_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return payload + "." + signature


def _session(handler):
    # Do not accept cookies signed with the development fallback when OAuth
    # secrets are absent or malformed (for example on a fresh deployment).
    if not AUTH_READY:
        return None
    value = _cookie(handler, "pangan_session")
    if "." not in value:
        return None
    payload, signature = value.rsplit(".", 1)
    expected = hmac.new(COOKIE_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        item = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        return item if item.get("email") and int(item.get("exp", 0)) > int(time.time()) else None
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def _account_for(handler):
    session = _session(handler)
    if session:
        email, name = session["email"], session.get("name", "")
        account = start_or_get_account(DB, email, name, trial_days=7)
        account["email"] = email
        account = check_account_access(DB, account)
        sub = get_subscription(DB, email)
        if sub:
            account["plan_id"] = sub.get("plan_id")
        return account, email, name, False
    if not _oauth_matches_host(handler) and _loopback(handler):
        email = "preview-lokal@pangan.local"
        return {"email": email, "status": "preview", "days_remaining": 0, "access_allowed": True}, email, "Preview lokal", True
    return {"email": "", "status": "anonymous", "days_remaining": 0, "access_allowed": False}, "", "", False


def _plans():
    try:
        return list_plans(DB)
    except Exception:
        return []


def _commodities(account):
    prices = read_table(PATHS["prices"])
    if prices.empty or "commodity" not in prices:
        return []
    result = sorted(prices["commodity"].dropna().astype(str).unique())
    cap = PLAN_CAP.get(account.get("plan_id")) if account.get("status") == "active" else None
    return result[:cap] if cap else result


def _bootstrap(handler):
    account, email, name, preview = _account_for(handler)
    is_admin = bool(email and _is_admin(email))
    metrics, forecast = frames()
    prices = read_table(PATHS["prices"], ("date",))
    if not prices.empty:
        region = str(prices["location"].dropna().iloc[0]) if "location" in prices and prices["location"].notna().any() else "Kota Depok"
        date_range = [str(prices["date"].min().date()), str(prices["date"].max().date())]
        latest_date = pd.Timestamp(prices["date"].max()).date()
        price_age_days = max(0, (datetime.now(ZoneInfo("Asia/Jakarta")).date() - latest_date).days)
        price_commodities = int(prices["commodity"].nunique()) if "commodity" in prices else 0
    else:
        region, date_range, price_commodities, price_age_days = "Kota Depok", [], 0, None
    return {
        "auth_ready": _oauth_matches_host(handler), "logged_in": bool(email), "local_preview": preview,
        "is_admin": is_admin,
        "user": {"email": email, "name": name} if email else None,
        "account": account, "access_allowed": bool(account.get("access_allowed")),
        "oauth_error": "" if _oauth_matches_host(handler) or preview else "Akses pelanggan memerlukan konfigurasi callback Google OAuth untuk domain ini.",
        "data": {"region": region, "date_range": date_range, "price_commodities": price_commodities,
                 "price_age_days": price_age_days,
                 "metric_commodities": int(metrics["commodity"].nunique()) if not metrics.empty and "commodity" in metrics else 0,
                 "metric_rows": len(metrics), "forecast_rows": len(forecast),
                 "ready": not metrics.empty and not forecast.empty},
        "commodities": _commodities(account),
        "models": sorted(metrics["model"].dropna().astype(str).unique()) if not metrics.empty else [],
        "features": sorted(metrics["features"].dropna().astype(str).unique()) if not metrics.empty else [],
        "forecast_choices": (forecast[["commodity", "model", "features"]]
                             .dropna().astype({"commodity": str, "model": str, "features": str})
                             .drop_duplicates().to_dict("records") if is_admin and not forecast.empty else []),
        "plans": _plans(),
        "billing": {"payment_instructions": str(BILLING.get("payment_instructions", "")),
                    "support_url": str(BILLING.get("support_url", "")),
                    "support_label": str(BILLING.get("support_label", "Hubungi pengelola")),
                    "checkout_urls": dict(BILLING.get("checkout_urls", {})) if hasattr(BILLING.get("checkout_urls", {}), "items") else {}},
    }


def _metadata():
    url = str(GOOGLE.get("server_metadata_url", ""))
    if not url:
        raise ValueError("Metadata Google OAuth belum dikonfigurasi.")
    if url not in OAUTH_CACHE:
        req = urllib.request.Request(url, headers={"User-Agent": "PanganLaba/1.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            OAUTH_CACHE[url] = json.loads(response.read().decode("utf-8"))
    return OAUTH_CACHE[url]


def _is_admin(email: str) -> bool:
    configured = ADMIN_CONFIG.get("emails", [])
    if isinstance(configured, str):
        configured = configured.split(",")
    admins = {str(x).strip().casefold() for x in configured if str(x).strip()}
    admins.update(x.strip().casefold() for x in os.environ.get("PANGAN_ADMIN_EMAILS", "").split(",") if x.strip())
    return email.casefold() in admins


def _safe_text(value, maxlen=1000) -> str:
    return str(value or "").strip()[:maxlen]


def _merge_uploaded_history(existing_path: Path, incoming: pd.DataFrame,
                            key_columns: list[str]) -> pd.DataFrame:
    """Merge an uploaded partial date series over existing rows.

    Incoming records take precedence for matching keys, so PIHPS corrections
    replace old values while dates and commodities absent from the upload stay
    in the active dataset.
    """
    if incoming.empty:
        raise ValueError("Data unggahan tidak berisi baris yang dapat digabungkan.")

    incoming = incoming.copy()
    try:
        existing = pd.read_csv(existing_path) if existing_path.is_file() else pd.DataFrame()
    except pd.errors.EmptyDataError:
        existing = pd.DataFrame()
    if existing.empty:
        existing = incoming.iloc[0:0].copy()
    else:
        missing = set(key_columns) - set(existing.columns)
        if missing:
            raise ValueError(f"Kolom kunci {sorted(missing)} tidak ditemukan pada {existing_path.name}.")

    for frame in (existing, incoming):
        missing = set(key_columns) - set(frame.columns)
        if missing:
            raise ValueError(f"Kolom kunci {sorted(missing)} tidak ditemukan pada data unggahan.")
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        for column in key_columns:
            if column != "date":
                frame[column] = frame[column].fillna("").astype(str).str.strip()
        frame.dropna(subset=["date"], inplace=True)

    if incoming.empty:
        raise ValueError("Tidak ada tanggal valid pada data unggahan.")

    merged = pd.concat([existing, incoming], ignore_index=True, sort=False)
    merged = merged.drop_duplicates(subset=key_columns, keep="last")
    return merged.sort_values(key_columns, kind="stable").reset_index(drop=True)


def _finite_number(value, label: str, *, minimum: float = 0,
                   strictly_positive: bool = False, maximum: float = 1_000_000_000_000) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} harus berupa angka.") from None
    if not math.isfinite(number) or number > maximum:
        raise ValueError(f"{label} harus berupa angka valid tidak lebih dari {maximum:,.0f}.")
    if number < minimum or (strictly_positive and number <= minimum):
        operator = "lebih dari" if strictly_positive else "minimal"
        raise ValueError(f"{label} harus {operator} {minimum}.")
    return number


AUDIT_PATH = ROOT / "data/admin_audit.csv"


def _audit(action: str, email: str, detail: str = ""):
    """Catat tindakan sensitif (admin/akun) ke CSV audit sederhana."""
    try:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        new_file = not AUDIT_PATH.exists()
        with open(AUDIT_PATH, "a", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            if new_file:
                writer.writerow(["timestamp_utc", "email", "action", "detail"])
            writer.writerow([
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                email, action, detail,
            ])
    except OSError:
        # Audit tidak boleh memutus request utama.
        pass


BACKUP_ROOT = ROOT / "backups"
ARTIFACT_DIRS = ("models", "reports")


def _snapshot_artifacts(prefix: str) -> Path:
    """Salin artefak model/laporan + file data utama ke backup ber-timestamp.

    Dipanggil TEPAT SEBELUM artefak aktif akan ditimpa. Dipakai untuk
    rollback bila pelatihan gagal di tengah jalan (F2).
    """
    nonce = secrets.token_hex(4)
    snap = BACKUP_ROOT / f"{prefix}_{nonce}"
    snap.mkdir(parents=True, exist_ok=True)
    for name in ARTIFACT_DIRS:
        src = ROOT / name
        if src.is_dir():
            shutil.copytree(src, snap / name, dirs_exist_ok=True)
    files: dict[str, Path] = {}
    for key in ("prices", "weather", "calendar"):
        p = PATHS.get(key)
        if p and p.is_file():
            files[key] = p
    for key in ("metrics", "forecast"):
        p = PATHS.get(key)
        if p and p.is_file():
            files[key] = p
    for fname in ("combined_daily.csv", "uploaded_daily.csv"):
        p = PATHS["clean_dir"] / fname
        if p.is_file():
            files[fname] = p
    if files:
        fsnap = snap / "files"
        fsnap.mkdir(parents=True, exist_ok=True)
        for p in files.values():
            rel = p.relative_to(ROOT)
            shutil.copy2(p, fsnap / rel.as_posix().replace("/", "__"))
    return snap


def _restore_artifacts(snap: Path) -> None:
    """Pulihkan model/laporan/file data dari snapshot tertentu."""
    for name in ARTIFACT_DIRS:
        src = snap / name
        dst = ROOT / name
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
    fsnap = snap / "files"
    if not fsnap.is_dir():
        return
    for f in fsnap.iterdir():
        target = ROOT / f.name.replace("__", "/")
        if target.parent:
            target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)


class Handler(BaseHTTPRequestHandler):
    server_version = "PanganLaba/1.1"

    def log_message(self, fmt, *args):
        safe_args = tuple(re.sub(r"(/auth/callback)\?[^\s\"]*", r"\1", str(arg)) for arg in args)
        print("[panganlaba]", fmt % safe_args)

    CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
           "img-src 'self' data:; font-src 'self' data:; connect-src 'self'; "
           "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'")

    def _send(self, status, body: bytes, content_type, headers=None):
        self._response_started = True
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Content-Security-Policy", self.CSP)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Set-Cookie",
                         f"pangan_csrf={CSRF_TOKEN}; Path=/; SameSite=Lax")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, data, status=200, headers=None):
        self._send(status, json_bytes(data), "application/json; charset=utf-8", headers)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length > 2_000_000:
            raise ValueError("Permintaan terlalu besar.")
        return json.loads(self.rfile.read(length or 0).decode("utf-8") or "{}")

    def _same_origin(self):
        origin = self.headers.get("Origin")
        return not origin or urllib.parse.urlparse(origin).netloc.lower() == self.headers.get("Host", "").lower()

    def _user(self):
        try:
            account, email, _, preview = _account_for(self)
        except Exception as exc:
            print(f"[panganlaba] account lookup failed: {type(exc).__name__}: {exc}", flush=True)
            self._json({"error": "Status akun gagal dibaca. Muat ulang dan coba masuk lagi."}, 500)
            return None
        if not email:
            self._json({"error": "Silakan daftar atau masuk terlebih dahulu.", "login_required": True}, 401)
            return None
        return account, email, preview

    def _access(self):
        user = self._user()
        if user is None:
            return None
        if _is_admin(user[1]):
            return user
        if not user[0].get("access_allowed"):
            expired_reason = user[0].get("expired_reason", "trial")
            message = ("Masa langganan paket ini berakhir. Pilih paket untuk melanjutkan."
                       if expired_reason == "subscription"
                       else "Masa trial berakhir. Pilih paket untuk melanjutkan.")
            self._json({"error": message, "access_required": True,
                        "access_status": "expired", "expired_reason": expired_reason}, 402)
            return None
        return user

    def _require_admin(self):
        user = self._user()
        if user is None:
            return None
        if not _is_admin(user[1]):
            self._json({"error": "Fitur ini hanya tersedia untuk admin proyek."}, 403)
            return None
        return user

    def do_GET(self):  # noqa: N802
        self._response_started = False
        try:
            self._dispatch_get()
        except (BrokenPipeError, ConnectionResetError):
            print("[panganlaba] client disconnected while sending GET response", flush=True)
        except Exception as exc:
            print(f"[panganlaba] GET handler failed: {type(exc).__name__}: {exc}", flush=True)
            if not self._response_started:
                self._json({"error": "Server gagal memproses permintaan. Coba muat ulang halaman."}, 500)

    def _dispatch_get(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        print(f"[panganlaba] dispatch GET {path}", flush=True)
        if path in {"/", "/index.html"}:
            try:
                body = (FRONTEND / "index.html").read_bytes()
            except Exception as exc:
                print(f"[panganlaba] failed to read frontend index: {exc!r}", flush=True)
                self._json({"error": "Halaman utama gagal dibaca."}, 500)
                return
            self._send(200, body, "text/html; charset=utf-8")
            return
        static_files = {
            "/css/app.css": (FRONTEND / "css" / "app.css", "text/css; charset=utf-8"),
            "/js/app.js": (FRONTEND / "js" / "app.js", "text/javascript; charset=utf-8"),
        }
        if path in static_files:
            target, content_type = static_files[path]
            if not target.is_file():
                self._json({"error": "Berkas frontend tidak ditemukan."}, 404); return
            self._send(200, target.read_bytes(), content_type); return
        if path.startswith("/assets/"):
            asset_root = (FRONTEND / "assets").resolve()
            target = (asset_root / Path(path.removeprefix("/assets/"))).resolve()
            if asset_root not in target.parents or not target.is_file():
                self._json({"error": "Berkas tidak ditemukan."}, 404); return
            self._send(200, target.read_bytes(), "image/jpeg" if target.suffix.lower() in {".jpg", ".jpeg"} else "application/octet-stream"); return
        if path == "/auth/login": self._login(); return
        if path == "/auth/callback": self._callback(parsed.query); return
        if path == "/auth/logout":
            secure = "; Secure" if urllib.parse.urlparse(str(AUTH.get("redirect_uri", ""))).scheme == "https" else ""
            self._send(302, b"", "text/plain", {"Location": "/", "Set-Cookie": f"pangan_session=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0{secure}"}); return
        if path == "/api/bootstrap":
            try: self._json(_bootstrap(self))
            except Exception as exc: self._json({"error": str(exc)}, 500)
            return
        if path == "/api/forecast":
            if self._require_admin() is None: return
            query = urllib.parse.parse_qs(parsed.query)
            try:
                commodity = query.get("commodity", [""])[0]
                model = query.get("model", [""])[0]
                feature = query.get("features", [""])[0]
                origin = query.get("origin", [""])[0]
                days = max(1, min(7, int(query.get("restock_days", ["7"])[0])))
                _, pred = frames()
                view = pred[(pred["commodity"].astype(str) == commodity) &
                            (pred["model"].astype(str) == model) &
                            (pred["features"].astype(str) == feature) &
                            (pred["origin_date"].astype(str).str[:10] == origin)].sort_values("step")
                if view.empty: self._json({"error": "Ramalan tidak ditemukan untuk pilihan ini."}, 404); return
                rows = view.to_dict("records")
                advice = make_recommendation(float(view.iloc[0]["reference_price"]),
                                             [max(0, float(x)) for x in view["predicted"].head(days)])
                self._json({"forecast": rows, "reference_price": float(view.iloc[0]["reference_price"]),
                            "recommendation": advice})
            except Exception as exc: self._json({"error": str(exc)}, 400)
            return
        if path == "/api/forecasts/current":
            if self._access() is None: return
            query = urllib.parse.parse_qs(parsed.query)
            try:
                model = query.get("model", ["GRU"])[0]
                feature = query.get("features", ["harga + cuaca + kalender + siklus tanggal"])[0]
                commodity = query.get("commodity", [""])[0]
                days = max(1, min(7, int(query.get("restock_days", ["7"])[0])))
                result = build_current_forecasts(ROOT, model, feature,
                                                 commodities=[commodity] if commodity else None,
                                                 restock_days=days)
                self._json(result)
            except FileNotFoundError as exc: self._json({"error": str(exc)}, 404)
            except ValueError as exc: self._json({"error": str(exc)}, 400)
            except Exception as exc:
                print(f"[panganlaba] forecast error: {type(exc).__name__}", flush=True)
                self._json({"error": "Prediksi belum tersedia. Periksa data dan model yang sudah dilatih."}, 500)
            return
        if path == "/api/evaluation":
            if self._require_admin() is None: return
            try:
                metrics, _ = frames()
                if metrics.empty: self._json({"error": "Hasil evaluasi belum tersedia."}, 404); return
                summary = metrics.groupby(["model", "features"], as_index=False).agg(
                    jumlah_komoditas=("commodity", "nunique"), median_MAE=("MAE", "median"),
                    median_RMSE=("RMSE", "median"), median_MAPE=("MAPE", "median"),
                    mean_MAE=("MAE", "mean"), mean_RMSE=("RMSE", "mean"), mean_MAPE=("MAPE", "mean"))
                commodity = urllib.parse.parse_qs(parsed.query).get("commodity", [""])[0]
                detail = metrics[metrics["commodity"].astype(str) == commodity] if commodity else metrics
                self._json({"summary": summary.to_dict("records"), "details": detail.to_dict("records"),
                            "commodities": sorted(metrics["commodity"].dropna().astype(str).unique())})
            except Exception as exc: self._json({"error": str(exc)}, 500)
            return
        if path in {"/api/history", "/api/history.csv"}:
            user = self._access()
            if user is None: return
            account, email, preview = user
            if preview: items = []
            else:
                from pangan_forecast.business import get_profit_history
                items = get_profit_history(DB, email, 500 if path.endswith(".csv") else 100)
            if path.endswith(".csv"):
                out = io.StringIO()
                cols = ["created_at", "menu_name", "period_label", "portions_sold", "selling_price", "revenue",
                        "ingredient_cost_per_portion", "total_ingredient_cost", "fixed_cost", "net_profit",
                        "predicted_net_profit", "net_margin_pct", "reference_date"]
                writer = csv.DictWriter(out, fieldnames=cols); writer.writeheader()
                for item in items: writer.writerow({key: item.get(key, "") for key in cols})
                self._send(200, out.getvalue().encode("utf-8-sig"), "text/csv; charset=utf-8",
                           {"Content-Disposition": "attachment; filename=riwayat_laba_menu.csv"})
            else: self._json({"items": items})
            return
        if path == "/api/admin/pending":
            user = self._user()
            if user is None: return
            if not _is_admin(user[1]): self._json({"error": "Akses admin diperlukan."}, 403); return
            self._json({"items": list_incomplete_subscriptions(DB)}); return
        if path == "/api/admin/payments":
            if self._require_admin() is None: return
            self._json({"items": list_admin_payments(DB)}); return
        if path.startswith("/api/train/status/"):
            if self._require_admin() is None: return
            job = TRAIN_JOBS.get(path.rsplit("/", 1)[-1])
            self._json(job if job else {"error": "Pekerjaan tidak ditemukan."}, 200 if job else 404); return
        self._json({"error": "Rute tidak ditemukan."}, 404)

    def _base_url(self) -> str:
        parsed = urllib.parse.urlparse(str(AUTH.get("redirect_uri", "")))
        return f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else "http://127.0.0.1:8000"

    def _create_xendit_invoice(self, plan: dict, email: str) -> tuple[str, str]:
        """Buat invoice Xendit; kembalikan (url_pembayaran, external_id)."""
        api_key = str(BILLING.get("xendit_api_key") or "").strip()
        if not api_key:
            raise ValueError("Provider xendit aktif, tetapi billing.xendit_api_key belum diisi.")
        ext = f"pangan-{plan['id']}-{secrets.token_hex(6)}"
        base = self._base_url()
        payload = json.dumps({
            "external_id": ext,
            "amount": int(plan["price_idr"]),
            "currency": "IDR",
            "payer_email": email,
            "description": f"Langganan PanganLaba - {plan['name']}",
            "success_redirect_url": base + "/?paid=success",
            "failure_redirect_url": base + "/?paid=failed",
        }).encode("utf-8")
        request = urllib.request.Request(
            "https://api.xendit.co/v2/invoices", data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Basic " + base64.b64encode((api_key + ":").encode()).decode(),
                "User-Agent": "PanganLaba/1.0",
            },
        )
        with urllib.request.urlopen(request, timeout=25) as response:
            invoice = json.loads(response.read().decode("utf-8"))
        url = str(invoice.get("invoice_url") or "").strip()
        if not url:
            raise ValueError("Xendit tidak mengembalikan halaman pembayaran.")
        return url, ext

    def _create_stripe_session(self, plan: dict, email: str) -> tuple[str, str]:
        """Buat Checkout Session Stripe (mode payment, price_data inline)."""
        api_key = str(BILLING.get("stripe_api_key") or "").strip()
        if not api_key:
            raise ValueError("Provider stripe aktif, tetapi billing.stripe_api_key belum diisi.")
        ext = f"pangan-stripe-{secrets.token_hex(6)}"
        base = self._base_url()
        fields = {
            "mode": "payment",
            "customer_email": email,
            "client_reference_id": ext,
            "success_url": base + "/?paid=success&session_id={CHECKOUT_SESSION_ID}",
            "cancel_url": base + "/?paid=failed",
            "metadata[plan_id]": plan["id"],
            "metadata[email]": email,
            "metadata[amount_idr]": str(int(plan["price_idr"])),
            "line_items[0][quantity]": "1",
            "line_items[0][price_data][currency]": "IDR",
            "line_items[0][price_data][unit_amount]": str(int(plan["price_idr"])),
            "line_items[0][price_data][product_data][name]": f"Langganan PanganLaba - {plan['name']}",
        }
        body = urllib.parse.urlencode(fields).encode("utf-8")
        request = urllib.request.Request(
            "https://api.stripe.com/v1/checkout/sessions", data=body,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": "Bearer " + api_key,
                "User-Agent": "PanganLaba/1.0",
            },
        )
        with urllib.request.urlopen(request, timeout=25) as response:
            session = json.loads(response.read().decode("utf-8"))
        url = str(session.get("url") or "").strip()
        if not url:
            raise ValueError("Stripe tidak mengembalikan halaman checkout.")
        return url, ext

    def _stripe_api_key(self) -> str:
        api_key = str(BILLING.get("stripe_api_key") or "").strip()
        if not api_key:
            raise ValueError("Provider stripe aktif, tetapi billing.stripe_api_key belum diisi.")
        return api_key

    def _ensure_recurring_price(self, plan: dict) -> str:
        """Kembalikan id Price recurring Stripe untuk plan (buat sekali, cache)."""
        plan_map = BILLING.get("stripe_price_map")
        if isinstance(plan_map, dict) and plan_map.get(plan["id"]):
            return str(plan_map[plan["id"]])
        cached = PRICE_CACHE.get(plan["id"])
        if cached:
            return cached
        fields = {
            "unit_amount": str(int(plan["price_idr"])),
            "currency": "IDR",
            "recurring[interval]": "month",
            "product_data[name]": f"Langganan PanganLaba - {plan['name']}",
        }
        request = urllib.request.Request(
            "https://api.stripe.com/v1/prices", data=urllib.parse.urlencode(fields).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded",
                     "Authorization": "Bearer " + self._stripe_api_key(),
                     "User-Agent": "PanganLaba/1.0"},
        )
        with urllib.request.urlopen(request, timeout=25) as response:
            price = json.loads(response.read().decode("utf-8"))
        price_id = str(price.get("id") or "")
        if not price_id:
            raise ValueError("Stripe tidak mengembalikan id harga.")
        PRICE_CACHE[plan["id"]] = price_id
        return price_id

    def _create_stripe_subscription_session(self, plan: dict, email: str) -> tuple[str, str]:
        """Buat Checkout Session mode=subscription (auto-renew bulanan)."""
        ext = f"pangan-stripe-{secrets.token_hex(6)}"
        base = self._base_url()
        price_id = self._ensure_recurring_price(plan)
        fields = {
            "mode": "subscription",
            "customer_email": email,
            "client_reference_id": ext,
            "success_url": base + "/?paid=success&session_id={CHECKOUT_SESSION_ID}",
            "cancel_url": base + "/?paid=failed",
            "line_items[0][quantity]": "1",
            "line_items[0][price]": price_id,
            "subscription_data[metadata][plan_id]": plan["id"],
            "subscription_data[metadata][email]": email,
            "subscription_data[metadata][amount_idr]": str(int(plan["price_idr"])),
        }
        request = urllib.request.Request(
            "https://api.stripe.com/v1/checkout/sessions", data=urllib.parse.urlencode(fields).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded",
                     "Authorization": "Bearer " + self._stripe_api_key(),
                     "User-Agent": "PanganLaba/1.0"},
        )
        with urllib.request.urlopen(request, timeout=25) as response:
            session = json.loads(response.read().decode("utf-8"))
        url = str(session.get("url") or "").strip()
        if not url:
            raise ValueError("Stripe tidak mengembalikan halaman checkout.")
        return url, ext

    def _auth_failure(self, reason: str):
        allowed = {"config", "cancelled", "state", "email", "provider"}
        reason = reason if reason in allowed else "provider"
        secure = "; Secure" if os.environ.get("PANGAN_COOKIE_SECURE", "").lower() == "true" else ""
        self._send(302, b"", "text/plain", {
            "Location": f"/?auth_error={reason}",
            "Set-Cookie": f"pangan_oauth_state=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0{secure}",
        })

    def _login(self):
        if not _oauth_matches_host(self):
            self._auth_failure("config")
            return
        try:
            metadata = _metadata()
            state = secrets.token_urlsafe(32)
            OAUTH_STATES[state] = time.time() + 600
            # Drop expired nonces to keep the single-process development server bounded.
            for saved_state, expiry in list(OAUTH_STATES.items()):
                if expiry <= time.time():
                    OAUTH_STATES.pop(saved_state, None)
            query = urllib.parse.urlencode({
                "client_id": GOOGLE["client_id"],
                "redirect_uri": AUTH["redirect_uri"],
                "response_type": "code",
                "scope": "openid email profile",
                "state": state,
                "prompt": "select_account",
            })
            secure = "; Secure" if urllib.parse.urlparse(AUTH["redirect_uri"]).scheme == "https" or \
                os.environ.get("PANGAN_COOKIE_SECURE", "").lower() == "true" else ""
            self._send(302, b"", "text/plain", {
                "Location": metadata["authorization_endpoint"] + "?" + query,
                "Set-Cookie": f"pangan_oauth_state={state}; Path=/; HttpOnly; SameSite=Lax; Max-Age=600{secure}",
            })
        except Exception as exc:
            print(f"[panganlaba] Google login initialization failed: {type(exc).__name__}", flush=True)
            self._auth_failure("provider")

    def _callback(self, query_string):
        query = urllib.parse.parse_qs(query_string)
        provider_error = query.get("error", [""])[0]
        if provider_error:
            self._auth_failure("cancelled" if provider_error == "access_denied" else "provider")
            return
        code, state = query.get("code", [""])[0], query.get("state", [""])[0]
        cookie_state = _cookie(self, "pangan_oauth_state")
        expiry = OAUTH_STATES.pop(state, 0) if state else 0
        if not code or not state or not hmac.compare_digest(state, cookie_state) or expiry < time.time():
            self._auth_failure("state")
            return
        try:
            metadata = _metadata()
            form = urllib.parse.urlencode({
                "code": code,
                "client_id": GOOGLE["client_id"],
                "client_secret": GOOGLE["client_secret"],
                "redirect_uri": AUTH["redirect_uri"],
                "grant_type": "authorization_code",
            }).encode()
            request = urllib.request.Request(metadata["token_endpoint"], data=form,
                headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "PanganLaba/1.0"})
            with urllib.request.urlopen(request, timeout=20) as response:
                token = json.loads(response.read())
            request = urllib.request.Request(metadata["userinfo_endpoint"],
                headers={"Authorization": "Bearer " + token["access_token"], "User-Agent": "PanganLaba/1.0"})
            with urllib.request.urlopen(request, timeout=20) as response:
                info = json.loads(response.read())
            email = str(info.get("email", "")).strip().casefold()
            if not email or str(info.get("email_verified", "")).lower() != "true":
                self._auth_failure("email")
                return
            name = str(info.get("name", "")).strip()
            start_or_get_account(DB, email, name, trial_days=7)
            cookie = _session_cookie(email, name, int(time.time()) + 2_592_000)
            secure = "; Secure" if urllib.parse.urlparse(AUTH["redirect_uri"]).scheme == "https" or \
                os.environ.get("PANGAN_COOKIE_SECURE", "").lower() == "true" else ""
            self._send(302, b"", "text/plain", {
                "Location": "/",
                "Set-Cookie": f"pangan_session={cookie}; Path=/; HttpOnly; SameSite=Lax; Max-Age=2592000{secure}",
            })
        except Exception as exc:
            print(f"[panganlaba] Google callback failed: {type(exc).__name__}", flush=True)
            self._auth_failure("provider")

    def _valid_csrf(self) -> bool:
        return hmac.compare_digest(self.headers.get("X-CSRF-Token", ""), CSRF_TOKEN)

    def _require_csrf(self) -> bool:
        # Webhook punya autentikasi sendiri (token/tanda tangan), bebas CSRF.
        webhooks = {"/api/webhook/xendit", "/api/webhook/stripe"}
        if urllib.parse.urlparse(self.path).path in webhooks:
            return True
        return self._valid_csrf()

    def do_POST(self):  # noqa: N802
        if not self._same_origin(): self._json({"error": "Origin tidak cocok."}, 403); return
        path = urllib.parse.urlparse(self.path).path
        if not self._require_csrf():
            self._json({"error": "Token keamanan tidak cocok. Muat ulang halaman."}, 403); return
        try:
            routes = {"/api/profit": self._profit, "/api/feedback": self._feedback,
                      "/api/subscription/request": self._subscription_request,
                      "/api/account/delete": self._delete_account,
                      "/api/admin/confirm-payment": self._admin_confirm,
                      "/api/train": self._start_training,
                      "/api/simulation": self._simulation,
                      "/api/webhook/xendit": self._xendit_webhook,
                      "/api/webhook/stripe": self._stripe_webhook,
                      "/api/train/local": self._train_local}
            handler = routes.get(path)
            if handler: handler()
            else: self._json({"error": "Rute tidak ditemukan."}, 404)
        except ValueError as exc: self._json({"error": str(exc)}, 400)
        except Exception as exc: self._json({"error": str(exc)}, 500)

    def _profit(self):
        user = self._access()
        if user is None: return
        _, email, preview = user
        body = self._read_json()
        recipe_rows = body.get("recipe", [])
        if not isinstance(recipe_rows, list) or len(recipe_rows) > 100:
            raise ValueError("Resep harus berupa daftar dengan maksimal 100 bahan.")
        recipe = pd.DataFrame(recipe_rows)
        if recipe.empty: raise ValueError("Tambahkan minimal satu bahan resep.")
        for col in ("commodity", "grams_per_portion", "actual_price_rp_per_kg"):
            if col not in recipe: raise ValueError("Kolom resep belum lengkap.")
        recipe["grams_per_portion"] = pd.to_numeric(recipe["grams_per_portion"], errors="coerce")
        if (recipe["grams_per_portion"].isna().any()
                or not recipe["grams_per_portion"].map(math.isfinite).all()
                or (recipe["grams_per_portion"] <= 0).any()
                or (recipe["grams_per_portion"] > 1_000_000).any()):
            raise ValueError("Takaran setiap bahan harus lebih dari 0 dan maksimal 1.000.000 gram per porsi.")
        raw_prices = recipe["actual_price_rp_per_kg"]
        has_price = raw_prices.notna() & raw_prices.astype(str).str.strip().ne("")
        recipe["actual_price_rp_per_kg"] = pd.to_numeric(raw_prices, errors="coerce")
        if (has_price & recipe["actual_price_rp_per_kg"].isna()).any():
            raise ValueError("Harga beli bahan harus berupa angka atau dikosongkan.")
        supplied_prices = recipe.loc[has_price, "actual_price_rp_per_kg"]
        if (not supplied_prices.map(math.isfinite).all()
                or (supplied_prices < 0).any()
                or (supplied_prices > 1_000_000_000_000).any()):
            raise ValueError("Harga beli bahan harus bernilai 0 sampai Rp1.000.000.000.000 per kg.")
        recipe["commodity"] = recipe["commodity"].fillna("").astype(str).str.strip()
        if (recipe["commodity"] == "").any():
            raise ValueError("Pilih komoditas untuk setiap bahan resep.")
        if len(recipe) == 0:
            raise ValueError("Tambahkan minimal satu bahan resep yang valid.")
        menu_name = _safe_text(body.get("menu_name"), 100)
        if not menu_name:
            raise ValueError("Nama menu wajib diisi.")
        selling_price = _finite_number(body.get("selling_price"), "Harga jual per porsi", strictly_positive=True)
        portions_value = _finite_number(body.get("portions_sold"), "Jumlah porsi", strictly_positive=True,
                                        maximum=100_000_000)
        if not portions_value.is_integer():
            raise ValueError("Jumlah porsi harus berupa bilangan bulat.")
        other_cost = _finite_number(body.get("other_cost_per_portion", 0), "Biaya lain per porsi")
        fixed_cost = _finite_number(body.get("fixed_cost", 0), "Biaya tetap")
        model_name = str(body.get("model", "GRU"))
        feature_name = str(body.get("features", "harga + cuaca + kalender + siklus tanggal"))
        names = list(dict.fromkeys(recipe["commodity"].tolist()))
        current = build_current_forecasts(ROOT, model_name, feature_name, commodities=names,
                                          restock_days=max(1, min(7, int(body.get("restock_days", 7)))))
        report, missing = compute_current_profit_report(
            recipe, current.get("quotes", {}), menu_name=menu_name,
            model_name=model_name, feature_name=feature_name, selling_price=selling_price,
            portions_sold=int(portions_value), other_cost_per_portion=other_cost,
            fixed_cost=fixed_cost, sales_period=_safe_text(body.get("sales_period", "Harian"), 50))
        if missing: self._json({"error": "Harga belum ditemukan: " + ", ".join(missing)}, 422); return
        saved = bool(body.get("save_history", True)) and not preview
        if saved:
            from pangan_forecast.business import save_profit_record
            report["record_id"] = save_profit_record(DB, email, report)
        self._json({"report": report, "saved": saved})

    def _simulation(self):
        if self._access() is None: return
        body = self._read_json()
        _, pred = frames()
        commodity = str(body.get("commodity", ""))
        model = str(body.get("model", ""))
        features = str(body.get("features", ""))
        view = pred[(pred["commodity"].astype(str) == commodity) & (pred["model"].astype(str) == model) &
                    (pred["features"].astype(str) == features)]
        if view.empty: raise ValueError("Data uji untuk simulasi tidak tersedia.")
        days = max(1, min(30, int(body.get("cycle_days", 7))))
        wait = max(0, min(days - 1, int(body.get("max_wait_days", 2))))
        quantity = max(.1, float(body.get("quantity_kg", 1)))
        result = simulate_purchase_policy(view, quantity_kg=quantity, threshold=.05,
                                          max_wait_days=wait, cycle_days=days)
        if result.empty: self._json({"rows": [], "summary": None}); return
        baseline, strategy = float(result["baseline_cost_rp"].sum()), float(result["policy_cost_rp"].sum())
        self._json({"rows": result.to_dict("records"), "summary": {
            "cycles": len(result), "deferred": int((result["wait_days"] > 0).sum()),
            "baseline_cost_rp": baseline, "policy_cost_rp": strategy,
            "savings_rp": baseline - strategy,
            "savings_pct": (baseline - strategy) / baseline * 100 if baseline else 0.0}})

    def _feedback(self):
        if self._access() is None: return
        body = self._read_json()
        if not body.get("consent_anonymous_feedback"): raise ValueError("Persetujuan peserta wajib ada.")
        code = _safe_text(body.get("session_code"), 40)
        if not code: raise ValueError("Isi kode sesi anonim.")
        fields = ("session_code", "business_type", "participant_role", "used_real_recipe_and_costs",
                  "calculator_task", "dashboard_task", "calculator_minutes", "dashboard_minutes",
                  "ease_rating_1_5", "clarity_rating_1_5", "usefulness_rating_1_5",
                  "manual_calculation_match", "would_use_again", "confusing_or_blocking", "requested_change")
        record = {key: body.get(key, "") for key in fields}
        record.update({"timestamp_local": datetime.now().astimezone().isoformat(timespec="seconds"),
                       "consent_anonymous_feedback": True})
        append_umkm_feedback(PATHS["feedback_csv"], record)
        self._json({"ok": True, "message": "Umpan balik anonim tersimpan."})

    def _subscription_request(self):
        user = self._user()
        if user is None: self._json({"error": "Login diperlukan."}, 401); return
        account, email, preview = user
        if preview:
            self._json({"error": "Paket berbayar hanya tersedia untuk akun pelanggan yang masuk dengan Google."}, 403); return
        body = self._read_json()
        plan_id = str(body.get("plan_id", ""))
        plan = get_plan(DB, plan_id)
        if not plan: raise ValueError("Paket tidak ditemukan.")
        checkout_urls = BILLING.get("checkout_urls", {})
        checkout = checkout_urls.get(plan_id, "") if hasattr(checkout_urls, "get") else ""
        checkout = str(checkout).replace("{email}", urllib.parse.quote(email)).replace("{amount}", str(plan["price_idr"]))
        provider = str(BILLING.get("provider") or "manual").strip().lower()
        payment_instructions = str(BILLING.get("payment_instructions") or "").strip()
        manual_payment_ready = bool(BILLING.get("bank_number") or payment_instructions)
        if not checkout and provider not in {"xendit", "stripe"} and not manual_payment_ready:
            self._json({"error": "Metode pembayaran belum dikonfigurasi. Silakan hubungi pengelola PanganLaba."}, 503)
            return
        set_subscription(DB, email, plan_id, status="incomplete", provider=provider)
        payment = {
            "method": "transfer",
            "bank_name": str(BILLING.get("bank_name") or ""),
            "account_number": str(BILLING.get("bank_number") or ""),
            "account_name": str(BILLING.get("bank_account_name") or ""),
            "amount_idr": int(plan["price_idr"]),
            "support_url": str(BILLING.get("support_url", "")),
            "support_label": str(BILLING.get("support_label", "Hubungi pengelola")),
        }
        # Provider online: buat checkout => redirect ke halaman pembayaran.
        if not checkout and provider == "xendit":
            try:
                checkout, external_id = self._create_xendit_invoice(plan, email)
                payment.update({"method": "online",
                                "message": "Kamu akan diarahkan ke halaman pembayaran (VA / QRIS / e-wallet)."})
                record_payment(DB, email, int(plan["price_idr"]), "pending",
                               provider="xendit", provider_transaction_id=external_id,
                               plan_id=plan_id)
            except Exception as exc:
                self._json({"error": f"Gagal membuat pembayaran: {exc}"}, 502)
                return
        elif not checkout and provider == "stripe":
            try:
                if str(BILLING.get("stripe_mode") or "subscription").strip().lower() == "subscription":
                    checkout, session_id = self._create_stripe_subscription_session(plan, email)
                    payment.update({"method": "online",
                                    "message": "Kamu akan diarahkan ke halaman pembayaran. Langganan diperbarui otomatis tiap bulan."})
                else:
                    checkout, session_id = self._create_stripe_session(plan, email)
                    payment.update({"method": "online",
                                    "message": "Kamu akan diarahkan ke halaman pembayaran (kartu / metode Stripe)."})
                record_payment(DB, email, int(plan["price_idr"]), "pending",
                               provider="stripe", provider_transaction_id=session_id,
                               plan_id=plan_id)
            except Exception as exc:
                self._json({"error": f"Gagal membuat pembayaran: {exc}"}, 502)
                return
        else:
            record_payment(DB, email, int(plan["price_idr"]), "pending",
                           provider="manual", plan_id=plan_id)
        self._json({"ok": True, "plan": plan, "checkout_url": checkout,
                    "payment": payment,
                    "payment_instructions": payment_instructions,
                    "message": "Permintaan paket tercatat. Akses diaktifkan otomatis setelah pembayaran dikonfirmasi."})

    def _xendit_webhook(self):
        """Aktivasi otomatis setelah Xendit membayar (status PAID)."""
        hook_token = str(BILLING.get("xendit_webhook_token") or "").strip()
        if not hook_token:
            self._json({"error": "Webhook Xendit belum dikonfigurasi."}, 503); return
        incoming = self.headers.get("x-callback-token", "") or self.headers.get("Xendit-Webhook-Token", "")
        if not hmac.compare_digest(incoming, hook_token):
            self._json({"error": "Token webhook tidak valid."}, 403); return
        body = self._read_json()
        ext = str(body.get("external_id") or "").strip()
        status = str(body.get("status") or "").upper()
        if not ext:
            self._json({"error": "Referensi transaksi tidak ditemukan."}, 400); return
        if status != "PAID":
            self._json({"ok": True, "activated": False, "status": status}); return
        amount = body.get("paid_amount", body.get("amount"))
        result = complete_provider_payment(
            DB, "xendit", ext, int(amount) if amount not in (None, "") else None
        )
        self._json({"ok": True, "activated": True, **result})

    def _unix_iso(self, value) -> str | None:
        try:
            return datetime.fromtimestamp(int(value), tz=timezone.utc).isoformat() if value else None
        except (TypeError, ValueError, OverflowError):
            return None

    def _apply_stripe_subscription(self, obj: dict) -> bool:
        """Set/update langganan dari event subscription (metadata memuat plan+email)."""
        meta = obj.get("metadata", {}) if isinstance(obj.get("metadata"), dict) else {}
        plan_id = str(meta.get("plan_id") or "")
        email = str(meta.get("email") or "")
        if not plan_id or "@" not in email:
            return False
        status = str(obj.get("status") or "active")
        set_subscription(
            DB, email, plan_id,
            status="active" if status == "active" else status,
            period_start=self._unix_iso(obj.get("current_period_start")),
            period_end=self._unix_iso(obj.get("current_period_end")),
            provider="stripe",
            provider_subscription_id=str(obj.get("id") or ""),
            cancel_at_period_end=int(bool(obj.get("cancel_at_period_end", False))),
        )
        return True

    def _stripe_webhook(self):
        """Webhook Stripe: aktivasi + auto-renew + pembatalan langganan."""
        secret = str(BILLING.get("stripe_webhook_secret") or "").strip()
        length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(length)
        if not secret:
            self._json({"error": "Webhook Stripe belum dikonfigurasi."}, 503); return
        from pangan_forecast.billing import verify_stripe_signature
        sig = self.headers.get("Stripe-Signature", "")
        if not verify_stripe_signature(payload, sig, secret):
            self._json({"error": "Tanda tangan webhook Stripe tidak valid."}, 403); return
        try:
            event = json.loads(payload.decode("utf-8"))
        except ValueError:
            self._json({"error": "Payload bukan JSON."}, 400); return
        event_type = str(event.get("type") or "")
        obj = event.get("data", {}).get("object", {}) or {}

        if event_type == "checkout.session.completed":
            # Fulfill only after Stripe reports the checkout as paid; lookup is durable.
            reference = str(obj.get("client_reference_id") or "").strip()
            if reference and str(obj.get("payment_status") or "").lower() == "paid":
                amount = obj.get("amount_total")
                result = complete_provider_payment(
                    DB, "stripe", reference, int(amount) if amount not in (None, "") else None
                )
                self._json({"ok": True, "activated": True, **result}); return
            self._json({"ok": True, "activated": False}); return

        if event_type in {"customer.subscription.created", "customer.subscription.updated"}:
            activated = self._apply_stripe_subscription(obj)
            self._json({"ok": True, "activated": activated}); return

        if event_type == "invoice.payment_succeeded":
            email = str(obj.get("customer_email") or "").strip()
            if email and "@" in email:
                record_payment(DB, email, int(obj.get("amount_paid", 0) or 0),
                               "succeeded", provider="stripe",
                               provider_transaction_id=str(obj.get("payment_intent") or ""))
            self._json({"ok": True, "handled": True}); return

        if event_type == "invoice.payment_failed":
            email = str(obj.get("customer_email") or "").strip()
            if email and "@" in email:
                record_payment(DB, email, int(obj.get("amount_due", 0) or 0),
                               "failed", provider="stripe",
                               provider_transaction_id=str(obj.get("payment_intent") or ""))
            self._json({"ok": True, "handled": True}); return

        if event_type == "customer.subscription.deleted":
            meta = obj.get("metadata", {}) if isinstance(obj.get("metadata"), dict) else {}
            email = str(meta.get("email") or "")
            if email and "@" in email:
                set_subscription(DB, email, "starter", status="canceled",
                                 provider="stripe", provider_subscription_id=str(obj.get("id") or ""))
            self._json({"ok": True, "handled": True}); return

        self._json({"ok": True, "handled": False})

    def _train_local(self):
        """Latih model dari data proyek (tanpa upload Excel), latar belakang."""
        user = self._require_admin()
        if user is None: return
        _, email, _ = user
        body = self._read_json()
        epochs = max(1, min(30, int(body.get("epochs", 15))))
        _audit("train_local", email, f"epochs={epochs}")
        job_id = secrets.token_urlsafe(10)
        snapshot = _snapshot_artifacts("train_local")
        TRAIN_JOBS[job_id] = {"id": job_id, "status": "queued",
                              "message": "Data lokal ditemukan. Menyiapkan…",
                              "metrics": 0, "epochs": epochs,
                              "snapshot": str(snapshot)}
        try:
            threading.Thread(target=_train_local_worker, args=(job_id,), daemon=True).start()
        except Exception:
            TRAIN_JOBS.pop(job_id, None)
            raise
        self._json({"job_id": job_id}, 202)

    def _admin_confirm(self):
        user = self._require_admin()
        if user is None: return
        _, email, _ = user
        body = self._read_json()
        payment_id = int(body.get("payment_id", 0))
        if payment_id <= 0: raise ValueError("Pilih transaksi transfer yang akan dikonfirmasi.")
        result = confirm_manual_payment_by_id(DB, payment_id)
        _audit("confirm_payment", email, f"payment_id={payment_id}")
        self._json({"ok": True, "payment": result})

    def _delete_account(self):
        user = self._user()
        if user is None or user[2]: self._json({"error": "Aksi ini hanya tersedia untuk akun pelanggan."}, 403); return
        account, email, _ = user
        if self._read_json().get("confirm") != email: raise ValueError("Ketik email akun untuk mengonfirmasi.")
        import sqlite3
        with sqlite3.connect(DB) as connection:
            for table in ("menu_profit_records", "payments", "subscriptions", "accounts"):
                connection.execute(f"DELETE FROM {table} WHERE email = ? COLLATE NOCASE", (email,))
        _audit("delete_account", email)
        self._send(200, json_bytes({"ok": True}), "application/json; charset=utf-8",
                   {"Set-Cookie": "pangan_session=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0"})

    def _start_training(self):
        user = self._require_admin()
        if user is None: return
        _, email, _ = user
        content_type = self.headers.get("Content-Type", "")
        length = int(self.headers.get("Content-Length", "0"))
        if length > 100_000_000: raise ValueError("Unggahan maksimum 100 MB.")
        raw = self.rfile.read(length)
        envelope = (f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n").encode() + raw
        message = BytesParser(policy=policy.default).parsebytes(envelope)
        fields, uploads = {}, []
        for part in message.iter_parts():
            name = part.get_param("name", header="content-disposition") or ""
            data = part.get_payload(decode=True) or b""
            filename = part.get_filename()
            if filename: uploads.append({"field": name, "filename": Path(filename).name, "data": data})
            else: fields[name] = data.decode(part.get_content_charset() or "utf-8", errors="replace")
        prices = [item for item in uploads if item["field"].startswith("price_")]
        if not prices: raise ValueError("Pilih Excel PIHPS (.xlsx) terlebih dahulu.")
        metadata = json.loads(fields.get("metadata", "[]"))
        meta = {str(x.get("field")): x for x in metadata}
        price_frames = []
        PATHS["upload_dir"].mkdir(parents=True, exist_ok=True)
        for item in prices:
            digest = hashlib.sha256(item["data"]).hexdigest()[:16]
            suffix = Path(item["filename"]).suffix.lower()
            (PATHS["upload_dir"] / f"pihps_{digest}{suffix}").write_bytes(item["data"])
            info = inspect_pihps_excel(item["data"])
            location = next((x for x in info["rows"] if x["label"].strip().casefold() in {"depok", "kota depok"}), None)
            if location is None: raise ValueError(f"Baris Kota Depok tidak ditemukan di {item['filename']}.")
            commodity = _safe_text(meta.get(item["field"], {}).get("commodity"), 100)
            if not commodity: raise ValueError(f"Isi nama komoditas untuk {item['filename']}.")
            price_frames.append(extract_pihps_series(item["data"], location["row_index"], commodity, "Kota Depok"))
        prices_frame = pd.concat(price_frames, ignore_index=True)
        PATHS["prices"].parent.mkdir(parents=True, exist_ok=True)
        epochs = max(1, min(30, int(fields.get("epochs", "15"))))
        nonce = secrets.token_hex(6)
        staged_prices = PATHS["upload_dir"] / f"prices_{nonce}.csv"
        weather_upload = next((x for x in uploads if x["field"] == "weather_file"), None)
        calendar_upload = next((x for x in uploads if x["field"] == "calendar_file"), None)
        staged_weather = PATHS["upload_dir"] / f"weather_{nonce}.csv" if weather_upload else None
        staged_calendar = PATHS["upload_dir"] / f"calendar_{nonce}.csv" if calendar_upload else None
        lock_acquired = False
        try:
            if not TRAIN_LOCK.acquire(blocking=False):
                raise ValueError("Training lain sedang berjalan.")
            lock_acquired = True
            # Keep old dates/commodities when uploads contain only a new period.
            merged_prices = _merge_uploaded_history(
                PATHS["prices"], prices_frame, ["date", "commodity", "location"]
            )
            merged_prices.to_csv(staged_prices, index=False, date_format="%Y-%m-%d")
            if weather_upload:
                weather_frame = pd.read_csv(io.BytesIO(weather_upload["data"]))
                merged_weather = _merge_uploaded_history(PATHS["weather"], weather_frame, ["date"])
                merged_weather.to_csv(staged_weather, index=False, date_format="%Y-%m-%d")
            if calendar_upload:
                calendar_frame = pd.read_csv(io.BytesIO(calendar_upload["data"]))
                merged_calendar = _merge_uploaded_history(PATHS["calendar"], calendar_frame, ["date"])
                merged_calendar.to_csv(staged_calendar, index=False, date_format="%Y-%m-%d")
            # Validate the merged dataset before replacing active files.
            load_and_merge(staged_prices, staged_weather or PATHS["weather"],
                           staged_calendar or PATHS["calendar"])
            # Backup artefak aktif sebelum menimpa; dipakai untuk rollback bila
            # pelatihan gagal setelah data diganti (F2).
            snapshot = _snapshot_artifacts("train")
            os.replace(staged_prices, PATHS["prices"])
            if staged_weather:
                os.replace(staged_weather, PATHS["weather"])
            if staged_calendar:
                os.replace(staged_calendar, PATHS["calendar"])
        except Exception:
            if lock_acquired:
                TRAIN_LOCK.release()
            if "snapshot" in locals():
                try:
                    _restore_artifacts(snapshot)
                except Exception:
                    pass
            raise
        finally:
            for staged in (staged_prices, staged_weather, staged_calendar):
                if staged and staged.exists():
                    staged.unlink()
        _audit("train_upload", email, f"files={len(prices)} epochs={epochs}")
        job_id = secrets.token_urlsafe(10)
        TRAIN_JOBS[job_id] = {"id": job_id, "status": "queued", "message": "Data diterima.",
                              "metrics": 0, "epochs": epochs,
                              "snapshot": str(snapshot)}
        try:
            threading.Thread(target=_train_worker, args=(job_id,), daemon=True).start()
        except Exception:
            TRAIN_JOBS.pop(job_id, None)
            TRAIN_LOCK.release()
            raise
        self._json({"job_id": job_id}, 202)

    def do_PUT(self):  # noqa: N802
        self._json({"error": "Method tidak didukung."}, 405)


def _train_worker(job_id: str):
    try:
        TRAIN_JOBS[job_id].update(status="training", message="Membersihkan data dan melatih model LSTM/GRU. Proses ini dapat memerlukan beberapa menit.")
        paths = project_paths(ROOT)
        clean = load_and_merge(paths["prices"], paths["weather"], paths["calendar"])
        clean.to_csv(ROOT / "data/processed/combined_daily.csv", index=False)
        os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
        from pangan_forecast.models import run_experiments, refit_full_history_models
        metrics, forecast = run_experiments(clean, ROOT, window=30, horizon=7,
            epochs=TRAIN_JOBS[job_id]["epochs"], batch_size=128, data_source="uploaded_pihps_excel")
        if metrics.empty: raise ValueError("Data terlalu pendek untuk membuat hasil model.")
        final_models = refit_full_history_models(
            clean, ROOT, window=30, horizon=7,
            epochs=TRAIN_JOBS[job_id]["epochs"], batch_size=128,
        )
        TRAIN_JOBS[job_id].update(status="done", message=f"Selesai: {len(metrics)} evaluasi dan {len(forecast)} prediksi.",
                                  metrics=len(metrics), forecasts=len(forecast),
                                  final_models=len(final_models))
    except Exception as exc:
        snap = Path(str(TRAIN_JOBS[job_id].get("snapshot") or ""))
        if snap.exists():
            try:
                _restore_artifacts(snap)
            except Exception:
                pass
        TRAIN_JOBS[job_id].update(status="error", message=str(exc))
    finally:
        TRAIN_LOCK.release()


def _train_local_worker(job_id: str):
    try:
        TRAIN_JOBS[job_id].update(status="training", message="Melatih LSTM/GRU dari data proyek…")
        os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
        from pangan_forecast.service import run_training
        clean_path = ROOT / "data/processed/combined_daily.csv"
        if not clean_path.exists():
            raise ValueError("data/processed/combined_daily.csv belum ada. Jalankan scripts/prepare_data.py dahulu.")
        clean = pd.read_csv(clean_path, parse_dates=["date"])
        is_demo = ("location" in clean.columns and clean["location"].astype(str)
                   .str.contains("DEMO", case=False, na=False).any())
        source_label = "synthetic_demo" if is_demo else "depok_pihps_era5_daily_weather_calendar"
        run_training(clean, ROOT, source_label, epochs=TRAIN_JOBS[job_id]["epochs"])
        TRAIN_JOBS[job_id].update(status="done", message="Selesai. Model dilatih dari data proyek.")
    except Exception as exc:
        snap = Path(str(TRAIN_JOBS[job_id].get("snapshot") or ""))
        if snap.exists():
            try:
                _restore_artifacts(snap)
            except Exception:
                pass
        TRAIN_JOBS[job_id].update(status="error", message=str(exc))


def main():
    os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
    try:
        server = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError as exc:
        if getattr(exc, "winerror", None) == 10048 or exc.errno == 98:
            raise SystemExit(
                f"Port {PORT} masih dipakai server lain. Hentikan proses server lama dengan Ctrl+C, lalu jalankan ulang."
            ) from exc
        raise
    server.daemon_threads = True
    print(f"PanganLaba HTML berjalan di http://{HOST}:{PORT}")
    print("Tekan Ctrl+C untuk berhenti.")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()


if __name__ == "__main__":
    main()
