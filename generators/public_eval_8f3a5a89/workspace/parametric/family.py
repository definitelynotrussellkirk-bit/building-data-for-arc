"""Authoring family for ARC public parent 8f3a5a89.

The canonical rule outlines the *outer* contour of the seed-reachable empty
region.  Enclosed obstacles are filled for contour purposes, so their inner
rims are not outlined.  The alternate setting leaves those holes outside the
boundary domain and therefore outlines them as well.
"""
from __future__ import annotations

from collections import deque
import copy
import hashlib
import json
import random
from typing import Iterable

BG = 8
WALL = 1
SEED = 6
OUTLINE = 7
SETTINGS = ("outer_only", "include_holes")
RIVALS = (
    "opposite_scope",
    "grid_edge_only",
    "keep_all_input",
    "erase_holes",
    "paint_region",
    "paint_walls",
    "drop_seed",
)

D4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
D8 = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
           if (dr, dc) != (0, 0))


def integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}]")
    return value


def _grid(grid: object) -> list[list[int]]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    w = len(grid[0])
    if any(type(row) is not list or len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("grid cells must be integers 0..9")
    return grid


def _components(cells: Iterable[tuple[int, int]], deltas=D4) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    out: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        comp = {start}
        q = deque([start])
        while q:
            r, c = q.popleft()
            for dr, dc in deltas:
                p = (r + dr, c + dc)
                if p in remaining:
                    remaining.remove(p)
                    comp.add(p)
                    q.append(p)
        out.append(comp)
    return out


def analyze(grid: list[list[int]]) -> dict[str, object]:
    g = _grid(grid)
    h, w = len(g), len(g[0])
    seeds = [(r, c) for r in range(h) for c in range(w) if g[r][c] == SEED]
    if len(seeds) != 1:
        raise ValueError("expected exactly one color-6 seed")
    seed = seeds[0]
    traversable = {(r, c) for r in range(h) for c in range(w) if g[r][c] in (BG, SEED)}
    region = next((comp for comp in _components(traversable) if seed in comp), None)
    if region is None:
        raise ValueError("seed has no reachable region")
    universe = {(r, c) for r in range(h) for c in range(w)}
    complement = _components(universe - region)
    border = lambda p: p[0] in (0, h - 1) or p[1] in (0, w - 1)
    holes = [comp for comp in complement if not any(border(p) for p in comp)]
    hole_cells = set().union(*holes) if holes else set()
    wall_cells = {(r, c) for r in range(h) for c in range(w) if g[r][c] == WALL}
    wall_components = _components(wall_cells)
    keep_walls: set[tuple[int, int]] = set()
    for comp in wall_components:
        if any((r + dr, c + dc) in region for r, c in comp for dr, dc in D4):
            keep_walls.update(comp)
    return {
        "height": h,
        "width": w,
        "seed": seed,
        "region": region,
        "holes": holes,
        "hole_cells": hole_cells,
        "keep_walls": keep_walls,
    }


def intermediate(grid: list[list[int]], setting: str = "outer_only") -> dict[str, object]:
    if setting not in SETTINGS:
        raise ValueError("unknown contour setting")
    info = analyze(grid)
    region = set(info["region"])
    hole_cells = set(info["hole_cells"])
    domain = region | hole_cells if setting == "outer_only" else region
    return {
        "region": sorted(region),
        "holes": [sorted(comp) for comp in info["holes"]],
        "boundary_domain": sorted(domain),
        "keep_walls": sorted(info["keep_walls"]),
    }


def _solve_with(grid: list[list[int]], setting: str, *, neighbors=D8) -> list[list[int]]:
    if setting not in SETTINGS:
        raise ValueError("unknown contour setting")
    g = _grid(grid)
    info = analyze(g)
    h, w = info["height"], info["width"]
    region = set(info["region"])
    holes = set(info["hole_cells"])
    keep_walls = set(info["keep_walls"])
    domain = region | holes if setting == "outer_only" else region
    out = [[BG] * w for _ in range(h)]
    for r, c in holes | keep_walls:
        out[r][c] = g[r][c]
    for r, c in region:
        if g[r][c] == SEED:
            out[r][c] = SEED
            continue
        boundary = False
        for dr, dc in neighbors:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w) or (nr, nc) not in domain:
                boundary = True
                break
        out[r][c] = OUTLINE if boundary else BG
    return out


def solve(grid: list[list[int]], setting: str = "outer_only") -> list[list[int]]:
    return _solve_with(grid, setting)


def solve_rival(grid: list[list[int]], setting: str, name: str) -> list[list[int]]:
    if name not in RIVALS:
        raise ValueError("unknown rival")
    g = _grid(grid)
    info = analyze(g)
    h, w = info["height"], info["width"]
    if name == "opposite_scope":
        return solve(g, "include_holes" if setting == "outer_only" else "outer_only")
    if name == "grid_edge_only":
        out = solve(g, setting)
        region = set(info["region"])
        for r, c in region:
            if g[r][c] != SEED:
                out[r][c] = OUTLINE if r in (0, h - 1) or c in (0, w - 1) else BG
        return out
    if name == "keep_all_input":
        out = solve(g, setting)
        region = set(info["region"])
        for r in range(h):
            for c in range(w):
                if (r, c) not in region and g[r][c] != BG:
                    out[r][c] = g[r][c]
        return out
    if name == "erase_holes":
        out = solve(g, setting)
        for r, c in info["hole_cells"]:
            out[r][c] = BG
        return out
    if name == "paint_region":
        out = solve(g, setting)
        for r, c in info["region"]:
            if g[r][c] != SEED:
                out[r][c] = OUTLINE
        return out
    if name == "paint_walls":
        out = solve(g, setting)
        for r, c in info["keep_walls"]:
            out[r][c] = OUTLINE
        return out
    if name == "drop_seed":
        out = solve(g, setting)
        r, c = info["seed"]
        out[r][c] = OUTLINE
        return out
    raise AssertionError(name)


