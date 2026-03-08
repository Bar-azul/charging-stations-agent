from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import AzureOpenAI

from Utils.ai_utils import generate_ai_answer, get_embedding
from Utils.geo_utils import detect_geo_intent, geo_filter
from Utils.rerank_utils import apply_filters, rerank_results
from Utils.search_utils import get_chroma_collection, load_all_metadata, search_vector_db
from Utils.ui_utils import (
    get_global_css,
    jump_page_to_top,
    render_chat_history,
    render_result_card,
    build_folium_map,
    safe_text,
)

load_dotenv()

# =========================
# Config
# =========================
APP_DIR = Path(__file__).parent
CHROMA_DIR = APP_DIR / "chroma_db"
COLLECTION_NAME = "ev_stations_lab3"
LOGO_PATH = APP_DIR / "paz_logo.png"

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
AZURE_OPENAI_CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")

if not AZURE_OPENAI_API_KEY:
    raise ValueError("Missing AZURE_OPENAI_API_KEY")

if not AZURE_OPENAI_ENDPOINT:
    raise ValueError("Missing AZURE_OPENAI_ENDPOINT")

if not AZURE_OPENAI_EMBEDDING_DEPLOYMENT:
    raise ValueError("Missing AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

if not AZURE_OPENAI_CHAT_DEPLOYMENT:
    raise ValueError("Missing AZURE_OPENAI_CHAT_DEPLOYMENT")

client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2024-02-01",
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
)

# =========================
# Page Setup
# =========================
st.set_page_config(
    page_title="תחנות טעינה - סוכן ניתוח מתחרים",
    page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "⚡",
    layout="wide",
)

st.markdown(get_global_css(), unsafe_allow_html=True)

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
# Collection + Metadata
# =========================
collection = get_chroma_collection(CHROMA_DIR, COLLECTION_NAME)
metadata_df = load_all_metadata(collection)

city_options = ["הכל"]
company_options = ["הכל"]
current_type_options = ["הכל"]

if not metadata_df.empty:
    city_options += sorted(
        [x for x in metadata_df["city"].dropna().astype(str).unique().tolist() if x.strip()]
    )
    company_options += sorted(
        [x for x in metadata_df["company"].dropna().astype(str).unique().tolist() if x.strip()]
    )
    current_type_options += sorted(
        [x for x in metadata_df["current_type"].dropna().astype(str).unique().tolist() if x.strip()]
    )

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
            <div class="fixed-header-panel">
                <div id="fixed-header-anchor"></div>
            </div>
        </div>
    </div>
    <div class="header-spacer"></div>
    """,
    unsafe_allow_html=True,
)

# =========================
# Search Area
# =========================
with st.container():
    st.markdown('<div class="fixed-header-panel">', unsafe_allow_html=True)

    header_col1, header_col2 = st.columns([1, 8])

    with header_col1:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=92)

    with header_col2:
        st.markdown(
            """
            <div class="hero-box">
                <div class="hero-title">תחנות טעינה - סוכן ניתוח מתחרים</div>
                <div class="hero-subtitle">חיפוש חכם, תשובות AI והמלצות על עמדות טעינה לרכב חשמלי</div>
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
    st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.sidebar_jump_to_top:
    jump_page_to_top()
    st.session_state.sidebar_jump_to_top = False

# =========================
# Search Flow
# =========================
if search_clicked:
    user_query = st.session_state.query_input.strip()

    if not user_query:
        st.warning("יש להזין שאלה.")
    else:
        with st.spinner("מבצע חיפוש סמנטי..."):
            try:
                query_embedding = get_embedding(
                    client=client,
                    deployment_name=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
                    text=user_query,
                )

                raw_results = search_vector_db(
                    collection=collection,
                    query_embedding=query_embedding,
                    top_k=int(top_k),
                    overfetch_factor=4,
                )

                metadata_filtered_results = apply_filters(
                    results=raw_results,
                    city_filter=city_filter,
                    company_filter=company_filter,
                    current_type_filter=current_type_filter,
                )

                detected_city, detected_region, detected_district = detect_geo_intent(user_query)

                geo_filtered_results = geo_filter(
                    results=metadata_filtered_results,
                    city=detected_city,
                    region=detected_region,
                    district=detected_district,
                )

                reranked_results = rerank_results(
                    query=user_query,
                    results=geo_filtered_results,
                )

                final_results = reranked_results[: int(top_k)]

            except Exception as e:
                st.error(f"החיפוש נכשל: {e}")
                final_results = []

        st.session_state.last_results = final_results
        st.session_state.last_query = user_query
        st.session_state.assistant_scroll_to_last_user = False

        if generate_ai_summary and final_results:
            with st.spinner("מייצר תשובת AI..."):
                try:
                    ai_answer = generate_ai_answer(
                        client=client,
                        deployment_name=AZURE_OPENAI_CHAT_DEPLOYMENT,
                        user_query=user_query,
                        results=final_results,
                        chat_history=st.session_state.chat_history,
                    )
                except Exception as e:
                    ai_answer = f"לא ניתן היה לייצר תשובת AI: {e}"

            st.session_state.chat_history.append({"role": "user", "content": user_query})
            st.session_state.chat_history.append({"role": "assistant", "content": ai_answer})
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
        st.metric("מספר תוצאות", len(results))

    with k2:
        st.metric(
            "ציון סופי מקסימלי",
            f"{max(r.get('rerank_score', r['similarity']) for r in results):.4f}",
        )

    with k3:
        unique_cities = sorted(
            set(safe_text(r["metadata"].get("city")) for r in results if safe_text(r["metadata"].get("city")))
        )
        st.metric("ערים בתוצאות", len(unique_cities))

    with k4:
        dc_count = sum(
            1 for r in results if safe_text(r["metadata"].get("current_type")).upper() == "DC"
        )
        st.metric("תוצאות DC", dc_count)
else:
    st.info("אין עדיין מדדים להצגה.")

st.markdown('<div class="section-title">מפת תוצאות</div>', unsafe_allow_html=True)
if results:
    fmap = build_folium_map(results)
    if fmap is not None:
        from streamlit_folium import st_folium

        st_folium(fmap, use_container_width=True, height=430)
    else:
        st.info("אין מיקומים תקינים להצגה על המפה.")
else:
    st.info("אין עדיין תוצאות להצגה על המפה.")

st.markdown('<div class="section-title">תוצאות</div>', unsafe_allow_html=True)
if results:
    st.caption(f"שאילתה אחרונה: {last_query}")
    for idx, result in enumerate(results, start=1):
        render_result_card(result, idx)
else:
    st.write("אין עדיין תוצאות להצגה.")

# =========================
# Footer
# =========================
st.markdown("---")
st.caption("Built with Azure OpenAI, ChromaDB, Streamlit, Folium | Paz AI Charging Assistant")