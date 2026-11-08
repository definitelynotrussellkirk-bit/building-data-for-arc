#!/usr/bin/env python3
"""Independent oracle and replayable audit helpers for ARC task e9be57a9c56d.

This module deliberately does not import implementation helpers from generator.py.
It gives task-local tests and later reviewers an independent transcription of the
selected Racket rule, concrete shortcut policies, and a compact distribution audit.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any, Iterable

TASK_ID = "e9be57a9c56d"
Grid = list[list[int]]


def load_generator(path: str | Path | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or Path(__file__).resolve().parents[1] / "generator.py")
    spec = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _root() -> Path:
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        if (candidate / "shared/data/canonical/puzzles.jsonl").is_file():
            return candidate
        if (candidate / "data/canonical/puzzles.jsonl").is_file():
            return candidate
    raise FileNotFoundError("no canonical ledger above reference_probe.py")


def canonical_record() -> dict[str, Any]:
    root = _root()
    path = (root / "shared/data/canonical/puzzles.jsonl"
            if (root / "shared/data/canonical/puzzles.jsonl").is_file()
            else root / "data/canonical/puzzles.jsonl")
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise KeyError(TASK_ID)


def canonical_pairs() -> list[dict[str, Any]]:
    row = canonical_record()
    pairs: list[dict[str, Any]] = []
    for split in ("train", "test"):
        values = row.get(split, [])
        if isinstance(values, dict):
            values = [values]
        for index, pair in enumerate(values):
            if "output" not in pair:
                continue
            pairs.append({
                "input": deepcopy(pair["input"]),
                "output": deepcopy(pair["output"]),
                "split": split,
                "pair_index": index,
            })
    return pairs


def _validated_grid(grid: Any) -> Grid:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid colors must be integers 0..9")
    return [list(row) for row in grid]


def components8(grid: Grid) -> list[dict[str, Any]]:
    """Same-colour 8-connected components, in row-major discovery order."""
    g = _validated_grid(grid)
    height, width = len(g), len(g[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = g[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == dc == 0:
                            continue
                        nr, nc = rr + dr, cc + dc
                        if (0 <= nr < height and 0 <= nc < width
                                and (nr, nc) not in seen and g[nr][nc] == color):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            cells.sort()
            result.append({"color": color, "cells": tuple(cells), "size": len(cells)})
    return result


def _normalized(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    values = tuple(cells)
    if not values:
        raise ValueError("cannot normalize an empty component")
    row0 = min(row for row, _ in values)
    col0 = min(col for _, col in values)
    return tuple(sorted((row - row0, col - col0) for row, col in values))


def analyze(grid: Grid) -> dict[str, Any]:
    g = _validated_grid(grid)
    height, width = len(g), len(g[0])
    components = sorted(components8(g), key=lambda item: item["size"], reverse=True)
    if len(components) < 3:
        raise ValueError("need one template and at least two marker components")
    template = components[0]
    if template["size"] < 3:
        raise ValueError("template must contain at least three cells")
    if components[1]["size"] >= template["size"]:
        raise ValueError("template is not uniquely largest")
    if any(component["size"] != 1 for component in components[1:]):
        raise ValueError("every non-template component must be a singleton marker")

    markers = [
        {"color": component["color"], "row": component["cells"][0][0], "col": component["cells"][0][1]}
        for component in components[1:]
    ]
    same_row = len({marker["row"] for marker in markers}) == 1
    same_col = len({marker["col"] for marker in markers}) == 1
    if same_row == same_col:
        raise ValueError("markers must lie on exactly one row or exactly one column")
    orientation = "horizontal" if same_row else "vertical"
    key = (lambda marker: marker["col"]) if same_row else (lambda marker: marker["row"])
    markers.sort(key=key)
    coordinates = [key(marker) for marker in markers]
    gaps = [right - left for left, right in zip(coordinates, coordinates[1:])]
    if any(gap < 2 for gap in gaps):
        raise ValueError("marker gaps must be at least two")

    anchor_candidates = [index for index, marker in enumerate(markers)
                         if marker["color"] == template["color"]]
    if len(anchor_candidates) != 1:
        raise ValueError("exactly one marker must share the template color")
    anchor = anchor_candidates[0]
    row0 = min(row for row, _ in template["cells"])
    col0 = min(col for _, col in template["cells"])
    row1 = max(row for row, _ in template["cells"])
    col1 = max(col for _, col in template["cells"])
    pattern = _normalized(template["cells"])
    template_h, template_w = row1 - row0 + 1, col1 - col0 + 1

    return {
        "grid": g,
        "height": height,
        "width": width,
        "template": template,
        "template_color": template["color"],
        "template_size": template["size"],
        "template_origin": (row0, col0),
        "template_h": template_h,
        "template_w": template_w,
        "pattern": pattern,
        "markers": markers,
        "n_markers": len(markers),
        "orientation": orientation,
        "anchor_pos": anchor,
        "gaps": gaps,
    }


def _positions(scene: dict[str, Any], anchor: int) -> list[tuple[int, int]]:
    row0, col0 = scene["template_origin"]
    n = scene["n_markers"]
    positions: list[tuple[int, int] | None] = [None] * n
    positions[anchor] = (row0, col0)
    horizontal = scene["orientation"] == "horizontal"
    for index in range(anchor + 1, n):
        prev_row, prev_col = positions[index - 1]  # type: ignore[misc]
        gap = scene["gaps"][index - 1]
        positions[index] = ((prev_row, prev_col + scene["template_w"] - 1 + gap)
                            if horizontal
                            else (prev_row + scene["template_h"] - 1 + gap, prev_col))
    for index in range(anchor - 1, -1, -1):
        next_row, next_col = positions[index + 1]  # type: ignore[misc]
        gap = scene["gaps"][index]
        positions[index] = ((next_row, next_col - gap - scene["template_w"] + 1)
                            if horizontal
                            else (next_row - gap - scene["template_h"] + 1, next_col))
    return [position for position in positions if position is not None]


def output_with_anchor(
    grid: Grid, anchor: int, *, clip_out_of_bounds: bool = False
) -> Grid:
    scene = analyze(grid)
    if type(anchor) is not int or not 0 <= anchor < scene["n_markers"]:
        raise ValueError("anchor outside marker range")
    output = deepcopy(scene["grid"])
    positions = _positions(scene, anchor)
    for index, marker in enumerate(scene["markers"]):
        if index == anchor:
            continue
        row0, col0 = positions[index]
        for dr, dc in scene["pattern"]:
            row, col = row0 + dr, col0 + dc
            if not (0 <= row < scene["height"] and 0 <= col < scene["width"]):
                if clip_out_of_bounds:
                    continue
                raise ValueError("derived copy leaves the grid")
            output[row][col] = marker["color"]
    return output


def oracle(grid: Grid) -> Grid:
    scene = analyze(grid)
    return output_with_anchor(grid, scene["anchor_pos"])


def fixed_color_two_anchor(grid: Grid) -> Grid:
    """Canonical-fitting shortcut: marker color 2 is always the anchor.

    A wrong anchor can project part of a copy beyond the canvas.  This rival is
    deliberately total: like many simple raster implementations, it clips those
    cells rather than rejecting the input.
    """
    scene = analyze(grid)
    chosen = next((index for index, marker in enumerate(scene["markers"])
                   if marker["color"] == 2), scene["anchor_pos"])
    return output_with_anchor(grid, chosen, clip_out_of_bounds=True)


def endpoint_only_anchor(grid: Grid) -> Grid:
    """Canonical-fitting shortcut: a valid anchor is assumed to be an endpoint."""
    scene = analyze(grid)
    chosen = scene["anchor_pos"] if scene["anchor_pos"] in {0, scene["n_markers"] - 1} else 0
    return output_with_anchor(grid, chosen, clip_out_of_bounds=True)


def facts(grid: Grid) -> dict[str, Any]:
    scene = analyze(grid)
    return {
        "height": scene["height"],
        "width": scene["width"],
        "palette_size": len({value for row in scene["grid"] for value in row}),
        "orientation": scene["orientation"],
        "n_markers": scene["n_markers"],
        "template_size": scene["template_size"],
        "template_color": scene["template_color"],
        "anchor_pos": scene["anchor_pos"],
        "gaps": list(scene["gaps"]),
    }


def profile(grid: Grid) -> tuple[int, int, int]:
    data = facts(grid)
    return data["height"], data["width"], data["palette_size"]


def racket_outputs(grids: list[Grid]) -> list[Grid]:
    """Execute the selected canonical Racket rule; never fall back to Python."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    from puzzle_generators import runner
    source = canonical_record()["program_solution"]
    bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(source))
    try:
        return [runner._apply_rule(bridge, name, deepcopy(grid)) for grid in grids]
    finally:
        bridge.shutdown()


