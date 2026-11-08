#!/usr/bin/env python3
"""Reproduce the color-blind connectivity shortcut on the current source."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "f4a1fcdd1c8b"
BANDS = ("easy", None, "medium", "hard")
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def color_blind_rival(grid):
    """Keep a nonzero 4-connected blob if any cell of the blob touches the frame."""
    h, w = len(grid), len(grid[0])
    out = [[0 for _ in row] for row in grid]
    seen = set()
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] == 0 or (r0, c0) in seen:
                continue
            cells = {(r0, c0)}
            seen.add((r0, c0))
            stack = [(r0, c0)]
            while stack:
                r, c = stack.pop()
                for dr, dc in CARDINAL:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h and 0 <= nc < w
                        and grid[nr][nc] != 0 and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        cells.add((nr, nc))
                        stack.append((nr, nc))
            if any(r in (0, h - 1) or c in (0, w - 1) for r, c in cells):
                for r, c in cells:
                    out[r][c] = grid[r][c]
    return out


def has_different_color_cardinal_touch(grid):
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if not value:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    other = grid[nr][nc]
                    if other and other != value:
                        return True
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"output already exists: {args.out}")

    root = find_root(__file__)
    generator, source, source_sha = load_selected_generator(TASK_ID, root=root)
    band_records = {}
    mismatches = []
    total = 0
    for band in BANDS:
        touch_count = 0
        rival_difference_count = 0
        accepted = 0
        for sample_index in range(200):
            grid = generator.generate(10007, sample_index, difficulty=band)
            errors = generator.self_check(grid, difficulty=band)
            if errors:
                raise AssertionError((band, sample_index, errors))
            accepted += 1
            total += 1
            touch_count += int(has_different_color_cardinal_touch(grid))
            intended = generator.rule_mirror(grid)
            rival = color_blind_rival(grid)
            if intended != rival:
                rival_difference_count += 1
                if len(mismatches) < 4:
                    mismatches.append({
                        "difficulty": band,
                        "sample_index": sample_index,
                        "input": grid,
                        "intended": intended,
                        "rival": rival,
                    })
        band_records["default" if band is None else band] = {
            "draw_count": accepted,
            "different_color_cardinal_touch_count": touch_count,
            "rival_difference_count": rival_difference_count,
        }

    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    train0 = next(p for p in canonical if p["split"] == "train" and p["pair_index"] == 0)
    canonical_intended = generator.rule_mirror(train0["input"])
    canonical_rival = color_blind_rival(train0["input"])
    if canonical_intended != train0["output"]:
        raise AssertionError("selected mirror does not match canonical train[0]")

    report = {
        "schema": "f4a1fcdd1c8b-color-blind-connectivity-audit-v1",
        "task_id": TASK_ID,
        "generator_path": source.relative_to(root).as_posix(),
        "generator_sha256": source_sha,
        "rival": {
            "name": "color_blind_nonzero_connectivity",
            "description": "Merge cardinally touching nonzero cells even when their colors differ; keep the whole merged blob if any cell touches the frame.",
        },
        "default_draw_census": {
            "seed": 10007,
            "sample_indices": [0, 199],
            "total_draws": total,
            "bands": band_records,
            "total_different_color_cardinal_touch_count": sum(v["different_color_cardinal_touch_count"] for v in band_records.values()),
            "total_rival_difference_count": sum(v["rival_difference_count"] for v in band_records.values()),
            "first_mismatches": mismatches,
        },
        "canonical_witness": {
            "split": "train",
            "pair_index": 0,
            "input": train0["input"],
            "intended": canonical_intended,
            "rival": canonical_rival,
            "disagrees": canonical_intended != canonical_rival,
            "specific_cells": {
                "input_6_5": train0["input"][6][5],
                "input_7_5": train0["input"][7][5],
                "intended_6_5": canonical_intended[6][5],
                "intended_7_5": canonical_intended[7][5],
                "rival_6_5": canonical_rival[6][5],
                "rival_7_5": canonical_rival[7][5],
            },
        },
        "status": "reproduced" if canonical_intended != canonical_rival and not mismatches else "unexpected",
        "limitations": [
            "The 800-draw census is finite and uses one pinned seed over 200 sample indices per band.",
            "The retained Racket apply receipt verifies the canonical witness output; generated parity uses the selected task mirror.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "total_draws": total,
        "touches": report["default_draw_census"]["total_different_color_cardinal_touch_count"],
        "rival_differences": report["default_draw_census"]["total_rival_difference_count"],
        "out": str(args.out),
    }))
    return int(report["status"] != "reproduced")


if __name__ == "__main__":
    raise SystemExit(main())
