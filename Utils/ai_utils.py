from __future__ import annotations

from typing import Any, Dict, List


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def get_embedding(client, deployment_name: str, text: str) -> List[float]:
    response = client.embeddings.create(
        model=deployment_name,
        input=text,
    )
    return response.data[0].embedding


def build_ai_context(results: List[Dict[str, Any]]) -> str:
    chunks = []

    for idx, item in enumerate(results, start=1):
        md = item["metadata"]

        distance_line = ""
        if "distance_km" in item and item["distance_km"] is not None:
            distance_line = f"Distance from requested city: {item['distance_km']:.2f} km"

        lines = [
            f"תוצאה #{idx}",
            f"Location: {safe_text(md.get('location_name'))}",
            f"City: {safe_text(md.get('city'))}",
            f"Address: {safe_text(md.get('address'))}",
            f"Company: {safe_text(md.get('company'))}",
            f"Provider: {safe_text(md.get('provider'))}",
            f"Current Type: {safe_text(md.get('current_type'))}",
            f"Connector Types: {safe_text(md.get('connector_types'))}",
            f"Max Power: {safe_text(md.get('max_power_kw'))} kW",
            f"Price/kWh: {safe_text(md.get('price_per_kwh'))} {safe_text(md.get('currency'))}",
            f"Station Status: {safe_text(md.get('station_status'))}",
            f"Similarity: {item.get('rerank_score', item['similarity']):.4f}",
        ]

        if distance_line:
            lines.append(distance_line)

        chunks.append("\n".join(lines))

    return "\n\n".join(chunks)


def generate_ai_answer(
    client,
    deployment_name: str,
    user_query: str,
    results: List[Dict[str, Any]],
    chat_history: List[Dict[str, str]],
) -> str:
    context = build_ai_context(results)
    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history[-6:]])

    prompt = f"""
אתה Paz AI Charging Assistant.
אתה עוזר חכם למציאת עמדות טעינה לרכב חשמלי בישראל.

הנחיות:
1. ענה בעברית.
2. התבסס רק על תוצאות החיפוש שניתנו לך.
3. אם ההתאמה חלקית או לא מושלמת, תגיד זאת בכנות.
4. סכם את הממצאים בצורה עניינית וברורה.
5. אם יש כמה תוצאות טובות, הצג אותן כרשימה.
6. התייחס לתוצאות לפי מספרי תוצאה (#1, #2, #3).
7. אם המשתמש מבקש המלצה, תן המלצה מנומקת לפי סוג זרם, סוג מחבר, עיר, הספק, מחיר ומרחק אם קיים.
8. אם אין מספיק מידע כדי לענות בוודאות, ציין זאת.
9. אם המשתמש שואל על "מהירה", הסבר האם מדובר ב-Fast Charge או Ultra Charge כאשר רלוונטי.

היסטוריית שיחה אחרונה:
{history_text}

שאלת המשתמש:
{user_query}

תוצאות החיפוש:
{context}

ענה בעברית, ברור ומובנה, עם התייחסות לתוצאות (#1/#2 וכו').
"""

    response = client.chat.completions.create(
        model=deployment_name,
        temperature=0.2,
        messages=[
            {"role": "system", "content": "אתה Paz AI Charging Assistant."},
            {"role": "user", "content": prompt},
        ],
    )

    return response.choices[0].message.content or ""