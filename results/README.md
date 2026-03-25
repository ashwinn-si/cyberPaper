# CyberCouncil — Evaluation Results

This directory contains the empirical results of evaluating the CyberCouncil multi-agent threat analysis system against a curated dataset of 50 cybersecurity threats.

## Project Overview

**CyberCouncil** is a multi-agent LLM council designed for cybersecurity threat detection, classification, and response synthesis. It uses an extensible provider pattern allowing any agent to be backed by different LLMs (e.g., Claude, GPT-4).

The architecture consists of:
- **Agent A (Threat Classifier)**: Identifies the threat category.
- **Agent B (Vulnerability Analyst)**: Maps the threat to CVE and MITRE ATT&CK.
- **Agent C (Impact Assessor)**: Scores severity and recommends immediate actions.
- **Judge Agent (CISO)**: Synthesizes the specialist reports into a single, authoritative threat assessment and resolves any contradictions between agents.

## Evaluation Methodology

The system was evaluated on a curated dataset of 50 threat descriptions covering 9 canonical categories (Phishing, Malware, SQL Injection, DDoS, Ransomware, Zero-Day Exploit, Insider Threat, Man-in-the-Middle, Other).

We compared the full **CyberCouncil (Full Council + Judge)** against two baselines:
1. **Baseline 1 (Single Agent)**: Uses only the Threat Classifier with a highly constrained prompt to output exactly one label and nothing else.
2. **Baseline 2 (Majority Vote)**: Runs all three specialist agents, but bypasses the Judge and simply takes the majority vote of their predicted labels.

## Empirical Results

The evaluation yielded the following metrics across the 50 samples:

| System | Accuracy | Precision | Recall | F1 Score |
|---|---|---|---|---|
| **Baseline 1 (Single Agent)** | **0.960** | **0.962** | **0.960** | **0.960** |
| **CyberCouncil (Full Council + Judge)** | 0.780 | 0.824 | 0.780 | 0.785 |
| **Baseline 2 (Majority Vote)** | 0.480 | 0.711 | 0.480 | 0.513 |

### Analysis of Findings

1. **Single Agent Outperforms Multi-Agent for Simple Classification**: Baseline 1 achieved the highest F1 score (0.960). Because its prompt is strictly constrained to output *only* the canonical label, it rarely deviates. 
2. **Judge Synthesis Adds Complexity**: The Full Council achieved a lower classification score (0.785 F1). When the Judge reads the complex, multi-faceted reports from the Vulnerability Analyst and Impact Assessor alongside the Classifier, it occasionally gets distracted by secondary elements of the threat and overrides the correct primary classification (e.g., misclassifying a Malware beacon as Phishing due to context).
3. **Majority Vote is Ineffective Here**: Baseline 2 performed the worst (0.513 F1). Because Agent B and Agent C are not prompted to classify the threat (their prompts explicitly forbid it), extracting a classification label from their output introduces significant noise, causing the majority vote to often fail.
4. **Value of the Council**: While Baseline 1 wins at simple categorization, it outputs exactly one word. The full CyberCouncil provides a comprehensive CISO-level report, complete with MITRE ATT&CK mappings, severity scores, and actionable incident response plans—capabilities far beyond simple classification.

## Directory Contents

The evaluation scripts automatically generate data and chart artifacts in this directory:

- `eval_results.json` / `baseline_results.json`: Raw evaluation data and predictions.
- `*_metrics.csv`: Detailed per-class precision, recall, and F1 scores.
- `*_predictions.csv`: Sample-by-sample true vs predicted labels.
- `*_confusion.png`: Confusion matrix heatmaps for error analysis.
- `*_metrics_bar.png`: Graphical representation of the core metrics.
- `comparison_chart.png`: A grouped bar chart comparing all three systems side-by-side.
