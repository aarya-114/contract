# core/redis_client.py
import redis
from .config import settings

redis_client = redis.from_url(
    settings.redis_url,
    decode_responses=False  # ← Change to False to support binary (PDF bytes)
)

def get_redis():
    return redis_client


def store_pdf(session_id: str, file_bytes: bytes, ttl: int = 3600):
    """
    Store PDF bytes in Redis with 1 hour TTL.
    Used for serving PDF to frontend viewer.
    """
    redis_client.setex(f"pdf:{session_id}", ttl, file_bytes)


def get_pdf(session_id: str) -> bytes:
    """Retrieve PDF bytes from Redis."""
    return redis_client.get(f"pdf:{session_id}")