from providers.claude_provider import ClaudeProvider
from providers.openai_provider import OpenAIProvider
from providers.llama_provider import LlamaProvider

# ─────────────────────────────────────────────────────────────────
#  AGENT PROVIDER CONFIGURATION
#
#  This is the ONLY file you edit to swap LLM providers per agent.
#
#  Available options:
#    ClaudeProvider()                          Claude Sonnet (default)
#    ClaudeProvider("claude-opus-4-5")         Claude Opus
#    OpenAIProvider()                          GPT-4o (default)
#    OpenAIProvider("gpt-4-turbo")             GPT-4 Turbo
#    LlamaProvider()                           Llama 3 (local, default endpoint)
#    LlamaProvider(model_name="llama-3", api_base="http://localhost:8000/v1")
#
#  Change one line here. Zero other code changes required.
# ─────────────────────────────────────────────────────────────────

# AGENT_A_PROVIDER = OpenAIProvider("gpt-4o")       # Threat Classifier
# AGENT_B_PROVIDER = OpenAIProvider()       # Vulnerability Analyst
# AGENT_C_PROVIDER = OpenAIProvider()       # Impact Assessor
# JUDGE_PROVIDER   = OpenAIProvider()       # Judge / Synthesizer

# To use a local Llama 3 endpoint for all agents, set:
AGENT_A_PROVIDER = LlamaProvider()
AGENT_B_PROVIDER = LlamaProvider()
AGENT_C_PROVIDER = LlamaProvider()
JUDGE_PROVIDER   = LlamaProvider()
AGENT_VALIDATOR_PROVIDER = LlamaProvider()   # Agent 0 — Validator
AGENT_D_PROVIDER         = LlamaProvider()   # Agent D — Remediation Engineer
#
# You can override the endpoint and model via environment variables:
#   LLAMA_API_BASE (default: http://localhost:8000/v1)
#   LLAMA_MODEL    (default: llama-3)
# Or pass them as arguments to LlamaProvider(...)

# ── Example: GPT for all agents, Claude only as judge ─────────────
# AGENT_A_PROVIDER = OpenAIProvider()
# AGENT_B_PROVIDER = OpenAIProvider()
# AGENT_C_PROVIDER = OpenAIProvider()
# JUDGE_PROVIDER   = ClaudeProvider()

# ── Example: Mixed models per agent ───────────────────────────────
# AGENT_A_PROVIDER = ClaudeProvider("claude-opus-4-5")   # Best reasoning for classification
# AGENT_B_PROVIDER = OpenAIProvider("gpt-4o")            # GPT-4o for CVE mapping
# AGENT_C_PROVIDER = OpenAIProvider("gpt-4-turbo")       # GPT Turbo for impact scoring
# JUDGE_PROVIDER   = ClaudeProvider()                    # Claude Sonnet as judge
