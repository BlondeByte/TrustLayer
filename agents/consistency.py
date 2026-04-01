import anthropic
import json
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

CONSISTENCY_SYSTEM_PROMPT = """
You are the Consistency Agent for TrustLayer by blondebytesecurity.

Your specialty is analyzing whether a piece of content
holds together internally — do the claims, evidence, and
conclusions actually agree with each other?

This is separate from whether sources are real or relevant.
This is about whether the content contradicts itself,
makes logical leaps, or presents conclusions that don't
follow from the evidence provided.

Analyze the following dimensions:

1. INTERNAL CONSISTENCY
   - Do claims made early in the text hold up later?
   - Does the conclusion follow from the evidence presented?
   - Are there contradictions within the text itself?
   - Does the author argue against their own points anywhere?

2. LOGICAL COHERENCE
   - Are causal claims logical? (X causes Y — does that follow?)
   - Are comparisons valid? (comparing unlike things?)
   - Are statistical claims used correctly?
   - Are there logical fallacies present?

3. SCOPE CONSISTENCY
   - Does the text make broad claims but only provide narrow evidence?
   - Does it generalize from single examples?
   - Does it present correlation as causation?
   - Are absolute claims ("always", "never") justified by evidence?

4. TONAL CONSISTENCY
   - Does confidence of language match strength of evidence?
   - Are hedging phrases used appropriately?
   - Does the text shift from uncertain to certain without justification?
   - Are emotional appeals used to substitute for evidence?

5. NARRATIVE CONSISTENCY
   - Does the overall narrative hold together?
   - Are there gaps in the argument?
   - Does the text set up questions it never answers?
   - Is the structure serving the argument or obscuring it?

Score each dimension 1-10:
1-3 = High inconsistency risk
4-6 = Mixed consistency
7-10 = Strong consistency

Always respond in clean JSON only. No preamble. No markdown.

Format:
{
  "internal_consistency": {
    "score": 0,
    "observations": "..."
  },
  "logical_coherence": {
    "score": 0,
    "observations": "..."
  },
  "scope_consistency": {
    "score": 0,
    "observations": "..."
  },
  "tonal_consistency": {
    "score": 0,
    "observations": "..."
  },
  "narrative_consistency": {
    "score": 0,
    "observations": "..."
  },
  "consistency_overall_score": 0,
  "contradictions_found": ["contradiction1", "contradiction2"],
  "logical_gaps_found": ["gap1", "gap2"],
  "consistency_summary": "..."
}

consistency_overall_score 1-10:
1-3 = High inconsistency risk
4-6 = Mixed
7-10 = Internally consistent
"""

def analyze_consistency(relevance_output: dict) -> dict:
    """
    Receives relevance output.
    Analyzes internal consistency of the content.
    Only runs in credibility or both modes.
    """
    mode = relevance_output.get("mode", "both")

    if mode == "authenticity":
        print("[Consistency Agent] Skipping — authenticity mode selected.\n")
        return {**relevance_output, "consistency_findings": None}

    print("[Consistency Agent] Analyzing internal consistency...\n")

    original_text = relevance_output["original_text"]
    context = relevance_output["context"]
    relevance_findings = relevance_output.get("relevance_findings", {})

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        system=CONSISTENCY_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""
Context from Orchestrator:
{json.dumps(context, indent=2)}

Relevance Findings from Previous Agent:
{json.dumps(relevance_findings, indent=2)}

Original Text to Analyze:
{original_text}

Perform full internal consistency analysis.
Return JSON only.
                """
            }
        ]
    )

    raw = response.content[0].text

    try:
        consistency_findings = json.loads(raw)
        print(f"[Consistency Agent] Analysis complete.")
        print(f"[Consistency Agent] Consistency score: "
              f"{consistency_findings.get('consistency_overall_score', 'N/A')}/10")
        contradictions = consistency_findings.get("contradictions_found", [])
        gaps = consistency_findings.get("logical_gaps_found", [])
        if contradictions:
            print(f"[Consistency Agent] Contradictions found: {len(contradictions)}")
        if gaps:
            print(f"[Consistency Agent] Logical gaps found: {len(gaps)}")
        print()
        return {
            **relevance_output,
            "consistency_findings": consistency_findings
        }
    except json.JSONDecodeError:
        print("[Consistency Agent] Warning: Could not parse JSON.")
        return {
            **relevance_output,
            "consistency_findings": raw
        }