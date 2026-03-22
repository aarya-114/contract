# services/vector_store.py
from typing import List, Optional
from .embedder import embed_text, embed_texts
from ..core.chroma_client import (
    get_or_create_knowledge_base,
    get_or_create_active_contract,
    clear_active_contract,
    KNOWLEDGE_BASE_COLLECTION,
    ACTIVE_CONTRACT_COLLECTION
)
from .segmenter import Clause


def load_knowledge_base(templates: List[dict]) -> int:
    """
    Load standard contract templates into ChromaDB.

    templates format:
    [
        {
            "id": "nda_payment_1",
            "text": "Payment shall be made within 30 days...",
            "contract_type": "NDA",
            "clause_type": "payment"
        }
    ]

    Returns number of chunks loaded.

    Why check existing count first?
    → Don't re-embed on every restart
    → Embedding costs money
    → If already loaded, skip
    """
    collection = get_or_create_knowledge_base()

    # Check if already loaded
    existing = collection.count()
    if existing > 0:
        print(f"✅ Knowledge base already loaded: {existing} chunks")
        return existing

    if not templates:
        print("⚠️ No templates provided to load")
        return 0

    # Prepare for batch embedding
    ids = [t["id"] for t in templates]
    texts = [t["text"] for t in templates]
    metadatas = [
        {
            "contract_type": t.get("contract_type", "unknown"),
            "clause_type": t.get("clause_type", "unknown"),
            "source": "knowledge_base"
        }
        for t in templates
    ]

    # Embed all at once
    print(f"🔄 Embedding {len(texts)} knowledge base chunks...")
    embeddings = embed_texts(texts)

    # Store in ChromaDB
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )

    print(f"✅ Knowledge base loaded: {len(texts)} chunks")
    return len(texts)


def store_contract_clauses(clauses: List[Clause]) -> int:
    """
    Store uploaded contract clauses in active collection.
    Clears previous contract first.

    Returns number of clauses stored.
    """
    # Clear previous contract
    collection = clear_active_contract()

    if not clauses:
        return 0

    # Prepare data
    ids = [f"clause_{c.index}" for c in clauses]
    texts = [c.text for c in clauses]
    metadatas = [
        {
            "index": c.index,
            "heading": c.heading or "",
            "number": c.number or "",
            "word_count": c.word_count,
            "source": "active_contract"
        }
        for c in clauses
    ]

    # Embed all clauses
    print(f"🔄 Embedding {len(clauses)} contract clauses...")
    embeddings = embed_texts(texts)

    # Store
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )

    print(f"✅ Stored {len(clauses)} clauses in active contract")
    return len(clauses)


def find_similar_standard_clause(
    clause_text: str,
    n_results: int = 3
) -> List[dict]:
    """
    Given a clause from the uploaded contract,
    find the most similar clauses in knowledge base.

    This is the RAG retrieval step.

    Returns list of similar clauses with similarity scores.
    """
    collection = get_or_create_knowledge_base()

    # Check knowledge base has content
    if collection.count() == 0:
        return []

    # Embed the query clause
    query_embedding = embed_text(clause_text)

    # Search ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas", "distances"]
    )

    if not results["documents"][0]:
        return []

    # Format results
    similar_clauses = []
    for i, (doc, meta, distance) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    )):
        # Convert distance to similarity score
        # ChromaDB returns L2 distance by default
        # Lower distance = more similar
        # Convert to 0-1 score where 1 = identical
        similarity = round(1 / (1 + distance), 3)

        similar_clauses.append({
            "text": doc,
            "contract_type": meta.get("contract_type"),
            "clause_type": meta.get("clause_type"),
            "similarity_score": similarity
        })

    return similar_clauses


def get_knowledge_base_stats() -> dict:
    """How many chunks are in the knowledge base."""
    collection = get_or_create_knowledge_base()
    return {
        "total_chunks": collection.count(),
        "collection_name": KNOWLEDGE_BASE_COLLECTION
    }