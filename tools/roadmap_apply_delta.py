from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _schema_path(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "assets" / "schemas" / name


def validate_with_schema(data: Any, schema_path: Path) -> List[str]:
    try:
        from jsonschema import Draft7Validator
    except Exception as e:  # pragma: no cover
        return [f"jsonschema not available: {e}"]
    try:
        schema = load_json(schema_path)
    except Exception as e:  # pragma: no cover
        return [f"failed to load schema {schema_path}: {e}"]
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    messages: List[str] = []
    for err in errors:
        loc = "/".join(str(x) for x in err.path) or "$"
        messages.append(f"{loc}: {err.message}")
    return messages


def deep_update(dst: Dict[str, Any], src: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            deep_update(dst[k], v)
        else:
            dst[k] = v
    return dst


def apply_ops(roadmap: Dict[str, Any], ops: List[Dict[str, Any]]) -> Dict[str, Any]:
    plan: List[Dict[str, Any]] = list(roadmap.get("plan", []))
    index: Dict[str, int] = {item["id"]: i for i, item in enumerate(plan) if isinstance(item, dict) and "id" in item}

    for op in ops:
        kind = op.get("op")
        if kind == "add":
            item = op.get("item")
            if not isinstance(item, dict) or "id" not in item:
                raise ValueError("add op requires object 'item' with an 'id'")
            if item["id"] in index:
                raise ValueError(f"duplicate id in add: {item['id']}")
            plan.append(item)
            index[item["id"]] = len(plan) - 1
        elif kind == "update":
            pid = op.get("id")
            fields = op.get("fields")
            if not isinstance(pid, str) or not isinstance(fields, dict):
                raise ValueError("update op requires 'id' and object 'fields'")
            if pid not in index:
                raise ValueError(f"update id not found: {pid}")
            deep_update(plan[index[pid]], fields)
        elif kind == "remove":
            pid = op.get("id")
            if not isinstance(pid, str):
                raise ValueError("remove op requires 'id'")
            if pid not in index:
                # no-op remove for robustness
                continue
            del plan[index[pid]]
            # rebuild index
            index = {item["id"]: i for i, item in enumerate(plan)}
        elif kind == "reorder":
            order = op.get("order")
            if not isinstance(order, list) or not all(isinstance(x, str) for x in order):
                raise ValueError("reorder op requires array 'order' of ids")
            # Stable reorder: bring listed ids to the front in given order; keep others in prior relative order
            wanted = [x for x in order if x in index]
            others = [it["id"] for it in plan if it["id"] not in wanted]
            new_ids = wanted + others
            plan = [next(item for item in plan if item["id"] == pid) for pid in new_ids]
            index = {item["id"]: i for i, item in enumerate(plan)}
        elif kind == "set_next_step":
            step_id = op.get("step_id")
            prompt = op.get("prompt")
            if not isinstance(step_id, str) or not isinstance(prompt, str):
                raise ValueError("set_next_step requires 'step_id' and 'prompt'")
            roadmap["next_step"] = {"step_id": step_id, "prompt": prompt}
        else:
            raise ValueError(f"unsupported op: {kind}")

    roadmap["plan"] = plan
    return roadmap


def iter_delta_files(paths: Sequence[str]) -> Iterable[Path]:
    for p in paths:
        path = Path(p)
        if any(ch in p for ch in "*?[]"):
            yield from (Path(q) for q in Path().glob(p))
        elif path.is_dir():
            yield from path.rglob("*.json")
        else:
            yield path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply plan-delta JSON ops to a roadmap JSON with schema validation.")
    parser.add_argument("--roadmap", required=True, help="Path to roadmap JSON to update")
    parser.add_argument("--delta", required=True, nargs="+", help="Plan-delta JSON file(s) or globs")
    parser.add_argument("--out", help="Output path (defaults to overwrite --roadmap)")
    parser.add_argument("--dry-run", action="store_true", help="Print updated roadmap to stdout without writing")
    parser.add_argument("--no-validate", action="store_true", help="Skip schema validation of inputs/outputs")
    args = parser.parse_args(argv)

    roadmap_path = Path(args.roadmap)
    if not roadmap_path.exists():
        print(f"Roadmap not found: {roadmap_path}", file=sys.stderr)
        return 2
    try:
        roadmap = load_json(roadmap_path)
    except Exception as e:
        print(f"Failed to load roadmap: {e}", file=sys.stderr)
        return 2

    if not args.no_validate:
        errs = validate_with_schema(roadmap, _schema_path("roadmap.schema.json"))
        if errs:
            print("Roadmap failed schema validation before applying deltas:", file=sys.stderr)
            for m in errs:
                print(f"  - {m}", file=sys.stderr)
            return 1

    delta_files = list(iter_delta_files(args.delta))
    if not delta_files:
        print("No delta files found.")
        return 0

    for df in delta_files:
        try:
            delta = load_json(df)
        except Exception as e:
            print(f"Failed to load delta {df}: {e}", file=sys.stderr)
            return 2
        if not args.no_validate:
            derrs = validate_with_schema(delta, _schema_path("plan-delta.schema.json"))
            if derrs:
                print(f"Delta failed schema validation: {df}", file=sys.stderr)
                for m in derrs:
                    print(f"  - {m}", file=sys.stderr)
                return 1
        ops = delta.get("ops") or []
        try:
            roadmap = apply_ops(roadmap, ops)
        except Exception as e:
            print(f"Failed applying ops from {df}: {e}", file=sys.stderr)
            return 1

    if not args.no_validate:
        out_errs = validate_with_schema(roadmap, _schema_path("roadmap.schema.json"))
        if out_errs:
            print("Updated roadmap failed schema validation:", file=sys.stderr)
            for m in out_errs:
                print(f"  - {m}", file=sys.stderr)
            return 1

    if args.dry_run:
        json.dump(roadmap, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0

    out_path = Path(args.out) if args.out else roadmap_path
    save_json(out_path, roadmap)
    print(f"Updated roadmap written to {out_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

