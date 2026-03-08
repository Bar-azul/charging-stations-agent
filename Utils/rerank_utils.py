from __future__ import annotations

from typing import Any, Dict, List

from Utils.geo_utils import (
    CITY_COORDS,
    CITY_TO_DISTRICT,
    REGION_MAP,
    detect_geo_intent,
    haversine_distance,
)


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_text_for_match(text: Any) -> str:
    return safe_text(text).lower()


def apply_filters(
    results: List[Dict[str, Any]],
    city_filter: str,
    company_filter: str,
    current_type_filter: str,
) -> List[Dict[str, Any]]:
    filtered: List[Dict[str, Any]] = []

    for item in results:
        md = item["metadata"]

        city_ok = city_filter == "הכל" or safe_text(md.get("city")) == city_filter
        company_ok = company_filter == "הכל" or safe_text(md.get("company")) == company_filter
        current_type_ok = (
            current_type_filter == "הכל" or safe_text(md.get("current_type")) == current_type_filter
        )

        if city_ok and company_ok and current_type_ok:
            filtered.append(item)

    return filtered


def rerank_results(query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    q = normalize_text_for_match(query)

    dc_keywords = ["dc", "מהירה", "fast", "rapid"]
    ac_keywords = ["ac"]
    ccs_keywords = ["ccs", "ccs2", "combo"]
    type2_keywords = ["type 2", "type2", "טייפ 2"]

    detected_city, detected_region, detected_district = detect_geo_intent(query)

    reranked: List[Dict[str, Any]] = []

    for item in results:
        md = item["metadata"]
        score = float(item["similarity"])

        city = safe_text(md.get("city"))
        item_region = REGION_MAP.get(city)
        item_district = CITY_TO_DISTRICT.get(city)

        current_type = normalize_text_for_match(md.get("current_type"))
        connectors = normalize_text_for_match(md.get("connector_types"))

        bonus = 0.0
        distance_km = None

        # =========================
        # GEO RERANK
        # =========================
        if detected_city and detected_city in city:
            bonus += 0.35

        if detected_region and item_region == detected_region:
            bonus += 0.20

        if detected_region and item_region and item_region != detected_region:
            bonus -= 0.15

        if detected_district and item_district == detected_district:
            bonus += 0.18

        if detected_district and item_district and item_district != detected_district:
            bonus -= 0.10

        # =========================
        # Semantic boosts
        # =========================
        if any(k in q for k in dc_keywords) and "dc" in current_type:
            bonus += 0.10

        if any(k in q for k in ac_keywords) and "ac" in current_type:
            bonus += 0.10

        if any(k in q for k in ccs_keywords) and "ccs" in connectors:
            bonus += 0.07

        if any(k in q for k in type2_keywords) and "type 2" in connectors:
            bonus += 0.07

        # =========================
        # Price boost
        # =========================
        if "זול" in q or "cheap" in q or "low price" in q or "מחיר" in q:
            try:
                price = float(md.get("price_per_kwh", -1))
                if price > 0:
                    bonus += max(0.0, (2.8 - price) * 0.03)
            except Exception:
                pass

        # =========================
        # LAB4.6 - Proximity Score
        # =========================
        if detected_city and detected_city in CITY_COORDS:
            try:
                station_lat = float(md.get("latitude"))
                station_lon = float(md.get("longitude"))
                city_lat, city_lon = CITY_COORDS[detected_city]

                distance_km = haversine_distance(station_lat, station_lon, city_lat, city_lon)
                distance_bonus = max(0.0, 0.2 - distance_km * 0.01)
                bonus += distance_bonus
            except Exception:
                distance_km = None

        item_copy = dict(item)
        item_copy["rerank_score"] = score + bonus

        if distance_km is not None:
            item_copy["distance_km"] = distance_km

        reranked.append(item_copy)

    reranked.sort(key=lambda x: x.get("rerank_score", x["similarity"]), reverse=True)
    return reranked