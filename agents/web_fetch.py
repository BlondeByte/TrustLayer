import anthropic
import json
import time
import random
import socket
import ipaddress
import logging
import requests
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# LOGGING
# ============================================================
logging.basicConfig(
    filename="trustlayer_audit.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

def audit_log(event: str, detail: str = ""):
    logging.info(f"{event} | {detail}")

# ============================================================
# SECURITY CONFIG
# ============================================================

BLOCKED_DOMAINS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "169.254.169.254",
    "metadata.google.internal",
    "169.254.170.2",
}

PRIVATE_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]

ALLOWED_SCHEMES = {"http", "https"}

MIN_DELAY = 2.0
MAX_DELAY = 5.0
MAX_URLS_PER_RUN = 10

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# ============================================================
# CONTENT QUALITY SIGNALS
# Low quality = paywall, cookie wall, login gate, bot block
# ============================================================

LOW_QUALITY_SIGNALS = [
    "subscribe to read",
    "subscribe to continue",
    "sign in to continue",
    "sign in to read",
    "log in to read",
    "create a free account",
    "enable cookies",
    "please enable cookies",
    "cookie consent",
    "access denied",
    "403 forbidden",
    "you have been blocked",
    "please verify you are human",
    "checking your browser",
    "just a moment",  # Cloudflare
    "enable javascript",
    "this content is for subscribers",
    "already a subscriber",
    "to continue reading",
    "unlimited access",
    "paywall",
]

# ============================================================
# FORTUNE COOKIES
# TrustLayer flavored — shown when a fetch is blocked/low quality
# ============================================================

FORTUNE_COOKIES = [
    "🔐 Even the best intelligence can't see through a locked door.",
    "🕵️  A source that hides may have something worth finding.",
    "🔮 The truth doesn't need a subscription — but some websites do.",
    "⚡ TrustLayer tried. The internet said no. The analysis continues.",
    "🧱 Every wall is just a data point about who controls the narrative.",
    "🍪 They wanted cookies. We wanted content. Nobody wins today.",
    "🌐 Paywalls: where credibility goes to be unverifiable.",
    "🤖 Cloudflare 1 — TrustLayer 0. The war continues.",
    "🔍 Unverifiable source detected. Treat with appropriate skepticism.",
    "📰 Breaking: this article cannot be broken into.",
    "🎭 The source exists. Whether it supports the claim remains a mystery.",
    "🚪 Some doors are locked for a reason. This one just costs $14.99/month.",
]

def get_fortune_cookie() -> str:
    return random.choice(FORTUNE_COOKIES)

# ============================================================
# CONTENT QUALITY CHECK
# ============================================================

def check_content_quality(content: str) -> tuple[bool, str]:
    """
    Checks if fetched content is actually useful or just a wall.
    Returns (is_low_quality, reason).
    """
    lower = content.lower()
    for signal in LOW_QUALITY_SIGNALS:
        if signal in lower:
            return True, signal
    return False, ""

# ============================================================
# URL VALIDATION
# ============================================================

def is_safe_url(url: str) -> tuple[bool, str]:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ALLOWED_SCHEMES:
            return False, f"Blocked scheme: {parsed.scheme}"
        if not parsed.hostname:
            return False, "No hostname found"
        hostname = parsed.hostname.lower()
        if hostname in BLOCKED_DOMAINS:
            return False, f"Blocked domain: {hostname}"
        try:
            ip_str = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(ip_str)
            for private_range in PRIVATE_RANGES:
                if ip in private_range:
                    return False, f"Private IP range blocked: {ip_str}"
        except socket.gaierror:
            return False, f"Could not resolve hostname: {hostname}"
        return True, "OK"
    except Exception as e:
        return False, f"URL parse error: {str(e)}"

# ============================================================
# SAFE FETCH
# ============================================================

def safe_fetch(url: str) -> tuple[bool, str, str]:
    """
    Fetches a URL safely.
    Returns (is_reachable, content, quality_status)
    quality_status: "ok" | "low_quality" | "blocked"
    """
    is_safe, reason = is_safe_url(url)
    if not is_safe:
        audit_log("BLOCKED_URL", f"url={url} reason={reason}")
        return False, f"Blocked: {reason}", "blocked"

    try:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

        response = requests.get(
            url,
            timeout=8,
            headers=headers,
            allow_redirects=True,
            stream=True
        )

        if response.history:
            final_url = response.url
            is_safe_final, reason_final = is_safe_url(final_url)
            if not is_safe_final:
                audit_log("BLOCKED_REDIRECT", f"original={url} final={final_url} reason={reason_final}")
                return False, f"Redirect blocked: {reason_final}", "blocked"

        if response.status_code == 200:
            content = ""
            for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                content += chunk
                if len(content) >= 3000:
                    break
            content = content[:3000]

            # Check content quality
            is_low_quality, signal = check_content_quality(content)
            if is_low_quality:
                audit_log("LOW_QUALITY_FETCH", f"url={url} signal='{signal}'")
                fortune = get_fortune_cookie()
                return True, content, f"low_quality:{signal}"
            
            audit_log("FETCH_SUCCESS", f"url={url} status=200 chars={len(content)}")
            return True, content, "ok"
        else:
            audit_log("FETCH_FAILED", f"url={url} status={response.status_code}")
            return False, f"Status code: {response.status_code}", "blocked"

    except requests.exceptions.Timeout:
        audit_log("FETCH_TIMEOUT", f"url={url}")
        return False, "Request timed out", "blocked"
    except requests.exceptions.TooManyRedirects:
        audit_log("FETCH_REDIRECT_LOOP", f"url={url}")
        return False, "Too many redirects", "blocked"
    except Exception as e:
        audit_log("FETCH_ERROR", f"url={url} error={str(e)}")
        return False, f"Could not reach URL: {str(e)}", "blocked"

