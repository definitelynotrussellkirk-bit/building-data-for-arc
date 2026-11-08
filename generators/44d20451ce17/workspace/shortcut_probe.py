#!/usr/bin/env python3
"""Recheck every declared canonical-fitting shortcut on one generated witness.

This is an authoring/audit tool, not a blind-solve helper: it reads canonical
labels and imports the selected generator. Run it from either the repository or
an isolated task-test runtime with reviewer_support on PYTHONPATH.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "44d20451ce17"


def build_report(*, seed: int, sample_index: int) -> dict[str, Any]:
    root = find_root(__file__)
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    overrides = {
        "grid_h": 5,
        "grid_w": 5,
        "n_ones": 4,
        "scene_profile": "counterexample",
    }
    grid = generator.generate(seed, sample_index, **overrides)
    intended = generator.rule_mirror(deepcopy(grid))

    rivals: dict[str, Any] = {}
    for name, rival in generator.CANONICAL_SHORTCUTS.items():
        canonical_fit = all(
            rival(deepcopy(pair["input"])) == pair["output"] for pair in pairs
        )
        rival_output = rival(deepcopy(grid))
        rivals[name] = {
            "fits_all_labeled_canonical_pairs": canonical_fit,
            "differs_on_counterexample": rival_output != intended,
            "output": rival_output,
        }

    return {
        "schema": "arcpuzzles-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(source_path.relative_to(root)),
        "generator_sha256": source_sha256,
        "rule_hash": generator.RULE_HASH,
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": None,
        "overrides": overrides,
        "input": grid,
        "intended_output_python_mirror": intended,
        "self_check": generator.self_check(deepcopy(grid)),
        "observed_overrides": generator.observe_overrides(deepcopy(grid)),
        "canonical_pair_count": len(pairs),
        "rivals": rivals,
        "all_declared_shortcuts_fit_canonical": all(
            row["fits_all_labeled_canonical_pairs"] for row in rivals.values()
        ),
        "all_declared_shortcuts_refuted": all(
            row["differs_on_counterexample"] for row in rivals.values()
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=991)
    parser.add_argument("--sample-index", type=int, default=1)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    report = build_report(seed=args.seed, sample_index=args.sample_index)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if (
        report["all_declared_shortcuts_fit_canonical"]
        and report["all_declared_shortcuts_refuted"]
        and not report["self_check"]
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
