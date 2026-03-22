from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.redis_client import redis_client
from .routers import upload, search, analyze, pdf_viewer
from .services.vector_store import load_knowledge_base, get_knowledge_base_stats
from .knowledge_base.templates import STANDARD_TEMPLATES

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)


@app.on_event("startup")
async def startup():
    # Check Redis
    try:
        redis_client.ping()
        print("✅ Redis connected")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")

    # Load knowledge base into ChromaDB
    try:
        count = load_knowledge_base(STANDARD_TEMPLATES)
        print(f"✅ Knowledge base ready: {count} chunks")
    except Exception as e:
        print(f"❌ Knowledge base failed: {e}")


@app.get("/health")
def health_check():
    try:
        redis_client.ping()
        redis_status = "connected"
    except:
        redis_status = "disconnected"

    kb_stats = get_knowledge_base_stats()

    return {
        "status": "running",
        "version": settings.app_version,
        "redis": redis_status,
        "knowledge_base_chunks": kb_stats["total_chunks"]
    }


@app.get("/")
def root():
    return {
        "message": "Welcome to ContractSense API",
        "docs": "/docs"
    }


app.include_router(upload.router)
app.include_router(search.router)  
app.include_router(upload.router)
app.include_router(search.router)
app.include_router(analyze.router)  

app.include_router(pdf_viewer.router)