def audit(count: int = 64, *, seed: int = 1701, difficulty: str | None = None) -> dict[str, Any]:
    """Return a compact, JSON-serializable distribution/semantic audit."""
    gen = load_generator()
    grids = [gen.generate(seed, index, difficulty=difficulty) for index in range(count)]
    rows = [facts(grid) for grid in grids]
    return {
        "task_id": TASK_ID,
        "generator_version": getattr(gen, "VERSION", None),
        "difficulty": difficulty,
        "count": count,
        "self_check_failures": [
            {"sample_index": index, "errors": gen.self_check(grid)}
            for index, grid in enumerate(grids) if gen.self_check(grid)
        ],
        "profiles": {str(item): sum(profile(grid) == item for grid in grids)
                     for item in sorted(set(map(profile, grids)))},
        "orientations": {value: sum(row["orientation"] == value for row in rows)
                         for value in sorted({row["orientation"] for row in rows})},
        "anchor_positions": {str(value): sum(row["anchor_pos"] == value for row in rows)
                             for value in sorted({row["anchor_pos"] for row in rows})},
        "template_colors": {str(value): sum(row["template_color"] == value for row in rows)
                            for value in sorted({row["template_color"] for row in rows})},
        "shortcut_counterexamples": {
            "fixed_color_two_anchor": sum(fixed_color_two_anchor(grid) != oracle(grid) for grid in grids),
            "endpoint_only_anchor": sum(endpoint_only_anchor(grid) != oracle(grid) for grid in grids),
        },
        "unique_inputs": len({tuple(map(tuple, grid)) for grid in grids}),
    }


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=64)
    parser.add_argument("--seed", type=int, default=1701)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"))
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = audit(args.count, seed=args.seed, difficulty=args.difficulty)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
