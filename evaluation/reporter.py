"""
evaluation/reporter.py — Results reporter: PNG charts + CSV export.

Called by run_eval.py and run_baselines.py after metrics are computed.
All outputs land in the results/ directory.

Outputs per evaluation run
──────────────────────────
  results/<prefix>_metrics.csv        — per-class precision/recall/F1 + macro/weighted
  results/<prefix>_confusion.png      — confusion matrix heatmap
  results/<prefix>_metrics_bar.png    — accuracy / precision / recall / F1 bar chart
  results/<prefix>_predictions.csv    — per-sample true vs predicted labels
"""

import os
import csv
import json
from datetime import datetime

import numpy as np
import matplotlib
matplotlib.use("Agg")           # headless rendering — no display required
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report

RESULTS_DIR = "results"

# ─── Palette (Paper-friendly: minimal, professional) ──────────────

WHITE      = "#ffffff"
LIGHT_GRAY = "#f5f5f5"
DARK_GRAY  = "#333333"
GRAY       = "#666666"
LIGHT_BORDER = "#cccccc"
BLACK      = "#000000"

# Grayscale bars with subtle differentiation
BAR_1      = "#4a4a4a"  # Dark gray
BAR_2      = "#6b6b6b"  # Medium gray
BAR_3      = "#8a8a8a"  # Light gray
BAR_4      = "#a0a0a0"  # Lighter gray

plt.rcParams.update({
    "figure.facecolor":  WHITE,
    "axes.facecolor":    WHITE,
    "axes.edgecolor":    LIGHT_BORDER,
    "axes.labelcolor":   DARK_GRAY,
    "axes.titlecolor":   BLACK,
    "xtick.color":       DARK_GRAY,
    "ytick.color":       DARK_GRAY,
    "text.color":        DARK_GRAY,
    "grid.color":        LIGHT_BORDER,
    "grid.linewidth":    0.8,
    "font.family":       "sans-serif",
    "font.size":         10,
})


# ── Public entry point ───────────────────────────────────────────

def save_report(
    prefix: str,
    system_label: str,
    metrics: dict,
    true_labels: list,
    pred_labels: list,
    label_order = None,
) -> dict:
    """
    Generate and save all report artefacts for one evaluation run.

    Args:
        prefix       : filename prefix (e.g. 'council', 'baseline1', 'baseline2')
        system_label : human-readable system name for chart titles
        metrics      : dict from compute_metrics()
        true_labels  : ground-truth label list
        pred_labels  : predicted label list
        label_order  : optional fixed label order for confusion matrix axes

    Returns:
        dict mapping artefact type → saved path
    """
    os.makedirs(RESULTS_DIR, exist_ok=True)

    paths = {}
    paths["metrics_csv"]     = _save_metrics_csv(prefix, system_label, metrics, true_labels, pred_labels)
    paths["predictions_csv"] = _save_predictions_csv(prefix, true_labels, pred_labels)
    paths["confusion_png"]   = _save_confusion_matrix(prefix, system_label, true_labels, pred_labels, label_order)
    paths["metrics_bar_png"] = _save_metrics_bar(prefix, system_label, metrics)

    print(f"\n  Reports saved:")
    for kind, path in paths.items():
        print(f"     {path}")

    return paths


# ── CSV exports ──────────────────────────────────────────────────

def _save_metrics_csv(prefix, system_label, metrics, true_labels, pred_labels):
    path = os.path.join(RESULTS_DIR, f"{prefix}_metrics.csv")
    report = classification_report(
        true_labels, pred_labels,
        output_dict=True, zero_division=0
    )

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["system", "label", "precision", "recall", "f1_score", "support"])
        for label, vals in report.items():
            if isinstance(vals, dict):
                w.writerow([
                    system_label, label,
                    round(vals["precision"], 4),
                    round(vals["recall"],    4),
                    round(vals["f1-score"],  4),
                    int(vals["support"]) if vals["support"] == int(vals["support"]) else vals["support"],
                ])
        # overall summary row
        w.writerow([])
        w.writerow(["system", "accuracy", "precision_w", "recall_w", "f1_w"])
        w.writerow([
            system_label,
            round(metrics["accuracy"],  4),
            round(metrics["precision"], 4),
            round(metrics["recall"],    4),
            round(metrics["f1_score"],  4),
        ])
    return path


