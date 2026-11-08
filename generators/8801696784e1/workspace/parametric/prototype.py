"""Deterministic two-setting object-selector family for 8801696784e1."""
from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path
from typing import Iterable

TASK_ID = "8801696784e1"
HOME = Path(__file__).resolve().parent
OBJECT_KINDS = ("symmetric", "asymmetric")
DEMO_PROFILES = (
    (11, 13, 3, 5),
    (13, 15, 5, 5),
    (15, 17, 5, 7),
    (18, 20, 7, 7),
    (22, 24, 7, 11),
    (26, 28, 9, 13),
)
QUERY_PROFILES = (
    (12, 14, 3, 5),
    (16, 18, 5, 7),
    (24, 26, 9, 11),
    (30, 30, 11, 13),
)


def _integer(value: int, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def _settings(value: dict) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"object_kind"}:
        raise ValueError("settings must contain exactly object_kind")
    kind = value["object_kind"]
    if type(kind) is not str or kind not in OBJECT_KINDS:
        raise ValueError(f"object_kind must be one of {OBJECT_KINDS}")
    return {"object_kind": kind}


def program(settings: dict) -> str:
    selected = _settings(settings)
    return (HOME / "rules" / f"{selected['object_kind']}.rkt").read_text(encoding="utf-8")


def _rng(seed: int, split: str, index: int) -> random.Random:
    material = f"{TASK_ID}:{seed}:{split}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(material).digest()[:16], "big"))


def _frame(height: int, width: int, variant: int) -> set[tuple[int, int]]:
    cells = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if r in {0, height - 1} or c in {0, width - 1}
    }
    if variant in {1, 3}:
        cells.update((height // 2, c) for c in range(width))
    if variant in {2, 3}:
        cells.update((r, width // 2) for r in range(height))
    return cells


def _asymmetric(height: int, width: int, variant: int) -> set[tuple[int, int]]:
    if variant >= 2:
        # A dense connected object makes the asymmetric object larger than the
        # frame in some episodes, so component size cannot stand in for symmetry.
        cells = {(r, c) for r in range(height) for c in range(width)}
        cells.remove((0, width - 1))
        if variant == 3 and height > 2:
            cells.remove((1, width - 1))
        return cells
    cells = {(r, 0) for r in range(height)}
    cells.update((height - 1, c) for c in range(width))
    if height > 2 and width > 2:
        cells.add((1, 1))
    if variant == 1 and height > 3:
        cells.add((2, 1))
    return cells


def _corner_position(
    grid_h: int, grid_w: int, shape_h: int, shape_w: int, corner: str
) -> tuple[int, int]:
    top = 1 if corner[0] == "t" else grid_h - shape_h - 2
    left = 1 if corner[1] == "l" else grid_w - shape_w - 2
    if top < 0 or left < 0:
        raise ValueError("profile cannot place shape in requested corner")
    return top, left


def _paint(grid: list[list[int]], cells: Iterable[tuple[int, int]], top: int, left: int, color: int) -> None:
    for r, c in cells:
        rr, cc = top + r, left + c
        if not (0 <= rr < len(grid) and 0 <= cc < len(grid[0])):
            raise ValueError("shape placement escaped the grid")
        if grid[rr][cc] != 0:
            raise ValueError("shape placement overlapped existing content")
        grid[rr][cc] = color


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    if split == "demo":
        if type(index) is not int or not 0 <= index < len(DEMO_PROFILES):
            raise ValueError("demo index outside supported profiles")
        h, w, sh, sw = DEMO_PROFILES[index]
    elif split == "query":
        if type(index) is not int or not 0 <= index < len(QUERY_PROFILES):
            raise ValueError("query index outside supported profiles")
        h, w, sh, sw = QUERY_PROFILES[index]
    else:
        raise ValueError("split must be demo or query")
    rng = _rng(seed, split, index)
    lesson_rng = _rng(seed, f"{split}-lesson", index // 2)
    dense_asymmetric = bool(lesson_rng.randrange(2) ^ (index % 2))
    symmetric = _frame(sh, sw, 0 if dense_asymmetric else rng.randrange(4))
    ah, aw = sh, sw
    asymmetric_variant = (2 if dense_asymmetric else 0) + rng.randrange(2)
    asymmetric = _asymmetric(ah, aw, asymmetric_variant)
    colors = rng.sample((4, 5, 6, 7, 8, 9), 2)
    grid = [[0 for _ in range(w)] for _ in range(h)]
    sym_corner, asym_corner = (("tl", "br"), ("tr", "bl"))[lesson_rng.randrange(2)]
    if lesson_rng.randrange(2) ^ (index % 2):
        sym_corner, asym_corner = asym_corner, sym_corner
    sym_top, sym_left = _corner_position(h, w, sh, sw, sym_corner)
    asym_top, asym_left = _corner_position(h, w, ah, aw, asym_corner)
    _paint(grid, symmetric, sym_top, sym_left, colors[0])
    _paint(grid, asymmetric, asym_top, asym_left, colors[1])
    grid[h - 1][w - 1] = 1 + rng.randrange(3)
    return grid


def _components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    work = copy.deepcopy(grid)
    work[h - 1][w - 1] = 0
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if work[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            component: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                component.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and work[nr][nc] != 0
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(component)
    return result


def _crop(grid: list[list[int]], cells: list[tuple[int, int]]) -> list[list[int]]:
    r0 = min(r for r, _ in cells); r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells); c1 = max(c for _, c in cells)
    return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]


def _both_symmetric(crop: list[list[int]]) -> bool:
    return crop == [list(reversed(row)) for row in crop] and crop == list(reversed(crop))


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*reversed(grid))]


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in reversed(grid)]


def _rotate_ccw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in reversed(list(zip(*grid)))]


def _upscale2(grid: list[list[int]]) -> list[list[int]]:
    out: list[list[int]] = []
    for row in grid:
        expanded = [value for value in row for _ in range(2)]
        out.extend([expanded[:], expanded[:]])
    return out


def transform(grid: list[list[int]], settings: dict) -> list[list[int]]:
    selected = _settings(settings)
    if (type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]
            or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)
            or any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row)):
        raise ValueError("grid must be rectangular exact integer ARC colors")
    code = grid[-1][-1]
    if code not in {1, 2, 3}:
        raise ValueError("bottom-right code must be 1, 2, or 3")
    candidates = []
    for component in _components(grid):
        crop = _crop(grid, component)
        if _both_symmetric(crop) == (selected["object_kind"] == "symmetric"):
            candidates.append((len(component), crop))
    if not candidates:
        raise ValueError("selected object kind is absent")
    crop = max(candidates, key=lambda item: item[0])[1]
    if code == 1:
        mapped = _rotate_cw(crop)
    elif code == 2:
        mapped = _rotate_180(crop)
    else:
        mapped = _rotate_ccw(crop)
    return _upscale2(mapped)


def generate(seed: int, settings: dict, demos: int = 3, queries: int = 4) -> dict:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    selected = _settings(settings)
    train = []
    test = []
    for split, count, target in (("demo", demos, train), ("query", queries, test)):
        for index in range(count):
            grid = sample_input(seed, split, index)
            target.append({"input": grid, "output": transform(grid, selected)})
    fingerprints = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(fingerprints) != len(set(fingerprints)):
        raise ValueError("episode inputs must be distinct")
    return {
        "schema": f"{TASK_ID}-object-kind-parametric-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": selected,
        "train": train,
        "test": test,
        "program_solution": program(selected),
    }
