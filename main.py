import os
import sys
from dotenv import load_dotenv

load_dotenv()

from agents.orchestrator import orchestrate
from agents.linguistic_analysis import analyze_linguistics
from agents.behavioral_pattern import analyze_behavior
from agents.citation_extraction import extract_citations
from agents.web_fetch import fetch_and_assess
from agents.relevance import assess_relevance
from agents.consistency import analyze_consistency
from agents.confidence_language import analyze_confidence_language
from agents.synthesizer import synthesize_report

def get_mode() -> str:
    print("\nSelect analysis mode:")
    print("  [1] Authenticity  — Was this written by a human or AI?")
    print("  [2] Credibility   — Can this content be trusted?")
    print("  [3] Full Analysis — Run both\n")

    while True:
        choice = input("Enter 1, 2, or 3: ").strip()
        if choice == "1":
            return "authenticity"
        elif choice == "2":
            return "credibility"
        elif choice == "3":
            return "both"
        else:
            print("Please enter 1, 2, or 3.")

def get_input() -> str:
    print("\nHow would you like to submit content?")
    print("  [1] Paste text")
    print("  [2] Enter a URL\n")

    while True:
        choice = input("Enter 1 or 2: ").strip()
        if choice == "1":
            return get_text_input()
        elif choice == "2":
            return get_url_input()
        else:
            print("Please enter 1 or 2.")

def get_text_input() -> str:
    print("\nPaste your text below.")
    print("When finished press Enter then type END and press Enter.\n")

    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)

    return "\n".join(lines)

def get_url_input() -> str:
    import requests
    url = input("\nEnter URL: ").strip()

    print(f"\n[TrustLayer] Fetching content from {url}...\n")
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            # Trim to avoid token overflow
            content = response.text[:5000]
            print(f"[TrustLayer] Content retrieved successfully.\n")
            return content
        else:
            print(f"[TrustLayer] Could not fetch URL. Status: {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"[TrustLayer] Error fetching URL: {str(e)}")
        sys.exit(1)

def main():
    print("\n" + "=" * 60)
    print("  🔐 TrustLayer")
    print("  Content Intelligence System")
    print("  by blondebytesecurity")
    print("=" * 60)

    # Get mode
    mode = get_mode()

    # Get content
    text_input = get_input()

    if not text_input.strip():
        print("No content provided. Exiting.")
        sys.exit(1)

    print(f"\n[TrustLayer] Starting {mode.upper()} analysis...\n")
    print("=" * 60 + "\n")

    # Run the full agent chain
    orchestrator_output    = orchestrate(text_input, mode)
    linguistic_output      = analyze_linguistics(orchestrator_output)
    behavioral_output      = analyze_behavior(linguistic_output)
    citation_output        = extract_citations(behavioral_output)
    fetch_output           = fetch_and_assess(citation_output)
    relevance_output       = assess_relevance(fetch_output)
    consistency_output     = analyze_consistency(relevance_output)
    confidence_output      = analyze_confidence_language(consistency_output)
    final_report           = synthesize_report(confidence_output)

    print("\n[TrustLayer] Analysis complete. 🔐\n")

if __name__ == "__main__":
    main()