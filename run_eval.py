import sys
import asyncio
import json
import os

# Windows: use SelectorEventLoop to avoid ProactorEventLoop conflicts with ThreadPoolExecutor
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from evaluation.evaluator import run_evaluation, run_baseline2_majority_vote
from evaluation.richness_evaluator import run_richness_comparison

DATASET     = "data/threats.json"
RESULTS_DIR = "results/"
SAMPLES_DIR = "results/samples"


# ── 1. Label Classification Metrics ───────────────────────────────────────
print("\n" + "="*60)
print("PART 1 — LABEL CLASSIFICATION METRICS")
print("="*60)

print("\n[Running] Full Council + Judge...")
print(f"  Per-sample reports will be saved to: {SAMPLES_DIR}/")
council_metrics, council_true, council_pred = run_evaluation(DATASET, output_dir=SAMPLES_DIR)

print("[Running] Baseline 2 — Council, No Judge...")
b2_metrics, b2_true, b2_pred = run_baseline2_majority_vote(DATASET)

print("\n--- Classification Results ---")
header = f"{'System':<35} {'Accuracy':>9} {'Precision':>10} {'Recall':>8} {'F1':>8}"
print(header)
print("-" * len(header))

systems = [
    ("Full Council + Judge",        council_metrics),
    ("Baseline 2 (Council No Judge)", b2_metrics),
]
for name, m in systems:
    print(f"{name:<35} {m['accuracy']:>9.4f} {m['precision']:>10.4f} {m['recall']:>8.4f} {m['f1_score']:>8.4f}")

print("\nDetailed Classification Report (Full Council):")
print(council_metrics["report"])


# ── 2. Output Richness Metrics ─────────────────────────────────────────────
print("\n" + "="*60)
print("PART 2 — OUTPUT RICHNESS METRICS")
print("="*60)

richness = run_richness_comparison("data/sample_threats.json")

dims = ["threat_classified", "mitre_mapped", "severity_scored", "response_plan", "contradiction_noted", "total"]
dim_labels = {
    "threat_classified":   "Threat classified",
    "mitre_mapped":        "MITRE ATT&CK mapped",
    "severity_scored":     "Severity scored",
    "response_plan":       "Response plan present",
    "contradiction_noted": "Contradiction addressed",
    "total":               "TOTAL RICHNESS SCORE",
}

print(f"\n{'Dimension':<30} {'Single Agent':>14} {'Full Council':>14}")
print("-" * 60)
for d in dims:
    single_val = richness["single_agent"][d]
    council_val = richness["full_council"][d]
    marker = " <--" if d == "total" else ""
    print(f"{dim_labels[d]:<30} {single_val:>14.3f} {council_val:>14.3f}{marker}")


# ── 3. Save all results ────────────────────────────────────────────────────
os.makedirs(RESULTS_DIR, exist_ok=True)
with open(RESULTS_DIR + "eval_results.json", "w", encoding="utf-8") as f:
    json.dump({
        "full_council_metrics":   {k: v for k, v in council_metrics.items() if k != "report"},
        "baseline2_metrics":      {k: v for k, v in b2_metrics.items() if k != "report"},
        "richness_comparison":    richness,
        "council_predictions":    list(zip(council_true, council_pred)),
        "baseline2_predictions":  list(zip(b2_true, b2_pred)),
    }, f, indent=2)

print(f"\n\nPer-sample reports saved to: {SAMPLES_DIR}/")
print("All results saved to results/eval_results.json")
print("="*60)
