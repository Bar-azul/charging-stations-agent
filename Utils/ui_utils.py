from __future__ import annotations

import html
from typing import Any, Dict, List

import folium
import streamlit as st
import streamlit.components.v1 as components


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def html_text(text: Any) -> str:
    return html.escape(safe_text(text)).replace("\n", "<br>")


def similarity_label(score: float) -> str:
    if score >= 0.35:
        return "התאמה גבוהה"
    if score >= 0.25:
        return "התאמה בינונית"
    return "התאמה נמוכה"


def similarity_badge_html(score: float) -> str:
    label = similarity_label(score)
    if score >= 0.35:
        cls = "badge badge-high"
    elif score >= 0.25:
        cls = "badge badge-mid"
    else:
        cls = "badge badge-low"
    return f'<span class="{cls}">{label}</span>'


def charge_speed_label(current_type: str, max_power_kw: Any) -> str:
    current_type = safe_text(current_type).upper()

    if current_type != "DC":
        return ""

    try:
        power = float(max_power_kw)
    except (TypeError, ValueError):
        return "Fast Charge"

    if power > 150:
        return "Ultra Charge"
    return "Fast Charge"


def current_type_badges_html(current_type: str, max_power_kw: Any) -> str:
    current_type_clean = safe_text(current_type).upper()
    badges: List[str] = []

    if current_type_clean == "DC":
        badges.append('<span class="badge badge-dc">DC</span>')
        speed_label = charge_speed_label(current_type_clean, max_power_kw)
        if speed_label == "Ultra Charge":
            badges.append('<span class="badge badge-ultra">Ultra Charge</span>')
        elif speed_label == "Fast Charge":
            badges.append('<span class="badge badge-fast">Fast Charge</span>')
    elif current_type_clean == "AC":
        badges.append('<span class="badge badge-ac">AC</span>')
    else:
        badges.append('<span class="badge">Unknown</span>')

    return "".join(badges)


