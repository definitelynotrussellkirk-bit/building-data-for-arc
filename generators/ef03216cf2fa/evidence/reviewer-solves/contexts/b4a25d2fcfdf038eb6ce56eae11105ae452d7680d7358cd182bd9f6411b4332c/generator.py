"""Canonical-profile generator for ARC task ef03216cf2fa.

The input contains three or four separated monochrome objects.  The selected
Racket rule crops each object, rotates a tall crop 90 degrees clockwise, sorts
objects by bounding-box perimeter descending (row-major on ties), and stacks
them vertically with one background row between consecutive crops.

Canonical demonstrations do not reveal rotation direction because every tall
canonical crop is symmetric under clockwise versus counterclockwise rotation.
Every generated sample therefore contains an asymmetric tall object that
refutes the strongest canonical-fitting counterclockwise rival.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ef03216cf2fa"
TASK_ID = GENERATOR_ID
RULE_HASH = "455db4f731f0"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Three or four separated monochrome objects have distinct bounding-box "
    "perimeters and a controlled row-major rank order. Crop each object, rotate "
    "tall crops clockwise, sort by perimeter descending (row-major on ties), "
    "and stack them vertically with one zero row between crops. Every generated "
    "input contains an asymmetric tall crop that distinguishes clockwise from "
    "counterclockwise rotation."
)

INVARIANTS = [
    "background is 0 and every object has its own nonzero color",
    "there are exactly 3 or 4 separated same-color 4-connected objects",
    "generated object perimeters are pairwise distinct",
    "generated scenes contain 1 or 2 tall objects and at least one non-tall object",
    "every generated tall crop distinguishes clockwise from counterclockwise rotation",
]

# Keep this assignment statically literal: repository lint reads it through AST.
AXES = {
    "grid_h": {"type": "int", "default": "canonical-profile schedule", "valid": "10..14"},
    "grid_w": {"type": "int", "default": "canonical-profile schedule", "valid": "10..14"},
    "n": {"type": "int", "default": "canonical-profile schedule", "valid": "3..4"},
    "tall_count": {"type": "int", "default": "uniform 1..2", "valid": "1..2"},
    "rank_layout": {
        "type": "str",
        "default": "uniform",
        "valid": "ascending|descending|interleaved",
    },
    "palette_family": {
        "type": "str",
        "default": "uniform",
        "valid": "low|high|mixed",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_RANK_LAYOUTS = ("ascending", "descending", "interleaved")
_PALETTE_FAMILIES = ("low", "high", "mixed")
_DIRECTIONS = ((-1, 0), (0, -1), (0, 1), (1, 0))


def _validate_generate_args(difficulty, overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    for name in ("grid_h", "grid_w", "n", "tall_count"):
        if name in overrides:
            value = overrides[name]
            if type(value) is not int:
                raise TypeError(f"{name} override must be an integer (not bool)")
    for name in ("rank_layout", "palette_family"):
        if name in overrides:
            value = overrides[name]
            if type(value) is not str:
                raise TypeError(f"{name} override must be a string")


def _scheduled_int(ctx, overrides: dict, label: str, lo: int, hi: int, default: int) -> int:
    """Record an exact scheduled default while preserving the full override domain."""
    if label in overrides:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_choice(label, (default,))


def _palette(ctx, family: str, count: int) -> list[int]:
    rng = ctx.draw_rng("palette")
    if family == "low":
        colors = rng.sample([1, 2, 3, 4], count)
    elif family == "high":
        colors = rng.sample([6, 7, 8, 9], count)
    elif family == "mixed":
        low_count = 1 + rng.randrange(count - 1)
        high_count = count - low_count
        colors = rng.sample([1, 2, 3, 4], low_count)
        colors += rng.sample([6, 7, 8, 9], high_count)
        rng.shuffle(colors)
    else:  # guarded by ctx.draw_choice, retained as a local invariant.
        raise ValueError(f"unknown palette family {family!r}")
    return colors


def _bbox_for_sum(side_sum: int, *, tall: bool) -> tuple[int, int]:
    """Return dimensions <=4 with the requested orientation and exact sum."""
    if side_sum == 4:
        return (2, 2)
    if side_sum == 5:
        return (3, 2) if tall else (2, 3)
    if side_sum == 6:
        return (4, 2) if tall else (2, 4)
    if side_sum == 7:
        return (4, 3) if tall else (3, 4)
    raise ValueError(f"unsupported bbox side sum {side_sum}")


def _corner_l(height: int, width: int, variant: int) -> set[tuple[int, int]]:
    """Connected asymmetric shape spanning an exact bounding box."""
    if variant == 0:  # top + left
        return {(0, c) for c in range(width)} | {(r, 0) for r in range(height)}
    if variant == 1:  # top + right
        return {(0, c) for c in range(width)} | {(r, width - 1) for r in range(height)}
    if variant == 2:  # bottom + left
        return {(height - 1, c) for c in range(width)} | {(r, 0) for r in range(height)}
    if variant == 3:  # bottom + right
        return {(height - 1, c) for c in range(width)} | {(r, width - 1) for r in range(height)}
    raise ValueError(f"unknown shape variant {variant}")


def _shape_cells(ctx, rank: int, height: int, width: int) -> set[tuple[int, int]]:
    rng = ctx.draw_rng(f"shape_{rank}")
    cells = _corner_l(height, width, rng.randrange(4))
    # Add at most one interior/boundary detail without ever filling the crop.
    missing = [
        (r, c)
        for r in range(height)
        for c in range(width)
        if (r, c) not in cells
        and any((r + dr, c + dc) in cells for dr, dc in _DIRECTIONS)
    ]
    if len(missing) >= 2 and rng.randrange(2):
        cells.add(rng.choice(missing))
    return cells


def _slot_rank_order(count: int, layout: str) -> tuple[int, ...]:
    if layout == "ascending":
        return tuple(range(count))
    if layout == "descending":
        return tuple(reversed(range(count)))
    if layout == "interleaved":
        return (1, 2, 0) if count == 3 else (1, 3, 0, 2)
    raise ValueError(f"unknown rank layout {layout!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_generate_args(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    canonical_profiles = ((10, 10, 3), (10, 12, 3), (11, 11, 4), (12, 12, 4))
    scheduled_h, scheduled_w, scheduled_n = canonical_profiles[
        ctx.draw_rng("canonical_profile").randrange(len(canonical_profiles))
    ]
    height = _scheduled_int(ctx, overrides, "grid_h", 10, 14, scheduled_h)
    width = _scheduled_int(ctx, overrides, "grid_w", 10, 14, scheduled_w)
    count = _scheduled_int(ctx, overrides, "n", 3, 4, scheduled_n)
    tall_count = ctx.draw_int_strict("tall_count", 1, 2)
    rank_layout = ctx.draw_choice("rank_layout", _RANK_LAYOUTS)
    palette_family = ctx.draw_choice("palette_family", _PALETTE_FAMILIES)

    side_sums = list(range(4, 4 + count))
    tall_ranks = set(range(count - tall_count, count))
    colors = _palette(ctx, palette_family, count)
    ranked = []
    for rank, (side_sum, color) in enumerate(zip(side_sums, colors)):
        box_h, box_w = _bbox_for_sum(side_sum, tall=rank in tall_ranks)
        ranked.append(
            {
                "rank": rank,
                "color": color,
                "height": box_h,
                "width": box_w,
                "cells": _shape_cells(ctx, rank, box_h, box_w),
            }
        )

    layout_rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        top, left = 0, 0
    elif difficulty == "medium":
        top, left = 1, 0
    elif difficulty == "hard":
        top, left = 0, 1
    else:
        top = layout_rng.choice((0, 1))
        left = layout_rng.choice((0, 1))
    bottom = height - 4
    right = width - 4
    slots = ((top, left), (top, right), (bottom, left), (bottom, right))

    grid = full_grid(height, width, 0)
    for slot_index, rank in enumerate(_slot_rank_order(count, rank_layout)):
        row0, col0 = slots[slot_index]
        spec = ranked[rank]
        for row, col in spec["cells"]:
            grid[row0 + row][col0 + col] = spec["color"]

    findings = self_check(grid)
    if findings:
        raise RuntimeError(f"internal generator invariant failed: {findings[0]}")
    if not _clockwise_direction_witness(grid):
        raise RuntimeError("generated scene failed to distinguish rotation direction")
    return grid


def _validate_grid(grid) -> tuple[list[str], int, int]:
    findings: list[str] = []
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"], 0, 0
    if not all(isinstance(row, list) for row in grid):
        return ["every row must be a list"], 0, 0
    if not grid[0]:
        return ["rows must be non-empty"], len(grid), 0
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        findings.append("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        findings.append("every cell must be an integer color in 0..9 (not bool)")
    return findings, len(grid), width


def _components(grid) -> list[dict]:
    """Same-color 4-connected nonzero objects in row-major discovery order."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in _DIRECTIONS:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            row0 = min(r for r, _ in cells)
            row1 = max(r for r, _ in cells)
            col0 = min(c for _, c in cells)
            col1 = max(c for _, c in cells)
            crop = [values[col0 : col1 + 1] for values in grid[row0 : row1 + 1]]
            result.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "bbox": (row0, col0, row1, col1),
                    "height": row1 - row0 + 1,
                    "width": col1 - col0 + 1,
                    "perimeter": 2 * ((row1 - row0 + 1) + (col1 - col0 + 1)),
                    "crop": crop,
                }
            )
    return result


