import anthropic
import json
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

LINGUISTIC_ANALYSIS_SYSTEM_PROMPT = """
You are the Linguistic Analysis Agent for TrustLayer by blondebytesecurity.

Your specialty is identifying linguistic fingerprints that distinguish
human writing from LLM-generated content.

Analyze the following dimensions:

1. SENTENCE STRUCTURE
   - Overly uniform sentence length (LLM signal)
   - Natural rhythm variation (human signal)
   - Run-ons, fragments, self-corrections (human signal)

2. VOCABULARY PATTERNS
   - Overuse of filler words: "furthermore", "it's worth noting",
     "in conclusion", "crucial", "fascinating" (LLM signal)
   - Casual, irregular, or domain-specific word choice (human signal)
   - Contractions and colloquialisms (human signal)

3. TRANSITION PATTERNS
   - Overly smooth, formulaic transitions (LLM signal)
   - Abrupt or unexpected pivots (human signal)
   - Natural conversational bridges (human signal)

4. STRUCTURAL PATTERNS
   - Rigid intro/body/conclusion format (LLM signal)
   - Non-linear or organic structure (human signal)
   - Predictable three-point structure (LLM signal)

5. VOICE CONSISTENCY
   - Generic neutral tone throughout (LLM signal)
   - Voice shifts, personality, opinion with edge (human signal)
   - Moments of genuine surprise or contradiction (human signal)

Score each dimension 1-10:
1-3 = Strong LLM signal
4-6 = Ambiguous
7-10 = Strong human signal

Always respond in clean JSON only. No preamble. No markdown.

Format:
{
  "sentence_structure": {
    "score": 0,
    "observations": "..."
  },
  "vocabulary_patterns": {
    "score": 0,
    "observations": "..."
  },
  "transition_patterns": {
    "score": 0,
    "observations": "..."
  },
  "structural_patterns": {
    "score": 0,
    "observations": "..."
  },
  "voice_consistency": {
    "score": 0,
    "observations": "..."
  },
  "linguistic_overall_score": 0,
  "linguistic_summary": "..."
}
"""

def analyze_linguistics(orchestrator_output: dict) -> dict:
    """
    Receives orchestrator context and original text.
    Performs deep linguistic analysis.
    Only runs in authenticity or both modes.
    """
    mode = orchestrator_output.get("mode", "both")

    if mode == "credibility":
        print("[Linguistic Agent] Skipping — credibility mode selected.\n")
        return {**orchestrator_output, "linguistic_findings": None}

    print("[Linguistic Agent] Beginning linguistic analysis...\n")

    original_text = orchestrator_output["original_text"]
    context = orchestrator_output["context"]

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=LINGUISTIC_ANALYSIS_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""
Context from Orchestrator:
{json.dumps(context, indent=2)}

Original Text to Analyze:
{original_text}

Perform full linguistic analysis and return JSON only.
                """
            }
        ]
    )

    raw = response.content[0].text

    try:
        linguistic_findings = json.loads(raw)
        print(f"[Linguistic Agent] Analysis complete.")
        print(f"[Linguistic Agent] Overall linguistic score: "
              f"{linguistic_findings.get('linguistic_overall_score', 'N/A')}/10\n")
        return {
            **orchestrator_output,
            "linguistic_findings": linguistic_findings
        }
    except json.JSONDecodeError:
        print("[Linguistic Agent] Warning: Could not parse JSON.")
        return {
            **orchestrator_output,
            "linguistic_findings": raw
        }