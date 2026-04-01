import anthropic
import json
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

CONFIDENCE_LANGUAGE_SYSTEM_PROMPT = """
You are the Confidence Language Agent for TrustLayer by blondebytesecurity.

Your specialty is analyzing whether the confidence of language
used in content appropriately matches the strength of evidence provided.

This is one of the most revealing credibility signals available.
Trustworthy content calibrates its certainty to its evidence.
Untrustworthy content overclaims, uses absolute language without
justification, or manipulates through emotional framing.

Analyze the following dimensions:

1. CERTAINTY CALIBRATION
   - Does language confidence match evidence strength?
   - "Studies suggest" vs "studies prove" — is the distinction respected?
   - Are hedging phrases used appropriately?
   - Does the text claim more certainty than evidence supports?

2. ABSOLUTE LANGUAGE USAGE
   - Flags: "always", "never", "proven", "fact", "certain", "guaranteed"
   - Are these justified by the evidence presented?
   - Are absolute claims in high stakes areas (health, finance, legal)?
   - How frequently does absolute language appear?

3. EMOTIONAL LANGUAGE PATTERNS
   - Is emotional language used to substitute for evidence?
   - Are fear, urgency, or outrage used to bypass critical thinking?
   - Does the text manipulate rather than inform?
   - Are loaded words used in place of neutral descriptors?

4. HEDGING APPROPRIATENESS
   - Are limitations of evidence acknowledged?
   - Does the text admit what it doesn't know?
   - Are counterarguments acknowledged fairly?
   - Is uncertainty treated honestly?

5. CLAIM ESCALATION
   - Does the text start with evidence and escalate to unsupported conclusions?
   - Are small findings used to justify large claims?
   - Does the conclusion overreach the body of the content?
   - Is there a pattern of building false confidence throughout?

Score each dimension 1-10:
1-3 = High confidence language risk
4-6 = Mixed
7-10 = Well calibrated language

Flag specific phrases that are high risk.

Always respond in clean JSON only. No preamble. No markdown.

Format:
{
  "certainty_calibration": {
    "score": 0,
    "observations": "..."
  },
  "absolute_language_usage": {
    "score": 0,
    "observations": "...",
    "flagged_phrases": ["phrase1", "phrase2"]
  },
  "emotional_language_patterns": {
    "score": 0,
    "observations": "...",
    "flagged_phrases": ["phrase1", "phrase2"]
  },
  "hedging_appropriateness": {
    "score": 0,
    "observations": "..."
  },
  "claim_escalation": {
    "score": 0,
    "observations": "..."
  },
  "confidence_overall_score": 0,
  "high_risk_phrases": ["phrase1", "phrase2"],
  "manipulation_risk": "low/medium/high",
  "confidence_summary": "..."
}

confidence_overall_score 1-10:
1-3 = High manipulation/overclaiming risk
4-6 = Mixed calibration
7-10 = Well calibrated and honest language
"""

def analyze_confidence_language(consistency_output: dict) -> dict:
    """
    Receives consistency output.
    Analyzes whether language confidence matches evidence strength.
    Only runs in credibility or both modes.
    """
    mode = consistency_output.get("mode", "both")

    if mode == "authenticity":
        print("[Confidence Agent] Skipping — authenticity mode selected.\n")
        return {**consistency_output, "confidence_findings": None}

    print("[Confidence Agent] Analyzing confidence language patterns...\n")
    print("[Confidence Agent] Checking if certainty matches evidence...\n")

    original_text = consistency_output["original_text"]
    context = consistency_output["context"]
    consistency_findings = consistency_output.get("consistency_findings", {})
    relevance_findings = consistency_output.get("relevance_findings", {})

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        system=CONFIDENCE_LANGUAGE_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""
Context from Orchestrator:
{json.dumps(context, indent=2)}

Consistency Findings from Previous Agent:
{json.dumps(consistency_findings, indent=2)}

Relevance Findings:
{json.dumps(relevance_findings, indent=2)}

Original Text to Analyze:
{original_text}

Analyze confidence language patterns.
Flag specific high risk phrases.
Return JSON only.
                """
            }
        ]
    )

    raw = response.content[0].text

    try:
        confidence_findings = json.loads(raw)
        print(f"[Confidence Agent] Analysis complete.")
        print(f"[Confidence Agent] Confidence language score: "
              f"{confidence_findings.get('confidence_overall_score', 'N/A')}/10")
        print(f"[Confidence Agent] Manipulation risk: "
              f"{confidence_findings.get('manipulation_risk', 'N/A').upper()}")
        high_risk = confidence_findings.get("high_risk_phrases", [])
        if high_risk:
            print(f"[Confidence Agent] High risk phrases found: {len(high_risk)}")
            for phrase in high_risk[:3]:
                print(f"[Confidence Agent]   → \"{phrase}\"")
        print()
        return {
            **consistency_output,
            "confidence_findings": confidence_findings
        }
    except json.JSONDecodeError:
        print("[Confidence Agent] Warning: Could not parse JSON.")
        return {
            **consistency_output,
            "confidence_findings": raw
        }