def _save_predictions_csv(prefix, true_labels, pred_labels):
    path = os.path.join(RESULTS_DIR, f"{prefix}_predictions.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["#", "true_label", "predicted_label", "correct"])
        for i, (t, p) in enumerate(zip(true_labels, pred_labels), 1):
            w.writerow([i, t, p, "✓" if t == p else "✗"])
    return path


# ── Confusion matrix ─────────────────────────────────────────────

def _save_confusion_matrix(prefix, system_label, true_labels, pred_labels, label_order):
    labels = label_order or sorted(set(true_labels) | set(pred_labels))
    cm = confusion_matrix(true_labels, pred_labels, labels=labels)

    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor(WHITE)

    # Normalise for colour intensity but annotate with raw counts
    cm_norm = cm.astype(float) / (cm.sum(axis=1, keepdims=True) + 1e-9)

    # Use grayscale colormap for academic paper
    sns.heatmap(
        cm_norm, annot=cm, fmt="d",
        xticklabels=labels, yticklabels=labels,
        cmap="Greys",
        linewidths=1.0, linecolor=WHITE,
        ax=ax,
        annot_kws={"size": 10, "color": BLACK},
        cbar_kws={"label": "Row-normalised proportion"},
    )

    ax.set_title(f"Confusion Matrix — {system_label}", pad=14, fontsize=12, fontweight="bold")
    ax.set_xlabel("Predicted Label", labelpad=10, fontsize=11)
    ax.set_ylabel("True Label",      labelpad=10, fontsize=11)
    ax.tick_params(axis="x", rotation=35)
    ax.tick_params(axis="y", rotation=0)

    # No watermark for paper
    plt.tight_layout()
    path = os.path.join(RESULTS_DIR, f"{prefix}_confusion.png")
    plt.savefig(path, dpi=300, bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)
    return path


# ── Metrics bar chart ────────────────────────────────────────────

def _save_metrics_bar(prefix, system_label, metrics):
    names  = ["Accuracy", "Precision", "Recall", "F1 Score"]
    values = [
        metrics["accuracy"],
        metrics["precision"],
        metrics["recall"],
        metrics["f1_score"],
    ]
    # Grayscale colors for paper
    colours = [BAR_1, BAR_2, BAR_3, BAR_4]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    fig.patch.set_facecolor(WHITE)

    bars = ax.bar(names, values, color=colours, width=0.5,
                  edgecolor=DARK_GRAY, linewidth=1.0, zorder=3)

    # Value labels on bars
    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.015,
            f"{val:.4f}",
            ha="center", va="bottom",
            fontsize=10, color=BLACK, fontweight="bold"
        )

    ax.set_ylim(0, 1.12)
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))
    ax.set_title(f"Evaluation Metrics — {system_label}", pad=12, fontsize=12, fontweight="bold")
    ax.set_ylabel("Score", fontsize=11)
    ax.grid(axis="y", zorder=0, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)

    plt.tight_layout()
    path = os.path.join(RESULTS_DIR, f"{prefix}_metrics_bar.png")
    plt.savefig(path, dpi=300, bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)
    return path


# ── Comparison bar chart (for run_baselines.py) ──────────────────

def save_comparison_chart(systems: dict) -> str:
    """
    systems = {
        "label": { "accuracy": 0.8, "precision": ..., "recall": ..., "f1_score": ... },
        ...
    }
    Saves a grouped bar chart comparing all systems.
    """
    metric_names = ["Accuracy", "Precision", "Recall", "F1 Score"]
    metric_keys  = ["accuracy", "precision", "recall", "f1_score"]
    # Grayscale colors for paper
    colours      = [BAR_1, BAR_2, BAR_3, BAR_4]

    labels = list(systems.keys())
    x      = np.arange(len(labels))
    bar_w  = 0.18
    n_met  = len(metric_names)

    fig, ax = plt.subplots(figsize=(max(8, len(labels) * 2.5), 5))
    fig.patch.set_facecolor(WHITE)

    for i, (key, colour, name) in enumerate(zip(metric_keys, colours, metric_names)):
        vals   = [systems[lbl][key] for lbl in labels]
        offset = (i - n_met / 2 + 0.5) * bar_w
        rects  = ax.bar(x + offset, vals, bar_w, label=name, color=colour,
                        edgecolor=DARK_GRAY, linewidth=0.8, zorder=3)
        for rect, val in zip(rects, vals):
            ax.text(
                rect.get_x() + rect.get_width() / 2,
                rect.get_height() + 0.012,
                f"{val:.3f}",
                ha="center", va="bottom", fontsize=9, color=BLACK,
            )

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylim(0, 1.18)
    ax.set_ylabel("Score", fontsize=11)
    ax.set_title("System Comparison — Baseline vs CyberCouncil", pad=12,
                 fontsize=12, fontweight="bold")
    ax.legend(fontsize=9, facecolor=WHITE, edgecolor=LIGHT_BORDER, labelcolor=BLACK)
    ax.grid(axis="y", zorder=0, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)

    plt.tight_layout()
    path = os.path.join(RESULTS_DIR, "comparison_chart.png")
    plt.savefig(path, dpi=300, bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)
    return path
