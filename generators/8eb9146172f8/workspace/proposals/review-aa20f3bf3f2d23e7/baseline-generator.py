"""Generator for ARC task f15e1fac / generator ``8eb9146172f8``.

Cyan 8 markers occupy one outer edge and red 2 markers a perpendicular
edge.  Every cyan marker emits a ray straight into the grid.  On each row
or column selected by a red marker, the ray first moves one cell away from
the red edge and then paints the new cell.  Input markers remain in place.

The canonical examples do not contain bottom-origin vertical rays, and all
horizontal canonical rays have their red markers on the bottom edge.  This
generator therefore deliberately emits bottom-origin and red-on-top cases;
those are counterexamples to two plausible direction shortcuts recorded in
``CANONICAL_SHORTCUTS``.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8eb9146172f8"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "5592536df499"
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Place cyan 8 markers on one edge and red 2 markers on a perpendicular "
    "edge. Each cyan marker emits a ray inward. Whenever the ray reaches a "
    "red marker's row or column, it steps one cell away from the red edge "
    "before continuing. All four cyan edges and both deflection directions "
    "are generated, including bottom-origin and red-on-top counterexamples "
    "that the canonical demonstrations omit."
)

INVARIANTS = [
    "the only colors are background 0, red 2, and cyan 8",
    "all cyan markers lie on exactly one non-corner edge",
    "all red markers lie on exactly one perpendicular non-corner edge",
    "there are one through four markers of each color",
    "ray cells outside the canvas are clipped while input markers remain",
]

EDGES = ("top", "bottom", "left", "right")
_VERTICAL_EDGES = frozenset(("top", "bottom"))
_HORIZONTAL_EDGES = frozenset(("left", "right"))

_CANONICAL_DIMENSIONS = ((14, 10), (17, 12), (12, 12), (12, 17))

AXES = {
    "grid_h": {"type": "int", "default": "canonical-profile anchor", "valid": "9..20"},
    "grid_w": {"type": "int", "default": "canonical-profile anchor", "valid": "9..22"},
    "cyan_edge": {
        "type": "str",
        "default": "varies",
        "valid": "top|bottom|left|right",
    },
    "red_edge": {
        "type": "str",
        "default": "perpendicular to cyan_edge",
        "valid": "top|bottom|left|right",
    },
    "n_red": {"type": "int", "default": "difficulty-scaled", "valid": "1..4"},
    "n_cyan": {"type": "int", "default": "difficulty-scaled", "valid": "1..4"},
}

# Parallel edge requests violate the task premise.  Declaring every concrete
# pair lets the override-contract checker distinguish intentional rejection
# from an accidental multi-axis failure.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = (
    {"cyan_edge": "top", "red_edge": "top"},
    {"cyan_edge": "top", "red_edge": "bottom"},
    {"cyan_edge": "bottom", "red_edge": "top"},
    {"cyan_edge": "bottom", "red_edge": "bottom"},
    {"cyan_edge": "left", "red_edge": "left"},
    {"cyan_edge": "left", "red_edge": "right"},
    {"cyan_edge": "right", "red_edge": "left"},
    {"cyan_edge": "right", "red_edge": "right"},
)
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()


def _perpendicular(first: str, second: str) -> bool:
    """Return whether two named edges meet at right angles."""
    return (first in _VERTICAL_EDGES and second in _HORIZONTAL_EDGES) or (
        first in _HORIZONTAL_EDGES and second in _VERTICAL_EDGES
    )


def _perpendicular_edges(edge: str) -> tuple[str, str]:
    if edge in _VERTICAL_EDGES:
        return ("left", "right")
    if edge in _HORIZONTAL_EDGES:
        return ("top", "bottom")
    raise ValueError(f"unknown edge {edge!r}")


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")

    for name in ("grid_h", "grid_w", "n_red", "n_cyan"):
        if name in overrides and overrides[name] is not None:
            value = overrides[name]
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{name} must be an integer")

    for name in ("cyan_edge", "red_edge"):
        if name in overrides and overrides[name] is not None:
            value = overrides[name]
            if not isinstance(value, str) or value not in EDGES:
                raise ValueError(f"{name} must be one of {EDGES}, got {value!r}")

    cyan = overrides.get("cyan_edge")
    red = overrides.get("red_edge")
    if cyan is not None and red is not None and not _perpendicular(cyan, red):
        raise ValueError(
            f"cyan_edge={cyan!r} and red_edge={red!r} must be perpendicular"
        )


def _draw_edges(ctx, overrides: dict[str, Any]) -> tuple[str, str]:
    """Consume both exact edge axes while respecting a single-edge pin."""
    cyan_pinned = overrides.get("cyan_edge") is not None
    red_pinned = overrides.get("red_edge") is not None

    if red_pinned and not cyan_pinned:
        red_edge = ctx.draw_choice("red_edge", EDGES)
        cyan_edge = ctx.draw_choice("cyan_edge", _perpendicular_edges(red_edge))
    else:
        cyan_edge = ctx.draw_choice("cyan_edge", EDGES)
        red_edge = ctx.draw_choice("red_edge", _perpendicular_edges(cyan_edge))
    return cyan_edge, red_edge


def _shift_for_red_edge(red_edge: str) -> int:
    # Away from top/left means increasing row/column; away from bottom/right
    # means decreasing it.
    return 1 if red_edge in ("top", "left") else -1


def _edge_cell(edge: str, position: int, h: int, w: int) -> tuple[int, int]:
    if edge == "top":
        return (0, position)
    if edge == "bottom":
        return (h - 1, position)
    if edge == "left":
        return (position, 0)
    if edge == "right":
        return (position, w - 1)
    raise ValueError(f"unknown edge {edge!r}")


def _edge_length(edge: str, h: int, w: int) -> int:
    return w if edge in _VERTICAL_EDGES else h


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one exact, observable instance of the staircase-ray rule."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # The profile floor is a support requirement, not merely a broad size
    # envelope.  With no dimension pins, anchor every band to one of the four
    # published (height, width) profiles.  A caller may still exercise every
    # declared boundary through exact overrides; single-dimension pins use the
    # full difficulty-scaled domain for the unpinned partner.
    if overrides.get("grid_h") is None and overrides.get("grid_w") is None:
        profile = ctx.draw_rng("canonical_dimensions").choice(
            _CANONICAL_DIMENSIONS
        )
        h = ctx.draw_choice("grid_h", (profile[0],))
        w = ctx.draw_choice("grid_w", (profile[1],))
    else:
        h = ctx.draw_int_diff("grid_h", 9, 20)
        w = ctx.draw_int_diff("grid_w", 9, 22)

    n_red = ctx.draw_int_diff("n_red", 1, 4)
    n_cyan = ctx.draw_int_diff("n_cyan", 1, 4)
    cyan_edge, red_edge = _draw_edges(ctx, overrides)

    red_length = _edge_length(red_edge, h, w)
    red_positions = sorted(
        ctx.draw_rng("red_positions").sample(range(1, red_length - 1), n_red)
    )

    lateral_length = _edge_length(cyan_edge, h, w)
    # Canonical examples include rays whose final tail leaves the canvas.
    # Sampling every non-corner marker position preserves that behavior; the
    # selected rule simply clips cells once a monotone staircase is outside.
    cyan_positions = sorted(
        ctx.draw_rng("cyan_positions").sample(
            range(1, lateral_length - 1), n_cyan
        )
    )

    grid = full_grid(h, w, 0)
    for position in red_positions:
        row, col = _edge_cell(red_edge, position, h, w)
        grid[row][col] = 2
    for position in cyan_positions:
        row, col = _edge_cell(cyan_edge, position, h, w)
        grid[row][col] = 8

    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "cyan_edge": cyan_edge,
        "red_edge": red_edge,
        "n_red": n_red,
        "n_cyan": n_cyan,
    }
    if observed != expected:
        raise RuntimeError(
            f"returned grid lost exact axes: expected {expected}, got {observed}"
        )
    return grid


def _shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int):
                return ["grid colors must be integers"]
    return []


def _edge_options(
    cells: list[tuple[int, int]], h: int, w: int
) -> list[str]:
    options: list[str] = []
    if cells and all(row == 0 for row, _ in cells):
        options.append("top")
    if cells and all(row == h - 1 for row, _ in cells):
        options.append("bottom")
    if cells and all(col == 0 for _, col in cells):
        options.append("left")
    if cells and all(col == w - 1 for _, col in cells):
        options.append("right")
    return options


def _analyze(grid: Any) -> tuple[dict[str, Any] | None, list[str]]:
    errors = _shape_errors(grid)
    if errors:
        return None, errors

    h, w = len(grid), len(grid[0])
    if not 9 <= h <= 20:
        errors.append(f"grid height {h} outside 9..20")
    if not 9 <= w <= 22:
        errors.append(f"grid width {w} outside 9..22")

    palette = {value for row in grid for value in row}
    if not palette <= {0, 2, 8}:
        errors.append(
            f"palette contains colors outside background 0, red 2, cyan 8: "
            f"{sorted(palette)}"
        )

    cyan = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 8
    ]
    red = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    ]

    if not 1 <= len(cyan) <= 4:
        errors.append(f"cyan marker count {len(cyan)} outside 1..4")
    if not 1 <= len(red) <= 4:
        errors.append(f"red marker count {len(red)} outside 1..4")

    corners = {(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)}
    if any(cell in corners for cell in cyan + red):
        errors.append("markers may not occupy ambiguous corners")

    cyan_options = _edge_options(cyan, h, w)
    red_options = _edge_options(red, h, w)
    if len(cyan_options) != 1:
        errors.append("cyan markers must all occupy exactly one edge")
    if len(red_options) != 1:
        errors.append("red markers must all occupy exactly one edge")

    if errors:
        return None, sorted(set(errors))

    cyan_edge = cyan_options[0]
    red_edge = red_options[0]
    if not _perpendicular(cyan_edge, red_edge):
        errors.append("cyan and red edges must be perpendicular")

    if errors:
        return None, sorted(set(errors))

    facts = {
        "grid_h": h,
        "grid_w": w,
        "cyan_edge": cyan_edge,
        "red_edge": red_edge,
        "n_red": len(red),
        "n_cyan": len(cyan),
        "cyan_cells": tuple(cyan),
        "red_cells": tuple(red),
    }
    return facts, []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return structural violations; accepts every canonical input."""
    del difficulty, meta
    _, errors = _analyze(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked strict manifold used by semantic coverage gates."""
    return self_check(grid)


def observe_overrides(grid: Any) -> dict[str, int | str]:
    """Recover every exact public axis from a lawful returned grid."""
    facts, errors = _analyze(grid)
    if errors or facts is None:
        raise ValueError(
            "cannot observe overrides from malformed grid: " + "; ".join(errors)
        )
    return {name: facts[name] for name in AXES}


def _paint_rays(
    grid: list[list[int]],
    *,
    horizontal_shift: int | None = None,
    bottom_stops: bool = False,
) -> list[list[int]]:
    facts, errors = _analyze(grid)
    if errors or facts is None:
        raise ValueError("rule expects a lawful scene: " + "; ".join(errors))

    h, w = facts["grid_h"], facts["grid_w"]
    cyan_edge = facts["cyan_edge"]
    red_edge = facts["red_edge"]
    cyan_cells = list(facts["cyan_cells"])
    red_cells = list(facts["red_cells"])
    red_rows = {row for row, _ in red_cells}
    red_cols = {col for _, col in red_cells}
    shift = _shift_for_red_edge(red_edge)
    if cyan_edge in _HORIZONTAL_EDGES and horizontal_shift is not None:
        shift = horizontal_shift

    output = [row[:] for row in grid]
    for start_row, start_col in cyan_cells:
        row, col = start_row, start_col
        if cyan_edge == "top":
            for row in range(0, h):
                if row in red_rows:
                    col += shift
                if 0 <= col < w:
                    output[row][col] = 8
        elif cyan_edge == "bottom":
            rows = (h - 1,) if bottom_stops else range(h - 1, -1, -1)
            for row in rows:
                if row in red_rows:
                    col += shift
                if 0 <= col < w:
                    output[row][col] = 8
        elif cyan_edge == "left":
            for col in range(0, w):
                if col in red_cols:
                    row += shift
                if 0 <= row < h:
                    output[row][col] = 8
        elif cyan_edge == "right":
            for col in range(w - 1, -1, -1):
                if col in red_cols:
                    row += shift
                if 0 <= row < h:
                    output[row][col] = 8
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for evidence; canonical Racket is authority."""
    return _paint_rays(grid)


def semantic_profile(grid: Any) -> dict[str, Any]:
    facts, errors = _analyze(grid)
    if errors or facts is None:
        return {"valid": False, "errors": errors}
    intended = rule_mirror(grid)
    return {
        "valid": True,
        **{name: facts[name] for name in AXES},
        "changed_cells": sum(
            intended[row][col] != grid[row][col]
            for row in range(facts["grid_h"])
            for col in range(facts["grid_w"])
        ),
    }


def _horizontal_always_shifts_up(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule: horizontal rays always step toward decreasing rows."""
    return _paint_rays(grid, horizontal_shift=-1)


def _vertical_emitters_always_travel_down(
    grid: list[list[int]],
) -> list[list[int]]:
    """Wrong rule: a bottom marker cannot emit an upward-moving ray."""
    facts, errors = _analyze(grid)
    if errors or facts is None:
        raise ValueError("shortcut expects a lawful scene: " + "; ".join(errors))
    return _paint_rays(grid, bottom_stops=facts["cyan_edge"] == "bottom")


def _horizontal_top_deflectors_shift_down(grid: list[list[int]]) -> bool:
    facts, errors = _analyze(grid)
    return bool(
        not errors
        and facts is not None
        and facts["cyan_edge"] in _HORIZONTAL_EDGES
        and facts["red_edge"] == "top"
        and _horizontal_always_shifts_up(grid) != rule_mirror(grid)
    )


def _bottom_emitters_travel_upward(grid: list[list[int]]) -> bool:
    facts, errors = _analyze(grid)
    return bool(
        not errors
        and facts is not None
        and facts["cyan_edge"] == "bottom"
        and _vertical_emitters_always_travel_down(grid) != rule_mirror(grid)
    )


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "horizontal_top_deflectors_shift_down": _horizontal_top_deflectors_shift_down,
    "bottom_emitters_travel_upward": _bottom_emitters_travel_upward,
}

SEMANTIC_RIVALS: dict[
    str, Callable[[list[list[int]]], list[list[int]]]
] = {
    "horizontal_always_shifts_up": _horizontal_always_shifts_up,
    "vertical_emitters_always_travel_down": _vertical_emitters_always_travel_down,
}

WITNESS_RIVALS = {
    "horizontal_top_deflectors_shift_down": ["horizontal_always_shifts_up"],
    "bottom_emitters_travel_upward": ["vertical_emitters_always_travel_down"],
}

# Both rivals agree with every canonical pair, so generated counterexamples—not
# the published demonstrations—must disambiguate them from the intended rule.
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
