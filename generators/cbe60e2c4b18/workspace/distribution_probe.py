#!/usr/bin/env python3
"""Measure palette and disconnected-bridge coverage for cbe60e2c4b18.

This authoring probe intentionally inspects only generated inputs.  It is useful
before and after edits because it reports normalized minimal bridge signatures,
ordinary input-color coverage, and observed axis values as stable JSON.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
import json
from collections import Counter
from pathlib import Path
from typing import Iterable

MODULE_NAME = "puzzle_generators.per_puzzle.cbe60e2c4b18.generator"
GENERATOR_PATH = Path(__file__).resolve().parents[1] / "generator.py"
_spec = importlib.util.spec_from_file_location(MODULE_NAME, GENERATOR_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"cannot load generator from {GENERATOR_PATH}")
GEN = importlib.util.module_from_spec(_spec)
sys.modules[MODULE_NAME] = GEN
_spec.loader.exec_module(GEN)


def _split(grid: list[list[int]]) -> tuple[list[list[int]], list[list[int]]]:
    divider = next(
        col
        for col in range(len(grid[0]))
        if all(row[col] == 9 for row in grid)
    )
    return (
        [row[:divider] for row in grid],
        [row[divider + 1 :] for row in grid],
    )


def _support(panel: list[list[int]]) -> set[tuple[int, int]]:
    return {
        (row, col)
        for row, values in enumerate(panel)
        for col, value in enumerate(values)
        if value != 0
    }


def _normalize_pair(
    left: set[tuple[int, int]], right: set[tuple[int, int]]
) -> str:
    cells = left | right
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)

    def normalized(cells_: Iterable[tuple[int, int]]) -> list[list[int]]:
        return sorted([[row - row0, col - col0] for row, col in cells_])

    return json.dumps(
        {"left": normalized(left), "right": normalized(right)},
        sort_keys=True,
        separators=(",", ":"),
    )


def collect(samples: int) -> dict[str, object]:
    colors: Counter[int] = Counter()
    palette_kinds: Counter[str] = Counter()
    layouts: Counter[str] = Counter()
    shapes: Counter[str] = Counter()

    bands = ("easy", "medium", "hard")
    for index in range(samples):
        band = bands[index % len(bands)]
        grid = GEN.generate(10_000 + index // 7, index, difficulty=band)
        observed = GEN.observe_overrides(grid)
        palette_kinds[str(observed.get("palette_kind"))] += 1
        layouts[str(observed.get("overlap_layout"))] += 1
        shapes[f"{len(grid)}x{(len(grid[0]) - 1) // 2}"] += 1
        left, right = _split(grid)
        for panel in (left, right):
            colors.update(value for row in panel for value in row if value != 0)

    bridge_signatures: Counter[str] = Counter()
    # Exact minimal counts isolate the mandatory 2x2 disconnected bridge core.
    for index in range(samples):
        grid = GEN.generate(
            20_000 + index // 5,
            index,
            difficulty="medium",
            overlap_layout="disconnected",
            shared_count=2,
            left_only_count=1,
            right_only_count=1,
        )
        left, right = _split(grid)
        bridge_signatures[_normalize_pair(_support(left), _support(right))] += 1

    return {
        "samples_per_probe": samples,
        "ordinary_input_colors": sorted(colors),
        "ordinary_input_color_counts": {str(k): colors[k] for k in sorted(colors)},
        "ordinary_palette_kinds": dict(sorted(palette_kinds.items())),
        "ordinary_overlap_layouts": dict(sorted(layouts.items())),
        "ordinary_panel_shapes": dict(sorted(shapes.items())),
        "minimal_disconnected_bridge_signature_count": len(bridge_signatures),
        "minimal_disconnected_bridge_signatures": dict(sorted(bridge_signatures.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=256)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.samples < 1:
        parser.error("--samples must be positive")
    result = collect(args.samples)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
