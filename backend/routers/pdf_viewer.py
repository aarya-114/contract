# routers/pdf_viewer.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from ..core.redis_client import get_pdf

router = APIRouter(prefix="/pdf", tags=["pdf"])


@router.get("/{session_id}")
def serve_pdf(session_id: str):
    """
    Serve the stored PDF file to the frontend viewer.
    Frontend calls this to render the actual PDF.
    """
    pdf_bytes = get_pdf(session_id)

    if not pdf_bytes:
        raise HTTPException(
            status_code=404,
            detail="PDF not found or expired. Please re-upload."
        )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "inline",
            "Access-Control-Allow-Origin": "*"
        }
    )