"""Generator for arc_additional_puzzle_bank_volume2:H12.

Rule: identify the yellow (4) outer rectangular frame and the blue (1)
inner rectangular frame. Paint cyan (8) in the annulus strictly inside the
outer frame and outside the inner frame's bounding box. Preserve both frames
and the empty interior of the inner frame.

The lawful lesson distribution contains exactly those two uniformly nested,
one-cell rectangular frames on a black background. The three declared axes are
exact and observable: grid height, grid width, and uniform annular thickness.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "8c7daa3d3cef"
RULE_HASH = "af62226587e1"
VERSION = "4.0.0"  # honest exact axes + mutation-sensitive nested-frame grammar
TASK_ID = "8c7daa3d3cef"
SUMMARY = (
    "A black grid contains exactly two one-cell rectangular frames: a yellow "
    "(4) outer frame and a blue (1) inner frame separated uniformly by one or "
    "two blank cells. Fill the annulus inside the outer frame but outside the "
    "inner frame's bounding box with cyan (8), preserving both frames and the "
    "empty interior of the inner frame."
)

INVARIANTS = [
    "the only non-background cells are one complete yellow outer frame and one complete blue inner frame",
    "the blue frame is strictly and uniformly nested inside the yellow frame with annular thickness 1 or 2",
    "the inner frame is at least 3x3, so its non-empty interior remains background 0",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-banded keyed draw",
        "valid": "7..16",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-banded keyed draw",
        "valid": "7..16",
    },
    "annular_thickness": {
        "type": "int",
        "default": "keyed draw; 1 on 7/8-cell constrained canvases, otherwise 1..2",
        "valid": "1..2",
    },
}

_ALLOWED_OVERRIDES = frozenset(AXES)
_BANDS = {
    None: (7, 16),
    "easy": (7, 10),
    "medium": (9, 13),
    "hard": (12, 16),
}


def _frame_cells(bbox: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    """Return the complete one-cell perimeter for an inclusive bbox."""
    r0, c0, r1, c1 = bbox
    cells = {(r0, c) for c in range(c0, c1 + 1)}
    cells.update((r1, c) for c in range(c0, c1 + 1))
    cells.update((r, c0) for r in range(r0, r1 + 1))
    cells.update((r, c1) for r in range(r0, r1 + 1))
    return cells


def _bbox(cells: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [row for row, _col in cells]
    cols = [col for _row, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _analysis(grid) -> dict:
    """Parse a lawful input and return structural errors plus exact facts.

    This deliberately recognizes the teaching distribution, not every grid on
    which the broad Racket program might happen to execute. In particular it
    rejects missing, broken, touching, duplicated, non-uniform, or solid frames.
    """
    facts: dict[str, object] = {}
    if not isinstance(grid, list) or not grid:
        return {"errors": ["empty or non-list grid"], "facts": facts}
    if not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["empty or non-list first row"], "facts": facts}

    height = len(grid)
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["ragged or non-list row"], "facts": facts}

    values = [value for row in grid for value in row]
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for value in values
    ):
        return {"errors": ["grid contains a non-ARC color value"], "facts": facts}

    errors: list[str] = []
    if not (7 <= height <= 16 and 7 <= width <= 16):
        errors.append(
            f"dimensions {height}x{width} outside declared 7..16 envelope"
        )

    palette = set(values)
    if not palette <= {0, 1, 4}:
        errors.append(
            "input palette must be a subset of {0,1,4}; found "
            + repr(sorted(palette))
        )

    outer_cells = {
        (row, col)
        for row, values_row in enumerate(grid)
        for col, value in enumerate(values_row)
        if value == 4
    }
    inner_cells = {
        (row, col)
        for row, values_row in enumerate(grid)
        for col, value in enumerate(values_row)
        if value == 1
    }
    if not outer_cells:
        errors.append("missing yellow outer frame")
    if not inner_cells:
        errors.append("missing blue inner frame")
    if not outer_cells or not inner_cells:
        return {"errors": errors, "facts": facts}

    outer_bbox = _bbox(outer_cells)
    inner_bbox = _bbox(inner_cells)
    expected_outer = _frame_cells(outer_bbox)
    expected_inner = _frame_cells(inner_bbox)
    if outer_cells != expected_outer:
        errors.append(
            "yellow cells are not exactly one complete one-cell rectangular frame"
        )
    if inner_cells != expected_inner:
        errors.append(
            "blue cells are not exactly one complete one-cell rectangular frame"
        )

    or0, oc0, or1, oc1 = outer_bbox
    ir0, ic0, ir1, ic1 = inner_bbox
    outer_height = or1 - or0 + 1
    outer_width = oc1 - oc0 + 1
    inner_height = ir1 - ir0 + 1
    inner_width = ic1 - ic0 + 1
    if outer_height < 7 or outer_width < 7:
        errors.append("outer frame is too small to contain the lawful lesson")
    if inner_height < 3 or inner_width < 3:
        errors.append("inner frame must be at least 3x3 with a non-empty interior")

    gaps = (
        ir0 - or0 - 1,
        or1 - ir1 - 1,
        ic0 - oc0 - 1,
        oc1 - ic1 - 1,
    )
    if min(gaps) < 1:
        errors.append("inner frame is not strictly separated from the outer frame")
    if len(set(gaps)) != 1:
        errors.append(f"frame separation is not uniform on all four sides: {gaps}")
    thickness = gaps[0]
    if thickness not in (1, 2):
        errors.append(f"annular thickness {thickness} is outside declared 1..2")

    if inner_height >= 3 and inner_width >= 3:
        dirty_interior = [
            (row, col)
            for row in range(ir0 + 1, ir1)
            for col in range(ic0 + 1, ic1)
            if grid[row][col] != 0
        ]
        if dirty_interior:
            errors.append("inner frame interior must remain background 0")

    facts.update(
        {
            "grid_h": height,
            "grid_w": width,
            "outer_bbox": outer_bbox,
            "inner_bbox": inner_bbox,
            "annular_thickness": thickness,
            "outer_area": outer_height * outer_width,
            "inner_area": inner_height * inner_width,
        }
    )
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject every grid outside the exact nested-frame lesson grammar."""
    return list(_analysis(grid)["errors"])