def get_global_css() -> str:
    return """
    <style>
        html, body, [class*="css"] {
            direction: rtl;
            text-align: right;
        }

        .block-container {
            padding-top: 0.2rem;
            padding-bottom: 2rem;
            max-width: 1520px;
        }

        :root {
            --paz-blue-1: #061632;
            --paz-blue-2: #0A234F;
            --paz-blue-3: #143A7B;
            --paz-blue-4: #2459A8;
            --paz-yellow: #F6B300;
            --paz-yellow-soft: #FFF5D9;
            --paz-bg-soft: #F7F9FC;
            --paz-border: #DCE3EE;
            --paz-text: #14213D;
            --paz-muted: #667085;
            --paz-white: #FFFFFF;
        }

        .section-title {
            color: var(--paz-blue-2);
            font-size: 2rem;
            font-weight: 900;
            margin-top: 0.45rem;
            margin-bottom: 0.8rem;
        }

        .result-title {
            color: var(--paz-blue-2);
        }

        .sidebar-logo-wrap {
            display: flex;
            justify-content: center;
            margin-bottom: 12px;
        }

        .fixed-top-shell {
            position: fixed;
            top: 0.5rem;
            left: 0;
            right: 0;
            z-index: 9999;
            pointer-events: none;
        }

        .fixed-top-inner {
            width: min(1520px, calc(100vw - 22rem));
            margin-right: auto;
            margin-left: 1rem;
            pointer-events: auto;
            background:
                linear-gradient(
                    180deg,
                    rgba(247,249,252,0.98) 0%,
                    rgba(247,249,252,0.96) 70%,
                    rgba(247,249,252,0.93) 100%
                );
            backdrop-filter: blur(10px);
            border-radius: 26px;
            padding: 0;
        }

        @media (max-width: 1200px) {
            .fixed-top-inner {
                width: calc(100vw - 2rem);
                margin-left: 1rem;
                margin-right: 1rem;
            }
        }

        .fixed-header-panel {
            border: 1px solid rgba(10,35,79,0.10);
            border-radius: 24px;
            overflow: hidden;
            background: #ffffff;
            box-shadow: 0 10px 24px rgba(6,22,50,0.10);
        }

        .hero-box {
            padding: 18px 24px 16px 24px;
            background:
                linear-gradient(
                    135deg,
                    rgba(6,22,50,1) 0%,
                    rgba(10,35,79,1) 55%,
                    rgba(20,58,123,1) 100%
                );
            position: relative;
            overflow: hidden;
            border-bottom: 1px solid rgba(246,179,0,0.18);
        }

        .hero-box::after {
            content: "";
            position: absolute;
            left: -40px;
            top: -40px;
            width: 180px;
            height: 180px;
            background: radial-gradient(circle, rgba(246,179,0,0.18) 0%, rgba(246,179,0,0) 70%);
            pointer-events: none;
        }

        .hero-title {
            color: white;
            font-size: 2rem;
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 6px;
        }

        .hero-subtitle {
            color: #E6EEF8;
            font-size: 1rem;
        }

        .search-panel {
            padding: 14px 16px 16px 16px;
            background: linear-gradient(180deg, #FFFFFF 0%, #FBFCFE 100%);
        }

        .search-title {
            color: var(--paz-blue-2);
            font-weight: 900;
            font-size: 1rem;
            margin-bottom: 10px;
        }

        .quick-caption {
            color: var(--paz-muted);
            font-size: 0.9rem;
            margin-bottom: 0.55rem;
        }

        .header-spacer {
            height: 20px;
        }

        .badge {
            display: inline-block;
            padding: 4px 11px;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 800;
            margin-left: 6px;
            margin-bottom: 6px;
            border: 1px solid transparent;
        }

        .badge-dc {
            background-color: #3D157B;
            color: #F3E8FF;
            border-color: #7C3AED;
        }

        .badge-ac {
            background-color: #0A4B78;
            color: #D9F2FF;
            border-color: #38BDF8;
        }

        .badge-fast {
            background-color: #7A3E00;
            color: #FFF0C2;
            border-color: #F59E0B;
        }

        .badge-ultra {
            background-color: #7A0C19;
            color: #FFE0E5;
            border-color: #EF4444;
        }

        .badge-high {
            background-color: #0B5E2B;
            color: #D7FBE4;
            border-color: #22C55E;
        }

        .badge-mid {
            background-color: #855300;
            color: #FFF0C2;
            border-color: #F59E0B;
        }

        .badge-low {
            background-color: #7A1220;
            color: #FFDCE2;
            border-color: #EF4444;
        }

        div[data-testid="stMetric"] {
            background: white;
            border: 1px solid var(--paz-border);
            border-radius: 18px;
            padding: 10px 8px;
            box-shadow: 0 4px 12px rgba(20,33,61,0.04);
        }

        div[data-testid="stTextInput"] input {
            border-radius: 14px !important;
            border: 1px solid var(--paz-border) !important;
            background: #FBFCFE !important;
            min-height: 46px !important;
        }

        div[data-testid="stNumberInput"] input {
            border-radius: 14px !important;
            border: 1px solid var(--paz-border) !important;
            background: #FBFCFE !important;
            min-height: 46px !important;
        }

        div[data-testid="stSelectbox"] > div {
            border-radius: 14px !important;
        }

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
            min-height: 48px !important;
            box-shadow: 0 8px 18px rgba(10,35,79,0.20) !important;
        }

        button[kind="primary"]:hover {
            filter: brightness(1.04);
        }

        button[kind="secondary"] {
            border-radius: 12px !important;
            border: 1px solid var(--paz-border) !important;
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
    </style>
    """


