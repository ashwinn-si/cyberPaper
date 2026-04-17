# ─────────────────────────────────────────────────────────────────
#  AGENT PROVIDER CONFIGURATION
#
#  OPTIMIZED FOR 34GB GPU-ACCESSIBLE MEMORY (RTX 5060 Ti):
#  - 16GB dedicated + 18GB shared from system RAM
#  - Agents (A,B,C,D): Llama-3 8B (parallel execution)
#  - Judge (CISO):     Qwen2.5-72B (runs after agents finish)
#  - Parallel execution in orchestrator.py — 5–10 sec per threat
#
#  Edit this file to swap providers per agent.
#  Zero code changes required — just update the provider assignment.
# ─────────────────────────────────────────────────────────────────

from providers.llama_provider import LlamaProvider
from providers.qwen2_5_provider import Qwen25Provider

# ── DEFAULT (34GB GPU, Parallel Execution) ──────────────────────
#
# Agent 0 (Validator):    Llama-3 8B
# Agent A (Classifier):   Llama-3 8B (generic but reliable)
# Agent B (Vuln Analyst): Llama-3 8B
# Agent C (Impact):       Llama-3 8B
# Agent D (Remediation):  Llama-3 8B
# Judge (CISO):           Qwen2.5-72B
#
# Execution: Parallel (all 4 agents run concurrently)
# Peak memory: ~32GB (4×8B agents + 72B judge)
# Performance: ~5–10 sec per threat (3–4x faster than sequential)

AGENT_VALIDATOR_PROVIDER = LlamaProvider(model_name="llama3", max_tokens=400)
AGENT_A_PROVIDER         = LlamaProvider(model_name="llama3", max_tokens=400)
AGENT_B_PROVIDER         = LlamaProvider(model_name="llama3", max_tokens=400)
AGENT_C_PROVIDER         = LlamaProvider(model_name="llama3", max_tokens=400)
AGENT_D_PROVIDER         = LlamaProvider(model_name="llama3", max_tokens=400)
JUDGE_PROVIDER           = Qwen25Provider()  # 72B runs after agents unload

# ── Alternative: Security-specialized models (34GB+ GPU, parallel) ───
# REQUIRES: Parallel execution (already default in orchestrator.py)
# REQUIRES: Pull models: ollama pull gemma-2-27b-security deepseek-r1 mistral-nemo
# from providers.foundation_sec_reasoning_provider import FoundationSecReasoningProvider
# from providers.llama_foundation_ai_provider import LlamaFoundationAIProvider
# from providers.gemma2_security_provider import Gemma2SecurityProvider
# from providers.deepseek_r1_provider import DeepSeekR1Provider
# from providers.mistral_nemo_provider import MistralNemoProvider
#
# AGENT_VALIDATOR_PROVIDER = FoundationSecReasoningProvider()
# AGENT_A_PROVIDER         = LlamaFoundationAIProvider()      # Threat Classifier
# AGENT_B_PROVIDER         = Gemma2SecurityProvider()         # Vulnerability Analyst
# AGENT_C_PROVIDER         = DeepSeekR1Provider()             # Impact Assessor
# AGENT_D_PROVIDER         = MistralNemoProvider()            # Remediation Engineer
# JUDGE_PROVIDER           = Qwen25Provider()                 # Judge / CISO
# Peak memory: ~50GB (8B + 8B + 27B + 33B + 12B agents parallel + 72B judge sequential)
# Note: Requires 40GB+ free GPU memory during agent parallel phase

# ── Alternative: Sequential execution (for ≤16GB GPU) ────────────────
# REQUIRES: Edit orchestrator.py to use _run_agents_sequential()
# Performance: ~20–30 sec per threat (slower but memory-safe)
# from providers.llama_provider import LlamaProvider
# AGENT_VALIDATOR_PROVIDER = LlamaProvider(model_name="llama3", max_tokens=400)
# AGENT_A_PROVIDER         = LlamaProvider(model_name="llama3", max_tokens=400)
# AGENT_B_PROVIDER         = LlamaProvider(model_name="llama3", max_tokens=400)
# AGENT_C_PROVIDER         = LlamaProvider(model_name="llama3", max_tokens=400)
# AGENT_D_PROVIDER         = LlamaProvider(model_name="llama3", max_tokens=400)
# JUDGE_PROVIDER           = LlamaProvider(model_name="llama3", max_tokens=400)

# ── Alternative: Mix with Claude/OpenAI (cloud-based) ────────────────
# from providers.claude_provider import ClaudeProvider
# from providers.openai_provider import OpenAIProvider
# AGENT_A_PROVIDER = ClaudeProvider("claude-opus-4-6")
# JUDGE_PROVIDER   = ClaudeProvider("claude-sonnet-4-6")

# ── Environment Override ───────────────────────────────────────────
# Set OLLAMA_API_BASE to override default (http://localhost:11434):
#   export OLLAMA_API_BASE=http://192.168.1.100:11434