def observe_overrides(grid) -> dict[str, int]:
    """Return the exact realized values of all declared semantic axes."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    facts = analysis["facts"]
    return {
        "grid_h": int(facts["grid_h"]),
        "grid_w": int(facts["grid_w"]),
        "annular_thickness": int(facts["annular_thickness"]),
    }


def _validated_explicit_dimension(overrides: dict, name: str) -> int | None:
    value = overrides.get(name)
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} override must be an integer") from exc
    if not 7 <= parsed <= 16:
        raise ValueError(f"{name} override {parsed} outside [7, 16]")
    return parsed


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _BANDS:
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(
        name for name, value in overrides.items()
        if value is not None and name not in _ALLOWED_OVERRIDES
    )
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")

    # Inspect explicit dimensions only to narrow the *default* thickness draw.
    # Every accepted exact value is still consumed through GenCtx below.
    explicit_h = _validated_explicit_dimension(overrides, "grid_h")
    explicit_w = _validated_explicit_dimension(overrides, "grid_w")
    explicit_thickness = overrides.get("annular_thickness")
    constrained_small_canvas = (
        explicit_thickness is None
        and any(value is not None and value < 9 for value in (explicit_h, explicit_w))
    )

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    thickness_hi = 1 if constrained_small_canvas else 2
    if difficulty == "easy" and explicit_thickness is None:
        thickness_hi = 1
    thickness = ctx.draw_int("annular_thickness", 1, thickness_hi)
    minimum_side = 5 + 2 * thickness

    band_lo, band_hi = _BANDS[difficulty]
    if explicit_h is None:
        height = ctx.draw_int("grid_h", max(band_lo, minimum_side), band_hi)
    else:
        height = ctx.draw_int("grid_h", 7, 16)
    if explicit_w is None:
        width = ctx.draw_int("grid_w", max(band_lo, minimum_side), band_hi)
    else:
        width = ctx.draw_int("grid_w", 7, 16)

    if height < minimum_side or width < minimum_side:
        raise ValueError(
            f"grid {height}x{width} cannot contain a >=3x3 inner frame "
            f"with annular_thickness={thickness}; each side must be at least "
            f"{minimum_side}"
        )

    outer_height = ctx.draw_int("outer_h", minimum_side, height)
    outer_width = ctx.draw_int("outer_w", minimum_side, width)
    outer_row = ctx.draw_int("outer_row", 0, height - outer_height)
    outer_col = ctx.draw_int("outer_col", 0, width - outer_width)
    outer_bottom = outer_row + outer_height - 1
    outer_right = outer_col + outer_width - 1

    inner_row = outer_row + 1 + thickness
    inner_col = outer_col + 1 + thickness
    inner_bottom = outer_bottom - 1 - thickness
    inner_right = outer_right - 1 - thickness

    grid = full_grid(height, width, 0)
    draw_frame(
        grid,
        outer_row,
        outer_col,
        outer_bottom,
        outer_right,
        4,
    )
    draw_frame(
        grid,
        inner_row,
        inner_col,
        inner_bottom,
        inner_right,
        1,
    )

    errors = self_check(grid, difficulty=difficulty)
    if errors:  # Construction bugs fail closed instead of returning a fallback.
        raise RuntimeError("constructed invalid nested-frame lesson: " + "; ".join(errors))
    return grid
