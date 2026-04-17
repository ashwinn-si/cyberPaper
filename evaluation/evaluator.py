import json
import os
from tqdm import tqdm
from council.orchestrator import CyberCouncil
from evaluation.metrics import compute_metrics


# Canonical label set — must remain stable across all runs
LABEL_MAP = [
    "Phishing", "Malware", "SQL Injection", "DDoS",
    "Ransomware", "Zero-Day Exploit", "Insider Threat",
    "Man-in-the-Middle", "Other"
]


def extract_label(text: str) -> str:
    """
    Extract the predicted threat category from the judge's final report.

    Searches for canonical labels in priority order. Falls back to "Other"
    if no known label is found. This is consistent with the fallback used
    in baselines for fair comparison.
    """
    text_lower = text.lower()
    for label in LABEL_MAP:
        if label.lower() in text_lower:
            return label
    return "Other"


def _save_sample_report(item: dict, result: dict, predicted: str, out_dir: str) -> None:
    """Save a single sample's full input + all agent outputs to a .txt file."""
    sample_id = item.get("id", "unknown")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"sample_{sample_id:03d}.txt")

    sep  = "=" * 70
    dash = "-" * 70

    lines = []
    lines.append(sep)
    lines.append(f"  SAMPLE {sample_id}  |  True Label: {item['true_label']}  |  Predicted: {predicted}")
    lines.append(sep)
    lines.append("")
    lines.append("INPUT — Threat Description")
    lines.append(dash)
    lines.append(item["threat_description"].strip())
    lines.append("")

    if result.get("clean_threat") and result["clean_threat"].strip() != item["threat_description"].strip():
        lines.append("VALIDATOR — Enriched Threat")
        lines.append(dash)
        lines.append(result["clean_threat"].strip())
        lines.append("")

    for rnd, key in [(1, "round1_outputs"), (2, "round2_outputs")]:
        outputs = result.get(key, [])
        if not outputs:
            continue
        lines.append(f"ROUND {rnd} — Agent Outputs")
        lines.append(dash)
        for agent_out in outputs:
            lines.append(f"  [{agent_out['agent']}]  ({agent_out['provider']})")
            lines.append("")
            for ln in agent_out["output"].strip().splitlines():
                lines.append(f"    {ln}")
            lines.append("")

        judge_key = "draft_report" if rnd == 1 else "final_report"
        judge_label = "JUDGE — Draft Report" if rnd == 1 else "JUDGE — Final Report (CISO)"
        report_text = result.get(judge_key, "").strip()
        if report_text:
            lines.append(judge_label)
            lines.append(dash)
            for ln in report_text.splitlines():
                lines.append(f"  {ln}")
            lines.append("")

    lines.append(sep)
    lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def run_evaluation(dataset_path: str, output_dir: str = "results/samples") -> tuple:
    """
    Run the CyberCouncil pipeline on a labeled dataset and compute metrics.
    Saves a detailed per-sample report to output_dir/sample_<id>.txt.

    Returns:
        (metrics_dict, true_labels, pred_labels)
    """
    with open(dataset_path) as f:
        dataset = json.load(f)

    council = CyberCouncil()
    true_labels: list = []
    pred_labels: list = []

    for item in tqdm(dataset, desc="CyberCouncil Evaluation"):
        result = council.analyze_sync(item["threat_description"])
        predicted = extract_label(result["final_report"])
        true_labels.append(item["true_label"])
        pred_labels.append(predicted)
        _save_sample_report(item, result, predicted, output_dir)
        print(f"  [{item['id']}] true={item['true_label']!r:20s}  pred={predicted!r}  → saved to {output_dir}/sample_{item['id']:03d}.txt")

    return compute_metrics(true_labels, pred_labels), true_labels, pred_labels


def run_baseline2_majority_vote(dataset_path: str):
    with open(dataset_path) as f:
        dataset = json.load(f)

    council = CyberCouncil()
    true_labels, pred_labels = [], []

    for item in tqdm(dataset, desc="Baseline 2 - Council No Judge"):
        threat = item["threat_description"]
        agent_outputs = [agent.analyze(threat) for agent in council.agents]

        # Only Agent A (index 0) is a classifier — extract label from classifier only.
        # Agent B and Agent C do not output threat categories by design.
        predicted = extract_label(agent_outputs[0]["output"])

        true_labels.append(item["true_label"])
        pred_labels.append(predicted)

    return compute_metrics(true_labels, pred_labels), true_labels, pred_labels
