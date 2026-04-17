"""
run_baselines.py — Baseline comparison runner for IEEE paper evaluation tables.

Usage:
    python3 run_baselines.py

Outputs (all in results/):
    baseline_results.json          — machine-readable metrics for both baselines
    baseline1_metrics.csv          — per-class metrics, single-agent baseline
    baseline1_predictions.csv      — per-sample predictions, single-agent baseline
    baseline1_confusion.png        — confusion matrix, single-agent baseline
    baseline1_metrics_bar.png      — bar chart, single-agent baseline
    baseline2_metrics.csv          — per-class metrics, majority-vote baseline
    baseline2_predictions.csv      — per-sample predictions, majority-vote baseline
    baseline2_confusion.png        — confusion matrix, majority-vote baseline
    baseline2_metrics_bar.png      — bar chart, majority-vote baseline
    comparison_chart.png           — grouped bar chart comparing both baselines
"""

import sys
import asyncio
import json
import os

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from evaluation.baselines import run_single_agent_baseline, run_majority_vote_baseline
from evaluation.reporter  import save_report, save_comparison_chart

DATASET_PATH = "data/threats.json"
OUTPUT_JSON  = "results/baseline_results.json"
os.makedirs("results", exist_ok=True)


def print_metrics(label: str, metrics: dict):
    print(f"\n  {label}")
    print(f"    Accuracy  : {metrics['accuracy']:.4f}")
    print(f"    Precision : {metrics['precision']:.4f}")
    print(f"    Recall    : {metrics['recall']:.4f}")
    print(f"    F1 Score  : {metrics['f1_score']:.4f}")


def main():
    print("\n" + "=" * 55)
    print("  BASELINE 1 — Single Agent (no council, no judge)")
    print("=" * 55)
    b1_metrics, b1_true, b1_pred = run_single_agent_baseline(DATASET_PATH)

    print("\n" + "=" * 55)
    print("  BASELINE 2 — Majority Vote (all agents, no judge)")
    print("=" * 55)
    b2_metrics, b2_true, b2_pred = run_majority_vote_baseline(DATASET_PATH)

    print("\n" + "=" * 55)
    print("  RESULTS SUMMARY")
    print("=" * 55)
    print_metrics("Baseline 1 — Single Agent",  b1_metrics)
    print_metrics("Baseline 2 — Majority Vote", b2_metrics)
    print()
    print("  -> Compare these against run_eval.py (Full Council + Judge)\n")

    # ── JSON (raw) ─────────────────────────────────────────────
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump({
            "baseline_1_single_agent": {
                "accuracy":    b1_metrics["accuracy"],
                "precision":   b1_metrics["precision"],
                "recall":      b1_metrics["recall"],
                "f1_score":    b1_metrics["f1_score"],
                "predictions": [{"true": t, "pred": p} for t, p in zip(b1_true, b1_pred)],
            },
            "baseline_2_majority_vote": {
                "accuracy":    b2_metrics["accuracy"],
                "precision":   b2_metrics["precision"],
                "recall":      b2_metrics["recall"],
                "f1_score":    b2_metrics["f1_score"],
                "predictions": [{"true": t, "pred": p} for t, p in zip(b2_true, b2_pred)],
            },
        }, f, indent=2)
    print(f"  Saved JSON -> {OUTPUT_JSON}")

    # ── Per-baseline PNG charts + CSV ──────────────────────────
    save_report(
        prefix       = "baseline1",
        system_label = "Baseline 1 — Single Agent",
        metrics      = b1_metrics,
        true_labels  = b1_true,
        pred_labels  = b1_pred,
    )
    save_report(
        prefix       = "baseline2",
        system_label = "Baseline 2 — Majority Vote",
        metrics      = b2_metrics,
        true_labels  = b2_true,
        pred_labels  = b2_pred,
    )

    # ── Grouped comparison chart ───────────────────────────────
    comparison_path = save_comparison_chart({
        "Single Agent\n(Baseline 1)":  b1_metrics,
        "Majority Vote\n(Baseline 2)": b2_metrics,
    })
    print(f"\n  Comparison chart -> {comparison_path}")


if __name__ == "__main__":
    main()
