"""
run_eval.py — Full dataset evaluation runner for the CyberCouncil pipeline.

Usage:
    python3 run_eval.py

Outputs (all in results/):
    eval_results.json          — machine-readable metrics
    council_metrics.csv        — per-class precision / recall / F1
    council_predictions.csv    — per-sample true vs predicted
    council_confusion.png      — confusion matrix heatmap
    council_metrics_bar.png    — accuracy / precision / recall / F1 bar chart
"""

import json
from evaluation.evaluator import run_evaluation
from evaluation.reporter  import save_report

DATASET_PATH = "data/threats.json"          # 50-sample dataset (run build_dataset.py first)
OUTPUT_JSON  = "results/eval_results.json"


def main():
    metrics, true_labels, pred_labels = run_evaluation(DATASET_PATH)

    print("\n" + "=" * 50)
    print("  CYBERCOUNCIL — EVALUATION RESULTS")
    print("=" * 50)
    print(f"  Accuracy  : {metrics['accuracy']:.4f}")
    print(f"  Precision : {metrics['precision']:.4f}")
    print(f"  Recall    : {metrics['recall']:.4f}")
    print(f"  F1 Score  : {metrics['f1_score']:.4f}")
    print("\nClassification Report:")
    print(metrics["report"])

    # ── JSON (raw) ────────────────────────────────────────────
    with open(OUTPUT_JSON, "w") as f:
        json.dump({
            "system":      "CyberCouncil — Full Council + Judge",
            "dataset":     DATASET_PATH,
            "accuracy":    metrics["accuracy"],
            "precision":   metrics["precision"],
            "recall":      metrics["recall"],
            "f1_score":    metrics["f1_score"],
            "predictions": [
                {"true": t, "pred": p}
                for t, p in zip(true_labels, pred_labels)
            ]
        }, f, indent=2)
    print(f"\n  Saved JSON → {OUTPUT_JSON}")

    # ── PNG charts + CSV ──────────────────────────────────────
    save_report(
        prefix       = "council",
        system_label = "CyberCouncil (Full Council + Judge)",
        metrics      = metrics,
        true_labels  = true_labels,
        pred_labels  = pred_labels,
    )


if __name__ == "__main__":
    main()
