# CyberCouncil — Step-by-Step Run Guide (Windows)

**For:** RTX 5060 Ti (34GB GPU-accessible) + 32GB RAM + Intel Core Ultra 9

**OS:** Windows 10 / 11

**Execution Model:** Parallel (5–10 sec per threat)

---

## Prerequisites Check

Before starting, verify your system:

### Check GPU
```cmd
nvidia-smi
```
Should show: NVIDIA RTX 5060 Ti with 16GB memory

### Check System RAM
```cmd
wmic OS get TotalVisibleMemorySize
```
Should show: ~33+ GB (32GB in bytes)

### Check Disk Space
```cmd
dir C:\
```
Should show: 954GB available

### Check Python
```cmd
python --version
```
Should be: Python 3.10 or higher

### Check if Ollama is Installed
```cmd
ollama --version
```
If not installed, follow "Step 0" below

---

## Step 0: Install Ollama (If Not Done)

### Windows

1. Download from: https://ollama.ai/download
2. Run the installer
3. Follow on-screen instructions
4. Ollama will start automatically as a service

**Verify in Command Prompt or PowerShell:**
```cmd
ollama --version
```

If you see version number, Ollama is installed. ✓

---

## Step 1: Clone & Setup Project

### Open Command Prompt or PowerShell

```cmd
# Navigate to project
cd C:\Users\ashwinsi\paper\cyberPaper

# Create Python virtual environment
python -m venv venv

# Activate environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Expected output:** No errors, all packages installed.

Your command prompt should now show `(venv)` prefix.

---

## Step 2: Configure Environment

```cmd
# Copy template
copy .env.example .env

# Edit .env (use Notepad or your preferred editor)
notepad .env
```

**What to check in `.env`:**
- `OLLAMA_API_BASE=http://localhost:11434` (default is fine)
- Save and close

No changes needed unless Ollama is on different machine.

---

## Step 3: Start Ollama Service

Ollama should already be running as a Windows service. **Verify it's running:**

```cmd
# Check if Ollama process is running
tasklist | findstr ollama
```

Should show `OllamaServer.exe` or similar.

**If not running:**

1. Open Start Menu
2. Search "Ollama"
3. Click "Ollama" to launch

**Or start from command prompt:**
```cmd
ollama serve
```

Keep this window open, or let it run in background.

---

## Step 4: Pull Models (Security-Specialized)

**RECOMMENDED:** Pull all specialized threat analysis models for best accuracy.

**Open NEW Command Prompt or PowerShell window** (keep Ollama running in first window):

```cmd
# Navigate to project
cd C:\Users\ashwinsi\paper\cyberPaper

# Activate venv
venv\Scripts\activate

# Pull all specialized security models (RECOMMENDED)
ollama pull foundation-sec-8b-reasoning
ollama pull llama-3.1-foundationai-securityllm-8b
ollama pull gemma-2-27b-security
ollama pull deepseek-r1
ollama pull mistral-nemo
ollama pull qwen2.5
```

**Expected:**
- Foundation-Sec-8B: ~5 min
- Llama-Sec-8B: ~5 min
- Gemma-2-27B: ~10 min
- DeepSeek-R1-33B: ~15 min
- Mistral-Nemo-12B: ~7 min
- Qwen2.5-72B: ~20 min
- **Total: ~60 minutes**

**Verify:**
```cmd
ollama list
```

Should show all 6 models:
```
NAME                                    ID              SIZE      MODIFIED
foundation-sec-8b-reasoning:latest      ...             4.7GB     ...
llama-3.1-foundationai-securityllm-8b   ...             4.7GB     ...
gemma-2-27b-security:latest             ...             13GB      ...
deepseek-r1:latest                      ...             18GB      ...
mistral-nemo:latest                     ...             7GB       ...
qwen2.5:latest                          ...             37GB      ...
```

---

### Alternative: Pull Only Llama-3 (Faster, Generic Models)

If you prefer faster setup and don't need maximum accuracy:

```cmd
ollama pull llama3
ollama pull qwen2.5
```

**Expected:**
- Llama-3: ~5 minutes
- Qwen2.5: ~10 minutes
- **Total: ~15 minutes**

This is already configured as fallback in `config/agent_config.py`.

---

## Step 5: Verify Ollama Connectivity

```cmd
# Test Ollama endpoint
curl http://localhost:11434/api/tags
```

Should return JSON with model list. If you get "Connection refused", Ollama is not running.

---

## Step 6: Test with Single Threat

```cmd
# Make sure venv is activated
# Command prompt should show (venv) prefix

python main.py
```

