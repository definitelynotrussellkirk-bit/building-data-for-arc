"""Emit a source-bound counterexample for each declared canonical shortcut."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "a8a99930c51a"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=71)
    parser.add_argument("--sample-index", type=int, default=2)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    root = find_root(__file__)
    gen, source, source_sha256 = load_selected_generator(TASK_ID, root=root)
    grid = gen.generate(args.seed, args.sample_index)
    findings = gen.self_check(grid)
    if findings:
        raise SystemExit(f"generated input failed self_check: {findings}")

    intended = gen._solve_strip(grid)
    rivals = {
        name: solver(grid)
        for name, solver in gen.CANONICAL_SHORTCUTS.items()
    }
    disagreements = [name for name, output in rivals.items() if output != intended]
    if not disagreements:
        raise SystemExit("chosen case does not refute a declared canonical shortcut")

    payload = {
        "schema": "a8a99930c51a-shortcut-counterexample-v1",
        "task_id": TASK_ID,
        "generator_path": str(source.relative_to(root)),
        "generator_sha256": source_sha256,
        "seed": args.seed,
        "sample_index": args.sample_index,
        "difficulty": None,
        "overrides": {},
        "self_check": findings,
        "input": grid,
        "intended_python_mirror": intended,
        "rival_outputs": rivals,
        "disagreeing_rivals": disagreements,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "out": str(args.out),
        "generator_sha256": source_sha256,
        "disagreeing_rivals": disagreements,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
