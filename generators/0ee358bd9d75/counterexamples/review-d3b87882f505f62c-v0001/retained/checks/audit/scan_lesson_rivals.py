"""Reproduce lesson-level shortcut rates for the two read-only audit targets.

Run from packet root:
  python3 run_with_racket.py python3 ../checks/audit/scan_lesson_rivals.py
The wrapper executes this with repo/ as cwd.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def load(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, Path(path))
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(1, h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                x, y = stack.pop()
                cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    a, b = x + dx, y + dy
                    if (
                        1 <= a < h
                        and 0 <= b < w
                        and grid[a][b] == color
                        and (a, b) not in seen
                    ):
                        seen.add((a, b))
                        stack.append((a, b))
            result.append((color, cells))
    return result


def crop(color, cells):
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    out = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
    for r, c in cells:
        out[r - r0][c - c0] = color
    return out


def hole_count(grid):
    h, w = len(grid), len(grid[0])
    outside = set()
    stack = []
    for r in range(h):
        for c in range(w):
            if (r in (0, h - 1) or c in (0, w - 1)) and grid[r][c] == 0:
                outside.add((r, c))
                stack.append((r, c))
    while stack:
        r, c = stack.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            p = (r + dr, c + dc)
            if (
                0 <= p[0] < h
                and 0 <= p[1] < w
                and grid[p[0]][p[1]] == 0
                and p not in outside
            ):
                outside.add(p)
                stack.append(p)
    unseen = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 0 and (r, c) not in outside
    }
    count = 0
    while unseen:
        count += 1
        stack = [unseen.pop()]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p = (r + dr, c + dc)
                if p in unseen:
                    unseen.remove(p)
                    stack.append(p)
    return count


def identity_rival_147(grid):
    candidates = []
    for color, cells in components(grid):
        shape = crop(color, cells)
        if hole_count(shape) == 1:
            candidates.append(shape)
    assert len(candidates) == 1
    shape = candidates[0]
    return [
        [value for value in row for _ in range(2)]
        for row in shape
        for _ in range(2)
    ]


def first_cell_rival_0ee(gen, grid):
    info = gen._analysis(grid)
    values = []
    for section in info["sections"]:
        r0, r1, c0, c1 = section["span"]
        values.append(
            next(
                grid[r][c]
                for r in range(r0, r1)
                for c in range(c0, c1)
                if grid[r][c] != 0
            )
        )
    width = len(info["col_spans"])
    return [values[i : i + width] for i in range(0, len(values), width)]


def transform_147(grid, code):
    if code == 1:
        return grid
    if code == 2:
        return [list(row) for row in zip(*grid[::-1])]
    if code == 3:
        return [row[::-1] for row in grid[::-1]]
    if code == 4:
        return [list(row) for row in zip(*grid)][::-1]
    if code == 5:
        return [row[::-1] for row in grid]
    if code == 6:
        return grid[::-1]
    raise ValueError(code)


def true_147(grid):
    code = next(value for value in grid[0] if value != 0)
    candidates = []
    for color, cells in components(grid):
        shape = crop(color, cells)
        if hole_count(shape) == 1:
            candidates.append(shape)
    assert len(candidates) == 1
    shape = transform_147(candidates[0], code)
    return [
        [value for value in row for _ in range(2)]
        for row in shape
        for _ in range(2)
    ]


def main():
    g147 = load("generators/147c2b92e5c1/generator.py", "audit_147")
    g0ee = load("generators/0ee358bd9d75/generator.py", "audit_0ee")
    result = {
        "schema": "arcpuzzles-audit-rival-scan-v1",
        "seed_range": "0..999",
        "sample_indices": "0..4",
        "147c2b92e5c1": {"rival": "always_identity_transform", "bands": {}},
        "0ee358bd9d75": {"rival": "first_nonzero_cell_per_section", "bands": {}},
    }
    for band in ("easy", "medium", "hard"):
        survivors_147 = []
        survivors_0ee = []
        fit_examples_0ee = 0
        single_examples_0ee = 0
        for seed in range(1000):
            fits_147 = []
            fits_0ee = []
            for index in range(5):
                grid_147 = g147.generate(seed, index, difficulty=band)
                fits_147.append(identity_rival_147(grid_147) == true_147(grid_147))
                grid_0ee = g0ee.generate(seed, index, difficulty=band)
                fit_0ee = first_cell_rival_0ee(g0ee, grid_0ee) == g0ee.rule_mirror(grid_0ee)
                fits_0ee.append(fit_0ee)
                fit_examples_0ee += int(fit_0ee)
                info = g0ee._analysis(grid_0ee)
                single_examples_0ee += int(
                    all(len(section["nonzero"]) == 1 for section in info["sections"])
                )
            if all(fits_147):
                survivors_147.append(seed)
            if all(fits_0ee):
                survivors_0ee.append(seed)
        result["147c2b92e5c1"]["bands"][band] = {
            "surviving_lessons": len(survivors_147),
            "total_lessons": 1000,
            "first_survivors": survivors_147[:20],
        }
        result["0ee358bd9d75"]["bands"][band] = {
            "surviving_lessons": len(survivors_0ee),
            "total_lessons": 1000,
            "fitting_examples": fit_examples_0ee,
            "total_examples": 5000,
            "single_color_examples": single_examples_0ee,
            "first_survivors": survivors_0ee[:20],
        }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
