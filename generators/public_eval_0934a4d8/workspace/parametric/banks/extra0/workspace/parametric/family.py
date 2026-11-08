"""Occluded off-centre mosaic family for public parent 0934a4d8."""
from __future__ import annotations

import copy
import hashlib
import json
import random
from dataclasses import dataclass

SETTINGS = ("mirrors_first", "transpose_first")
RIVALS = ("opposite_priority", "whole_grid", "raw_crop")
OCCLUDER = 8
PALETTE = (0, 1, 2, 3, 4, 5, 6, 7, 9)


def integer(value: object, lo: int, hi: int, name: str) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")
    return value


def _grid(grid: object) -> list[list[int]]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a non-empty rectangular list")
    width = len(grid[0])
    out: list[list[int]] = []
    for row in grid:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        clean: list[int] = []
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                raise ValueError("grid colors must be exact integers in [0, 9]")
            clean.append(value)
        out.append(clean)
    return out


def _axis_score(grid: list[list[int]], axis_sum: int, *, vertical: bool) -> tuple[int, int]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    overlap = 0
    conflicts = 0
    for r in range(h):
        for c in range(w):
            rr, cc = (r, axis_sum - c) if vertical else (axis_sum - r, c)
            if not (0 <= rr < h and 0 <= cc < w) or (rr, cc) == (r, c):
                continue
            key = tuple(sorted(((r, c), (rr, cc))))
            if key in seen:
                continue
            seen.add(key)
            a, b = grid[r][c], grid[rr][cc]
            if a == OCCLUDER or b == OCCLUDER:
                continue
            overlap += 1
            if a != b:
                conflicts += 1
    return conflicts, overlap


def _best_axis(grid: list[list[int]], *, vertical: bool) -> int:
    size = len(grid[0]) if vertical else len(grid)
    candidates: list[tuple[int, int]] = []
    for axis_sum in range(2 * size - 1):
        conflicts, overlap = _axis_score(grid, axis_sum, vertical=vertical)
        if conflicts == 0 and overlap:
            candidates.append((overlap, axis_sum))
    if not candidates:
        raise ValueError("no reflection axis fits the visible mosaic")
    best_overlap = max(score for score, _ in candidates)
    winners = [axis for score, axis in candidates if score == best_overlap]
    if len(winners) != 1:
        raise ValueError("reflection axis is ambiguous")
    return winners[0]


def _hole_box(grid: list[list[int]]) -> tuple[int, int, int, int, set[tuple[int, int]]]:
    cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == OCCLUDER}
    if not cells:
        raise ValueError("one color-8 occluding rectangle is required")
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    rectangle = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}
    if cells != rectangle:
        raise ValueError("color 8 must be one solid rectangle")
    return r0, r1, c0, c1, cells


def _candidate_sources(r: int, c: int, row_axis: int, col_axis: int, setting: str) -> list[tuple[int, int]]:
    mirrors = [
        (r, col_axis - c),
        (row_axis - r, c),
        (row_axis - r, col_axis - c),
    ]
    transposes = [
        (c, r),
        (col_axis - c, r),
        (c, row_axis - r),
        (col_axis - c, row_axis - r),
    ]
    return mirrors + transposes if setting == "mirrors_first" else transposes + mirrors


def analyze(grid: object, setting: str = "mirrors_first") -> dict[str, object]:
    if setting not in SETTINGS:
        raise ValueError("unknown source priority")
    g = _grid(grid)
    h, w = len(g), len(g[0])
    row_axis = _best_axis(g, vertical=False)
    col_axis = _best_axis(g, vertical=True)
    r0, r1, c0, c1, holes = _hole_box(g)
    selected: list[dict[str, object]] = []
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            source = None
            for rr, cc in _candidate_sources(r, c, row_axis, col_axis, setting):
                if 0 <= rr < h and 0 <= cc < w and (rr, cc) not in holes and g[rr][cc] != OCCLUDER:
                    source = (rr, cc)
                    break
            if source is None:
                raise ValueError("occluded cell has no visible symmetric source")
            selected.append({"target": [r, c], "source": [source[0], source[1]], "value": g[source[0]][source[1]]})
    return {
        "height": h,
        "width": w,
        "row_axis_sum": row_axis,
        "col_axis_sum": col_axis,
        "hole_box": [r0, r1, c0, c1],
        "holes": sorted(holes),
        "selected": selected,
    }


def solve(grid: object, setting: str = "mirrors_first") -> list[list[int]]:
    g = _grid(grid)
    info = analyze(g, setting)
    r0, r1, c0, c1 = info["hole_box"]
    values = {tuple(item["target"]): item["value"] for item in info["selected"]}
    return [[values[(r, c)] for c in range(c0, c1 + 1)] for r in range(r0, r1 + 1)]


def _repaired_grid(grid: object, setting: str) -> list[list[int]]:
    g = _grid(grid)
    info = analyze(g, setting)
    out = copy.deepcopy(g)
    for item in info["selected"]:
        r, c = item["target"]
        out[r][c] = item["value"]
    return out


def solve_rival(grid: object, setting: str, rival: str) -> list[list[int]]:
    if rival not in RIVALS:
        raise ValueError("unknown rival")
    if rival == "opposite_priority":
        other = "transpose_first" if setting == "mirrors_first" else "mirrors_first"
        return solve(grid, other)
    if rival == "whole_grid":
        return _repaired_grid(grid, setting)
    g = _grid(grid)
    r0, r1, c0, c1, _ = _hole_box(g)
    return [row[c0 : c1 + 1] for row in g[r0 : r1 + 1]]