def self_check(grid) -> list[str]:
    findings, height, width = _validate_grid(grid)
    if findings:
        return findings
    if not (5 <= height <= 30 and 5 <= width <= 30):
        findings.append("grid dimensions must be in 5..30")
    parts = _components(grid)
    if not 3 <= len(parts) <= 4:
        findings.append(f"expected 3 or 4 objects, found {len(parts)}")
    colors = [obj["color"] for obj in parts]
    if len(colors) != len(set(colors)):
        findings.append("each color must identify exactly one object")
    if any(len(obj["cells"]) < 2 for obj in parts):
        findings.append("every object must contain at least two cells")

    occupied = {(r, c): obj["color"] for obj in parts for r, c in obj["cells"]}
    for (row, col), color in occupied.items():
        for dr, dc in _DIRECTIONS:
            other = occupied.get((row + dr, col + dc))
            if other is not None and other != color:
                findings.append("objects of different colors may not touch orthogonally")
                break
        if findings and findings[-1].startswith("objects of different"):
            break

    tall_count = sum(obj["height"] > obj["width"] for obj in parts)
    non_tall_count = len(parts) - tall_count
    if tall_count < 1:
        findings.append("at least one object must be taller than wide")
    if non_tall_count < 1:
        findings.append("at least one object must be square or wider than tall")
    if len({obj["perimeter"] for obj in parts}) < 2:
        findings.append("scene must contain at least two bounding-box perimeters")
    return findings


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def _rotate_clockwise(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_counterclockwise(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)][::-1]


