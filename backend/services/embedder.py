# services/embedder.py
from sentence_transformers import SentenceTransformer
from typing import List

# Load model once when module is imported
# all-MiniLM-L6-v2:
# → 384 dimensions (vs OpenAI's 1536)
# → 80MB download on first run
# → Fast, good quality, free
print("🔄 Loading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ Embedding model loaded")


def embed_text(text: str) -> List[float]:
    """
    Convert single text to vector.
    Returns list of 384 floats.
    
    Identical interface to OpenAI version —
    rest of codebase doesn't need to change.
    """
    # Truncate if too long
    # all-MiniLM-L6-v2 max: 256 tokens
    # ~1000 chars is safe
    text = text[:1000]
    
    embedding = model.encode(text)
    return embedding.tolist()


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Embed multiple texts at once.
    sentence-transformers handles batching internally.
    Actually faster than calling embed_text in a loop.
    """
    # Truncate each
    truncated = [t[:1000] for t in texts]
    
    embeddings = model.encode(truncated)
    return embeddings.tolist()
