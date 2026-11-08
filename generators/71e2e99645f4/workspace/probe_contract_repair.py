#!/usr/bin/env python3
"""Reproduce the reviewed 71e2e99645f4 contract defects and repaired behavior.

This probe is intentionally independent of pytest so future reviewers can run it
against the retained pre-review source and the current generator in one command.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from itertools import combinations
from pathlib import Path
from typing import Any

TASK_DIR = Path(__file__).resolve().parents[1]
OLD_PATH = TASK_DIR / "workspace" / "generator-before-review.py"
NEW_PATH = TASK_DIR / "generator.py"

CANONICAL_EDGE = frozenset({(1, 0), (1, 3), (2, 0), (2, 3)})
FULL_EDGE_COLUMNS = frozenset((row, col) for row in range(4) for col in (0, 3))


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def section_holes(grid: list[list[int]], index: int) -> frozenset[tuple[int, int]]:
    start = index * 5
    return frozenset(
        (row, col)
        for row in range(4)
        for col in range(4)
        if grid[row][start + col] == 0
    )


def unknown_override_result(module: Any) -> str:
    try:
        module.generate(0, 0, typo_axis=3)
    except Exception as exc:  # exact type and message are part of the evidence
        return f"{type(exc).__name__}: {exc}"
    return "accepted"


def census(module: Any, n: int) -> dict[str, int]:
    counts = {
        "canonical_four_cell_edge_sections": 0,
        "full_eight_cell_edge_sections": 0,
        "other_sections": 0,
    }
    for index in range(n):
        grid = module.generate(10000 + index, index, difficulty=("easy", "medium", "hard")[index % 3])
        for section in range(3):
            holes = section_holes(grid, section)
            if holes == CANONICAL_EDGE:
                counts["canonical_four_cell_edge_sections"] += 1
            elif holes == FULL_EDGE_COLUMNS:
                counts["full_eight_cell_edge_sections"] += 1
            else:
                counts["other_sections"] += 1
    counts["draws"] = n
    counts["sections"] = 3 * n
    return counts


def rotation_probe(module: Any) -> dict[str, Any]:
    pairs = []
    for index in range(4):
        grid = module.generate(8123, index, difficulty="medium")
        pairs.append({"input": grid, "output": module.rule_mirror(grid)})
    failures = []
    for demo_indices in combinations(range(4), 3):
        query_index = next(i for i in range(4) if i not in demo_indices)
        reasons = module.lesson_identifiable(
            [pairs[i] for i in demo_indices], pairs[query_index]
        )
        if reasons:
            failures.append(
                {
                    "demo_indices": list(demo_indices),
                    "query_index": query_index,
                    "reasons": reasons,
                }
            )
    return {"rotations_checked": 4, "failures": failures}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draws", type=int, default=300)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.draws <= 0:
        raise SystemExit("--draws must be positive")

    old = load(OLD_PATH, "generator_before_71e2e99645f4")
    new = load(NEW_PATH, "generator_after_71e2e99645f4")
    request = {
        "seed": 9,
        "sample_index": 4,
        "fill_color": 6,
        "hole_patterns": ["edge_hole", "no_hole", "center_hole"],
    }
    old_grid = old.generate(
        request["seed"],
        request["sample_index"],
        fill_color=request["fill_color"],
        hole_patterns=request["hole_patterns"],
    )
    new_grid = new.generate(
        request["seed"],
        request["sample_index"],
        fill_color=request["fill_color"],
        hole_patterns=request["hole_patterns"],
    )

    payload = {
        "schema": "71e2e99645f4-contract-probe-v1",
        "request": request,
        "before": {
            "generator_sha256": __import__("hashlib").sha256(OLD_PATH.read_bytes()).hexdigest(),
            "first_section_holes": sorted(section_holes(old_grid, 0)),
            "unknown_override": unknown_override_result(old),
            "minimal_impostor_self_check": old.self_check([[1]], meta={"texture": "no_holes"}),
            "census": census(old, args.draws),
        },
        "after": {
            "generator_sha256": __import__("hashlib").sha256(NEW_PATH.read_bytes()).hexdigest(),
            "first_section_holes": sorted(section_holes(new_grid, 0)),
            "observed_overrides": new.observe_overrides(new_grid),
            "unknown_override": unknown_override_result(new),
            "minimal_impostor_self_check": new.self_check([[1]], meta={"texture": "no_holes"}),
            "census": census(new, args.draws),
            "rotation_probe": rotation_probe(new),
        },
    }
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")

    assert payload["before"]["unknown_override"] == "accepted"
    assert payload["before"]["minimal_impostor_self_check"] == []
    assert payload["before"]["census"]["canonical_four_cell_edge_sections"] == 0
    assert payload["after"]["first_section_holes"] == sorted(CANONICAL_EDGE)
    assert payload["after"]["observed_overrides"]["hole_patterns"] == request["hole_patterns"]
    assert payload["after"]["unknown_override"].startswith("ValueError:")
    assert payload["after"]["minimal_impostor_self_check"]
    assert payload["after"]["census"]["full_eight_cell_edge_sections"] == 0
    assert payload["after"]["rotation_probe"]["failures"] == []
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
