from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import chromadb
import pandas as pd


def get_chroma_collection(db_path: Path, collection_name: str):
    chroma_client = chromadb.PersistentClient(path=str(db_path))
    return chroma_client.get_collection(collection_name)


def load_all_metadata(collection) -> pd.DataFrame:
    payload = collection.get(include=["metadatas"])
    metadatas = payload.get("metadatas", [])

    if not metadatas:
        return pd.DataFrame()

    df = pd.DataFrame(metadatas)

    expected_cols = [
        "provider",
        "company",
        "city",
        "location_name",
        "address",
        "station_id",
        "location_id",
        "current_type",
        "connector_types",
        "currency",
        "station_status",
        "max_power_kw",
        "price_per_kwh",
        "latitude",
        "longitude",
    ]

    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""

    return df


def search_vector_db(
    collection,
    query_embedding: List[float],
    top_k: int = 5,
    overfetch_factor: int = 4,
) -> List[Dict[str, Any]]:
    n_results = max(top_k * overfetch_factor, 15)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
    )

    ids = results["ids"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]
    documents = results["documents"][0]

    output: List[Dict[str, Any]] = []

    for doc_id, distance, metadata, document in zip(ids, distances, metadatas, documents):
        similarity = 1 - distance
        output.append(
            {
                "id": doc_id,
                "similarity": float(similarity),
                "metadata": metadata,
                "document": document,
            }
        )

    return output