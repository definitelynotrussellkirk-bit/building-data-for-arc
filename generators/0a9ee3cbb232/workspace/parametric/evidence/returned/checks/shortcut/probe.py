#!/usr/bin/env python3
"""Retain a source-bound canonical-shortcut witness for task 0a9ee3cbb232."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import find_root

TASK_ID = "0a9ee3cbb232"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("selected_shortcut_probe", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_canonical(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise RuntimeError(f"missing canonical task {TASK_ID}")


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--seed", type=int, default=20261021)
    args = parser.parse_args()

    repo = find_root(__file__)
    task_home = repo / "generators" / TASK_ID
    generator_path = task_home / "generator.py"
    canonical_path = repo / "shared" / "data" / "canonical" / "puzzles.jsonl"
    generator = load_module(generator_path)
    canonical = load_canonical(canonical_path)
    rival = generator.CANONICAL_SHORTCUTS["connected_components"]

    canonical_checks = []
    for split in ("train", "test"):
        for pair_index, pair in enumerate(canonical[split]):
            actual = rival(pair["input"])
            canonical_checks.append(
                {
                    "split": split,
                    "pair_index": pair_index,
                    "rival_output": actual,
                    "canonical_output": pair["output"],
                    "fits": actual == pair["output"],
                }
            )
    if not all(row["fits"] for row in canonical_checks):
        raise SystemExit("connected-components rival does not fit every canonical pair")

    witness = None
    for sample_index in range(64):
        difficulty = ("easy", "medium", "hard")[sample_index % 3]
        grid = generator.generate(args.seed, sample_index, difficulty=difficulty)
        intended = generator._mirror(grid)
        rival_output = rival(grid)
        if intended != rival_output:
            witness = {
                "seed": args.seed,
                "sample_index": sample_index,
                "difficulty": difficulty,
                "overrides": {},
                "input": grid,
                "intended_python_mirror": intended,
                "connected_components_rival": rival_output,
                "self_check": generator.self_check(grid, difficulty=difficulty),
                "observed_controls": generator.observe_overrides(grid),
            }
            break
    if witness is None:
        raise SystemExit("no generated shortcut witness in sample indices 0..63")
    if witness["self_check"]:
        raise SystemExit(f"witness left generator domain: {witness['self_check']}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "input.json", witness["input"])
    report = {
        "schema": "0a9ee3cbb232-connected-components-shortcut-probe-v1",
        "status": "pre_racket_passed",
        "task_id": TASK_ID,
        "generator_sha256": sha256(generator_path),
        "canonical_jsonl_sha256": sha256(canonical_path),
        "canonical_program_sha256": hashlib.sha256(
            canonical["program_solution"].encode("utf-8")
        ).hexdigest(),
        "shortcut": {
            "name": "connected_components",
            "description": "count 4-connected components of each color instead of maximal horizontal runs",
            "canonical_pairs_checked": len(canonical_checks),
            "canonical_pairs_fit": sum(row["fits"] for row in canonical_checks),
            "checks": canonical_checks,
        },
        "generated_witness": witness,
        "search": {
            "seed": args.seed,
            "sample_index_range": [0, 63],
            "first_disagreement_sample_index": witness["sample_index"],
        },
    }
    write_json(out_dir / "probe.json", report)
    print(json.dumps({
        "status": "passed",
        "canonical_fit": f"{sum(row['fits'] for row in canonical_checks)}/{len(canonical_checks)}",
        "witness_sample_index": witness["sample_index"],
        "intended": witness["intended_python_mirror"],
        "rival": witness["connected_components_rival"],
        "input_path": str(out_dir / "input.json"),
        "report_path": str(out_dir / "probe.json"),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
