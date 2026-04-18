import json
import os
from tqdm import tqdm
from council.orchestrator import CyberCouncil
from evaluation.metrics import compute_metrics
from evaluation.cache import load_cache, add_to_cache, get_cached_ids


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

    outputs = result.get("agent_outputs", [])
    if outputs:
        lines.append("AGENT OUTPUTS")
        lines.append(dash)
        for agent_out in outputs:
            lines.append(f"  [{agent_out['agent']}]  ({agent_out['provider']})")
            lines.append("")
            for ln in agent_out["output"].strip().splitlines():
                lines.append(f"    {ln}")
            lines.append("")

    report_text = result.get("final_report", "").strip()
    if report_text:
        lines.append("JUDGE — Final Report (CISO)")
        lines.append(dash)
        for ln in report_text.splitlines():
            lines.append(f"  {ln}")
        lines.append("")

    # Disagreement log section
    log = result.get("disagreement_log", {})
    if log:
        lines.append("CONSENSUS / DISAGREEMENT LOG")
        lines.append(dash)
        cl = log.get("classification", {})
        sv = log.get("severity", {})
        lines.append(f"  Classification: A1={cl.get('agent_a_primary')}  A2={cl.get('agent_a_secondary')}  conflict={cl.get('disagree')}")
        lines.append(f"  Severity:       C1={sv.get('agent_c_primary')}  C2={sv.get('agent_c_secondary')}  conflict={sv.get('disagree')}")
        lines.append("")

    lines.append(sep)
    lines.append("")

    with open(path, "w", encoding="utf-8", errors="replace") as f:
        f.write("\n".join(lines))


def run_evaluation(dataset_path: str, output_dir: str = "results/samples", use_cache: bool = True) -> tuple:
    """
    Run the CyberCouncil pipeline on a labeled dataset and compute metrics.
    Saves a detailed per-sample report to output_dir/sample_<id>.txt.

    Supports resumable checkpointing: completed items cached in results/eval_cache.json
    Skip with use_cache=False to force full re-evaluation.

    Returns:
        (metrics_dict, true_labels, pred_labels)
    """
    with open(dataset_path, encoding="utf-8") as f:
        dataset = json.load(f)

    # Load cache
    cache = load_cache("eval_cache") if use_cache else {}
    cached_ids = get_cached_ids(cache)
    new_items = [item for item in dataset if str(item["id"]) not in cached_ids]

    if cached_ids:
        print(f"[Cache] Loaded {len(cached_ids)} completed results. Processing {len(new_items)} new items.")

    council = CyberCouncil()
    true_labels: list = []
    pred_labels: list = []

    # Process new items
    for item in tqdm(new_items, desc="CyberCouncil Evaluation"):
        result = council.analyze_sync(item["threat_description"])

        # Validator asked clarifying questions — force pass-two with a neutral answer
        if result["status"] == "needs_clarification":
            print(f"  [{item['id']}] needs_clarification — re-running with neutral answer")
            result = council.analyze_sync(
                item["threat_description"],
                user_answers="No additional context available. Proceed with best available information."
            )

        if result["status"] == "rejected":
            print(f"  [{item['id']}] SKIPPED — validator rejected input")
            add_to_cache(cache, item["id"], {"status": "rejected"}, "eval_cache")
            continue
        predicted = extract_label(result["final_report"])

        # Save cache immediately (so we can resume if it crashes)
        result["predicted_label"] = predicted
        result["true_label"] = item["true_label"]
        add_to_cache(cache, item["id"], result, "eval_cache")

        # Save detailed report
        _save_sample_report(item, result, predicted, output_dir)
        print(f"  [{item['id']}] true={item['true_label']!r:20s}  pred={predicted!r}  → saved to {output_dir}/sample_{item['id']:03d}.txt")

    # Collect all results (cached) for metrics computation
    for item in dataset:
        item_id = str(item["id"])
        if item_id in cache.get("items", {}):
            cached_result = cache["items"][item_id]
            if cached_result.get("status") == "rejected":
                continue  # Skip rejected items
            true_labels.append(cached_result.get("true_label", item["true_label"]))
            pred_labels.append(cached_result.get("predicted_label", "Other"))

    return compute_metrics(true_labels, pred_labels), true_labels, pred_labels


def run_baseline2_majority_vote(dataset_path: str, use_cache: bool = True):
    """
    Baseline 2: Council without Judge (majority vote of agents).
    Supports caching for resumable runs.
    """
    with open(dataset_path, encoding="utf-8") as f:
        dataset = json.load(f)

    cache = load_cache("baseline2_cache") if use_cache else {}
    cached_ids = get_cached_ids(cache)
    new_items = [item for item in dataset if str(item["id"]) not in cached_ids]

    if cached_ids:
        print(f"[Cache] Loaded {len(cached_ids)} baseline2 results. Processing {len(new_items)} new items.")

    council = CyberCouncil()
    true_labels, pred_labels = [], []

    for item in tqdm(new_items, desc="Baseline 2 - Council No Judge"):
        threat = item["threat_description"]
        agent_outputs = [agent.analyze(threat) for agent in council.agents]

        # Agents at index 0 (A) and 1 (A₂) are classifiers — use A primary for label
        predicted = extract_label(agent_outputs[0]["output"])

        result = {"predicted_label": predicted, "true_label": item["true_label"], "agent_outputs": [ao.get("output", "") for ao in agent_outputs]}
        add_to_cache(cache, item["id"], result, "baseline2_cache")

    # Collect all cached results for metrics computation
    for item in dataset:
        item_id = str(item["id"])
        if item_id in cache.get("items", {}):
            cached_result = cache["items"][item_id]
            true_labels.append(cached_result.get("true_label", item["true_label"]))
            pred_labels.append(cached_result.get("predicted_label", "Other"))

    return compute_metrics(true_labels, pred_labels), true_labels, pred_labels
