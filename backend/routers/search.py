# routers/search.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..services.vector_store import find_similar_standard_clause

router = APIRouter(prefix="/search", tags=["search"])


class SearchRequest(BaseModel):
    clause_text: str
    n_results: int = 3


@router.post("/similar")
def find_similar(request: SearchRequest):
    """
    Given any clause text, find similar
    clauses in the knowledge base.

    This tests that RAG retrieval is working
    before we wire it into the full analysis.
    """
    if not request.clause_text.strip():
        raise HTTPException(
            status_code=400,
            detail="clause_text cannot be empty"
        )

    results = find_similar_standard_clause(
        clause_text=request.clause_text,
        n_results=request.n_results
    )

    return {
        "query": request.clause_text[:100] + "...",
        "similar_clauses": results
    }