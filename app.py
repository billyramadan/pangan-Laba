from pathlib import Path
import hashlib
import sys
from urllib.parse import urlsplit
import pandas as pd
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


def styled_table(frame: pd.DataFrame):
    """Improve table contrast with dark text and subtle alternating rows."""
    display = frame.reset_index(drop=True)

    def shade_row(row):
        background = "#F7EFE4" if row.name % 2 else "#FFFDFA"
        return [f"background-color: {background}; color: #2D2722; border-bottom: 1px solid #EADFD3;"] * len(row)

    formatters = {}
    integer_columns = {"Siklus", "Hari ditunda", "Porsi terjual", "Jumlah komoditas", "Urutan latih", "Urutan uji", "Epoch aktual"}
    for column in display.columns:
        if not pd.api.types.is_numeric_dtype(display[column]):
            continue
        if column in integer_columns:
            formatters[column] = "{:,.0f}"
        elif "(Rp)" in column or ("(Rp/kg)" in column and not column.startswith(("MAE", "RMSE"))):
            formatters[column] = "{:,.0f}"
        else:
            formatters[column] = "{:,.2f}"

    table_style = display.style.apply(shade_row, axis=1)
    return table_style.apply_index(
        lambda labels: [
            "background-color: #A33D22; color: #FFFFFF; font-weight: 700; border-bottom: 3px solid #E9A33B;"
        ] * len(labels),
        axis=1,
    ).format(formatters, na_rep="—")

ROOT = Path(__file__).resolve().parent
with open(ROOT / "app_run.log", "a", encoding="utf-8") as _boot_f:
    _boot_f.write("boot-c\n")
sys.path.insert(0, str(ROOT / "src"))
from pangan_forecast.data import load_and_merge
from pangan_forecast.pihps_excel import extract_pihps_series, inspect_pihps_excel
from pangan_forecast.recommend import simulate_purchase_policy
from pangan_forecast.accounts import start_or_get_account, delete_account
from pangan_forecast.business import get_profit_history, save_profit_record
from pangan_forecast.service import (
    project_paths, has_model_results, compute_overview,
    load_metrics_forecast, build_scenario, compute_profit_report,
    run_training, append_umkm_feedback,
    evaluate_model_results, model_comparison_for, cross_commodity_summary,
)
from pangan_forecast.billing import (
    initialize_billing, check_account_access, list_plans, set_subscription,
    list_incomplete_subscriptions, confirm_manual_payment, list_all_subscriptions,
)

st.set_page_config(page_title="PanganLaba | Depok", page_icon=":material/monitoring:", layout="wide")

st.markdown("""
<style>
:root { --ink:#2d2722; --muted:#746c64; --primary:#c64d2c; --primary-dark:#a33d22; --spice:#e9a33b; --tomato:#c64d2c; --line:#eadfd3; --surface:#fffdfa; --canvas:#fff9f1; }
.stApp { background:var(--canvas); color:var(--ink); }
[data-testid="stAppViewContainer"] { background:var(--canvas); }
.block-container { max-width:1320px; padding-top:1.25rem; padding-bottom:3.5rem; }
[data-testid="stToolbar"] { display:none; }
[data-testid="stHeader"] { height:0 !important; min-height:0 !important; background:transparent; }
[data-testid="stDecoration"] { background:linear-gradient(90deg,#c64d2c 0 58%,#e9a33b 58% 82%,#594236 82%); height:4px; }
[data-testid="stSidebar"] { background:#f7efe4; border-right:1px solid #eadfd3; }
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,[data-testid="stSidebar"] p,[data-testid="stSidebar"] label,[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] { color:var(--ink) !important; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color:var(--muted) !important; }
[data-testid="stSidebar"] hr { border-color:#e7d8c8; }
h1,h2,h3,h4 { color:var(--ink); letter-spacing:-.025em; }
.page-intro { color:#655b52; max-width:940px; font-size:1.08rem; line-height:1.7; margin:.35rem 0 .8rem; }
.section-label { color:var(--primary-dark); font-size:.73rem; font-weight:850; letter-spacing:.13em; text-transform:uppercase; margin:1.65rem 0 .65rem; }
div[data-testid="stMetric"] { background:var(--surface); border:1px solid var(--line); border-radius:16px; padding:1.05rem 1.15rem; box-shadow:0 7px 22px rgba(94,58,34,.055); min-height:108px; }
.st-key-data_summary [data-testid="stColumn"]:nth-child(1) [data-testid="stMetric"] { border-top:3px solid #c64d2c; }
.st-key-data_summary [data-testid="stColumn"]:nth-child(2) [data-testid="stMetric"] { border-top:3px solid #e9a33b; }
.st-key-data_summary [data-testid="stColumn"]:nth-child(3) [data-testid="stMetric"] { border-top:3px solid #8b6b4a; }
[data-testid="stMetricLabel"] p { color:var(--muted) !important; font-size:.8rem; font-weight:650; }
[data-testid="stMetricValue"] div { color:var(--ink) !important; font-size:1.42rem; line-height:1.25; white-space:normal; font-weight:700; }
[data-testid="stMetricDelta"] { color:var(--primary-dark) !important; }
.st-key-analysis_filters,.st-key-profit_panel { background:var(--surface); border:1px solid var(--line); border-radius:16px; padding:1rem 1.15rem 1.1rem; box-shadow:0 7px 24px rgba(32,53,47,.05); }
.st-key-analysis_filters h3 { color:var(--ink); font-size:1.15rem; }
div[data-testid="stTabs"] > div:first-child { gap:.55rem; border-bottom:1px solid #d9d4c9; align-items:flex-end; }
button[data-baseweb="tab"] { border:1px solid transparent; border-bottom:0; border-radius:10px 10px 0 0; background:transparent; color:#746c64; font-size:.94rem; font-weight:700; padding:.82rem 1.25rem; transition:background-color .15s ease,color .15s ease; }
button[data-baseweb="tab"]:hover { color:var(--primary-dark); background:#f5e9dc; }
button[data-baseweb="tab"][aria-selected="true"] { color:#fff !important; background:var(--primary) !important; border-color:var(--primary); box-shadow:inset 0 -3px 0 var(--spice); }
button[data-baseweb="tab"][aria-selected="true"] * { color:#fff !important; }
div[data-testid="stTabs"] [role="tabpanel"] { padding-top:.65rem; }
div[data-testid="stForm"] { border:0; padding:0; }
div[data-testid="stExpander"] { background:var(--surface); border:1px solid var(--line); border-radius:12px; box-shadow:0 3px 12px rgba(32,53,47,.025); }
.status-card { background:#f8f0e5; border:1px solid #eedbc4; border-left:4px solid var(--primary); border-radius:10px; padding:.85rem 1rem; margin:.65rem 0 .9rem; }
.status-card p { color:var(--ink); margin:0; line-height:1.5; }
[data-testid="stButton"] button { border-radius:9px; font-weight:650; transition:transform .15s ease,box-shadow .15s ease; }
[data-testid="stButton"] button:hover { transform:translateY(-1px); box-shadow:0 5px 14px rgba(24,84,64,.12); }
.stButton > button[kind="primary"] { background:var(--primary); border-color:var(--primary); color:#fff; }
[data-testid="stButton"] button[kind="primary"]:hover { background:var(--primary-dark); border-color:var(--primary-dark); color:#fff; }
[data-testid="stSelectbox"] div[data-baseweb="select"] > div { background:#fff !important; border-color:var(--line) !important; color:var(--ink) !important; }
[data-testid="stSelectbox"] div[data-baseweb="select"] span { color:var(--ink) !important; }
[data-testid="stSelectbox"] div[data-baseweb="select"] svg { fill:var(--muted) !important; }
[data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within > div { border-color:var(--primary) !important; box-shadow:0 0 0 1px var(--primary); }
[data-testid="stDataFrame"],[data-testid="stDataEditor"] {
 --gdg-bg-cell:#fffdfa; --gdg-bg-cell-medium:#f7efe4; --gdg-bg-header:#a33d22;
 --gdg-bg-header-hover:#91381f; --gdg-bg-header-has-focus:#a33d22;
 --gdg-text-dark:#2d2722; --gdg-text-medium:#62574e; --gdg-text-light:#85776b;
 --gdg-accent-color:#c64d2c; --gdg-border-color:#eadfd3;
 background:var(--surface); border:1px solid #eadfd3; border-radius:13px;
 overflow:hidden; box-shadow:0 5px 18px rgba(94,58,34,.055);
}
[data-testid="stDataEditor"] { --gdg-bg-header:#a33d22; --gdg-bg-header-hover:#91381f; }
.st-key-recipe_editor_card { background:#fbf3e7; border:1px solid #ecdcc6; border-radius:15px; padding:.9rem 1rem .65rem; margin:.45rem 0 .8rem; }
.recipe-heading { display:flex; align-items:center; gap:.65rem; color:#2d2722; font-weight:800; font-size:1rem; margin:0 0 .25rem; }
.recipe-heading .recipe-tag { display:inline-block; color:#a33d22; background:#f4e2cf; border-radius:999px; padding:.22rem .55rem; font-size:.67rem; letter-spacing:.08em; font-weight:850; }
.recipe-help { color:#746c64; font-size:.88rem; line-height:1.5; margin:.25rem 0 .55rem; }
.st-key-recipe_editor_card [data-testid="stDataEditor"] { border-radius:12px; --gdg-bg-cell:#fffdfa; --gdg-bg-cell-medium:#f7efe4; --gdg-bg-header:#a33d22; --gdg-bg-header-hover:#91381f; --gdg-bg-header-has-focus:#a33d22; --gdg-text-dark:#2d2722; --gdg-text-medium:#62574e; --gdg-text-light:#85776b; --gdg-accent-color:#c64d2c; --gdg-border-color:#eadfd3; --gdg-header-font-style:700 13px var(--gdg-font-family); }
.st-key-project_hero { background:#fffdfa; border:1px solid var(--line); border-radius:20px; padding:1rem 1.15rem 1.1rem; margin:.2rem 0 1.1rem; box-shadow:0 9px 28px rgba(94,58,34,.06); }
.st-key-project_hero [data-testid="stImage"] { display:flex; justify-content:center; }
.st-key-project_hero [data-testid="stImage"] img { display:block; width:100%; max-width:100%; height:auto; border:1px solid #f0ddc5; border-radius:16px; }
.st-key-project_hero h1 { color:#2d2722; font-size:clamp(2rem,3.5vw,3.15rem); line-height:1.02; margin:.35rem 0 .8rem; max-width:680px; }
.hero-label { color:#a33d22; font-size:.7rem; font-weight:850; letter-spacing:.11em; text-transform:uppercase; margin-top:.8rem; }
.hero-actions { display:flex; flex-wrap:wrap; gap:.65rem; margin:1rem 0 .35rem; }
.hero-actions a { display:inline-block; border-radius:9px; padding:.68rem 1rem; font-size:.91rem; font-weight:750; text-decoration:none; }
.hero-actions a:first-child { background:#c64d2c; border:1px solid #c64d2c; color:#fff; box-shadow:0 4px 10px rgba(163,61,34,.13); }
.hero-actions a:last-child { background:#fffdfa; border:1px solid #d9cbbd; color:#2d2722; }
.hero-actions a:hover { transform:translateY(-1px); }
.st-key-workflow_cards [data-testid="stVerticalBlockBorderWrapper"] { background:var(--surface); border:1px solid var(--line); border-radius:14px; box-shadow:0 5px 16px rgba(32,53,47,.035); min-height:126px; }
.workflow-step { color:#b94b35; font-size:.7rem; font-weight:800; letter-spacing:.1em; text-transform:uppercase; margin:0 0 .25rem; }
.workflow-title { color:#2d2722; font-size:1rem; font-weight:750; margin:0 0 .28rem; }
.workflow-copy { color:#746c64; font-size:.88rem; line-height:1.45; margin:0; }
/* ===== Landing publik (gaya raciklaba.id) ===== */
.landing-brand { font-size:1.32rem; font-weight:850; color:var(--ink); letter-spacing:-.02em; background:var(--canvas); padding:.35rem 0; }
.landing-nav { display:flex; gap:1.4rem; justify-content:flex-end; background:var(--canvas); }
.landing-nav-link { color:var(--muted); font-size:.95rem; font-weight:650; text-decoration:none; white-space:nowrap; }
.landing-nav-link:hover { color:var(--primary); }
.landing-tag { display:inline-block; background:#f6e5d2; color:var(--primary-dark); border-radius:999px; padding:.4rem .9rem; font-size:.8rem; font-weight:750; letter-spacing:.02em; margin-bottom:.9rem; }
.landing-section-title { color:var(--ink); font-size:1.35rem; font-weight:800; letter-spacing:-.02em; margin:1.4rem 0 .9rem; }
.landing-hero h1 { color:var(--ink); font-size:clamp(2rem,4.2vw,3.1rem); line-height:1.1; letter-spacing:-.03em; margin:0 0 1.1rem; word-wrap:break-word; }
.landing-lead { color:var(--muted); font-size:1.08rem; line-height:1.65; margin-bottom:1.6rem; max-width:560px; }
.landing-btn-secondary { display:block; width:100%; text-align:center; background:var(--surface); border:1px solid #d9cbbd; color:var(--ink); font-weight:700; font-size:.92rem; border-radius:9px; padding:.62rem .9rem; text-decoration:none; box-sizing:border-box; transition:box-shadow .15s ease,transform .15s ease; }
.landing-btn-secondary:hover { box-shadow:0 5px 14px rgba(94,58,34,.12); transform:translateY(-1px); }
.landing-step-num { width:40px; height:40px; border-radius:50%; background:var(--primary); color:#fff; font-weight:800; display:flex; align-items:center; justify-content:center; font-size:1.05rem; }
.landing-step { background:var(--surface); border:1px solid var(--line); border-radius:14px; padding:.78rem 1rem; font-size:.95rem; color:var(--muted); margin-bottom:.6rem; min-height:42px; display:flex; align-items:center; }
.landing-step strong { color:var(--ink); }
.landing-visual { max-width:560px; margin-left:auto; margin-top:1.1rem; background:var(--surface); border:1px solid var(--line); border-radius:16px; box-shadow:0 14px 36px rgba(94,58,34,.12); padding:1.15rem 1.2rem; }
.landing-card-label { color:var(--muted); font-size:.82rem; font-weight:650; margin-bottom:.25rem; }
.landing-card-value { color:var(--ink); font-size:2.1rem; font-weight:850; letter-spacing:-.02em; margin-bottom:.3rem; }
.landing-card-sub { color:var(--muted); font-size:.82rem; line-height:1.45; }
.landing-chips { display:flex; flex-wrap:wrap; gap:.55rem; justify-content:center; margin-top:.2rem; }
.landing-chip { display:inline-block; background:var(--surface); border:1px solid var(--line); border-radius:999px; padding:.42rem .95rem; font-size:.8rem; font-weight:650; color:var(--muted); white-space:nowrap; }
.st-key-simulation_panel { background:#fbf3e7; border:1px solid #ecdcc6; border-radius:17px; padding:1.1rem 1.15rem .95rem; margin-top:1rem; }
.st-key-simulation_panel h4 { color:#2d2722; }
.st-key-simulation_metrics [data-testid="stColumn"]:nth-child(1) [data-testid="stMetric"] { border-top:3px solid #8b6b4a; }
.st-key-simulation_metrics [data-testid="stColumn"]:nth-child(2) [data-testid="stMetric"] { border-top:3px solid #a33d22; }
.st-key-simulation_metrics [data-testid="stColumn"]:nth-child(3) [data-testid="stMetric"] { border-top:3px solid #e9a33b; }
.st-key-simulation_metrics [data-testid="stColumn"]:nth-child(4) [data-testid="stMetric"] { border-top:3px solid #d9573d; }
[data-testid="stAlert"] { border-radius:11px; }
a { color:var(--primary-dark); }
@media (max-width:640px) {
 .block-container { padding:1rem .85rem 2rem; }
 .st-key-analysis_filters,.st-key-profit_panel,.st-key-simulation_panel { padding:.7rem .75rem .75rem; }
 .st-key-project_hero { padding:.7rem; border-radius:15px; }
 .st-key-workflow_cards [data-testid="stVerticalBlockBorderWrapper"] { min-height:0; }
 div[data-testid="stMetric"] { padding:.72rem .75rem; min-height:88px; }
 [data-testid="stMetricValue"] div { font-size:1.2rem; }
 button[data-baseweb="tab"] { font-size:.85rem; padding:.68rem .72rem; }
 [data-testid="stHorizontalBlock"] { flex-wrap:wrap; gap:.9rem; }
 [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { flex:0 0 100% !important; max-width:100% !important; }
 .landing-brand { font-size:1.2rem; }
 .landing-nav { justify-content:flex-start; gap:.9rem; margin-top:.2rem; }
 .landing-nav-link { font-size:.85rem; }
 .landing-hero h1 { font-size:1.9rem; line-height:1.15; margin-bottom:.9rem; }
 .landing-lead { font-size:1rem; margin-bottom:1.4rem; }
 .landing-visual { max-width:100%; margin:1.2rem 0 0; padding:1rem; }
 [data-testid="stImage"] img { max-height:300px; width:100%; object-fit:cover; border-radius:14px; }
 .landing-chips { gap:.45rem; }
 .landing-chip { font-size:.78rem; padding:.42rem .85rem; }
 [data-testid="stButton"] button { min-height:46px; font-size:1rem; }
}
</style>
""", unsafe_allow_html=True)

