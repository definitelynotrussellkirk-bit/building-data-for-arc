#!/usr/bin/env python3
"""Find a lesson where ignoring the diagonal filter survives demos but fails query."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "f06b9f1a5114"


def _groups(grid):
    result = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                result.setdefault(value, []).append((r, c))
    return result


def _paint_bbox_border(out, cells, color):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if r in (r0, r1) or c in (c0, c1):
                out[r][c] = color


def intended(grid):
    out = [list(row) for row in grid]
    for color, cells in sorted(_groups(grid).items()):
        if len(cells) == 2 and cells[0][0] != cells[1][0] and cells[0][1] != cells[1][1]:
            _paint_bbox_border(out, cells, color)
    return out


def rival(grid):
    """Wrong rule: any same-color pair defines its bbox, even if collinear."""
    out = [list(row) for row in grid]
    for color, cells in sorted(_groups(grid).items()):
        if len(cells) == 2:
            _paint_bbox_border(out, cells, color)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"output already exists: {args.out}")

    root = find_root(__file__)
    generator, source, source_sha = load_selected_generator(TASK_ID, root=root)
    canonical = canonical_pairs(TASK_ID, root=root)
    canonical_train = [pair for pair in canonical if pair.get("split") == "train"]
    canonical_fit = [rival(pair["input"]) == pair["output"] for pair in canonical_train]
    intended_fit = [intended(pair["input"]) == pair["output"] for pair in canonical]
    if not all(canonical_fit) or not all(intended_fit):
        raise AssertionError("probe mirrors do not fit the canonical evidence")

    found = None
    bands = ("easy", None, "medium", "hard")
    checked_windows = 0
    for band in bands:
        for seed in range(64):
            cache = []
            for index in range(35):
                grid = generator.generate(seed, index, difficulty=band)
                errors = generator.self_check(grid, difficulty=band)
                if errors:
                    raise AssertionError((band, seed, index, errors))
                cache.append({"input": grid, "intended": intended(grid), "rival": rival(grid)})
            for start in range(32):
                checked_windows += 1
                window = cache[start:start + 4]
                if all(pair["rival"] == pair["intended"] for pair in window[:3]) and window[3]["rival"] != window[3]["intended"]:
                    found = {
                        "difficulty": band,
                        "seed": seed,
                        "start": start,
                        "sample_indices": list(range(start, start + 4)),
                        "demonstration_count": 3,
                        "query_position": 3,
                        "pairs": window,
                    }
                    break
            if found:
                break
        if found:
            break

    report = {
        "schema": "f06b9f1a5114-collinear-filter-shortcut-v1",
        "task_id": TASK_ID,
        "status": "found" if found else "not_found",
        "generator_path": source.relative_to(root).as_posix(),
        "generator_sha256": source_sha,
        "rival": {
            "name": "paint_bbox_for_every_same_color_pair",
            "description": "Paint a bounding-box border for every color with exactly two cells, omitting the intended different-row AND different-column condition.",
            "fits_all_canonical_demonstrations": all(canonical_fit),
            "canonical_training_fit": canonical_fit,
        },
        "intended_mirror_matches_all_canonical_pairs": all(intended_fit),
        "search": {
            "bands": ["easy", "default", "medium", "hard"],
            "seeds": [0, 63],
            "starts_per_seed": 32,
            "checked_windows_before_stop": checked_windows,
            "production_order": "three consecutive demonstrations followed by fourth-pair query",
        },
        "witness": found,
        "limitations": [
            "Finite search over the declared generator, not a universal frequency estimate.",
            "Python mirrors are diagnostic; the retained Racket apply receipt verifies the four witness labels.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "checked_windows": checked_windows, "out": str(args.out)}))
    return 0 if found else 1


if __name__ == "__main__":
    raise SystemExit(main())
