"""Generator for ARC task f395ecd79f92 — keep the median-area object.

The input contains an odd number of isolated, monochrome 4-connected objects.
Object cell-areas are distinct.  Sort objects by area ascending (reading order
is the canonical tie-break, though ordinary generated lessons avoid ties) and
copy only the middle object to an otherwise-zero grid of the same dimensions.

The lesson schedule deliberately varies object count, reading-order rank,
numeric color rank, shape, and bounding-box area so the intended cell-area
rule is identifiable from three demonstrations rather than from shortcuts.
"""
from __future__ import annotations

from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f395ecd79f92"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "77202e38a056"

SUMMARY = (
    "Find the isolated nonzero objects, sort them by cell-area ascending "
    "(reading order breaks ties), and keep only the middle object on a "
    "same-size zero background."
)

INVARIANTS = [
    "the grid has exactly 3, 5, or 7 isolated monochrome 4-connected objects",
    "object colors and cell-areas are pairwise distinct",
    "the selected object is the floor(n/2)-th item after area/read-order sorting",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.18

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchor or difficulty-skewed 8..16",
        "valid": "8..16",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchor or difficulty-skewed 8..18",
        "valid": "8..18",
    },
    "n_blobs": {
        "type": "int",
        "default": "lesson-scheduled odd count",
        "valid": "3|5|7",
    },
    "shape_style": {
        "type": "str",
        "default": "lesson-scheduled",
        "valid": "rectangles|mixed|organic",
    },
    "size_order": {
        "type": "str",
        "default": "lesson-scheduled",
        "valid": "ascending_reading|descending_reading|shuffled",
    },
    "palette_kind": {
        "type": "str",
        "default": "lesson-scheduled",
        "valid": "mixed|warm|cool",
    },
}