**What happens:**
1. Validator checks threat (2–3 sec)
2. Agents A, B, C, D run in parallel (3–5 sec)
3. Judge synthesizes (3–5 sec)
4. **Total: 5–10 sec**

**Expected output:**
```
Status: analyzed
Threat: [your threat]
Classification: [Agent A output]
Vulnerabilities: [Agent B output]
Impact: [Agent C output]
Remediation: [Agent D output]
Final Report: [Judge synthesis]
```

If this works, everything is set up correctly. ✓

---

## Step 7: Run Local Tests (Quick Validation)

```cmd
python tests/test_local.py
```

**Expected:**
- All 4 tests pass
- Total time: ~20–40 seconds
- No OOM errors

---

## Step 8: Generate Full Dataset

```cmd
python scripts/build_dataset.py
```

**What it does:**
- Creates 50 threat samples
- Saves to `data/threats.json`
- **Time: <1 minute**

**Verify:**
```cmd
# Count lines in file
find /v /c "" data\threats.json
```

Should show ~100+ lines (50 threats in JSON format)

---

## Step 9: Run Full Evaluation

```cmd
python run_eval.py
```

**What it does:**
- Runs all 50 threats through council
- Computes metrics (accuracy, precision, recall, F1)
- Generates confusion matrix & bar charts
- **Time: ~5–10 minutes** (50 threats × 5–10 sec each)

**Monitor progress (in another Command Prompt):**
```cmd
# List results directory
dir results\
```

**Expected output files:**
```
results\
├── eval_results.json          # Raw metrics
├── council_metrics.csv        # Per-threat predictions
├── council_confusion.png      # Confusion matrix (grayscale)
└── council_metrics_bar.png    # Accuracy/Precision/Recall bars
```

---

## Step 10: Run Baseline Comparisons

```cmd
python run_baselines.py
```

**What it does:**
- Compares:
  1. Single Agent A (no council)
  2. Majority vote (no judge)
  3. Full council + judge
- Generates comparison chart
- **Time: ~5–10 minutes**

**Expected output:**
```
results\
└── comparison_chart.png       # Side-by-side comparison (grayscale)
```

---

## Step 11: View Results

### View in Command Prompt

```cmd
# View evaluation metrics
type results\eval_results.json

# View predictions (first 20 lines)
findstr /r ".*" results\council_metrics.csv | more
```

### View Confusion Matrix

```cmd
# Open in default image viewer
start results\council_confusion.png
```

### View Comparison Chart

```cmd
start results\comparison_chart.png
```

---

## Step 12 (Optional): Run Web UI

```cmd
python server.py
```

**Expected:**
```
Flask app running on http://127.0.0.1:5050
```

**Open browser:**
```
http://127.0.0.1:5050
```

**Features:**
- Submit threats via web form
- View real-time analysis
- Dark SOC theme UI

**To stop:** `Ctrl+C` in terminal

---

## Quick Reference: Complete Workflow

**Terminal 1:** Keep Ollama running (background service)

**Terminal 2:** Run all commands:

```cmd
# Setup (first time only)
cd C:\Users\ashwinsi\paper\cyberPaper
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env

# Pull specialized security models (RECOMMENDED - ~60 min)
ollama pull foundation-sec-8b-reasoning
ollama pull llama-3.1-foundationai-securityllm-8b
ollama pull gemma-2-27b-security
ollama pull deepseek-r1
ollama pull mistral-nemo
ollama pull qwen2.5

# Verify setup
python main.py                # Test single threat (~5–10 sec)
python tests/test_local.py    # Test suite (~20–40 sec)

# Generate & evaluate
python scripts/build_dataset.py      # Create 50 threats (~1 min)
python run_eval.py                   # Full eval (~5–10 min)
python run_baselines.py              # Baselines (~5–10 min)

# View results
type results\eval_results.json
start results\council_confusion.png
start results\comparison_chart.png

# Optional: Web UI
python server.py  # Open http://127.0.0.1:5050 in browser
```

**Total time (first run):** ~120 minutes (includes 60 min model pulls)  
**Total time (subsequent runs, skip model pull):** ~15 minutes

---

### Fast Setup (Llama-3 Only - Optional)

If you want faster initial setup without specialized models:

```cmd
# Pull only generic models (~15 min instead of 60 min)
ollama pull llama3
ollama pull qwen2.5

# Then edit config/agent_config.py to use all-Llama-3 fallback
# (see "Experiment 1" section below)
```

---

## Troubleshooting

### Ollama Not Running

