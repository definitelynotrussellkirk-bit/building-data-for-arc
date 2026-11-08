"""Constructive generator for filling enclosed background regions.

The canonical rule is ``(fill-all-enclosed g 8 0)``: every zero-region that
cannot reach the outer border becomes color 8; the exterior and interiors of
open frames remain zero.  Version 3 removes the imported pseudo-axes and keeps
three exact, observable controls: height, width, and a structural scene profile.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "75381adf158d"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "ae1411cac560"
SUMMARY = (
    "Zero-background grids contain several colored rectangular frames. Closed "
    "frames enclose zero-regions that become cyan (8); open frames have a missing "
    "side and remain connected to the exterior. Exact size and scene-profile "
    "overrides support ordinary, largest-hole counterexample, and many-hole scenes."
)
INVARIANTS = [
    "rectangular integer grid with dimensions 6..30 and input palette excluding color 8",
    "outer border is zero and at least one zero-region is fully enclosed",
    "closed and open frames occupy separated quadrants and never overlap",
    "the Python rule mirror exactly flood-fills only border-inaccessible zeros",
]
SCENE_PROFILES = ("mixed", "largest_counterexample", "many_holes")
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware 10..30", "valid": "10..30"},
    "grid_w": {"type": "int", "default": "difficulty-aware 12..30", "valid": "12..30"},
    "scene_profile": {"type": "str", "default": "three-profile schedule", "valid": "|".join(SCENE_PROFILES)},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = ()


def _validate_grid(value: Any) -> list[list[int]]:
    if not isinstance(value, (list, tuple)) or not value:
        raise ValueError("expected a nonempty rectangular grid")
    if not isinstance(value[0], (list, tuple)) or not value[0]:
        raise ValueError("expected a nonempty rectangular grid")
    h, w = len(value), len(value[0])
    if not 1 <= h <= 30 or not 1 <= w <= 30:
        raise ValueError("grid dimensions must be within 1..30")
    out: list[list[int]] = []
    for row in value:
        if not isinstance(row, (list, tuple)) or len(row) != w:
            raise ValueError("expected a rectangular grid")
        converted = []
        for cell in row:
            if type(cell) is not int or not 0 <= cell <= 9:
                raise ValueError("cells must be exact integer colors 0..9")
            converted.append(cell)
        out.append(converted)
    return out


def _zero_regions(grid: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 0}
    regions: list[dict[str, Any]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells: list[tuple[int, int]] = []
        touches = False
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            touches = touches or r in (0, h - 1) or c in (0, w - 1)
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    queue.append(point)
        regions.append({"cells": tuple(sorted(cells)), "touches_border": touches})
    return regions


def rule_mirror(value: Any) -> list[list[int]]:
    """Return the exact canonical flood-fill result without mutating ``value``."""
    source = _validate_grid(value)
    output = deepcopy(source)
    for region in _zero_regions(source):
        if not region["touches_border"]:
            for r, c in region["cells"]:
                output[r][c] = 8
    return output


def analyse(value: Any) -> dict[str, Any]:
    source = _validate_grid(value)
    h, w = len(source), len(source[0])
    regions = _zero_regions(source)
    enclosed = [row for row in regions if not row["touches_border"]]
    occupied = {(min(1, (2 * r) // h), min(1, (2 * c) // w))
                for r, row in enumerate(source) for c, cell in enumerate(row) if cell != 0}
    return {
        "height": h,
        "width": w,
        "enclosed_regions": len(enclosed),
        "open_regions": sum(row["touches_border"] for row in regions),
        "enclosed_sizes": sorted(len(row["cells"]) for row in enclosed),
        "nonzero": sum(cell != 0 for row in source for cell in row),
        "palette": sorted({cell for row in source for cell in row}),
        "occupied_quadrants": len(occupied),
    }


def self_check(grid: Any, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    try:
        source = _validate_grid(grid)
    except ValueError as exc:
        return [str(exc)]
    h, w = len(source), len(source[0])
    if not 6 <= h <= 30 or not 6 <= w <= 30:
        errors.append(f"grid dimensions outside supported 6..30: {h}x{w}")
    if any(cell == 8 for row in source for cell in row):
        errors.append("input color 8 is reserved for the canonical output")
    border = source[0] + source[-1] + [source[r][0] for r in range(1, h - 1)] + [source[r][-1] for r in range(1, h - 1)]
    if any(border):
        errors.append("outer border must remain zero")
    if not any(cell not in (0, 8) for row in source for cell in row):
        errors.append("no colored frame cells")
    facts = analyse(source)
    if facts["enclosed_regions"] < 1:
        errors.append("no enclosed zero-region")
    if facts["open_regions"] < 1:
        errors.append("no border-connected zero-region")
    return errors


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    for key in ("grid_h", "grid_w"):
        if key in overrides and type(overrides[key]) is not int:
            raise TypeError(f"{key} override must be an exact integer (not bool)")
    if "scene_profile" in overrides:
        value = overrides["scene_profile"]
        if type(value) is not str or value not in SCENE_PROFILES:
            raise ValueError(f"scene_profile must be one of {SCENE_PROFILES}")


def schedule_profile(seed: Any, sample_index: Any, difficulty=None) -> str:
    if type(seed) is not int or type(sample_index) is not int:
        raise TypeError("seed and sample_index must be exact integers")
    return SCENE_PROFILES[(seed + sample_index) % len(SCENE_PROFILES)]


def _difficulty_bounds(difficulty: Any) -> tuple[tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (10, 15), (12, 17)
    if difficulty == "medium":
        return (14, 23), (16, 25)
    if difficulty == "hard":
        return (22, 30), (24, 30)
    return (10, 30), (12, 30)


def _quadrants(h: int, w: int) -> list[tuple[int, int, int, int]]:
    mr, mc = h // 2, w // 2
    regions = [
        (1, 1, mr - 1, mc - 1),
        (1, mc, mr - 1, w - 2),
        (mr, 1, h - 2, mc - 1),
        (mr, mc, h - 2, w - 2),
    ]
    if any(r2 - r1 + 1 < 3 or c2 - c1 + 1 < 3 for r1, c1, r2, c2 in regions):
        raise ValueError(f"grid {h}x{w} is too small for four teaching quadrants")
    return regions


def _size(region: tuple[int, int, int, int], role: str) -> tuple[int, int]:
    r1, c1, r2, c2 = region
    rh, rw = r2 - r1 + 1, c2 - c1 + 1
    if role == "small":
        return min(rh, max(3, rh // 3 + 1)), min(rw, max(3, rw // 3 + 1))
    if role == "medium":
        return min(rh, max(3, rh // 2)), min(rw, max(4, rw // 2 + 1))
    if role == "large":
        return rh, rw
    if role == "open":
        return min(rh, max(3, rh // 2)), min(rw, max(3, rw // 2))
    raise ValueError(role)


def _box(region: tuple[int, int, int, int], size: tuple[int, int], rng) -> tuple[int, int, int, int]:
    r1, c1, r2, c2 = region
    rh, rw = size
    rr = r1 + rng.randrange(r2 - r1 + 2 - rh)
    cc = c1 + rng.randrange(c2 - c1 + 2 - rw)
    return rr, cc, rr + rh - 1, cc + rw - 1


def _draw_frame(grid: list[list[int]], box: tuple[int, int, int, int], color: int, *, gap: str | None = None) -> None:
    r1, c1, r2, c2 = box
    for c in range(c1, c2 + 1):
        if gap != "top":
            grid[r1][c] = color
        if gap != "bottom":
            grid[r2][c] = color
    for r in range(r1, r2 + 1):
        if gap != "left":
            grid[r][c1] = color
        if gap != "right":
            grid[r][c2] = color


def _scene(h: int, w: int, profile: str, rng) -> list[list[int]]:
    regions = _quadrants(h, w)
    grid = [[0 for _ in range(w)] for _ in range(h)]
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 4)
    if profile == "largest_counterexample":
        specs = [(0, "small", True), (1, "medium", True), (2, "large", True), (3, "open", False)]
    elif profile == "many_holes":
        specs = [(0, "small", True), (1, "medium", True), (2, "large", True), (3, "medium", True)]
    else:
        specs = [(0, "medium", True), (1, "open", False), (2, "open", False), (3, "large", True)]
    outward = {0: "top", 1: "top", 2: "bottom", 3: "bottom"}
    for color, (quadrant, role, closed) in zip(colors, specs):
        region = regions[quadrant]
        box = _box(region, _size(region, role), rng)
        _draw_frame(grid, box, color, gap=None if closed else outward[quadrant])
    # Horizontal reflection adds positional diversity while keeping the unique
    # largest hole in the lower half, so the largest-to-border route is taught.
    if rng.randrange(2):
        grid = [row[::-1] for row in grid]
    return grid


def generate(seed: Any, sample_index: Any, *, difficulty=None, **overrides):
    if type(seed) is not int or type(sample_index) is not int:
        raise TypeError("seed and sample_index must be exact integers")
    _validate_overrides(overrides)
    scheduled = overrides.get("scene_profile") or schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    profile = ctx.draw_choice("scene_profile", [scheduled])
    hb, wb = _difficulty_bounds(difficulty)
    h = ctx.draw_int_strict("grid_h", *hb)
    w = ctx.draw_int_strict("grid_w", *wb)
    grid = _scene(h, w, profile, ctx.draw_rng(f"layout_{profile}"))
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructed scene failed self_check: {errors}")
    return grid


def observe_overrides(seed: Any, sample_index: Any, *, difficulty=None, **overrides) -> dict[str, Any]:
    """Validate a generation request and report the exact consumed overrides."""
    generate(seed, sample_index, difficulty=difficulty, **overrides)
    return {key: overrides[key] for key in AXES if key in overrides}
