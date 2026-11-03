import requests

OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text:latest"

_fallback_fn = None


def get_fallback_embedding(text: str):
    global _fallback_fn
    if _fallback_fn is None:
        from chromadb.utils import embedding_functions
        _fallback_fn = embedding_functions.DefaultEmbeddingFunction()
    emb = _fallback_fn([text])[0]
    return emb.tolist() if hasattr(emb, "tolist") else list(emb)


def get_embedding(text: str):
    try:
        response = requests.post(
            OLLAMA_EMBED_URL,
            json={
                "model": EMBED_MODEL,
                "prompt": text
            },
            timeout=2
        )
        if response.status_code == 200:
            data = response.json()
            return data["embedding"]
    except Exception:
        pass

    return get_fallback_embedding(text)
