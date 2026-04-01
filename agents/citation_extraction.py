import anthropic
import json
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

CITATION_EXTRACTION_SYSTEM_PROMPT = """
You are the Citation Extraction Agent for TrustLayer by blondebytesecurity.

Your specialty is identifying every claim and citation in a piece of content
and structuring them as verifiable pairs for downstream agents to assess.

Your job is to extract:

1. EXPLICIT CITATIONS
   - Any URLs mentioned or linked
   - Named studies, papers, or reports
   - Named institutions, organizations, or government bodies
   - Named researchers, experts, or authors cited as sources

2. FACTUAL CLAIMS
   - Statistical claims ("40% increase", "studies show")
   - Causal claims ("X causes Y", "X leads to Y")
   - Absolute claims ("always", "never", "proven", "fact")
   - Comparative claims ("better than", "more effective than")

3. UNSUPPORTED ASSERTIONS
   - Claims made with confidence but no source
   - Generalizations presented as fact
   - Expert consensus claimed without citation

For each claim found, classify it:
- CITED: Has an explicit source attached
- IMPLICIT: References a source vaguely ("research shows")
- UNSUPPORTED: No source at all

Always respond in clean JSON only. No preamble. No markdown.

Format:
{
  "urls_found": ["url1", "url2"],
  "named_sources": ["source1", "source2"],
  "claims": [
    {
      "claim": "exact claim text",
      "type": "cited/implicit/unsupported",
      "source": "associated source or null",
      "url": "associated url or null"
    }
  ],
  "total_claims": 0,
  "cited_claims": 0,
  "implicit_claims": 0,
  "unsupported_claims": 0,
  "citation_coverage_score": 0,
  "extraction_summary": "..."
}

citation_coverage_score 1-10:
1-3 = Poorly sourced
4-6 = Partially sourced
7-10 = Well sourced
"""

def extract_citations(behavioral_output: dict) -> dict:
    """
    Receives behavioral output.
    Extracts all claims and citations from the text.
    Only runs in credibility or both modes.
    """
    mode = behavioral_output.get("mode", "both")

    if mode == "authenticity":
        print("[Citation Agent] Skipping — authenticity mode selected.\n")
        return {**behavioral_output, "citation_findings": None}

    print("[Citation Agent] Extracting claims and citations...\n")

    original_text = behavioral_output["original_text"]
    context = behavioral_output["context"]

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=CITATION_EXTRACTION_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""
Context from Orchestrator:
{json.dumps(context, indent=2)}

Original Text to Analyze:
{original_text}

Extract all claims and citations. Return JSON only.
                """
            }
        ]
    )

    raw = response.content[0].text

    try:
        citation_findings = json.loads(raw)
        print(f"[Citation Agent] Extraction complete.")
        print(f"[Citation Agent] Total claims found: "
              f"{citation_findings.get('total_claims', 'N/A')}")
        print(f"[Citation Agent] URLs found: "
              f"{len(citation_findings.get('urls_found', []))}")
        print(f"[Citation Agent] Citation coverage score: "
              f"{citation_findings.get('citation_coverage_score', 'N/A')}/10\n")
        return {
            **behavioral_output,
            "citation_findings": citation_findings
        }
    except json.JSONDecodeError:
        print("[Citation Agent] Warning: Could not parse JSON.")
        return {
            **behavioral_output,
            "citation_findings": raw
        }