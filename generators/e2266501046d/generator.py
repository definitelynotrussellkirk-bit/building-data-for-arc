"""Generator for ARC task e2266501046d: fill a hollow rectangle.

The input contains exactly one one-cell-thick, axis-aligned rectangular outline
in a nonzero color.  The selected rule paints that outline's entire bounding
box with the same color on a fresh zero background.

The public axes are intentionally small and exact.  Every declared value is
recoverable from the returned grid, every cross-product is constructible, and
unknown controls fail loudly.  Ordinary examples follow a six-slot teaching
schedule.  Every consecutive three examples include square and non-square
geometry, an interior and an edge-touching placement, and a non-four color;
those three facts jointly refute the named shortcut rules below.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid

GENERATOR_ID = "e2266501046d"
TASK_ID = "e2266501046d"
VERSION = "3.0.1"
RULE_HASH = "efaedeef4719"

SUMMARY = (
    "Find the single nonzero hollow axis-aligned rectangle.  Keep its bounding "
    "box and color, but paint every cell in that box on a fresh zero grid."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the grid is a literal ARC grid with one nonzero color",
    "all nonzero cells are exactly the one-cell perimeter of one rectangle",
    "the rectangle is at least 3x3, so its blank interior is nonempty",
    "the output is same-sized, zero outside the bbox, and solid inside it",
]

RECT_ASPECTS = ("square", "wide", "tall")
EDGE_RELATIONS = (
    "interior",
    "touch_top",
    "touch_bottom",
    "touch_left",
    "touch_right",
)

# Every circular window of length three contains all three aspects, at least
# one interior placement, at least one edge-touching placement, and colors
# 2/4/7.  The lesson-identifiability contract relies on those exact facts.
_ASPECT_SCHEDULE = ("square", "wide", "tall", "square", "wide", "tall")
_EDGE_SCHEDULE = (
    "interior",
    "touch_top",
    "touch_bottom",
    "interior",
    "touch_left",
    "touch_right",
)
_NON_FOUR_COLORS = (1, 2, 3, 5, 6, 7, 8, 9)
SCHEDULE_PROFILES = (
    "slot0_square_interior",
    "slot1_wide_touch_top",
    "slot2_tall_touch_bottom",
    "slot3_square_interior",
    "slot4_wide_touch_left",
    "slot5_tall_touch_right",
)

# Canonical dimensions are deliberately retained in every band.  Exact public
# overrides expose the broader lawful support without letting the default
# curriculum drift away from the task it is supposed to teach.
_CANONICAL_DIMS_BY_BAND = {
    "easy": ((6, 11), (7, 9), (8, 10)),
    "medium": ((7, 9), (8, 10), (8, 12), (9, 9)),
    "hard": ((8, 10), (8, 12), (9, 9)),
    None: ((6, 11), (7, 9), (8, 10), (8, 12), (9, 9)),
}

# These are the complete caller-facing controls.  Every one is exact and is
# returned by observe_overrides().
AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical dimension",
        "valid": "6..14",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical dimension",
        "valid": "9..14",
    },
    "color": {
        "type": "color",
        "default": "three-slot teaching schedule",
        "valid": "1..9",
    },
    "rect_aspect": {
        "type": "str",
        "default": "square|wide|tall teaching schedule",
        "valid": "|".join(RECT_ASPECTS),
    },
    "edge_relation": {
        "type": "str",
        "default": "six-slot interior/edge teaching schedule",
        "valid": "|".join(EDGE_RELATIONS),
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the declared six-slot teaching profile for one draw."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")


def _coerce_grid(grid: Any) -> tuple[list[list[int]], list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return [], ["grid must be a nonempty row sequence"]
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return [], ["every grid row must be a sequence"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return [], ["grid must be nonempty and rectangular"]
    if len(grid) > 30 or width > 30:
        return [], ["grid dimensions must not exceed 30"]

    result: list[list[int]] = []
    for row in grid:
        out_row: list[int] = []
        for value in row:
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 0 <= value <= 9
            ):
                return [], ["grid cells must be literal ARC integers 0..9"]
            out_row.append(value)
        result.append(out_row)
    return result, []


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _analyze(grid: Any) -> dict[str, Any]:
    normalized, errors = _coerce_grid(grid)
    if errors:
        return {"errors": errors}

    height, width = len(normalized), len(normalized[0])
    colors = {
        value for row in normalized for value in row if value != 0
    }
    if len(colors) != 1:
        return {
            "errors": [
                "expected exactly one nonzero rectangle color, got "
                f"{sorted(colors)}"
            ]
        }
    color = next(iter(colors))
    cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if normalized[row][col] == color
    ]
    if not cells:
        return {"errors": ["expected a hollow rectangle, found no colored cells"]}

    top, left, bottom, right = _bbox(cells)
    rect_height = bottom - top + 1
    rect_width = right - left + 1
    if rect_height < 3 or rect_width < 3:
        errors.append(
            f"rectangle bbox must be at least 3x3, got {rect_height}x{rect_width}"
        )

    expected_perimeter = {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if row in (top, bottom) or col in (left, right)
    }
    actual_cells = set(cells)
    if actual_cells != expected_perimeter:
        missing = len(expected_perimeter - actual_cells)
        extra = len(actual_cells - expected_perimeter)
        errors.append(
            "nonzero cells must equal exactly one rectangular perimeter "
            f"(missing={missing}, extra={extra})"
        )

    if rect_width > rect_height:
        aspect = "wide"
    elif rect_height > rect_width:
        aspect = "tall"
    else:
        aspect = "square"

    touched: list[str] = []
    if top == 0:
        touched.append("touch_top")
    if bottom == height - 1:
        touched.append("touch_bottom")
    if left == 0:
        touched.append("touch_left")
    if right == width - 1:
        touched.append("touch_right")
    edge_relation = "interior" if not touched else (
        touched[0] if len(touched) == 1 else "multiple_edges"
    )

    return {
        "errors": errors,
        "grid": normalized,
        "height": height,
        "width": width,
        "color": color,
        "cells": actual_cells,
        "bbox": (top, left, bottom, right),
        "rect_height": rect_height,
        "rect_width": rect_width,
        "rect_aspect": aspect,
        "edge_relation": edge_relation,
        "touched_edges": touched,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    if isinstance(nested, dict):
        return dict(nested)
    return {name: meta[name] for name in AXES if name in meta}


def observe_overrides(grid: Any) -> dict[str, Any]:
    """Recover every declared exact axis from a valid generated grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    if analysis["edge_relation"] == "multiple_edges":
        raise ValueError(
            "rectangle touches multiple canvas edges; outside public edge domain"
        )
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "color": analysis["color"],
        "rect_aspect": analysis["rect_aspect"],
        "edge_relation": analysis["edge_relation"],
    }


