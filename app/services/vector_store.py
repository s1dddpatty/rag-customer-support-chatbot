import os
import chromadb
from chromadb.config import Settings

from app.core.config import settings


def get_chroma_client():
    try:
        client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
            settings=Settings(
                anonymized_telemetry=False
            )
        )
        client.heartbeat()
        return client
    except Exception:
        os.makedirs("./chroma_data", exist_ok=True)
        return chromadb.PersistentClient(
            path="./chroma_data",
            settings=Settings(
                anonymized_telemetry=False
            )
        )


def get_document_collection():
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name=settings.chroma_collection_name
    )
    return collection
