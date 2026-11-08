"""Matched-input native column-selection lessons for a53fa114c4a9.

The default setting preserves the approved rule: recolor the body through the
legend and crop every color-1 mask column.  The alternative uses the same
recolored body, but keeps only marked columns intersecting its largest
monochromatic 4-connected component.  Authored inputs map two checkerboard
source colors to one target color, so that component exists only after the
legend is applied.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any

HERE = Path(__file__).resolve().parent
CANONICAL = (HERE / "canonical.rkt").read_text(encoding="utf-8")
MERGED_COMPONENT = (HERE / "merged_component.rkt").read_text(encoding="utf-8")
PROGRAMS = {"explicit_mask": CANONICAL, "merged_component": MERGED_COMPONENT}
DEMO_DIMS = ((8, 10), (9, 12), (12, 14), (16, 18), (22, 24), (30, 30))
QUERY_DIMS = ((10, 13), (14, 17), (24, 28), (30, 30))
COLORS = (2, 3, 4, 5, 6, 7, 8, 9)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(settings: dict[str, Any]) -> str:
    if type(settings) is not dict:
        raise TypeError("settings must be an exact dictionary")
    if set(settings) != {"column_mode"}:
        raise ValueError("settings must name exactly column_mode")
    value = settings["column_mode"]
    if type(value) is not str or value not in PROGRAMS:
        raise ValueError("column_mode must be explicit_mask or merged_component")
    return value


def program(settings: dict[str, Any]) -> str:
    return PROGRAMS[_mode(settings)]


def _grid(value: Any) -> list[list[int]]:
    if (type(value) is not list or not 4 <= len(value) <= 30 or
            type(value[0]) is not list or not 1 <= len(value[0]) <= 30):
        raise ValueError("grid must have 4..30 rows and 1..30 columns")
    width = len(value[0])
    if any(type(row) is not list or len(row) != width or
           any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in value):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return [row[:] for row in value]


def legend_mapping(grid: list[list[int]]) -> dict[int, int]:
    source = _grid(grid)
    return {
        source[0][c]: source[1][c]
        for c in range(len(source[0]))
        if source[0][c] != 0 and source[1][c] != 0
    }


def keep_columns(grid: list[list[int]]) -> list[int]:
    source = _grid(grid)
    return [c for c, value in enumerate(source[2]) if value == 1]


def recolor_body(grid: list[list[int]]) -> list[list[int]]:
    source = _grid(grid)
    mapping = legend_mapping(source)
    return [[mapping.get(value, value) for value in row] for row in source[3:]]


def _components(body: list[list[int]]) -> list[list[tuple[int, int]]]:
    if not body or not body[0]:
        return []
    h, w = len(body), len(body[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            color = body[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and body[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(cells)
    return result


def largest_component_columns(body: list[list[int]]) -> list[int]:
    components = _components(body)
    if not components:
        return []
    winner = max(components, key=len)
    return sorted({c for _, c in winner})


def _crop(body: list[list[int]], columns: list[int]) -> list[list[int]]:
    return [[row[c] for c in columns] for row in body]


def transform(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    source = _grid(grid)
    mode = _mode(settings)
    body = recolor_body(source)
    keep = keep_columns(source)
    columns = keep
    if mode == "merged_component":
        component_columns = set(largest_component_columns(body))
        selected = [c for c in keep if c in component_columns]
        columns = selected or keep
    return _crop(body, columns)


def transform_with_raw_component(grid: list[list[int]]) -> list[list[int]]:
    """Counterfactual: choose the component before applying the legend."""
    source = _grid(grid)
    body = recolor_body(source)
    raw_body = [row[:] for row in source[3:]]
    keep = keep_columns(source)
    component_columns = set(largest_component_columns(raw_body))
    selected = [c for c in keep if c in component_columns]
    return _crop(body, selected or keep)


def _rng(seed: int, split: str, index: int) -> random.Random:
    material = f"a53fa114c4a9/column-mode-v1/{seed}/{split}/{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def _paint_rect(body: list[list[int]], top: int, left: int, height: int, width: int,
                colors: tuple[int, ...], checker: bool = False) -> None:
    for rr in range(height):
        for cc in range(width):
            body[top + rr][left + cc] = colors[(rr + cc) % len(colors)] if checker else colors[0]


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    if split not in ("train", "test"):
        raise ValueError("split must be train or test")
    dims = DEMO_DIMS if split == "train" else QUERY_DIMS
    _integer(index, 0, len(dims) - 1, "index")
    h, w = dims[index]
    body_h = h - 3
    rng = _rng(seed, split, index)
    palette = list(COLORS)
    rng.shuffle(palette)
    source_a, source_b, source_decoy, merged_target, decoy_target = palette[:5]

    main_h = max(3, min(body_h - 1 if body_h > 3 else body_h, body_h // 2 + 2))
    main_w = max(4, min(w // 2, w - 4))
    decoy_h = max(2, min(body_h, max(2, main_h // 2)))
    available = max(2, w - main_w - 2)
    decoy_w = max(2, min(available, max(2, main_w // 2)))
    main_on_left = ((index + (0 if split == "train" else 1) + rng.randrange(2)) % 2 == 0)
    if main_on_left:
        main_left, decoy_left = 0, w - decoy_w
    else:
        main_left, decoy_left = w - main_w, 0
    main_on_top = ((index + rng.randrange(2)) % 2 == 0)
    main_top = 0 if main_on_top else body_h - main_h
    decoy_top = body_h - decoy_h if main_on_top else 0

    body = [[0] * w for _ in range(body_h)]
    _paint_rect(body, main_top, main_left, main_h, main_w, (source_a, source_b), checker=True)
    _paint_rect(body, decoy_top, decoy_left, decoy_h, decoy_w, (source_decoy,))

    # A few isolated source cells broaden spatial coverage without challenging
    # either deliberately unique largest component.
    candidates = [
        (body_h - 1, w // 2),
        (0, w // 2),
        (body_h // 2, 0),
        (body_h // 2, w - 1),
    ]
    for k, (r, c) in enumerate(candidates):
        if body[r][c] == 0:
            body[r][c] = (source_a, source_b, source_decoy)[k % 3]

    main_columns = [main_left, main_left + main_w // 2, main_left + main_w - 1]
    decoy_column = decoy_left + decoy_w // 2
    gap_columns = [c for c in range(w)
                   if not (main_left <= c < main_left + main_w)
                   and not (decoy_left <= c < decoy_left + decoy_w)]
    neutral_column = gap_columns[len(gap_columns) // 2] if gap_columns else decoy_column
    keep = sorted(set(main_columns + [decoy_column, neutral_column]))

    grid = [[0] * w for _ in range(h)]
    pair_columns = (0, w // 2, w - 1)
    sources = (source_a, source_b, source_decoy)
    targets = (merged_target, merged_target, decoy_target)
    for c, src, dst in zip(pair_columns, sources, targets):
        grid[0][c] = src
        grid[1][c] = dst
    for c in keep:
        grid[2][c] = 1
    for r, row in enumerate(body, start=3):
        grid[r] = row

    recolored_columns = largest_component_columns(recolor_body(grid))
    raw_columns = largest_component_columns(body)
    if recolored_columns == raw_columns:
        raise AssertionError("authored input lost recolor-before-selection witness")
    if not set(recolored_columns) & set(keep) or not set(raw_columns) & set(keep):
        raise AssertionError("authored mask misses a causal component")
    return grid


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    _mode(settings)
    train: list[dict[str, list[list[int]]]] = []
    test: list[dict[str, list[list[int]]]] = []
    for split, count, target in (("train", demos, train), ("test", queries, test)):
        for index in range(count):
            grid = sample_input(seed, split, index)
            target.append({"input": grid, "output": transform(grid, settings)})
    return {"train": deepcopy(train), "test": deepcopy(test),
            "program_solution": program(settings)}
