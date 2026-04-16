# CyberCouncil — Model Setup & Ollama Configuration

This guide covers complete setup for running **CyberCouncil with security-specialized models via Ollama**.

---

## Architecture

All agents use local models running via **Ollama** (no API costs, full privacy):

| Agent | Model | Size | Role |
|-------|-------|------|------|
| **Agent 0 (Validator)** | Foundation-Sec-8B-Reasoning | 8B | Input validation & enrichment |
| **Agent A (Classifier)** | Llama-3.1-FoundationAI-SecurityLLM-8B | 8B | Threat classification |
| **Agent B (Vuln Analyst)** | Gemma-2-27B-Security | 27B | CVE & MITRE ATT&CK mapping |
| **Agent C (Impact)** | DeepSeek-R1-Reasoning | 33B | Risk quantification & impact scoring |
| **Agent D (Remediation)** | Mistral-Nemo-Instruct | 12B | Remediation planning & containment |
| **Judge (CISO)** | Qwen2.5-72B-Instruct | 72B | Final synthesis & orchestration |

---

## Prerequisites

### Hardware Requirements

- **GPU:** NVIDIA GPU with 24GB+ VRAM (for running 27B–72B models)
  - RTX 4090 / A100 / H100 recommended
- **CPU Fallback:** 64GB+ RAM (slower, but works)
- **Disk:** 300GB+ for all models

### Software Requirements

- **Ollama:** https://ollama.ai (download & install for your OS)
- **Python:** 3.10+
- **Git** (for cloning repo)

---

## Step-by-Step Setup

### 0. Install Ollama

**Mac:**
```bash
brew install ollama
```

**Linux:**
```bash
curl https://ollama.ai/install.sh | sh
```

**Windows:**
Download from https://ollama.ai/download

Verify installation:
```bash
ollama --version
```

---

### 1. Clone & Setup Project

```bash
cd /path/to/cyberPaper
python3 -m venv venv
source venv/bin/activate  # (or venv\Scripts\activate on Windows)
pip install -r requirements.txt
cp .env.example .env
```

---

### 2. Pull Models from Ollama Registry

Start Ollama daemon in a separate terminal:

**Mac/Linux:**
```bash
ollama serve
```

**Windows:**
Ollama runs as a service automatically.

---

### Pull all models (in another terminal, with venv activated):

```bash
# Foundation-Sec models (8B each)
ollama pull foundation-sec-8b-instruct
ollama pull foundation-sec-8b-reasoning

# Llama Security model (8B)
ollama pull llama-3.1-foundationai-securityllm-8b

# Gemma Security (27B)
ollama pull gemma-2-27b-security

# DeepSeek reasoning (33B)
ollama pull deepseek-r1

# Mistral Nemo (12B)
ollama pull mistral-nemo

# Qwen (72B)
ollama pull qwen2.5
```

**Note:** First pull takes 5–15 minutes per model (downloads from Ollama registry).

---

### 3. Verify Ollama Models

```bash
ollama list
```

Should show all 6 models with their sizes.

---

### 4. Configure Environment

Edit `.env`:

```bash
# Ollama endpoint (default: localhost:11434)
OLLAMA_API_BASE=http://localhost:11434

# Optional: for remote Ollama server
# OLLAMA_API_BASE=http://192.168.1.100:11434
```

---

### 5. Verify Setup

**Check Ollama is running:**
```bash
curl http://localhost:11434/api/tags
```

Should return JSON list of available models.

**Test with single threat:**
```bash
python3 main.py
```

Edit `threat` variable in `main.py` for testing.

---

## Testing

### Local Test (4 scenarios)

```bash
python3 tests/test_local.py
```

Expected output: All 4 tests pass, agents complete within 5–10 sec each.

### Full Evaluation

```bash
# Generate dataset (50 threats)
python3 scripts/build_dataset.py

# Run evaluation
python3 run_eval.py
```

Outputs to `results/`:
- `council_metrics.csv` — accuracy, precision, recall, F1
- `council_confusion.png` — grayscale confusion matrix
- `council_metrics_bar.png` — grayscale metric bars

### Baseline Comparisons

```bash
python3 run_baselines.py
```

Compares:
1. Single Agent A (no council)
2. Majority vote (no judge)
3. Full council + judge

Output: `results/comparison_chart.png`

---

## Performance Tuning

### GPU Memory Management

If you get out-of-memory errors:

1. **Reduce max_tokens** in provider code:
   ```python
   super().__init__(
       model_name="qwen2.5",
       api_base=api_base,
       max_tokens=512  # Reduce from 600
   )
   ```

2. **Run models sequentially** (edit `council/orchestrator.py`):
   - Replace `asyncio.gather()` with sequential calls
   - Slower but uses less GPU memory

3. **Use smaller fallback models:**
   ```python
   # In config/agent_config.py
   from providers.llama_provider import LlamaProvider
   AGENT_C_PROVIDER = LlamaProvider(model_name="llama3")  # Use 8B instead of 33B
   ```

### CPU-Only Mode

If no GPU:

```bash
# In .env
OLLAMA_API_BASE=http://localhost:11434
# Ollama will auto-detect and use CPU

# Expect ~10–30 sec per agent (vs. 2–5 sec on GPU)
```

---

## Troubleshooting

### "Connection refused" error

Ollama daemon not running. Start it:

**Mac/Linux:**
```bash
ollama serve
```

**Windows:** Ensure Ollama service is running (check taskbar).

### "Model not found" error

Model not pulled yet. Pull it:

```bash
ollama pull qwen2.5
```

