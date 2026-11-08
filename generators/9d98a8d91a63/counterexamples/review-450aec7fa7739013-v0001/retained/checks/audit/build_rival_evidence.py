#!/usr/bin/env python3
"""Build reproducible adversarial-audit rival evidence for this review packet.

This script intentionally uses only public canonical training pairs, the audited
source generators, and the retained `arcpuzzles apply` results.  It does not call
private runner functions.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import deque
from pathlib import Path
from typing import Callable, Iterable

PACKET = Path(__file__).resolve().parents[2]
REPO = PACKET / "repo"
AUDIT = PACKET / "checks" / "audit"
TASKS = ("424c822d69f3", "9d98a8d91a63")
BANDS = (None, "easy", "medium", "hard")

Grid = list[list[int]]
Cell = tuple[int, int]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_generator_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical(task_id: str) -> dict:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open() as fh:
        for line in fh:
            record = json.loads(line)
            if record.get("task_id") == task_id:
                return record
    raise KeyError(task_id)


def components(grid: Grid, *, accept: Callable[[int], bool]) -> list[tuple[int, list[Cell]]]:
    h, w = len(grid), len(grid[0])
    seen: set[Cell] = set()
    out: list[tuple[int, list[Cell]]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if (r, c) in seen or not accept(color):
                continue
            seen.add((r, c))
            q = deque([(r, c)])
            cells: list[Cell] = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            out.append((color, cells))
    return out


def marker_recolor(grid: Grid, *, tie: str) -> Grid:
    markers = [(c, value) for c, value in enumerate(grid[0]) if value not in (0, 5)]
    out = [row[:] for row in grid]
    for _color, cells in components(grid, accept=lambda value: value == 5):
        cols = [c for _r, c in cells]
        center2 = min(cols) + max(cols)  # twice the bbox-center column
        if tie == "left":
            marker_col, marker_color = min(markers, key=lambda item: (abs(2 * item[0] - center2), item[0]))
        elif tie == "right":
            marker_col, marker_color = min(markers, key=lambda item: (abs(2 * item[0] - center2), -item[0]))
        else:
            raise ValueError(tie)
        del marker_col
        for r, c in cells:
            out[r][c] = marker_color
    return out


def border_touch_recolor(grid: Grid, *, target_only_7: bool) -> Grid:
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    for color, cells in components(grid, accept=lambda value: value != 0):
        touches = sum(
            (
                any(r == 0 for r, _c in cells),
                any(r == h - 1 for r, _c in cells),
                any(c == 0 for _r, c in cells),
                any(c == w - 1 for _r, c in cells),
            )
        )
        if touches == 2 and (color == 7 or not target_only_7):
            for r, c in cells:
                out[r][c] = 6
    return out


def diff_cells(a: Grid, b: Grid) -> list[dict]:
    return [
        {"row": r, "col": c, "actual": a[r][c], "rival": b[r][c]}
        for r in range(len(a))
        for c in range(len(a[0]))
        if a[r][c] != b[r][c]
    ]


def tie_objects(grid: Grid) -> list[dict]:
    markers = [(c, value) for c, value in enumerate(grid[0]) if value not in (0, 5)]
    ties = []
    for _color, cells in components(grid, accept=lambda value: value == 5):
        cols = [c for _r, c in cells]
        c1, c2 = min(cols), max(cols)
        center2 = c1 + c2
        distances = [(abs(2 * c - center2), c, color) for c, color in markers]
        best = min(d for d, _c, _color in distances)
        winners = [(c, color) for d, c, color in distances if d == best]
        if len(winners) > 1 and len({color for _c, color in winners}) > 1:
            rows = [r for r, _c in cells]
            ties.append(
                {
                    "bbox": [min(rows), c1, max(rows), c2],
                    "center_column": center2 / 2,
                    "equidistant_markers": [
                        {"col": c, "color": color} for c, color in winners
                    ],
                }
            )
    return ties


def write(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=False) + "\n")


def main() -> None:
    generators = {task: load_generator(task) for task in TASKS}
    records = {task: canonical(task) for task in TASKS}

    # Audit 424: left-vs-right tie policy.
    task = "424c822d69f3"
    canonical_checks = []
    for i, pair in enumerate(records[task]["train"]):
        left = marker_recolor(pair["input"], tie="left")
        right = marker_recolor(pair["input"], tie="right")
        canonical_checks.append(
            {
                "pair_index": i,
                "intended_matches": left == pair["output"],
                "rival_matches": right == pair["output"],
                "different_color_tie_count": len(tie_objects(pair["input"])),
            }
        )
    assert all(x["intended_matches"] and x["rival_matches"] for x in canonical_checks)

    input_424 = json.loads((AUDIT / task / "input.json").read_text())
    apply_424 = json.loads((AUDIT / task / "racket.json").read_text())
    actual_424 = apply_424["results"][0]["output"]
    intended_424 = marker_recolor(input_424, tie="left")
    rival_424 = marker_recolor(input_424, tie="right")
    assert actual_424 == intended_424
    assert actual_424 != rival_424
    write(
        AUDIT / task / "rival.json",
        {
            "schema": "arcpuzzles-audit-rival-v1",
            "task_id": task,
            "rival_name": "bbox-center nearest marker; exact ties choose the right marker",
            "fits_canonical_training_pairs": sum(x["rival_matches"] for x in canonical_checks),
            "canonical_training_pair_count": len(canonical_checks),
            "output": rival_424,
        },
    )
    sample_424 = []
    for band in BANDS:
        generated = valid = tie_samples = tie_object_count = 0
        for sample_index in range(100):
            grid = generators[task].generate(0, sample_index, difficulty=band)
            generated += 1
            if not generators[task].self_check(grid, difficulty=band, meta=None):
                valid += 1
            ties = tie_objects(grid)
            if ties:
                tie_samples += 1
                tie_object_count += len(ties)
        sample_424.append(
            {
                "difficulty": band,
                "seed": 0,
                "sample_index_range": [0, 99],
                "generated": generated,
                "self_check_passed": valid,
                "samples_with_different_color_exact_tie": tie_samples,
                "different_color_tie_objects": tie_object_count,
            }
        )
    write(AUDIT / task / "canonical-rival-check.json", {"task_id": task, "checks": canonical_checks})
    write(AUDIT / task / "sampling.json", {"task_id": task, "bands": sample_424})
    write(
        AUDIT / task / "counterexample.json",
        {
            "schema": "arcpuzzles-audit-counterexample-v1",
            "task_id": task,
            "classification": "reproduced teaching ambiguity",
            "generator_sha256": sha256(REPO / "generators" / task / "generator.py"),
            "rule_hash": apply_424["executed_rule_hash"],
            "rule_text_sha256": apply_424["rule_text_sha256"],
            "generation": {"seed": 0, "sample_index": 0, "difficulty": None, "overrides": {}},
            "validator_messages": generators[task].self_check(input_424, difficulty=None, meta=None),
            "belongs_to_documented_generator_domain": True,
            "tie_objects": tie_objects(input_424),
            "input": input_424,
            "actual_racket_output": actual_424,
            "rival": "bbox-center nearest marker; exact ties choose the right marker",
            "rival_output": rival_424,
            "differing_cells": diff_cells(actual_424, rival_424),
            "canonical_fit": {
                "rival_matches": sum(x["rival_matches"] for x in canonical_checks),
                "pair_count": len(canonical_checks),
            },
            "apply_command": apply_424["command"],
            "apply_cwd": apply_424["cwd"],
        },
    )

    # Audit 9d: target-color-specific vs color-agnostic border rule.
    task = "9d98a8d91a63"
    canonical_checks = []
    for i, pair in enumerate(records[task]["train"]):
        intended = border_touch_recolor(pair["input"], target_only_7=True)
        rival = border_touch_recolor(pair["input"], target_only_7=False)
        canonical_checks.append(
            {
                "pair_index": i,
                "intended_matches": intended == pair["output"],
                "rival_matches": rival == pair["output"],
            }
        )
    assert all(x["intended_matches"] and x["rival_matches"] for x in canonical_checks)

    input_9d = json.loads((AUDIT / task / "input.json").read_text())
    apply_9d = json.loads((AUDIT / task / "racket.json").read_text())
    actual_9d = apply_9d["results"][0]["output"]
    intended_9d = border_touch_recolor(input_9d, target_only_7=True)
    rival_9d = border_touch_recolor(input_9d, target_only_7=False)
    assert actual_9d == intended_9d
    assert actual_9d != rival_9d
    write(
        AUDIT / task / "rival.json",
        {
            "schema": "arcpuzzles-audit-rival-v1",
            "task_id": task,
            "rival_name": "recolor every nonbackground component touching exactly two borders, regardless of color",
            "fits_canonical_training_pairs": sum(x["rival_matches"] for x in canonical_checks),
            "canonical_training_pair_count": len(canonical_checks),
            "output": rival_9d,
        },
    )
    sample_9d = []
    for band in BANDS:
        generated = valid = only_0_7 = 0
        for sample_index in range(100):
            grid = generators[task].generate(0, sample_index, difficulty=band)
            generated += 1
            if not generators[task].self_check(grid, difficulty=band, meta=None):
                valid += 1
            if {value for row in grid for value in row} <= {0, 7}:
                only_0_7 += 1
        sample_9d.append(
            {
                "difficulty": band,
                "seed": 0,
                "sample_index_range": [0, 99],
                "generated": generated,
                "self_check_passed": valid,
                "samples_using_only_colors_0_and_7": only_0_7,
            }
        )
    write(AUDIT / task / "canonical-rival-check.json", {"task_id": task, "checks": canonical_checks})
    write(AUDIT / task / "sampling.json", {"task_id": task, "bands": sample_9d})
    write(
        AUDIT / task / "counterexample.json",
        {
            "schema": "arcpuzzles-audit-counterexample-v1",
            "task_id": task,
            "classification": "reproduced generator-domain omission / plausible color-role shortcut",
            "generator_sha256": sha256(REPO / "generators" / task / "generator.py"),
            "rule_hash": apply_9d["executed_rule_hash"],
            "rule_text_sha256": apply_9d["rule_text_sha256"],
            "generation": None,
            "validator_messages": generators[task].self_check(input_9d, difficulty=None, meta=None),
            "belongs_to_documented_generator_domain": False,
            "belongs_to_canonical_task_domain": True,
            "domain_basis": "canonical demonstrations contain non-7 distractor objects; this counterfactual moves such a distractor onto exactly two borders",
            "input": input_9d,
            "actual_racket_output": actual_9d,
            "rival": "recolor every nonbackground component touching exactly two borders, regardless of color",
            "rival_output": rival_9d,
            "differing_cells": diff_cells(actual_9d, rival_9d),
            "canonical_fit": {
                "rival_matches": sum(x["rival_matches"] for x in canonical_checks),
                "pair_count": len(canonical_checks),
            },
            "apply_command": apply_9d["command"],
            "apply_cwd": apply_9d["cwd"],
        },
    )

    print("wrote audit evidence for", ", ".join(TASKS))


if __name__ == "__main__":
    main()
