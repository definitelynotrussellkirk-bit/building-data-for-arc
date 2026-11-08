"""Independent oracle, rival rules, and distribution probe for 7ce16af847d6.

This file deliberately does not import implementation helpers from generator.py.
It is useful to future reviewers as both a portable oracle and a lesson-schedule
census.  The canonical Racket program remains the label authority.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Iterable

TASK_ID = "7ce16af847d6"
ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs as _canonical_pairs, find_root  # noqa: E402


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK_ID}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_7ce16af847d6", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK_ID, root=find_root(__file__))


def components(grid, *, background=0):
    """Four-connected same-color components, matching the Racket object model."""
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != background}
    parts = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        color = grid[start[0]][start[1]]
        cells = {start}
        todo = [start]
        while todo:
            r, c = todo.pop()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in unseen and grid[nr][nc] == color:
                    unseen.remove((nr, nc))
                    cells.add((nr, nc))
                    todo.append((nr, nc))
        parts.append({"color": color, "cells": cells})
    return parts


def bounds(cells):
    return (
        min(r for r, _ in cells), min(c for _, c in cells),
        max(r for r, _ in cells), max(c for _, c in cells),
    )


def signature(part):
    r0, c0, r1, c1 = bounds(part["cells"])
    return part["color"], len(part["cells"]), r1 - r0 + 1, c1 - c0 + 1


def is_exact_blue_3x3(part):
    return signature(part) == (1, 9, 3, 3)


def contains_solid_blue_3x3(grid, part):
    if part["color"] != 1:
        return False
    cells = part["cells"]
    r0, c0, r1, c1 = bounds(cells)
    return any(
        {(r + dr, c + dc) for dr in range(3) for dc in range(3)} <= cells
        for r in range(r0, r1 - 1)
        for c in range(c0, c1 - 1)
    )


def _paint_parts(grid, predicate):
    out = deepcopy(grid)
    for part in components(grid):
        if predicate(grid, part):
            for r, c in part["cells"]:
                out[r][c] = 3
    return out


def intended_output(grid):
    return _paint_parts(grid, lambda _grid, part: is_exact_blue_3x3(part))


def rival_blue_size_nine(grid):
    return _paint_parts(
        grid, lambda _grid, part: part["color"] == 1 and len(part["cells"]) == 9
    )


def rival_blue_bbox_3x3(grid):
    def predicate(_grid, part):
        color, _size, h, w = signature(part)
        return color == 1 and (h, w) == (3, 3)
    return _paint_parts(grid, predicate)


def rival_contains_3x3(grid):
    return _paint_parts(grid, contains_solid_blue_3x3)


def rival_any_color_exact_3x3(grid):
    def predicate(_grid, part):
        color, size, h, w = signature(part)
        return color != 0 and (size, h, w) == (9, 3, 3)
    return _paint_parts(grid, predicate)


def rival_all_blue(grid):
    return _paint_parts(grid, lambda _grid, part: part["color"] == 1)


def facts(grid):
    parts = components(grid)
    sigs = [signature(part) for part in parts]
    blue = [part for part in parts if part["color"] == 1]
    nonblue = [part for part in parts if part["color"] != 1]
    exact = [part for part in blue if is_exact_blue_3x3(part)]
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "palette": sorted({value for row in grid for value in row}),
        "components": len(parts),
        "targets": len(exact),
        "blue_distractors": len(blue) - len(exact),
        "decorations": len(nonblue),
        "blue_hollow_3x3": any(
            color == 1 and size < 9 and (h, w) == (3, 3)
            for color, size, h, w in sigs
        ),
        "blue_nine_cell_non_square": any(
            color == 1 and size == 9 and (h, w) != (3, 3)
            for color, size, h, w in sigs
        ),
        "blue_contains_3x3_but_not_exact": any(
            contains_solid_blue_3x3(grid, part) and not is_exact_blue_3x3(part)
            for part in blue
        ),
        "nonblue_exact_3x3": any(
            color != 1 and (size, h, w) == (9, 3, 3)
            for color, size, h, w in sigs
        ),
    }


def profile_of(grid):
    info = facts(grid)
    if info["nonblue_exact_3x3"]:
        return "color_counterexample"
    if (
        info["blue_hollow_3x3"]
        and info["blue_nine_cell_non_square"]
        and info["blue_contains_3x3_but_not_exact"]
    ):
        return "shape_counterexamples"
    return "canonical_mix"


def canonical_profiles():
    return {
        (
            len(pair["input"]),
            len(pair["input"][0]),
            len({v for row in pair["input"] for v in row}),
        )
        for pair in canonical_pairs()
    }


def _pair(module, seed, sample_index, band):
    grid = module.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": intended_output(grid)}


def audit(module, count):
    canonical = canonical_pairs()
    canonical_profile_set = {
        (len(pair["input"]), len(pair["input"][0]),
         len({value for row in pair["input"] for value in row}))
        for pair in canonical
    }
    reports = {}
    for band in ("easy", "medium", "hard"):
        rows = []
        grids = []
        for index in range(count):
            grid = module.generate(17000, index, difficulty=band)
            grids.append(grid)
            rows.append(facts(grid) | {"profile": profile_of(grid)})
        bad_windows = []
        for seed in range(6):
            for start in range(9):
                demos = [_pair(module, seed, start + offset, band) for offset in range(3)]
                query = _pair(module, seed, start + 3, band)
                reasons = module.lesson_identifiable(demos, query)
                if reasons:
                    bad_windows.append({"seed": seed, "start": start, "reasons": reasons})
        reports[band] = {
            "samples": count,
            "distinct_inputs": len({json.dumps(g, separators=(",", ":")) for g in grids}),
            "self_check_failures": sum(bool(module.self_check(g)) for g in grids),
            "profiles": sorted({row["profile"] for row in rows}),
            "dimensions": sorted({(row["height"], row["width"]) for row in rows}),
            "component_counts": sorted({row["components"] for row in rows}),
            "target_counts": sorted({row["targets"] for row in rows}),
            "canonical_profile_hits": sum(
                (row["height"], row["width"], len(row["palette"])) in canonical_profile_set
                for row in rows
            ),
            "bad_three_demo_windows": bad_windows,
        }
    return {
        "schema": "7ce16af847d6-independent-audit-v1",
        "generator_version": getattr(module, "VERSION", None),
        "rule_hash": getattr(module, "RULE_HASH", None),
        "canonical_pairs": len(canonical),
        "canonical_oracle_matches": sum(
            intended_output(pair["input"]) == pair["output"] for pair in canonical
        ),
        "canonical_self_check_failures": [
            {"split": pair["split"], "pair_index": pair["pair_index"],
             "errors": module.self_check(pair["input"])}
            for pair in canonical if module.self_check(pair["input"])
        ],
        "bands": reports,
    }


def main(argv: Iterable[str] | None = None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=128)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report = audit(module, args.count)
    source = args.generator or ROOT / f"generators/{TASK_ID}/generator.py"
    report["generator_sha256"] = hashlib.sha256(Path(source).read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"canonical_self_check_failures": report["canonical_self_check_failures"],
                      "bands": report["bands"]}, indent=2))
    return int(
        bool(report["canonical_self_check_failures"])
        or any(value["self_check_failures"] or value["bad_three_demo_windows"]
               for value in report["bands"].values())
    )


if __name__ == "__main__":
    raise SystemExit(main())