**Error:** "Connection refused"

**Solution:**

1. Open Start Menu, search "Services"
2. Look for "Ollama" service
3. If not running, right-click and select "Start"

**Or from Command Prompt:**
```cmd
# Restart Ollama service
net stop Ollama
net start Ollama
```

### Models Not Found

**Error:** "model not found"

**Solution:**
```cmd
# Pull models again
ollama pull llama3
ollama pull qwen2.5

# Verify
ollama list
```

### Out of Memory

**Error:** "CUDA out of memory" or "OOM"

Unlikely with 34GB, but if it happens:

```cmd
# 1. Check GPU memory
nvidia-smi
```

Should stay under 34GB. If above 34GB:

```cmd
# 2. Close other GPU apps (Chrome, Discord, etc.)

# 3. Reduce Qwen max_tokens in config\agent_config.py:
notepad config\agent_config.py
```

Change:
```python
JUDGE_PROVIDER = Qwen25Provider()
# To:
JUDGE_PROVIDER = Qwen25Provider(max_tokens=300)
```

Or use all Llama-3 (safest):
```python
JUDGE_PROVIDER = LlamaProvider(model_name="llama3", max_tokens=400)
```

Then re-run: `python run_eval.py`

### Slow Responses (>15 sec per threat)

**Check GPU usage:**
```cmd
nvidia-smi
```

**Expected timing:**
- Validator: 2–3 sec
- Agents (parallel): max(3–5 sec) = 3–5 sec
- Judge: 3–5 sec
- Total: 5–10 sec

**If slower:** Check thermal throttling
```cmd
nvidia-smi -q -d TEMPERATURE
```

If temperature > 80°C, let GPU cool down.

### Model Gives Nonsensical Output

**Test Ollama directly:**
```cmd
ollama run llama3 "What is a phishing attack?"
ollama run qwen2.5 "Summarize a threat"
```

If Ollama works but CyberCouncil doesn't:

```cmd
# Check config
type config\agent_config.py
# Should use LlamaProvider and Qwen25Provider

# Check for errors
python main.py 2>&1 | more
```

---

## Performance Expectations

### Your Hardware (RTX 5060 Ti, 34GB GPU-Accessible)

#### With Specialized Security Models (RECOMMENDED)

| Operation | Time | Notes |
|-----------|------|-------|
| Pull all 6 models | 60 min | One-time, includes all specialized |
| Single threat | 5–10 sec | Parallel agents (specialized) |
| 50-threat eval | 5–10 min | ~50 × 5–10 sec |
| Baselines | 5–10 min | 3 configs × 50 threats |
| **Total (first run)** | ~120 min | Includes 60 min model pulls |
| **Total (re-run)** | ~15 min | Skip model pulls |

#### With Generic Llama-3 (Fallback)

| Operation | Time | Notes |
|-----------|------|-------|
| Pull Llama-3 + Qwen | 15 min | One-time, generic models |
| Single threat | 5–10 sec | Parallel agents (generic) |
| 50-threat eval | 5–10 min | ~50 × 5–10 sec |
| Baselines | 5–10 min | 3 configs × 50 threats |
| **Total (first run)** | ~45 min | Includes 15 min model pulls |
| **Total (re-run)** | ~15 min | Skip model pulls |

### GPU Memory Usage (Specialized Models, Parallel)

| Phase | Memory | Safe? |
|-------|--------|-------|
| Validator (Foundation-Sec 8B) | 4GB | ✓ |
| Agent A (Llama-Sec 8B) | 4GB | ✓ |
| Agent B (Gemma-2 27B) | 13GB | ✓ |
| Agent C (DeepSeek-R1 33B) | 16GB | ✓ |
| Agent D (Mistral-Nemo 12B) | 6GB | ✓ |
| **Agents Total (parallel)** | ~43GB | May use system RAM |
| Judge (Qwen 72B, sequential) | 37GB | Runs after agents unload |
| **Peak** | ~43GB | Under 34GB dedicated, uses shared |

**Note:** Ollama is smart about memory. It can:
- Spill larger models to system RAM (18GB available)
- Use hybrid VRAM+RAM execution
- Unload models as needed

If you get OOM, fallback options:
1. Use sequential execution (slower, safe)
2. Switch to all-Llama-3 (faster, generic)

### GPU Memory Usage (Generic Llama-3, Parallel)

