from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

CITY_LIST = [
    "תל אביב",
    "חיפה",
    "ירושלים",
    "באר שבע",
    "אשדוד",
    "פתח תקווה",
    "אילת",
    "נהריה",
    "עכו",
    "קרית שמונה",
]

REGION_MAP = {
    "חיפה": "north",
    "נהריה": "north",
    "עכו": "north",
    "קרית שמונה": "north",
    "תל אביב": "center",
    "פתח תקווה": "center",
    "אשדוד": "center",
    "ירושלים": "center",
    "באר שבע": "south",
    "אילת": "south",
}

DISTRICT_KEYWORDS = {
    "מחוז חיפה": "haifa_district",
    "מחוז צפון": "north_district",
    "מחוז תל אביב": "tel_aviv_district",
    "מחוז ירושלים": "jerusalem_district",
    "מחוז דרום": "south_district",
}

CITY_TO_DISTRICT = {
    "חיפה": "haifa_district",
    "נהריה": "north_district",
    "עכו": "north_district",
    "קרית שמונה": "north_district",
    "תל אביב": "tel_aviv_district",
    "פתח תקווה": "tel_aviv_district",
    "אשדוד": "tel_aviv_district",
    "ירושלים": "jerusalem_district",
    "באר שבע": "south_district",
    "אילת": "south_district",
}

REGION_KEYWORDS = {
    "צפון": "north",
    "דרום": "south",
    "מרכז": "center",
}

CITY_COORDS = {
    "תל אביב": (32.0853, 34.7818),
    "חיפה": (32.7940, 34.9896),
    "ירושלים": (31.7683, 35.2137),
    "באר שבע": (31.2529, 34.7915),
    "אשדוד": (31.8014, 34.6435),
    "פתח תקווה": (32.0840, 34.8878),
    "אילת": (29.5577, 34.9519),
    "נהריה": (33.0059, 35.0941),
    "עכו": (32.9230, 35.0827),
    "קרית שמונה": (33.2070, 35.5700),
}


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def detect_geo_intent(query: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    q = safe_text(query).lower()

    detected_city: Optional[str] = None
    detected_region: Optional[str] = None
    detected_district: Optional[str] = None

    for district_kw, district_value in DISTRICT_KEYWORDS.items():
        if district_kw in q:
            detected_district = district_value
            break

    for city in CITY_LIST:
        if city in query:
            detected_city = city
            detected_region = REGION_MAP.get(city)
            if not detected_district:
                detected_district = CITY_TO_DISTRICT.get(city)
            break

    if not detected_region:
        for region_kw, region_value in REGION_KEYWORDS.items():
            if region_kw in q:
                detected_region = region_value
                break

    return detected_city, detected_region, detected_district


def geo_filter(
    results: List[Dict[str, Any]],
    city: Optional[str],
    region: Optional[str],
    district: Optional[str],
) -> List[Dict[str, Any]]:
    if not city and not region and not district:
        return results

    filtered: List[Dict[str, Any]] = []

    for item in results:
        md = item["metadata"]

        md_city = safe_text(md.get("city"))
        md_region = REGION_MAP.get(md_city)
        md_district = CITY_TO_DISTRICT.get(md_city)

        if city:
            if md_city == city:
                filtered.append(item)
            continue

        if district:
            if md_district == district:
                filtered.append(item)
            continue

        if region:
            if md_region == region:
                filtered.append(item)
            continue

        filtered.append(item)

    # fallback: אם hard filter החזיר 0 תוצאות, נחזיר את התוצאות המקוריות
    return filtered if filtered else results


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0

    lat1_r = math.radians(lat1)
    lon1_r = math.radians(lon1)
    lat2_r = math.radians(lat2)
    lon2_r = math.radians(lon2)

    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return r * c