# LLM Roadmap Authoring Checklist (for agents)

Goal: Produce a roadmap JSON that validates against `assets/schemas/roadmap.schema.json` and embeds evidence per `LLM_CHECKLIST.md`.

MUST
- Output JSON only. No prose. Conform to `assets/schemas/roadmap.schema.json`.
- Keep purpose/scope/metrics within 3 short items (LLM_CHECKLIST.md:3–6).
- Record environment: filesystem, network, approvals, sensitive_data, time budget (LLM_CHECKLIST.md:18–21).
- Attach evidence for factual claims using `path:line` or command snippet (LLM_CHECKLIST.md:14–16,51).
- Produce 5–12 plan items with success criteria and validation artifacts (LLM_CHECKLIST.md:23–31,33–36).
- Include LLM limitations reflection in `meta.llm_limitations` (LLM_CHECKLIST.md:49–54).
- End with `next_step` containing a single actionable step and a short prompt (LLM_CHECKLIST.md:27–31,52).

SHOULD
- Prefer atomic tasks; one goal → one deliverable set (LLM_CHECKLIST.md:29).
- Mark high-risk tasks as `risk_level: "high"` and front-load a spike.
- Keep each success criterion ≤ 1 line, measurable.
- Use repo guidelines from `AGENTS.md` for structure, testing, and style.

SHOULD NOT
- Do not propose destructive actions without explicit approval triggers.
- Do not include secrets; reference `.example` files only (LLM_CHECKLIST.md:38–41).

ACTION LOOP (repeat until done)
1) Plan: Select the next 1 step only; define its success evidence.
2) Do: Produce minimal changes to satisfy that step.
3) Check: Capture test/linters/log evidence.
4) Log: Append decisions/assumptions/open_questions.

FIELD LIMITS (hard caps to avoid context blowup)
- `inputs.success_metrics`: 1–3 items.
- `plan[*].success_criteria`: 1–3 items.
- `plan`: 5–12 items total.
- Strings ≤ 300 chars unless otherwise stated by schema.

EVIDENCE EXAMPLES
- File: `AGENTS.md:11` (command reference)
- File: `LLM_CHECKLIST.md:49` (LLM limitations)
- Command: `pytest -q` → include 1–3 line summary

VALIDATION COMMANDS (suggested)
- `ruff check src agents`
- `ruff format --check src agents`
- `pytest -q`

OUTPUT CONTRACT
- Single JSON object; validates against `assets/schemas/roadmap.schema.json`.
- All arrays non-empty where required.
- `references` contains at least 3 items tying claims to evidence.