_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_PROFILES = ((8, 10), (9, 11), (8, 12), (10, 12))
_CANONICAL_SIZES = ((2, 4, 9), (3, 6, 9), (4, 8, 12), (5, 8, 12))
_PALETTES = {
    "mixed": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    "warm": (2, 4, 6, 7, 8, 9, 1, 3, 5),
    "cool": (1, 3, 5, 8, 9, 6, 2, 4, 7),
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty sequences"]
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be ARC colors 0..9"]
    return []


def _components(grid: Any) -> list[dict[str, Any]]:
    """Return nonzero monochrome 4-components in reading order."""
    if _validate_grid(grid):
        return []
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _DIRS:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            cells.sort()
            r0 = min(rr for rr, _ in cells)
            r1 = max(rr for rr, _ in cells)
            c0 = min(cc for _, cc in cells)
            c1 = max(cc for _, cc in cells)
            bbox_area = (r1 - r0 + 1) * (c1 - c0 + 1)
            result.append(
                {
                    "color": color,
                    "cells": tuple(cells),
                    "size": len(cells),
                    "first": cells[0],
                    "bbox": (r0, c0, r1, c1),
                    "bbox_area": bbox_area,
                    "solid_rectangle": bbox_area == len(cells),
                }
            )
    result.sort(key=lambda item: item["first"])
    return result


def _median_component(grid: Any, *, key: str = "size") -> dict[str, Any]:
    comps = _components(grid)
    ranked = sorted(comps, key=lambda item: (item[key], item["first"]))
    return ranked[len(ranked) // 2]


def expected_output(grid: Any) -> list[list[int]]:
    """Pure Python statement of the canonical rule, used by semantic hooks/tests."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid median-object input: " + "; ".join(errors))
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    selected = _median_component(grid)
    for r, c in selected["cells"]:
        out[r][c] = selected["color"]
    return out


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _validate_grid(grid)
    if errors:
        return {"errors": errors}
    h, w = len(grid), len(grid[0])
    comps = _components(grid)
    colors = [item["color"] for item in comps]
    sizes = [item["size"] for item in comps]
    occupied = {cell for item in comps for cell in item["cells"]}
    owner = {
        cell: index
        for index, item in enumerate(comps)
        for cell in item["cells"]
    }

    if not (8 <= h <= 16 and 8 <= w <= 18):
        errors.append(f"dims {h}x{w} outside declared envelope 8..16 x 8..18")
    if len(comps) not in (3, 5, 7):
        errors.append(f"need exactly 3, 5, or 7 objects, found {len(comps)}")
    if len(set(colors)) != len(colors):
        errors.append(f"object colors must be distinct, got {colors}")
    if len(set(sizes)) != len(sizes):
        errors.append(f"object cell-areas must be distinct, got {sizes}")
    if sum(value == 0 for row in grid for value in row) <= h * w // 2:
        errors.append("zero must remain the majority background")
    for r, c in occupied:
        for dr, dc in _DIRS:
            neighbor = (r + dr, c + dc)
            if neighbor in owner and owner[neighbor] != owner[(r, c)]:
                errors.append("different objects touch orthogonally")
                break
        if errors and errors[-1] == "different objects touch orthogonally":
            break

    selected = None
    if comps and len(set(sizes)) == len(sizes):
        selected = sorted(comps, key=lambda item: (item["size"], item["first"]))[
            len(comps) // 2
        ]
        if selected["size"] >= sum(sizes):
            errors.append("selected object does not visibly reduce the input")

    reading_middle = comps[len(comps) // 2] if comps else None
    color_middle = (
        sorted(comps, key=lambda item: item["color"])[len(comps) // 2]
        if comps
        else None
    )
    bbox_middle = (
        sorted(comps, key=lambda item: (item["bbox_area"], item["first"]))[
            len(comps) // 2
        ]
        if comps
        else None
    )
    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "components": comps,
        "n_blobs": len(comps),
        "selected": selected,
        "all_rectangles": bool(comps) and all(item["solid_rectangle"] for item in comps),
        "has_nonrectangle": any(not item["solid_rectangle"] for item in comps),
        "median_not_reading_middle": bool(selected and reading_middle is not selected),
        "median_not_color_middle": bool(selected and color_middle is not selected),
        "median_not_bbox_middle": bool(selected and bbox_middle is not selected),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-ambiguous median-object inputs."""
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Recognize the canonical three-solid-rectangle teaching manifold."""
    analysis = _analysis(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    if (analysis["grid_h"], analysis["grid_w"]) not in _CANONICAL_PROFILES:
        reasons.append("dimensions are not one of the four canonical profiles")
    if analysis["n_blobs"] != 3:
        reasons.append("canonical profile has exactly three objects")
    if not analysis["all_rectangles"]:
        reasons.append("canonical objects are solid rectangles")
    return reasons


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact count/dimension axis from the returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n_blobs": analysis["n_blobs"],
    }


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _orientations(cells: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    base = tuple(cells)
    variants: set[tuple[tuple[int, int], ...]] = set()
    for reflect in (False, True):
        for rotation in range(4):
            transformed = []
            for r, c in base:
                x, y = (r, -c) if reflect else (r, c)
                for _ in range(rotation):
                    x, y = y, -x
                transformed.append((x, y))
            variants.add(_normalize(transformed))
    return tuple(sorted(variants))


def _rectangle(area: int) -> tuple[tuple[int, int], ...]:
    factors = [factor for factor in range(1, int(area**0.5) + 1) if area % factor == 0]
    height = max(factors)
    width = area // height
    return tuple((r, c) for r in range(height) for c in range(width))


def _organic(area: int) -> tuple[tuple[int, int], ...]:
    banks = {
        1: ((0, 0),),
        2: ((0, 0), (0, 1)),
        3: ((0, 0), (1, 0), (1, 1)),
        4: ((0, 0), (1, 0), (1, 1), (2, 0)),
        5: ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),
        6: ((0, 0), (0, 1), (1, 1), (1, 2), (2, 1), (2, 2)),
        7: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)),
        8: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
        9: ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
        10: ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3)),
        11: ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3)),
        12: ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3), (3, 1), (3, 2)),
    }
    return banks[area]


def _shape_for(area: int, style: str, index: int) -> tuple[tuple[int, int], ...]:
    if style == "rectangles":
        return _rectangle(area)
    if style == "organic":
        return _organic(area)
    return _rectangle(area) if index % 2 == 0 else _organic(area)


def _size_set(n: int, slot: int) -> list[int]:
    if n == 3:
        if slot == 0:
            return list(_CANONICAL_SIZES[(slot // 4) % len(_CANONICAL_SIZES)])
        if slot == 1:
            # The 5-cell staircase has bbox area 9, so the cell-area median
            # differs from the bbox-area median in this scheduled demonstration.
            return [5, 6, 8]
        return [3, 7, 10]
    if n == 5:
        return [1, 3, 5, 7, 9]
    return [1, 2, 3, 4, 6, 8, 10]


def _ordered_sizes(sizes: list[int], order: str) -> list[int]:
    ascending = sorted(sizes)
    if order == "ascending_reading":
        return ascending
    if order == "descending_reading":
        return list(reversed(ascending))
    middle = ascending[len(ascending) // 2]
    rest = [value for value in ascending if value != middle]
    # Put the true median first, then alternate extremes.  It therefore cannot
    # coincide with the reading-order middle for any supported odd object count.
    ordered = [middle]
    while rest:
        ordered.append(rest.pop(0))
        if rest:
            ordered.append(rest.pop(-1))
    return ordered


def _axis_choice(ctx, label: str, default_options: tuple[str, ...], all_options: tuple[str, ...]):
    options = all_options if label in ctx.overrides else default_options
    return ctx.draw_choice(label, options)


def _n_choice(ctx, default_n: int) -> int:
    options = (3, 5, 7) if "n_blobs" in ctx.overrides else (default_n,)
    return int(ctx.draw_choice("n_blobs", options))


def _candidate_placements(
    shape: tuple[tuple[int, int], ...], h: int, w: int
) -> list[tuple[tuple[int, int], ...]]:
    height = max(r for r, _ in shape) + 1
    width = max(c for _, c in shape) + 1
    placements = []
    for top in range(h - height + 1):
        for left in range(w - width + 1):
            placements.append(tuple((top + r, left + c) for r, c in shape))
    return placements


def _touches(cells: Iterable[tuple[int, int]], occupied: set[tuple[int, int]]) -> bool:
    for r, c in cells:
        if (r, c) in occupied:
            return True
        if any((r + dr, c + dc) in occupied for dr, dc in _DIRS):
            return True
    return False


def _place_shapes(
    *,
    h: int,
    w: int,
    sizes_in_reading_order: list[int],
    style: str,
    rng,
) -> list[tuple[tuple[int, int], ...]]:
    """Randomized backtracking with a fixed reading-order contract."""
    for restart in range(96):
        candidate_lists: list[list[tuple[tuple[int, int], ...]]] = []
        for index, area in enumerate(sizes_in_reading_order):
            base = _shape_for(area, style, index)
            orientations = list(_orientations(base))
            rng.shuffle(orientations)
            candidates: list[tuple[tuple[int, int], ...]] = []
            for shape in orientations:
                candidates.extend(_candidate_placements(shape, h, w))
            # Preserve deterministic diversity without relying on global random.
            rng.shuffle(candidates)
            candidate_lists.append(candidates)

        placed: list[tuple[tuple[int, int], ...]] = []
        occupied: set[tuple[int, int]] = set()
        node_budget = 12000

        def search(index: int, previous_first: tuple[int, int]) -> bool:
            nonlocal node_budget
            if index == len(candidate_lists):
                return True
            for cells in candidate_lists[index]:
                node_budget -= 1
                if node_budget <= 0:
                    return False
                first = min(cells)
                if first <= previous_first or _touches(cells, occupied):
                    continue
                placed.append(cells)
                occupied.update(cells)
                if search(index + 1, first):
                    return True
                for cell in cells:
                    occupied.remove(cell)
                placed.pop()
            return False

        if search(0, (-1, -1)):
            return list(placed)
        # The restart changes orientation/candidate ordering and avoids a rare
        # unlucky prefix exhausting the bounded search budget.
        rng.random()
    raise ValueError(
        f"cannot place {len(sizes_in_reading_order)} isolated objects in {h}x{w}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    band = _band(difficulty)
    slot = int(sample_index) % 4
    anchor = slot == 0 and not overrides
    profile_anchor = slot in (0, 1) and not overrides
    requested_n = overrides.get("n_blobs")
    if requested_n is not None and int(requested_n) not in (3, 5, 7):
        raise ValueError("n_blobs must be one of 3, 5, 7")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    default_n = 3 if slot in (0, 1) else (5 if slot == 2 else 7)
    if requested_n is None and ({"grid_h", "grid_w"} & set(overrides)):
        # A dimension boundary by itself must remain realizable; object-count
        # escalation is a separate axis and is only coupled when explicitly set.
        default_n = 3
    n = _n_choice(ctx, default_n)

    # A legal single n_blobs override must not fail because random dimensions
    # were too small.  Explicit incompatible dimension/count combinations may
    # reject loudly, as required by the override contract.
    if profile_anchor:
        profile = _CANONICAL_PROFILES[(int(sample_index) // 4) % len(_CANONICAL_PROFILES)]
        h = ctx.draw_int("grid_h", profile[0], profile[0])
        w = ctx.draw_int("grid_w", profile[1], profile[1])
    else:
        min_h = 8 if n <= 3 else (10 if n == 5 else 12)
        min_w = 8 if n <= 3 else (12 if n == 5 else 14)
        if "grid_h" in overrides:
            h = ctx.draw_int_diff("grid_h", 8, 16)
        else:
            h = ctx.draw_int_diff("grid_h", min_h, 16)
        if "grid_w" in overrides:
            w = ctx.draw_int_diff("grid_w", 8, 18)
        else:
            w = ctx.draw_int_diff("grid_w", min_w, 18)

    default_styles = (
        ("rectangles",) if slot == 0 else ("mixed",) if slot == 1 else ("organic",)
    )
    shape_style = _axis_choice(
        ctx,
        "shape_style",
        default_styles,
        ("rectangles", "mixed", "organic"),
    )
    default_orders = (
        ("ascending_reading",)
        if slot == 0
        else ("shuffled",)
        if slot in (1, 2)
        else ("descending_reading",)
    )
    size_order = _axis_choice(
        ctx,
        "size_order",
        default_orders,
        ("ascending_reading", "descending_reading", "shuffled"),
    )
    default_palettes = (("mixed",), ("warm",), ("cool",), ("mixed",))[slot]
    palette_kind = _axis_choice(
        ctx,
        "palette_kind",
        default_palettes,
        ("mixed", "warm", "cool"),
    )

    sizes = _size_set(n, slot)
    sizes_in_reading_order = _ordered_sizes(sizes, size_order)
    rng = ctx.draw_rng("layout")
    placements = _place_shapes(
        h=h,
        w=w,
        sizes_in_reading_order=sizes_in_reading_order,
        style=shape_style,
        rng=rng,
    )

    colors = list(_PALETTES[palette_kind][:n])
    # Shuffled/color-decoy lessons put the selected object's color at a numeric
    # extreme, ruling out "keep the middle color".
    if size_order == "shuffled":
        selected_size = sorted(sizes)[n // 2]
        selected_index = sizes_in_reading_order.index(selected_size)
        colors[0], colors[selected_index] = colors[selected_index], colors[0]
    elif size_order == "descending_reading":
        colors.reverse()

    grid = full_grid(h, w, 0)
    for color, cells in zip(colors, placements):
        for r, c in cells:
            grid[r][c] = color

    errors = self_check(grid, difficulty=band)
    if errors:
        raise AssertionError("generated invalid median-object lesson: " + "; ".join(errors))
    return grid


def _witness(field: str):
    def predicate(grid) -> bool:
        analysis = _analysis(grid)
        return not analysis["errors"] and bool(analysis[field])

    return predicate


SEMANTIC_WITNESSES = {
    "three_objects": lambda grid: not _analysis(grid)["errors"]
    and _analysis(grid)["n_blobs"] == 3,
    "five_or_seven_objects": lambda grid: not _analysis(grid)["errors"]
    and _analysis(grid)["n_blobs"] >= 5,
    "nonrectangular_object": _witness("has_nonrectangle"),
    "median_not_reading_middle": _witness("median_not_reading_middle"),
    "median_not_numeric_color_middle": _witness("median_not_color_middle"),
    "cell_area_not_bbox_area": _witness("median_not_bbox_middle"),
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations that eliminate the principal shortcut rules."""
    reasons: list[str] = []
    if len(demos) < 3:
        return ["need at least three demonstrations"]

    analyses = []
    for index, pair in enumerate(demos):
        inp = pair.get("input")
        out = pair.get("output")
        analysis = _analysis(inp)
        if analysis["errors"]:
            reasons.append(f"demo {index} input is outside teaching grammar")
            continue
        try:
            expected = expected_output(inp)
        except ValueError as exc:
            reasons.append(f"demo {index} cannot be evaluated: {exc}")
            continue
        if out != expected:
            reasons.append(f"demo {index} output is not the median cell-area object")
        analyses.append(analysis)

    if not any(item["n_blobs"] == 3 for item in analyses):
        reasons.append("no three-object demonstration")
    if not any(item["n_blobs"] >= 5 for item in analyses):
        reasons.append("no demonstration varies the object count above three")
    if not any(item["median_not_reading_middle"] for item in analyses):
        reasons.append("no demonstration refutes reading-order selection")
    if not any(item["median_not_color_middle"] for item in analyses):
        reasons.append("no demonstration refutes numeric-color selection")
    if not any(item["has_nonrectangle"] for item in analyses):
        reasons.append("no demonstration includes a nonrectangular object")
    if not any(item["median_not_bbox_middle"] for item in analyses):
        reasons.append("no demonstration distinguishes cell-area from bounding-box area")

    query_analysis = _analysis(query.get("input"))
    if query_analysis["errors"]:
        reasons.append("query input is outside teaching grammar")
    return reasons
