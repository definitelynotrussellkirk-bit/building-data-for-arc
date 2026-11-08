"""Generator for ARC task e88171ec / task id 1e7eb285f158.

Rule: enumerate every all-zero axis-aligned rectangle of height and width at
least three.  Select maximum area, breaking ties by top row and then left
column, and paint only its strict one-cell-inset interior cyan (8).

The distribution deliberately includes one- and two-nonzero-color textures,
three noise levels, five target positions, non-square rectangles, and simple
row/column ties that expose the oracle's top/left tie-break.  Outside the
planted rectangle(s), zeros occur in separated 1x1, 1x2, or 2x2 micro-blocks
on a 3x3 lattice, so they cannot form an accidental 3x3 competitor or extend
a planted rectangle by a complete row or column.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "1e7eb285f158"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "d40abed3e512"  # sha256[:12] of normalized canonical program_solution

SUMMARY = (
    "A 12..21 by 12..21 grid contains one or, for tie-break lessons, two "
    "largest all-zero rectangles at least 3x3 amid separated micro-block "
    "zero noise and one or two nonzero texture colors. Enumerate all all-zero "
    "rectangles with both dimensions at least three; choose maximum area, "
    "breaking ties by top row then left column; paint only that rectangle's "
    "strict one-cell-inset interior cyan (8)."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.99

INVARIANTS = [
    "input uses zero plus one or two nonzero colors from 1..7; cyan 8 is absent",
    "at least one all-zero rectangle has height and width >=3",
    "the selected maximum rectangle has a nonempty strict interior",
    "ordinary four-sample lessons schedule unique, row-tie, column-tie, unique scenes",
    "separated outside-zero micro-blocks cannot create or extend a 3x3 competitor",
]

POSITION_BIASES = (
    "top_left",
    "top_right",
    "bottom_left",
    "bottom_right",
    "center",
)
PALETTE_MODES = ("one_nonzero", "two_nonzero")
NOISE_LEVELS = ("sparse", "balanced", "dense")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware keyed draw 12..21",
        "valid": "12..21",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware keyed draw 12..21",
        "valid": "12..21",
    },
    "rect_h": {
        "type": "int",
        "default": "difficulty-aware keyed draw 3..7",
        "valid": "3..7",
    },
    "rect_w": {
        "type": "int",
        "default": "difficulty-aware keyed draw 3..7",
        "valid": "3..7",
    },
    "foreground_color": {
        "type": "color",
        "default": "keyed draw 1..7",
        "valid": "1..7",
    },
    "palette_mode": {
        "type": "str",
        "default": "keyed one_nonzero|two_nonzero",
        "valid": "one_nonzero|two_nonzero",
    },
    "noise_level": {
        "type": "str",
        "default": "keyed sparse|balanced|dense",
        "valid": "sparse|balanced|dense",
    },
    "position_bias": {
        "type": "str",
        "default": "keyed five-way placement",
        "valid": "top_left|top_right|bottom_left|bottom_right|center",
    },
}

Rect = tuple[int, int, int, int]


def _max_zero_rectangles(grid: list[list[int]]) -> list[Rect]:
    """Return every maximum-area all-zero rectangle (minimum 3x3).

    O(h^2*w): for each top/bottom pair, maintain columns that are all zero and
    take each maximal contiguous run.  A global maximum rectangle is maximal
    in width for its row span, so no candidate can be missed.
    """
    height, width = len(grid), len(grid[0])
    best_area = 0
    best: list[Rect] = []
    column_clear = [True] * width
    for top in range(height):
        column_clear[:] = [True] * width
        for bottom in range(top, height):
            for col in range(width):
                column_clear[col] = column_clear[col] and grid[bottom][col] == 0
            rect_h = bottom - top + 1
            if rect_h < 3:
                continue
            col = 0
            while col < width:
                if not column_clear[col]:
                    col += 1
                    continue
                left = col
                while col < width and column_clear[col]:
                    col += 1
                right = col - 1
                rect_w = right - left + 1
                if rect_w < 3:
                    continue
                area = rect_h * rect_w
                candidate = (top, left, bottom, right)
                if area > best_area:
                    best_area = area
                    best = [candidate]
                elif area == best_area:
                    best.append(candidate)
    # Matches the canonical enumeration's residual order after area/top/left:
    # bottom row, then right column.
    return sorted(set(best), key=lambda rect: (rect[0], rect[1], rect[2], rect[3]))


def _rect_cells(rect: Rect) -> set[tuple[int, int]]:
    top, left, bottom, right = rect
    return {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
    }


def _position_for(mode: str, height: int, width: int, rh: int, rw: int) -> tuple[int, int]:
    if mode == "top_left":
        return 1, 1
    if mode == "top_right":
        return 1, width - rw - 1
    if mode == "bottom_left":
        return height - rh - 1, 1
    if mode == "bottom_right":
        return height - rh - 1, width - rw - 1
    if mode == "center":
        return (height - rh) // 2, (width - rw) // 2
    raise ValueError(f"unknown position_bias {mode!r}")


def _classify_position(height: int, width: int, rect: Rect) -> str | None:
    top, left, bottom, right = rect
    rh, rw = bottom - top + 1, right - left + 1
    candidates = {
        mode: _position_for(mode, height, width, rh, rw)
        for mode in POSITION_BIASES
    }
    for mode in POSITION_BIASES:
        if candidates[mode] == (top, left):
            return mode
    return None


def _noise_predicate(level: str, row: int, col: int, phase: int) -> bool:
    """Separated micro-block texture with no all-zero 3x3 outside the target."""
    row_mod = (row + phase) % 3
    col_mod = (col + phase // 3) % 3
    if level == "sparse":
        return row_mod == 0 and col_mod == 0
    if level == "balanced":
        return row_mod == 0 and col_mod in (0, 1)
    if level == "dense":
        return row_mod in (0, 1) and col_mod in (0, 1)
    raise ValueError(f"unknown noise_level {level!r}")


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid must be a non-empty list-of-lists"]}
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular and non-empty"]}
    height = len(grid)
    if not (12 <= height <= 30 and 12 <= width <= 30):
        errors.append(f"grid dimensions must be 12..30, got {height}x{width}")

    flat = [value for row in grid for value in row]
    invalid = [
        value
        for value in flat
        if not isinstance(value, int)
        or isinstance(value, bool)
        or value < 0
        or value > 9
    ]
    if invalid:
        errors.append(f"grid contains invalid ARC values: {invalid[:3]}")
        return {"errors": errors}
    if 8 in flat:
        errors.append("input must not already contain output color 8")
    if 9 in flat:
        errors.append("task grammar uses only input colors 0..7")

    counts = Counter(flat)
    nonzero_colors = sorted(color for color in counts if color != 0)
    if not (1 <= len(nonzero_colors) <= 2):
        errors.append(
            f"expected one or two nonzero texture colors, found {nonzero_colors}"
        )
    total = height * width
    zero_ratio = counts.get(0, 0) / total
    if not (0.08 <= zero_ratio <= 0.78):
        errors.append(f"zero fraction {zero_ratio:.3f} outside 0.08..0.78")

    rects = _max_zero_rectangles(grid)
    if not rects:
        errors.append("no all-zero rectangle with height and width at least three")
        return {"errors": errors}
    best = rects[0]
    top, left, bottom, right = best
    rect_h, rect_w = bottom - top + 1, right - left + 1
    if rect_h > 8 or rect_w > 8:
        errors.append(f"largest zero rectangle too large for task grammar: {rect_h}x{rect_w}")

    max_area = rect_h * rect_w
    max_rects = [
        rect
        for rect in rects
        if (rect[2] - rect[0] + 1) * (rect[3] - rect[1] + 1) == max_area
    ]
    same_shape = all(
        rect[2] - rect[0] + 1 == rect_h and rect[3] - rect[1] + 1 == rect_w
        for rect in max_rects
    )
    if not same_shape:
        errors.append("equal-area maxima with different shapes are outside the teaching grammar")

    if len(max_rects) == 1:
        tie_kind = "unique"
    elif all(rect[0] == top and rect[2] == bottom for rect in max_rects):
        tie_kind = "row_tie"
    elif all(rect[1] == left and rect[3] == right for rect in max_rects):
        tie_kind = "column_tie"
    else:
        tie_kind = "complex_tie"
        errors.append("maximum rectangles must be unique or a simple row/column tie")

    target_cells: set[tuple[int, int]] = set()
    for rect in max_rects:
        target_cells |= _rect_cells(rect)
    outside_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in target_cells
    ]
    outside_zeros = sum(grid[row][col] == 0 for row, col in outside_cells)
    if outside_zeros < 6:
        errors.append(f"expected scattered zero texture outside target, found {outside_zeros}")
    outside_zero_rate = outside_zeros / len(outside_cells) if outside_cells else 0.0

    position_bias = _classify_position(height, width, best)
    foreground_color = None
    if nonzero_colors:
        foreground_color = max(nonzero_colors, key=lambda color: (counts[color], -color))
    palette_mode = (
        "one_nonzero" if len(nonzero_colors) == 1 else
        "two_nonzero" if len(nonzero_colors) == 2 else None
    )

    # Generated textures have an exact 3x3-lattice signature. Recover it
    # structurally instead of inferring from a fragile density threshold: tie
    # lessons remove two large target regions, which legitimately shifts the
    # residual zero rate. A second nonzero marker is excluded from comparison.
    noise_scores: dict[str, int] = {}
    if foreground_color is not None:
        score_cells = [
            (row, col)
            for row, col in outside_cells
            if grid[row][col] in (0, foreground_color)
        ]
        for level in NOISE_LEVELS:
            noise_scores[level] = min(
                sum(
                    (grid[row][col] == 0)
                    != _noise_predicate(level, row, col, phase)
                    for row, col in score_cells
                )
                for phase in range(9)
            )
    exact_levels = [level for level, score in noise_scores.items() if score == 0]
    if len(exact_levels) == 1:
        noise_level = exact_levels[0]
    elif outside_zero_rate < 0.18:
        noise_level = "sparse"
    elif outside_zero_rate < 0.34:
        noise_level = "balanced"
    else:
        noise_level = "dense"

    return {
        "errors": errors,
        "facts": {
            "grid_h": height,
            "grid_w": width,
            "zero_ratio": zero_ratio,
            "best": best,
            "max_rects": max_rects,
            "rect_h": rect_h,
            "rect_w": rect_w,
            "max_area": max_area,
            "tie_kind": tie_kind,
            "position_bias": position_bias,
            "foreground_color": foreground_color,
            "palette_mode": palette_mode,
            "nonzero_colors": nonzero_colors,
            "outside_zeros": outside_zeros,
            "outside_zero_rate": outside_zero_rate,
            "noise_level": noise_level,
        },
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate a deterministic, non-degenerate task input.

    With no overrides, sample_index mod 4 schedules unique, row-tie,
    column-tie, unique.  That makes every ordinary three-demo lesson expose
    both top/left tie branches before its query.  Explicit overrides disable
    the hidden tie schedule so every declared boundary combination remains
    exact and independently testable.
    """
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    desired_tie = "unique"
    if not overrides:
        desired_tie = ("unique", "row_tie", "column_tie", "unique")[
            sample_index % 4
        ]

    height = ctx.draw_int_diff("grid_h", 12, 21)
    width = ctx.draw_int_diff("grid_w", 12, 21)
    if desired_tie == "column_tie":
        rect_h = ctx.draw_int_diff("rect_h", 3, min(7, (height - 2) // 2))
    else:
        rect_h = ctx.draw_int_diff("rect_h", 3, 7)
    if desired_tie == "row_tie":
        rect_w = ctx.draw_int_diff("rect_w", 3, min(7, (width - 2) // 2))
        position_options = ("top_left", "bottom_left")
    else:
        rect_w = ctx.draw_int_diff("rect_w", 3, 7)
        position_options = POSITION_BIASES
    if desired_tie == "column_tie":
        position_options = ("top_left", "top_right")

    foreground = ctx.draw_choice("foreground_color", tuple(range(1, 8)))
    palette_mode = ctx.draw_choice("palette_mode", PALETTE_MODES)
    noise_level = ctx.draw_choice("noise_level", NOISE_LEVELS)
    position_bias = ctx.draw_choice("position_bias", position_options)

    grid = [[foreground for _ in range(width)] for _ in range(height)]
    distractor = None
    distractor_phase = 0
    if palette_mode == "two_nonzero":
        distractor = ctx.draw_choice(
            "distractor_color",
            tuple(color for color in range(1, 8) if color != foreground),
        )
        distractor_phase = ctx.draw_rng("distractor_phase").randrange(64)

    top, left = _position_for(
        position_bias, height, width, rect_h, rect_w
    )
    target_rects: list[Rect] = [
        (top, left, top + rect_h - 1, left + rect_w - 1)
    ]
    if desired_tie == "row_tie":
        second_left = left + rect_w + 1
        if second_left + rect_w <= width:
            target_rects.append(
                (top, second_left, top + rect_h - 1, second_left + rect_w - 1)
            )
        else:
            desired_tie = "unique"
    elif desired_tie == "column_tie":
        second_top = top + rect_h + 1
        if second_top + rect_h <= height:
            target_rects.append(
                (second_top, left, second_top + rect_h - 1, left + rect_w - 1)
            )
        else:
            desired_tie = "unique"

    target_cells: set[tuple[int, int]] = set()
    for rect in target_rects:
        target_cells |= _rect_cells(rect)
        r0, c0, r1, c1 = rect
        for row in range(r0, r1 + 1):
            for col in range(c0, c1 + 1):
                grid[row][col] = 0

    phase = ctx.draw_rng("noise_phase").randrange(9)
    for row in range(height):
        for col in range(width):
            if (row, col) in target_cells:
                continue
            if _noise_predicate(noise_level, row, col, phase):
                grid[row][col] = 0

    # A second input color is a single connected top-edge marker, not pepper
    # noise. Row 0 is outside every planted rectangle, including the second
    # rectangle in a column-tie lesson, so it cannot alter the rule branch.
    if distractor is not None:
        marker_row = 0
        marker_len = 3 + (distractor_phase // 2) % min(5, width - 2)
        span = width - marker_len - 1
        marker_left = 1 + (distractor_phase // 10) % max(1, span)
        for col in range(marker_left, marker_left + marker_len):
            grid[marker_row][col] = distractor

    # Fail closed if a future edit violates a declared exact axis or permits an
    # accidental competitor.  This is deterministic and has no side effects.
    observed = observe_overrides(grid)
    requested = ctx.recorded_draws()
    for axis in AXES:
        if axis in observed and axis in requested and observed[axis] != requested[axis]:
            raise RuntimeError(
                f"internal axis drift: {axis} requested {requested[axis]!r}, "
                f"observed {observed[axis]!r}"
            )
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("generated invalid scene: " + "; ".join(errors))
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural teaching-grammar check; accepts every canonical input."""
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Task-linked canonical-manifold predicate used by the semantic gate."""
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    facts = analysis["facts"]
    if facts["grid_h"] > 21 or facts["grid_w"] > 21:
        errors.append("canonical-scale envelope is 12..21 in each dimension")
    if not (3 <= facts["rect_h"] <= 7 and 3 <= facts["rect_w"] <= 7):
        errors.append("largest zero rectangle must be 3..7 by 3..7")
    if facts["position_bias"] is None:
        # Canonical examples need not sit at a generated named anchor.  Their
        # dimensions/palette/zero grammar are still canonical, so this remains
        # an observability distinction rather than a rejection.
        pass
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared exact axis from a valid returned grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    facts = analysis["facts"]
    observed: dict[str, int | str] = {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "rect_h": facts["rect_h"],
        "rect_w": facts["rect_w"],
        "foreground_color": facts["foreground_color"],
        "palette_mode": facts["palette_mode"],
        "noise_level": facts["noise_level"],
    }
    if facts["position_bias"] is not None:
        observed["position_bias"] = facts["position_bias"]
    return observed


def semantic_signature(grid) -> dict[str, Any]:
    """Count-backed task observables for focused tests and review censuses."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    facts = analysis["facts"]
    return {
        "errors": [],
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "rect_h": facts["rect_h"],
        "rect_w": facts["rect_w"],
        "max_area": facts["max_area"],
        "max_rect_count": len(facts["max_rects"]),
        "tie_kind": facts["tie_kind"],
        "position_bias": facts["position_bias"],
        "foreground_color": facts["foreground_color"],
        "palette_mode": facts["palette_mode"],
        "nonzero_colors": facts["nonzero_colors"],
        "noise_level": facts["noise_level"],
        "outside_zero_rate": facts["outside_zero_rate"],
        "changed_cells": (facts["rect_h"] - 2) * (facts["rect_w"] - 2),
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for tests; Racket remains output authority."""
    rects = _max_zero_rectangles(grid)
    if not rects:
        return [row[:] for row in grid]
    top, left, bottom, right = rects[0]
    output = [row[:] for row in grid]
    for row in range(top + 1, bottom):
        for col in range(left + 1, right):
            output[row][col] = 8
    return output


def _competitor_full_rectangle(grid: list[list[int]]) -> list[list[int]]:
    rects = _max_zero_rectangles(grid)
    output = [row[:] for row in grid]
    if rects:
        top, left, bottom, right = rects[0]
        for row in range(top, bottom + 1):
            for col in range(left, right + 1):
                output[row][col] = 8
    return output


def _competitor_all_ties(grid: list[list[int]]) -> list[list[int]]:
    output = [row[:] for row in grid]
    for top, left, bottom, right in _max_zero_rectangles(grid):
        for row in range(top + 1, bottom):
            for col in range(left + 1, right):
                output[row][col] = 8
    return output


def _competitor_foreground_echo(grid: list[list[int]]) -> list[list[int]]:
    rects = _max_zero_rectangles(grid)
    output = [row[:] for row in grid]
    nonzero = Counter(value for row in grid for value in row if value != 0)
    color = nonzero.most_common(1)[0][0] if nonzero else 8
    if rects:
        top, left, bottom, right = rects[0]
        for row in range(top + 1, bottom):
            for col in range(left + 1, right):
                output[row][col] = color
    return output


def _competitor_first_3x3(grid: list[list[int]]) -> list[list[int]]:
    output = [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    for top in range(height - 2):
        for left in range(width - 2):
            if all(
                grid[row][col] == 0
                for row in range(top, top + 3)
                for col in range(left, left + 3)
            ):
                output[top + 1][left + 1] = 8
                return output
    return output


_COMPETITORS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "paint_full_rectangle": _competitor_full_rectangle,
    "paint_all_maximum_ties": _competitor_all_ties,
    "echo_modal_foreground": _competitor_foreground_echo,
    "paint_first_3x3_center": _competitor_first_3x3,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a plausible rival fits demos but changes query."""
    reasons: list[str] = []
    for name, competitor in _COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            predicted = competitor(query["input"])
            if predicted != query["output"]:
                reasons.append(
                    f"competitor {name} fits every demonstration but changes query"
                )
    return reasons


def _witness(grid, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    signature = semantic_signature(grid)
    return not signature.get("errors") and bool(predicate(signature))


SEMANTIC_WITNESSES = {
    "unique_maximum": lambda grid: _witness(grid, lambda s: s["tie_kind"] == "unique"),
    "row_tie_top_then_left": lambda grid: _witness(grid, lambda s: s["tie_kind"] == "row_tie"),
    "column_tie_top_then_left": lambda grid: _witness(grid, lambda s: s["tie_kind"] == "column_tie"),
    "single_nonzero_palette": lambda grid: _witness(grid, lambda s: s["palette_mode"] == "one_nonzero"),
    "two_nonzero_palette": lambda grid: _witness(grid, lambda s: s["palette_mode"] == "two_nonzero"),
    "sparse_noise": lambda grid: _witness(grid, lambda s: s["noise_level"] == "sparse"),
    "balanced_noise": lambda grid: _witness(grid, lambda s: s["noise_level"] == "balanced"),
    "dense_noise": lambda grid: _witness(grid, lambda s: s["noise_level"] == "dense"),
    "non_square_target": lambda grid: _witness(grid, lambda s: s["rect_h"] != s["rect_w"]),
    "off_center_target": lambda grid: _witness(grid, lambda s: s["position_bias"] != "center"),
}