def render_chat_history(chat_history: List[Dict[str, str]], scroll_to_last_user: bool = False) -> None:
    chat_css = """
    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: transparent;
            direction: rtl;
            text-align: right;
        }

        .assistant-shell {
            border: 1px solid #DCE3EE;
            border-radius: 22px;
            background: linear-gradient(180deg, #FBFCFE 0%, #F4F8FD 100%);
            box-shadow: 0 8px 24px rgba(20,33,61,0.06);
            padding: 14px;
            box-sizing: border-box;
        }

        .assistant-scrollbox {
            height: 500px;
            overflow-y: auto;
            padding: 4px 6px;
            scroll-behavior: smooth;
        }

        .chat-row {
            display: flex;
            width: 100%;
            margin-bottom: 12px;
        }

        .chat-row.user {
            justify-content: flex-end;
        }

        .chat-row.assistant {
            justify-content: flex-start;
        }

        .chat-bubble {
            max-width: 82%;
            padding: 14px 16px;
            border-radius: 18px;
            border: 1px solid #DCE3EE;
            box-shadow: 0 4px 14px rgba(20,33,61,0.05);
            box-sizing: border-box;
        }

        .chat-row.user .chat-bubble {
            background: linear-gradient(180deg, #FFF8ED 0%, #FFF2D6 100%);
            border-right: 6px solid #F6B300;
        }

        .chat-row.assistant .chat-bubble {
            background: linear-gradient(180deg, #EEF5FF 0%, #E4EEFF 100%);
            border-right: 6px solid #143A7B;
        }

        .chat-role {
            font-size: 0.8rem;
            font-weight: 800;
            color: #0A234F;
            margin-bottom: 8px;
        }

        .chat-content {
            color: #14213D;
            font-size: 0.98rem;
            line-height: 1.8;
            white-space: pre-wrap;
            word-break: break-word;
        }

        .chat-empty {
            padding: 18px;
            border: 1px dashed #DCE3EE;
            border-radius: 16px;
            background: white;
            color: #667085;
        }
    </style>
    """

    if not chat_history:
        html_doc = f"""
        {chat_css}
        <div class="assistant-shell">
            <div class="chat-empty">עדיין אין שיחה. שאל שאלה כדי להתחיל.</div>
        </div>
        """
        components.html(html_doc, height=120, scrolling=False)
        return

    html_parts: List[str] = [
        chat_css,
        '<div class="assistant-shell">',
        '<div class="assistant-scrollbox" id="assistant-scrollbox">'
    ]

    user_counter = 0
    last_user_anchor_id = ""

    i = 0
    while i < len(chat_history):
        if chat_history[i]["role"] == "user":
            user_counter += 1
            user_text = chat_history[i]["content"]
            anchor_id = f"last-user-anchor-{user_counter}"
            last_user_anchor_id = anchor_id

            html_parts.append(
                f"""
                <div id="{anchor_id}"></div>
                <div class="chat-row user">
                    <div class="chat-bubble">
                        <div class="chat-role">שאלה</div>
                        <div class="chat-content">{html_text(user_text)}</div>
                    </div>
                </div>
                """
            )

            if i + 1 < len(chat_history) and chat_history[i + 1]["role"] == "assistant":
                assistant_text = chat_history[i + 1]["content"]
                html_parts.append(
                    f"""
                    <div class="chat-row assistant">
                        <div class="chat-bubble">
                            <div class="chat-role">תשובה</div>
                            <div class="chat-content">{html_text(assistant_text)}</div>
                        </div>
                    </div>
                    """
                )

            i += 2
        else:
            assistant_text = chat_history[i]["content"]
            html_parts.append(
                f"""
                <div class="chat-row assistant">
                    <div class="chat-bubble">
                        <div class="chat-role">תשובה</div>
                        <div class="chat-content">{html_text(assistant_text)}</div>
                    </div>
                </div>
                """
            )
            i += 1

    if scroll_to_last_user and last_user_anchor_id:
        html_parts.append(
            f"""
            <script>
                function scrollLastQuestionToTop() {{
                    const box = document.getElementById("assistant-scrollbox");
                    const target = document.getElementById("{last_user_anchor_id}");
                    if (!box || !target) return;

                    const targetTop = target.offsetTop - 8;
                    box.scrollTop = targetTop < 0 ? 0 : targetTop;
                }}

                window.addEventListener("load", function() {{
                    scrollLastQuestionToTop();
                    requestAnimationFrame(scrollLastQuestionToTop);
                    setTimeout(scrollLastQuestionToTop, 60);
                    setTimeout(scrollLastQuestionToTop, 180);
                    setTimeout(scrollLastQuestionToTop, 400);
                    setTimeout(scrollLastQuestionToTop, 800);
                    setTimeout(scrollLastQuestionToTop, 1200);
                }});
            </script>
            """
        )

    html_parts.append("</div></div>")
    html_doc = "".join(html_parts)

    components.html(html_doc, height=540, scrolling=False)


