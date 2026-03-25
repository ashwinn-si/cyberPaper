---
description: 'Use when implementing or refactoring CyberCouncil Python code for providers, agents, council orchestration, and evaluation. Enforces provider abstraction, config-driven wiring, prompt-file usage, and reproducible metrics outputs. Keywords: cybercouncil, provider swap, judge agent, CVE, MITRE ATT&CK, baseline, ablation.'
name: 'CyberCouncil Python Architecture Rules'
applyTo: '**/*.py'
---

# CyberCouncil Python Rules

- Preserve layer boundaries: providers hold model API clients, agents hold role behavior, council handles orchestration, evaluation handles metrics.
- Never import vendor SDKs (Anthropic, OpenAI, Gemini, and similar) in agents or council files. Keep SDK imports only in provider files.
- Keep provider wiring in config/agent_config.py. Agent classes should only consume provider constants injected from config.
- Keep prompts in prompts/\*.txt and load with BaseAgent.load_prompt. Avoid large inline prompt strings in Python files.
- Keep agent outputs structured and parseable with stable labels and keys.
- Include both agent name and provider name in judge synthesis input for mixed-model traceability and ablation analysis.
- Keep evaluation outputs reproducible: persist machine-readable artifacts to results/\*.json in addition to terminal summaries.
- When adding metrics, keep deterministic settings and explicit parameters (for example weighted averages and zero-division handling) to preserve baseline comparability.
- Prefer minimal, localized edits that do not break existing experiment pipelines.
