#!/usr/bin/env python3
"""Source-bound probe for declared shortcuts and lesson competitors."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "01ab62800c73"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--sample-index", type=int, default=0)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="easy")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    root = find_root(__file__)
    module, source_path, generator_sha256 = load_selected_generator(TASK, root=root)
    labeled = canonical_pairs(TASK, root=root, labeled_only=True)
    grid = module.generate(args.seed, args.sample_index, difficulty=args.difficulty)
    intended = module.rule_mirror(grid)

    declared = {}
    names = sorted(set(module.CANONICAL_SHORTCUTS) | set(module.LESSON_COMPETITORS))
    for name in names:
        solver = module.LESSON_COMPETITORS.get(name, module.CANONICAL_SHORTCUTS.get(name))
        prediction = solver(grid)
        declared[name] = {
            "fits_all_labeled_canonical_pairs": all(
                solver(pair["input"]) == pair["output"] for pair in labeled
            ),
            "generated_prediction": prediction,
            "disagrees_with_intended": prediction != intended,
        }

    payload = {
        "schema": "01ab62800c73-shortcut-probe-v1",
        "task_id": TASK,
        "generator_path": str(source_path.relative_to(root)),
        "generator_sha256": generator_sha256,
        "rule_hash": module.RULE_HASH,
        "seed": args.seed,
        "sample_index": args.sample_index,
        "difficulty": args.difficulty,
        "input": grid,
        "python_rule_mirror_output": intended,
        "self_check": module.self_check(grid),
        "observed_overrides": module.observe_overrides(grid),
        "declared_rivals": declared,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(out), "generator_sha256": generator_sha256, "rivals": declared}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
