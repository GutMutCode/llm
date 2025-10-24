# Repository Guidelines

## Project Structure & Module Organization
- `src/llm/` hosts core runtime modules (prompt routing, tool adapters, evaluation utilities). Keep subpackages grouped by concern (e.g., `planning`, `memory`, `io`).
- `agents/` contains agent manifests (YAML/JSON) and Python entrypoints. Mirror production agent names and keep helper functions alongside their manifest.
- `configs/` stores environment-specific settings. Provide `.example` templates for anything with secrets and commit only the template.
- `tests/` mirrors `src/` structure with `unit/` and `integration`. Add reusable fixtures under `tests/fixtures`.
- `assets/` holds prompt templates, sample transcripts, and reference datasets used in docs or tests.
- `docs/` curates HOWTOs; update `docs/README.md` whenever new documentation ships.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate` creates and activates the local virtual environment.
- `pip install -r requirements.txt` installs pinned production dependencies; rerun after adding packages.
- `python -m pip install -r requirements-dev.txt` brings in linting and testing tooling.
- `pytest` executes the full unit and integration suite; use `pytest tests/unit -k my_agent` for focused runs.
- `ruff check src agents` enforces lint rules; `ruff format src agents` applies formatting before committing.
- `python -m llm.cli serve --config configs/dev.yaml` launches the local orchestrator for manual end-to-end checks.

## Coding Style & Naming Conventions
- Target Python 3.11+, 4-space indentation, and comprehensive type hints. Keep functions under ~40 lines and break complex flows into helpers under `src/llm/utils`.
- Use snake_case for modules/functions, PascalCase for classes, and UPPER_SNAKE_CASE for constants. Agent manifests use kebab-case filenames (e.g., `web-search.yaml`).
- Prefer dataclasses for structured settings and Pydantic models for external payloads; serialize via `model_dump`.

## Testing Guidelines
- Place unit tests under `tests/unit` and integration suites under `tests/integration`. Name files `test_<module>.py`.
- Maintain ≥85% coverage on planners and safety-critical modules; add regression tests reflecting reported incidents under `tests/regression`.
- Reuse pytest fixtures in `tests/conftest.py` for sandboxed tool stubs; patch network calls with `respx` or `responses` before hitting live services.

## Commit & Pull Request Guidelines
- Follow Conventional Commits (`feat:`, `fix:`, `docs:`, etc.) and keep each commit focused on one concern.
- Branch names follow `type/short-description` (e.g., `feat/rag-router`).
- Pull requests must explain behavioral changes, link tracker issues, and attach before/after logs or screenshots when applicable.
- Request review from an LLM maintainer and wait for green CI before merging.

## Agent-Specific Notes
- Declare external tool permissions in each agent manifest and document required environment variables in `configs/README.md`.
- For safety-critical agents, attach an evaluation run summary in the PR describing prompt sets used and pass/fail counts.
