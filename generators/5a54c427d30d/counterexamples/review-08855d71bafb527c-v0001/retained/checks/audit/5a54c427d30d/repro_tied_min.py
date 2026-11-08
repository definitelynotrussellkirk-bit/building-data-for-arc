#!/usr/bin/env python3
"""Reproduce ordinary invalid generations in generator 5a54c427d30d."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3] / "repo"
GEN_PATH = REPO / "generators" / "5a54c427d30d" / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("audit_g5a", GEN_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def component_stats(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    stats = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 0 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0 and (nr, nc) not in seen:
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            stats.append({
                "area": len(cells),
                "nine_count": sum(grid[r][c] == 9 for r, c in cells),
                "colors": sorted({grid[r][c] for r, c in cells}),
                "bbox": [min(r for r, _ in cells), min(c for _, c in cells), max(r for r, _ in cells), max(c for _, c in cells)],
            })
    return stats


def capture_case(gen, seed, sample_index, difficulty):
    capture = {"requested_nine_counts": None, "drawn_shapes": []}
    original_counts = gen._draw_nine_counts
    original_shape = gen._draw_shape

    def wrapped_counts(dist, n_objs, rng):
        values = original_counts(dist, n_objs, rng)
        capture["distribution"] = dist
        capture["requested_nine_counts"] = values[:]
        return values

    def wrapped_shape(kind, s_lo, s_hi, rng):
        dims = original_shape(kind, s_lo, s_hi, rng)
        capture["drawn_shapes"].append(list(dims))
        return dims

    gen._draw_nine_counts = wrapped_counts
    gen._draw_shape = wrapped_shape
    try:
        grid = gen.generate(seed, sample_index, difficulty=difficulty)
    finally:
        gen._draw_nine_counts = original_counts
        gen._draw_shape = original_shape
    capture.update({
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "grid": grid,
        "self_check": gen.self_check(grid, difficulty=difficulty),
        "components": component_stats(grid),
    })
    return capture


def main():
    gen = load_generator()
    checked = 0
    invalid = []
    for difficulty in ("easy", None, "hard"):
        for seed in range(200):
            for sample_index in range(10):
                grid = gen.generate(seed, sample_index, difficulty=difficulty)
                errors = gen.self_check(grid, difficulty=difficulty)
                checked += 1
                if errors:
                    invalid.append({"seed": seed, "sample_index": sample_index, "difficulty": difficulty, "errors": errors})
    case = capture_case(gen, 39, 8, None)
    assert case["self_check"] == ["minimum 9-count is tied (no unique object to erase)"]
    assert case["requested_nine_counts"] is not None
    result = {
        "ordinary_samples_checked": checked,
        "invalid_sample_count": len(invalid),
        "invalid_samples": invalid,
        "reproduction": case,
        "root_cause": "The requested distinct nine-counts can exceed a block's area. generate() clips each count with min(n9, len(local_cells)); different requested counts therefore collapse to the same realized count, sometimes replacing every major-color cell with 9 and tying the minimum.",
    }
    out_path = Path(__file__).with_name("tied_min_evidence.json")
    out_path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "ordinary_samples_checked": checked,
        "invalid_sample_count": len(invalid),
        "first_invalid": invalid[0] if invalid else None,
        "reproduction_requested_counts": case["requested_nine_counts"],
        "reproduction_shapes": case["drawn_shapes"],
        "reproduction_realized_components": case["components"],
        "reproduction_self_check": case["self_check"],
    }, indent=2))
    print(f"evidence={out_path}")
    if not invalid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
