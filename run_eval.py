import sys
import asyncio
import json
import os

# Windows: use SelectorEventLoop to avoid ProactorEventLoop conflicts with ThreadPoolExecutor
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from evaluation.evaluator import run_evaluation, run_baseline2_majority_vote
from evaluation.richness_evaluator import run_richness_comparison
from evaluation.cache import load_cache, validate_cache

DATASET     = "data/threats.json"
RESULTS_DIR = "results/"
SAMPLES_DIR = "results/samples"

# ── Cache Status ──────────────────────────────────────────────────────────
# Caching enabled: completed results saved to results/eval_cache.json
# If run fails midway, restarting will skip completed items and resume from crash point.
# To force fresh run: python3 run_eval.py --clear-cache
clear_cache = "--clear-cache" in sys.argv

# Validate cache files (auto-delete if corrupted)
validate_cache("eval_cache")
validate_cache("baseline2_cache")

if clear_cache:
    for cache_file in ["results/eval_cache.json", "results/baseline2_cache.json"]:
        if os.path.exists(cache_file):
            os.remove(cache_file)
            print(f"[Cache] Cleared {cache_file}")
    eval_cache = {}
    baseline_cache = {}
else:
    eval_cache = load_cache("eval_cache")
    baseline_cache = load_cache("baseline2_cache")

print(f"\n[Cache] eval_cache: {len(eval_cache.get('items', {}))} items cached")
print(f"[Cache] baseline2_cache: {len(baseline_cache.get('items', {}))} items cached")
if eval_cache.get("items") and not clear_cache:
    print("To start fresh: python3 run_eval.py --clear-cache\n")


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
