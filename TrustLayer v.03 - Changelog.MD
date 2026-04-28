# TrustLayer v0.3 — Changelog

## What changed

### New: `agents/content_classifier.py`
Slots between Orchestrator and Linguistic Agent. Detects content genre
and injects a scoring weight profile into the pipeline.

Five content types supported:
- `academic`       — rigid structure is genre norm, not LLM signal
- `editorial`      — voice and opinion risk-taking are primary signals
- `conversational` — messiness and fragments are human signals
- `technical`      — accuracy depth and reference specificity matter most
- `institutional`  — most convergent with LLM; only cognitive fingerprint is reliable

### Modified: `agents/linguistic_analysis.py`
Now receives `content_type` and `scoring_weights` from classifier.
Each scored dimension includes `weight_applied` field in output.
Overall score is genre-adjusted, not universal.

### Modified: `agents/behavioral_pattern.py`
Same pattern — weight profile applied to all five behavioral dimensions.
Includes `genre_adjusted: true` in output so synthesizer can flag it.

### Modified: `main.py`
One new import, one new line in the agent chain.
Version bumped to v0.3 in header.

## Why this matters

The MIT researcher false-positive problem: two verified human authors
scoring 2/10 and 3/10 because academic writing structurally converges
with LLM output. With context-aware scoring, academic content is judged
against academic baselines — structural uniformity stops dragging the score down,
and reference specificity + cognitive fingerprint carry more weight instead.

## What to watch in reports

New fields to look for:
- `content_type` in report header
- `weight_applied` per dimension in authenticity scores
- `genre_adjusted: true` flag on linguistic and behavioral findings

## Files not changed
All other agents (citation_extraction, web_fetch, relevance, consistency,
confidence_language, synthesizer, orchestrator) are unchanged.
Drop the three new/modified files into your existing agents/ folder.