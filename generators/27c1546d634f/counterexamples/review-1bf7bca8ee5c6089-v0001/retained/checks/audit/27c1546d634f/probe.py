#!/usr/bin/env python3
"""Source-bound audit probe for 27c1546d634f curriculum shortcuts."""
from __future__ import annotations

import argparse
import json
from collections import deque
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "27c1546d634f"
EXPECTED_SOURCE_SHA256 = "d6868189578e51934ca8ba9ff8546d38a3bf506d778602fdd7184b9133b30e93"
BANDS = ("easy", "medium", "hard")
PER_BAND = 200


def components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0}
    out: list[set[tuple[int, int]]] = []
    while cells:
        start = min(cells)
        cells.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nxt in cells:
                    cells.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        out.append(component)
    return out


def bbox(component: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in component]
    cols = [c for _, c in component]
    return min(rows), min(cols), max(rows), max(cols)


def is_perfect_hollow_rectangle(component: set[tuple[int, int]]) -> bool:
    r1, c1, r2, c2 = bbox(component)
    if r2 - r1 + 1 < 3 or c2 - c1 + 1 < 3:
        return False
    border = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }
    return component == border


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    root = find_root(__file__)
    gen, source, source_sha256 = load_selected_generator(TASK_ID, root=root)
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"source drift: expected {EXPECTED_SOURCE_SHA256}, got {source_sha256}")

    rows = []
    perfect_unique = 0
    frame_largest = 0
    no_frame = 0
    max_distractor = 0
    self_check_failures = []
    for band_index, band in enumerate(BANDS):
        for index in range(PER_BAND):
            seed = 910_000 + band_index * 10_000 + index
            sample_index = index
            grid = gen.generate(seed, sample_index, difficulty=band)
            errors = list(gen.self_check(grid, difficulty=band))
            if errors:
                self_check_failures.append({"band": band, "seed": seed, "sample_index": sample_index, "errors": errors})
            comps = components(grid)
            frames = [component for component in comps if is_perfect_hollow_rectangle(component)]
            if len(frames) == 1:
                perfect_unique += 1
                frame = frames[0]
                distractors = [len(component) for component in comps if component is not frame]
                max_distractor = max(max_distractor, max(distractors, default=0))
                if len(frame) > max(distractors, default=-1):
                    frame_largest += 1
            else:
                no_frame += 1
            if len(rows) < 3:
                rows.append({
                    "band": band,
                    "seed": seed,
                    "sample_index": sample_index,
                    "component_sizes": sorted((len(component) for component in comps), reverse=True),
                    "perfect_frame_count": len(frames),
                })

    samples = len(BANDS) * PER_BAND
    ignored_override_probe = {
        "same_seed_palette_kind_warm_equals_cool": (
            gen.generate(1234, 17, difficulty="medium", palette_kind="warm")
            == gen.generate(1234, 17, difficulty="medium", palette_kind="cool")
        ),
        "n_solids_zero_still_generates_nonframe_components": None,
        "unknown_override_accepted": None,
    }
    zero_grid = gen.generate(4321, 19, difficulty="medium", n_solids=0)
    zero_components = components(zero_grid)
    zero_frames = [component for component in zero_components if is_perfect_hollow_rectangle(component)]
    ignored_override_probe["n_solids_zero_still_generates_nonframe_components"] = (
        len(zero_components) - len(zero_frames) > 0
    )
    try:
        gen.generate(7, 8, difficulty="medium", typo_axis="ignored")
    except Exception:
        ignored_override_probe["unknown_override_accepted"] = False
    else:
        ignored_override_probe["unknown_override_accepted"] = True

    report = {
        "schema": "arcpuzzles-audit-probe-27c1546d634f-v1",
        "task_id": TASK_ID,
        "generator_path": str(source.relative_to(root)),
        "generator_source_sha256": source_sha256,
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "sampling": {
            "bands": list(BANDS),
            "per_band": PER_BAND,
            "seed_recipe": "910000 + band_index*10000 + index",
            "sample_index_recipe": "index",
            "samples": samples,
        },
        "results": {
            "unique_perfect_rectangular_frame": perfect_unique,
            "perfect_frame_is_strictly_largest_component": frame_largest,
            "missing_or_multiple_perfect_frames": no_frame,
            "max_distractor_component_size": max_distractor,
            "self_check_failures": self_check_failures,
            "shortcut_fit": {
                "crop_unique_perfect_rectangle": perfect_unique == samples,
                "crop_largest_component": frame_largest == samples,
            },
            "ignored_override_probe": ignored_override_probe,
        },
        "sample_rows": rows,
        "scope_note": (
            "Finite source-bound sampling only. The authority rule selects the first object with exactly one hole; "
            "the generated curriculum instead makes that object uniquely rectangular and strictly largest."
        ),
        "command": [
            "python3", "review.py", "run", "python3",
            "../checks/audit/27c1546d634f/probe.py", "--out",
            "../checks/audit/27c1546d634f/probe.json",
        ],
        "working_directory": "packet_root",
        "payload_working_directory": "repo",
    }
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "samples": samples,
        "shortcut_fit": report["results"]["shortcut_fit"],
        "ignored_override_probe": ignored_override_probe,
        "source_sha256": source_sha256,
    }, indent=2, sort_keys=True))
    return 0 if all(report["results"]["shortcut_fit"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