def build_folium_map(results: List[Dict[str, Any]]) -> folium.Map | None:
    points = []

    for item in results:
        md = item["metadata"]
        lat = md.get("latitude")
        lon = md.get("longitude")

        try:
            lat_f = float(lat)
            lon_f = float(lon)
        except (TypeError, ValueError):
            continue

        if lat_f == 0.0 and lon_f == 0.0:
            continue

        points.append((lat_f, lon_f))

    if not points:
        return None

    avg_lat = sum(p[0] for p in points) / len(points)
    avg_lon = sum(p[1] for p in points) / len(points)

    fmap = folium.Map(location=[avg_lat, avg_lon], zoom_start=7, tiles="CartoDB positron")

    for idx, item in enumerate(results, start=1):
        md = item["metadata"]

        try:
            lat_f = float(md.get("latitude"))
            lon_f = float(md.get("longitude"))
        except (TypeError, ValueError):
            continue

        if lat_f == 0.0 and lon_f == 0.0:
            continue

        title = safe_text(md.get("location_name"))
        company = safe_text(md.get("company"))
        city = safe_text(md.get("city"))
        current_type = safe_text(md.get("current_type"))
        power = safe_text(md.get("max_power_kw"))
        price = safe_text(md.get("price_per_kwh"))
        currency = safe_text(md.get("currency"))

        popup_html = f"""
        <div style="direction: rtl; text-align: right; min-width: 220px;">
            <b>{html.escape(title)}</b><br>
            חברה: {html.escape(company)}<br>
            עיר: {html.escape(city)}<br>
            סוג זרם: {html.escape(current_type)}<br>
            הספק: {html.escape(power)} kW<br>
            מחיר: {html.escape(price)} {html.escape(currency)}<br>
            תוצאה: #{idx}
        </div>
        """

        color = "purple" if safe_text(current_type).upper() == "DC" else "blue"

        folium.Marker(
            location=[lat_f, lon_f],
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{title} | {company}",
            icon=folium.Icon(color=color, icon="flash", prefix="glyphicon"),
        ).add_to(fmap)

    return fmap


def render_result_card(result: Dict[str, Any], index: int) -> None:
    md = result["metadata"]
    similarity = result["similarity"]
    rerank_score = result.get("rerank_score", similarity)
    distance_km = result.get("distance_km")

    title = safe_text(md.get("location_name")) or f"תוצאה #{index}"
    city = safe_text(md.get("city"))
    company = safe_text(md.get("company"))
    provider = safe_text(md.get("provider"))
    address = safe_text(md.get("address"))
    current_type = safe_text(md.get("current_type"))
    connector_types = safe_text(md.get("connector_types"))
    max_power_kw = md.get("max_power_kw")
    price_per_kwh = md.get("price_per_kwh")
    currency = safe_text(md.get("currency"))
    station_id = safe_text(md.get("station_id"))
    location_id = safe_text(md.get("location_id"))
    station_status = safe_text(md.get("station_status"))
    document = result["document"]

    with st.container(border=True):
        top_left, top_right = st.columns([4, 1])

        with top_left:
            st.markdown(f'<div class="result-title">### {index}. {title}</div>', unsafe_allow_html=True)
            st.caption(f"{city} | {company} | {provider}")

        with top_right:
            st.markdown(
                current_type_badges_html(current_type, max_power_kw) + similarity_badge_html(rerank_score),
                unsafe_allow_html=True,
            )

        c1, c2, c3 = st.columns(3)

        with c1:
            st.write("**עיר**")
            st.write(city)

            st.write("**כתובת**")
            st.write(address)

            st.write("**חברה**")
            st.write(company)

            st.write("**ספק**")
            st.write(provider)

        with c2:
            st.write("**סוג זרם**")
            st.write(current_type)

            st.write("**סוגי מחברים**")
            st.write(connector_types)

            st.write("**הספק מקסימלי**")
            st.write(f"{max_power_kw} kW")

            st.write("**מחיר לקוט״ש**")
            st.write(f"{price_per_kwh} {currency}")

        with c3:
            st.write("**Station ID**")
            st.write(station_id)

            st.write("**Location ID**")
            st.write(location_id)

            st.write("**סטטוס תחנה**")
            st.write(station_status)

            st.write("**ציון Vector**")
            st.write(f"{similarity:.4f}")

            st.write("**ציון סופי**")
            st.write(f"{rerank_score:.4f}")

            if distance_km is not None:
                st.write("**מרחק משוער**")
                st.write(f"{distance_km:.2f} ק״מ")

        with st.expander("הצג Document מלא"):
            st.text(document)


def jump_page_to_top() -> None:
    components.html(
        """
        <script>
            function jumpTop() {
                try {
                    window.parent.scrollTo({ top: 0, behavior: "smooth" });
                } catch (e) {}
            }

            window.addEventListener("load", function() {
                jumpTop();
                requestAnimationFrame(jumpTop);
                setTimeout(jumpTop, 100);
                setTimeout(jumpTop, 300);
                setTimeout(jumpTop, 700);
            });
        </script>
        """,
        height=0,
        scrolling=False,
    )