"""Matched-input parametric family for c1b80aa665e4.

The canonical setting recolors every orthogonally isolated foreground cell to 9.
The alternate first finds the unique largest non-singleton component, retains its
input-derived color, and recolors only isolated cells of that color.  The retained
color is therefore a real selector consumed by the later recoloring step.
"""
from __future__ import annotations

import copy
from collections import Counter
import hashlib
from pathlib import Path
import random
from typing import Callable, Iterable

HERE = Path(__file__).resolve().parent
POLICIES = ("all_isolated", "largest_cluster_color")
PROGRAMS = {
    "all_isolated": (HERE / "canonical.rkt").read_text(encoding="utf-8"),
    "largest_cluster_color": (HERE / "largest_cluster_color.rkt").read_text(encoding="utf-8"),
}
Grid = list[list[int]]
Rival = Callable[[Grid], Grid]

_A7 = ((0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2))
_B4 = ((0, 0), (0, 1), (1, 0), (1, 1))
_B4_ALT = ((0, 0), (1, 0), (2, 0), (2, 1))
_C2 = ((0, 0), (0, 1))
_D3 = ((0, 0), (1, 0), (1, 1))


def _integer(value, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def policy(settings) -> str:
    if type(settings) is not dict or set(settings) != {"isolation_policy"}:
        raise ValueError("settings must contain exactly isolation_policy")
    value = settings["isolation_policy"]
    if type(value) is not str or value not in POLICIES:
        raise ValueError(f"isolation_policy must be one of {POLICIES!r}")
    return value


def program(settings) -> str:
    return PROGRAMS[policy(settings)]


def _components(grid: Grid) -> tuple[tuple[tuple[int, int], ...], ...]:
    foreground = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    result = []
    while foreground:
        start = min(foreground)
        foreground.remove(start)
        cells = [start]
        stack = [start]
        while stack:
            r, c = stack.pop()
            for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nxt in foreground:
                    foreground.remove(nxt)
                    cells.append(nxt)
                    stack.append(nxt)
        result.append(tuple(sorted(cells)))
    return tuple(sorted(result, key=lambda cells: cells[0]))


def _component_color(grid: Grid, cells: Iterable[tuple[int, int]]) -> int:
    colors = {grid[r][c] for r, c in cells}
    if len(colors) != 1:
        raise ValueError("components must be monochrome in the admitted grammar")
    return next(iter(colors))


def _parse(grid) -> dict[str, object]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty lists")
    width = len(grid[0])
    if len(grid) > 30 or width > 30 or any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular and at most 30x30")
    if any(type(value) is not int or not 0 <= value <= 8 for row in grid for value in row):
        raise ValueError("input cells must be exact integer colors 0..8")
    components = _components(grid)
    clusters = tuple(cells for cells in components if len(cells) > 1)
    isolated = tuple(cells[0] for cells in components if len(cells) == 1)
    if len(clusters) < 4 or len(isolated) < 5:
        raise ValueError("scene needs at least four clusters and five isolated cells")
    colors = {cells: _component_color(grid, cells) for cells in components}
    largest_size = max(map(len, clusters))
    largest = [cells for cells in clusters if len(cells) == largest_size]
    if len(largest) != 1:
        raise ValueError("largest non-singleton component must be unique")
    anchor = largest[0]
    anchor_color = colors[anchor]
    if not any(grid[r][c] == anchor_color for r, c in isolated):
        raise ValueError("scene needs an isolated cell matching the largest component color")
    if not any(grid[r][c] != anchor_color for r, c in isolated):
        raise ValueError("scene needs a non-anchor isolated cell")
    aggregate = Counter()
    for cells in clusters:
        aggregate[colors[cells]] += len(cells)
    most_cluster_cells_color = max(sorted(aggregate), key=lambda color: aggregate[color])
    smallest = min(clusters, key=lambda cells: (len(cells), cells[0]))
    return {
        "height": len(grid),
        "width": width,
        "components": components,
        "clusters": clusters,
        "isolated": isolated,
        "colors": colors,
        "anchor": anchor,
        "anchor_color": anchor_color,
        "largest_size": largest_size,
        "largest_component_unique": True,
        "first_cluster_color": colors[clusters[0]],
        "last_cluster_color": colors[clusters[-1]],
        "smallest_cluster_color": colors[smallest],
        "most_cluster_cells_color": most_cluster_cells_color,
        "cluster_colors": frozenset(colors[cells] for cells in clusters),
    }


def _solve_selected_color(grid: Grid, selected_color: int | None, *, invert: bool = False) -> Grid:
    parsed = _parse(grid)
    output = copy.deepcopy(grid)
    for r, c in parsed["isolated"]:
        matches = selected_color is None or grid[r][c] == selected_color
        if invert:
            matches = not matches
        if matches:
            output[r][c] = 9
    return output


def solve(grid: Grid, selected_policy: str) -> Grid:
    if selected_policy not in POLICIES:
        raise ValueError(f"unknown policy {selected_policy!r}")
    parsed = _parse(grid)
    selected = None if selected_policy == "all_isolated" else int(parsed["anchor_color"])
    return _solve_selected_color(grid, selected)


def solve_with_smallest_cluster_color(grid: Grid) -> Grid:
    return _solve_selected_color(grid, int(_parse(grid)["smallest_cluster_color"]))


def describe_case(grid: Grid) -> dict[str, object]:
    parsed = _parse(grid)
    return {
        "height": parsed["height"],
        "width": parsed["width"],
        "cluster_sizes": [len(cells) for cells in parsed["clusters"]],
        "isolated_count": len(parsed["isolated"]),
        "anchor_color": parsed["anchor_color"],
        "largest_size": parsed["largest_size"],
        "largest_component_unique": parsed["largest_component_unique"],
        "first_cluster_color": parsed["first_cluster_color"],
        "last_cluster_color": parsed["last_cluster_color"],
        "smallest_cluster_color": parsed["smallest_cluster_color"],
        "most_cluster_cells_color": parsed["most_cluster_cells_color"],
    }


def _selector_rival(key: str) -> Rival:
    return lambda grid: _solve_selected_color(grid, int(_parse(grid)[key]))


def _any_cluster_color(grid: Grid) -> Grid:
    parsed = _parse(grid)
    output = copy.deepcopy(grid)
    for r, c in parsed["isolated"]:
        if grid[r][c] in parsed["cluster_colors"]:
            output[r][c] = 9
    return output


def _non_anchor(grid: Grid) -> Grid:
    parsed = _parse(grid)
    return _solve_selected_color(grid, int(parsed["anchor_color"]), invert=True)


def rivals_for(selected_policy: str) -> dict[str, Rival]:
    if selected_policy not in POLICIES:
        raise ValueError(selected_policy)
    rivals: dict[str, Rival] = {
        "other_admitted_setting": lambda grid: solve(
            grid,
            "largest_cluster_color" if selected_policy == "all_isolated" else "all_isolated",
        ),
        "first_cluster_color": _selector_rival("first_cluster_color"),
        "last_cluster_color": _selector_rival("last_cluster_color"),
        "smallest_cluster_color": _selector_rival("smallest_cluster_color"),
        "most_cluster_cells_color": _selector_rival("most_cluster_cells_color"),
        "any_cluster_color": _any_cluster_color,
        "all_non_anchor_isolates": _non_anchor,
    }
    for color in range(1, 9):
        rivals[f"fixed_color_{color}"] = lambda grid, color=color: _solve_selected_color(grid, color)
    return rivals


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"c1b80aa665e4:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _colors(seed: int, split: str, index: int) -> dict[str, int]:
    base = (seed * 3 + index * 2 + (0 if split == "demo" else 3)) % 8
    rotated = [1 + ((base + offset) % 8) for offset in range(8)]
    return {"A": rotated[0], "B": rotated[2], "C": rotated[4], "D": rotated[6], "E": rotated[1]}


def _candidate_cells(shape, top: int, left: int) -> set[tuple[int, int]]:
    return {(top + r, left + c) for r, c in shape}


def _can_place(grid: Grid, cells: set[tuple[int, int]]) -> bool:
    height, width = len(grid), len(grid[0])
    if any(not (0 <= r < height and 0 <= c < width) or grid[r][c] != 0 for r, c in cells):
        return False
    for r, c in cells:
        for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if nxt not in cells and 0 <= nxt[0] < height and 0 <= nxt[1] < width and grid[nxt[0]][nxt[1]] != 0:
                return False
    return True


def _paint(grid: Grid, cells: set[tuple[int, int]], color: int) -> None:
    if not _can_place(grid, cells):
        raise ValueError("component placement collision")
    for r, c in cells:
        grid[r][c] = color


def _place_shape(
    grid: Grid,
    shape,
    color: int,
    rng: random.Random,
    *,
    row_min: int = 0,
    row_max: int | None = None,
) -> set[tuple[int, int]]:
    shape_h = max(r for r, _ in shape) + 1
    shape_w = max(c for _, c in shape) + 1
    max_top = len(grid) - shape_h if row_max is None else min(row_max, len(grid) - shape_h)
    candidates = [
        (top, left)
        for top in range(row_min, max_top + 1)
        for left in range(0, len(grid[0]) - shape_w + 1)
    ]
    rng.shuffle(candidates)
    for top, left in candidates:
        cells = _candidate_cells(shape, top, left)
        if _can_place(grid, cells):
            _paint(grid, cells, color)
            return cells
    raise ValueError("could not place component")


def _place_isolates(grid: Grid, labels: list[str], colors: dict[str, int], rng: random.Random) -> None:
    candidates = [(r, c) for r in range(len(grid)) for c in range(len(grid[0]))]
    rng.shuffle(candidates)
    for label in labels:
        for index, cell in enumerate(candidates):
            if _can_place(grid, {cell}):
                _paint(grid, {cell}, colors[label])
                candidates.pop(index)
                break
        else:
            raise ValueError("could not place isolated cell")


def _small_scene(seed: int, split: str, index: int) -> Grid:
    rng = _rng(seed, split, index)
    colors = _colors(seed, split, index)
    height = 12 + ((index + (0 if split == "demo" else 1)) % 3)
    width = 14 + ((2 * index + (0 if split == "demo" else 1)) % 3)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    if split == "demo" and index == 0:
        _place_shape(grid, _B4, colors["B"], rng, row_min=0, row_max=0)
        _place_shape(grid, _C2, colors["C"], rng, row_min=3, row_max=4)
        _place_shape(grid, _B4_ALT, colors["B"], rng, row_min=5, row_max=6)
        _place_shape(grid, _D3, colors["D"], rng, row_min=7, row_max=8)
        _place_shape(grid, _A7, colors["A"], rng, row_min=height - 3, row_max=height - 3)
    elif split == "demo" and index == 1:
        _place_shape(grid, _A7, colors["A"], rng, row_min=0, row_max=0)
        _place_shape(grid, _B4, colors["B"], rng, row_min=4, row_max=4)
        _place_shape(grid, _C2, colors["C"], rng, row_min=6, row_max=7)
        _place_shape(grid, _D3, colors["D"], rng, row_min=8, row_max=8)
        _place_shape(grid, _B4_ALT, colors["B"], rng, row_min=height - 3, row_max=height - 3)
    else:
        for shape, label in ((_A7, "A"), (_B4, "B"), (_B4_ALT, "B"), (_C2, "C"), (_D3, "D")):
            _place_shape(grid, shape, colors[label], rng)
    _place_isolates(grid, ["A", "A", "B", "C", "D", "E", "E"], colors, rng)
    _parse(grid)
    return grid


def _large_scene(seed: int) -> Grid:
    colors = _colors(seed, "query", 3)
    grid = [[0 for _ in range(30)] for _ in range(30)]
    components = [
        ({(r, c) for r in range(13, 16) for c in range(13, 17)}, "A"),
        ({(0, c) for c in range(2, 9)}, "B"),
        ({(r, 29) for r in range(20, 27)}, "B"),
        ({(4, 24), (4, 25)}, "C"),
        ({(24, 0), (25, 0), (26, 0), (26, 1), (26, 2)}, "D"),
        ({(8, 3), (8, 4), (9, 3), (9, 4)}, "E"),
        ({(18, 5), (18, 6), (18, 7)}, "D"),
    ]
    for cells, label in components:
        _paint(grid, set(cells), colors[label])
    labels = ["A", "A", "B", "C", "D", "E"]
    for r in range(30):
        start = (7 * r + 11) % 30
        for delta in range(30):
            cell = (r, (start + delta) % 30)
            if _can_place(grid, {cell}):
                _paint(grid, {cell}, colors[labels[r % len(labels)]])
                break
        else:
            raise ValueError(f"could not place spread isolate in row {r}")
    _parse(grid)
    return grid


def _pair(seed: int, split: str, index: int, selected_policy: str) -> dict[str, Grid]:
    grid = _large_scene(seed) if split == "query" and index == 3 else _small_scene(seed, split, index)
    return {"input": grid, "output": solve(grid, selected_policy)}


def generate(seed, settings, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    selected_policy = policy(settings)
    return {
        "train": [_pair(seed, "demo", index, selected_policy) for index in range(demos)],
        "test": [_pair(seed, "query", index, selected_policy) for index in range(queries)],
        "program_solution": PROGRAMS[selected_policy],
    }


def public_turn(episode, query_index=0):
    if type(query_index) is not int or query_index < 0:
        raise ValueError("query_index must be a nonnegative integer")
    if not isinstance(episode, dict) or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train/test lists")
    if query_index >= len(episode["test"]):
        raise ValueError("query_index is outside the retained queries")
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }
