#!/usr/bin/env python3
"""Cheap opt-in coverage gate for reference-verified wall-selection lessons.

Require a painted region with a side longer than four cells, plus the same small
interior shape both painted behind complete walls and left black with a failed
bounding-box side. Shape and size alone then cannot explain every demo label.
This does not execute the reference, prove uniqueness, or measure learning benefit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def _grid(value, colors):
    if type(value) is not list or not 8 <= len(value) <= 30:
        raise ValueError("grid height must be in 8..30")
    if type(value[0]) is not list or not 8 <= len(value[0]) <= 30:
        raise ValueError("grid width must be in 8..30")
    width = len(value[0])
    if any(type(row) is not list or len(row) != width for row in value):
        raise ValueError("grid must be rectangular")
    if any(type(v) is not int or v not in colors for row in value for v in row):
        raise ValueError("grid cells must be exact integer role colors")
    return value


def _components(grid):
    remaining = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 0}
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        cells, queue = {start}, [start]
        while queue:
            r, c = queue.pop()
            for other in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if other in remaining:
                    remaining.remove(other)
                    cells.add(other)
                    queue.append(other)
        yield cells


def check_episode(episode):
    """Inspect observed component labels in train only; never evaluate test."""
    if type(episode) is not dict or type(episode.get("train")) is not list or not episode["train"]:
        raise ValueError("at least one labeled demonstration is required")
    large, small = [], []
    painted_shapes, rejected_shapes = {}, {}
    for index, pair in enumerate(episode["train"]):
        if type(pair) is not dict or "input" not in pair or "output" not in pair:
            raise ValueError("demonstration must contain input and output")
        grid = _grid(pair["input"], {0, 5})
        output = _grid(pair["output"], {0, 4, 5})
        h, w = len(grid), len(grid[0])
        if len(output) != h or len(output[0]) != w:
            raise ValueError("input and output dimensions must agree")
        if any(output[r][c] != 5 for r in range(h) for c in range(w) if grid[r][c] == 5):
            raise ValueError("gray walls must remain unchanged")
        for cells in _components(grid):
            labels = {output[r][c] for r, c in cells}
            if labels not in ({0}, {4}):
                raise ValueError("a zero component must be wholly black or wholly yellow")
            r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
            c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
            record = {"demonstration_index": index, "bbox": [r0, c0, r1, c1], "size": len(cells)}
            if labels == {4} and (r1 - r0 + 1 > 4 or c1 - c0 + 1 > 4):
                large.append(record)
            interior = 0 < r0 <= r1 < h - 1 and 0 < c0 <= c1 < w - 1
            compact = r1 - r0 + 1 <= 4 and c1 - c0 + 1 <= 4
            if interior and compact:
                walls = {
                    "top": all(grid[r0 - 1][c] == 5 for c in range(c0, c1 + 1)),
                    "bottom": all(grid[r1 + 1][c] == 5 for c in range(c0, c1 + 1)),
                    "left": all(grid[r][c0 - 1] == 5 for r in range(r0, r1 + 1)),
                    "right": all(grid[r][c1 + 1] == 5 for r in range(r0, r1 + 1)),
                }
                signature = tuple(sorted((r - r0, c - c0) for r, c in cells))
                if labels == {4} and all(walls.values()):
                    painted_shapes.setdefault(signature, []).append(record)
                if labels == {0} and not all(walls.values()):
                    rejected = {**record, "failed_walls": [name for name, ok in walls.items() if not ok]}
                    small.append(rejected)
                    rejected_shapes.setdefault(signature, []).append(rejected)
    contrasts = [{"normalized_cells": [list(cell) for cell in signature],
                  "painted_examples": painted_shapes[signature],
                  "rejected_examples": rejected_shapes[signature]}
                 for signature in sorted(painted_shapes.keys() & rejected_shapes.keys())]
    missing = []
    if not large:
        missing.append("large_painted_region")
    if not small:
        missing.append("small_interior_rejected_wall_region")
    if not contrasts:
        missing.append("same_shape_opposite_wall_outcomes")
    return {
        "status": "missing_contrast" if missing else "passed",
        "demonstrations": len(episode["train"]),
        "large_painted_regions": large,
        "small_rejected_wall_regions": small,
        "matched_shape_wall_contrasts": contrasts,
        "missing": missing,
    }


def _episodes(value):
    if type(value) is list:
        return [episode for item in value for episode in _episodes(item)]
    if type(value) is not dict:
        raise ValueError("expected episode object, collection, or native metadata wrapper")
    if "train" in value:
        return [value]
    for key in ("episode", "episodes"):
        if key in value:
            return _episodes(value[key])
    raise ValueError("no episode train data found")


def read_episodes(path):
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        return [episode for line in text.splitlines() if line.strip() for episode in _episodes(json.loads(line))]
    return _episodes(json.loads(text))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--require-contrast", action="store_true")
    args = parser.parse_args(argv)
    rows = [check_episode(episode) for episode in read_episodes(args.input)]
    if not rows:
        raise ValueError("input must contain at least one episode")
    report = {
        "schema": "wall-teaching-contrast-gate-v1",
        "status": "passed" if all(row["status"] == "passed" for row in rows) else "missing_contrast",
        "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "scope": "Demonstration-only structural coverage over supplied labels; no reference execution, query use, acceptance or measured learner benefit.",
        "episodes": rows,
    }
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("x", encoding="utf-8") as handle:
            handle.write(payload)
    print(payload, end="")
    return int(args.require_contrast and report["status"] != "passed")


if __name__ == "__main__":
    raise SystemExit(main())
