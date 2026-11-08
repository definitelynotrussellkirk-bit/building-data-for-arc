#!/usr/bin/env python3
"""Reproduce the fixed-shape shortcut in generator 33fcd12e6b89."""
from __future__ import annotations

from collections import deque
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

PACKET = Path(__file__).resolve().parents[3]
REPO = PACKET / "repo"
sys.path[:0] = [str(REPO / "src"), str(REPO / "shared/runtime")]
from reviewer_support import canonical_pairs

TASK = "33fcd12e6b89"
GENERATOR = REPO / "generators" / TASK / "generator.py"
INPUT = Path(__file__).with_name("input.json")
RACKET = Path(__file__).with_name("racket.json")
RIVAL = Path(__file__).with_name("rival.json")
OUT = Path(__file__).with_name("probe.json")

spec = importlib.util.spec_from_file_location("audit_33f_generator", GENERATOR)
assert spec and spec.loader
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

ALLOWED_NORMALIZED_SHAPES = {frozenset(shape) for shape in gen._SHAPES}


def cells(grid, predicate):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if predicate(value)]


def normalized_object_shape(grid):
    points = cells(grid, lambda value: value not in (0, 3, 4))
    r0 = min(r for r, _ in points)
    c0 = min(c for _, c in points)
    return frozenset((r - r0, c - c0) for r, c in points)


def connected(points):
    remaining = set(points)
    if not remaining:
        return False
    seen = {next(iter(remaining))}
    todo = deque(seen)
    while todo:
        r, c = todo.popleft()
        for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if point in remaining and point not in seen:
                seen.add(point)
                todo.append(point)
    return seen == remaining


def canonical_translation(grid):
    h, w = len(grid), len(grid[0])
    src = cells(grid, lambda value: value == 3)[0]
    dst = cells(grid, lambda value: value == 4)[0]
    dr, dc = dst[0] - src[0], dst[1] - src[1]
    out = [[0] * w for _ in range(h)]
    out[src[0]][src[1]] = 3
    out[dst[0]][dst[1]] = 4
    for r, c in cells(grid, lambda value: value not in (0, 3, 4)):
        rr, cc = r + dr, c + dc
        if 0 <= rr < h and 0 <= cc < w:
            out[rr][cc] = grid[r][c]
    return out


def fixed_shape_rival(grid):
    """Translate only the three normalized shapes hard-coded by the sampler."""
    if normalized_object_shape(grid) not in ALLOWED_NORMALIZED_SHAPES:
        return [list(row) for row in grid]
    return canonical_translation(grid)


def documented_domain_status(grid):
    h, w = len(grid), len(grid[0])
    markers3 = cells(grid, lambda value: value == 3)
    markers4 = cells(grid, lambda value: value == 4)
    obj = cells(grid, lambda value: value not in (0, 3, 4))
    src, dst = markers3[0], markers4[0]
    dr, dc = dst[0] - src[0], dst[1] - src[1]
    moved = {(r + dr, c + dc) for r, c in obj}
    return {
        "grid_within_advertised_axis_bounds": 5 <= h <= 14 and 5 <= w <= 14,
        "exactly_one_color_3": len(markers3) == 1,
        "exactly_one_color_4": len(markers4) == 1,
        "nonempty_connected_object": bool(obj) and connected(obj),
        "translated_object_in_bounds": all(0 <= r < h and 0 <= c < w for r, c in moved),
        "translated_object_avoids_markers": not (moved & {src, dst}),
    }


def main():
    grid = json.loads(INPUT.read_text())["input"]
    racket = json.loads(RACKET.read_text())
    actual = racket["results"][0]["output"]
    rival = fixed_shape_rival(grid)
    RIVAL.write_text(json.dumps({"output": rival}, indent=2) + "\n")

    canonical = canonical_pairs(TASK, root=REPO)
    demos = [pair for pair in canonical if pair["split"] == "train"]
    generated = []
    for difficulty in (None, "easy", "medium", "hard"):
        for index in range(150):
            sample = gen.generate(900_000 + index, index * 19 + 7, difficulty=difficulty)
            generated.append(
                {
                    "difficulty": difficulty,
                    "index": index,
                    "self_check": gen.self_check(sample),
                    "shape": sorted(map(list, normalized_object_shape(sample))),
                    "rival_matches_canonical_translation": fixed_shape_rival(sample) == canonical_translation(sample),
                }
            )

    domain = documented_domain_status(grid)
    report = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": TASK,
        "finding": "fixed-shape sampler shortcut",
        "generator_path": str(GENERATOR.relative_to(PACKET)),
        "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
        "rule_hash": racket["executed_rule_hash"],
        "input_path": str(INPUT.relative_to(PACKET)),
        "racket_output_path": str(RACKET.relative_to(PACKET)),
        "rival_output_path": str(RIVAL.relative_to(PACKET)),
        "racket_command": racket["command"],
        "racket_cwd": "repo",
        "racket_exit_code": 0,
        "counterexample": {
            "input": grid,
            "normalized_object_shape": sorted(map(list, normalized_object_shape(grid))),
            "allowed_sampler_shapes": [sorted(map(list, shape)) for shape in sorted(ALLOWED_NORMALIZED_SHAPES, key=lambda s: sorted(s))],
            "generator_self_check": gen.self_check(grid),
            "documented_domain_status": domain,
            "documented_domain_member": all(domain.values()),
            "actual_racket_output": actual,
            "rival_output": rival,
            "outputs_disagree": actual != rival,
        },
        "shortcut_fit": {
            "canonical_training_pairs": len(demos),
            "canonical_training_fits": [fixed_shape_rival(pair["input"]) == pair["output"] for pair in demos],
            "fits_all_canonical_training_pairs": all(fixed_shape_rival(pair["input"]) == pair["output"] for pair in demos),
            "generated_samples_checked": len(generated),
            "generated_self_check_failures": sum(bool(row["self_check"]) for row in generated),
            "generated_rival_mismatches": sum(not row["rival_matches_canonical_translation"] for row in generated),
            "counterexample_shape_emitted": any(
                frozenset(map(tuple, row["shape"])) == normalized_object_shape(grid) for row in generated
            ),
            "sampler_shape_support": sorted({tuple(map(tuple, row["shape"])) for row in generated}),
        },
        "interpretation": (
            "A solver can memorize the three normalized object templates and apply the correct vector rule only to those templates. "
            "That rival fits both canonical demonstrations and every sampled input checked, but rejects a lawful 2x2 connected object."
        ),
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "self_check": report["counterexample"]["generator_self_check"],
        "documented_domain_member": report["counterexample"]["documented_domain_member"],
        "outputs_disagree": report["counterexample"]["outputs_disagree"],
        "canonical_training_fits": report["shortcut_fit"]["canonical_training_fits"],
        "generated_samples_checked": report["shortcut_fit"]["generated_samples_checked"],
        "generated_rival_mismatches": report["shortcut_fit"]["generated_rival_mismatches"],
        "counterexample_shape_emitted": report["shortcut_fit"]["counterexample_shape_emitted"],
        "out": str(OUT.relative_to(PACKET)),
    }, sort_keys=True))
    return int(
        bool(report["counterexample"]["generator_self_check"])
        or not report["counterexample"]["documented_domain_member"]
        or not report["counterexample"]["outputs_disagree"]
        or not report["shortcut_fit"]["fits_all_canonical_training_pairs"]
        or report["shortcut_fit"]["generated_rival_mismatches"] != 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
