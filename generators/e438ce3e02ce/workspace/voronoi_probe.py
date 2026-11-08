#!/usr/bin/env python3
"""Independent nearest-seed oracle and inspection CLI for e438ce3e02ce.

This file deliberately does not import the generator.  Reviewers can use it to
check a JSON grid, compare Manhattan and squared-Euclidean partitions, inspect
tie arity, and evaluate truncated-seed shortcuts without trusting generator
helpers.

Examples:
    python3 voronoi_probe.py input.json
    cat input.json | python3 voronoi_probe.py -
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

Grid = list[list[int]]
Seed = tuple[int, int, int]


def normalize_grid(value: Any) -> Grid:
    """Return a rectangular ARC integer grid or raise ValueError."""
    if not isinstance(value, list) or not value:
        raise ValueError("grid must be a non-empty list")
    rows: Grid = []
    width: int | None = None
    for row in value:
        if isinstance(row, str):
            row = [int(ch) for ch in row if not ch.isspace()]
        if not isinstance(row, list) or not row:
            raise ValueError("every row must be a non-empty list")
        if any(type(cell) is not int or not 0 <= cell <= 9 for cell in row):
            raise ValueError("cells must be integer ARC colors 0..9")
        if width is None:
            width = len(row)
        elif len(row) != width:
            raise ValueError("grid must be rectangular")
        rows.append(list(row))
    return rows


def seed_cells(grid: Any) -> list[Seed]:
    rows = normalize_grid(grid)
    return [
        (r, c, value)
        for r, row in enumerate(rows)
        for c, value in enumerate(row)
        if value != 0
    ]


def _distance(metric: str, r: int, c: int, sr: int, sc: int) -> int:
    dr, dc = abs(r - sr), abs(c - sc)
    if metric == "manhattan":
        return dr + dc
    if metric in {"euclidean2", "squared_euclidean"}:
        return dr * dr + dc * dc
    if metric == "chebyshev":
        return max(dr, dc)
    raise ValueError(f"unknown metric {metric!r}")


def nearest_indices(
    grid: Any,
    *,
    metric: str = "manhattan",
    limit_seeds: int | None = None,
) -> dict[tuple[int, int], tuple[int, ...]]:
    rows = normalize_grid(grid)
    seeds = seed_cells(rows)
    if limit_seeds is not None:
        if type(limit_seeds) is not int or limit_seeds < 1:
            raise ValueError("limit_seeds must be a positive integer")
        seeds = seeds[:limit_seeds]
    if not seeds:
        raise ValueError("nearest-seed rule needs at least one seed")
    result: dict[tuple[int, int], tuple[int, ...]] = {}
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            if value != 0:
                continue
            distances = [_distance(metric, r, c, sr, sc) for sr, sc, _ in seeds]
            best = min(distances)
            result[(r, c)] = tuple(i for i, distance in enumerate(distances) if distance == best)
    return result


def fill(
    grid: Any,
    *,
    metric: str = "manhattan",
    tie_value: int | None = 8,
    limit_seeds: int | None = None,
) -> Grid:
    rows = normalize_grid(grid)
    seeds = seed_cells(rows)
    active = seeds if limit_seeds is None else seeds[:limit_seeds]
    classes = nearest_indices(rows, metric=metric, limit_seeds=limit_seeds)
    out = [list(row) for row in rows]
    for (r, c), hits in classes.items():
        if len(hits) == 1:
            out[r][c] = active[hits[0]][2]
        elif tie_value is not None:
            out[r][c] = tie_value
    return out


def owner_counts(grid: Any, *, metric: str = "manhattan") -> Counter[int]:
    counts: Counter[int] = Counter()
    for hits in nearest_indices(grid, metric=metric).values():
        if len(hits) == 1:
            counts[hits[0]] += 1
    return counts


def tie_arity_counts(grid: Any, *, metric: str = "manhattan") -> Counter[int]:
    return Counter(
        len(hits)
        for hits in nearest_indices(grid, metric=metric).values()
        if len(hits) >= 2
    )


def disagreement_count(
    grid: Any,
    *,
    left_metric: str = "manhattan",
    right_metric: str = "euclidean2",
) -> int:
    left = fill(grid, metric=left_metric)
    right = fill(grid, metric=right_metric)
    return sum(a != b for row_a, row_b in zip(left, right) for a, b in zip(row_a, row_b))


def inspect(grid: Any) -> dict[str, Any]:
    rows = normalize_grid(grid)
    seeds = seed_cells(rows)
    ties = tie_arity_counts(rows)
    owners = owner_counts(rows)
    return {
        "grid_h": len(rows),
        "grid_w": len(rows[0]),
        "n_seeds": len(seeds),
        "seed_cells": [list(seed) for seed in seeds],
        "unique_owner_counts": {str(index): owners[index] for index in range(len(seeds))},
        "tie_arity_counts": {str(arity): count for arity, count in sorted(ties.items())},
        "max_tie_arity": max(ties, default=0),
        "manhattan_vs_euclidean_disagreements": disagreement_count(rows),
        "ignore_after_three_disagreements": (
            0 if len(seeds) <= 3 else sum(
                a != b
                for row_a, row_b in zip(fill(rows), fill(rows, limit_seeds=3))
                for a, b in zip(row_a, row_b)
            )
        ),
        "ignore_after_four_disagreements": (
            0 if len(seeds) <= 4 else sum(
                a != b
                for row_a, row_b in zip(fill(rows), fill(rows, limit_seeds=4))
                for a, b in zip(row_a, row_b)
            )
        ),
    }


def _load(path: str) -> Any:
    if path == "-":
        value = json.load(sys.stdin)
    else:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(value, dict) and "input" in value:
        return value["input"]
    return value


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("grid_json", help="JSON grid or {'input': grid}; '-' reads stdin")
    parser.add_argument("--emit-output", action="store_true", help="also emit the Manhattan output grid")
    args = parser.parse_args(list(argv) if argv is not None else None)
    grid = _load(args.grid_json)
    payload = inspect(grid)
    if args.emit_output:
        payload["output"] = fill(grid)
    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
