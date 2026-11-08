#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "729429f8ea2c"


def load_generator(repo: Path):
    path = repo / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path, hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    repo = Path.cwd()
    gen, source, source_sha = load_generator(repo)
    cases = [
        ("base", {}),
        ("palette_warm", {"palette_kind": "warm"}),
        ("palette_cool", {"palette_kind": "cool"}),
        ("unknown_axis", {"definitely_not_an_axis": "x"}),
    ]
    rows = []
    for name, overrides in cases:
        grid = gen.generate(123, 7, difficulty="medium", **overrides)
        rows.append({
            "name": name,
            "overrides": overrides,
            "grid": grid,
            "grid_sha256": hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest(),
            "self_check": gen.self_check(grid, difficulty="medium", meta=overrides),
        })
    report = {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(source.relative_to(repo)),
        "generator_sha256": source_sha,
        "seed": 123,
        "sample_index": 7,
        "difficulty": "medium",
        "all_outputs_identical": all(row["grid"] == rows[0]["grid"] for row in rows[1:]),
        "all_self_checks_clean": all(not row["self_check"] for row in rows),
        "cases": rows,
        "command_cwd": str(repo),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    input_path = out.with_name("input.json")
    input_path.write_text(json.dumps(rows[0]["grid"], indent=2) + "\n")
    print(json.dumps({
        "task_id": TASK_ID,
        "generator_sha256": source_sha,
        "all_outputs_identical": report["all_outputs_identical"],
        "all_self_checks_clean": report["all_self_checks_clean"],
        "report": str(out),
        "input": str(input_path),
    }, sort_keys=True))
    return 0 if report["all_outputs_identical"] and report["all_self_checks_clean"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
