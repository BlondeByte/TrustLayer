import anthropic
import json
import requests
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

WEB_FETCH_SYSTEM_PROMPT = """
You are the Web Fetch Agent for TrustLayer by blondebytesecurity.

Your specialty is retrieving and summarizing web content from cited URLs
so that downstream agents can assess whether sources actually support
the claims made in the analyzed text.

You will receive a list of URLs and their associated claims.

For each URL you are given the fetched content.
Your job is to:

1. Summarize what the source actually says
2. Note the credibility of the source domain
3. Identify whether the content is relevant to the claim
4. Flag any mismatches between claim and source content

Domain credibility signals:
- .gov, .edu, established news outlets = high credibility
- Known research institutions = high credibility  
- Personal blogs, unknown domains = low credibility
- Parked domains, error pages = unreachable

Always respond in clean JSON only. No preamble. No markdown.

Format:
{
  "url_assessments": [
    {
      "url": "...",
      "reachable": true/false,
      "domain_credibility": "high/medium/low",
      "source_summary": "...",
      "relevant_to_claim": true/false,
      "claim_associated": "...",
      "verdict": "supports/tangential/contradicts/unreachable"
    }
  ],
  "fetch_summary": "..."
}
"""

def fetch_and_assess(citation_output: dict) -> dict:
    """
    Receives citation extraction output.
    Fetches each URL and assesses source credibility and relevance.
    Only runs in credibility or both modes.
    """
    mode = citation_output.get("mode", "both")

    if mode == "authenticity":
        print("[Web Fetch Agent] Skipping — authenticity mode selected.\n")
        return {**citation_output, "fetch_findings": None}

    citation_findings = citation_output.get("citation_findings")

    if not isinstance(citation_findings, dict):
        print("[Web Fetch Agent] No citation findings to process.\n")
        return {**citation_output, "fetch_findings": None}

    urls_found = citation_findings.get("urls_found", [])
    claims = citation_findings.get("claims", [])

    if not urls_found:
        print("[Web Fetch Agent] No URLs found in text — skipping fetch.\n")
        return {
            **citation_output,
            "fetch_findings": {
                "url_assessments": [],
                "fetch_summary": "No URLs were present in the analyzed text."
            }
        }

    print(f"[Web Fetch Agent] Fetching {len(urls_found)} URL(s)...\n")

    # Build URL to claim mapping
    url_claim_map = {}
    for claim in claims:
        url = claim.get("url")
        if url:
            url_claim_map[url] = claim.get("claim", "No specific claim mapped")

    # Fetch each URL
    fetched_content = []
    for url in urls_found:
        print(f"[Web Fetch Agent] Fetching: {url}")
        try:
            response = requests.get(url, timeout=8)
            if response.status_code == 200:
                # Trim content to avoid token overflow
                content = response.text[:3000]
                reachable = True
                print(f"[Web Fetch Agent] ✓ Reached: {url}")
            else:
                content = f"Status code: {response.status_code}"
                reachable = False
                print(f"[Web Fetch Agent] ✗ Failed: {url} ({response.status_code})")
        except Exception as e:
            content = f"Could not reach URL: {str(e)}"
            reachable = False
            print(f"[Web Fetch Agent] ✗ Unreachable: {url}")

        fetched_content.append({
            "url": url,
            "reachable": reachable,
            "content": content,
            "associated_claim": url_claim_map.get(url, "No direct claim mapped")
        })

    print(f"\n[Web Fetch Agent] Fetch complete. Sending to Claude for assessment...\n")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        system=WEB_FETCH_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""
Assess the following fetched URLs for credibility and claim relevance:

{json.dumps(fetched_content, indent=2)}

Return JSON only.
                """
            }
        ]
    )

    raw = response.content[0].text

    try:
        fetch_findings = json.loads(raw)
        assessments = fetch_findings.get("url_assessments", [])
        print(f"[Web Fetch Agent] Assessment complete.")
        for a in assessments:
            print(f"[Web Fetch Agent] {a.get('url', 'N/A')} → "
                  f"{a.get('verdict', 'N/A').upper()}")
        print()
        return {
            **citation_output,
            "fetch_findings": fetch_findings
        }
    except json.JSONDecodeError:
        print("[Web Fetch Agent] Warning: Could not parse JSON.")
        return {
            **citation_output,
            "fetch_findings": raw
        }