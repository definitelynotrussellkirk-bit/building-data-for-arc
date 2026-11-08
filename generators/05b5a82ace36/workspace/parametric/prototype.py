"""Deterministic two-setting template-selector family for 05b5a82ace36."""
from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path

TASK_ID = "05b5a82ace36"
HOME = Path(__file__).resolve().parent
SELECTORS = ("largest", "smallest")
DEMO_PROFILES = (
    (12, 14, 7, 3, 2),
    (14, 16, 9, 4, 2),
    (16, 18, 11, 5, 3),
    (19, 21, 13, 6, 3),
    (23, 25, 15, 7, 4),
    (27, 29, 17, 8, 4),
)
QUERY_PROFILES = (
    (13, 15, 8, 3, 2),
    (17, 19, 10, 4, 3),
    (24, 26, 14, 6, 3),
    (30, 30, 18, 8, 4),
)


def _integer(value: int, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def _settings(value: dict) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"template_selector"}:
        raise ValueError("settings must contain exactly template_selector")
    selector = value["template_selector"]
    if type(selector) is not str or selector not in SELECTORS:
        raise ValueError(f"template_selector must be one of {SELECTORS}")
    return {"template_selector": selector}


def program(settings: dict) -> str:
    selected = _settings(settings)
    return (HOME / "rules" / f"{selected['template_selector']}.rkt").read_text(encoding="utf-8")


def _rng(seed: int, split: str, index: int) -> random.Random:
    material = f"{TASK_ID}:{seed}:{split}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(material).digest()[:16], "big"))


def _snake(size: int, width: int, *, transpose: bool, mirror: bool) -> list[tuple[int, int]]:
    width = max(2, min(width, size))
    cells: list[tuple[int, int]] = []
    for index in range(size):
        row, offset = divmod(index, width)
        col = offset if row % 2 == 0 else width - 1 - offset
        cells.append((row, col))
    if transpose:
        cells = [(c, r) for r, c in cells]
    if mirror:
        max_col = max(c for _, c in cells)
        cells = [(r, max_col - c) for r, c in cells]
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    normalized = sorted((r - top, c - left) for r, c in cells)
    if len(set(normalized)) != size:
        raise ValueError("shape construction duplicated a cell")
    return normalized


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int]:
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _corner_position(
    grid_h: int, grid_w: int, shape_h: int, shape_w: int, corner: str
) -> tuple[int, int]:
    top = 1 if corner[0] == "t" else grid_h - shape_h - 2
    left = 1 if corner[1] == "l" else grid_w - shape_w - 2
    if top < 0 or left < 0:
        raise ValueError("profile cannot place template in requested corner")
    return top, left


def _paint_shape(
    grid: list[list[int]], cells: list[tuple[int, int]], top: int, left: int, rng: random.Random
) -> None:
    for index, (dr, dc) in enumerate(cells):
        rr, cc = top + dr, left + dc
        if not (0 <= rr < len(grid) and 0 <= cc < len(grid[0])):
            raise ValueError("template placement escaped grid")
        if grid[rr][cc] != 0:
            raise ValueError("template placement overlapped content")
        grid[rr][cc] = (2, 4)[(index + rng.randrange(2)) % 2]


