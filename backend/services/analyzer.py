# services/analyzer.py
from google import genai
from google.genai import types
import json
import re
from typing import Optional
from pydantic import BaseModel
from enum import Enum
from ..core.config import settings
from ..services.vector_store import find_similar_standard_clause
import time

# Configure Gemini with new SDK
client = genai.Client(api_key=settings.gemini_api_key)
MODEL = "gemini-2.0-flash"

# ─── OUTPUT SCHEMA ───

class RiskLevel(str, Enum):
    SAFE    = "safe"
    CAUTION = "caution"
    RISKY   = "risky"


class ClauseAnalysis(BaseModel):
    clause_index: int
    clause_number: Optional[str]
    clause_heading: Optional[str]
    clause_type: str
    risk_level: RiskLevel
    risk_reasoning: str
    plain_english: str
    negotiation_suggestion: Optional[str]
    similar_standard_clause: Optional[str]
    word_count: int


class ContractReport(BaseModel):
    total_clauses: int
    risky_count: int
    caution_count: int
    safe_count: int
    overall_risk_score: float
    overall_risk_label: str
    clauses: list[ClauseAnalysis]


ANALYSIS_PROMPT = """
You are a senior contract lawyer analyzing a legal clause for risk.

CLAUSE TO ANALYZE:
{clause_text}

SIMILAR STANDARD CLAUSE FOR REFERENCE:
{standard_clause}

Analyze this clause and respond with ONLY a valid JSON object.
No explanation before or after. Just the JSON.

JSON format:
{{
  "clause_type": "one of: payment, termination, confidentiality, liability, dispute_resolution, intellectual_property, security_deposit, force_majeure, governing_law, employment, general, other",
  "risk_level": "one of: safe, caution, risky",
  "risk_reasoning": "one clear sentence explaining WHY this risk level was assigned",
  "plain_english": "explain this clause in simple English a non-lawyer would understand, max 2 sentences",
  "negotiation_suggestion": "one specific thing to negotiate or null if clause is safe"
}}

Risk level guidelines:
- safe: standard clause, protects both parties fairly
- caution: slightly one-sided or missing standard protections
- risky: heavily one-sided, missing critical protections, or contains unusual terms

Be specific. Reference actual text from the clause in your reasoning.
"""


def analyze_clause(
    clause_text: str,
    clause_index: int,
    clause_number: Optional[str] = None,
    clause_heading: Optional[str] = None,
    word_count: int = 0
) -> ClauseAnalysis:

    # Step 1: RAG retrieval
    similar = find_similar_standard_clause(clause_text, n_results=1)
    standard_clause_text = "No similar standard clause found."
    similar_clause_label = None

    if similar:
        top_match = similar[0]
        if top_match["similarity_score"] > 0.4:
            standard_clause_text = top_match["text"]
            similar_clause_label = (
                f"{top_match['contract_type']} - "
                f"{top_match['clause_type']} "
                f"(similarity: {top_match['similarity_score']})"
            )

    # Step 2: Build prompt
    prompt = ANALYSIS_PROMPT.format(
        clause_text=clause_text[:2000],
        standard_clause=standard_clause_text
    )

    # Step 3: Call Gemini
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
            )
        raw_text = response.text.strip()
        # Step 4: Parse response
        parsed = _parse_ai_response(raw_text)

        return ClauseAnalysis(
            clause_index=clause_index,
            clause_number=clause_number,
            clause_heading=clause_heading,
            clause_type=parsed.get("clause_type", "general"),
            risk_level=RiskLevel(parsed.get("risk_level", "caution")),
            risk_reasoning=parsed.get("risk_reasoning", "Unable to determine"),
            plain_english=parsed.get("plain_english", clause_text[:200]),
            negotiation_suggestion=parsed.get("negotiation_suggestion"),
            similar_standard_clause=similar_clause_label,
            word_count=word_count
        )

    except Exception as e:
        print(f"⚠️ Analysis failed for clause {clause_index}: {e}")
        return ClauseAnalysis(
            clause_index=clause_index,
            clause_number=clause_number,
            clause_heading=clause_heading,
            clause_type="general",
            risk_level=RiskLevel.CAUTION,
            risk_reasoning=f"Analysis failed: {str(e)}",
            plain_english=clause_text[:200],
            negotiation_suggestion=None,
            similar_standard_clause=None,
            word_count=word_count
        )


