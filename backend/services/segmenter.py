# services/segmenter.py
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class Clause:
    index: int
    text: str
    heading: Optional[str] = None
    number: Optional[str] = None
    word_count: int = 0

    def __post_init__(self):
        self.word_count = len(self.text.split())

    def is_substantial(self) -> bool:
        return self.word_count >= 15

    def is_too_long(self) -> bool:
        return self.word_count > 500


def segment_contract(text: str) -> List[Clause]:
    """
    Smart segmentation with quality over quantity.

    Strategy priority (high to low):
    1. Article style   (ARTICLE-1, ARTICLE-2)
    2. Decimal nums    (1.1, 1.2, 2.0, 3.5)
    3. Simple nums     (1. 2. 3.)
    4. Lettered        ((a) (b) (c))
    5. Caps headings   (PAYMENT TERMS)
    6. Paragraphs      (last resort)

    Key insight: We don't pick "most clauses"
    We pick highest priority strategy that gives
    at least 3 substantial clauses.
    """
    if not text or not text.strip():
        return []

    # Ordered by quality — stop at first that works
    strategies = [
        ("article",    _segment_by_article_style),
        ("decimal",    _segment_by_decimal_numbering),
        ("simple",     _segment_by_simple_numbering),
        ("lettered",   _segment_by_lettered_sections),
        ("caps",       _segment_by_caps_headings),
        ("paragraphs", _segment_by_paragraphs),
    ]

    for strategy_name, strategy_fn in strategies:
        clauses = strategy_fn(text)
        clauses = [c for c in clauses if c.is_substantial()]

        if len(clauses) >= 3:
            # Sub-split anything too long
            final_clauses = []
            for clause in clauses:
                if clause.is_too_long():
                    sub = _sub_split_long_clause(clause)
                    final_clauses.extend(sub)
                else:
                    final_clauses.append(clause)

            # Re-index
            for i, c in enumerate(final_clauses):
                c.index = i

            return final_clauses

    return []


def _segment_by_article_style(text: str) -> List[Clause]:
    """
    NOW also detects Annexure boundaries:
    ARTICLE—1, ARTICLE—2, Annexure—I, Annexure—II
    """
    # Extended pattern to include Annexure
    pattern = r'(?:^|\n)((?:ARTICLE|Annexure)[\s\u2014\-]*[\dIVXivx]+[^\n]*)\n'
    matches = list(re.finditer(pattern, text, re.IGNORECASE))

    if len(matches) < 2:
        return []

    clauses = []
    for i, match in enumerate(matches):
        heading = _clean_heading(match.group(1))

        text_start = match.end()
        text_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        body = text[text_start:text_end].strip()

        if body:
            clauses.append(Clause(
                index=i,
                text=f"{heading}\n{body}",
                heading=heading,
                number=str(i + 1)
            ))

    return clauses



def _segment_by_decimal_numbering(text: str) -> List[Clause]:
    """
    Matches:
    1.0 Definition of terms
    1.1 The Contract shall mean...
    2.3 The vendor shall...

    Common in formal contracts and
    government tenders in India.

    NOT matched:
    - 1.1.1 (too deep)
    - "within 2.5 days" (number in sentence)
    """
    # Must be at line start
    # Must be X.Y format (not X.Y.Z)
    # Must be followed by space then content
    pattern = r'(?:^|\n)(\d{1,2}\.\d{1,2})\s+(?=\S)'
    matches = list(re.finditer(pattern, text))

    if len(matches) < 3:
        return []

    clauses = []
    for i, match in enumerate(matches):
        number = match.group(1).strip()

        text_start = match.end()
        text_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        raw = text[text_start:text_end].strip()
        heading, body = _extract_heading_from_text(raw)
        full_text = f"{heading}\n{body}" if heading else raw

        if full_text.strip():
            clauses.append(Clause(
                index=i,
                text=full_text,
                heading=heading,
                number=number
            ))

    return clauses


def _segment_by_simple_numbering(text: str) -> List[Clause]:
    """
    Matches:
    1. Payment Terms
    2. Confidentiality
    3. Termination

    Strict — only at line start followed by
    capital letter to avoid false matches.
    """
    pattern = r'(?:^|\n)(\d+\.)\s+(?=[A-Z])'
    matches = list(re.finditer(pattern, text))

    if len(matches) < 3:
        return []

    clauses = []
    for i, match in enumerate(matches):
        number = match.group(1).strip()

        text_start = match.end()
        text_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        raw = text[text_start:text_end].strip()
        heading, body = _extract_heading_from_text(raw)
        full_text = f"{heading}\n{body}" if heading else raw

        if full_text.strip():
            clauses.append(Clause(
                index=i,
                text=full_text,
                heading=heading,
                number=number
            ))

    return clauses


