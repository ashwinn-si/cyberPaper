import json
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


def run_evaluation(dataset_path: str) -> tuple:
    """
    Run the CyberCouncil pipeline on a labeled dataset and compute metrics.

    Args:
        dataset_path : Path to a JSON file with items having
                       'threat_description' and 'true_label' keys.

    Returns:
        (metrics_dict, true_labels, pred_labels)
    """
    with open(dataset_path) as f:
        dataset = json.load(f)

    council = CyberCouncil()
    true_labels: list = []
    pred_labels: list = []

    for item in tqdm(dataset, desc="CyberCouncil Evaluation"):
        result    = council.analyze(item["threat_description"])
        predicted = extract_label(result["final_report"])
        true_labels.append(item["true_label"])
        pred_labels.append(predicted)
        print(f"  [{item['id']}] true={item['true_label']!r:20s}  pred={predicted!r}")

    return compute_metrics(true_labels, pred_labels), true_labels, pred_labels
