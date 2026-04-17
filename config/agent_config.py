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

# ── DEFAULT (34GB GPU, Parallel, Security-Specialized Models) ───
#
# Agent 0 (Validator):    Foundation-Sec-8B-Reasoning (specialized)
# Agent A (Classifier):   Llama-3.1-FoundationAI-SecurityLLM-8B (specialized)
# Agent B (Vuln Analyst): Gemma-2-27B-Security (specialized)
# Agent C (Impact):       DeepSeek-R1-Reasoning (specialized, strong reasoning)
# Agent D (Remediation):  Mistral-Nemo-Instruct (specialized, actionable)
# Judge (CISO):           Qwen2.5-72B (strong synthesis)
#
# Execution: Parallel (all 4 agents run concurrently)
# Peak memory: ~50GB total (agents + judge may overlap slightly with RAM)
#   - Agents parallel: ~8+8+27+33+12 = 88B model params (~40–45GB with KV cache)
#   - Judge: ~37GB (runs after agents unload, or parallel with spillover to RAM)
# Performance: ~5–10 sec per threat (parallel execution)
# Accuracy: BEST (specialized threat models for each agent role)
# Note: Monitor GPU memory with nvidia-smi. If OOM, either:
#   1. Use sequential execution (slower but safe)
#   2. Switch to all-Llama-3 fallback (faster, generic)

from providers.foundation_sec_reasoning_provider import FoundationSecReasoningProvider
from providers.llama_foundation_ai_provider import LlamaFoundationAIProvider
from providers.gemma2_security_provider import Gemma2SecurityProvider
from providers.deepseek_r1_provider import DeepSeekR1Provider
from providers.mistral_nemo_provider import MistralNemoProvider

AGENT_VALIDATOR_PROVIDER = FoundationSecReasoningProvider()
AGENT_A_PROVIDER         = LlamaFoundationAIProvider()      # Threat Classifier
AGENT_B_PROVIDER         = Gemma2SecurityProvider()         # Vulnerability Analyst
AGENT_C_PROVIDER         = DeepSeekR1Provider()             # Impact Assessor
AGENT_D_PROVIDER         = MistralNemoProvider()            # Remediation Engineer
JUDGE_PROVIDER           = Qwen25Provider()                 # Judge / CISO runs after agents unload

# ── Alternative: All Generic Llama-3 (Fallback) ────────────────────
# REQUIRES: Only Llama-3 model pulled
# Use if specialized models cause OOM
# Performance: ~5–10 sec per threat (parallel), but lower accuracy
# from providers.llama_provider import LlamaProvider
#
# AGENT_VALIDATOR_PROVIDER = LlamaProvider(model_name="llama3", max_tokens=400)
# AGENT_A_PROVIDER         = LlamaProvider(model_name="llama3", max_tokens=400)
# AGENT_B_PROVIDER         = LlamaProvider(model_name="llama3", max_tokens=400)
# AGENT_C_PROVIDER         = LlamaProvider(model_name="llama3", max_tokens=400)
# AGENT_D_PROVIDER         = LlamaProvider(model_name="llama3", max_tokens=400)
# JUDGE_PROVIDER           = Qwen25Provider()
# Peak memory: ~32GB (4×8B agents parallel + 72B judge)

# ── Alternative: Sequential Execution (If Parallel Causes OOM) ───────
# REQUIRES: Edit orchestrator.py to use _run_agents_sequential()
# Use if parallel + specialized models exceed memory
# Performance: ~20–30 sec per threat (slower but memory-safe)
# Agents run one-at-a-time, each unloads before next starts
# from providers.foundation_sec_reasoning_provider import FoundationSecReasoningProvider
# from providers.llama_foundation_ai_provider import LlamaFoundationAIProvider
# from providers.gemma2_security_provider import Gemma2SecurityProvider
# from providers.deepseek_r1_provider import DeepSeekR1Provider
# from providers.mistral_nemo_provider import MistralNemoProvider
#
# AGENT_VALIDATOR_PROVIDER = FoundationSecReasoningProvider()
# AGENT_A_PROVIDER         = LlamaFoundationAIProvider()
# AGENT_B_PROVIDER         = Gemma2SecurityProvider()
# AGENT_C_PROVIDER         = DeepSeekR1Provider()
# AGENT_D_PROVIDER         = MistralNemoProvider()
# JUDGE_PROVIDER           = Qwen25Provider()
# Peak memory: ~37GB max (largest model = Qwen 72B or DeepSeek 33B)

# ── Alternative: Mix with Claude/OpenAI (cloud-based) ────────────────
# from providers.claude_provider import ClaudeProvider
# from providers.openai_provider import OpenAIProvider
# AGENT_A_PROVIDER = ClaudeProvider("claude-opus-4-6")
# JUDGE_PROVIDER   = ClaudeProvider("claude-sonnet-4-6")

# ── Environment Override ───────────────────────────────────────────
# Set OLLAMA_API_BASE to override default (http://localhost:11434):
#   export OLLAMA_API_BASE=http://192.168.1.100:11434
