from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import chromadb
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()


# =========================
# Config
# =========================
DATA_DIR = Path("data")
CHROMA_DIR = Path("chroma_db")
COLLECTION_NAME = "ev_stations_lab3"

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

if not AZURE_OPENAI_API_KEY:
    raise ValueError("Missing AZURE_OPENAI_API_KEY")

if not AZURE_OPENAI_ENDPOINT:
    raise ValueError("Missing AZURE_OPENAI_ENDPOINT")

if not AZURE_OPENAI_EMBEDDING_DEPLOYMENT:
    raise ValueError("Missing AZURE_OPENAI_EMBEDDING_DEPLOYMENT")


client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2024-02-01",
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)


# =========================
# Helpers
# =========================
def print_field(label: str, value: Any) -> None:
    print(f"{label}:")
    print("" if value is None else str(value))


def print_document_lines(document: str) -> None:
    print("Document:")
    for line in document.splitlines():
        print(line)

def get_embedding(text: str) -> List[float]:
    response = client.embeddings.create(
        model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        input=text
    )
    return response.data[0].embedding


def safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def normalize_connector_type(connector_type: Optional[str]) -> str:
    if not connector_type:
        return ""

    text = connector_type.strip()

    replacements = {
        "IEC_62196_T2_COMBO | CABLE": "CCS2 cable",
        "IEC_62196_T2 | SOCKET": "Type 2 socket",
        "IEC_62196_T2 | CABLE": "Type 2 cable",
        "CCS2": "CCS2",
        "Type 2": "Type 2",
    }

    return replacements.get(text, text)


def extract_station_price(station: Dict[str, Any]) -> Tuple[Optional[float], Optional[str]]:
    """
    מחיר התחנה:
    1. קודם station.tariff
    2. אם אין, ניקח מה-connector הראשון שיש בו tariff.price_per_kwh
    """
    station_tariff = station.get("tariff") or {}
    price = station_tariff.get("price_per_kwh")
    currency = station_tariff.get("currency")

    if price is not None:
        return price, currency

    for connector in station.get("connectors", []):
        connector_tariff = connector.get("tariff") or {}
        price = connector_tariff.get("price_per_kwh")
        currency = connector_tariff.get("currency")
        if price is not None:
            return price, currency

    return None, None


def extract_connector_summary(station: Dict[str, Any]) -> Tuple[str, str, str]:
    connector_types: List[str] = []
    connector_powers: List[str] = []
    connector_statuses: List[str] = []

    for connector in station.get("connectors", []):
        ctype = normalize_connector_type(connector.get("connector_type"))
        cpow = connector.get("power_kw")
        cstatus = connector.get("status")

        if ctype:
            connector_types.append(ctype)

        if cpow is not None:
            connector_powers.append(f"{cpow} kW")

        if cstatus:
            connector_statuses.append(str(cstatus))

    connector_types_text = ", ".join(sorted(set(connector_types)))
    connector_powers_text = ", ".join(sorted(set(connector_powers)))
    connector_statuses_text = ", ".join(sorted(set(connector_statuses)))

    return connector_types_text, connector_powers_text, connector_statuses_text


def build_station_document(
    company_root: Dict[str, Any],
    location: Dict[str, Any],
    station: Dict[str, Any]
) -> Tuple[str, Dict[str, Any], str]:
    """
    מחזיר:
    1. document_id
    2. metadata
    3. document_text
    """
    top_company = safe_str(company_root.get("company"))
    output_key = safe_str(company_root.get("output_key"))
    provider = safe_str(location.get("provider"))
    company = safe_str(location.get("company"), top_company)

    location_id = safe_str(location.get("location_id"))
    location_name = safe_str(location.get("location_name"))
    address = safe_str(location.get("address"))
    city = safe_str(location.get("city"))
    latitude = location.get("latitude")
    longitude = location.get("longitude")

    station_id = safe_str(station.get("station_id"))
    station_identifier = safe_str(station.get("station_identifier"))
    max_power_kw = station.get("max_power_kw")
    current_type = safe_str(station.get("current_type"))
    station_status = safe_str(station.get("status"))

    connector_types_text, connector_powers_text, connector_statuses_text = extract_connector_summary(station)
    price_per_kwh, currency = extract_station_price(station)

    document_id = f"{output_key}__{location_id}__{station_id}"

    lines = [
        f"Charging station provider: {provider}.",
        f"Company: {company}.",
        f"Output key: {output_key}.",
        f"Location name: {location_name}.",
        f"City: {city}.",
        f"Address: {address}.",
        f"Location ID: {location_id}.",
        f"Station ID: {station_id}.",
        f"Station identifier: {station_identifier}.",
        f"Current type: {current_type}.",
        f"Max power: {max_power_kw} kW." if max_power_kw is not None else "Max power: unknown.",
        f"Station status: {station_status}.",
        f"Connector types: {connector_types_text or 'unknown'}.",
        f"Connector powers: {connector_powers_text or 'unknown'}.",
        f"Connector statuses: {connector_statuses_text or 'unknown'}.",
    ]

    if price_per_kwh is not None:
        lines.append(f"Price per kWh: {price_per_kwh} {currency or ''}.".strip())
    else:
        lines.append("Price per kWh: unknown.")

    if latitude is not None and longitude is not None:
        lines.append(f"Coordinates: latitude {latitude}, longitude {longitude}.")

    document_text = "\n".join(lines)

    metadata = {
        "provider": provider,
        "company": company,
        "output_key": output_key,
        "location_id": location_id,
        "location_name": location_name,
        "city": city,
        "address": address,
        "station_id": station_id,
        "station_identifier": station_identifier,
        "current_type": current_type,
        "station_status": station_status,
        "connector_types": connector_types_text,
        "price_per_kwh": float(price_per_kwh) if price_per_kwh is not None else -1.0,
        "currency": currency or "",
        "max_power_kw": float(max_power_kw) if max_power_kw is not None else -1.0,
        "latitude": float(latitude) if latitude is not None else 0.0,
        "longitude": float(longitude) if longitude is not None else 0.0,
    }

    return document_id, metadata, document_text


