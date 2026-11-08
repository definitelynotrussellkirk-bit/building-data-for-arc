"""Generator for arc_additional_puzzles_21_set10_bundle:M70.

Rule: sort separated monochrome connected objects by reading order, then emit
an object-by-object matrix comparing bounding-box widths: 1 equal, 2 greater,
3 less.  The sampler uses rectangles as a lawful, controllable subset.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "758360aea29b"
TASK_ID = GENERATOR_ID
VERSION = "2.3.0"
RULE_HASH = "a2e0aeab30da"
SUMMARY = (
    "N separated monochrome connected objects with varied bounding-box widths; "
    "output is the N x N width-comparison matrix (1=equal, 2=greater, 3=less)."
)

INVARIANTS = [
    "2..7 monochrome 4-connected objects separated by background",
    "object colors exclude 1, which is reserved for the output alphabet",
    "object bounding-box widths vary",
]

# Palette controls are useful sampling aliases, but are not advertised as exact
# observable AXES: a returned subset of colors can belong to multiple palettes.
PALETTES = {
    "warm": (2, 3, 4, 5, 6, 7, 8),
    "cool": (2, 3, 4, 5, 6, 8, 9),
    "broad": (2, 3, 4, 5, 6, 7, 8, 9),
    "primary": (2, 3, 4, 5, 6, 7, 9),
}
PALETTE_KINDS = tuple(PALETTES)
HELPFUL_TEXTURES = PALETTE_KINDS
DEGENERATE_TEXTURES = ("no_objects", "single_object", "full_grid")

# Only values exactly recoverable from the returned grid are public axes.
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-keyed", "valid": "10..18"},
    "grid_w": {"type": "int", "default": "difficulty-keyed", "valid": "12..22"},
    "n_objects": {"type": "int", "default": "difficulty-keyed", "valid": "2..7"},
}

_ALLOWED_OVERRIDES = set(AXES) | {"palette_kind", "texture"}


def _exact_int(value: Any, name: str, lo: int | None = None, hi: int | None = None) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an exact integer")
    if lo is not None and value < lo or hi is not None and value > hi:
        raise ValueError(f"{name} must be in {lo}..{hi}")
    return value


def _validated_call(seed, sample_index, difficulty, overrides):
    _exact_int(seed, "seed", 0)
    _exact_int(sample_index, "sample_index", 0)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, lo, hi in (("grid_h", 10, 18), ("grid_w", 12, 22), ("n_objects", 2, 7)):
        if name in overrides and overrides[name] is not None:
            _exact_int(overrides[name], name, lo, hi)
    for name in ("palette_kind", "texture"):
        if name in overrides and overrides[name] is not None:
            value = overrides[name]
            if type(value) is not str or value not in PALETTE_KINDS:
                raise ValueError(f"{name} must be one of {'|'.join(PALETTE_KINDS)}")
    if overrides.get("palette_kind") is not None and overrides.get("texture") is not None:
        if overrides["palette_kind"] != overrides["texture"]:
            raise ValueError("palette_kind and texture aliases must agree")


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Canonical `objects g 0`: monochrome 4-connected components."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for start_r in range(h):
        for start_c in range(w):
            color = grid[start_r][start_c]
            if color == 0 or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= rr < h and 0 <= cc < w
                            and (rr, cc) not in seen and grid[rr][cc] == color):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            r1 = min(r for r, _ in cells); r2 = max(r for r, _ in cells)
            c1 = min(c for _, c in cells); c2 = max(c for _, c in cells)
            result.append({"color": color, "cells": cells, "r1": r1, "c1": c1,
                           "r2": r2, "c2": c2, "width": c2 - c1 + 1})
    result.sort(key=lambda item: (item["r1"], item["c1"]))
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical connected-object grammar, including irregular shapes."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    if not 1 <= h <= 30 or not 1 <= w <= 30:
        return [f"grid too large or empty: {h}x{w}"]
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid rows must be rectangular"]

    errors: list[str] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")
    if errors:
        return errors
    objects = _components(grid)
    if any(item["color"] == 1 for item in objects):
        errors.append("color 1 used as an object color (reserved for output)")
    if not 2 <= len(objects) <= 7:
        errors.append(f"expected 2..7 connected objects, got {len(objects)}")

    for item in objects:
        color = item["color"]
        for r, c in item["cells"]:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] not in (0, color):
                        errors.append(
                            f"colors {color} and {grid[rr][cc]} touch; objects must be separated"
                        )
                        break
                else:
                    continue
                break
            else:
                continue
            break
    widths = [item["width"] for item in objects]
    if len(set(widths)) < 2:
        errors.append("all object widths equal; greater/less is not demonstrated")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_objects": len(_components(grid))}


def _place_rect(g, rh, rw, color, rng, occupied):
    h, w = len(g), len(g[0])
    if rh > h or rw > w:
        return False
    for _ in range(180):
        r0 = rng.randint(0, h - rh)
        c0 = rng.randint(0, w - rw)
        cells = [(r0 + r, c0 + c) for r in range(rh) for c in range(rw)]
        if any((r + dr, c + dc) in occupied for r, c in cells for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
            continue
        for r, c in cells:
            g[r][c] = color
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    occupied.add((r + dr, c + dc))
        return True
    return False


def _width_pool(rng, n, width_hi):
    if width_hi < 2:
        raise ValueError("canvas cannot demonstrate unequal widths")
    if n == 2:
        a = rng.randint(1, width_hi)
        b = rng.choice([x for x in range(1, width_hi + 1) if x != a])
        widths = [a, b]
    else:
        a = rng.randint(1, width_hi)
        b = rng.choice([x for x in range(1, width_hi + 1) if x != a])
        widths = [a, a, b]
        while len(widths) < n:
            widths.append(rng.randint(1, width_hi))
    rng.shuffle(widths)
    return widths


def _fallback_layout(h, w, widths, colors):
    """Two separated shelves; guaranteed for the declared minimum canvas."""
    grid = full_grid(h, w, 0)
    left_capacity = (w - 2) // 2
    right_start = left_capacity + 2
    right_capacity = w - right_start
    rows = list(range(0, h, 2))
    left_count = (len(widths) + 1) // 2
    if left_count > len(rows) or len(widths) - left_count > len(rows):
        raise ValueError("declared canvas cannot hold the requested separated objects")
    for index, (width, color) in enumerate(zip(widths, colors)):
        if index < left_count:
            r, c0, capacity = rows[index], 0, left_capacity
        else:
            r, c0, capacity = rows[index - left_count], right_start, right_capacity
        if width > capacity:
            raise ValueError("fallback slot is narrower than a constructed rectangle")
        for c in range(c0, c0 + width):
            grid[r][c] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validated_call(seed, sample_index, difficulty, overrides)

    normalized = dict(overrides)
    texture = normalized.pop("texture", None)
    if texture is not None:
        normalized["palette_kind"] = texture
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=normalized,
    )

    h_explicit = normalized.get("grid_h") is not None
    w_explicit = normalized.get("grid_w") is not None
    n_explicit = normalized.get("n_objects") is not None
    # Every difficulty retains an exact canonical-scale anchor.  This is a
    # scheduled default branch only: explicit overrides always keep the full
    # declared domain.
    canonical_anchor = sample_index % 4 == 0
    if canonical_anchor:
        h = ctx.draw_int("grid_h", 10, 18) if h_explicit else ctx.draw_int("grid_h", 10, 10)
        w = ctx.draw_int("grid_w", 12, 22) if w_explicit else ctx.draw_int("grid_w", 12, 12)
        n = ctx.draw_int("n_objects", 2, 7) if n_explicit else ctx.draw_int("n_objects", 3, 3)
        nominal_width_hi = 5
    elif difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 18) if h_explicit else ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 12, 22) if w_explicit else ctx.draw_int("grid_w", 12, 15)
        n = ctx.draw_int("n_objects", 2, 7) if n_explicit else ctx.draw_int("n_objects", 2, 4)
        nominal_width_hi = 5
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 18) if h_explicit else ctx.draw_int("grid_h", 14, 18)
        w = ctx.draw_int("grid_w", 12, 22) if w_explicit else ctx.draw_int("grid_w", 16, 22)
        n = ctx.draw_int("n_objects", 2, 7) if n_explicit else ctx.draw_int("n_objects", 5, 7)
        nominal_width_hi = 8
    else:
        h = ctx.draw_int("grid_h", 10, 18) if h_explicit else ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 12, 22) if w_explicit else ctx.draw_int("grid_w", 14, 20)
        n = ctx.draw_int("n_objects", 2, 7) if n_explicit else ctx.draw_int("n_objects", 2, 6)
        nominal_width_hi = 7

    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    rng = ctx.draw_rng("layout")
    colors = rng.sample(list(PALETTES[palette_kind]), n)
    width_hi = min(nominal_width_hi, (w - 2) // 2)
    widths = _width_pool(rng, n, width_hi)

    for _attempt in range(80):
        grid = full_grid(h, w, 0)
        occupied: set[tuple[int, int]] = set()
        for index, width in enumerate(widths):
            height = rng.randint(1, min(4, h - 1))
            if not _place_rect(grid, height, width, colors[index], rng, occupied):
                break
        else:
            if self_check(grid) == []:
                return grid

    grid = _fallback_layout(h, w, widths, colors)
    reasons = self_check(grid)
    if reasons:
        raise RuntimeError(f"fallback construction violated invariants: {reasons}")
    return grid


def _draw_from_degenerate(name, rng=None):
    """Private negative fixtures; generate() deliberately rejects these names."""
    del rng
    grid = full_grid(11, 14, 0)
    if name == "no_objects":
        return grid
    if name == "single_object":
        draw_rect(grid, 4, 5, 2, 4, 3)
        return grid
    if name == "full_grid":
        return full_grid(11, 14, 3)
    raise ValueError(f"unknown degenerate fixture: {name}")
