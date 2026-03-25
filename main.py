"""
main.py — Manual single-threat test runner.

Usage:
    python main.py

Edit the `threat` variable below to test any custom threat description.
"""

from council.orchestrator import CyberCouncil


threat = """
An employee received an email from ceo-financials.com claiming to be the CEO,
requesting an urgent wire transfer of $150,000 to an external account.
The link in the email points to http://docusign-secure.ceo-financials.com/sign.
Email was sent at 2:47 AM. The real company domain is company.com.
"""


def main():
    council = CyberCouncil()
    result  = council.analyze(threat)

    # Print each specialist agent's output
    for output in result["agent_outputs"]:
        print(f"\n{'=' * 60}")
        print(f"[{output['agent']}]  via {output['provider']}")
        print("-" * 60)
        print(output["output"])

    # Print the judge's final synthesized report
    print(f"\n{'=' * 60}")
    print("[FINAL JUDGE REPORT]")
    print("=" * 60)
    print(result["final_report"])
    print()


if __name__ == "__main__":
    main()
