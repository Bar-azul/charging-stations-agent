from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import AzureOpenAI

from Utils.ai_utils import generate_ai_answer, get_embedding
from Utils.geo_utils import detect_geo_intent, geo_filter
from Utils.rerank_utils import apply_filters, rerank_results
from Utils.search_utils import get_chroma_collection, load_all_metadata, search_vector_db

load_dotenv()

# =========================
# Config
# =========================
APP_DIR = Path(__file__).parent
CHROMA_DIR = APP_DIR / "chroma_db"
COLLECTION_NAME = "ev_stations_lab3"

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


# =========================
# Singletons
# =========================
_client: AzureOpenAI | None = None
_collection = None
_metadata_df = None


def get_client() -> AzureOpenAI:
    global _client
    if _client is None:
        _client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version="2024-02-01",
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
        )
    return _client


def get_collection():
    global _collection
    if _collection is None:
        _collection = get_chroma_collection(CHROMA_DIR, COLLECTION_NAME)
    return _collection


def get_metadata_df():
    global _metadata_df
    if _metadata_df is None:
        _metadata_df = load_all_metadata(get_collection())
    return _metadata_df


# =========================
# Public helpers for UI
# =========================
def get_filter_options() -> Dict[str, List[str]]:
    metadata_df = get_metadata_df()

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

    return {
        "city_options": city_options,
        "company_options": company_options,
        "current_type_options": current_type_options,
    }


# =========================
# Main Agent API
# =========================
def search_agent(
    user_query: str,
    top_k: int = 5,
    city_filter: str = "הכל",
    company_filter: str = "הכל",
    current_type_filter: str = "הכל",
    chat_history: List[Dict[str, str]] | None = None,
    generate_summary: bool = True,
) -> Dict[str, Any]:
    """
    פונקציה מרכזית שכל UI יכול להשתמש בה.
    מחזירה גם תוצאות וגם תשובת AI.
    """
    if not user_query or not user_query.strip():
        return {
            "ok": False,
            "error": "יש להזין שאלה.",
            "results": [],
            "ai_answer": "",
            "detected_city": None,
            "detected_region": None,
            "detected_district": None,
        }

    user_query = user_query.strip()
    chat_history = chat_history or []

    client = get_client()
    collection = get_collection()

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

    ai_answer = ""
    if generate_summary and final_results:
        ai_answer = generate_ai_answer(
            client=client,
            deployment_name=AZURE_OPENAI_CHAT_DEPLOYMENT,
            user_query=user_query,
            results=final_results,
            chat_history=chat_history,
        )

    return {
        "ok": True,
        "error": "",
        "results": final_results,
        "ai_answer": ai_answer,
        "detected_city": detected_city,
        "detected_region": detected_region,
        "detected_district": detected_district,
        "raw_count": len(raw_results),
        "metadata_filtered_count": len(metadata_filtered_results),
        "geo_filtered_count": len(geo_filtered_results),
    }


def ask_agent_text(
    user_query: str,
    top_k: int = 5,
    city_filter: str = "הכל",
    company_filter: str = "הכל",
    current_type_filter: str = "הכל",
    chat_history: List[Dict[str, str]] | None = None,
) -> str:
    """
    פונקציה פשוטה לדמו Gradio/API:
    מחזירה רק טקסט.
    """
    result = search_agent(
        user_query=user_query,
        top_k=top_k,
        city_filter=city_filter,
        company_filter=company_filter,
        current_type_filter=current_type_filter,
        chat_history=chat_history or [],
        generate_summary=True,
    )

    if not result["ok"]:
        return result["error"]

    if result["ai_answer"]:
        return result["ai_answer"]

    if not result["results"]:
        return "לא נמצאו תוצאות מתאימות."

    top = result["results"][0]
    md = top["metadata"]

    return (
        f"נמצאה תוצאה מובילה:\n"
        f"מיקום: {md.get('location_name', '')}\n"
        f"עיר: {md.get('city', '')}\n"
        f"חברה: {md.get('company', '')}\n"
        f"סוג זרם: {md.get('current_type', '')}\n"
        f"מחיר: {md.get('price_per_kwh', '')} {md.get('currency', '')}"
    )