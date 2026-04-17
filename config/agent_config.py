# ─────────────────────────────────────────────────────────────────
#  AGENT PROVIDER CONFIGURATION
#
#  OPTIMIZED FOR 16GB GPU:
#  - Agents (A,B,C,D): Llama-3 8B (fast, low memory)
#  - Judge (CISO):     Qwen2.5-72B (runs after agents unload)
#  - Sequential execution in orchestrator.py ensures safe GPU memory
#
#  Edit this file to swap providers per agent.
#  Zero code changes required — just update the provider assignment.
# ─────────────────────────────────────────────────────────────────

from providers.llama_provider import LlamaProvider
from providers.qwen2_5_provider import Qwen25Provider

# ── OPTIMIZED FOR 16GB GPU (Default Configuration) ────────────────
#
# Agent 0 (Validator):    Llama-3 8B
# Agent A (Classifier):   Llama-3 8B (generic but reliable)
# Agent B (Vuln Analyst): Llama-3 8B
# Agent C (Impact):       Llama-3 8B
# Agent D (Remediation):  Llama-3 8B
# Judge (CISO):           Qwen2.5-72B (runs sequentially after agents)
#
# Why: 8B agents fit in 16GB GPU. Judge runs alone after agents unload.
#      Sequential execution in orchestrator.py prevents OOM.

AGENT_VALIDATOR_PROVIDER = LlamaProvider(model_name="llama3", max_tokens=400)
AGENT_A_PROVIDER         = LlamaProvider(model_name="llama3", max_tokens=400)
AGENT_B_PROVIDER         = LlamaProvider(model_name="llama3", max_tokens=400)
AGENT_C_PROVIDER         = LlamaProvider(model_name="llama3", max_tokens=400)
AGENT_D_PROVIDER         = LlamaProvider(model_name="llama3", max_tokens=400)
JUDGE_PROVIDER           = Qwen25Provider()  # 72B runs after agents unload

# ── Alternative: Security-specialized models (24GB+ GPU required) ───
# REQUIRES: Parallel execution in orchestrator.py (switch to _run_agents_parallel)
# REQUIRES: GPU with 24GB+ VRAM
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

# ── Alternative: All Llama-3 (fastest, lowest memory) ────────────────
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
