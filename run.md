# CyberCouncil — Run Guide

## 1. Setup

```bash
# Clone and enter project
cd cyberPaper

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt
```

## 2. API Keys

```bash
cp .env.example .env
```

Edit `.env` and fill in your keys:

```
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here
```

> At least one key is required. Configure which models are used per agent in `config/agent_config.py`.

---

## 3. Web Frontend (Recommended)

Start the API server — this also serves the UI:

```bash
python3 server.py
```

Open **http://127.0.0.1:5050** in your browser.

- Type or paste a threat description, or click an example chip (Phishing, Ransomware, etc.)
- Press **Analyze Threat** or `Ctrl+Enter`
- See each agent's output and the Judge's final CISO report

---

## 4. CLI — Single Threat Test

Edit the `threat` variable in `main.py`, then:

```bash
python3 main.py
```

---

## 5. Build the Evaluation Dataset

Generates `data/threats.json` — 50 labeled samples across all 9 threat categories:

```bash
python3 scripts/build_dataset.py

# Custom output path
python3 scripts/build_dataset.py --out data/custom.json
```

---

## 6. Run Evaluation (Full Council)

```bash
python3 run_eval.py
```

Saves the following to `results/`:

| File | Description |
|---|---|
| `eval_results.json` | Raw metrics (accuracy, precision, recall, F1) |
| `council_metrics.csv` | Per-class precision / recall / F1 + support |
| `council_predictions.csv` | Per-sample true vs predicted label |
| `council_confusion.png` | Confusion matrix heatmap |
| `council_metrics_bar.png` | Accuracy / precision / recall / F1 bar chart |

> Update `DATASET_PATH` in `run_eval.py` to `data/threats.json` for the full 50-sample run.

---

## 7. Run Baselines (for IEEE Paper)

```bash
python3 run_baselines.py
```

Saves for each baseline (`baseline1_*`, `baseline2_*`):
- `_metrics.csv`, `_predictions.csv`, `_confusion.png`, `_metrics_bar.png`

Plus a grouped comparison chart: `results/comparison_chart.png`.

---

## 8. Viewing Results (Images and CSVs)

All evaluation runs output a combination of images (PNG) and spreadsheets (CSV) to the `results/` directory for use in your IEEE research paper.

- **Images (`.png`)**: Open these directly in your OS image viewer or embed them in your document. Includes confusion matrices (`*_confusion.png`), metric bar charts (`*_metrics_bar.png`), and model comparisons (`comparison_chart.png`).
- **Data (`.csv`)**: Open these in Microsoft Excel, Google Sheets, or Apple Numbers to perform further statistical analysis. You can also import these directly into LaTeX/Word.


---

## 9. Swap Providers

Edit **only** `config/agent_config.py`:

```python
AGENT_A_PROVIDER = ClaudeProvider()       # or OpenAIProvider()
AGENT_B_PROVIDER = OpenAIProvider()
AGENT_C_PROVIDER = OpenAIProvider("gpt-4-turbo")
JUDGE_PROVIDER   = ClaudeProvider()
```

No other code changes needed.

---

## Quick Reference

| Command | Description |
|---|---|
| `python3 server.py` | Start web UI at localhost:5050 |
| `python3 main.py` | Run one threat in the terminal |
| `python3 scripts/build_dataset.py` | Build 50-sample dataset |
| `python3 run_eval.py` | Full evaluation (council + judge) |
| `python3 run_baselines.py` | Baseline comparison |