def _segment_by_lettered_sections(text: str) -> List[Clause]:
    """
    Matches:
    (a) The vendor shall...
    (b) Payment must be...
    a) First condition
    b) Second condition
    """
    pattern = r'(?:^|\n)\s*\(?([a-z])\)\s+'
    matches = list(re.finditer(pattern, text))

    if len(matches) < 3:
        return []

    clauses = []
    for i, match in enumerate(matches):
        number = f"({match.group(1)})"
        text_start = match.end()
        text_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[text_start:text_end].strip()

        if body:
            clauses.append(Clause(
                index=i,
                text=body,
                heading=None,
                number=number
            ))

    return clauses


def _segment_by_caps_headings(text: str) -> List[Clause]:
    """
    Matches standalone ALL CAPS headings:
    PAYMENT TERMS
    CONFIDENTIALITY
    TERMINATION
    """
    pattern = r'(?:^|\n)([A-Z][A-Z\s\-]{2,})\n(?=[A-Za-z])'
    matches = list(re.finditer(pattern, text))

    if len(matches) < 3:
        return []

    clauses = []
    for i, match in enumerate(matches):
        heading = _clean_heading(match.group(1))
        text_start = match.end()
        text_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[text_start:text_end].strip()

        if body:
            clauses.append(Clause(
                index=i,
                text=f"{heading}\n{body}",
                heading=heading,
                number=None
            ))

    return clauses


def _segment_by_paragraphs(text: str) -> List[Clause]:
    """
    Last resort only.
    Split by blank lines between paragraphs.
    """
    paragraphs = re.split(r'\n\s*\n', text)
    clauses = []

    for i, para in enumerate(paragraphs):
        para = para.strip()
        if para:
            heading, body = _extract_heading_from_text(para)
            full_text = f"{heading}\n{body}" if heading else para
            clauses.append(Clause(
                index=i,
                text=full_text,
                heading=heading,
                number=None
            ))

    return clauses


def _sub_split_long_clause(clause: Clause) -> List[Clause]:
    """
    Split clauses over 500 words into chunks.
    Preserves heading on first chunk only.
    """
    paragraphs = re.split(r'\n\s*\n', clause.text)
    sub_clauses = []
    current_chunk = []
    current_words = 0
    chunk_index = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        para_words = len(para.split())

        if current_words + para_words > 500 and current_chunk:
            sub_clauses.append(Clause(
                index=chunk_index,
                text='\n\n'.join(current_chunk),
                heading=clause.heading if chunk_index == 0 else None,
                # FIX: use letter suffix not number
                # "7a", "7b" instead of "7.5", "7.6"
                number=f"{clause.number}{chr(97 + chunk_index)}" if clause.number else None
            ))
            chunk_index += 1
            current_chunk = [para]
            current_words = para_words
        else:
            current_chunk.append(para)
            current_words += para_words

    if current_chunk:
        sub_clauses.append(Clause(
            index=chunk_index,
            text='\n\n'.join(current_chunk),
            heading=clause.heading if chunk_index == 0 else None,
            number=f"{clause.number}{chr(97 + chunk_index)}" if clause.number else None
        ))

    return sub_clauses if sub_clauses else [clause]


def _extract_heading_from_text(text: str) -> Tuple[Optional[str], str]:
    """
    Check if first line looks like a heading.
    Returns (heading, body) tuple.
    """
    lines = text.split('\n')
    if not lines:
        return None, text

    first_line = lines[0].strip()
    rest = '\n'.join(lines[1:]).strip()

    is_heading = (
        len(first_line) <= 80 and
        len(first_line.split()) <= 8 and
        not first_line.endswith(',') and
        not first_line.endswith(';') and
        not first_line.endswith('.') and
        (first_line.isupper() or first_line.istitle()) and
        bool(rest)  # Must have body text after it
    )

    if is_heading:
        return _clean_heading(first_line), rest

    return None, text


def _clean_heading(heading: str) -> str:
    heading = heading.rstrip('.-:\u2014')
    heading = re.sub(r'[\u2014\-]', ' ', heading)
    heading = re.sub(r'\s+', ' ', heading)
    return heading.strip()


def get_segmentation_stats(clauses: List[Clause]) -> dict:
    if not clauses:
        return {"total": 0}

    word_counts = [c.word_count for c in clauses]

    return {
        "total_clauses": len(clauses),
        "total_words": sum(word_counts),
        "avg_words_per_clause": round(sum(word_counts) / len(clauses)),
        "shortest_clause_words": min(word_counts),
        "longest_clause_words": max(word_counts),
        "clauses_with_headings": sum(1 for c in clauses if c.heading),
        "clauses_with_numbers": sum(1 for c in clauses if c.number),
    }


# ## What Changed
# ```
# BEFORE: Run all strategies, pick most clauses
#         → Paragraphs won with 167 chunks (wrong)

# AFTER:  Priority order, stop at first that works
#         → Article style runs first
#         → Finds ARTICLE—1 through ARTICLE—7
#         → Gets 7 high quality sections
#         → Each section sub-splits if > 500 words
#         → Result: ~30-40 meaningful clauses