def _parse_ai_response(raw_text: str) -> dict:
    raw_text = re.sub(r'```json\s*', '', raw_text)
    raw_text = re.sub(r'```\s*', '', raw_text)
    raw_text = raw_text.strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        pass

    start = raw_text.find('{')
    end = raw_text.rfind('}')

    if start != -1 and end != -1:
        try:
            return json.loads(raw_text[start:end + 1])
        except json.JSONDecodeError:
            pass

    print(f"⚠️ Could not parse AI response: {raw_text[:200]}")
    return {
        "clause_type": "general",
        "risk_level": "caution",
        "risk_reasoning": "Could not parse AI response",
        "plain_english": "Analysis unavailable",
        "negotiation_suggestion": None
    }


def calculate_risk_score(analyses: list[ClauseAnalysis]) -> tuple[float, str]:
    if not analyses:
        return 0.0, "Unknown"

    weights = {
        RiskLevel.SAFE:    0,
        RiskLevel.CAUTION: 1,
        RiskLevel.RISKY:   3
    }

    important_types = {
        "termination", "liability", "payment",
        "intellectual_property", "dispute_resolution"
    }

    total_score = 0
    max_possible = 0

    for analysis in analyses:
        base_weight = weights[analysis.risk_level]
        if analysis.clause_type in important_types:
            base_weight *= 2
        total_score += base_weight
        max_possible += 6

    if max_possible == 0:
        return 0.0, "Low"

    score = round((total_score / max_possible) * 100, 1)

    if score < 20:
        label = "Low"
    elif score < 40:
        label = "Medium"
    elif score < 65:
        label = "High"
    else:
        label = "Critical"

    return score, label


def analyze_contract(clauses: list) -> ContractReport:
    print(f"🔄 Analyzing {len(clauses)} clauses...")

    analyses = []
    for clause in clauses:
        print(f"  → Analyzing clause {clause.index + 1}/{len(clauses)}")
        analysis = analyze_clause(
            clause_text=clause.text,
            clause_index=clause.index,
            clause_number=clause.number,
            clause_heading=clause.heading,
            word_count=clause.word_count
        )
        analyses.append(analysis)

    risky_count   = sum(1 for a in analyses if a.risk_level == RiskLevel.RISKY)
    caution_count = sum(1 for a in analyses if a.risk_level == RiskLevel.CAUTION)
    safe_count    = sum(1 for a in analyses if a.risk_level == RiskLevel.SAFE)

    score, label = calculate_risk_score(analyses)

    print(f"✅ Analysis complete: {risky_count} risky, {caution_count} caution, {safe_count} safe")
    print(f"   Overall risk: {label} ({score})")

    return ContractReport(
        total_clauses=len(analyses),
        risky_count=risky_count,
        caution_count=caution_count,
        safe_count=safe_count,
        overall_risk_score=score,
        overall_risk_label=label,
        clauses=analyses
    )



def analyze_contract(clauses: list) -> ContractReport:
    print(f"🔄 Analyzing {len(clauses)} clauses...")

    analyses = []
    for clause in clauses:
        print(f"  → Analyzing clause {clause.index + 1}/{len(clauses)}")
        
        analysis = analyze_clause(
            clause_text=clause.text,
            clause_index=clause.index,
            clause_number=clause.number,
            clause_heading=clause.heading,
            word_count=clause.word_count
        )
        analyses.append(analysis)
        
        # Rate limiting — wait 4 seconds between each API call
        # Gemini free tier = 15 requests/minute = 1 per 4 seconds
        # This keeps us safely under the limit
        if clause.index < len(clauses) - 1:  # Don't wait after last clause
            time.sleep(4)

    risky_count   = sum(1 for a in analyses if a.risk_level == RiskLevel.RISKY)
    caution_count = sum(1 for a in analyses if a.risk_level == RiskLevel.CAUTION)
    safe_count    = sum(1 for a in analyses if a.risk_level == RiskLevel.SAFE)

    score, label = calculate_risk_score(analyses)

    print(f"✅ Analysis complete: {risky_count} risky, {caution_count} caution, {safe_count} safe")
    print(f"   Overall risk: {label} ({score})")

    return ContractReport(
        total_clauses=len(analyses),
        risky_count=risky_count,
        caution_count=caution_count,
        safe_count=safe_count,
        overall_risk_score=score,
        overall_risk_label=label,
        clauses=analyses
    )