### Out of Memory (OOM)

1. Reduce batch size (sequential agents)
2. Use smaller models (Llama-3 8B instead of Qwen 72B)
3. Increase available GPU memory (close other apps)

### Slow responses

1. Check GPU usage: `nvidia-smi`
2. If CPU-bound, ensure GPU drivers installed
3. Switch to smaller models for testing

### Model gives nonsensical output

1. Verify model pulled correctly: `ollama list`
2. Test with direct Ollama call:
   ```bash
   ollama run qwen2.5 "Classify this threat: User receives phishing email"
   ```
3. If Ollama works but CyberCouncil doesn't, check `config/agent_config.py` imports

---

## Model Details & Paper Reference

### Foundation-Sec Series (8B)

**Instruct:** 98% phishing recall, native threat pattern recognition  
**Reasoning:** Multi-step reasoning, validates against MITRE evidence, 9% fewer false positives

**Best for:** Input validation, threat classification

**Paper claim:** Specialized security models outperform general-purpose LLMs for threat detection

---

### Llama-3.1-FoundationAI-SecurityLLM-8B

Deep threat intelligence analysis, matches 70B performance

**Best for:** Agent A (Classifier) — detailed threat analysis

**Paper claim:** 8B security-specialized model matches 70B general model on threat classification

---

### Gemma-2-27B-Security

Code/log vulnerability scanning, lightweight exploit analysis

**Best for:** Agent B (Vuln Analyst) — CVE mapping & MITRE ATT&CK

**Paper claim:** Moderate-sized security model sufficient for vulnerability analysis

---

### DeepSeek-R1-Reasoning (33B)

Risk quantification & business impact scoring

**Best for:** Agent C (Impact Assessor) — severity scoring & impact analysis

**Paper claim:** Advanced reasoning model improves impact assessment accuracy

---

### Mistral-Nemo-Instruct (12B)

Actionable SecOps workflows & containment steps

**Best for:** Agent D (Remediation Engineer) — practical remediation planning

**Paper claim:** Instruction-tuned model produces actionable remediation guidance

---

### Qwen2.5-72B-Instruct (72B)

Structured reporting, contradiction resolution, final synthesis

**Best for:** Judge Agent — synthesizes all agent outputs, resolves conflicts

**Paper claim:** Larger model with strong reasoning essential for Judge role

---

## Advanced Configuration

### Use Mixed Models

Example: Use Llama for quick tests, Qwen only for Judge:

```python
# In config/agent_config.py
from providers.llama_provider import LlamaProvider
from providers.qwen2_5_provider import Qwen25Provider

AGENT_VALIDATOR_PROVIDER = LlamaProvider(model_name="llama3")
AGENT_A_PROVIDER         = LlamaProvider(model_name="llama3")
AGENT_B_PROVIDER         = LlamaProvider(model_name="llama3")
AGENT_C_PROVIDER         = LlamaProvider(model_name="llama3")
AGENT_D_PROVIDER         = LlamaProvider(model_name="llama3")
JUDGE_PROVIDER           = Qwen25Provider()  # Use best model for Judge
```

### Remote Ollama Server

Run Ollama on separate machine:

**Server machine:**
```bash
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

**Client (.env):**
```bash
OLLAMA_API_BASE=http://192.168.1.50:11434
```

---

## Complete Workflow

```bash
# 1. Start Ollama
ollama serve

# 2. In new terminal, activate env & pull models
source venv/bin/activate
for model in foundation-sec-8b-instruct foundation-sec-8b-reasoning \
             llama-3.1-foundationai-securityllm-8b gemma-2-27b-security \
             deepseek-r1 mistral-nemo qwen2.5; do
  ollama pull $model
done

# 3. Configure
cp .env.example .env

# 4. Test
python3 tests/test_local.py

# 5. Generate dataset
python3 scripts/build_dataset.py

# 6. Run evaluation
python3 run_eval.py

# 7. Run baselines
python3 run_baselines.py

# 8. Check results
ls results/
```

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OLLAMA_API_BASE` | `http://localhost:11434` | Ollama endpoint |
| `OLLAMA_NUM_GPU` | Auto-detect | # GPU layers (default: all) |
| `OLLAMA_NUM_THREAD` | # CPU cores | # CPU threads to use |

---

## For the Paper

### Reproducibility Note

All models are open-source, available via Ollama registry. Full reproducibility:

1. Install Ollama
2. Pull models (see Step 2 above)
3. Run `python3 run_eval.py`

### Model Combination Rationale

- **Agent 0 (Validator):** Reasoning variant for input validation accuracy
- **Agent A (Classifier):** FoundationAI security model (8B = 70B performance)
- **Agent B (Vuln Analyst):** Gemma-2-27B (CVE/MITRE expertise)
- **Agent C (Impact):** DeepSeek reasoning (quantification accuracy)
- **Agent D (Remediation):** Mistral Nemo instruction-tuned (actionable steps)
- **Judge:** Qwen 72B (synthesis, contradiction resolution)

### Cost Analysis

**No API costs** — all models run locally. Compute cost:
- GPU: ~$0 (amortized hardware cost)
- Electricity: ~$10 per 50-threat evaluation (GPU power)

vs. GPT-4 API: ~$500 per 50-threat evaluation

---

## Support

If issues:

1. Check `ollama list` — all models pulled?
2. Test direct Ollama: `ollama run qwen2.5 "hello"`
3. Check `.env` — correct `OLLAMA_API_BASE`?
4. Check logs: `python3 main.py` — what error message?