def _pack_with_rotation(
    grid: list[list[int]],
    rotate_tall: Callable[[list[list[int]]], list[list[int]]],
) -> list[list[int]]:
    findings = self_check(grid)
    if findings:
        raise ValueError(findings[0])
    items = []
    for obj in _components(grid):
        shape = deepcopy(obj["crop"])
        if obj["height"] > obj["width"]:
            shape = rotate_tall(shape)
        row0, col0, _, _ = obj["bbox"]
        items.append((obj["perimeter"], row0, col0, shape))
    items.sort(key=lambda item: (-item[0], item[1], item[2]))
    shapes = [item[3] for item in items]
    out_height = sum(len(shape) for shape in shapes) + len(shapes) - 1
    out_width = max(len(shape[0]) for shape in shapes)
    out = full_grid(out_height, out_width, 0)
    top = 0
    for shape in shapes:
        for row, values in enumerate(shape):
            for col, value in enumerate(values):
                if value != 0:
                    out[top + row][col] = value
        top += len(shape) + 1
    return out


def rule_mirror(grid) -> list[list[int]]:
    """Independent-use Python mirror; the selected Racket rule is authority."""
    return _pack_with_rotation(grid, _rotate_clockwise)


def _rotate_tall_counterclockwise(grid) -> list[list[int]]:
    """Canonical-fitting rival: use the opposite 90-degree direction."""
    return _pack_with_rotation(grid, _rotate_counterclockwise)


def _clockwise_direction_witness(grid) -> bool:
    try:
        return rule_mirror(grid) != _rotate_tall_counterclockwise(grid)
    except (TypeError, ValueError):
        return False


def observe_overrides(grid) -> dict:
    findings = self_check(grid)
    if findings:
        raise ValueError(findings[0])
    parts = _components(grid)
    perimeters = [obj["perimeter"] for obj in parts]
    if len(set(perimeters)) != len(perimeters):
        raise ValueError("rank_layout is not observable when perimeters tie")
    ordered = sorted(perimeters)
    ranks = [ordered.index(value) for value in perimeters]
    if ranks == list(range(len(ranks))):
        rank_layout = "ascending"
    elif ranks == list(reversed(range(len(ranks)))):
        rank_layout = "descending"
    else:
        rank_layout = "interleaved"
    colors = {obj["color"] for obj in parts}
    if max(colors) <= 4:
        palette_family = "low"
    elif min(colors) >= 6:
        palette_family = "high"
    else:
        palette_family = "mixed"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n": len(parts),
        "tall_count": sum(obj["height"] > obj["width"] for obj in parts),
        "rank_layout": rank_layout,
        "palette_family": palette_family,
    }


SEMANTIC_WITNESSES = {"clockwise_rotation_direction": _clockwise_direction_witness}
SEMANTIC_RIVALS = {"rotate_tall_counterclockwise": _rotate_tall_counterclockwise}
WITNESS_RIVALS = {
    "clockwise_rotation_direction": ["rotate_tall_counterclockwise"],
}
CANONICAL_SHORTCUTS = {
    "rotate_tall_counterclockwise": _rotate_tall_counterclockwise,
}
LESSON_COMPETITORS = {
    "rotate_tall_counterclockwise": _rotate_tall_counterclockwise,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report a declared rival that survives all demos but changes the query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    valid_demos = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input invalid: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the hook rule")
            continue
        valid_demos.append(pair)

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input invalid: {query_errors[0]}")
    elif query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with the hook rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in valid_demos):
            if competitor(query["input"]) != query["output"]:
                reasons.append(
                    f"competing rule {name!r} fits every demo but changes the query answer"
                )
    return reasons
