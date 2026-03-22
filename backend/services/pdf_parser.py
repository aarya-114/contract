# services/pdf_parser.py
import fitz  # PyMuPDF
import re
from pathlib import Path


class PDFParseResult:
    """
    Result of parsing a PDF file.
    Always check is_valid before using text.
    """
    def __init__(
        self,
        text: str,
        page_count: int,
        is_scanned: bool,
        is_valid: bool,
        warning: str = None
    ):
        self.text = text
        self.page_count = page_count
        self.is_scanned = is_scanned
        self.is_valid = is_valid
        self.warning = warning

    def __repr__(self):
        return (
            f"PDFParseResult("
            f"pages={self.page_count}, "
            f"chars={len(self.text)}, "
            f"scanned={self.is_scanned}, "
            f"valid={self.is_valid})"
        )


def parse_pdf(file_bytes: bytes) -> PDFParseResult:
    """
    Main entry point. Takes raw PDF bytes, returns PDFParseResult.

    Why bytes not filepath?
    → File comes from HTTP upload as bytes
    → No need to save to disk first
    → Faster and cleaner
    """
    try:
        # Open PDF from bytes (not file path)
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        page_count = len(doc)

        if page_count == 0:
            return PDFParseResult(
                text="",
                page_count=0,
                is_scanned=False,
                is_valid=False,
                warning="PDF has no pages"
            )

        # Extract text from all pages
        raw_text = _extract_text(doc)

        # Check if scanned (image-based PDF)
        is_scanned = _is_scanned_pdf(raw_text, page_count)

        if is_scanned:
            return PDFParseResult(
                text="",
                page_count=page_count,
                is_scanned=True,
                is_valid=False,
                warning="This PDF appears to be scanned. Please upload a text-based PDF."
            )

        # Clean the extracted text
        cleaned_text = _clean_text(raw_text)

        # Check if enough content was extracted
        if len(cleaned_text.strip()) < 100:
            return PDFParseResult(
                text=cleaned_text,
                page_count=page_count,
                is_scanned=False,
                is_valid=False,
                warning="Could not extract enough text from this PDF"
            )

        return PDFParseResult(
            text=cleaned_text,
            page_count=page_count,
            is_scanned=False,
            is_valid=True
        )

    except Exception as e:
        return PDFParseResult(
            text="",
            page_count=0,
            is_scanned=False,
            is_valid=False,
            warning=f"Failed to parse PDF: {str(e)}"
        )


def _extract_text(doc: fitz.Document) -> str:
    """
    Extract text from all pages.

    Why "text" mode not "blocks" or "words"?
    → "text" preserves reading order best
    → Good enough for contracts which are
      mostly single column
    """
    pages_text = []

    for page_num, page in enumerate(doc):
        page_text = page.get_text("text")
        if page_text.strip():
            pages_text.append(page_text)

    return "\n".join(pages_text)


def _is_scanned_pdf(text: str, page_count: int) -> bool:
    """
    Detect if PDF is scanned (image-based).

    Logic:
    → If very few characters per page, likely scanned
    → Real contracts have hundreds of words per page
    → Threshold: less than 100 chars per page = scanned
    """
    if page_count == 0:
        return False

    chars_per_page = len(text.strip()) / page_count
    return chars_per_page < 100


def _clean_text(text: str) -> str:
    """
    Clean extracted text for AI processing.

    Each step explained:
    """
    # Remove null bytes and weird control characters
    text = text.replace('\x00', '').replace('\x0c', '\n')

    # Normalize different types of whitespace to regular space
    text = re.sub(r'[ \t]+', ' ', text)

    # Maximum 2 consecutive newlines (remove excessive blank lines)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Remove page numbers (standalone numbers on a line)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)

    # Remove common header/footer patterns
    text = re.sub(r'Page \d+ of \d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'CONFIDENTIAL', '', text, flags=re.IGNORECASE)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def get_text_coordinates(file_bytes: bytes, search_text: str, page_num: int = None):
    """
    Find where a piece of text appears in the PDF.
    Returns list of {page, rect} objects.
    
    rect = [x0, y0, x1, y1] — bounding box coordinates
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    results = []
    
    pages_to_search = range(len(doc)) if page_num is None else [page_num]
    
    for i in pages_to_search:
        page = doc[i]
        # search_for returns list of rectangles where text was found
        rects = page.search_for(search_text)
        for rect in rects:
            results.append({
                "page": i,
                "rect": [rect.x0, rect.y0, rect.x1, rect.y1]
            })
    
    return results

def find_clause_location(file_bytes: bytes, clause_text: str):
    """
    Find where a clause starts in the PDF.
    Uses first sentence (up to 10 words) as search query.
    Returns page number and coordinates.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    
    # Get first meaningful line of clause
    # Skip heading line, get first content line
    lines = [l.strip() for l in clause_text.split('\n') if l.strip()]
    
    # Try progressively shorter search strings until we find a match
    search_text = None
    for line in lines[1:]:  # Skip heading
        if len(line.split()) >= 6:  # At least 6 words
            # Take first 8 words
            words = line.split()[:8]
            search_text = ' '.join(words)
            break
    
    if not search_text:
        return None
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        rects = page.search_for(search_text)
        if rects:
            return {
                "page": page_num,
                "rect": [rects[0].x0, rects[0].y0, rects[0].x1, rects[0].y1],
                "search_text": search_text
            }
    
    return None

def find_clause_locations(file_bytes: bytes, clauses: list) -> list:
    """
    For each clause, find its location in the PDF.
    Returns list of highlight objects with coordinates.
    
    Strategy:
    → Take first meaningful line of clause text
    → Search PDF page by page
    → Return page number + coordinates
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    highlights = []

    for clause in clauses:
        location = _find_clause_in_pdf(doc, clause.text)
        if location:
            highlights.append({
                "clause_index": clause.index,
                "clause_number": clause.number,
                "clause_heading": clause.heading,
                "page": location["page"],
                "rect": location["rect"],
                "search_text": location["search_text"]
            })

    doc.close()
    return highlights


def _find_clause_in_pdf(doc, clause_text: str) -> dict:
    """
    Find where a clause starts in the PDF.
    Tries progressively shorter search strings.
    """
    # Clean the text and split into lines
    lines = [l.strip() for l in clause_text.split('\n') if l.strip()]

    # Build search candidates
    # Skip very short lines and headings (ALL CAPS)
    candidates = []
    for line in lines:
        words = line.split()
        # Skip if too short
        if len(words) < 5:
            continue
        # Skip ALL CAPS headings
        if line.isupper():
            continue
        # Take first 8 words as search string
        candidates.append(' '.join(words[:8]))

    # Try each candidate
    for search_text in candidates[:3]:  # Max 3 attempts per clause
        for page_num in range(len(doc)):
            page = doc[page_num]
            rects = page.search_for(search_text)
            if rects:
                return {
                    "page": page_num,
                    "rect": [
                        rects[0].x0,
                        rects[0].y0,
                        rects[0].x1,
                        rects[0].y1
                    ],
                    "search_text": search_text
                }

    return None