#!/usr/bin/env python3
"""Read-only audit reproducer for 03000b260ae0's public generator contract."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "03000b260ae0"


def _max_copy_overlap(gen, grid):
    comps = gen._self_nonzero_components_4(grid)
    templates = [
        cells
        for cells in comps
        if len(cells) > 1 and sum(grid[r][c] == 9 for r, c in cells) == 1
    ]
    markers = [
        cells[0]
        for cells in comps
        if len(cells) == 1 and grid[cells[0][0]][cells[0][1]] == 9
    ]
    if len(templates) != 1:
        return None
    template = templates[0]
    anchor = next((r, c) for r, c in template if grid[r][c] == 9)
    offsets = {(r - anchor[0], c - anchor[1]) for r, c in template}
    counts = {}
    for mr, mc in markers:
        for dr, dc in offsets:
            pos = (mr + dr, mc + dc)
            counts[pos] = counts.get(pos, 0) + 1
    return max(counts.values(), default=0)


def _attempt(gen, **overrides):
    try:
        grid = gen.generate(0, 0, difficulty="easy", **overrides)
    except Exception as exc:  # exact public failure is audit evidence
        return {
            "accepted": False,
            "exception": type(exc).__name__,
            "message": str(exc),
        }
    return {
        "accepted": True,
        "shape": [len(grid), len(grid[0])],
        "self_check": gen.self_check(grid),
        "max_copy_overlap": _max_copy_overlap(gen, grid),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    root = find_root(Path.cwd())
    gen, source, source_sha256 = load_selected_generator(TASK_ID, root=root)

    endpoints = {
        f"{axis}={value}": _attempt(gen, **{axis: value})
        for axis, value in (
            ("grid_h", 8),
            ("grid_h", 14),
            ("grid_w", 10),
            ("grid_w", 17),
            ("n_markers", 1),
            ("n_markers", 5),
        )
    }

    explicit_triple = gen.generate(0, 0, difficulty="easy", overlap="triple")
    omitted_overlap = gen.generate(0, 0, difficulty="easy")
    actual_triple_texture = gen.generate(0, 0, difficulty="easy", texture="triple")
    no_markers = gen.generate(0, 0, difficulty="easy", texture="no_markers")

    report = {
        "schema": "arcpuzzles-audit-reproducer-v1",
        "task_id": TASK_ID,
        "generator_path": str(source.relative_to(root)),
        "generator_sha256": source_sha256,
        "version": gen.VERSION,
        "declared_axes": gen.AXES,
        "advertised_endpoint_cases": endpoints,
        "advertised_endpoint_failures": sum(
            not row["accepted"] for row in endpoints.values()
        ),
        "overlap_override_case": {
            "seed": 0,
            "sample_index": 0,
            "difficulty": "easy",
            "override": {"overlap": "triple"},
            "same_grid_as_omitted_overlap": explicit_triple == omitted_overlap,
            "observed_max_copy_overlap": _max_copy_overlap(gen, explicit_triple),
            "texture_triple_max_copy_overlap": _max_copy_overlap(
                gen, actual_triple_texture
            ),
            "self_check": gen.self_check(explicit_triple),
        },
        "degenerate_texture_case": {
            "seed": 0,
            "sample_index": 0,
            "difficulty": "easy",
            "override": {"texture": "no_markers"},
            "accepted_by_generate": True,
            "self_check": gen.self_check(no_markers),
        },
        "conclusion": (
            "Reproduced public-contract defects: all six advertised numeric "
            "endpoints are rejected; overlap='triple' is ignored when texture "
            "is omitted; and advertised texture='no_markers' produces a grid "
            "rejected by self_check."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "generator_sha256": source_sha256,
        "advertised_endpoint_failures": report["advertised_endpoint_failures"],
        "overlap_override_ignored": report["overlap_override_case"]["same_grid_as_omitted_overlap"],
        "overlap_override_observed_max": report["overlap_override_case"]["observed_max_copy_overlap"],
        "texture_triple_observed_max": report["overlap_override_case"]["texture_triple_max_copy_overlap"],
        "no_markers_self_check_errors": len(report["degenerate_texture_case"]["self_check"]),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