def intermediate(grid: object, settings: dict[str, str] | None = None) -> dict[str, object]:
    setting = "mirrors_first" if settings is None else settings.get("source_priority")
    info = analyze(grid, setting)
    return {
        "axes": [info["row_axis_sum"], info["col_axis_sum"]],
        "hole_box": info["hole_box"],
        "selected_sources": info["selected"],
    }


def dependency() -> dict[str, str]:
    return {
        "step_a": "Infer the input's off-centre horizontal and vertical reflection axes, then choose the first visible source coordinate for every occluded cell under the episode's source-priority rule.",
        "intermediate": "The two axis sums, the occluder rectangle, and an input-specific target-to-visible-source map carrying recovered values.",
        "step_b": "Crop the occluder rectangle and render each output cell from the selected source map.",
        "why": "The crop values cannot be chosen before the axes and per-cell visible sources are inferred; changing that intermediate source map changes the final recovered patch.",
    }


def _rng(seed: int, tag: object) -> random.Random:
    material = json.dumps([seed, tag], sort_keys=True, separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(material).digest()[:16], "big"))


class _DSU:
    def __init__(self, n: int):
        self.parent = list(range(n))

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        a, b = self.find(a), self.find(b)
        if a != b:
            self.parent[b] = a


def _symmetric_base(n: int, row_axis: int, col_axis: int, rng: random.Random) -> list[list[int]]:
    dsu = _DSU(n * n)
    index = lambda r, c: r * n + c
    for r in range(n):
        for c in range(n):
            for rr, cc in ((row_axis - r, c), (r, col_axis - c)):
                if 0 <= rr < n and 0 <= cc < n:
                    dsu.union(index(r, c), index(rr, cc))
    colors: dict[int, int] = {}
    grid = [[0] * n for _ in range(n)]
    for r in range(n):
        for c in range(n):
            root = dsu.find(index(r, c))
            colors.setdefault(root, rng.choice(PALETTE))
            grid[r][c] = colors[root]
    return grid


def make_scene(seed: int, tag: object, n: int, *, stress: bool = False) -> list[list[int]]:
    integer(seed, 0, 2**63 - 1, "seed")
    integer(n, 10, 30, "size")
    rng = _rng(seed, [tag, n, stress])
    for attempt in range(300):
        row_axis = n - 1 + rng.choice((-2, -1, 0, 1, 2))
        col_axis = n - 1 + rng.choice((-2, -1, 0, 1, 2))
        base = _symmetric_base(n, row_axis, col_axis, rng)
        shapes = [(2, 2), (2, 3), (3, 2), (3, 3)]
        if stress:
            shapes.extend(((3, 4), (4, 3)))
        rng.shuffle(shapes)
        candidates = [(r, c, rh, cw) for rh, cw in shapes for r in range(1, n - rh) for c in range(1, n - cw)]
        rng.shuffle(candidates)
        for r0, c0, rh, cw in candidates[:500]:
            holes = {(r, c) for r in range(r0, r0 + rh) for c in range(c0, c0 + cw)}
            g = copy.deepcopy(base)
            for r, c in holes:
                g[r][c] = OCCLUDER
            try:
                if _best_axis(g, vertical=False) != row_axis or _best_axis(g, vertical=True) != col_axis:
                    continue
                canonical = solve(g, "mirrors_first")
                alternate = solve(g, "transpose_first")
                if canonical == alternate:
                    continue
                return g
            except ValueError:
                continue
    raise RuntimeError("could not sample an identifiable occluded mosaic")


def _shapes() -> tuple[list[int], list[int]]:
    return [12, 14, 16, 18, 20, 22], [15, 19, 24, 30]


def generate(seed: int, settings: dict[str, str], demos: int, queries: int) -> dict[str, object]:
    integer(seed, 0, 2**63 - 1, "seed")
    integer(demos, 2, 6, "demos")
    integer(queries, 1, 4, "queries")
    if type(settings) is not dict or set(settings) != {"source_priority"} or settings["source_priority"] not in SETTINGS:
        raise ValueError("settings must be exactly source_priority=mirrors_first|transpose_first")
    setting = settings["source_priority"]
    demo_sizes, query_sizes = _shapes()

    def pair(index: int, n: int, query: bool) -> dict[str, object]:
        grid = make_scene(seed, ["query" if query else "demo", index], n, stress=query and index == 3)
        return {"input": grid, "output": solve(grid, setting)}

    train = [pair(i, demo_sizes[i], False) for i in range(demos)]
    bank = [pair(i, n, True) for i, n in enumerate(query_sizes)]
    return {"train": train, "test": copy.deepcopy(bank[:queries]), "private_query_bank": bank}


def self_check(grid: object) -> list[str]:
    issues: list[str] = []
    try:
        g = _grid(grid)
        analyze(g, "mirrors_first")
        analyze(g, "transpose_first")
        if solve(g, "mirrors_first") == solve(g, "transpose_first"):
            issues.append("source-priority settings do not differ")
    except Exception as exc:
        issues.append(str(exc))
    return issues
