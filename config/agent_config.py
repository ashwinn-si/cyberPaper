# ─────────────────────────────────────────────────────────────────
#  AGENT PROVIDER CONFIGURATION
#
#  Security-specialized models via Ollama (local execution)
#  All models optimized for threat analysis, no API costs.
#
#  Edit this file to swap providers per agent.
#  Zero code changes required — just update the provider assignment.
# ─────────────────────────────────────────────────────────────────

from providers.foundation_sec_reasoning_provider import FoundationSecReasoningProvider
from providers.llama_foundation_ai_provider import LlamaFoundationAIProvider
from providers.gemma2_security_provider import Gemma2SecurityProvider
from providers.deepseek_r1_provider import DeepSeekR1Provider
from providers.mistral_nemo_provider import MistralNemoProvider
from providers.qwen2_5_provider import Qwen25Provider

# ── Default Configuration: Security-specialized models via Ollama ──
#
# Agent 0 (Validator):    Foundation-Sec-8B-Reasoning
# Agent A (Classifier):   Llama-3.1-FoundationAI-SecurityLLM-8B
# Agent B (Vuln Analyst): Gemma-2-27B-Security
# Agent C (Impact):       DeepSeek-R1-Reasoning
# Agent D (Remediation):  Mistral-Nemo-Instruct
# Judge (CISO):           Qwen2.5-72B-Instruct

AGENT_VALIDATOR_PROVIDER = FoundationSecReasoningProvider()
AGENT_A_PROVIDER         = LlamaFoundationAIProvider()      # Threat Classifier
AGENT_B_PROVIDER         = Gemma2SecurityProvider()         # Vulnerability Analyst
AGENT_C_PROVIDER         = DeepSeekR1Provider()             # Impact Assessor
AGENT_D_PROVIDER         = MistralNemoProvider()            # Remediation Engineer
JUDGE_PROVIDER           = Qwen25Provider()                 # Judge / CISO

# ── Alternative: Use local Llama fallback (if Ollama models unavailable) ────
# from providers.llama_provider import LlamaProvider
# AGENT_VALIDATOR_PROVIDER = LlamaProvider(model_name="llama3")
# AGENT_A_PROVIDER         = LlamaProvider(model_name="llama3")
# AGENT_B_PROVIDER         = LlamaProvider(model_name="llama3")
# AGENT_C_PROVIDER         = LlamaProvider(model_name="llama3")
# AGENT_D_PROVIDER         = LlamaProvider(model_name="llama3")
# JUDGE_PROVIDER           = LlamaProvider(model_name="llama3")

# ── Alternative: Mix with Claude/OpenAI (cloud-based) ────────────────
# from providers.claude_provider import ClaudeProvider
# from providers.openai_provider import OpenAIProvider
# AGENT_A_PROVIDER = ClaudeProvider("claude-opus-4-6")
# JUDGE_PROVIDER   = ClaudeProvider("claude-sonnet-4-6")

# ── Environment Override ───────────────────────────────────────────
# Set OLLAMA_API_BASE to override default (http://localhost:11434):
#   export OLLAMA_API_BASE=http://192.168.1.100:11434