def self_check(grid: Any, *, difficulty=None, meta=None) -> list[str]:
    """Accept the authority grammar and reject ambiguous/impostor inputs."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    requested = _meta_overrides(meta)
    if requested and not errors:
        try:
            observed = observe_overrides(analysis["grid"])
        except ValueError as exc:
            errors.append(f"could not observe exact axes: {exc}")
        else:
            for name, expected in requested.items():
                if name not in AXES:
                    continue
                actual = observed.get(name)
                if type(actual) is not type(expected) or actual != expected:
                    errors.append(
                        f"override {name!r} requested {expected!r}, observed "
                        f"{actual!r}"
                    )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """The strict task manifold is exactly the valid hollow-rectangle grammar."""
    return self_check(grid)


def rule_mirror(grid: Any) -> list[list[int]]:
    """Pure Python mirror used only for tests and semantic adversaries."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid hollow-rectangle input: " + "; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 0)
    top, left, bottom, right = analysis["bbox"]
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            output[row][col] = analysis["color"]
    return output


def _rival_square_only(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    return (
        rule_mirror(grid)
        if analysis["rect_aspect"] == "square"
        else [row[:] for row in analysis["grid"]]
    )


def _rival_fixed_color_four(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    output = full_grid(analysis["height"], analysis["width"], 0)
    top, left, bottom, right = analysis["bbox"]
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            output[row][col] = 4
    return output


def _rival_interior_only(grid: Any) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    return (
        rule_mirror(grid)
        if analysis["edge_relation"] == "interior"
        else [row[:] for row in analysis["grid"]]
    )


def _fact(predicate: Callable[[dict[str, Any]], bool]) -> Callable[[Any], bool]:
    def witness(grid: Any) -> bool:
        analysis = _analyze(grid)
        return not analysis["errors"] and bool(predicate(analysis))

    return witness


SEMANTIC_WITNESSES = {
    "square_outline": _fact(lambda facts: facts["rect_aspect"] == "square"),
    "non_square_outline": _fact(lambda facts: facts["rect_aspect"] != "square"),
    "interior_placement": _fact(lambda facts: facts["edge_relation"] == "interior"),
    "edge_touching": _fact(
        lambda facts: facts["edge_relation"] in set(EDGE_RELATIONS) - {"interior"}
    ),
    "non_four_color": _fact(lambda facts: facts["color"] != 4),
}
BRANCH_WITNESSES = {"square_outline", "interior_placement"}

SEMANTIC_RIVALS = {
    "square_only_fill": _rival_square_only,
    "fixed_color_four": _rival_fixed_color_four,
    "interior_only_fill": _rival_interior_only,
}
WITNESS_RIVALS = {
    "non_square_outline": ["square_only_fill"],
    "edge_touching": ["interior_only_fill"],
    "non_four_color": ["fixed_color_four"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# Every official pair leaves a zero margin around the rectangle, so canonical
# examples alone cannot falsify this wrong edge-sensitive shortcut.
CANONICAL_SHORTCUTS = {"interior_only_fill": _rival_interior_only}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Require a valid three-demo lesson that refutes every named competitor."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    reasons: list[str] = []
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    elif self_check(query["input"]):
        reasons.append("query input is outside the hollow-rectangle grammar")

    valid_demos: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is outside the grammar: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the selected rule")
        valid_demos.append(demo)

    if len(valid_demos) == len(demos):
        for name, rival in LESSON_COMPETITORS.items():
            if all(rival(demo["input"]) == demo["output"] for demo in valid_demos):
                reasons.append(f"named competitor survives all demonstrations: {name}")
    return reasons


def _scheduled_defaults(
    seed: int, sample_index: int, difficulty: str | None
) -> dict[str, Any]:
    slot = int(sample_index) % len(SCHEDULE_PROFILES)
    dimensions = _CANONICAL_DIMS_BY_BAND[difficulty]
    rng = stable_rng(
        seed, f"{TASK_ID}|{sample_index}|scheduled_defaults", VERSION
    )

    # One member of every three-example lesson is pinned to an exact canonical
    # dimension profile.  The other two vary across the wider lawful support,
    # increasing episode diversity without sacrificing canonical anchoring.
    if int(sample_index) % EXAMPLES_NEEDED == 0:
        height, width = dimensions[
            (int(sample_index) // EXAMPLES_NEEDED) % len(dimensions)
        ]
    else:
        height_ranges = {
            "easy": (6, 9),
            "medium": (7, 12),
            "hard": (9, 14),
            None: (6, 14),
        }
        width_ranges = {
            "easy": (9, 12),
            "medium": (9, 14),
            "hard": (10, 14),
            None: (9, 14),
        }
        height = rng.randint(*height_ranges[difficulty])
        width = rng.randint(*width_ranges[difficulty])

    return {
        "grid_h": height,
        "grid_w": width,
        # Every default color is deliberately non-four, so every lesson
        # falsifies the plausible fixed-color-four shortcut while still
        # varying across eight foreground colors.
        "color": rng.choice(_NON_FOUR_COLORS),
        "rect_aspect": _ASPECT_SCHEDULE[slot],
        "edge_relation": _EDGE_SCHEDULE[slot],
    }


def _choose_rect_size(
    aspect: str, height: int, width: int, rng: Any
) -> tuple[int, int]:
    # Reserve at least one zero row/column beyond every non-selected edge, so
    # each public edge_relation is unambiguous and all cross-products exist.
    max_height = height - 2
    max_width = width - 2
    if aspect == "square":
        side = rng.randint(3, min(max_height, max_width))
        return side, side
    if aspect == "wide":
        rect_height = rng.randint(3, min(max_height, max_width - 1))
        rect_width = rng.randint(rect_height + 1, max_width)
        return rect_height, rect_width
    if aspect == "tall":
        rect_width = rng.randint(3, min(max_width, max_height - 1))
        rect_height = rng.randint(rect_width + 1, max_height)
        return rect_height, rect_width
    raise AssertionError(f"unknown aspect: {aspect}")


def _choose_position(
    relation: str,
    height: int,
    width: int,
    rect_height: int,
    rect_width: int,
    rng: Any,
) -> tuple[int, int]:
    interior_row = lambda: rng.randint(1, height - rect_height - 1)
    interior_col = lambda: rng.randint(1, width - rect_width - 1)
    if relation == "interior":
        return interior_row(), interior_col()
    if relation == "touch_top":
        return 0, interior_col()
    if relation == "touch_bottom":
        return height - rect_height, interior_col()
    if relation == "touch_left":
        return interior_row(), 0
    if relation == "touch_right":
        return interior_row(), width - rect_width
    raise AssertionError(f"unknown edge relation: {relation}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input; the selected Racket rule owns output."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    _validate_overrides(overrides)
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")

    effective = _scheduled_defaults(seed, int(sample_index), difficulty)
    effective.update(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    height = ctx.draw_int_strict("grid_h", 6, 14)
    width = ctx.draw_int_strict("grid_w", 9, 14)
    color = ctx.draw_color_strict("color", exclude={0})
    aspect = ctx.draw_choice("rect_aspect", RECT_ASPECTS)
    relation = ctx.draw_choice("edge_relation", EDGE_RELATIONS)
    rng = ctx.draw_rng("geometry")

    rect_height, rect_width = _choose_rect_size(aspect, height, width, rng)
    top, left = _choose_position(
        relation, height, width, rect_height, rect_width, rng
    )
    grid = full_grid(height, width, 0)
    draw_rect_outline(grid, top, left, rect_height, rect_width, color)

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": effective},
    )
    if errors:
        raise AssertionError("constructed invalid hollow rectangle: " + "; ".join(errors))
    return grid


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Targeted malformed inputs used by focused regression tests."""
    base = generate(901, 0, difficulty="easy", grid_h=8, grid_w=10)
    facts = _analyze(base)
    top, left, bottom, right = facts["bbox"]
    color = facts["color"]

    missing_corner = [row[:] for row in base]
    missing_corner[top][left] = 0

    filled_interior = [row[:] for row in base]
    filled_interior[top + 1][left + 1] = color

    outside_cell = [row[:] for row in base]
    outside_row = 0 if top > 0 else len(base) - 1
    outside_col = 0 if left > 0 else len(base[0]) - 1
    outside_cell[outside_row][outside_col] = color

    mixed_color = [row[:] for row in base]
    mixed_color[top][left] = 9 if color != 9 else 8

    solid_rectangle = rule_mirror(base)
    return [
        ("missing_corner", missing_corner),
        ("filled_interior", filled_interior),
        ("outside_cell", outside_cell),
        ("mixed_color", mixed_color),
        ("solid_rectangle", solid_rectangle),
    ]


def negative_recombination_fixture() -> tuple[list[list[int]], str]:
    """Two valid outlines recombined into one invalid multi-object scene."""
    grid = full_grid(10, 13, 0)
    draw_rect_outline(grid, 1, 1, 3, 4, 6)
    draw_rect_outline(grid, 6, 8, 3, 4, 6)
    return grid, "two_disjoint_outlines"