| Phase | Memory | Safe? |
|-------|--------|-------|
| Validator (Llama-3 8B) | 4GB | ✓ |
| Agent A (Llama-3 8B) | 4GB | ✓ |
| Agent B (Llama-3 8B) | 4GB | ✓ |
| Agent C (Llama-3 8B) | 4GB | ✓ |
| Agent D (Llama-3 8B) | 4GB | ✓ |
| **Agents Total (parallel)** | ~20GB | Easy fit |
| Judge (Qwen 72B, sequential) | 37GB | Runs after agents unload |
| **Peak** | ~37GB | Comfortably under 34GB dedicated |

---

## When You Have Results

### Check Accuracy

```cmd
python -c "import json; r=json.load(open('results/eval_results.json')); print(f'Accuracy: {r[\"accuracy\"]:.2%}\nPrecision: {r[\"precision\"]:.2%}\nRecall: {r[\"recall\"]:.2%}\nF1: {r[\"f1\"]:.2%}')"
```

### Export for Paper

```cmd
# Copy results to paper directory
copy results\council_confusion.png C:\Users\ashwinsi\paper\figures\
copy results\council_metrics_bar.png C:\Users\ashwinsi\paper\figures\
copy results\comparison_chart.png C:\Users\ashwinsi\paper\figures\

# Or view summary
type results\eval_results.json
```

---

## Next Steps

### Experiment 1: Swap Judge Model

```cmd
# Edit config
notepad config\agent_config.py
```

Change from:
```python
JUDGE_PROVIDER = Qwen25Provider()
```

To:
```python
JUDGE_PROVIDER = LlamaProvider(model_name="llama3", max_tokens=400)
```

Then re-run:
```cmd
python run_eval.py
```

### Experiment 2: Add Security-Specialized Models (Optional)

```cmd
# Pull security models
ollama pull foundation-sec-8b-reasoning
ollama pull llama-3.1-foundationai-securityllm-8b
ollama pull gemma-2-27b-security
ollama pull deepseek-r1
ollama pull mistral-nemo

# Edit config
notepad config\agent_config.py
```

Uncomment the "Alternative: Security-specialized models" section.

Then re-run:
```cmd
python run_eval.py
```

### Experiment 3: Sequential Execution (for comparison)

```cmd
# Edit orchestrator
notepad council\orchestrator.py
```

Change:
```python
round1_outputs = await self._run_agents_parallel(clean_threat, loop)
```

To:
```python
round1_outputs = await self._run_agents_sequential(clean_threat, loop)
```

Then compare timing & memory with parallel version.

---

## Support

If stuck:

1. **Check Ollama:** Running? `tasklist | findstr ollama`
2. **Check GPU:** `nvidia-smi` shows RTX 5060 Ti?
3. **Check models:** `ollama list` shows llama3 + qwen2.5?
4. **Check Python:** `python main.py` produces output?
5. **Check venv:** Command prompt shows `(venv)` prefix?
6. **Check logs:**
   ```cmd
   python main.py > output.txt 2>&1
   type output.txt
   ```

For detailed troubleshooting, see `MODEL.md` section "Troubleshooting".

---

## Paper Reproducibility

To reproduce all results from the paper:

```cmd
# Clean run from scratch
rmdir /s /q results
del data\threats.json

# Run full pipeline
python scripts/build_dataset.py
python run_eval.py
python run_baselines.py

# Check results
dir results\
type results\eval_results.json
```

All models are open-source via Ollama. No API keys needed.

---

## Common Windows Issues

### PowerShell Execution Policy Error

**Error:** "Cannot be loaded because running scripts is disabled"

**Solution (PowerShell only):**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Or use Command Prompt (`cmd.exe`) instead of PowerShell.

### Python Not Found

**Error:** "python is not recognized"

**Solution:**

1. Check Python is installed:
   ```cmd
   py --version
   ```

2. If not installed, download from python.org

3. During installation, **CHECK** "Add Python to PATH"

4. Restart Command Prompt

5. Try again:
   ```cmd
   python --version
   ```

### venv Activation Not Working

**Error:** "venv\Scripts\activate is not recognized"

**Solution:**

Try PowerShell instead:
```powershell
.\venv\Scripts\Activate.ps1
```

Or use full path:
```cmd
C:\Users\ashwinsi\paper\cyberPaper\venv\Scripts\activate.bat
```

### Curl Not Found (Older Windows)

**Error:** "curl is not recognized"

**Solution:**

Use PowerShell instead:
```powershell
Invoke-WebRequest -Uri http://localhost:11434/api/tags
```

Or use `python` to test:
```cmd
python -c "import requests; print(requests.get('http://localhost:11434/api/tags').json())"
```

---

## Tips for Windows Users

