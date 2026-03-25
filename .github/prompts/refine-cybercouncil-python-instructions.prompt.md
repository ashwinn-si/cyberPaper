---
description: 'Review and refine the CyberCouncil Python instruction file for clarity, enforceability, and architecture safety. Use when you want to improve project rules without over-constraining development.'
name: 'Refine CyberCouncil Python Instructions'
argument-hint: 'Optional focus (e.g., stricter provider rules, evaluation reproducibility, prompt handling).'
agent: 'CyberCouncil Research Engineer'
model: ['GPT-5 (copilot)', 'Claude Sonnet 4.5 (copilot)']
tools: [read, edit, search]
---

Refine the instruction file at [CyberCouncil Python rules](../instructions/cybercouncil-python.instructions.md).

Goal:

- Improve precision and usefulness of the rules.
- Keep rules concise, testable, and aligned with the CyberCouncil architecture.
- Avoid adding broad or vague guidance.

Inputs:

- User request in this chat message (treat it as the focus area).
- Existing instruction content in [CyberCouncil Python rules](../instructions/cybercouncil-python.instructions.md).

Required checks before editing:

- Ensure each rule is actionable and verifiable.
- Ensure rules do not conflict with config-driven provider wiring.
- Ensure rules preserve separation of concerns across providers, agents, council, and evaluation.
- Ensure guidance supports reproducible experiments for research reporting.

Editing policy:

- Make minimal edits only.
- Keep one concern per bullet.
- Prefer concrete language (must/avoid) over soft wording.
- Do not duplicate guidance that already exists unless rewording for clarity.

Output format:

1. Short summary of what changed and why.
2. Updated file path.
3. Open questions (if any) to tighten the instruction further.