def _rng(seed: int, tag: object) -> random.Random:
    material = json.dumps([seed, tag], sort_keys=True, separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(material).digest()[:16], "big"))


def _paint_rect(g: list[list[int]], r0: int, c0: int, rh: int, cw: int, value: int) -> None:
    for r in range(r0, r0 + rh):
        for c in range(c0, c0 + cw):
            g[r][c] = value


def make_scene(seed: int, tag: object, h: int, w: int, *, orientation: str, stress: bool) -> list[list[int]]:
    integer(seed, 0, 2**63 - 1, "seed")
    integer(h, 10, 30, "height")
    integer(w, 10, 30, "width")
    if orientation not in ("vertical", "horizontal"):
        raise ValueError("orientation must be vertical or horizontal")
    rng = _rng(seed, tag)
    g = [[BG] * w for _ in range(h)]
    if orientation == "vertical":
        split = max(7, min(w - 5, w // 2 + rng.choice((-1, 0, 1))))
        for r in range(h):
            g[r][split] = WALL
        # A wall spur makes the outer contour genuinely non-rectangular.
        spur_r = max(3, min(h - 4, h // 2 + rng.choice((-2, 1))))
        for c in range(split - 2 - int(stress), split):
            g[spur_r][c] = WALL
        g[h - 1][0] = SEED
        # Enclosed obstacles: one rectangle and one asymmetric cluster.
        _paint_rect(g, 2, 2, 2, 2 + int(stress), WALL)
        base_r = max(6, min(h - 4, h // 2 + 2))
        base_c = 2 + (seed % 2)
        for dr, dc in ((0, 0), (1, 0), (1, 1), (2, 1)):
            if base_r + dr < h - 1 and base_c + dc < split - 1:
                g[base_r + dr][base_c + dc] = WALL
        # Outside decoys must be erased.
        _paint_rect(g, 1, min(w - 3, split + 2), 2, 2, WALL)
        if stress:
            _paint_rect(g, h - 5, min(w - 4, split + 2), 3, 2, WALL)
    else:
        split = max(7, min(h - 5, h // 2 + rng.choice((-1, 0, 1))))
        for c in range(w):
            g[split][c] = WALL
        spur_c = max(3, min(w - 4, w // 2 + rng.choice((-2, 1))))
        for r in range(split - 2 - int(stress), split):
            g[r][spur_c] = WALL
        g[0][0] = SEED
        _paint_rect(g, 2, 2, 2 + int(stress), 2, WALL)
        base_r = 2 + (seed % 2)
        base_c = max(6, min(w - 4, w // 2 + 2))
        for dr, dc in ((0, 0), (0, 1), (1, 1), (1, 2)):
            if base_r + dr < split - 1 and base_c + dc < w - 1:
                g[base_r + dr][base_c + dc] = WALL
        _paint_rect(g, min(h - 3, split + 2), 1, 2, 2, WALL)
        if stress:
            _paint_rect(g, min(h - 4, split + 2), w - 5, 2, 3, WALL)
    # Construction must produce a meaningful hole-sensitive distinction.
    if solve(g, "outer_only") == solve(g, "include_holes"):
        raise AssertionError("scene does not distinguish contour settings")
    return g


def _shapes() -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    return ([(12, 14), (14, 16), (16, 18), (18, 20), (20, 22), (22, 24)],
            [(14, 16), (18, 20), (24, 27), (30, 30)])


def generate(seed: int, settings: dict[str, str], demos: int, queries: int) -> dict[str, object]:
    integer(seed, 0, 2**63 - 1, "seed")
    integer(demos, 2, 6, "demos")
    integer(queries, 1, 4, "queries")
    if type(settings) is not dict or set(settings) != {"contour"} or settings["contour"] not in SETTINGS:
        raise ValueError("settings must be exactly contour=outer_only|include_holes")
    setting = settings["contour"]
    train_shapes, query_shapes = _shapes()
    def pair(index: int, shape: tuple[int, int], query: bool = False) -> dict[str, object]:
        orientation = "vertical" if index % 2 == 0 else "horizontal"
        g = make_scene(seed, ["query" if query else "demo", index], *shape,
                       orientation=orientation, stress=query and index >= 2)
        return {"input": g, "output": solve(g, setting)}
    train = [pair(i, train_shapes[i]) for i in range(demos)]
    bank = [pair(i, shape, True) for i, shape in enumerate(query_shapes)]
    return {"train": train, "test": copy.deepcopy(bank[:queries]), "private_query_bank": bank}


def self_check(grid: list[list[int]]) -> list[str]:
    issues: list[str] = []
    try:
        info = analyze(grid)
        if not info["holes"]:
            issues.append("scene has no enclosed holes")
        if solve(grid, "outer_only") == solve(grid, "include_holes"):
            issues.append("settings do not differ")
    except Exception as exc:  # ordinary generator reports, rather than crashes
        issues.append(str(exc))
    return issues


def dependency() -> dict[str, str]:
    return {
        "step_a": "Flood-fill the color-6 seed through 8/6 cells and classify every complementary component as exterior or enclosed hole.",
        "intermediate": "The seed region, enclosed-hole cell sets, retained adjacent wall components, and chosen boundary domain.",
        "step_b": "Render color 7 exactly on seed-region cells touching the outside of that computed domain while retaining the seed and relevant walls.",
        "why": "Whether a region cell borders an enclosed obstacle cannot be known until the complement components have been classified.",
    }
