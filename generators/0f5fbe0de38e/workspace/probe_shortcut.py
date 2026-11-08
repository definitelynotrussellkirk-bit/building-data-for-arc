#!/usr/bin/env python3
"""Build source-bound evidence for the canonical-demo first-two-pairs rival."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "0f5fbe0de38e"
DEFAULT_RELATIVE_OUT = Path(
    "generators/0f5fbe0de38e/counterexamples/current-shortcut/checks/question-shortcut"
)
DEFAULT_OVERRIDES: dict[str, Any] = {
    "grid_h": 22,
    "grid_w": 22,
    "bg_color": 0,
    "fill_color": 8,
    "marker_a_color": 2,
    "marker_b_color": 6,
    "template_profile": "cross4_anti",
    "lesson_profile": "mixed_1_2_3",
    "orientation_profile": "mixed",
}


def _grid_hash(grid: list[list[int]]) -> str:
    body = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(body).hexdigest()


def _diff_cells(expected: list[list[int]], rival: list[list[int]]) -> list[dict[str, int]]:
    return [
        {"row": r, "column": c, "intended": expected[r][c], "rival": rival[r][c]}
        for r in range(len(expected))
        for c in range(len(expected[0]))
        if expected[r][c] != rival[r][c]
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_RELATIVE_OUT)
    parser.add_argument("--seed", type=int, default=4242)
    parser.add_argument("--sample-index", type=int, default=5)
    parser.add_argument("--difficulty", default="hard")
    parser.add_argument("--racket-json", type=Path)
    args = parser.parse_args()

    root = find_root(__file__)
    gen, source_path, generator_sha = load_selected_generator(TASK_ID, root=root)
    out_dir = args.out_dir if args.out_dir.is_absolute() else root / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    demos = [pair for pair in pairs if pair["split"] == "train"]
    queries = [pair for pair in pairs if pair["split"] == "test"]
    rival_fn = gen.LESSON_COMPETITORS["first_two_pairs_only"]
    demo_matches = [rival_fn(pair["input"]) == pair["output"] for pair in demos]
    query_matches = [rival_fn(pair["input"]) == pair["output"] for pair in queries]

    grid = gen.generate(
        args.seed,
        args.sample_index,
        difficulty=args.difficulty,
        **DEFAULT_OVERRIDES,
    )
    intended = gen._predict(grid, "canonical")
    rival = rival_fn(grid)
    differing = _diff_cells(intended, rival)
    self_errors = gen.self_check(grid)
    strict_errors = gen.strict_canonical_like(grid)
    observed = gen.observe_overrides(grid)

    if not all(demo_matches):
        raise SystemExit("first_two_pairs_only no longer fits every canonical training demo")
    if not queries or all(query_matches):
        raise SystemExit("first_two_pairs_only no longer disagrees with a canonical query")
    if self_errors or strict_errors:
        raise SystemExit(f"generated witness is outside the task domain: {self_errors or strict_errors}")
    if observed != DEFAULT_OVERRIDES:
        raise SystemExit(f"override mismatch: requested={DEFAULT_OVERRIDES}, observed={observed}")
    if not differing:
        raise SystemExit("generated witness does not distinguish the rival")

    input_path = out_dir / "input.json"
    input_path.write_text(json.dumps(grid, indent=2) + "\n")

    evidence: dict[str, Any] = {
        "schema": "arcpuzzles-generator-shortcut-counterexample-v1",
        "task_id": TASK_ID,
        "generator_source": str(source_path.relative_to(root)),
        "generator_sha256": generator_sha,
        "declared_rule_hash": gen.RULE_HASH,
        "rival": {
            "name": "first_two_pairs_only",
            "description": (
                "Apply the intended scaled-template fill to only the first two "
                "greedy-nearest marker pairs and ignore later pairs."
            ),
        },
        "canonical_demo_fit": {
            "train_pairs": len(demos),
            "train_matches": sum(demo_matches),
            "fits_all_train": all(demo_matches),
            "test_pairs": len(queries),
            "test_matches": sum(query_matches),
            "disagrees_with_test": any(not value for value in query_matches),
        },
        "seed": args.seed,
        "sample_index": args.sample_index,
        "difficulty": args.difficulty,
        "overrides": DEFAULT_OVERRIDES,
        "observed_overrides": observed,
        "self_check_errors": self_errors,
        "strict_canonical_like_errors": strict_errors,
        "input": grid,
        "input_sha256": _grid_hash(grid),
        "reference_mirror_output": intended,
        "reference_mirror_output_sha256": _grid_hash(intended),
        "rival_output": rival,
        "rival_output_sha256": _grid_hash(rival),
        "differing_cells": differing,
        "differing_cell_count": len(differing),
    }

    racket_path = args.racket_json
    if racket_path is None:
        candidate = out_dir / "racket.json"
        racket_path = candidate if candidate.is_file() else None
    elif not racket_path.is_absolute():
        racket_path = root / racket_path
    if racket_path is not None:
        racket = json.loads(racket_path.read_text())
        results = racket.get("results") or []
        if len(results) != 1 or results[0].get("error") is not None:
            raise SystemExit(f"invalid Racket apply record: {racket_path}")
        racket_output = results[0]["output"]
        if racket_output != intended:
            raise SystemExit("task-linked Python mirror disagrees with live Racket output")
        evidence["racket_apply"] = {
            "path": str(racket_path.relative_to(root)),
            "executed_rule_hash": racket.get("executed_rule_hash"),
            "generator_sha256": racket.get("generator_sha256"),
            "rule_text_sha256": racket.get("rule_text_sha256"),
            "input_sha256": results[0].get("input_sha256"),
            "output_sha256": results[0].get("output_sha256"),
            "output": racket_output,
            "command": racket.get("command"),
            "cwd": racket.get("cwd"),
        }
        if racket.get("generator_sha256") != generator_sha:
            raise SystemExit("Racket apply used different generator bytes")

    (out_dir / "counterexample.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({
        "generator_sha256": generator_sha,
        "input": str(input_path.relative_to(root)),
        "counterexample": str((out_dir / "counterexample.json").relative_to(root)),
        "racket_bound": "racket_apply" in evidence,
        "differing_cell_count": len(differing),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
