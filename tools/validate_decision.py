from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def iter_json_files(paths: Sequence[str]) -> Iterable[Path]:
    for p in paths:
        path = Path(p)
        if any(ch in p for ch in "*?[]"):
            yield from (Path(q) for q in Path().glob(p))
        elif path.is_dir():
            yield from path.rglob("*.json")
        else:
            yield path


def validate_against_schema(data: Any, schema: dict) -> list[str]:
    try:
        from jsonschema import Draft7Validator
    except Exception as e:  # pragma: no cover
        return [f"jsonschema not available: {e}"]
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    messages: list[str] = []
    for err in errors:
        loc = "/".join(str(x) for x in err.path) or "$"
        messages.append(f"{loc}: {err.message}")
    return messages


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate decision (ADR) JSON against schema.")
    parser.add_argument("paths", nargs="+", help="JSON files, directories, or globs")
    parser.add_argument("--schema", default=str(Path(__file__).resolve().parents[1] / "assets" / "schemas" / "decision.schema.json"))
    args = parser.parse_args(argv)

    try:
        schema = load_json(Path(args.schema))
    except Exception as e:
        print(f"Failed to load schema: {e}", file=sys.stderr)
        return 2

    files = list(iter_json_files(args.paths))
    total = 0
    for f in files:
        try:
            data = load_json(f)
        except Exception as e:
            print(f"FAIL {f}: {e}", file=sys.stderr)
            total += 1
            continue
        errs = validate_against_schema(data, schema)
        if errs:
            print(f"FAIL {f}")
            for m in errs:
                print(f"  - {m}")
            total += len(errs)
        else:
            print(f"OK   {f}")
    if total:
        print(f"Validation failed with {total} issue(s).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

