#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "3b92ab3eeca6"


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
        ("palette_size_2", {"palette_size": 2}),
        ("palette_size_5", {"palette_size": 5}),
        ("unknown_axis", {"definitely_not_an_axis": "x"}),
    ]
    rows = []
    for name, overrides in cases:
        grid = gen.generate(101, 7, **overrides)
        rows.append({
            "name": name,
            "overrides": overrides,
            "grid": grid,
            "grid_sha256": hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest(),
            "nonzero_colors": sorted({value for row in grid for value in row if value}),
            "self_check": gen.self_check(grid, meta=overrides),
        })
    report = {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(source.relative_to(repo)),
        "generator_sha256": source_sha,
        "seed": 101,
        "sample_index": 7,
        "difficulty": None,
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
