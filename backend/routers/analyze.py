# routers/analyze.py
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from rich.diagnose import report
from ..services.pdf_parser import parse_pdf, find_clause_locations
from ..services.segmenter import segment_contract
from ..services.vector_store import store_contract_clauses
from ..services.analyzer import analyze_contract
from ..core.redis_client import store_pdf
from fastapi.responses import StreamingResponse
import asyncio

router = APIRouter(prefix="/analyze", tags=["analyze"])

MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("/")
async def analyze_contract_endpoint(file: UploadFile = File(...)):
    """
    Full pipeline:
    PDF → parse → segment → embed → analyze → highlights → report
    """

    if file.content_type not in ["application/pdf", "application/octet-stream"]:
        raise HTTPException(status_code=400, detail="Only PDFs allowed")

    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB")

    # Step 1: Parse PDF
    parse_result = parse_pdf(file_bytes)
    if not parse_result.is_valid:
        raise HTTPException(status_code=422, detail=parse_result.warning)

    # Step 2: Segment clauses
    clauses = segment_contract(parse_result.text)
    if not clauses:
        raise HTTPException(
            status_code=422,
            detail="Could not extract clauses from this contract"
        )

    # Step 3: Store PDF in Redis for viewer
    session_id = str(uuid.uuid4())
    store_pdf(session_id, file_bytes)

    # Step 4: Store clauses in ChromaDB
    store_contract_clauses(clauses)

    # Step 5: AI Analysis
    report = analyze_contract(clauses)

    # Step 6: Find clause locations in PDF for highlighting
    print("🔄 Finding clause locations in PDF...")
    highlights = find_clause_locations(file_bytes, clauses)
    print(f"✅ Found locations for {len(highlights)}/{len(clauses)} clauses")

    # Step 7: Add risk levels to highlights
    # Map clause_index → risk_level from report
    risk_map = {
        c.clause_index: c.risk_level
        for c in report.clauses
    }

    for h in highlights:
        h["risk_level"] = risk_map.get(h["clause_index"], "caution")

    # Return report + session_id + highlights
    return {
        "session_id": session_id,
        "pdf_url": f"/pdf/{session_id}",
        "highlights": highlights,
        **report.dict()
    }

@router.post("/stream")
async def analyze_stream(file: UploadFile = File(...)):
    """
    Same as /analyze but streams progress updates.
    Frontend shows real-time clause-by-clause progress.
    """
    async def generate():
        # Parse
        yield f"data: {json.dumps({'status': 'parsing', 'message': 'Reading PDF...'})}\n\n"
        
        file_bytes = await file.read()
        parse_result = parse_pdf(file_bytes)
        
        if not parse_result.is_valid:
            yield f"data: {json.dumps({'status': 'error', 'message': parse_result.warning})}\n\n"
            return

        # Segment
        yield f"data: {json.dumps({'status': 'segmenting', 'message': 'Extracting clauses...'})}\n\n"
        clauses = segment_contract(parse_result.text)
        yield f"data: {json.dumps({'status': 'segmented', 'message': f'Found {len(clauses)} clauses'})}\n\n"

        # Store
        session_id = str(uuid.uuid4())
        store_pdf(file_bytes, session_id)
        store_contract_clauses(clauses)

        # Analyze clause by clause with progress
        analyses = []
        for clause in clauses:
            yield f"data: {json.dumps({'status': 'analyzing', 'current': clause.index + 1, 'total': len(clauses), 'message': f'Analyzing clause {clause.index + 1} of {len(clauses)}...'})}\n\n"
            
            analysis = analyze_clause(
                clause_text=clause.text,
                clause_index=clause.index,
                clause_number=clause.number,
                clause_heading=clause.heading,
                word_count=clause.word_count
            )
            analyses.append(analysis)
            
            if clause.index < len(clauses) - 1:
                await asyncio.sleep(2)

        # Build report
        yield f"data: {json.dumps({'status': 'finishing', 'message': 'Building report...'})}\n\n"
        
        # ... rest of report building
        yield f"data: {json.dumps({'status': 'done', 'report': report.dict()})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")