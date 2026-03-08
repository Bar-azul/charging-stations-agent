from __future__ import annotations

import sys

try:
    __import__("pysqlite3")
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
except Exception:
    pass

from pathlib import Path
import streamlit as st

from agent_logic import get_filter_options, search_agent
from Utils.ui_utils import (
    jump_page_to_top,
    render_chat_history,
    render_result_card,
    build_folium_map,
    safe_text,
)

# =========================
# Config
# =========================
APP_DIR = Path(__file__).parent
LOGO_PATH = APP_DIR / "paz_logo.png"

# =========================
# Page Setup
# =========================
st.set_page_config(
    page_title="תחנות טעינה - סוכן ניתוח מתחרים",
    page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "⚡",
    layout="wide",
)

# =========================
# Enhanced Global CSS
# =========================
st.markdown(
    """
<style>
html, body, [class*="css"], [data-testid="stAppViewContainer"], .main {
    direction: rtl;
    text-align: right;
    overflow-x: hidden !important;
}

.block-container {
    padding-top: 0.5rem;
    padding-bottom: 2rem;
    max-width: 1480px;
}

/* Theme */
:root {
    --paz-blue-1: #061632;
    --paz-blue-2: #0A234F;
    --paz-blue-3: #143A7B;
    --paz-blue-4: #2459A8;
    --paz-yellow: #F6B300;
    --paz-yellow-soft: #FFF7E2;
    --paz-bg-soft: #F4F7FB;
    --paz-bg-card: #FFFFFF;
    --paz-border: #DCE3EE;
    --paz-text: #14213D;
    --paz-muted: #667085;
    --paz-white: #FFFFFF;
    --shadow-soft: 0 10px 30px rgba(10, 35, 79, 0.08);
    --shadow-card: 0 8px 24px rgba(20, 33, 61, 0.06);
}

/* App background */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #F8FAFD 0%, #F2F6FB 100%);
}

/* Sidebar */
[data-testid="stSidebar"] {
    z-index: 1000;
}
.sidebar-logo-wrap {
    display: flex;
    justify-content: center;
    margin-bottom: 10px;
}

/* Section titles */
.section-title {
    color: var(--paz-blue-2);
    font-size: 2rem;
    font-weight: 900;
    margin-top: 0.7rem;
    margin-bottom: 0.9rem;
    letter-spacing: -0.02em;
}

.result-title {
    color: var(--paz-blue-2);
}

/* Fixed header */
.fixed-top-shell {
    position: fixed;
    top: 0.55rem;
    left: 0;
    right: 0;
    z-index: 999;
    pointer-events: none;
    padding-left: 1rem;
    padding-right: 1rem;
    box-sizing: border-box;
}

.fixed-top-inner {
    width: 100%;
    max-width: 1480px;
    margin: 0 auto;
    pointer-events: auto;
}

.fixed-header-panel {
    border: 1px solid rgba(10,35,79,0.08);
    border-radius: 26px;
    overflow: hidden;
    background: rgba(255,255,255,0.92);
    backdrop-filter: blur(10px);
    box-shadow: var(--shadow-soft);
}

.header-spacer {
    height: 22px;
}

/* Hero */
.hero-shell {
    border-radius: 26px;
    overflow: hidden;
    box-shadow: var(--shadow-soft);
    border: 1px solid rgba(255,255,255,0.12);
}

.hero-box {
    padding: 24px 28px 22px 28px;
    background:
        radial-gradient(circle at 15% 20%, rgba(246,179,0,0.22) 0%, rgba(246,179,0,0) 25%),
        radial-gradient(circle at 85% 20%, rgba(255,255,255,0.14) 0%, rgba(255,255,255,0) 28%),
        linear-gradient(135deg, #07162f 0%, #0A234F 52%, #18438d 100%);
    position: relative;
    overflow: hidden;
}

.hero-box::after {
    content: "";
    position: absolute;
    inset: auto -40px -60px auto;
    width: 240px;
    height: 240px;
    background: radial-gradient(circle, rgba(255,255,255,0.12) 0%, rgba(255,255,255,0) 72%);
    pointer-events: none;
}

.hero-title {
    color: white;
    font-size: 2.35rem;
    font-weight: 900;
    line-height: 1.05;
    margin-bottom: 10px;
    letter-spacing: -0.03em;
}

.hero-subtitle {
    color: #E9F0FA;
    font-size: 1.05rem;
    line-height: 1.8;
    max-width: 980px;
}

.hero-badges {
    margin-top: 14px;
}

.hero-badge {
    display: inline-block;
    margin-left: 8px;
    margin-bottom: 8px;
    padding: 6px 12px;
    border-radius: 999px;
    background: rgba(255,255,255,0.12);
    color: #F6F8FC;
    border: 1px solid rgba(255,255,255,0.15);
    font-size: 0.82rem;
    font-weight: 700;
}

/* Search panel */
.search-panel {
    margin-top: 14px;
    background: linear-gradient(180deg, #FFFFFF 0%, #FBFCFE 100%);
    border: 1px solid var(--paz-border);
    border-radius: 22px;
    padding: 18px 18px 18px 18px;
    box-shadow: var(--shadow-card);
}

.search-title {
    color: var(--paz-blue-2);
    font-weight: 900;
    font-size: 1.08rem;
    margin-bottom: 6px;
}

.quick-caption {
    color: var(--paz-muted);
    font-size: 0.95rem;
    margin-bottom: 0.7rem;
}

/* KPI cards */
.kpi-card {
    background: linear-gradient(180deg, #FFFFFF 0%, #F9FBFE 100%);
    border: 1px solid var(--paz-border);
    border-radius: 20px;
    padding: 14px 16px;
    box-shadow: var(--shadow-card);
}

.kpi-label {
    color: var(--paz-muted);
    font-size: 0.9rem;
    margin-bottom: 6px;
    font-weight: 700;
}

.kpi-value {
    color: var(--paz-blue-2);
    font-size: 1.65rem;
    font-weight: 900;
    line-height: 1.1;
}

/* Result / map wrappers */
.panel-card {
    background: linear-gradient(180deg, #FFFFFF 0%, #FBFCFE 100%);
    border: 1px solid var(--paz-border);
    border-radius: 22px;
    padding: 12px;
    box-shadow: var(--shadow-card);
}

/* Buttons */
button[kind="primary"] {
    background: linear-gradient(
        90deg,
        var(--paz-blue-2) 0%,
        var(--paz-blue-3) 70%,
        var(--paz-blue-4) 100%
    ) !important;
    border: none !important;
    border-radius: 14px !important;
    color: white !important;
    font-weight: 800 !important;
    min-height: 50px !important;
    box-shadow: 0 8px 18px rgba(10,35,79,0.20) !important;
}

button[kind="primary"]:hover {
    filter: brightness(1.04);
}

button[kind="secondary"] {
    border-radius: 12px !important;
    border: 1px solid var(--paz-border) !important;
}

/* Inputs */
div[data-testid="stTextInput"] input {
    border-radius: 14px !important;
    border: 1px solid var(--paz-border) !important;
    background: #FBFCFE !important;
    min-height: 48px !important;
}

div[data-testid="stNumberInput"] input {
    border-radius: 14px !important;
    border: 1px solid var(--paz-border) !important;
    background: #FBFCFE !important;
    min-height: 48px !important;
}

div[data-testid="stSelectbox"] > div {
    border-radius: 14px !important;
}

div[data-testid="stMetric"] {
    background: white;
    border: 1px solid var(--paz-border);
    border-radius: 18px;
    padding: 10px 8px;
    box-shadow: 0 4px 12px rgba(20,33,61,0.04);
}

div[data-testid="stToggle"] label {
    font-weight: 700 !important;
    color: var(--paz-blue-2) !important;
}

div[data-testid="stToggle"] div[role="switch"][aria-checked="true"] {
    background-color: var(--paz-yellow) !important;
    border-color: var(--paz-yellow) !important;
}

div[data-testid="stToggle"] div[role="switch"][aria-checked="false"] {
    background-color: #D7DEE9 !important;
    border-color: #D7DEE9 !important;
}

/* Mobile fixes */
@media (max-width: 768px) {
    .fixed-top-shell {
        position: static;
        padding-left: 0.5rem;
        padding-right: 0.5rem;
    }

    .fixed-top-inner {
        max-width: 100%;
    }

    .header-spacer {
        display: none;
    }

    .hero-box {
        padding: 18px 18px 18px 18px;
    }

    .hero-title {
        font-size: 1.95rem !important;
        line-height: 1.15 !important;
        word-break: break-word;
    }

    .hero-subtitle {
        font-size: 0.96rem !important;
        line-height: 1.6 !important;
    }

    .search-panel {
        padding: 14px;
        border-radius: 18px;
    }

    .section-title {
        font-size: 1.7rem;
    }

    .kpi-value {
        font-size: 1.35rem;
    }
}

</style>
""",
    unsafe_allow_html=True,
)

