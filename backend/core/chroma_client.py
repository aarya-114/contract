# core/chroma_client.py
import chromadb
from chromadb.config import Settings as ChromaSettings
from .config import settings

# Single ChromaDB client for entire app
# PersistentClient saves to disk automatically
chroma_client = chromadb.PersistentClient(
    path=settings.chroma_persist_dir
)

# Collection names as constants
# Never hardcode strings in multiple places
KNOWLEDGE_BASE_COLLECTION = "knowledge_base"
ACTIVE_CONTRACT_COLLECTION = "active_contract"


def get_or_create_knowledge_base():
    """
    Get knowledge base collection.
    Creates it if doesn't exist.
    This collection is PERMANENT — never deleted.
    """
    return chroma_client.get_or_create_collection(
        name=KNOWLEDGE_BASE_COLLECTION,
        metadata={"description": "Standard contract templates"}
    )


def get_or_create_active_contract():
    """
    Get active contract collection.
    Creates it if doesn't exist.
    This collection is TEMPORARY — cleared per upload.
    """
    return chroma_client.get_or_create_collection(
        name=ACTIVE_CONTRACT_COLLECTION,
        metadata={"description": "Current contract being analyzed"}
    )


def clear_active_contract():
    """
    Delete and recreate active contract collection.
    Called every time a new contract is uploaded.

    Why delete + recreate instead of just deleting docs?
    → Cleaner — guaranteed fresh state
    → No risk of stale vectors from previous contract
    """
    try:
        chroma_client.delete_collection(ACTIVE_CONTRACT_COLLECTION)
    except Exception:
        pass  # Collection might not exist yet — that's fine

    return chroma_client.create_collection(
        name=ACTIVE_CONTRACT_COLLECTION,
        metadata={"description": "Current contract being analyzed"}
    )