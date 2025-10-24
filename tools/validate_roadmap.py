from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Sequence, Tuple


@dataclass
class Issue:
    file: Path
    location: str
    message: str


def _default_schema_path() -> Path:
    # tools/validate_roadmap.py -> repo_root/assets/schemas/roadmap.schema.json
    return Path(__file__).resolve().parents[1] / "assets" / "schemas" / "roadmap.schema.json"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def iter_json_files(paths: Sequence[str]) -> Iterable[Path]:
    for p in paths:
        path = Path(p)
        if any(ch in p for ch in "*?[]"):
            # Glob pattern
            yield from (Path(q) for q in Path().glob(p))
        elif path.is_dir():
            yield from path.rglob("*.json")
        else:
            yield path


def validate_against_schema(data: Any, schema: dict) -> List[str]:
    try:
        from jsonschema import Draft7Validator
    except Exception as e:  # pragma: no cover - environment dependency
        return [
            "jsonschema is not installed. Install with `python -m pip install jsonschema` or add it to requirements-dev.txt.",
            f"Import error: {e}",
        ]

    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    messages: List[str] = []
    for err in errors:
        loc = "/".join(str(x) for x in err.path) or "$"
        messages.append(f"{loc}: {err.message}")
    return messages


def additional_checks(data: Any) -> List[str]:
    messages: List[str] = []
    # Enforce presence and minimum count of references (authoring checklist contract)
    refs = data.get("references")
    if refs is None:
        messages.append("references: missing (expect at least 3 items with claim/evidence)")
    elif not isinstance(refs, list):
        messages.append("references: must be an array")
    elif len(refs) < 3:
        messages.append("references: must contain at least 3 items")
    return messages


def _parse_evidence_ref(evidence: str) -> Tuple[str, str | None, int | None]:
    """
    Returns tuple(kind, path, line) where kind in {"file", "cmd", "unknown"}.
    For file refs, path is relative repository path, and line is 1-based line number.
    Accepted patterns:
    - path:line
    - path#Lline
    - cmd: <command snippet>
    """
    s = evidence.strip()
    if s.lower().startswith("cmd:"):
        rest = s[4:].strip()
        return ("cmd", None if not rest else rest, None)
    if "#L" in s:
        parts = s.rsplit("#L", 1)
        if len(parts) == 2 and parts[1].isdigit():
            return ("file", parts[0], int(parts[1]))
    if ":" in s:
        head, tail = s.rsplit(":", 1)
        if tail.isdigit():
            return ("file", head, int(tail))
    return ("unknown", None, None)


def strict_evidence_checks(data: Any, repo_root: Path) -> List[str]:
    messages: List[str] = []
    refs = data.get("references")
    if not isinstance(refs, list):
        return messages

    for idx, item in enumerate(refs):
        prefix = f"references[{idx}]"
        if not isinstance(item, dict):
            messages.append(f"{prefix}: must be an object with claim/evidence")
            continue
        ev = item.get("evidence")
        if not isinstance(ev, str) or not ev.strip():
            messages.append(f"{prefix}.evidence: must be a non-empty string")
            continue
        kind, path_or_cmd, line = _parse_evidence_ref(ev)
        if kind == "cmd":
            if not path_or_cmd:
                messages.append(f"{prefix}.evidence: cmd must include content after 'cmd:'")
            continue
        if kind == "file":
            path = path_or_cmd or ""
            if "://" in path:
                messages.append(f"{prefix}.evidence: external URLs not allowed: {path}")
                continue
            p = Path(path)
            if p.is_absolute():
                messages.append(f"{prefix}.evidence: absolute paths not allowed: {path}")
                continue
            try:
                norm = (repo_root / p).resolve()
            except Exception:
                messages.append(f"{prefix}.evidence: invalid path: {path}")
                continue
            # ensure within repo_root
            try:
                norm.relative_to(repo_root)
            except Exception:
                messages.append(f"{prefix}.evidence: path escapes repository root: {path}")
                continue
            if not norm.exists() or not norm.is_file():
                messages.append(f"{prefix}.evidence: file does not exist: {path}")
                continue
            if not isinstance(line, int) or line <= 0:
                messages.append(f"{prefix}.evidence: invalid line number in {ev}")
                continue
            try:
                with norm.open("r", encoding="utf-8", errors="ignore") as f:
                    for i, _ in enumerate(f, start=1):
                        if i >= line:
                            break
                    else:
                        i = 0
                if i < line:
                    messages.append(f"{prefix}.evidence: line {line} exceeds file length for {path}")
            except Exception as e:
                messages.append(f"{prefix}.evidence: failed to read file {path}: {e}")
            continue
        messages.append(f"{prefix}.evidence: unsupported format (use path:line, path#Lline, or 'cmd: ...')")
    return messages


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate roadmap JSON against schema and additional checks.")
    parser.add_argument("paths", nargs="+", help="JSON files, directories, or globs (e.g., roadmap.json or **/roadmap*.json)")
    parser.add_argument("--schema", default=str(_default_schema_path()), help="Path to JSON schema file")
    parser.add_argument("--strict-evidence", action="store_true", help="Enforce evidence format and file/line existence for references[*].evidence")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]), help="Repository root for resolving file references")
    args = parser.parse_args(argv)

    schema_path = Path(args.schema)
    if not schema_path.exists():
        print(f"Schema not found: {schema_path}", file=sys.stderr)
        return 2

    try:
        schema = load_json(schema_path)
    except Exception as e:
        print(f"Failed to load schema: {e}", file=sys.stderr)
        return 2

    files = list(iter_json_files(args.paths))
    if not files:
        print("No JSON files found for validation.")
        return 0

    total_issues = 0
    repo_root = Path(args.repo_root).resolve()
    for fp in files:
        try:
            data = load_json(fp)
        except Exception as e:
            print(f"FAIL {fp}: Could not parse JSON ({e})", file=sys.stderr)
            total_issues += 1
            continue

        schema_errors = validate_against_schema(data, schema)
        extra_errors = additional_checks(data)
        strict_errors: List[str] = []
        if args.strict_evidence:
            strict_errors = strict_evidence_checks(data, repo_root)
        if schema_errors or extra_errors or strict_errors:
            print(f"FAIL {fp}")
            for msg in schema_errors:
                print(f"  - {msg}")
            for msg in extra_errors:
                print(f"  - {msg}")
            for msg in strict_errors:
                print(f"  - {msg}")
            total_issues += len(schema_errors) + len(extra_errors) + len(strict_errors)
        else:
            print(f"OK   {fp}")

    if total_issues > 0:
        print(f"Validation failed with {total_issues} issue(s).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