# =========================
# Session State
# =========================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_results" not in st.session_state:
    st.session_state.last_results = []

if "last_query" not in st.session_state:
    st.session_state.last_query = ""

if "query_input" not in st.session_state:
    st.session_state.query_input = "איפה יש עמדת DC מהירה בבאר שבע?"

if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

if "assistant_scroll_to_last_user" not in st.session_state:
    st.session_state.assistant_scroll_to_last_user = False

if "sidebar_jump_to_top" not in st.session_state:
    st.session_state.sidebar_jump_to_top = False

if st.session_state.pending_query is not None:
    st.session_state.query_input = st.session_state.pending_query
    st.session_state.pending_query = None

# =========================
# Filter Options
# =========================
options = get_filter_options()
city_options = options["city_options"]
company_options = options["company_options"]
current_type_options = options["current_type_options"]

# =========================
# Sidebar
# =========================
with st.sidebar:
    if LOGO_PATH.exists():
        st.markdown('<div class="sidebar-logo-wrap">', unsafe_allow_html=True)
        st.image(str(LOGO_PATH), width=76)
        st.markdown("</div>", unsafe_allow_html=True)

    st.header("פילטרים")

    city_filter = st.selectbox("עיר", city_options)
    company_filter = st.selectbox("חברה", company_options)
    current_type_filter = st.selectbox("סוג זרם", current_type_options)

    st.markdown("---")
    st.subheader("שאילתות מהירות")

    if st.button("עמדת DC מהירה בבאר שבע", use_container_width=True):
        st.session_state.pending_query = "איפה יש עמדת DC מהירה בבאר שבע?"
        st.session_state.sidebar_jump_to_top = True
        st.rerun()

    if st.button("CCS2 בתל אביב", use_container_width=True):
        st.session_state.pending_query = "איפה יש עמדת CCS2 בתל אביב?"
        st.session_state.sidebar_jump_to_top = True
        st.rerun()

    if st.button("עמדת AC בירושלים", use_container_width=True):
        st.session_state.pending_query = "איפה יש עמדת AC בירושלים?"
        st.session_state.sidebar_jump_to_top = True
        st.rerun()

    if st.button("העמדה הכי זולה", use_container_width=True):
        st.session_state.pending_query = "איפה נמצאת עמדת הטעינה הזולה ביותר?"
        st.session_state.sidebar_jump_to_top = True
        st.rerun()

    if st.button("DC בצפון", use_container_width=True):
        st.session_state.pending_query = "איפה יש עמדת DC בצפון?"
        st.session_state.sidebar_jump_to_top = True
        st.rerun()

    st.markdown("---")

    if st.button("נקה שיחה", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.last_results = []
        st.session_state.last_query = ""
        st.session_state.pending_query = None
        st.session_state.assistant_scroll_to_last_user = False
        st.session_state.sidebar_jump_to_top = False
        st.rerun()

# =========================
# Fixed Header Visual Shell
# =========================
st.markdown(
    """
    <div class="fixed-top-shell">
        <div class="fixed-top-inner">
            <div id="fixed-header-anchor"></div>
        </div>
    </div>
    <div class="header-spacer"></div>
    """,
    unsafe_allow_html=True,
)

# =========================
# Hero + Search Area
# =========================
with st.container():
    hero_left, hero_right = st.columns([1, 8])

    with hero_left:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=96)

    with hero_right:
        st.markdown(
            """
            <div class="hero-shell">
                <div class="hero-box">
                    <div class="hero-title">תחנות טעינה - סוכן ניתוח מתחרים</div>
                    <div class="hero-subtitle">
                        חיפוש חכם, תשובות AI והמלצות על עמדות טעינה לרכב חשמלי.
                        כלי פנימי לניתוח תחנות, השוואת ספקים, חיפוש לפי עיר/אזור וסיוע בקבלת החלטות.
                    </div>
                    <div class="hero-badges">
                        <span class="hero-badge">Semantic Search</span>
                        <span class="hero-badge">Geo-aware Retrieval</span>
                        <span class="hero-badge">AI Assistant</span>
                        <span class="hero-badge">Competitor Analysis</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="search-panel">', unsafe_allow_html=True)
    st.markdown('<div class="search-title">חיפוש חכם</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="quick-caption">הזן שאלה או השתמש בשאילתות המהירות מהצד</div>',
        unsafe_allow_html=True,
    )

    q1, q2, q3 = st.columns([6, 2, 2])

    with q1:
        _query = st.text_input(
            "שאל את ה־AI Assistant",
            key="query_input",
            placeholder="לדוגמה: איפה יש CCS2 בתל אביב?",
        )

    with q2:
        top_k = st.number_input(
            "מספר תוצאות",
            min_value=1,
            max_value=20,
            value=5,
            step=1,
        )

    with q3:
        generate_ai_summary = st.toggle("תשובת AI", value=True)

    search_clicked = st.button("חפש", type="primary", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.sidebar_jump_to_top:
    jump_page_to_top()
    st.session_state.sidebar_jump_to_top = False

# =========================
# Search Flow
# =========================
if search_clicked:
    user_query = st.session_state.query_input.strip()

    result = search_agent(
        user_query=user_query,
        top_k=int(top_k),
        city_filter=city_filter,
        company_filter=company_filter,
        current_type_filter=current_type_filter,
        chat_history=st.session_state.chat_history,
        generate_summary=generate_ai_summary,
    )

    if not result["ok"]:
        st.warning(result["error"])
    else:
        st.session_state.last_results = result["results"]
        st.session_state.last_query = user_query
        st.session_state.assistant_scroll_to_last_user = False

        if generate_ai_summary and result["ai_answer"]:
            st.session_state.chat_history.append({"role": "user", "content": user_query})
            st.session_state.chat_history.append({"role": "assistant", "content": result["ai_answer"]})
            st.session_state.assistant_scroll_to_last_user = True

# =========================
# Assistant Section
# =========================
st.markdown('<div class="section-title">Assistant</div>', unsafe_allow_html=True)
render_chat_history(
    st.session_state.chat_history,
    scroll_to_last_user=st.session_state.assistant_scroll_to_last_user,
)
st.session_state.assistant_scroll_to_last_user = False

# =========================
# Results / KPI / Map
# =========================
results = st.session_state.last_results
last_query = st.session_state.last_query

st.markdown('<div class="section-title">מדדים</div>', unsafe_allow_html=True)

if results:
    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">מספר תוצאות</div>
                <div class="kpi-value">{len(results)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k2:
        max_score = max(r.get("rerank_score", r["similarity"]) for r in results)
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">ציון סופי מקסימלי</div>
                <div class="kpi-value">{max_score:.4f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k3:
        unique_cities = sorted(
            set(safe_text(r["metadata"].get("city")) for r in results if safe_text(r["metadata"].get("city")))
        )
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">ערים בתוצאות</div>
                <div class="kpi-value">{len(unique_cities)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k4:
        dc_count = sum(
            1 for r in results if safe_text(r["metadata"].get("current_type")).upper() == "DC"
        )
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">תוצאות DC</div>
                <div class="kpi-value">{dc_count}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.info("אין עדיין מדדים להצגה.")

st.markdown('<div class="section-title">מפת תוצאות</div>', unsafe_allow_html=True)
if results:
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    fmap = build_folium_map(results)
    if fmap is not None:
        from streamlit_folium import st_folium
        st_folium(fmap, use_container_width=True, height=430)
    else:
        st.info("אין מיקומים תקינים להצגה על המפה.")
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("אין עדיין תוצאות להצגה על המפה.")

st.markdown('<div class="section-title">תוצאות</div>', unsafe_allow_html=True)
if results:
    st.caption(f"שאילתה אחרונה: {last_query}")
    for idx, result_item in enumerate(results, start=1):
        render_result_card(result_item, idx)
else:
    st.write("אין עדיין תוצאות להצגה.")

# =========================
# Footer
# =========================
st.markdown("---")
st.caption("Built with Azure OpenAI, ChromaDB, Streamlit, Folium | Paz AI Charging Assistant")