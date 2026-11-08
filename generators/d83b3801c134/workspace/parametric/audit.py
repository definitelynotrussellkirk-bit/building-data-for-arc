"""Bounded teaching and shortcut audit for the marker-vector family."""
from __future__ import annotations

import argparse
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from typing import Callable, Iterable

HERE = Path(__file__).resolve().parent


def _load_adapter():
    path = HERE / "adapter.py"
    spec = importlib.util.spec_from_file_location("d83_parametric_adapter_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load adapter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ADAPTER = _load_adapter()
Grid = list[list[int]]


def _markers(grid: Grid) -> tuple[tuple[int, int], tuple[int, int]]:
    one = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
    two = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    return one[0], two[0]


def _vector(grid: Grid, direction: str) -> tuple[int, int]:
    one, two = _markers(grid)
    start, end = (one, two) if direction == "one_to_two" else (two, one)
    return end[0] - start[0], end[1] - start[1]


def _green_components(grid: Grid) -> list[set[tuple[int, int]]]:
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3}
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for nbr in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nbr in remaining:
                    remaining.remove(nbr)
                    component.add(nbr)
                    stack.append(nbr)
        result.append(component)
    return sorted(result, key=lambda cells: min(cells))


def _paint_shift(grid: Grid, cells: Iterable[tuple[int, int]], dr: int, dc: int) -> Grid:
    h, w = len(grid), len(grid[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    for r, c in cells:
        rr, cc = r + dr, c + dc
        if 0 <= rr < h and 0 <= cc < w:
            out[rr][cc] = 3
    return out


def _first_component(grid: Grid, direction: str) -> Grid:
    dr, dc = _vector(grid, direction)
    return _paint_shift(grid, _green_components(grid)[0], dr, dc)


def _fixed(grid: Grid, dr: int, dc: int) -> Grid:
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3]
    return _paint_shift(grid, cells, dr, dc)


def _origin_stamp(grid: Grid) -> Grid:
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3]
    r0, c0 = min(r for r, _ in cells), min(c for _, c in cells)
    normalized = [(r - r0 + 1, c - c0 + 1) for r, c in cells]
    return _paint_shift(grid, normalized, 0, 0)


def run_audit(seeds: Iterable[int] = range(20)) -> dict[str, object]:
    teaching_holes: list[dict[str, object]] = []
    finite_equivalences: list[dict[str, object]] = []
    vector_values: set[tuple[int, int]] = set()
    minimum_30 = 10**9
    episodes = 0
    rival_failures: dict[str, int] = {}

    for seed in seeds:
        for direction in ADAPTER.DIRECTIONS:
            settings = {"direction": direction}
            episode = ADAPTER.generate(int(seed), settings, demos=3, queries=4)
            episodes += 1
            all_pairs = episode["train"] + episode["test"]
            for pair in all_pairs:
                vector_values.add(_vector(pair["input"], direction))
                if len(pair["input"]) == 30 and len(pair["input"][0]) == 30:
                    green_count = sum(cell == 3 for row in pair["input"] for cell in row)
                    minimum_30 = min(minimum_30, green_count)

            opposite = "two_to_one" if direction == "one_to_two" else "one_to_two"
            rivals: dict[str, Callable[[Grid], Grid]] = {
                "opposite_direction": lambda g, other=opposite: ADAPTER.transform(g, other),
                "first_component_only": lambda g, selected=direction: _first_component(g, selected),
                "fixed_down_right": lambda g: _fixed(g, 1, 1),
                "fixed_up_left": lambda g: _fixed(g, -1, -1),
                "copy_input": lambda g: deepcopy(g),
                "origin_stamp": _origin_stamp,
            }
            for name, rival in rivals.items():
                train_matches = [rival(pair["input"]) == pair["output"] for pair in episode["train"]]
                if all(train_matches):
                    query_matches = [rival(pair["input"]) == pair["output"] for pair in episode["test"]]
                    row = {"seed": int(seed), "settings": settings, "rival": name,
                           "query_matches": query_matches}
                    if all(query_matches):
                        finite_equivalences.append(row)
                    else:
                        teaching_holes.append(row)
                else:
                    rival_failures[name] = rival_failures.get(name, 0) + 1

    if minimum_30 == 10**9:
        minimum_30 = 0
    status = "passed" if not teaching_holes and not finite_equivalences else "failed"
    return {
        "schema": "d83b3801c134-parametric-bounded-audit-v1",
        "status": status,
        "episodes": episodes,
        "settings": list(ADAPTER.DIRECTIONS),
        "demos": 3,
        "queries": 4,
        "declared_rivals": sorted(rival_failures),
        "rival_rejections": rival_failures,
        "teaching_holes": teaching_holes,
        "finite_equivalences": finite_equivalences,
        "vectors_seen": len(vector_values),
        "minimum_green_cells_30x30": minimum_30,
        "limits": "Finite seeds and declared rivals only; this is not universal uniqueness.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=20)
    args = parser.parse_args()
    report = run_audit(range(args.seeds))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "episodes": report["episodes"],
                      "teaching_holes": len(report["teaching_holes"])}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
