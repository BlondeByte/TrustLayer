# TrustLayer — Research Findings

Observations emerging from real analysis runs. These inform product development,
calibration decisions, and the broader research direction of TrustLayer.

---

## FINDING 001 — Authority Bias Detection
**Date:** April 2026
**Source tested:** MIT News, MathNet announcement
**URL:** https://news.mit.edu/2026/mit-scientists-build-worlds-largest-collection-olympiad-level-math-problems-open-0424

### What happened
TrustLayer flagged a legitimate MIT institutional news page as LOW credibility /
HIGH manipulation risk due to unsupported superlative claims ("world's largest
collection", "largest high-quality dataset ever created").

### Why it matters
MIT's institutional authority is routinely used as a substitute for inline evidence.
The claim "MIT said it" becomes the citation — so the assertion never needs to be
sourced within the content itself. TrustLayer evaluates claim-to-evidence ratio
independent of source prestige, which surfaces a pattern most human readers miss.

### The broader pattern
Institutional sources — universities, governments, corporations — regularly publish
claims that would be flagged as misinformation if written by an anonymous blogger.
Source reputation launders credibility. TrustLayer sees through that.

### Product implication
This is a genuine differentiator. Most content trust tools defer to source authority.
TrustLayer applies consistent skepticism regardless of who is speaking.
Frame: **TrustLayer detects authority bias, not just factual inaccuracy.**

### Calibration note
The `institutional_pr` content type (v0.3+) should adjust credibility expectations
for promotional language — superlatives are genre convention in press releases,
not necessarily manipulation. But the underlying finding remains valid: even
genre-conventional superlatives should be flagged when evidence is absent.

---

## FINDING 002 — URL Fetch Truncation Skews Credibility Scores
**Date:** April 2026
**Source tested:** MIT News, MathNet announcement (same as above)

### What happened
TrustLayer's URL fetch is capped at 5,000 characters in `main.py`. For long
articles, this captures only navigation, headers, and the opening paragraph —
not the body where evidence typically lives. The MathNet article contains
substantial verification of its claims deeper in the piece:

- Dataset is five times larger than next-biggest of its kind
- 30,000+ problems across 47 countries, 17 languages, 143 competitions
- Peer-reviewed solutions, grading group of 30+ human evaluators
- Presented at ICLR 2026, NSF funded
- Specific benchmark results (GPT-5 averaged 69.3% on main benchmark)

None of this was visible to TrustLayer because it was beyond the 5,000 char cutoff.

### Why it matters
Credibility scores for long-form content are currently being generated from
the headline and lede only. This systematically underscores well-evidenced
articles and creates false positives on credibility analysis.

### Fix applied
URL fetch limit increased from 5,000 to 15,000 characters in `main.py` (v0.3).
This aligns the URL fetch window with the existing `MAX_TEXT_FOR_ANALYSIS`
limit used by all downstream agents.

### Remaining limitation
Even 15,000 characters may not capture full evidence in very long articles.
Future consideration: intelligent chunking that prioritizes body content
over navigation markup, or a secondary fetch pass if credibility score
is borderline.

---

## FINDING 003 — Academic Writing Converges With LLM Output
**Date:** April 2026
**Sources tested:** Two MIT researcher blog posts / academic abstracts

### What happened
Two verified human authors writing in academic register scored 2/10 and 3/10
on authenticity in TrustLayer v0.1 — indistinguishable from pure LLM output.
After adding the content classifier in v0.3, the same content scored 6/10
(Ambiguous, Medium confidence) — a more defensible and accurate verdict.

### Why it matters
Academic writing has structurally converged with LLM output. Rigid structure,
formulaic transitions, neutral tone, and hedged language are genre conventions
in academia — not LLM signals. A universal scoring baseline incorrectly
penalizes human academics for writing like academics.

### Fix applied
Content Type Classifier (v0.3) detects academic register and applies a
weight profile that downweights structural signals and upweights reference
specificity and cognitive fingerprint instead.

### Deeper implication
The convergence runs both directions. Academic writing now sounds like LLMs
because LLMs were trained on academic writing. This creates a genuine
detection ceiling for authenticity tools that rely on surface linguistic
patterns. TrustLayer's behavioral layer (cognitive fingerprint, reference
behavior, opinion integrity) is more robust than structural analysis alone.

---

## FINDING 004 — High Authenticity Does Not Predict High Credibility
**Date:** April 2026
**Sources tested:** Agent outputs from Multiworlds (Sources 2-9 in batch run)

### What happened
Agent-generated content from the Multiworlds system consistently scored
7-8.5/10 on authenticity (Likely Human / Strong Human) while simultaneously
scoring 1.5-3/10 on credibility (Critical Risk). The most "human-sounding"
content was also the least trustworthy.

### Why it matters
This inverts the assumption most people bring to AI detection tools —
that AI-generated = untrustworthy, human-generated = trustworthy.
The data shows these are orthogonal dimensions, not correlated ones.

### The threat this reveals
A bad actor who knows that emotional volatility, controversial opinions,
and confrontational voice score as human will optimize for exactly those
signals. TrustLayer's authenticity scores are essentially a red team
finding: they reveal what optimized deception looks like.

### Product implication
TrustLayer's real product surface may not be "detect AI" but
**"detect content optimized to manipulate trust"** — a harder problem,
higher value, and more defensible moat. The dataset being built through
real runs is training data for exactly this capability.

### Buyer implication
- Disinformation researchers — state-sponsored influence ops already do this
- Financial services — analyst report and sentiment manipulation
- Legal/compliance — AI-optimized evidence or testimony
- Platforms — not "is this AI" but "is this engineered to deceive at scale"

---

## META — What TrustLayer Is Actually Building

Every analysis run generates a data point on the relationship between:
- Writing style and human origin
- Confidence language and evidence quality
- Institutional authority and factual support
- Emotional authenticity and credibility

The reports folder is a research dataset. As volume grows, pattern analysis
across runs will surface calibration insights that no individual report reveals.

**Priority:** Move reports into Supabase when count exceeds ~50.
Schema suggestion:
- `source_label` (human/llm/agent/unknown)
- `content_type` (academic/editorial/conversational/technical/institutional/institutional_pr)
- `auth_score` (float)
- `credibility_score` (float)
- `verdict` (string)
- `manipulation_risk` (low/medium/high)
- `raw_report` (text)
- `created_at` (timestamp)