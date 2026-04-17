"""
Output Richness Evaluator
-------------------------
Scores each system's output on 5 dimensions that matter for real incident response.
A single-agent system scores 1/5. The full council scores 5/5.
This metric is the primary evidence that the council architecture adds value
beyond simple label classification.

Scoring dimensions:
  1. threat_classified    — output contains a named threat category
  2. mitre_mapped         — output contains a MITRE ATT&CK technique ID (e.g., T1566)
  3. severity_scored      — output contains a numeric severity score (e.g., "8/10" or "Severity: 7")
  4. response_plan        — output contains numbered or bulleted defensive actions
  5. contradiction_noted  — output explicitly addresses contradictions or confirms agreement

Each dimension scores 1 if present, 0 if absent.
Total richness score = sum of all 5 dimensions (max 5).
"""

import re
import json
from council.orchestrator import CyberCouncil
from providers.base_provider import BaseLLMProvider


# ── Dimension detectors ────────────────────────────────────────────────────

THREAT_LABELS = [
    "phishing", "malware", "sql injection", "ddos", "ransomware",
    "zero-day", "zero day", "insider threat", "man-in-the-middle", "mitm"
]

def has_threat_classification(text: str) -> bool:
    """Check if output contains a named threat category."""
    t = text.lower()
    return any(label in t for label in THREAT_LABELS)


def has_mitre_mapping(text: str) -> bool:
    """Check if output contains a MITRE ATT&CK technique ID like T1566 or T1190."""
    return bool(re.search(r'\bT\d{4}(\.\d{3})?\b', text))


def has_severity_score(text: str) -> bool:
    """Check if output contains a numeric severity score."""
    patterns = [
        r'severity[\s\S]{0,20}\d{1,2}\s*/\s*10',   # "Severity: 8/10"
        r'severity\s*score\s*[:\-]?\s*\d{1,2}',     # "Severity Score: 9"
        r'\b([1-9]|10)\s*/\s*10\b',                  # "9/10" standalone
        r'severity[\s\S]{0,10}(critical|high|medium|low)',  # "Severity: High"
    ]
    t = text.lower()
    return any(re.search(p, t) for p in patterns)


def has_response_plan(text: str) -> bool:
    """Check if output contains numbered or bulleted defensive actions."""
    patterns = [
        r'^\s*\d+[\.\)]\s+\w',                  # "1. Block the..." or "1) Block..."
        r'^\s*[-*•]\s+\w',                       # "- Block the..." or "• Block..."
        r'(immediate action|response plan|recommended action|defensive action)',
    ]
    t = text.lower()
    for p in patterns:
        if re.search(p, t, re.MULTILINE):
            return True
    return False


def has_contradiction_note(text: str) -> bool:
    """Check if output explicitly addresses contradictions between agents."""
    keywords = [
        "no contradiction", "contradiction", "conflict", "disagree",
        "agents agree", "consistent", "discrepancy", "resolved"
    ]
    t = text.lower()
    return any(kw in t for kw in keywords)


# ── Single output scorer ───────────────────────────────────────────────────

def score_output(output: str) -> dict:
    """
    Score a single text output on all 5 richness dimensions.
    Returns a dict with each dimension score (0 or 1) and total.
    """
    scores = {
        "threat_classified":   int(has_threat_classification(output)),
        "mitre_mapped":        int(has_mitre_mapping(output)),
        "severity_scored":     int(has_severity_score(output)),
        "response_plan":       int(has_response_plan(output)),
        "contradiction_noted": int(has_contradiction_note(output)),
    }
    scores["total"] = sum(scores.values())
    return scores


# ── System-level richness evaluation ──────────────────────────────────────

def evaluate_richness(dataset_path: str, use_judge: bool = True) -> dict:
    """
    Run all threats through the council and score output richness.

    Args:
        dataset_path : Path to sample_threats.json
        use_judge    : If True, score the judge's final report.
                       If False, score only Agent A output (single-agent baseline).

    Returns:
        dict with average richness scores per dimension and overall average.
    """
    with open(dataset_path, encoding="utf-8") as f:
        dataset = json.load(f)

    council = CyberCouncil()

    dimension_totals = {
        "threat_classified":   0,
        "mitre_mapped":        0,
        "severity_scored":     0,
        "response_plan":       0,
        "contradiction_noted": 0,
        "total":               0,
    }

    n = len(dataset)

    skipped = 0
    for item in dataset:
        result = council.analyze_sync(item["threat_description"])

        if result["status"] == "rejected":
            skipped += 1
            continue

        if use_judge:
            text_to_score = result["final_report"]
        else:
            # Single-agent baseline: score only Agent A output
            text_to_score = result["round1_outputs"][0]["output"]

        scores = score_output(text_to_score)
        for key in dimension_totals:
            dimension_totals[key] += scores[key]

    effective_n = n - skipped
    if effective_n == 0:
        return {k: 0.0 for k in dimension_totals} | {"n_samples": 0}
    averages = {k: round(v / effective_n, 3) for k, v in dimension_totals.items()}
    averages["n_samples"] = n
    return averages


# ── Run comparison ─────────────────────────────────────────────────────────

def run_richness_comparison(dataset_path: str) -> dict:
    """
    Compare full council vs single agent on output richness.
    Returns both result sets for printing and saving.
    """
    print("\nScoring output richness — Full Council...")
    council_richness = evaluate_richness(dataset_path, use_judge=True)

    print("Scoring output richness — Single Agent (Baseline 1)...")
    baseline_richness = evaluate_richness(dataset_path, use_judge=False)

    return {
        "full_council":   council_richness,
        "single_agent":   baseline_richness,
    }