### Pin to Quick Access
- Right-click project folder → "Pin to Quick Access"
- Faster navigation

### Open Command Prompt Here
- Shift + Right-click in folder → "Open PowerShell window here" or "Open command window here"

### Use Windows Terminal (Recommended)
- Modern terminal from Microsoft Store
- Better than old Command Prompt
- Supports multiple tabs

### Keyboard Shortcuts
- `Ctrl+C` — Stop running process
- `Ctrl+L` — Clear screen
- `↑` / `↓` — Previous/next command in history
- `Tab` — Auto-complete file names

---

## Final Checklist

Before running evaluation:

- [ ] Ollama installed and running
- [ ] Python 3.10+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` copied (default settings OK)
- [ ] Llama-3 pulled (`ollama pull llama3`)
- [ ] Qwen2.5 pulled (`ollama pull qwen2.5`)
- [ ] Single threat test passed (`python main.py`)
- [ ] Local tests passed (`python tests/test_local.py`)

If all checked, you're ready for full evaluation!

```cmd
python run_eval.py
```

---

## Experiments & Configurations

### Current Default Setup

**Specialized Security Models + Parallel Execution** (BEST)
- Agent 0: Foundation-Sec-8B-Reasoning
- Agent A: Llama-3.1-FoundationAI-SecurityLLM-8B  
- Agent B: Gemma-2-27B-Security
- Agent C: DeepSeek-R1-Reasoning
- Agent D: Mistral-Nemo-Instruct
- Judge: Qwen2.5-72B
- **Performance:** 5–10 sec/threat, ~43GB peak memory
- **Accuracy:** Best (specialized threat models)

---

### Experiment 1: Switch to Generic Llama-3 (If OOM)

If you get out-of-memory errors:

```cmd
notepad config\agent_config.py
```

**Find lines 22–32** (starting with `from providers.foundation_sec...`) and **comment them out**.

**Find lines 35–50** (comment section "Alternative: All Generic Llama-3") and **uncomment them**.

Save and re-run:
```cmd
python run_eval.py
```

**Comparison:**
| Config | Accuracy | Memory | Speed |
|--------|----------|--------|-------|
| Specialized | Best | ~43GB | 5–10s |
| Llama-3 | Good | ~20GB | 5–10s |

---

### Experiment 2: Sequential Execution (Safe, Slower)

If parallel still causes OOM, use sequential mode:

```cmd
notepad council\orchestrator.py
```

**Find line ~113** (contains `round1_outputs = await self._run_agents_parallel`).

**Replace `_run_agents_parallel` with `_run_agents_sequential`** on this line.

**Find line ~127** (contains `round2_outputs = await self._run_agents_parallel`).

**Replace `_run_agents_parallel` with `_run_agents_sequential`** on this line too.

Save and re-run:
```cmd
python run_eval.py
```

**Comparison:**
| Mode | Memory | Speed |
|------|--------|-------|
| Parallel | ~43GB | 5–10s |
| Sequential | ~37GB | 20–30s |

---

### Experiment 3: Compare 3 Configurations (Paper Ablation)

Run evaluation with each setup for paper comparison:

```cmd
REM Config 1: Specialized + Parallel (current default)
python run_eval.py
copy results\eval_results.json results\config1_specialized_parallel.json

REM Config 2: Llama-3 + Parallel (generic baseline)
REM (edit config to use Llama-3)
notepad config\agent_config.py
python run_eval.py
copy results\eval_results.json results\config2_llama3_parallel.json

REM Config 3: Specialized + Sequential (safe)
REM (edit orchestrator to use sequential)
notepad council\orchestrator.py
python run_eval.py
copy results\eval_results.json results\config3_specialized_sequential.json
```

**Compare results:**
```cmd
python -c "import json, glob; [print(f\"{f.split(chr(92))[-1]:40} Acc: {json.load(open(f))[chr(34)accuracy chr(34)]:.1%}\") for f in glob.glob('results/config*.json')]"
```

---

### Experiment 4: Paper Summary Table

For IEEE paper, create comparison table:

| Config | Accuracy | Precision | Recall | F1 | Memory | Time |
|--------|----------|-----------|--------|-----|--------|------|
| Specialized Council (Parallel) | X% | X% | X% | X% | 43GB | 5–10s |
| Generic Council (Parallel) | X% | X% | X% | X% | 20GB | 5–10s |
| Specialized Council (Sequential) | X% | X% | X% | X% | 37GB | 20–30s |

Run each config, save results, and fill in actual percentages.

Good luck! 🚀