# Real identity comes from Google OIDC; passwords are never stored by this app.
try:
    auth_config = st.secrets.get("auth", {})
    billing_config = st.secrets.get("billing", {})
except StreamlitSecretNotFoundError:
    auth_config = {}
    billing_config = {}
google_config = auth_config.get("google", {}) if hasattr(auth_config, "get") else {}


def render_subscription_offer():
    """Show available paid plans and an external/manual payment path."""
    support_url = str(billing_config.get("support_url", "")).strip()
    support_label = str(billing_config.get("support_label", "Hubungi pengelola")).strip()
    instructions = str(billing_config.get("payment_instructions", "")).strip()
    checkout_url = str(billing_config.get("checkout_url", "")).strip()

    try:
        plans = list_plans(ROOT / "data" / "app_users.sqlite3")
    except Exception:
        plans = []
    if not plans:
        # Fallback: single configured plan if the plan table is empty.
        plan_name = str(billing_config.get("plan_name", "PanganLaba Bulanan"))
        try:
            price_idr = max(0, int(billing_config.get("price_idr", 0) or 0))
        except (TypeError, ValueError):
            price_idr = 0
        plans = [{"id": "fallback", "name": plan_name, "price_idr": price_idr,
                  "interval": "month", "interval_count": 1,
                  "features": ["Akses penuh dashboard fit prediksi", "Kalkulator modal & laba menu", "Riwayat usaha"]}]

    selected = st.session_state.get("selected_plan")

    plan_cols = st.columns(len(plans), gap="medium")
    for column, plan in zip(plan_cols, plans):
        with column.container(border=True):
            st.subheader(plan["name"])
            price = f"Rp{plan['price_idr']:,.0f}" if plan["price_idr"] else "Hubungi pengelola"
            interval = plan.get("interval", "month")
            period = f"/{plan['interval_count']} bulan" if interval == "month" else f"/{plan['interval_count'] * 12} bulan"
            st.markdown(f"<div style='font-size:1.6rem;font-weight:800;color:var(--primary-dark)'>{price}{period}</div>",
                        unsafe_allow_html=True)
            for feature in plan.get("features", []):
                st.markdown(f"- {feature}")
            if st.button("Pilih paket ini", key=f"choose_{plan['id']}",
                         type="primary", use_container_width=True,
                         disabled=bool(checkout_url)):
                try:
                    rec = set_subscription(ROOT / "data" / "app_users.sqlite3",
                                           user_email, plan["id"], status="incomplete")
                    st.session_state["selected_plan"] = plan["id"]
                    st.session_state["selected_plan_amount"] = plan["price_idr"]
                    st.success(f"Paket {plan['name']} dipilih. Silakan transfer sesuai instruksi di bawah.")
                except Exception as exc:
                    st.error(f"Gagal mencatat paket: {exc}")

    if selected:
        amount = st.session_state.get("selected_plan_amount")
        st.markdown(
            '<div class="status-card">'
            f'<p><strong>Pembayaran ke rekening BCA</strong><br>'
            f'Nomor: <strong>8692436708</strong> a.n. PanganLaba<br>'
            f'Jumlah: <strong>Rp{amount:,.0f}</strong> — paket {selected}<br>'
            'Setelah transfer, kirim bukti ke pengelola; akses diaktifkan setelah diverifikasi.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        if support_url:
            st.link_button(support_label or "Hubungi pengelola", support_url)
    elif instructions:
        st.info(instructions, icon=":material/payments:")
    elif checkout_url:
        st.link_button("Lanjut ke pembayaran", checkout_url, type="primary", icon=":material/payments:")
    if not selected and support_url:
        st.link_button(support_label or "Hubungi pengelola", support_url)
_UNCONFIGURED = {
    "", "GANTI_DENGAN_CLIENT_ID", "GANTI_DENGAN_CLIENT_SECRET",
    "GANTI_DENGAN_RANDOM_SECRET_PANJANG",
}

def _configured(value) -> bool:
    return bool(value) and str(value) not in _UNCONFIGURED

_PLAN_COMMODITY_CAP = {"starter": 3, "pro": 10, "enterprise": None}


def _plan_index() -> dict:
    try:
        return {p["id"]: p for p in list_plans(ROOT / "data" / "app_users.sqlite3")}
    except Exception:
        return {}


def _open_subscription():
    st.session_state["show_subscription"] = True
    st.session_state["show_my_plan"] = False
    st.rerun()


def render_my_plan():
    """Tampilkan paket aktif, sisa akses, dan tombol upgrade."""
    st.markdown('<div class="section-label">Paket saya</div>', unsafe_allow_html=True)
    status = account["status"]
    status_label = {
        "trial": "Trial", "active": "Langganan aktif",
        "preview": "Preview", "expired": "Trial berakhir",
    }.get(status, status)
    col1, col2 = st.columns(2, gap="medium")
    col1.metric("Status", status_label)
    col2.metric("Sisa akses", f"{account['days_remaining']} hari")

    plan_id = account.get("plan_id")
    plans = _plan_index()
    if status == "active" and plan_id in plans:
        plan = plans[plan_id]
        interval = plan.get("interval", "month")
        period = f"/{plan['interval_count']} bulan" if interval == "month" else f"/{plan['interval_count'] * 12} bulan"
        st.markdown(
            '<div class="status-card">'
            f'<p><strong>{plan["name"]}</strong> · Rp{plan["price_idr"]:,.0f}{period}<br>'
            f'Komoditas dianalisis: {account.get("commodity_cap") or "tak terbatas"}<br>'
            f'Fitur: {", ".join(plan.get("features", []))}</p></div>',
            unsafe_allow_html=True,
        )
        if st.button("Upgrade paket", key="upgrade_plan", type="primary",
                     icon=":material/upgrade:"):
            _open_subscription()
    elif status in {"trial", "preview"}:
        st.info("Masih dalam masa trial. Setelah trial berakhir, pilih paket untuk melanjutkan akses.")
        if st.button("Lihat paket & harga", key="view_plans_from_myplan",
                     type="primary", icon=":material/card_membership:"):
            _open_subscription()
    else:
        st.warning("Akses terkunci karena masa trial berakhir. Pilih paket untuk melanjutkan.")
        if st.button("Pilih paket", key="choose_plan_from_myplan",
                     type="primary", icon=":material/card_membership:"):
            _open_subscription()

    st.divider()
    with st.expander("Hapus akun & data", icon=":material/delete_forever:"):
        st.caption("Menghapus akun, langganan, dan riwayat data usaha secara permanen. Tindakan ini tidak dapat dibatalkan.")
        confirm_delete = st.checkbox("Saya yakin ingin menghapus akun ini.", key="confirm_delete_account")
        if st.button("Hapus akun", key="delete_account_btn", type="primary",
                     disabled=not confirm_delete):
            try:
                delete_account(ROOT / "data" / "app_users.sqlite3", user_email)
                st.session_state.clear()
                st.logout()
            except Exception as exc:
                st.error(f"Gagal menghapus akun: {exc}")


def _admin_emails() -> set:
    """Email Google pemilik yang berhak membuka Panel Admin (dari [admin].emails)."""
    try:
        raw = st.secrets.get("admin", {}).get("emails", [])
    except StreamlitSecretNotFoundError:
        return set()
    if isinstance(raw, str):
        raw = [e for e in raw.split(",") if e.strip()]
    return {str(e).strip().lower() for e in raw if str(e).strip()}


def render_admin_panel(db: Path, admin_email: str):
    """Panel verifikasi pembayaran manual (BCA) & rekap langganan."""
    st.title("Panel Admin", anchor=False)
    st.caption(f"Masuk sebagai pengelola · {admin_email}")

    st.markdown('<div class="section-label">Verifikasi pembayaran (menunggu)</div>', unsafe_allow_html=True)
    try:
        pending = list_incomplete_subscriptions(db)
    except Exception as exc:
        st.error(f"Gagal memuat antrean verifikasi: {exc}")
        pending = []
    if not pending:
        st.success("Tidak ada pembayaran yang menunggu konfirmasi.")
    for row in pending:
        c1, c2 = st.columns([3, 1], vertical_alignment="center")
        with c1:
            name = row.get("display_name") or row["email"]
            st.markdown(f"**{name}** — `{row['email']}`")
            st.caption(
                f"{row['plan_name']} · Rp{row['price_idr']:,} · diminta "
                f"{row['created_at'][:16].replace('T', ' ')} UTC"
            )
        with c2:
            if st.button("Konfirmasi bayar", key=f"ok_{row['email']}", type="primary"):
                try:
                    confirm_manual_payment(db, row["email"], row["plan_id"])
                    st.success(f"Akses diaktifkan untuk {row['email']} ({row['plan_name']}).")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Gagal konfirmasi: {exc}")

    st.divider()
    st.markdown('<div class="section-label">Rekap semua langganan</div>', unsafe_allow_html=True)
    status_label = {
        "active": "Aktif", "incomplete": "Belum bayar",
        "past_due": "Telat bayar", "canceled": "Dibatalkan",
    }
    try:
        subs = list_all_subscriptions(db)
        if not subs:
            st.info("Belum ada langganan tercatat.")
        else:
            df = pd.DataFrame(subs)
            if "display_name" in df:
                df.insert(0, "Nama", df.pop("display_name").fillna("-"))
            df = df.rename(columns={
                "email": "Email", "plan_name": "Paket", "status": "Status",
                "current_period_end": "Berakhir", "updated_at": "Diperbarui",
            })
            if "Status" in df:
                df["Status"] = df["Status"].map(status_label).fillna(df["Status"])
            st.dataframe(df, use_container_width=True, hide_index=True)
    except Exception as exc:
        st.warning(f"Gagal memuat rekap: {exc}")


def _commodity_cap(account: dict):
    """Jumlah komoditas yang boleh dianalisis per paket (None = tak terbatas)."""
    if account.get("status") == "active" and account.get("plan_id") in _PLAN_COMMODITY_CAP:
        return _PLAN_COMMODITY_CAP[account["plan_id"]]
    return None

_auth_ready = all(
    _configured(auth_config.get(key)) for key in ("redirect_uri", "cookie_secret")
) and all(
    _configured(google_config.get(key)) for key in ("client_id", "client_secret", "server_metadata_url")
)
_request_host = urlsplit("//" + str(st.context.headers.get("host", ""))).hostname or ""
_demo_override = bool(auth_config.get("enable_demo"))
local_preview = (_demo_override or not _auth_ready) and _request_host.lower() in {"localhost", "127.0.0.1", "::1"}


def _resolve_account():
    if not _auth_ready and not local_preview:
        st.title("Login dan akses trial")
        st.info(
            "Kerangka login trial dan langganan sudah disiapkan, tetapi akses belum aktif. "
            "Konfigurasikan Google OAuth di `.streamlit/secrets.toml` untuk akses pelanggan. "
            "Untuk mencoba dashboard dan fitur laba di komputer ini, jalankan mode preview lokal.",
            icon=":material/lock:",
        )
        st.code(".\\scripts\\run_local.ps1", language="powershell")
        st.caption("Mode preview hanya untuk komputer lokal; login, trial pelanggan, dan langganan tetap memerlukan OAuth.")
        st.markdown("Langkah OAuth lengkap ada di **`docs/TRIAL_SUBSCRIPTION.md`**.")
        st.stop()

    _DEMO_ACCOUNTS = {
        "Preview dasar": ("preview-lokal@pangan.local", "Preview lokal",
                          {"status": "preview", "days_remaining": 0, "access_allowed": True}),
        "Trial baru (7 hari)": ("trial@demo.local", "Demo Trial",
                                {"status": "trial", "days_remaining": 7, "access_allowed": True}),
        "Langganan aktif": ("aktif@demo.local", "Demo Pro",
                            {"status": "active", "days_remaining": 25, "access_allowed": True, "plan_id": "starter"}),
        "Trial telah berakhir": ("habis@demo.local", "Demo Expired",
                                 {"status": "expired", "days_remaining": 0, "access_allowed": False}),
    }

    if local_preview:
        persona = st.selectbox("Simulasi status akun (demo lokal)", list(_DEMO_ACCOUNTS))
        user_email, user_name, account = _DEMO_ACCOUNTS[persona]
        return account, user_email, user_name

    if not st.user.is_logged_in:
        # Landing publik mirip raciklaba.id: hanya menjelaskan kegunaan, tanpa data/fitur.
        def _login_google():
            try:
                st.login("google")
            except Exception as _exc:
                import traceback as _tb
                with open(ROOT / "app_error.log", "w", encoding="utf-8") as _f:
                    _f.write(_tb.format_exc())
                st.error(f"Login gagal: {_exc}", icon=":material/error:")
                st.code(_tb.format_exc(), language="python")

        top_cols = st.columns([1.6, 2.4, 0.8], gap="medium", vertical_alignment="center")
        with top_cols[0]:
            st.markdown('<div class="landing-brand">PanganLaba</div>', unsafe_allow_html=True)
        with top_cols[1]:
            st.markdown(
                '<div class="landing-nav">'
                '<a href="#fitur" class="landing-nav-link">Fitur</a>'
                '<a href="#cara-kerja" class="landing-nav-link">Cara kerja</a>'
                '<a href="#harga" class="landing-nav-link">Harga</a>'
                '<a href="#pertanyaan" class="landing-nav-link">Pertanyaan</a>'
                '</div>',
                unsafe_allow_html=True,
            )
        with top_cols[2]:
            if st.button("Masuk", use_container_width=True):
                _login_google()

        hero_cols = st.columns([1.25, 1], gap="large")
        with hero_cols[0]:
            st.markdown(
                '<div class="landing-tag">Aplikasi web untuk usaha makan &amp; minuman</div>'
                '<div class="landing-hero"><h1>'
                'Jualan enak saja belum cukup.<br>Pastikan juga untung.</h1></div>'
                '<div class="landing-lead">'
                'PanganLaba menghitung modal tiap porsi, memperkirakan harga jual yang aman, '
                'dan merapikan pesanan Kakak — pakai bahasa sehari-hari, bukan bahasa akuntan.'
                '</div>',
                unsafe_allow_html=True,
            )
            b1, b2 = st.columns(2, gap="medium")
            with b1:
                if st.button("Mulai gratis sekarang", type="primary", icon=":material/login:",
                             use_container_width=True):
                    _login_google()
            with b2:
                st.markdown(
                    '<a class="landing-btn-secondary" href="#cara-kerja">Lihat cara kerjanya</a>',
                    unsafe_allow_html=True,
                )
            st.caption("Tanpa kartu kredit · Paket trial 7 hari · Siap dipakai dari HP")
        with hero_cols[1]:
            st.image((ROOT / "assets" / "umkm_header.jpg").as_posix(),
                     use_container_width=True, output_format="auto")
            st.markdown(
                '<div class="landing-visual">'
                '<div class="landing-card-label">Modal per porsi</div>'
                '<div class="landing-card-value">Rp8.400</div>'
                '<div class="landing-card-sub">Harga jual aman dari Rp14.000<br>'
                'Angka contoh, bukan data usaha sungguhan.</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        try:
            _land_plans = list_plans(ROOT / "data" / "app_users.sqlite3")
        except Exception:
            _land_plans = [
                {"id": "starter", "name": "Starter", "price_idr": 150_000, "features": ["3 komoditas", "Dashboard dasar"]},
                {"id": "pro", "name": "Pro", "price_idr": 300_000, "features": ["10 komoditas", "Support prioritas"]},
                {"id": "enterprise", "name": "Enterprise", "price_idr": 750_000, "features": ["Komoditas tak terbatas", "Support VIP"]},
            ]

        st.markdown('<div id="fitur" class="landing-section-title">Fitur PanganLaba</div>', unsafe_allow_html=True)
        land_cols = st.columns(3, gap="medium")
        land_feats = [
            ("PREDIKSI HARGA",
             "Perkiraan harga bahan baku ke depan memakai model LSTM/GRU, biar belanja tak kaget sama kenaikan harga."),
            ("KALKULATOR MODAL",
             "Hitung modal tiap porsi dan harga jual yang aman, langsung dari resep dan harga bahan."),
            ("LABA & RIWAYAT",
             "Simulasikan untung tiap menu dan simpan riwayatnya, biar keputusan usaha lebih terukur."),
        ]
        for col, (step, copy) in zip(land_cols, land_feats):
            with col.container(border=True):
                st.markdown(f'<div class="workflow-step">{step}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="workflow-copy">{copy}</div>', unsafe_allow_html=True)

        st.markdown('<div id="cara-kerja" class="landing-section-title">Cara kerja</div>', unsafe_allow_html=True)
        step_data = [
            ("Daftar dengan Google", "Buat akun gratis 7 hari, tanpa kartu kredit."),
            ("Isi resep & bahan", "Masukkan menu dan harga bahan yang biasa kamu beli."),
            ("Lihat prediksi & laba", "Dapatkan perkiraan harga dan hitungan untung tiap menu."),
        ]
        for idx, (step_title, step_copy) in enumerate(step_data, start=1):
            s1, s2 = st.columns([0.6, 5], vertical_alignment="center")
            with s1:
                st.markdown(f'<div class="landing-step-num">{idx}</div>', unsafe_allow_html=True)
            with s2:
                st.markdown(
                    f'<div class="landing-step"><strong>{step_title}</strong> — {step_copy}</div>',
                    unsafe_allow_html=True,
                )

        st.markdown('<div id="harga" class="landing-section-title">Paket & harga</div>', unsafe_allow_html=True)
        plan_cols = st.columns(len(_land_plans) or 1, gap="medium")
        for col, plan in zip(plan_cols, _land_plans):
            with col.container(border=True):
                st.markdown(f'<div class="workflow-step">{plan["name"]}</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div style="font-size:1.9rem;font-weight:850;color:var(--ink);letter-spacing:-.02em;">'
                    f'Rp{plan["price_idr"]:,}<span style="font-size:.9rem;font-weight:600;color:var(--muted);">/bulan</span></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="workflow-copy">{", ".join(plan.get("features", []))}</div>',
                    unsafe_allow_html=True,
                )
        st.markdown(
            '<div class="landing-lead" style="font-size:.92rem;">Paket diaktifkan setelah pembayaran manual (transfer BCA) '
            'diverifikasi pengelola. Daftar gratis dulu — tidak ada biaya sebelum trial berakhir.</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div id="pertanyaan" class="landing-section-title">Pertanyaan umum</div>', unsafe_allow_html=True)
        with st.expander("Berapa lama masa trial? Biayanya apa?"):
            st.write("Trial berlaku 7 hari sejak login pertama, gratis, tanpa kartu kredit. Setelah habis, kamu memilih paket untuk melanjutkan.")
        with st.expander("Bagaimana cara membayar setelah trial habis?"):
            st.write("Transfer ke rekening BCA PanganLaba (nomor tampil di halaman paket setelah login), lalu kirim bukti transfer ke WhatsApp pengelola. Akses aktif setelah diverifikasi.")
        with st.expander("Apakah data usaha saya aman dan terpisah?"):
            st.write("Data tiap akun tersimpan terpisah. Detail kebijakan privasi tersedia setelah login.")
        with st.expander("Bisakah akun dan data saya dihapus?"):
            st.write("Ya. Setelah masuk, buka Paket saya → Hapus akun & data.")

        st.markdown("<br>")
        chips = [
            "Bahasa Indonesia", "Rupiah, tanpa koma", "Cocok untuk pre-order",
            "QRIS statis", "Tanya PanganLaba", "Data tiap bisnis terpisah",
        ]
        st.markdown(
            '<div class="landing-chips">'
            + "".join(f'<span class="landing-chip">{chip}</span>' for chip in chips)
            + '</div>',
            unsafe_allow_html=True,
        )
        st.stop()

    user_email = str(st.user.get("email", "")).strip()
    user_name = str(st.user.get("name", "")).strip()
    if not st.user.get("email_verified", False):
        st.error("Google belum memverifikasi email akun ini. Gunakan akun Google dengan email terverifikasi.", icon=":material/mark_email_unread:")
        if st.button("Keluar", icon=":material/logout:"):
            st.logout()
        st.stop()
    account = start_or_get_account(
        ROOT / "data" / "app_users.sqlite3", user_email, user_name, trial_days=7
    )

    # Billing layer: extend access for paid subscriptions without changing UI.
    try:
        initialize_billing(ROOT / "data" / "app_users.sqlite3")
        account = check_account_access(ROOT / "data" / "app_users.sqlite3", account)
    except Exception as exc:
        st.warning(f"Lapisan langganan tidak tersedia: {exc}")

    # Panel admin: pemilik tetap bisa membuka verifikasi pembayaran walau trial berakhir.
    if user_email.lower() in _admin_emails() and st.session_state.get("show_admin", False):
        render_admin_panel(ROOT / "data" / "app_users.sqlite3", user_email)
        st.stop()

    if not account["access_allowed"]:
        st.title("Masa trial sudah berakhir", anchor=False)
        st.warning(
            "Masa trial berakhir. Pilih paket langganan untuk melanjutkan akses.",
            icon=":material/hourglass_disabled:",
        )
        render_subscription_offer()
        if user_email.lower() in _admin_emails():
            if st.button("Buka Panel Admin", key="paywall_open_admin", type="secondary"):
                st.session_state["show_admin"] = True
                st.rerun()
        if st.button("Keluar", icon=":material/logout:"):
            st.logout()
        st.stop()

    return account, user_email, user_name


try:
    account, user_email, user_name = _resolve_account()
    account["commodity_cap"] = _commodity_cap(account)
except Exception as exc:
    import traceback as _tb
    _tb_str = _tb.format_exc()
    with open(ROOT / "app_error.log", "w", encoding="utf-8") as _f:
        _f.write(_tb_str)
    st.title("Error", anchor=False)
    st.error(str(exc), icon=":material/error:")
    st.code(_tb_str, language="python")
    st.stop()

if account.get("status") == "trial" and account.get("days_remaining", 0) <= 3:
    st.warning(
        f"Masa trial tersisa {account['days_remaining']} hari. Pilih paket sekarang "
        "agar akses tidak terputus.",
        icon=":material/timer:",
    )

paths = project_paths(ROOT)
prices_file = paths["prices"]
weather_path = paths["weather"]
calendar_path = paths["calendar"]
metrics_path = paths["metrics"]
forecast_path = paths["forecast"]
has_results = has_model_results(paths)
overview_data, region, date_start, date_end = compute_overview(prices_file)

with st.sidebar:
    st.markdown("### PanganLaba")
    st.caption("Harga bahan · modal resep · laba menu")
    st.markdown("---")
    st.markdown("**Akun**")
    if local_preview:
        st.caption("Mode preview lokal · data laporan tersimpan di komputer ini")
    else:
        st.caption(user_email)
    if account["status"] == "trial":
        st.badge(f"Trial · {account['days_remaining']} hari tersisa", icon=":material/schedule:", color="orange")
    elif account["status"] == "active":
        st.badge(f"Langganan aktif · {account['days_remaining']} hari", icon=":material/verified:", color="green")
    if st.button("Paket saya", key="open_my_plan", icon=":material/card_membership:"):
        st.session_state["show_my_plan"] = True
        st.session_state["show_subscription"] = False
        st.rerun()
    if not local_preview:
        if st.button("Paket langganan", key="open_subscription", icon=":material/card_membership:"):
            st.session_state["show_subscription"] = True
            st.session_state["show_my_plan"] = False
            st.rerun()
        if user_email.lower() in _admin_emails():
            if st.button("Panel Admin", key="toggle_admin", icon=":material/admin_panel_settings:"):
                st.session_state["show_admin"] = not st.session_state.get("show_admin", False)
                st.session_state["show_subscription"] = False
                st.session_state["show_my_plan"] = False
                st.rerun()
        if st.button("Keluar", key="logout", icon=":material/logout:"):
            st.logout()
    st.markdown("---")
    st.markdown("**Wilayah data harga**")
    st.write(region)
    if not overview_data.empty:
        st.markdown("**Periode data**")
        st.write(f"{date_start} — {date_end}")
        st.markdown("**Komoditas tercatat**")
        st.write(f"{overview_data['commodity'].nunique()} jenis")
    st.markdown("---")
    st.caption("Sumber harga: workbook PIHPS yang dimasukkan ke proyek.")
    with st.expander("Ketentuan & Privasi", icon=":material/gavel:"):
        st.markdown(
            "**Data yang tersimpan** — email, nama tampilan, status trial/langganan, dan riwayat "
            "hasil perhitungan usaha kamu tersimpan pada server terpisah per akun.\n\n"
            "**Pembayaran** — dilakukan manual via transfer BCA PanganLaba; akses aktif setelah "
            "diverifikasi pengelola.\n\n"
            "**Penghapusan** — kamu bisa menghapus akun & data kapan saja lewat Paket saya → "
            "Hapus akun & data.\n\n"
            "**Penggunaan** — alat ini membantu perkiraan, bukan jaminan harga pasar aktual. "
            "Tidak menjual atau membagikan data pribadi ke pihak ketiga."
        )

if st.session_state.get("show_subscription", False):
    st.markdown('<div class="section-label">Langganan</div>', unsafe_allow_html=True)
    st.write("Trial gratis berlaku 7 hari sejak login pertama. Pilih paket berikut untuk melanjutkan setelah trial.")
    render_subscription_offer()
    if st.button("Kembali ke dashboard", key="close_subscription"):
        st.session_state["show_subscription"] = False
        st.rerun()

if st.session_state.get("show_my_plan", False):
    render_my_plan()
    if st.button("Kembali ke dashboard", key="close_my_plan"):
        st.session_state["show_my_plan"] = False
        st.rerun()

with st.container(key="project_hero"):
    hero_copy, hero_art = st.columns([1.15, .85], gap="large", vertical_alignment="center")
    with hero_copy:
        st.markdown('<div class="hero-label">PanganLaba · Asisten usaha kuliner · Kota Depok</div>', unsafe_allow_html=True)
        st.title("Modal menu lebih jelas. Belanja bahan lebih terukur.", anchor=False)
        st.markdown(
            '<div class="page-intro">Hitung modal dari resep, pantau perubahan harga bahan, dan lihat perkiraan pengaruhnya terhadap laba usahamu.</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="hero-actions"><a href="#kalkulator-laba-menu">Hitung modal menu</a>'
            '<a href="#ringkasan-usaha">Lihat saran belanja</a></div>',
            unsafe_allow_html=True,
        )
        st.caption("Harga PIHPS Depok · Model 7 hari pada data uji historis · Hitungan Rp dan kg")
    with hero_art:
        st.image(
            ROOT / "assets" / "umkm_header.jpg",
            width="stretch",
            alt="Ilustrasi UMKM dengan tiga kios pangan berwarna-warni",
        )
with st.expander("Rancangan judul tugas akhir", expanded=False):
    st.write("Prediksi Harga Komoditas Pangan Strategis dan Analisis Laba Menu untuk Mendukung Keputusan Belanja UMKM Kuliner Menggunakan LSTM dan GRU dengan Fitur Eksternal.")
    st.caption("Ini masih rancangan judul; pastikan cakupan dan redaksinya disetujui dosen pembimbing.")
if not overview_data.empty:
    with st.container(key="data_summary"):
        st.markdown('<div class="section-label">Ringkasan data</div>', unsafe_allow_html=True)
        stat_cols = st.columns(3, gap="medium")
        stat_cols[0].metric("Komoditas", f"{overview_data['commodity'].nunique()} jenis")
        stat_cols[1].metric("Observasi harga", f"{len(overview_data):,}")
        stat_cols[2].metric("Periode", f"{overview_data['date'].min().year}–{overview_data['date'].max().year}")
        st.caption(f"Sumber harga: PIHPS · Wilayah: {region} · Tanggal data: {date_start} sampai {date_end}.")

with st.container(key="workflow_cards"):
    flow_columns = st.columns(3, gap="medium")
    flow_items = [
        ("MODAL MENU", "Hitung biaya per porsi", "Masukkan bahan dan takaran resep untuk memperkirakan modal menu."),
        ("HARGA BAHAN", "Rencanakan belanja", "Bandingkan harga acuan dengan perkiraan harga komoditas pilihan."),
        ("HASIL USAHA", "Cek estimasi laba", "Masukkan harga jual dan jumlah porsi untuk melihat perkiraan laba bersih."),
    ]
    for column, (step, title, description) in zip(flow_columns, flow_items):
        with column.container(border=True):
            st.markdown(f'<div class="workflow-step">{step}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="workflow-title">{title}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="workflow-copy">{description}</div>', unsafe_allow_html=True)

with st.expander("Latih model dari data proyek", expanded=not has_results):
    st.write("Dataset PIHPS yang tersimpan di proyek dapat langsung dipakai untuk melatih model.")
    if weather_path.exists():
        st.success("Data cuaca historis Depok berbasis ERA5 (Open-Meteo; 1 Jan 2020–26 Okt 2026) tersedia dan dipakai sebagai fitur eksternal.")
    else:
        st.error("Data cuaca Depok belum ditemukan di data/raw/weather.csv.")
    if calendar_path.exists():
        st.success("Data kalender Indonesia (libur nasional, cuti bersama, akhir pekan, dan keterangan Idulfitri) tersedia dan dipakai pada paket fitur eksternal.")
    else:
        st.warning("Data kalender belum tersedia. Varian eksternal memakai data cuaca harian serta fitur siklus hari dan bulan.")
    epochs = st.number_input("Jumlah epoch", min_value=1, max_value=100, value=15, step=1)
    local_prices_path = ROOT / "data/raw/prices.csv"
    if local_prices_path.exists():
        st.markdown('<div class="status-card"><p>Data siap: harga PIHPS Kota Depok dan cuaca historis Depok tersedia di proyek.</p></div>', unsafe_allow_html=True)
        if st.button("Latih model dari data proyek", type="primary", key="train_local_pihps"):
            try:
                with st.spinner("Melatih model LSTM/GRU untuk data PIHPS. Proses dapat memerlukan beberapa menit."):
                    clean = load_and_merge(local_prices_path, weather_path, calendar_path)
                    is_demo = ("location" in clean.columns and clean["location"].astype(str)
                               .str.contains("DEMO", case=False, na=False).any())
                    source_label = "synthetic_demo" if is_demo else "depok_pihps_era5_daily_weather_calendar"
                    metrics_new = run_training(clean, ROOT, source_label, epochs=int(epochs))
                if metrics_new.empty:
                    st.error("Data belum cukup untuk membentuk model.")
                    st.stop()
                st.success(f"Selesai. {len(metrics_new)} kombinasi model dilatih.")
                st.rerun()
            except Exception as exc:
                st.error(f"Pelatihan gagal: {exc}")

with st.expander("Impor data PIHPS dari Excel (opsional)", expanded=False):
    st.caption("Gunakan untuk menambah atau mengganti harga PIHPS dan memasukkan data historis cuaca Depok. Data cuaca yang diunggah menjadi fitur eksternal model. Pembacaan file .xlsx memerlukan paket openpyxl pada environment Python Streamlit.")
    excel_files = st.file_uploader("File Excel PIHPS (.xlsx/.xlsm)", type=["xlsx", "xlsm"],
                                   accept_multiple_files=True, key="pihps_excel_upload")
    parsed_uploads, parse_errors = [], []
    for upload in excel_files or []:
        file_bytes = upload.getvalue()
        key_id = hashlib.sha1(upload.name.encode("utf-8") + file_bytes[:256]).hexdigest()[:12]
        try:
            info = inspect_pihps_excel(file_bytes)
            with st.container(border=True):
                st.caption(f"Tanggal: {info['date_start']:%d %b %Y} – {info['date_end']:%d %b %Y}.")
                options = info["rows"]
                default_row = next((i for i, item in enumerate(options)
                                    if item["label"].strip().casefold() in {"kota depok", "depok"}), 0)
                row_choice = st.selectbox("Wilayah/pasar", options,
                                          format_func=lambda item: item["display"], index=default_row,
                                          key=f"pihps_location_{key_id}")
                stem = Path(upload.name).stem
                suggested = "" if stem.lower().startswith("tabel harga") else stem.replace("_", " ")
                commodity = st.text_input("Nama komoditas", value=suggested,
                                          placeholder="Contoh: Beras", key=f"pihps_commodity_{key_id}")
            parsed_uploads.append({"name": upload.name, "bytes": file_bytes,
                                   "row_index": row_choice["row_index"],
                                   "location": row_choice["label"], "commodity": commodity.strip()})
        except Exception as exc:
            parse_errors.append(f"{upload.name}: {exc}")
            st.error(parse_errors[-1])
    weather_file = st.file_uploader("CSV cuaca (disarankan untuk fitur eksternal): date,rain_mm,temp_c", type=["csv"], key="weather_upload")
    calendar_file = st.file_uploader("CSV kalender Indonesia: date/tanggal, penanda libur/cuti/weekend; keterangan Idulfitri opsional", type=["csv"], key="calendar_upload")
    if st.button("Proses Excel dan latih model", key="upload_and_train"):
        if not parsed_uploads or parse_errors:
            st.error("Pilih workbook Excel PIHPS yang formatnya terbaca terlebih dahulu.")
        elif any(not item["commodity"] for item in parsed_uploads):
            st.error("Isi nama komoditas pada setiap workbook.")
        else:
            try:
                upload_dir = ROOT / "data/uploads"
                upload_dir.mkdir(parents=True, exist_ok=True)
                series = []
                for item in parsed_uploads:
                    digest = hashlib.sha256(item["bytes"]).hexdigest()[:16]
                    (upload_dir / f"pihps_{digest}.xlsx").write_bytes(item["bytes"])
                    series.append(extract_pihps_series(item["bytes"], item["row_index"],
                                                       item["commodity"], item["location"]))
                prices_path = upload_dir / "prices.csv"
                pd.concat(series, ignore_index=True).to_csv(prices_path, index=False)
                weather_path, calendar_path = upload_dir / "weather.csv", upload_dir / "calendar.csv"
                if weather_file is not None:
                    weather_path.write_bytes(weather_file.getvalue())
                elif weather_path.exists():
                    weather_path.unlink()
                if calendar_file is not None:
                    calendar_path.write_bytes(calendar_file.getvalue())
                elif calendar_path.exists():
                    calendar_path.unlink()
                with st.spinner("Membersihkan data dan melatih model LSTM/GRU."):
                    clean = load_and_merge(prices_path, weather_path, calendar_path)
                    locations_by_commodity = clean.groupby("commodity")["location"].nunique()
                    if (locations_by_commodity > 1).any():
                        raise ValueError("Pilih wilayah yang sama untuk seluruh workbook dalam komoditas yang sama.")
                    metrics_new = run_training(clean, ROOT, "uploaded_pihps_excel", epochs=int(epochs))
                if metrics_new.empty:
                    st.error("Data belum cukup untuk membentuk model.")
                    st.stop()
                st.success(f"Selesai. {len(metrics_new)} kombinasi model dilatih.")
                st.rerun()
            except Exception as exc:
                st.error(f"Data gagal diproses: {exc}")

if not has_results:
    st.info("Data harga Kota Depok sudah tersedia, tetapi hasil model tersimpan masih berasal dari data sebelum pembaruan. Buka **Latih model dari data proyek** lalu jalankan pelatihan untuk membuat pilihan LSTM/GRU dan hasil analisis Depok.")
    st.stop()

metrics, pred = load_metrics_forecast(paths)
if metrics.empty or pred.empty:
    st.warning("Belum ada hasil evaluasi model. Latih ulang model dari data proyek.")
    st.stop()

with st.sidebar:
    st.markdown("---")
    st.markdown("### Atur belanja")
    st.caption("Pilih bahan dan pola belanja usaha.")
    all_commodities = sorted(pred["commodity"].dropna().unique())
    commodity_cap = account.get("commodity_cap")
    available_commodities = all_commodities if commodity_cap is None else all_commodities[:commodity_cap]
    commodity = st.selectbox("Komoditas bahan baku", available_commodities)
    if commodity_cap is not None and len(all_commodities) > commodity_cap:
        st.caption(f"Paket Anda: {commodity_cap} dari {len(all_commodities)} komoditas (upgrade untuk lebih banyak).")
    subset = pred[pred["commodity"] == commodity]
    variants = sorted(subset.apply(
        lambda row: f"{row['model']} — {row['features']}", axis=1
    ).unique())
    variant = st.selectbox("Model prediksi", variants)
    model_name, feature_name = variant.split(" — ", 1)
    view = subset[(subset["model"] == model_name) & (subset["features"] == feature_name)]
    origins = sorted(view["origin_date"].dt.strftime("%Y-%m-%d").unique(), reverse=True)
    origin = st.selectbox("Tanggal data acuan", origins)
    restock_label = st.selectbox(
        "Jadwal belanja stok", ["Setiap 2 hari", "Seminggu sekali"],
        help="Pilih pola belanja yang paling mendekati kebiasaan usahamu."
    )
    st.caption(f"Prediksi: {model_name} · {feature_name}")
    restock_days = 2 if restock_label == "Setiap 2 hari" else 7

forecast, last, decision_forecast, rec = build_scenario(
    pred, commodity, model_name, feature_name, origin, restock_days
)

business_tab, research_tab = st.tabs(["Beranda usaha", "Hasil penelitian"])

with business_tab:
    st.markdown('<div id="ringkasan-usaha"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Ringkasan untuk usaha</div>', unsafe_allow_html=True)
    if "data_source" in metrics and not metrics.empty and metrics["data_source"].iloc[0] in {"depok_pihps", "depok_pihps_daily_weather", "depok_pihps_era5_daily_weather", "depok_pihps_era5_daily_weather_calendar", "uploaded_pihps_excel"}:
        st.caption(f"Evaluasi {commodity} · {region} · periode awal {origin}")
    else:
        st.caption("Pastikan sumber data pada hasil model sesuai dengan data penelitian yang digunakan.")
    summary_cols = st.columns(3, gap="medium")
    summary_cols[0].metric("Harga acuan (Rp/kg)", f"Rp{last:,.0f}")
    summary_cols[1].metric(f"Rata-rata prediksi {restock_days} hari (Rp/kg)", f"Rp{rec['forecast_mean']:,.0f}", f"{rec['expected_change_pct']:+.1f}%")
    summary_cols[2].metric("Saran sederhana", rec["recommendation"])

    st.markdown('<div id="kalkulator-laba-menu"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Modal dan laba menu</div>', unsafe_allow_html=True)
    st.caption("Hitung perkiraan modal resep dan keuntungan menu memakai harga acuan PIHPS serta prediksi model yang dipilih.")
    st.info(
        "Laba bersih di bawah ini dihitung dari resep, harga, penjualan, dan biaya yang Anda masukkan. Gunakan sebagai gambaran untuk merencanakan usaha; hasil aktual mengikuti kondisi penjualan dan biaya di lapangan.",
        icon=":material/info:",
    )
    st.caption("Skenario model mengikuti tanggal evaluasi yang dipilih; ini evaluasi historis, belum prakiraan setelah tanggal data terakhir.")
    recipe_defaults = pd.DataFrame([{
        "commodity": commodity,
        "grams_per_portion": 50.0,
        "actual_price_rp_per_kg": float("nan"),
    }])

    with st.container(border=True, key="profit_panel"):
        with st.form("menu_profit_calculator"):
            menu_cols = st.columns(3, gap="medium")
            menu_name = menu_cols[0].text_input("Nama menu", placeholder="Contoh: Gado-gado")
            selling_price = menu_cols[1].number_input(
                "Harga jual per porsi (Rp)", min_value=0, value=15000, step=1000
            )
            portions_sold = menu_cols[2].number_input(
                "Porsi terjual pada periode ini", min_value=0, value=20, step=1
            )

            with st.container(key="recipe_editor_card"):
                st.markdown(
                    '<div class="recipe-heading"><span class="recipe-tag">RESEP</span>'
                    '<span>Takaran bahan untuk satu porsi</span></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div class="recipe-help">Tambah satu bahan per baris. Gunakan gram; isi harga beli sendiri jika harga bahan tidak tersedia di PIHPS.</div>',
                    unsafe_allow_html=True,
                )
                recipe = st.data_editor(
                    recipe_defaults,
                    width="stretch",
                    height=250,
                    row_height=44,
                    hide_index=True,
                    num_rows="dynamic",
                    key="menu_profit_recipe",
                    alt="Tabel bahan dan takaran resep per porsi",
                    column_config={
                        "commodity": st.column_config.TextColumn(
                            "Nama bahan", required=True,
                            help="Samakan nama dengan komoditas PIHPS agar harga acuan terisi otomatis. Bahan lain bisa ditambahkan dengan harga beli manual.",
                        ),
                        "grams_per_portion": st.column_config.NumberColumn(
                            "Takaran / porsi (g)", min_value=0.0, step=10.0, format="localized",
                        ),
                        "actual_price_rp_per_kg": st.column_config.NumberColumn(
                            "Harga beli (Rp/kg)", min_value=0.0, step=500.0,
                            format="localized", help="Isi sesuai nota pemasok agar modal resep lebih akurat.",
                        ),
                    },
                )

            cost_cols = st.columns(2, gap="medium")
            other_cost_per_portion = cost_cols[0].number_input(
                "Biaya lain per porsi (Rp)", min_value=0, value=0, step=500,
                help="Contoh kemasan, gas, atau biaya variabel lain.",
            )
            fixed_cost = cost_cols[1].number_input(
                "Biaya tetap periode ini (Rp)", min_value=0, value=0, step=10000,
                help="Contoh alokasi sewa dan biaya tetap lain pada periode penjualan yang sama.",
            )
            sales_period = st.selectbox("Periode penjualan", ["Harian", "Mingguan", "Bulanan"])
            st.caption("Samakan periode jumlah porsi terjual dan biaya tetap yang dimasukkan.")
            save_profit_history = st.checkbox(
                "Simpan rincian resep dan hasil ke riwayat akun",
                value=True,
                help="Matikan jika sedang uji coba dan tidak ingin menyimpan resep serta harga pemasok.",
            )
            calculate_profit = st.form_submit_button("Hitung laba menu", type="primary", icon=":material/calculate:")

        if calculate_profit:
            recipe_rows = recipe.copy()
            recipe_rows["grams_per_portion"] = pd.to_numeric(
                recipe_rows["grams_per_portion"], errors="coerce"
            )
            recipe_rows["actual_price_rp_per_kg"] = pd.to_numeric(
                recipe_rows["actual_price_rp_per_kg"], errors="coerce"
            )
            recipe_rows["commodity"] = recipe_rows["commodity"].astype(str).str.strip()
            recipe_rows = recipe_rows.dropna(subset=["grams_per_portion"])
            recipe_rows = recipe_rows[recipe_rows["grams_per_portion"] > 0]

            if not menu_name.strip():
                st.error("Isi nama menu terlebih dahulu.")
            elif selling_price <= 0:
                st.error("Harga jual per porsi harus lebih dari Rp0.")
            elif portions_sold <= 0:
                st.error("Isi jumlah porsi terjual lebih dari 0.")
            elif recipe_rows.empty:
                st.error("Tambahkan minimal satu bahan dengan takaran lebih dari 0 gram.")
            else:
                report, missing_price, fallback_forecast = compute_profit_report(
                    recipe_rows, pred,
                    menu_name=menu_name, model_name=model_name, feature_name=feature_name,
                    origin=origin, restock_days=restock_days,
                    selling_price=selling_price, portions_sold=portions_sold,
                    other_cost_per_portion=other_cost_per_portion, fixed_cost=fixed_cost,
                    sales_period=sales_period,
                )
                if missing_price:
                    st.error(
                        "Harga belum ditemukan untuk: " + ", ".join(sorted(set(missing_price)))
                        + ". Isi harga aktual per kg pada tabel bahan."
                    )
                else:
                    current_ingredient_cost = report["ingredient_cost_per_portion"]
                    predicted_ingredient_cost = report["predicted_ingredient_cost_per_portion"]
                    revenue = report["revenue"]
                    current_gross_profit = report["gross_profit"]
                    current_net_profit = report["net_profit"]
                    predicted_net_profit = report["predicted_net_profit"]
                    break_even = report["break_even_portions"]
                    break_even_label = f"{break_even:,} porsi" if break_even else "Belum tercapai"
                    if save_profit_history:
                        try:
                            saved_id = save_profit_record(
                                ROOT / "data" / "app_users.sqlite3", user_email, report
                            )
                            st.success(f"Catatan #{saved_id} tersimpan di riwayat akun ini.")
                        except Exception as exc:
                            st.error(f"Hitungan berhasil, tetapi catatan belum tersimpan: {exc}")
                    else:
                        st.caption("Hitungan ini tidak disimpan ke riwayat akun.")

                    st.markdown(f"#### Hasil untuk {menu_name.strip()}")
                    result_cols = st.columns(3, gap="medium")
                    result_cols[0].metric("Modal bahan per porsi", f"Rp{current_ingredient_cost:,.0f}")
                    result_cols[1].metric("Omzet periode ini", f"Rp{revenue:,.0f}")
                    result_cols[2].metric("Laba bersih estimasi pada harga acuan", f"Rp{current_net_profit:,.0f}")
                    forecast_cols = st.columns(3, gap="medium")
                    forecast_cols[0].metric("Modal bahan/porsi pada harga prediksi", f"Rp{predicted_ingredient_cost:,.0f}")
                    forecast_cols[1].metric(
                        "Laba bersih pada skenario prediksi", f"Rp{predicted_net_profit:,.0f}",
                        f"Rp{predicted_net_profit - current_net_profit:+,.0f} vs harga acuan",
                    )
                    current_margin = current_net_profit / revenue * 100 if revenue else 0.0
                    forecast_cols[2].metric("Margin bersih estimasi", f"{current_margin:.1f}%")
                    st.caption(
                        f"Laba kotor saat ini Rp{current_gross_profit:,.0f} · "
                        f"perkiraan titik impas {break_even_label} · "
                        f"{int(portions_sold):,} porsi ({sales_period.lower()})."
                    )
                    if current_net_profit > 0:
                        st.success(f"Estimasi menu **{menu_name.strip()}** untung Rp{current_net_profit:,.0f} pada periode ini.")
                    elif current_net_profit < 0:
                        st.error(f"Estimasi menu **{menu_name.strip()}** rugi Rp{abs(current_net_profit):,.0f} pada periode ini.")
                    else:
                        st.warning(f"Estimasi menu **{menu_name.strip()}** impas pada periode ini.")
                    if fallback_forecast:
                        st.warning(
                            "Prediksi belum tersedia untuk " + ", ".join(sorted(set(fallback_forecast)))
                            + "; skenario bahan tersebut memakai harga acuan saat ini."
                        )
                    st.info(
                        "Gunakan hasil ini sebagai gambaran untuk merencanakan usaha. Hasil aktual mengikuti kondisi "
                        "penjualan dan biaya di lapangan, termasuk harga pemasok, stok, serta bahan terbuang.",
                        icon=":material/info:",
                    )

    profit_history = get_profit_history(ROOT / "data" / "app_users.sqlite3", user_email, limit=100)
    st.markdown("#### Riwayat laba-rugi menu")
    if profit_history:
        history_view = pd.DataFrame(profit_history)
        history_view["Waktu catat"] = pd.to_datetime(history_view["created_at"], utc=True).dt.tz_convert("Asia/Jakarta").dt.strftime("%d %b %Y %H:%M")
        history_view = history_view.rename(columns={
            "menu_name": "Menu", "period_label": "Periode", "portions_sold": "Porsi terjual",
            "selling_price": "Harga jual/porsi (Rp)", "revenue": "Omzet (Rp)",
            "net_profit": "Laba bersih estimasi (Rp)",
            "predicted_net_profit": "Laba pada skenario prediksi (Rp)",
            "net_margin_pct": "Margin bersih (%)", "reference_date": "Tanggal acuan",
        })
        history_table = history_view[["Waktu catat", "Menu", "Periode", "Porsi terjual", "Harga jual/porsi (Rp)",
                                      "Omzet (Rp)", "Laba bersih estimasi (Rp)", "Laba pada skenario prediksi (Rp)",
                                      "Margin bersih (%)", "Tanggal acuan"]]
        st.dataframe(
            styled_table(history_table), width="stretch", hide_index=True,
            alt="Riwayat catatan laba menu milik akun ini",
        )
        csv_history = history_view.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "Unduh riwayat laba-rugi CSV", data=csv_history,
            file_name="riwayat_laba_menu.csv", mime="text/csv",
            icon=":material/download:",
        )
    else:
        st.caption("Belum ada catatan. Hitung dan simpan penjualan menu untuk mulai membuat riwayat.")

    with st.container(key="simulation_panel"):
        st.markdown("#### Simulasi pembelian bahan baku")
        st.caption(f"Bandingkan belanja rutin setiap {restock_days} hari dengan strategi menunda pembelian. Masukkan jumlah kg dan batas penundaan; biaya dihitung dari harga aktual pada tanggal pembelian di data uji.")
        sim_controls = st.columns([1, 1, 2], gap="medium")
        quantity = sim_controls[0].number_input("Jumlah kg per transaksi", min_value=0.1, value=1.0, step=1.0,
                                                 help="Harga PIHPS pada project ini dinyatakan dalam rupiah per kilogram (Rp/kg).")
        max_wait_allowed = min(3, restock_days - 1)
        max_wait = sim_controls[1].slider("Maksimal tunda (hari)", min_value=0,
                                          max_value=max_wait_allowed,
                                          value=min(2, max_wait_allowed))
        simulated = simulate_purchase_policy(view, quantity_kg=quantity,
                                             threshold=0.05, max_wait_days=max_wait,
                                             cycle_days=restock_days)
        if simulated.empty:
            st.info(f"Belum ada siklus uji {restock_days} hari yang lengkap untuk disimulasikan.")
        else:
            baseline_total = float(simulated["baseline_cost_rp"].sum())
            policy_total = float(simulated["policy_cost_rp"].sum())
            savings = baseline_total - policy_total
            savings_pct = savings / baseline_total * 100 if baseline_total else 0.0
            deferred = int((simulated["wait_days"] > 0).sum())
            with st.container(key="simulation_metrics"):
                sim_metrics = st.columns(4, gap="medium")
                sim_metrics[0].metric("Belanja rutin", f"Rp{baseline_total:,.0f}")
                sim_metrics[1].metric("Belanja strategi", f"Rp{policy_total:,.0f}")
                sim_metrics[2].metric("Selisih simulasi", f"Rp{savings:,.0f}", f"{savings_pct:+.2f}% vs rutin")
                sim_metrics[3].metric("Transaksi ditunda", f"{deferred} dari {len(simulated)} siklus")
            sim_display = simulated.rename(columns={
                "cycle": "Siklus", "baseline_buy_date": "Tanggal rutin",
                "policy_buy_date": "Tanggal strategi", "wait_days": "Hari ditunda",
                "baseline_unit_price_rp_per_kg": "Harga rutin (Rp/kg)", "policy_unit_price_rp_per_kg": "Harga strategi (Rp/kg)",
                "quantity_kg": "Jumlah beli (kg)", "baseline_cost_rp": "Belanja rutin (Rp)",
                "policy_cost_rp": "Belanja strategi (Rp)", "savings_rp": "Selisih biaya (Rp)",
                "advice_on_purchase_day": "Saran pada hari beli",
            })
            for date_column in ["Tanggal rutin", "Tanggal strategi"]:
                sim_display[date_column] = pd.to_datetime(
                    sim_display[date_column], errors="coerce"
                ).dt.strftime("%d %b %Y")
            sim_table = sim_display[["Siklus", "Tanggal rutin", "Tanggal strategi",
                                    "Jumlah beli (kg)", "Belanja rutin (Rp)", "Belanja strategi (Rp)",
                                    "Selisih biaya (Rp)"]]
            st.dataframe(styled_table(sim_table), width="stretch", hide_index=True)
            st.download_button("Unduh rincian simulasi CSV",
                               data=simulated.to_csv(index=False).encode("utf-8-sig"),
                               file_name=f"simulasi_{commodity.lower().replace(' ', '_')}_{model_name.lower()}.csv",
                               mime="text/csv", width="content")
            st.caption("Hasil ini simulasi retrospektif pada data uji, bukan bukti penghematan nyata. Belum memasukkan stok, biaya simpan, perubahan kebutuhan, kedaluwarsa, dan biaya transaksi; volume dihitung dalam kg dan harga dalam Rp/kg.")


    with st.expander("Catat umpan balik uji coba UMKM", expanded=False):
        st.caption(
            "Gunakan setelah pemilik atau pekerja UMKM mencoba sendiri. Catatan hanya menyimpan kode sesi dan masukan, "
            "bukan nama, kontak, resep, atau harga pemasok. Minta persetujuan sebelum mencatat."
        )
        st.write(
            "Minta peserta memakai satu menu yang benar-benar dijual, memasukkan takaran resep serta harga beli dari "
            "nota/pemasok, lalu mencari harga acuan, prediksi, dan saran belanja. Amati tanpa mengarahkan; minta izin "
            "sebelum membantu."
        )
        with st.form("umkm_field_test_feedback"):
            feedback_cols = st.columns(3, gap="medium")
            session_code = feedback_cols[0].text_input(
                "Kode sesi anonim", placeholder="UMKM-01", help="Jangan isi nama orang, usaha, atau nomor kontak."
            )
            business_type = feedback_cols[1].selectbox(
                "Jenis usaha", ["Warung makan", "Pecel lele", "Gado-gado", "Katering", "Jajanan", "Lainnya"]
            )
            participant_role = feedback_cols[2].selectbox("Peran peserta", ["Pemilik", "Pengelola", "Pekerja"])
            used_real_data = st.checkbox(
                "Peserta mencoba dengan resep dan biaya bahan yang benar-benar dipakai",
                value=False,
            )
            task_cols = st.columns(2, gap="medium")
            calculator_task = task_cols[0].selectbox(
                "Tugas: hitung modal dan estimasi laba menu",
                ["Berhasil sendiri", "Berhasil setelah dibantu", "Belum berhasil"],
            )
            dashboard_task = task_cols[1].selectbox(
                "Tugas: temukan harga, prediksi, dan saran belanja",
                ["Berhasil sendiri", "Berhasil setelah dibantu", "Belum berhasil"],
            )
            timing_cols = st.columns(2, gap="medium")
            calculator_minutes = timing_cols[0].number_input(
                "Waktu kalkulator (menit)", min_value=0, max_value=120, value=0, step=1
            )
            dashboard_minutes = timing_cols[1].number_input(
                "Waktu dashboard (menit)", min_value=0, max_value=120, value=0, step=1
            )
            rating_cols = st.columns(3, gap="medium")
            ease_rating = rating_cols[0].select_slider("Kemudahan penggunaan (1 sulit–5 mudah)", options=[1, 2, 3, 4, 5], value=3)
            clarity_rating = rating_cols[1].select_slider("Kejelasan hasil (1–5)", options=[1, 2, 3, 4, 5], value=3)
            usefulness_rating = rating_cols[2].select_slider("Manfaat untuk keputusan usaha (1–5)", options=[1, 2, 3, 4, 5], value=3)
            manual_match = st.selectbox(
                "Dibanding hitungan manual peserta, hasil modal resep",
                ["Belum dibandingkan", "Sesuai", "Ada selisih kecil", "Ada selisih besar"],
            )
            would_use = st.selectbox("Apakah peserta ingin memakai lagi?", ["Ya", "Mungkin", "Tidak"])
            confusing = st.text_area("Bagian yang membingungkan atau menghambat", max_chars=1000)
            requested_change = st.text_area("Perubahan atau fitur yang diminta peserta", max_chars=1000)
            consent = st.checkbox("Peserta setuju umpan balik anonim ini dicatat untuk evaluasi skripsi.")
            submitted_feedback = st.form_submit_button("Simpan umpan balik sesi", type="primary")
        if submitted_feedback:
            if not consent:
                st.error("Minta persetujuan peserta sebelum menyimpan umpan balik.")
            elif not session_code.strip():
                st.error("Isi kode sesi anonim, bukan nama atau kontak.")
            else:
                feedback_record = {
                    "timestamp_local": pd.Timestamp.now(tz="Asia/Jakarta").isoformat(timespec="seconds"),
                    "session_code": session_code.strip(),
                    "business_type": business_type,
                    "participant_role": participant_role,
                    "used_real_recipe_and_costs": bool(used_real_data),
                    "calculator_task": calculator_task,
                    "dashboard_task": dashboard_task,
                    "calculator_minutes": int(calculator_minutes),
                    "dashboard_minutes": int(dashboard_minutes),
                    "ease_rating_1_5": int(ease_rating),
                    "clarity_rating_1_5": int(clarity_rating),
                    "usefulness_rating_1_5": int(usefulness_rating),
                    "manual_calculation_match": manual_match,
                    "would_use_again": would_use,
                    "confusing_or_blocking": confusing.strip(),
                    "requested_change": requested_change.strip(),
                    "consent_anonymous_feedback": True,
                }
                try:
                    append_umkm_feedback(ROOT / "data" / "umkm_user_tests" / "feedback.csv", feedback_record)
                    st.success("Umpan balik anonim tersimpan di data/umkm_user_tests/feedback.csv.")
                except Exception as exc:
                    st.error(f"Umpan balik belum tersimpan: {exc}")

with research_tab:
    st.markdown("### Hasil evaluasi pada data uji")
    ev = evaluate_model_results(metrics)
    st.caption(f"Ringkasan dihitung dari hasil uji pada {ev['commodity_count']} komoditas di Kota Depok.")
    eval_cols = st.columns(4, gap="medium")
    eval_cols[0].metric("Model median terbaik", f"{ev['best_score']['model']} · {ev['best_score']['features']}")
    eval_cols[1].metric("MAE median", f"Rp{ev['best_score']['MAE']:,.0f}/kg")
    eval_cols[2].metric("RMSE median", f"Rp{ev['best_score']['RMSE']:,.0f}/kg")
    eval_cols[3].metric("MAPE median", f"{ev['best_score']['MAPE']:.2f}%")
    st.info(
        f"Pada data uji saat ini, fitur eksternal menurunkan MAE pada **{ev['external_wins']} dari {ev['paired_count']}** perbandingan komoditas dan model. "
        "Artinya, manfaat fitur eksternal perlu dibahas berdasarkan hasil pengujian; belum semua komoditas mendapat prediksi yang lebih akurat.",
    )
    st.markdown("#### Harga aktual dan hasil model")
    st.caption("Grafik menunjukkan perbandingan aktual dan prediksi pada bagian evaluasi waktu yang dipilih.")
    fig, ax = plt.subplots(figsize=(11, 4.6))
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")
    ax.plot(forecast["target_date"], forecast["actual"], marker="o", markersize=5, linewidth=2.5,
            color="#594236", label="Harga aktual")
    ax.plot(forecast["target_date"], forecast["predicted"], marker="o", markersize=5, linewidth=2.5,
            color="#c64d2c", label="Prediksi model")
    ax.set_title(f"{commodity} · periode evaluasi {origin}", loc="left", color="#2d2722", fontsize=13, pad=14)
    ax.set_ylabel("Harga per kg (Rp)")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"Rp{value:,.0f}"))
    ax.grid(axis="y", color="#eee5da", linewidth=.8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#dfd3c6")
    ax.spines["bottom"].set_color("#dfd3c6")
    ax.legend(frameon=False, ncol=2, loc="upper left")
    fig.autofmt_xdate()
    st.pyplot(fig, width="stretch", alt="Grafik harga aktual dan prediksi model untuk periode evaluasi")

    st.markdown("#### Perbandingan model")
    commodity_metrics, chart_values = model_comparison_for(metrics, commodity)
    if all(len(values) == 2 and values.notna().all() for values in chart_values):
        fig_mae, ax_mae = plt.subplots(figsize=(9, 4.1))
        fig_mae.patch.set_facecolor("#ffffff")
        ax_mae.set_facecolor("#ffffff")
        positions = [0, 1]
        bar_width = .32
        bars_price = ax_mae.bar([x - bar_width / 2 for x in positions], chart_values[0].to_numpy(),
                                width=bar_width, color="#594236", label="Harga saja")
        bars_external = ax_mae.bar([x + bar_width / 2 for x in positions], chart_values[1].to_numpy(),
                                   width=bar_width, color="#e9a33b", label="Harga + fitur eksternal")
        max_error = max(max(chart_values[0]), max(chart_values[1]))
        ax_mae.set_ylim(0, max_error * 1.2)
        for bar in [*bars_price, *bars_external]:
            height = bar.get_height()
            ax_mae.annotate(f"Rp{height:,.0f}", (bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontsize=8)
        ax_mae.set_xticks(positions, ["LSTM", "GRU"])
        ax_mae.set_ylabel("MAE (Rp/kg) · makin rendah makin baik")
        ax_mae.set_title(f"Kesalahan prediksi {commodity}", loc="left", color="#2d2722", fontsize=12, pad=12)
        ax_mae.grid(axis="y", color="#eee5da", linewidth=.8)
        ax_mae.set_axisbelow(True)
        ax_mae.spines["top"].set_visible(False)
        ax_mae.spines["right"].set_visible(False)
        ax_mae.spines["left"].set_color("#dfd3c6")
        ax_mae.spines["bottom"].set_color("#dfd3c6")
        ax_mae.legend(frameon=False, ncol=2, loc="upper left")
        fig_mae.tight_layout()
        st.pyplot(fig_mae, width="stretch", alt=f"Perbandingan MAE model LSTM dan GRU untuk {commodity}")
        st.caption("Batang hijau menunjukkan model dengan harga saja; batang jingga menunjukkan model dengan tambahan cuaca dan kalender. Yang lebih rendah memiliki MAE lebih kecil.")
    commodity_metrics_display = commodity_metrics.rename(columns={
        "MAE": "MAE (Rp/kg)", "RMSE": "RMSE (Rp/kg)", "MAPE": "MAPE (%)",
        "features": "Fitur", "model": "Model", "commodity": "Komoditas",
        "train_target_end": "Akhir target latih", "test_target_start": "Awal target uji",
        "test_target_end": "Akhir target uji", "n_train_sequences": "Urutan latih",
        "n_test_sequences": "Urutan uji", "epochs_trained": "Epoch aktual",
    })
    metric_columns = ["Komoditas", "Model", "Fitur", "MAE (Rp/kg)", "RMSE (Rp/kg)", "MAPE (%)"]
    st.dataframe(styled_table(commodity_metrics_display[metric_columns].round(2)), width="stretch", hide_index=True)
    st.markdown("#### Ringkasan lintas komoditas")
    summary = cross_commodity_summary(metrics)
    st.dataframe(styled_table(summary.round(2)), width="stretch", hide_index=True)
    st.caption("Saran beli/tunda memakai ambang ±5%. Pertimbangkan stok, kebutuhan, mutu, cuaca, pasokan, dan biaya simpan sebelum mengambil keputusan.")

    st.markdown("#### Catatan hasil")
    st.markdown("""
    - Data dibagi berdasarkan waktu: 80% bagian awal untuk pelatihan dan 20% bagian akhir untuk pengujian.
    - Fitur cuaca dan kalender diuji sebagai satu paket, jadi pengaruh masing-masing fitur belum dipisahkan.
    - Simulasi memakai data historis dan belum memperhitungkan stok atau biaya penyimpanan.
    """)

    with st.expander("Tentang sumber data dan metode"):
        st.write(f"Data harga berasal dari workbook PIHPS. Wilayah yang dipakai saat ini adalah **{region}**; nama komoditas diambil dari nama file dan tanggal mengikuti isi workbook.")
        st.write("Eksperimen membandingkan LSTM dan GRU, masing-masing dengan fitur harga saja dan paket fitur eksternal: cuaca harian, kalender libur/cuti/akhir pekan serta keterangan tanggal Idulfitri, dan siklus hari/bulan. Paket eksternal ini menggabungkan beberapa kelompok fitur. Kalender tidak memiliki penanda periode Ramadan atau rentang hari menjelang Idulfitri; model menggunakan indikator kalender dari jendela historis 30 hari. Data dibagi kronologis (80% pelatihan, 20% pengujian), lalu dinilai menggunakan MAE, RMSE, dan MAPE.")
        st.write("Fitur cuaca aktif diunduh langsung dari Open-Meteo Historical Weather API dengan model ERA5. Variabelnya meliputi suhu rata-rata/maksimum/minimum, curah hujan, angin maksimum, dan radiasi matahari. Koordinat grid hasil API dan satuan dicatat di data/processed/weather_openmeteo_era5_metadata.json. Ini data reanalisis grid, bukan observasi stasiun BMKG.")
        st.write("Prakiraan harga membantu mempertimbangkan waktu pembelian, tetapi belum menghitung jumlah kebutuhan bahan, stok, perubahan pasokan, distribusi, kualitas, atau kondisi pasar setempat.")

    with st.expander("Data yang dibutuhkan untuk penelitian"):
        st.markdown("**Data utama — wajib**")
        st.markdown("- Harga harian PIHPS untuk tiap komoditas, dengan tanggal, nama komoditas, harga, wilayah/pasar yang konsisten, dan satuan yang jelas. Format CSV: `date,commodity,price,location`.")
        st.markdown("**Data eksternal — diperlukan untuk menguji judul penelitian**")
        st.markdown("- Cuaca historis ERA5 (Open-Meteo): `data/raw/weather.csv` berisi suhu rata-rata/maksimum/minimum, hujan, angin maksimum, dan radiasi untuk 1 Jan 2020–26 Okt 2026. Prakiraan BMKG tidak digunakan dalam model.")
        st.markdown("- Kalender Indonesia: `data/raw/calendar.csv` memakai tanggal, libur nasional, cuti bersama, akhir pekan, dan penanda tanggal yang keterangannya menyebut Idulfitri. Dataset ini belum menandai periode Ramadan atau hari-hari menjelang Idulfitri. Hari dalam minggu dan bulan dihitung otomatis.")
        st.markdown("**Disarankan**")
        st.markdown("- Riwayat sepanjang mungkin dan konsisten—idealnya beberapa tahun—untuk setiap komoditas, plus catatan sumber, tanggal pengunduhan, wilayah/pasar, dan satuan harga.")
        st.caption("Data penjualan resep dan stok outlet tidak wajib untuk judul ini karena sistem memprediksi harga pasar dan memberi pertimbangan waktu pembelian, bukan menghitung jumlah restock.")
