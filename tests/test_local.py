"""
Local test runner for CyberCouncil.
Tests all paths: valid threat, vague threat with answers, and invalid input.
Run with: python tests/test_local.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from council.orchestrator import CyberCouncil


# ── Test cases ─────────────────────────────────────────────────────────────

TESTS = [
    {
        "name":         "1 — Clear threat (should go straight through)",
        "threat":       "All files on the network share are encrypted. A ransom note demands $500,000 in Bitcoin within 48 hours.",
        "user_answers": "",
    },
    {
        "name":         "2 — Vague threat with answers supplied",
        "threat":       "my computer is acting weird",
        "user_answers": "It started after I opened an email attachment. Lots of pop-ups and the fan is running loud. Just my laptop, Windows 11.",
    },
    {
        "name":         "3a — Invalid: random gibberish (should be rejected)",
        "threat":       "asdfghjkl qwerty zxcvbnm",
        "user_answers": "",
    },
    {
        "name":         "3b — Invalid: non-security topic (should be rejected)",
        "threat":       "What's the best way to cook pasta?",
        "user_answers": "",
    },
    {
        "name":         "3c — Invalid: greeting (should be rejected)",
        "threat":       "hello",
        "user_answers": "",
    },
    {
        "name":         "3d — Invalid: random word (should be rejected)",
        "threat":       "test",
        "user_answers": "",
    },
    {
        "name":         "4 — Phishing (parallel agents stress test)",
        "threat":       "An employee received an email from ceo-financials.com claiming to be the CEO, requesting an urgent wire transfer of $150,000. The link points to http://docusign-secure.ceo-financials.com/sign. Sent at 2:47 AM.",
        "user_answers": "",
    },
]


# ── Runner ─────────────────────────────────────────────────────────────────

def print_separator(label=""):
    print("\n" + "=" * 65)
    if label:
        print(f"  {label}")
        print("=" * 65)


def run_test(council: CyberCouncil, test: dict):
    print_separator(test["name"])
    print(f"INPUT : {test['threat']}")
    if test["user_answers"]:
        print(f"ANSWERS: {test['user_answers']}")

    result = council.analyze_sync(test["threat"], test["user_answers"])

    status = result["status"]
    print(f"\nSTATUS: {status.upper()}")

    if status == "rejected":
        print(f"REASON: {result['validation'].get('reason', 'N/A')}")
        return

    if status == "needs_clarification":
        print("QUESTIONS:")
        for i, q in enumerate(result.get("questions", []), 1):
            print(f"  {i}. {q}")
        return

    # Analyzed — print summary
    print(f"\nCLEAN THREAT:\n{result['clean_threat']}\n")

    print("── ROUND 1 AGENT OUTPUTS ──")
    for out in result["round1_outputs"]:
        print(f"\n[{out['agent']}] via {out['provider']}")
        # Print first 300 chars to keep terminal readable
        preview = out["output"][:300].replace("\n", " ")
        print(f"  {preview}{'...' if len(out['output']) > 300 else ''}")

    print(f"\n── DRAFT REPORT (Round 1 Judge) ──")
    draft_preview = result["draft_report"][:400].replace("\n", " ")
    print(f"  {draft_preview}{'...' if len(result['draft_report']) > 400 else ''}")

    print(f"\n── FINAL REPORT (Round 2 Judge) ──")
    print(result["final_report"])


def main():
    print("\nCyberCouncil — Local Test Runner")
    print("Initializing council...")

    council = CyberCouncil()

    for test in TESTS:
        try:
            run_test(council, test)
        except Exception as e:
            print(f"\n[ERROR in test '{test['name']}']: {e}")
            import traceback
            traceback.print_exc()

    print_separator("All tests complete")


if __name__ == "__main__":
    main()
