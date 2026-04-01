import anthropic
import json
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

BEHAVIORAL_PATTERN_SYSTEM_PROMPT = """
You are the Behavioral Pattern Agent for TrustLayer by blondebytesecurity.

Your specialty is analyzing what the writing DOES behaviorally —
not how it's structured, but how it thinks, references, and moves.

You receive linguistic findings from the previous agent.
Use those findings to inform and deepen your behavioral analysis.

Analyze the following dimensions:

1. INFORMATION DENSITY
   - Surface coverage of predictable points (LLM signal)
   - Unexpected depth, niche detail, or domain expertise (human signal)
   - Generic examples vs specific lived or researched examples (LLM vs human)
   - Does it tell you where to go next? Citations, resources, names (human signal)

2. CURIOSITY SIGNALS
   - Does the writing open new questions or close everything too neatly?
     (neat closure = LLM signal)
   - Does it acknowledge what it doesn't know? (human signal)
   - Are there tangents or digressions that serve no obvious purpose?
     (human signal)
   - Does anything in the text surprise you? (human signal)

3. OPINION INTEGRITY
   - Are opinions held that could alienate someone? (human signal)
   - Are all perspectives balanced to the point of saying nothing?
     (LLM signal)
   - Does the writing take a risk anywhere? (human signal)
   - Could you have predicted every point before reading? (LLM signal)

4. REFERENCE BEHAVIOR
   - Gestures at "research shows" without grounding (LLM signal)
   - Specific named studies, institutions, researchers (human signal)
   - Actual resource links or pathways for further reading (human signal)
   - Domain-specific terminology used correctly and naturally (human signal)

5. COGNITIVE FINGERPRINT
   - Does the writing feel like someone thought through it? (human signal)
   - Or does it feel like points were assembled? (LLM signal)
   - Are there moments where the writer seems to forget
     they are writing and just thinks out loud? (human signal)
   - Is there evidence of a mind behind the text? (human signal)

Score each dimension 1-10:
1-3 = Strong LLM signal
4-6 = Ambiguous
7-10 = Strong human signal

Weight your analysis against the linguistic findings passed to you.
If linguistic score was low (LLM signal) and behavioral is also low,
confidence in LLM origin increases significantly.

Always respond in clean JSON only. No preamble. No markdown.

Format:
{
  "information_density": {
    "score": 0,
    "observations": "..."
  },
  "curiosity_signals": {
    "score": 0,
    "observations": "..."
  },
  "opinion_integrity": {
    "score": 0,
    "observations": "..."
  },
  "reference_behavior": {
    "score": 0,
    "observations": "..."
  },
  "cognitive_fingerprint": {
    "score": 0,
    "observations": "..."
  },
  "behavioral_overall_score": 0,
  "linguistic_score_received": 0,
  "combined_signal": "strong_llm/likely_llm/ambiguous/likely_human/strong_human",
  "confidence": "low/medium/high",
  "behavioral_summary": "..."
}
"""

def analyze_behavior(linguistic_output: dict) -> dict:
    """
    Receives linguistic agent output.
    Performs deep behavioral pattern analysis.
    Only runs in authenticity or both modes.
    """
    mode = linguistic_output.get("mode", "both")

    if mode == "credibility":
        print("[Behavioral Agent] Skipping — credibility mode selected.\n")
        return {**linguistic_output, "behavioral_findings": None}

    print("[Behavioral Agent] Beginning behavioral pattern analysis...\n")

    original_text = linguistic_output["original_text"]
    context = linguistic_output["context"]
    linguistic_findings = linguistic_output.get("linguistic_findings")

    if isinstance(linguistic_findings, dict):
        linguistic_score = linguistic_findings.get(
            "linguistic_overall_score", "unavailable"
        )
    else:
        linguistic_score = "unavailable"

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=BEHAVIORAL_PATTERN_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""
Context from Orchestrator:
{json.dumps(context, indent=2)}

Linguistic Findings from Previous Agent:
{json.dumps(linguistic_findings, indent=2)}

Linguistic Overall Score: {linguistic_score}/10

Original Text to Analyze:
{original_text}

Perform full behavioral pattern analysis.
Weight your findings against the linguistic score received.
Return JSON only.
                """
            }
        ]
    )

    raw = response.content[0].text

    try:
        behavioral_findings = json.loads(raw)
        print(f"[Behavioral Agent] Analysis complete.")
        print(f"[Behavioral Agent] Behavioral overall score: "
              f"{behavioral_findings.get('behavioral_overall_score', 'N/A')}/10")
        print(f"[Behavioral Agent] Combined signal: "
              f"{behavioral_findings.get('combined_signal', 'N/A')}")
        print(f"[Behavioral Agent] Confidence: "
              f"{behavioral_findings.get('confidence', 'N/A')}\n")
        return {
            **linguistic_output,
            "behavioral_findings": behavioral_findings
        }
    except json.JSONDecodeError:
        print("[Behavioral Agent] Warning: Could not parse JSON.")
        return {
            **linguistic_output,
            "behavioral_findings": raw
        }