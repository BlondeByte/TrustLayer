import anthropic
import json
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

RELEVANCE_SYSTEM_PROMPT = """
You are the Relevance Agent for TrustLayer by blondebytesecurity.

You are the intelligence layer of the credibility chain.

Your specialty is deep reasoning about whether cited sources
actually support the claims they are attached to.

This is not about whether a source is credible in general.
This is about whether THIS source supports THIS claim.

A source can be:
- Real and credible but completely irrelevant to the claim
- Real and relevant but actually contradicting the claim
- Real, relevant, and genuinely supporting the claim
- Unreachable and therefore unverifiable

You will receive:
- The original text
- Extracted claims and their sources
- Web fetch assessments of each URL

Your job is to reason carefully about each claim-source pair and deliver
a relevance verdict that a non-technical reader can understand.

Classify each claim-source pair:

VERIFIED
Source is real, reachable, credible, and directly supports the claim.

MISLEADING
Source is real but does not actually support the claim as made.
The citation exists but the connection is weak, tangential, or forced.
(This is your NSA example — real domain, zero relevance to claim)

CONTRADICTORY
Source is real but actually contradicts the claim being made.

UNVERIFIABLE
Source cannot be reached or does not exist.

UNSOURCED
Claim has no citation at all.

IMPLICIT
Claim references research or evidence vaguely without a source.

For overall credibility consider:
- What percentage of claims are verified vs misleading vs unsourced?
- Are the most important claims the ones that are sourced?
- Are absolute claims ("always", "proven", "fact") supported?
- Does the confidence of language match the strength of evidence?

Always respond in clean JSON only. No preamble. No markdown.

Format:
{
  "claim_assessments": [
    {
      "claim": "...",
      "source": "...",
      "classification": "verified/misleading/contradictory/unverifiable/unsourced/implicit",
      "reasoning": "plain English explanation of why",
      "risk_level": "low/medium/high"
    }
  ],
  "verified_count": 0,
  "misleading_count": 0,
  "contradictory_count": 0,
  "unverifiable_count": 0,
  "unsourced_count": 0,
  "implicit_count": 0,
  "relevance_overall_score": 0,
  "highest_risk_claim": "...",
  "relevance_summary": "..."
}

relevance_overall_score 1-10:
1-3 = High credibility risk
4-6 = Mixed credibility
7-10 = Strong credibility
"""

def assess_relevance(fetch_output: dict) -> dict:
    """
    Receives web fetch output.
    Performs deep claim-source relevance analysis.
    Only runs in credibility or both modes.
    """
    mode = fetch_output.get("mode", "both")

    if mode == "authenticity":
        print("[Relevance Agent] Skipping — authenticity mode selected.\n")
        return {**fetch_output, "relevance_findings": None}

    print("[Relevance Agent] Beginning claim-source relevance analysis...\n")
    print("[Relevance Agent] This is the intelligence layer — reasoning")
    print("[Relevance Agent] about whether sources actually support claims...\n")

    original_text = fetch_output["original_text"]
    citation_findings = fetch_output.get("citation_findings", {})
    fetch_findings = fetch_output.get("fetch_findings", {})

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=RELEVANCE_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""
Original Text:
{original_text}

Extracted Claims and Citations:
{json.dumps(citation_findings, indent=2)}

Web Fetch Assessments:
{json.dumps(fetch_findings, indent=2)}

Perform deep claim-source relevance analysis.
Reason carefully about each claim-source pair.
Return JSON only.
                """
            }
        ]
    )

    raw = response.content[0].text

    try:
        relevance_findings = json.loads(raw)
        print(f"[Relevance Agent] Analysis complete.")
        print(f"[Relevance Agent] Relevance score: "
              f"{relevance_findings.get('relevance_overall_score', 'N/A')}/10")
        print(f"[Relevance Agent] Verified claims: "
              f"{relevance_findings.get('verified_count', 0)}")
        print(f"[Relevance Agent] Misleading citations: "
              f"{relevance_findings.get('misleading_count', 0)}")
        print(f"[Relevance Agent] Unsourced claims: "
              f"{relevance_findings.get('unsourced_count', 0)}")
        if relevance_findings.get('highest_risk_claim'):
            print(f"[Relevance Agent] Highest risk claim: "
                  f"{relevance_findings.get('highest_risk_claim')}")
        print()
        return {
            **fetch_output,
            "relevance_findings": relevance_findings
        }
    except json.JSONDecodeError:
        print("[Relevance Agent] Warning: Could not parse JSON.")
        return {
            **fetch_output,
            "relevance_findings": raw
        }