def _anchor_candidates(h: int, w: int) -> list[tuple[int, int]]:
    return [
        (h // 2, w // 2),
        (h - 1, w - 1),
        (h // 2, 1),
        (1, w // 2),
    ]


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    if split == "demo":
        if type(index) is not int or not 0 <= index < len(DEMO_PROFILES):
            raise ValueError("demo index outside supported profiles")
        h, w, large_size, small_size, anchor_count = DEMO_PROFILES[index]
    elif split == "query":
        if type(index) is not int or not 0 <= index < len(QUERY_PROFILES):
            raise ValueError("query index outside supported profiles")
        h, w, large_size, small_size, anchor_count = QUERY_PROFILES[index]
    else:
        raise ValueError("split must be demo or query")

    rng = _rng(seed, split, index)
    large = _snake(
        large_size,
        3 + rng.randrange(3),
        transpose=bool(rng.randrange(2)),
        mirror=bool(rng.randrange(2)),
    )
    small = _snake(
        small_size,
        2 + rng.randrange(2),
        transpose=bool(rng.randrange(2)),
        mirror=bool(rng.randrange(2)),
    )
    lh, lw = _bbox(large)
    sh, sw = _bbox(small)
    grid = [[0 for _ in range(w)] for _ in range(h)]

    lesson_rng = _rng(seed, f"{split}-lesson", index // 2)
    large_corner, small_corner = (("tl", "br"), ("tr", "bl"))[lesson_rng.randrange(2)]
    if lesson_rng.randrange(2) ^ (index % 2):
        large_corner, small_corner = small_corner, large_corner
    large_top, large_left = _corner_position(h, w, lh, lw, large_corner)
    small_top, small_left = _corner_position(h, w, sh, sw, small_corner)
    large_absolute = {(large_top + r, large_left + c) for r, c in large}
    small_absolute = {(small_top + r, small_left + c) for r, c in small}
    if any(abs(r - rr) + abs(c - cc) <= 1
           for r, c in large_absolute for rr, cc in small_absolute):
        raise ValueError("profile does not separate template components")
    _paint_shape(grid, large, large_top, large_left, rng)
    _paint_shape(grid, small, small_top, small_left, rng)

    colors = rng.sample((6, 7, 8, 9), anchor_count)
    anchors: list[tuple[int, int]] = []
    for candidate in _anchor_candidates(h, w):
        if len(anchors) == anchor_count:
            break
        r, c = candidate
        if grid[r][c] == 0 and candidate not in anchors:
            anchors.append(candidate)
    if len(anchors) != anchor_count:
        raise ValueError("could not place requested anchor profile")
    for (r, c), color in zip(anchors, colors):
        grid[r][c] = color
    return grid


def _strict_grid(grid: list[list[int]]) -> tuple[int, int]:
    if (type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]
            or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)
            or any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row)):
        raise ValueError("grid must be rectangular exact integer ARC colors")
    h, w = len(grid), len(grid[0])
    if not 1 <= h <= 30 or not 1 <= w <= 30:
        raise ValueError("grid dimensions must be in 1..30")
    return h, w


def _components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] not in {2, 4} or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            component: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                component.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] in {2, 4}):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            if len(component) > 1:
                result.append(component)
    return result


def _normalize(cells: list[tuple[int, int]]) -> list[tuple[int, int]]:
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return sorted((r - top, c - left) for r, c in cells)


def transform(grid: list[list[int]], settings: dict) -> list[list[int]]:
    selector = _settings(settings)["template_selector"]
    h, w = _strict_grid(grid)
    components = _components(grid)
    if not components:
        raise ValueError("no multi-cell 2/4 template component")
    sizes = sorted(len(component) for component in components)
    if len(sizes) < 2 or sizes[0] == sizes[-1]:
        raise ValueError("family inputs require distinct largest and smallest templates")
    source = (max if selector == "largest" else min)(components, key=len)
    normalized = _normalize(source)
    out = [[0 for _ in range(w)] for _ in range(h)]
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color not in {6, 7, 8, 9}:
                continue
            for dr, dc in normalized:
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w:
                    out[rr][cc] = color
    return out


def generate(seed: int, settings: dict, demos: int = 3, queries: int = 4) -> dict:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    selected = _settings(settings)
    train: list[dict] = []
    test: list[dict] = []
    for split, count, target in (("demo", demos, train), ("query", queries, test)):
        for index in range(count):
            grid = sample_input(seed, split, index)
            target.append({"input": grid, "output": transform(grid, selected)})
    fingerprints = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(fingerprints) != len(set(fingerprints)):
        raise ValueError("episode inputs must be distinct")
    return {
        "schema": f"{TASK_ID}-template-selector-parametric-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": selected,
        "train": train,
        "test": test,
        "program_solution": program(selected),
    }
