#!/usr/bin/env python3
"""Independent diagnostic probe for b7ff231aab1a.

This tool deliberately does not import the production rule mirror.  It computes
both the intended area-ranked answer and the strongest canonical-compatible
reading-order rival from pixels, making it useful when reviewing future edits.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
from typing import Any

TASK_HOME = Path(__file__).resolve().parents[1]


def components(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            comp: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                comp.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            found.append(comp)
    return found


def bbox(comp: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in comp]
    cols = [c for _, c in comp]
    return min(rows), min(cols), max(rows), max(cols)


def render(grid: list[list[int]], comp: list[tuple[int, int]]) -> list[list[int]]:
    r0, c0, r1, c1 = bbox(comp)
    crop = [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]
    return [
        [8 if crop[r // 2][c // 2] != 0 else 0 for c in range(2 * len(crop[0]))]
        for r in range(2 * len(crop))
    ]


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    blue = components(grid, 1)
    if len(blue) != 3:
        raise ValueError(f"expected three blue components, found {len(blue)}")
    marker_count = sum(value == 9 for row in grid for value in row)
    if not 1 <= marker_count <= 3:
        raise ValueError(f"expected 1..3 marker cells, found {marker_count}")

    by_area = sorted(blue, key=lambda comp: (len(comp), bbox(comp)[0], bbox(comp)[1]))
    by_reading = sorted(blue, key=lambda comp: (bbox(comp)[0], bbox(comp)[1]))
    size_order = [len(comp) for comp in by_area]
    rank_by_size = {size: rank + 1 for rank, size in enumerate(size_order)}
    reading_ranks = [rank_by_size[len(comp)] for comp in by_reading]
    intended = render(grid, by_area[marker_count - 1])
    rival = render(grid, by_reading[marker_count - 1])
    return {
        "marker_count": marker_count,
        "size_order": size_order,
        "reading_order_sizes": [len(comp) for comp in by_reading],
        "reading_order_size_ranks": reading_ranks,
        "intended_selected_bbox": list(bbox(by_area[marker_count - 1])),
        "reading_order_selected_bbox": list(bbox(by_reading[marker_count - 1])),
        "intended_output": intended,
        "reading_order_output": rival,
        "disagrees": intended != rival,
    }


def _load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load generator at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def witness(seed: int, sample_index: int) -> dict[str, Any]:
    generator_path = Path(
        os.environ.get("GENERATOR_UNDER_TEST", TASK_HOME / "generator.py")
    )
    gen = _load_generator(generator_path)
    overrides = {
        "grid_h": 11,
        "grid_w": 15,
        "marker_count": 1,
        "size_profile": "sizes_234",
        "rank_layout": "medium_large_small",
    }
    grid = gen.generate(seed, sample_index, **overrides)
    return {
        "task_id": "b7ff231aab1a",
        "seed": seed,
        "sample_index": sample_index,
        "overrides": overrides,
        "input": grid,
        **analyze(grid),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="JSON grid to analyze")
    parser.add_argument("--seed", type=int, default=20261007)
    parser.add_argument("--sample-index", type=int, default=0)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    if args.input is None:
        report = witness(args.seed, args.sample_index)
    else:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        grid = payload.get("input", payload) if isinstance(payload, dict) else payload
        report = {"task_id": "b7ff231aab1a", "input": grid, **analyze(grid)}

    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
