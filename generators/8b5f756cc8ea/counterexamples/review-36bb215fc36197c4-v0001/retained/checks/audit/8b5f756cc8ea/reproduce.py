from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "8b5f756cc8ea"
ROOT = find_root(__file__)
gen, source_path, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)


def digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def component_stats(grid):
    h, w = len(grid), len(grid[0])
    occupied = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    rows = []
    while occupied:
        start = min(occupied)
        stack = [start]
        occupied.remove(start)
        cells = {start}
        while stack:
            r, c = stack.pop()
            for nr, nc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if (nr, nc) in occupied:
                    occupied.remove((nr, nc))
                    cells.add((nr, nc))
                    stack.append((nr, nc))
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        rows.append({
            "bbox": [min(rs), min(cs), max(rs), max(cs)],
            "size": len(cells),
            "non4_count": sum(grid[r][c] != 4 for r, c in cells),
            "colors": sorted({grid[r][c] for r, c in cells}),
        })
    return sorted(rows, key=lambda row: row["bbox"])


seed, sample_index, difficulty = 12345, 7, "medium"
base = gen.generate(seed, sample_index, difficulty=difficulty)
cases = {
    "default": base,
    "anchor_corner_true": gen.generate(seed, sample_index, difficulty=difficulty, anchor_corner=True),
    "palette_size_3": gen.generate(seed, sample_index, difficulty=difficulty, palette_size=3),
    "unknown_axis": gen.generate(seed, sample_index, difficulty=difficulty, invented_axis=42),
    "n_frames_7": gen.generate(seed, sample_index, difficulty=difficulty, n_frames=7),
}
errors = {}
try:
    gen.generate(seed, sample_index, difficulty=difficulty, n_frames=9)
except Exception as exc:
    errors["declared_n_frames_9_medium"] = {"type": type(exc).__name__, "message": str(exc)}
try:
    gen.generate(seed, sample_index, difficulty="easy", grid_h=28)
except Exception as exc:
    errors["declared_grid_h_28_easy"] = {"type": type(exc).__name__, "message": str(exc)}

canonical = []
for pair in canonical_pairs(TASK_ID, root=ROOT, variant=0, labeled_only=True):
    canonical.append({
        "split": pair["split"],
        "pair_index": pair["pair_index"],
        "dims": [len(pair["input"]), len(pair["input"][0])],
        "components": component_stats(pair["input"]),
        "self_check": gen.self_check(pair["input"]),
    })

report = {
    "task_id": TASK_ID,
    "generator_path": str(Path(source_path).relative_to(ROOT)),
    "generator_sha256": source_sha256,
    "reproducer": {"seed": seed, "sample_index": sample_index, "difficulty": difficulty},
    "cases": {
        name: {
            "sha256": digest(grid),
            "dims": [len(grid), len(grid[0])],
            "components": component_stats(grid),
            "self_check": gen.self_check(grid),
            "equals_default": grid == base,
        }
        for name, grid in cases.items()
    },
    "errors": errors,
    "canonical_variant_0": canonical,
    "findings": {
        "ignored_axes": [
            name for name in ("anchor_corner_true", "palette_size_3", "unknown_axis")
            if cases[name] == base
        ],
        "requested_n_frames": 7,
        "observed_n_frames": len(component_stats(cases["n_frames_7"])),
        "declared_n_frames_9_rejected_in_medium": "declared_n_frames_9_medium" in errors,
        "declared_grid_h_28_rejected_in_easy": "declared_grid_h_28_easy" in errors,
        "canonical_non4_counts": [
            [component["non4_count"] for component in row["components"]]
            for row in canonical
        ],
        "generated_non4_counts": [
            component["non4_count"] for component in component_stats(base)
        ],
    },
}
Path(__file__).with_name("report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report["findings"], indent=2, sort_keys=True))
