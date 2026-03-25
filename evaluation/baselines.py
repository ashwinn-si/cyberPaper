"""
Baseline implementations for ablation and comparison studies.

Baseline 1 — Single Agent (no council):
    Uses only Agent A (Classifier) with a minimal prompt.
    Represents the simplest LLM-based approach. Establishes the floor.

Baseline 2 — Majority Vote (no judge):
    Runs all 3 agents but combines results via majority vote instead of judge synthesis.
    Tests whether the judge adds value beyond simple voting.

Both baselines use the same label extraction and metrics pipeline as the
full council evaluation, ensuring fair comparison for IEEE paper tables.
"""

import json
from collections import Counter
from tqdm import tqdm
from config.agent_config import AGENT_A_PROVIDER
from evaluation.metrics import compute_metrics
from evaluation.evaluator import extract_label, LABEL_MAP
from agents.classifier_agent import ClassifierAgent
from agents.vuln_agent import VulnAgent
from agents.impact_agent import ImpactAgent


# ─────────────────────────────────────────────────────────────────
#  Baseline 1 — Single Agent
# ─────────────────────────────────────────────────────────────────

_BASELINE_SYSTEM_PROMPT = (
    "You are a cybersecurity expert. "
    "Classify this threat as exactly one of: "
    + " | ".join(LABEL_MAP)
    + ". Output the label only. No explanation."
)


def run_single_agent_baseline(dataset_path: str) -> tuple:
    """
    Baseline 1: Only Agent A's provider with a minimal system prompt.
    No specialist agents, no judge.

    Returns: (metrics_dict, true_labels, pred_labels)
    """
    with open(dataset_path) as f:
        dataset = json.load(f)

    true_labels: list = []
    pred_labels: list = []

    for item in tqdm(dataset, desc="Baseline 1 — Single Agent"):
        output    = AGENT_A_PROVIDER.complete(
            system_prompt=_BASELINE_SYSTEM_PROMPT,
            user_message=item["threat_description"]
        )
        predicted = extract_label(output)
        true_labels.append(item["true_label"])
        pred_labels.append(predicted)
        print(f"  [{item['id']}] true={item['true_label']!r:20s}  pred={predicted!r}")

    return compute_metrics(true_labels, pred_labels), true_labels, pred_labels


# ─────────────────────────────────────────────────────────────────
#  Baseline 2 — Majority Vote (no judge)
# ─────────────────────────────────────────────────────────────────

def run_majority_vote_baseline(dataset_path: str) -> tuple:
    """
    Baseline 2: All 3 specialist agents run independently; result is majority vote.
    No judge synthesis step.

    Returns: (metrics_dict, true_labels, pred_labels)
    """
    with open(dataset_path) as f:
        dataset = json.load(f)

    agents = [ClassifierAgent(), VulnAgent(), ImpactAgent()]

    true_labels: list = []
    pred_labels: list = []

    for item in tqdm(dataset, desc="Baseline 2 — Majority Vote"):
        outputs   = [agent.analyze(item["threat_description"]) for agent in agents]
        labels    = [extract_label(o["output"]) for o in outputs]
        predicted = Counter(labels).most_common(1)[0][0]
        true_labels.append(item["true_label"])
        pred_labels.append(predicted)
        print(f"  [{item['id']}] true={item['true_label']!r:20s}  pred={predicted!r}  votes={labels}")

    return compute_metrics(true_labels, pred_labels), true_labels, pred_labels
