# ─────────────────────────────────────────────────────────────────
#  AGENT PROVIDER CONFIGURATION
#
#  OPTIMIZED FOR 34GB GPU-ACCESSIBLE MEMORY (RTX 5060 Ti):
#  - 16GB dedicated + 18GB shared from system RAM
#  - Using models available on Ollama public registry
#  - Agents (A,B,C,D): Llama-3 8B (parallel execution)
#  - Judge (CISO):     Qwen2.5-72B (runs after agents finish)
#  - Parallel execution in orchestrator.py — 5–10 sec per threat
#
#  NOTE: Specialized security models (Foundation-Sec, FoundationAI-SecurityLLM, etc.)
#  are NOT available on Ollama's public registry. Using generic Llama-3 instead.
#
#  Edit this file to swap providers per agent.
#  Zero code changes required — just update the provider assignment.
# ─────────────────────────────────────────────────────────────────

from providers.llama_provider import LlamaProvider
from providers.deepseek_r1_provider import DeepSeekR1Provider
from providers.mistral_nemo_provider import MistralNemoProvider
from providers.qwen2_5_provider import Qwen25Provider

# ── DEFAULT (34GB GPU, Parallel, Mixed Available Models) ─────────
#
# Agent 0 (Validator):    Llama-3 8B      — reliable general-purpose validation
# Agent A (Classifier):   DeepSeek-R1     — strong reasoning for threat classification
# Agent B (Vuln Analyst): Mistral-Nemo    — technical analysis, CVE/ATT&CK mapping
# Agent C (Impact):       Llama-3 8B      — impact scoring + immediate actions
# Agent D (Remediation):  Llama-3 8B      — remediation planning
# Judge (CISO):           Qwen2.5-72B     — synthesis & arbitration (runs after agents)
#
# Execution: Parallel (all 4 agents run concurrently)
# Peak memory: ~30–34GB total
#   - Agents parallel: mixed 7–8B models ≈ 30GB with KV cache
#   - Judge: ~4.7GB quantized (runs after agents unload)
# Performance: ~5–10 sec per threat (parallel execution)
# Models installed: llama3, deepseek-r1, mistral-nemo, qwen2.5

AGENT_VALIDATOR_PROVIDER = LlamaProvider(model_name="llama3", max_tokens=400)
AGENT_A_PROVIDER         = DeepSeekR1Provider()                                    # Threat Classifier  — reasoning
AGENT_B_PROVIDER         = MistralNemoProvider()                                   # Vulnerability Analyst — technical
AGENT_C_PROVIDER         = LlamaProvider(model_name="llama3", max_tokens=400)      # Impact Assessor
AGENT_D_PROVIDER         = LlamaProvider(model_name="llama3", max_tokens=400)      # Remediation Engineer
JUDGE_PROVIDER           = Qwen25Provider()                                        # Judge / CISO runs after agents unload

# ── Alternative: All Generic Llama-3 (Fallback) ────────────────────
# Use if DeepSeek-R1 or Mistral-Nemo cause OOM or errors
# Performance: same speed, slightly lower accuracy
#
# AGENT_VALIDATOR_PROVIDER = LlamaProvider(model_name="llama3", max_tokens=400)
# AGENT_A_PROVIDER         = LlamaProvider(model_name="llama3", max_tokens=400)
# AGENT_B_PROVIDER         = LlamaProvider(model_name="llama3", max_tokens=400)
# AGENT_C_PROVIDER         = LlamaProvider(model_name="llama3", max_tokens=400)
# AGENT_D_PROVIDER         = LlamaProvider(model_name="llama3", max_tokens=400)
# JUDGE_PROVIDER           = Qwen25Provider()

# ── Alternative: Sequential Execution (If Parallel Causes OOM) ───────
# REQUIRES: Edit orchestrator.py to use _run_agents_sequential()
# Use if parallel execution exceeds memory (unlikely with 34GB)
# Performance: ~20–30 sec per threat (slower but memory-safe)
# Agents run one-at-a-time, each unloads before next starts
#
# AGENT_VALIDATOR_PROVIDER = LlamaProvider(model_name="llama3", max_tokens=400)
# AGENT_A_PROVIDER         = DeepSeekR1Provider()
# AGENT_B_PROVIDER         = MistralNemoProvider()
# AGENT_C_PROVIDER         = LlamaProvider(model_name="neural-chat", max_tokens=400)
# AGENT_D_PROVIDER         = LlamaProvider(model_name="openchat", max_tokens=400)
# JUDGE_PROVIDER           = Qwen25Provider()
# Peak memory: ~7GB max per step (one model at a time)

# ── Alternative: Mix with Claude/OpenAI (cloud-based) ────────────────
# from providers.claude_provider import ClaudeProvider
# from providers.openai_provider import OpenAIProvider
# AGENT_A_PROVIDER = ClaudeProvider("claude-opus-4-6")
# JUDGE_PROVIDER   = ClaudeProvider("claude-sonnet-4-6")

# ── Environment Override ───────────────────────────────────────────
# Set OLLAMA_API_BASE to override default (http://localhost:11434):
#   export OLLAMA_API_BASE=http://192.168.1.100:11434