# ============================================================
# CLAUDE PROMPT
# ============================================================

WEB_FETCH_SYSTEM_PROMPT = """
You are the Web Fetch Agent for TrustLayer by blondebytesecurity.

Your specialty is retrieving and summarizing web content from cited URLs
so that downstream agents can assess whether sources actually support
the claims made in the analyzed text.

For URLs marked as low_quality (paywall, cookie wall, login gate):
Note this clearly in your assessment — the source cannot be verified
and should be treated as unverifiable for credibility purposes.

Domain credibility signals:
- .gov, .edu, established news outlets = high credibility
- Known research institutions = high credibility
- Personal blogs, unknown domains = low credibility
- Paywalled, blocked, or unreachable = unverifiable

Always respond in clean JSON only. No preamble. No markdown.

Format:
{
  "url_assessments": [
    {
      "url": "...",
      "reachable": true/false,
      "quality_status": "ok/low_quality/blocked",
      "domain_credibility": "high/medium/low",
      "source_summary": "...",
      "relevant_to_claim": true/false,
      "claim_associated": "...",
      "verdict": "supports/tangential/contradicts/unreachable/unverifiable"
    }
  ],
  "fetch_summary": "..."
}
"""

# ============================================================
# MAIN AGENT FUNCTION
# ============================================================

client = anthropic.Anthropic()

def fetch_and_assess(citation_output: dict) -> dict:
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

    if len(urls_found) > MAX_URLS_PER_RUN:
        print(f"[Web Fetch Agent] Capping at {MAX_URLS_PER_RUN} URLs (found {len(urls_found)}).\n")
        audit_log("URL_CAP_APPLIED", f"found={len(urls_found)} capped={MAX_URLS_PER_RUN}")
        urls_found = urls_found[:MAX_URLS_PER_RUN]

    print(f"[Web Fetch Agent] Fetching {len(urls_found)} URL(s)...\n")
    audit_log("FETCH_SESSION_START", f"url_count={len(urls_found)} mode={mode}")

    url_claim_map = {}
    for claim in claims:
        url = claim.get("url")
        if url:
            url_claim_map[url] = claim.get("claim", "No specific claim mapped")

    fetched_content = []
    for i, url in enumerate(urls_found):
        print(f"[Web Fetch Agent] Fetching ({i+1}/{len(urls_found)}): {url}")

        reachable, content, quality_status = safe_fetch(url)

        if reachable and quality_status == "ok":
            print(f"[Web Fetch Agent] ✓ Reached: {url}")
        elif reachable and quality_status.startswith("low_quality"):
            signal = quality_status.split(":")[1] if ":" in quality_status else "unknown"
            fortune = get_fortune_cookie()
            print(f"[Web Fetch Agent] ⚠️  Low quality content: {url}")
            print(f"[Web Fetch Agent] Signal: '{signal}'")
            print(f"[Web Fetch Agent] {fortune}\n")
        else:
            print(f"[Web Fetch Agent] ✗ Blocked/Failed: {url} — {content}")

        fetched_content.append({
            "url": url,
            "reachable": reachable,
            "quality_status": quality_status,
            "content": content if quality_status == "ok" else f"[{quality_status}] Content not usable for analysis.",
            "associated_claim": url_claim_map.get(url, "No direct claim mapped")
        })

        if i < len(urls_found) - 1:
            delay = random.uniform(MIN_DELAY, MAX_DELAY)
            print(f"[Web Fetch Agent] Waiting {delay:.1f}s before next request...\n")
            time.sleep(delay)

    print(f"\n[Web Fetch Agent] Fetch complete. Sending to Claude for assessment...\n")
    audit_log("FETCH_SESSION_COMPLETE", f"fetched={len(fetched_content)}")

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
raw = raw.strip()
if raw.startswith('```'):
    raw = raw.split('```')[1]
    if raw.startswith('json'):
        raw = raw[4:]
raw = raw.strip()

raw = raw.strip()
if raw.startswith('```'):
    raw = raw.split('```')[1]
    if raw.startswith('json'):
        raw = raw[4:]
raw = raw.strip()


    try:
        fetch_findings = json.loads(raw)
        assessments = fetch_findings.get("url_assessments", [])
        print(f"[Web Fetch Agent] Assessment complete.")
        for a in assessments:
            print(f"[Web Fetch Agent] {a.get('url', 'N/A')} → "
                  f"{a.get('verdict', 'N/A').upper()}")
        print()
        return {**citation_output, "fetch_findings": fetch_findings}
    except json.JSONDecodeError:
        audit_log("JSON_PARSE_ERROR", f"raw_response_length={len(raw)}")
        print("[Web Fetch Agent] Warning: Could not parse JSON.")
        return {
            **citation_output,
            "fetch_findings": raw
        }