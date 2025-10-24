# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **llm-mogent**, a framework for LLM-driven project management using structured roadmaps, decisions, and plan deltas. The system enables LLMs to operate autonomously within defined guardrails using JSON schemas, validation tools, and an Incident→Decision→Plan Delta→Roadmap operation loop.

## Core Architecture

### Three-Layer JSON Schema System
1. **Roadmap** (`assets/schemas/roadmap.schema.json`): Top-level project plan with meta, inputs, plan steps, validation, risks, and release info
2. **Decision** (`assets/schemas/decision.schema.json`): ADR-style decision records capturing problem context, options, and approved choices
3. **Plan Delta** (`assets/schemas/plan-delta.schema.json`): Atomic operations (add/update/remove/reorder/set_next_step) to modify roadmaps

### Directory Structure
- `assets/`: JSON schemas, prompt templates for the operation loop, and sample files
  - `assets/schemas/`: JSON Schema definitions for roadmap, decision, plan-delta
  - `assets/prompts/loop/`: 4-phase operation loop prompts (01_intake, 02_decision_gate, 03_plan_delta, 04_prioritize)
  - `assets/prompts/roadmap/`: Roadmap authoring checklist and prompt
  - `assets/templates/`: Sample JSON files showing correct structure
- `tools/`: Python validation and delta application scripts
- `projects/`: Individual project roadmaps (e.g., `projects/mogent/roadmap.mogent.json`)
- `docs/`: HOWTO guides referenced by LLM operation loop
- `.github/workflows/`: CI automation for validation

### Operation Loop (Incident → Roadmap)
The core workflow defined in `LLM_OPERATION_LOOP.md`:
1. **Intake & Explore**: Analyze incident, generate options → `decisions/ADR-*.json` (status: proposed)
2. **Decision Gate**: Human approval/rejection → update decision JSON (status: approved/rejected)
3. **Plan Delta**: Generate atomic operations → `deltas/plan-delta-*.json`
4. **Integrate**: Apply delta to roadmap, validate with strict evidence checks

## Common Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv .venv && source .venv/bin/activate

# Install development dependencies (includes jsonschema)
python -m pip install -r requirements-dev.txt
```

### Validation Commands
```bash
# Validate roadmap JSON against schema
python -m tools.validate_roadmap roadmap.json

# Validate with strict evidence checks (path:line or cmd: format required)
python -m tools.validate_roadmap --strict-evidence roadmap.json

# Validate all roadmap files (excluding assets/)
python -m tools.validate_roadmap projects/**/roadmap*.json

# Validate decision JSON
python -m tools.validate_decision decisions/*.json

# Validate plan delta JSON
python -m tools.validate_plan_delta deltas/*.json
```

### Apply Plan Deltas
```bash
# Apply delta operations to roadmap
python -m tools.roadmap_apply_delta --roadmap roadmap.json --delta deltas/plan-delta-*.json
```

## Key Constraints and Rules

### Evidence Requirements (LLM_CHECKLIST.md compliance)
- Every factual claim in roadmaps/decisions MUST have evidence in `references[]`
- Evidence format: `path:line` (e.g., `AGENTS.md:17`), `path#Lline`, or `cmd: <command>`
- Use `--strict-evidence` flag to enforce this in validation
- File paths must be relative to repository root; no absolute paths or URLs

### LLM Operation Guidelines (from LLM_CHECKLIST.md)
1. **Deterministic Progress**: Execute exactly ONE `next_step` before re-planning
2. **Context Limits**: Summarize large files first, then verify critical sections
3. **Hallucination Prevention**: Attach `path:line` or command output for ALL claims
4. **Memory Logging**: Persist assumptions/decisions in `open_questions` and `references`
5. **Tool Crosscheck**: Verify results via lint/tests and logs

### Roadmap Authoring Rules (from AGENTS.md)
- Purpose/scope/metrics: Keep concise (metrics: 1-3 items max)
- Plan steps: 5-9 atomic work units with measurable success criteria
- Test coverage: ≥85% on safety-critical modules
- High-risk items: Perform spike (short validation) first

### Commit Conventions
- Follow Conventional Commits: `feat:`, `fix:`, `docs:`, etc.
- Branch names: `type/short-description` (e.g., `feat/rag-router`)
- PRs must link tracker issues and attach before/after evidence

## Testing
Currently no production code to test. When tests exist:
- Unit tests: `pytest tests/unit -k <pattern>` for focused runs
- Full suite: `pytest` (targets ≥85% coverage)
- Validation tests run in CI via `.github/workflows/roadmap-validate.yml`

## CI/CD
- **roadmap-validate.yml**: Validates sample roadmap and all `roadmap*.json` files with `--strict-evidence`
- **decision-delta-validate.yml**: Validates decision and plan-delta JSON files
- CI blocks PR merge on validation failures

## Important Files for LLM Context
When working on roadmaps or decisions, reference these:
- `LLM_CHECKLIST.md`: Checklist for roadmap execution (purpose/scope/WBS/evidence/verification)
- `LLM_OPERATION_LOOP.md`: 4-phase loop definition with prompt locations
- `AGENTS.md`: Repository structure, coding style, naming conventions
- `docs/HOWTO_ROADMAP_AUTHORING.md`: Step-by-step guide for roadmap creation
- `docs/HOWTO_STRICT_EVIDENCE.md`: Evidence format requirements
- `docs/HOWTO_INCIDENT_TO_ROADMAP_LOOP.md`: Full operation loop details

## Schema Contract
- **Roadmap** must have: meta, inputs, plan[], validation, risks, release, next_step, references[]
- **Decision** must have: problem, options[], decision, justification, consequences, references[]
- **Plan Delta** must have: decision_id, operations[] with type (add/update/remove/reorder/set_next_step)
- All schemas enforce: version=1.0, strict additionalProperties=false

## Working with Projects
- Each project lives in `projects/<name>/`
- Project roadmaps: `projects/<name>/roadmap.<name>.json`
- Current project: `mogent` (MVP orchestrator and agent runtime)

## NixOS Environment Notes
- System uses NixOS with flake at `/home/gmc/nixos-dotfiles`
- Avoid `sudo` commands; delegate to user
- Test CLI tools with `--help` or `--version` before use
- Python 3.12+ available (repo targets 3.11+ per AGENTS.md)
