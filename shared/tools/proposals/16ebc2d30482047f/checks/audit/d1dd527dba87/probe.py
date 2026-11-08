#!/usr/bin/env python3
"""Retain a generated lesson ambiguous with a bottommost-object shortcut."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Iterable

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "d1dd527dba87"


def bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def normalize(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = tuple(cells)
    r0, c0, _, _ = bbox(cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def render(mask: Iterable[tuple[int, int]]) -> list[list[int]]:
    mask = frozenset(mask)
    if not mask:
        return [[0]]
    r0, c0, r1, c1 = bbox(mask)
    out = [[0 for _ in range(c1 - c0 + 1)] for _ in range(r1 - r0 + 1)]
    for r, c in mask:
        out[r - r0][c - c0] = 8
    return out


def bottommost_rival(gen, grid: list[list[int]]) -> list[list[int]]:
    """Choose each color's component with the lexicographically greatest bbox."""
    selected = []
    for color in (1, 2):
        components = gen._components(grid, color)
        if not components:
            return [[0]]
        selected.append(max(components, key=bbox))
    return render(normalize(selected[0]) ^ normalize(selected[1]))


def lesson(gen, seed: int, start: int, difficulty: str):
    inputs = [gen.generate(seed, start + offset, difficulty=difficulty) for offset in range(4)]
    intended = [gen._truth_xor(grid) for grid in inputs]
    rival = [bottommost_rival(gen, grid) for grid in inputs]
    return inputs, intended, rival


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=100000)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    parser.add_argument("--survey-seeds", type=int, default=100)
    parser.add_argument("--survey-starts", type=int, default=12)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    root = find_root(__file__)
    gen, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    inputs, intended, rival = lesson(gen, args.seed, args.start, args.difficulty)
    demo_matches = [rival[index] == intended[index] for index in range(3)]
    query_differs = rival[3] != intended[3]
    self_checks = [gen.self_check(grid, difficulty=args.difficulty) for grid in inputs]
    if demo_matches != [True, True, True] or not query_differs or any(self_checks):
        raise RuntimeError({
            "demo_matches": demo_matches,
            "query_differs": query_differs,
            "self_checks": self_checks,
        })

    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    canonical_matches = [bottommost_rival(gen, pair["input"]) == pair["output"] for pair in canonical]

    ambiguous_windows = 0
    windows = 0
    first_five = []
    for seed_offset in range(args.survey_seeds):
        survey_seed = args.seed + seed_offset
        for start in range(args.survey_starts):
            windows += 1
            _, truth_rows, rival_rows = lesson(gen, survey_seed, start, args.difficulty)
            ambiguous = rival_rows[:3] == truth_rows[:3] and rival_rows[3] != truth_rows[3]
            if ambiguous:
                ambiguous_windows += 1
                if len(first_five) < 5:
                    first_five.append({"seed": survey_seed, "start": start})

    observations = [gen.observe_overrides(grid) for grid in inputs]
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "inputs.json").write_text(json.dumps({"inputs": inputs}, indent=2) + "\n")
    (out_dir / "intended_outputs.json").write_text(json.dumps(intended, indent=2) + "\n")
    (out_dir / "rival_outputs.json").write_text(json.dumps(rival, indent=2) + "\n")
    (out_dir / "lesson.json").write_text(json.dumps({
        "task_id": TASK_ID,
        "seed": args.seed,
        "start": args.start,
        "difficulty": args.difficulty,
        "demonstrations": [
            {"input": inputs[i], "output": intended[i], "rival_output": rival[i]}
            for i in range(3)
        ],
        "query": {"input": inputs[3], "output": intended[3], "rival_output": rival[3]},
    }, indent=2) + "\n")

    report = {
        "schema": "arcpuzzles-audit-bottommost-lesson-shortcut-v1",
        "task_id": TASK_ID,
        "generator_source": str(source_path.relative_to(root)),
        "generator_sha256": source_sha256,
        "rule_hash_declared": getattr(gen, "RULE_HASH", None),
        "cwd": os.getcwd(),
        "argv": sys.argv,
        "exact_lesson": {
            "seed": args.seed,
            "start_sample_index": args.start,
            "difficulty": args.difficulty,
            "demonstration_count": 3,
            "query_offset": 3,
            "input_path": "inputs.json",
            "lesson_path": "lesson.json",
            "intended_outputs_path": "intended_outputs.json",
            "rival_outputs_path": "rival_outputs.json",
            "self_check_errors": self_checks,
            "observed_overrides": observations,
            "rival_description": "for each of colors 1 and 2, select the component with the bottommost/rightmost bbox instead of the largest component; then normalize, XOR and crop",
            "rival_matches_demonstrations": demo_matches,
            "rival_differs_on_query": query_differs,
        },
        "canonical_fit": {
            "pairs_total": len(canonical_matches),
            "pairs_fit": sum(canonical_matches),
            "fits_all": all(canonical_matches),
        },
        "finite_survey": {
            "difficulty": args.difficulty,
            "seed_range": [args.seed, args.seed + args.survey_seeds - 1],
            "start_range": [0, args.survey_starts - 1],
            "windows": windows,
            "ambiguous_windows": ambiguous_windows,
            "first_five": first_five,
            "overlap_note": "adjacent windows overlap; this count is lesson windows, not unique inputs",
        },
        "finding": (
            "A production three-demo lesson leaves bottommost-object selection consistent with every visible demonstration, "
            "but the same rival disagrees with the canonical largest-object rule on the generated query."
        ),
        "limits": [
            "The rival is one plausible undeclared positional heuristic; the finite survey does not enumerate all rivals or seeds.",
            "The separate apply receipt binds all four retained generated inputs to the canonical Racket outputs.",
        ],
    }
    (out_dir / "probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "out": str(out_dir / "probe.json"),
        "generator_sha256": source_sha256,
        "canonical_fit": report["canonical_fit"],
        "demo_matches": demo_matches,
        "query_differs": query_differs,
        "survey": report["finite_survey"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
