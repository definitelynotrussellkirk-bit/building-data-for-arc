#!/usr/bin/env python3
"""Source-bound shortcut probe for a36fd3a00941.

It verifies which declared canonical shortcuts fit every labeled canonical pair,
then emits one generated teaching case and every declared competitor output.
Run from repo with the shared runtime on PYTHONPATH, or through the packet wrapper.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK_ID = "a36fd3a00941"
HERE = Path(__file__).resolve()
ROOT = find_root(HERE)
GENERATOR_PATH = HERE.parents[1] / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("generator_under_probe", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _same(left: Any, right: Any) -> bool:
    return [list(row) for row in left] == [list(row) for row in right]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--sample-index", type=int, default=0)
    parser.add_argument("--difficulty", default="medium")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    gen = _load_generator()
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    shortcuts = dict(gen.CANONICAL_SHORTCUTS)
    competitors = dict(gen.LESSON_COMPETITORS)

    canonical_fit = {
        name: {
            "fits": sum(_same(fn(pair["input"]), pair["output"]) for pair in pairs),
            "total": len(pairs),
        }
        for name, fn in shortcuts.items()
    }

    grid = gen.generate(args.seed, args.sample_index, difficulty=args.difficulty)
    intended = gen.rule_mirror(grid)
    rival_outputs = {name: fn(grid) for name, fn in competitors.items()}
    disagreements = {
        name: not _same(output, intended)
        for name, output in rival_outputs.items()
    }

    report = {
        "schema": "a36fd3a00941-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "rule_hash": gen.RULE_HASH,
        "seed": args.seed,
        "sample_index": args.sample_index,
        "difficulty": args.difficulty,
        "canonical_shortcut_fit": canonical_fit,
        "input": grid,
        "intended_python_mirror": intended,
        "competitor_outputs": rival_outputs,
        "competitor_disagrees": disagreements,
        "self_check": gen.self_check(grid),
        "strict_canonical_like": gen.strict_canonical_like(grid),
    }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
