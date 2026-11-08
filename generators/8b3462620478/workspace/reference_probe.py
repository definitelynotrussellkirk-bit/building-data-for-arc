#!/usr/bin/env python3
"""Independent beam oracle and rival probe for ARC task 8b3462620478.

This file intentionally does not import ``generator.py``.  Future reviewers can
use it to replay canonical inputs, generated scenes, or saved counterexamples
without trusting the implementation under review.

Examples:
    python3 workspace/reference_probe.py counterexamples/first_three_mirrors_only.json
    python3 workspace/reference_probe.py scene.json --mirror-limit 3
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
from typing import Any

Grid = list[list[int]]


def _validate_grid(grid: Any) -> Grid:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("expected a nonempty list-of-lists grid")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("expected a rectangular list-of-lists grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be integer ARC colors 0..9")
    return deepcopy(grid)


def _reflect(direction: tuple[int, int], mirror: int) -> tuple[int, int]:
    dr, dc = direction
    if mirror == 3:  # slash
        return -dc, -dr
    if mirror == 4:  # backslash
        return dc, dr
    raise ValueError(f"not a mirror color: {mirror!r}")


def trace(
    grid: Any,
    *,
    mirror_limit: int | None = None,
    swap_mirrors: bool = False,
    fuel: int = 500,
) -> tuple[Grid, dict[str, Any]]:
    """Trace the beam using an implementation independent of the generator.

    ``mirror_limit=N`` is the finite-depth rival: every encountered mirror is
    recorded, but only the first N mirrors change direction. ``swap_mirrors``
    exchanges the slash/backslash color meanings.
    """
    if mirror_limit is not None and (type(mirror_limit) is not int or mirror_limit < 0):
        raise ValueError("mirror_limit must be a nonnegative int or None")
    if type(fuel) is not int or fuel <= 0:
        raise ValueError("fuel must be a positive int")

    source_grid = _validate_grid(grid)
    source = [
        (r, c)
        for r, row in enumerate(source_grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    arrow = [
        (r, c)
        for r, row in enumerate(source_grid)
        for c, value in enumerate(row)
        if value == 1
    ]
    if len(source) != 1 or len(arrow) != 1:
        raise ValueError(
            f"expected exactly one red(2) source and blue(1) arrow; got {len(source)} and {len(arrow)}"
        )

    sr, sc = source[0]
    ar, ac = arrow[0]
    dr, dc = ar - sr, ac - sc
    output = deepcopy(source_grid)
    if abs(dr) + abs(dc) != 1:
        return output, {
            "painted": [],
            "mirrors": [],
            "turns": [],
            "stop": "bad_heading",
            "steps": 0,
        }

    h, w = len(source_grid), len(source_grid[0])
    r, c = ar + dr, ac + dc
    painted: list[list[int]] = []
    mirrors: list[list[int]] = []
    turns: list[dict[str, Any]] = []

    for step in range(fuel):
        if not (0 <= r < h and 0 <= c < w):
            stop = "edge"
            break
        value = source_grid[r][c]
        if value == 5:
            stop = "wall"
            break
        if value == 0:
            output[r][c] = 8
            painted.append([r, c])
        if value in (3, 4):
            mirrors.append([r, c, value])
            before = (dr, dc)
            if mirror_limit is None or len(mirrors) <= mirror_limit:
                mirror = 7 - value if swap_mirrors else value
                dr, dc = _reflect(before, mirror)
            turns.append(
                {
                    "at": [r, c],
                    "color": value,
                    "before": list(before),
                    "after": [dr, dc],
                    "active": mirror_limit is None or len(mirrors) <= mirror_limit,
                }
            )
        r, c = r + dr, c + dc
    else:
        stop = "fuel"
        step = fuel

    return output, {
        "painted": painted,
        "mirrors": mirrors,
        "turns": turns,
        "stop": stop,
        "steps": step,
    }


def compare_first_three_rival(grid: Any) -> dict[str, Any]:
    intended, intended_report = trace(grid)
    rival, rival_report = trace(grid, mirror_limit=3)
    differing_cells = [
        [r, c]
        for r, (truth_row, rival_row) in enumerate(zip(intended, rival))
        for c, (truth, guess) in enumerate(zip(truth_row, rival_row))
        if truth != guess
    ]
    return {
        "intended_output": intended,
        "rival_output": rival,
        "disagrees": bool(differing_cells),
        "differing_cells": differing_cells,
        "intended_report": intended_report,
        "rival_report": rival_report,
    }


def _read_grid(path: Path) -> Grid:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        if "input" not in payload:
            raise ValueError("JSON object must contain an 'input' grid")
        payload = payload["input"]
    return _validate_grid(payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_path", type=Path, help="raw grid JSON or object containing an input grid")
    parser.add_argument("--mirror-limit", type=int, default=None)
    parser.add_argument("--swap-mirrors", action="store_true")
    parser.add_argument(
        "--compare-first-three",
        action="store_true",
        help="emit intended-vs-first-three-rival comparison",
    )
    args = parser.parse_args(argv)

    grid = _read_grid(args.json_path)
    if args.compare_first_three:
        payload = compare_first_three_rival(grid)
    else:
        output, report = trace(
            grid,
            mirror_limit=args.mirror_limit,
            swap_mirrors=args.swap_mirrors,
        )
        payload = {"output": output, "report": report}
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
