#!/usr/bin/env python3
"""Canonical-compatible rival: partition each multi-seed region by nearest seed.

The selected generator deliberately emits at most one seed per 4-connected
non-wall component.  On that domain this rival is observationally identical to
the canonical sequential flood.  It differs on lawful rule inputs containing
competing seeds and is therefore useful as a review probe, not as authority.
"""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
from typing import Any

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list")
    if any(not isinstance(row, list) or not row for row in grid):
        raise ValueError("rows must be nonempty lists")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("cells must be integer colors 0..9")
    return grid


def _components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] != 5
    }
    result: list[set[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARDINAL:
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    queue.append(point)
        result.append(component)
    return result


def _distances(
    component: set[tuple[int, int]], start: tuple[int, int]
) -> dict[tuple[int, int], int]:
    distance = {start: 0}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        for dr, dc in _CARDINAL:
            point = (r + dr, c + dc)
            if point in component and point not in distance:
                distance[point] = distance[(r, c)] + 1
                queue.append(point)
    return distance


def nearest_seed_within_component(grid: Any) -> list[list[int]]:
    """Color each zero by its graph-nearest seed in the same 4-connected region.

    Ties are resolved by original row-major seed order.  Seed cells and gray
    walls are preserved; components with no seed remain zero.
    """
    valid = _validate_grid(grid)
    out = [list(row) for row in valid]
    for component in _components(valid):
        seeds = sorted(
            (r, c, valid[r][c])
            for r, c in component
            if valid[r][c] not in (0, 5)
        )
        if not seeds:
            continue
        maps = [(_distances(component, (r, c)), r, c, color) for r, c, color in seeds]
        for r, c in component:
            if valid[r][c] != 0:
                continue
            _, _, _, color = min(
                maps,
                key=lambda item: (item[0][(r, c)], item[1], item[2], item[3]),
            )
            out[r][c] = color
    return out


def _sha256(value: Any) -> str:
    payload = json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    grid = json.loads(args.input.read_text())
    output = nearest_seed_within_component(grid)
    payload = {
        "schema": "arc-competing-seed-rival-v1",
        "rival": "nearest_seed_within_4_connected_component",
        "input": grid,
        "output": output,
        "input_sha256": _sha256(grid),
        "output_sha256": _sha256(output),
        "note": (
            "Review rival only. It matches the canonical demonstrations because "
            "each demonstrated non-wall component contains at most one seed."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
