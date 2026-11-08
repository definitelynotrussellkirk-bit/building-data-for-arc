#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_path, find_root, load_selected_generator, normalize_grid

TASK_ID = "09647f283588"
CORNERS = ((0, 0), (0, 2), (2, 0), (2, 2))
BORDER = ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2))


def canonical_source(root: Path) -> str:
    found = set()
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
            found.add(row["program_solution"])
    if len(found) != 1:
        raise AssertionError(f"expected one canonical source, got {len(found)}")
    return found.pop()


def valid_windows(grid):
    h, w = len(grid), len(grid[0])
    rows = []
    for r0 in range(h - 2):
        for c0 in range(w - 2):
            corners = [grid[r0 + dr][c0 + dc] for dr, dc in CORNERS]
            color = corners[0]
            center = grid[r0 + 1][c0 + 1]
            border = [grid[r0 + dr][c0 + dc] for dr, dc in BORDER]
            if color != 0 and len(set(corners)) == 1 and center == 0 and all(v in (0, color) for v in border):
                rows.append({"r0": r0, "c0": c0, "color": color})
    return rows


def main():
    root = find_root(__file__)
    gen, source_path, source_sha = load_selected_generator(TASK_ID, root=root)
    rule = canonical_source(root)
    samples = []
    for seed in range(10):
        grid = normalize_grid(gen.generate(seed, 0, texture="overlapping_frames"))
        windows = valid_windows(grid)
        samples.append({
            "seed": seed,
            "sample_index": 0,
            "self_check": gen.self_check(grid),
            "grid": grid,
            "canonical_valid_windows": windows,
            "canonical_valid_window_count": len(windows),
        })
    base = Path(__file__).parent
    (base / "inputs.json").write_text(
        json.dumps({"inputs": [row["grid"] for row in samples]}, indent=2) + "\n",
        encoding="utf-8",
    )
    report = {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": TASK_ID,
        "finding": "overlapping_frames overwrites the first frame's shared corners with the second frame color, leaving only one canonical-valid window",
        "generator_path": str(source_path.relative_to(root)),
        "generator_sha256": source_sha,
        "canonical_source_sha256": hashlib.sha256(rule.encode()).hexdigest(),
        "texture": "overlapping_frames",
        "sample_count": len(samples),
        "samples_with_exactly_one_valid_window": sum(row["canonical_valid_window_count"] == 1 for row in samples),
        "samples_with_two_valid_windows": sum(row["canonical_valid_window_count"] == 2 for row in samples),
        "samples": samples,
        "explanation": (
            "Frame A uses corner columns 1 and 3; frame B uses columns 3 and 5. "
            "The second loop assigns a distinct color to both shared column-3 corners, "
            "so frame A cannot retain four same-color corners. The public Racket apply "
            "receipt in racket.json independently shows only one ring is completed."
        ),
    }
    (base / "analysis.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("generator_sha256", "sample_count", "samples_with_exactly_one_valid_window", "samples_with_two_valid_windows")}, sort_keys=True))


if __name__ == "__main__":
    main()
