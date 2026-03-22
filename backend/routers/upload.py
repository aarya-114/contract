# routers/upload.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from ..services.pdf_parser import parse_pdf
from ..services.segmenter import segment_contract, get_segmentation_stats

router = APIRouter(prefix="/upload", tags=["upload"])

MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_TYPES = ["application/pdf", "application/octet-stream"]


@router.post("/")
async def upload_contract(file: UploadFile = File(...)):
    """
    Upload contract PDF.
    Returns extracted text AND segmented clauses.
    """

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Only PDFs allowed."
        )

    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 10MB."
        )

    # Step 1: Parse PDF
    parse_result = parse_pdf(file_bytes)

    if not parse_result.is_valid:
        raise HTTPException(
            status_code=422,
            detail=parse_result.warning
        )

    # Step 2: Segment into clauses
    clauses = segment_contract(parse_result.text)

    if not clauses:
        raise HTTPException(
            status_code=422,
            detail="Could not extract clauses from this contract. "
                   "Please ensure it is a standard formatted contract."
        )

    # Step 3: Get stats
    stats = get_segmentation_stats(clauses)

    return {
        "success": True,
        "filename": file.filename,
        "page_count": parse_result.page_count,
        "stats": stats,
        "clauses": [
            {
                "index": c.index,
                "number": c.number,
                "heading": c.heading,
                "text": c.text,
                "word_count": c.word_count
            }
            for c in clauses
        ]
    }