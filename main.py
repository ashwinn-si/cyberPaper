"""
main.py — Manual single-threat test runner.

Usage:
    python main.py

Edit the `threat` variable below to test any custom threat description.
"""

import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from council.orchestrator import CyberCouncil


threat = """
An employee received an email from ceo-financials.com claiming to be the CEO,
requesting an urgent wire transfer of $150,000 to an external account.
The link in the email points to http://docusign-secure.ceo-financials.com/sign.
Email was sent at 2:47 AM. The real company domain is company.com.
"""


def main():
    council = CyberCouncil()
    result  = council.analyze_sync(threat)

    print(f"\nStatus: {result['status']}")

    if result["status"] == "rejected":
        print("Threat rejected by validator:")
        print(result["validation"])
        return

    if result["status"] == "needs_clarification":
        print("Validator needs clarification:")
        for q in result.get("questions", []):
            print(f"  - {q}")
        return

    # Round 1 agent outputs
    print(f"\n{'=' * 60}")
    print("ROUND 1 — Agent Outputs")
    for output in result["round1_outputs"]:
        print(f"\n[{output['agent']}]  via {output['provider']}")
        print("-" * 60)
        print(output["output"])

    # Draft report
    print(f"\n{'=' * 60}")
    print("JUDGE DRAFT REPORT (Round 1)")
    print("=" * 60)
    print(result["draft_report"])

    # Round 2 agent outputs
    print(f"\n{'=' * 60}")
    print("ROUND 2 — Agent Outputs (with draft context)")
    for output in result["round2_outputs"]:
        print(f"\n[{output['agent']}]  via {output['provider']}")
        print("-" * 60)
        print(output["output"])

    # Final report
    print(f"\n{'=' * 60}")
    print("FINAL JUDGE REPORT")
    print("=" * 60)
    print(result["final_report"])

    # Disagreement log
    log = result.get("disagreement_log", {})
    if log:
        print(f"\n{'=' * 60}")
        print("DISAGREEMENT / CONSENSUS LOG")
        print("=" * 60)
        cl = log.get("classification", {})
        sv = log.get("severity", {})
        print(f"  Classification: A1={cl.get('agent_a_primary')}  A2={cl.get('agent_a_secondary')}  conflict={cl.get('disagree')}")
        print(f"  Severity:       C1={sv.get('agent_c_primary')}  C2={sv.get('agent_c_secondary')}  conflict={sv.get('disagree')}")
        rc = log.get("round_changes", {})
        if rc:
            print("  Round changes:")
            for agent_name, info in rc.items():
                marker = "REVISED (weight=1.5)" if info["changed"] else "stable  (weight=1.0)"
                print(f"    {agent_name:<30} {marker}")
    print()


if __name__ == "__main__":
    main()
