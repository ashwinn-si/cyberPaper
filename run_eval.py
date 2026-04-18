"""
run_eval.py — Full dataset evaluation runner.

Usage:
    python run_eval.py                              # default dataset + all parts
    python run_eval.py --clear-cache                # fresh run, ignore cache
    python run_eval.py --dataset data/custom.json   # custom dataset
    python run_eval.py --output results/run2        # custom output dir
    python run_eval.py --skip-baseline              # skip baseline2 (faster)
    python run_eval.py --skip-richness              # skip richness eval (faster)
"""

import sys
import json
import os
import argparse

from evaluation.evaluator import run_evaluation, run_baseline2_majority_vote
from evaluation.richness_evaluator import run_richness_comparison
from evaluation.cache import load_cache, validate_cache, invalidate_stale_items

# ── CLI args ───────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="CyberCouncil full evaluation runner")
parser.add_argument("--dataset",        default="data/threats.json",  help="Path to labeled dataset JSON")
parser.add_argument("--output",         default="results",             help="Output directory for results")
parser.add_argument("--samples-dir",    default=None,                  help="Directory for per-sample reports (default: <output>/samples)")
parser.add_argument("--clear-cache",    action="store_true",           help="Ignore existing cache and start fresh")
parser.add_argument("--skip-baseline",  action="store_true",           help="Skip baseline2 (council without judge)")
parser.add_argument("--skip-richness",  action="store_true",           help="Skip output richness evaluation")
args = parser.parse_args()

DATASET     = args.dataset
RESULTS_DIR = args.output.rstrip("/\\") + "/"
SAMPLES_DIR = args.samples_dir or os.path.join(args.output, "samples")

# ── Pre-flight checks ──────────────────────────────────────────────────────────
if not os.path.exists(DATASET):
    print(f"\n[ERROR] Dataset not found: {DATASET}")
    print("  Generate it first:  python scripts/build_dataset.py")
    print(f"  Or specify a path:  python run_eval.py --dataset <path>\n")
    sys.exit(1)

os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(SAMPLES_DIR, exist_ok=True)

# ── Cache setup ────────────────────────────────────────────────────────────────
validate_cache("eval_cache")
validate_cache("baseline2_cache")

if args.clear_cache:
    for cache_file in [
        os.path.join(RESULTS_DIR, "eval_cache.json"),
        os.path.join(RESULTS_DIR, "baseline2_cache.json"),
        "results/eval_cache.json",
        "results/baseline2_cache.json",
    ]:
        if os.path.exists(cache_file):
            os.remove(cache_file)
            print(f"[Cache] Cleared {cache_file}")
    eval_cache     = {}
    baseline_cache = {}
else:
    eval_cache     = load_cache("eval_cache")
    baseline_cache = load_cache("baseline2_cache")

    # Evict old items missing agent_outputs (schema updated to single-round)
    n = invalidate_stale_items(eval_cache, required_keys=["agent_outputs", "disagreement_log"], cache_name="eval_cache")
    if n:
        print(f"[Cache] Evicted {n} stale item(s) missing 'disagreement_log' — will re-run those.")

print(f"\n[Cache] eval_cache:      {len(eval_cache.get('items', {}))} items cached")
print(f"[Cache] baseline2_cache: {len(baseline_cache.get('items', {}))} items cached")
if eval_cache.get("items") and not args.clear_cache:
    print("  To start fresh: python run_eval.py --clear-cache")


# ── PART 1: Label Classification Metrics ──────────────────────────────────────
print("\n" + "=" * 60)
print("PART 1 — LABEL CLASSIFICATION METRICS")
print("=" * 60)

print(f"\n[Running] Full Council + Judge  (dataset: {DATASET})")
print(f"  Per-sample reports → {SAMPLES_DIR}/")
council_metrics, council_true, council_pred = run_evaluation(
    DATASET, output_dir=SAMPLES_DIR
)

b2_metrics = b2_true = b2_pred = None
if not args.skip_baseline:
    print("\n[Running] Baseline 2 — Council, No Judge…")
    b2_metrics, b2_true, b2_pred = run_baseline2_majority_vote(DATASET)

print("\n--- Classification Results ---")
header = f"{'System':<35} {'Accuracy':>9} {'Precision':>10} {'Recall':>8} {'F1':>8}"
print(header)
print("-" * len(header))
print(f"{'Full Council + Judge':<35} {council_metrics['accuracy']:>9.4f} {council_metrics['precision']:>10.4f} {council_metrics['recall']:>8.4f} {council_metrics['f1_score']:>8.4f}")
if b2_metrics:
    print(f"{'Baseline 2 (Council No Judge)':<35} {b2_metrics['accuracy']:>9.4f} {b2_metrics['precision']:>10.4f} {b2_metrics['recall']:>8.4f} {b2_metrics['f1_score']:>8.4f}")

print("\nDetailed Classification Report (Full Council):")
print(council_metrics["report"])


# ── PART 2: Output Richness Metrics ───────────────────────────────────────────
richness = None
if not args.skip_richness:
    RICHNESS_DATASET = "data/sample_threats.json"
    if not os.path.exists(RICHNESS_DATASET):
        print(f"\n[WARN] Richness dataset not found ({RICHNESS_DATASET}) — skipping richness eval.")
    else:
        print("\n" + "=" * 60)
        print("PART 2 — OUTPUT RICHNESS METRICS")
        print("=" * 60)

        richness = run_richness_comparison(RICHNESS_DATASET)

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
            single_val  = richness["single_agent"][d]
            council_val = richness["full_council"][d]
            marker = " <--" if d == "total" else ""
            print(f"{dim_labels[d]:<30} {single_val:>14.3f} {council_val:>14.3f}{marker}")


# ── PART 3: Save all results ───────────────────────────────────────────────────
# Aggregate disagreement stats from cache
_items = load_cache("eval_cache").get("items", {})
classification_conflicts = sum(
    1 for v in _items.values()
    if isinstance(v.get("disagreement_log"), dict)
    and v["disagreement_log"].get("classification", {}).get("disagree")
)
severity_conflicts = sum(
    1 for v in _items.values()
    if isinstance(v.get("disagreement_log"), dict)
    and v["disagreement_log"].get("severity", {}).get("disagree")
)
output_payload = {
    "full_council_metrics":  {k: v for k, v in council_metrics.items() if k != "report"},
    "council_predictions":   list(zip(council_true, council_pred)),
    "disagreement_stats": {
        "classification_conflicts": classification_conflicts,
        "severity_conflicts":       severity_conflicts,
        "samples_evaluated":        len(_items),
    },
}
if b2_metrics:
    output_payload["baseline2_metrics"]     = {k: v for k, v in b2_metrics.items() if k != "report"}
    output_payload["baseline2_predictions"] = list(zip(b2_true, b2_pred))
if richness:
    output_payload["richness_comparison"] = richness

results_file = os.path.join(RESULTS_DIR, "eval_results.json")
with open(results_file, "w", encoding="utf-8") as f:
    json.dump(output_payload, f, indent=2)

print(f"\n\nPer-sample reports saved to: {SAMPLES_DIR}/")
print(f"All results saved to:        {results_file}")
print(f"\nDisagreement stats:")
print(f"  Classification conflicts : {classification_conflicts}")
print(f"  Severity conflicts       : {severity_conflicts}")
print(f"  Total agent revisions    : {revised_agents}")
print(f"  Samples evaluated        : {len(_items)}")
print("=" * 60)