def load_station_documents(data_dir: Path) -> Tuple[List[str], List[Dict[str, Any]], List[str]]:
    ids: List[str] = []
    metadatas: List[Dict[str, Any]] = []
    documents: List[str] = []

    json_files = sorted(data_dir.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {data_dir.resolve()}")

    for json_file in json_files:
        print(f"Loading file: {json_file.name}")

        with json_file.open("r", encoding="utf-8") as f:
            payload = json.load(f)

        locations = payload.get("locations", [])
        print(f"  locations found: {len(locations)}")

        for location in locations:
            for station in location.get("stations", []):
                document_id, metadata, document_text = build_station_document(
                    company_root=payload,
                    location=location,
                    station=station
                )
                ids.append(document_id)
                metadatas.append(metadata)
                documents.append(document_text)

    print(f"\nTotal station documents created: {len(documents)}")
    return ids, metadatas, documents


def recreate_collection(db_path: Path, collection_name: str):
    chroma_client = chromadb.PersistentClient(path=str(db_path))

    existing = [c.name for c in chroma_client.list_collections()]
    if collection_name in existing:
        chroma_client.delete_collection(collection_name)

    collection = chroma_client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    return collection


def build_vector_db():
    ids, metadatas, documents = load_station_documents(DATA_DIR)

    print("\nGenerating embeddings...")
    embeddings = []
    for i, doc in enumerate(documents, start=1):
        emb = get_embedding(doc)
        embeddings.append(emb)

        if i % 25 == 0 or i == len(documents):
            print(f"  embedded {i}/{len(documents)}")

    print("\nCreating Chroma collection...")
    collection = recreate_collection(CHROMA_DIR, COLLECTION_NAME)

    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings
    )

    print(f"Done. Collection '{COLLECTION_NAME}' created with {len(documents)} documents.")


def search_vector_db(query: str, top_k: int = 5):
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = chroma_client.get_collection(COLLECTION_NAME)

    query_embedding = get_embedding(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    print("\n====================")
    print("QUERY")
    print("====================")
    print(query)

    print("\n====================")
    print("TOP RESULTS")
    print("====================")

    ids = results["ids"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]
    documents = results["documents"][0]

    for i, (doc_id, distance, metadata, document) in enumerate(
        zip(ids, distances, metadatas, documents),
        start=1
    ):
        similarity = 1 - distance

        print(f"\n{'=' * 40}")
        print(f"Result #{i}")
        print(f"{'=' * 40}")

        print_field("ID", doc_id)
        print_field("Similarity (approx)", f"{similarity:.4f}")
        print_field("Provider", metadata.get("provider"))
        print_field("Company", metadata.get("company"))
        print_field("City", metadata.get("city"))
        print_field("Location", metadata.get("location_name"))
        print_field("Address", metadata.get("address"))
        print_field("Station ID", metadata.get("station_id"))
        print_field("Current Type", metadata.get("current_type"))
        print_field("Connector Types", metadata.get("connector_types"))
        print_field("Max Power", metadata.get("max_power_kw"))
        print_field("Price/kWh", f"{metadata.get('price_per_kwh')} {metadata.get('currency')}")

        print_document_lines(document)
    for i, (doc_id, distance, metadata, document) in enumerate(zip(ids, distances, metadatas, documents), start=1):
        similarity = 1 - distance

        print(f"\nResult #{i}")
        print(f"ID: {doc_id}")
        print(f"Similarity (approx): {similarity:.4f}")
        print(f"Provider: {rtl(metadata.get('provider'))}")
        print(f"Company: {rtl(metadata.get('company'))}")
        print(f"City: {rtl(metadata.get('city'))}")
        print(f"Location: {rtl(metadata.get('location_name'))}")
        print(f"Address: {rtl(metadata.get('address'))}")
        print(f"Station ID: {metadata.get('station_id')}")
        print(f"Current Type: {metadata.get('current_type')}")
        print(f"Connector Types: {rtl(metadata.get('connector_types'))}")
        print(f"Max Power: {metadata.get('max_power_kw')}")
        print(f"Price/kWh: {metadata.get('price_per_kwh')} {metadata.get('currency')}")
        print("Document:")
        print(rtl(document))


if __name__ == "__main__":
    print("1) Build / rebuild vector DB")
    print("2) Search existing vector DB")
    choice = input("Choose option (1/2): ").strip()

    if choice == "1":
        build_vector_db()
    elif choice == "2":
        user_query = input("Enter your query: ").strip()
        top_k_input = input("Enter top_k (default 5): ").strip()
        top_k = int(top_k_input) if top_k_input else 5
        search_vector_db(user_query, top_k=top_k)
    else:
        print("Invalid choice.")