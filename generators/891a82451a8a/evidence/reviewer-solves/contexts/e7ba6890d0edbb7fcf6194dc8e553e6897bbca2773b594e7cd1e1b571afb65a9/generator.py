"""Generator for ARC task 891a82451a8a.

A lawful input is a rectangular grid with a unique modal background and exactly
one non-background seed.  The seed color must belong to the authoritative fixed
cycle ``(0, 5, 2, 8, 9, 6, 1, 3, 4)``.  The background is nonzero because the
selected Racket ``mode`` primitive ignores zero cells.
The output colors every cell by Manhattan distance from the seed, advancing
through that cycle from the seed's color.

The sampler exposes only controls that are visible in returned pixels.  It keeps
an exact 8x8/two-color branch in every difficulty band while varying scale,
nonzero background, cycle phase, and four disjoint seed-position regions.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "891a82451a8a"
TASK_ID = "891a82451a8a"
VERSION = "3.0.0"
RULE_HASH = "635140e0e1b3"

SUMMARY = (
    "Fill a 5..18 by 5..18 grid with one background color and place exactly "
    "one seed of a color from the fixed cycle 0,5,2,8,9,6,1,3,4. The "
    "background may be any nonzero ARC color (the selected Racket mode ignores "
    "zero). Color every output cell by Manhattan "
    "distance from the seed, advancing through the fixed cycle from the "
    "seed's color. Defaults cover corner, edge, center, and interior seeds "
    "and include an 8x8 canonical-profile branch in every difficulty band."
)

EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

CYCLE = (0, 5, 2, 8, 9, 6, 1, 3, 4)
ALL_COLORS = tuple(range(10))
BACKGROUND_COLORS = tuple(range(1, 10))
DIMENSIONS = tuple(range(5, 19))
SEED_REGIONS = ("corner", "edge", "center", "interior")

INVARIANTS = [
    "grid dimensions are between 5 and 18 inclusive",
    "the background is the unique strict mode",
    "there is exactly one non-background seed",
    "the seed color is in the fixed cycle 0,5,2,8,9,6,1,3,4",
    "the background is a nonzero ARC color and differs from the seed",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "keyed 5..18 mixture with periodic canonical 8",
        "valid": "5..18",
    },
    "grid_w": {
        "type": "int",
        "default": "keyed 5..18 mixture with periodic canonical 8",
        "valid": "5..18",
    },
    "bg_color": {
        "type": "color",
        "default": "scheduled across nonzero ARC colors",
        "valid": "1..9",
    },
    "seed_color": {
        "type": "color",
        "default": "scheduled fixed-cycle color distinct from background",
        "valid": "0,1,2,3,4,5,6,8,9",
    },
    "seed_region": {
        "type": "str",
        "default": "scheduled disjoint visible region",
        "valid": "corner|edge|center|interior",
    },
}

# Opt into strict override-rejection classification.  The one conditional
# incompatibility (equal explicit background/seed colors) is carried on the
# raised exception because it depends on values, not merely on axis names.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()


class IncompatibleOverrides(ValueError):
    """A loud, machine-readable refusal of a jointly impossible request."""

    def __init__(self, message: str, axes: tuple[str, ...]):
        super().__init__(message)
        self.incompatible_axes = axes


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    for name in ("grid_h", "grid_w", "bg_color", "seed_color"):
        if name in overrides and overrides[name] is not None:
            if type(overrides[name]) is not int:
                raise TypeError(f"{name} override must be an integer (not bool)")

    for name in ("grid_h", "grid_w"):
        if name in overrides and overrides[name] is not None:
            value = overrides[name]
            if value not in DIMENSIONS:
                raise ValueError(f"{name}={value} outside 5..18")

    if "bg_color" in overrides and overrides["bg_color"] is not None:
        value = overrides["bg_color"]
        if value not in BACKGROUND_COLORS:
            raise ValueError(f"bg_color={value} outside nonzero ARC colors 1..9")

    if "seed_color" in overrides and overrides["seed_color"] is not None:
        value = overrides["seed_color"]
        if value not in CYCLE:
            raise ValueError(
                f"seed_color={value} is not in the fixed cycle {CYCLE}"
            )

    if "seed_region" in overrides and overrides["seed_region"] is not None:
        value = overrides["seed_region"]
        if type(value) is not str or value not in SEED_REGIONS:
            raise ValueError(
                f"seed_region={value!r} must be one of {SEED_REGIONS}"
            )

    bg = overrides.get("bg_color")
    seed = overrides.get("seed_color")
    if bg is not None and seed is not None and bg == seed:
        raise IncompatibleOverrides(
            "bg_color and seed_color must differ",
            ("bg_color", "seed_color"),
        )


def _dimension_options(difficulty: str | None) -> tuple[int, ...]:
    """Full legal support with band-specific default weighting."""
    if difficulty == "easy":
        weighted = tuple(range(5, 10)) * 3
    elif difficulty == "medium":
        weighted = tuple(range(7, 15)) * 3
    elif difficulty == "hard":
        weighted = tuple(range(11, 19)) * 3
    else:
        weighted = DIMENSIONS
    return DIMENSIONS + weighted


def _draw_dimension(
    ctx, label: str, seed: int, sample_index: int, difficulty: str | None
) -> int:
    # Explicit controls retain the complete documented domain in every band.
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, DIMENSIONS)
    # A deterministic, auditable one-third branch keeps every pinned band
    # above the 25% canonical-envelope floor without collapsing the scale range.
    if (sample_index + seed) % 3 == 0:
        return ctx.draw_choice(label, (8,))
    return ctx.draw_choice(label, _dimension_options(difficulty))


def _draw_background(ctx, seed: int, sample_index: int) -> int:
    if ctx.overrides.get("bg_color") is not None:
        return ctx.draw_choice("bg_color", BACKGROUND_COLORS)

    explicit_seed = ctx.overrides.get("seed_color")
    legal = tuple(color for color in BACKGROUND_COLORS if color != explicit_seed)
    scheduled = legal[(sample_index + seed // 9) % len(legal)]
    return ctx.draw_choice("bg_color", (scheduled,))


def _draw_seed_color(
    ctx, seed: int, sample_index: int, background: int
) -> int:
    if ctx.overrides.get("seed_color") is not None:
        value = ctx.draw_choice("seed_color", CYCLE)
        if value == background:
            raise IncompatibleOverrides(
                "bg_color and seed_color must differ",
                ("bg_color", "seed_color"),
            )
        return value

    schedule_index = (sample_index + seed) % len(CYCLE)
    candidate = CYCLE[schedule_index]
    if candidate == background:
        # Never introduce an extra phase-0 sample while resolving a collision;
        # this keeps every two-demo cyclic lesson capable of refuting a
        # fixed-zero-phase shortcut.
        candidate = next(
            color
            for offset in range(1, len(CYCLE) + 1)
            if (color := CYCLE[(schedule_index + offset) % len(CYCLE)])
            != background
            and color != 0
        )
    return ctx.draw_choice("seed_color", (candidate,))


def _draw_seed_region(ctx, seed: int, sample_index: int) -> str:
    if ctx.overrides.get("seed_region") is not None:
        return ctx.draw_choice("seed_region", SEED_REGIONS)
    return ctx.draw_choice(
        "seed_region",
        (SEED_REGIONS[(sample_index + seed // 4) % len(SEED_REGIONS)],),
    )


def _region_cells(height: int, width: int, region: str) -> tuple[tuple[int, int], ...]:
    corners = {
        (0, 0),
        (0, width - 1),
        (height - 1, 0),
        (height - 1, width - 1),
    }
    center_rows = {(height - 1) // 2, height // 2}
    center_cols = {(width - 1) // 2, width // 2}
    center = {(row, col) for row in center_rows for col in center_cols}
    edge = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
    } - corners
    interior = {
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
    } - center
    cells = {
        "corner": corners,
        "edge": edge,
        "center": center,
        "interior": interior,
    }[region]
    if not cells:
        raise RuntimeError(
            f"internal region {region!r} has no cells for {height}x{width}"
        )
    return tuple(sorted(cells))


def _classify_region(height: int, width: int, row: int, col: int) -> str:
    corners = {
        (0, 0),
        (0, width - 1),
        (height - 1, 0),
        (height - 1, width - 1),
    }
    if (row, col) in corners:
        return "corner"
    if row in (0, height - 1) or col in (0, width - 1):
        return "edge"
    center_rows = {(height - 1) // 2, height // 2}
    center_cols = {(width - 1) // 2, width // 2}
    if row in center_rows and col in center_cols:
        return "center"
    return "interior"


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return ["rows must be non-empty lists"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}

    height, width = len(grid), len(grid[0])
    if not (5 <= height <= 18 and 5 <= width <= 18):
        errors.append(
            f"dimensions {height}x{width} must each be between 5 and 18"
        )

    counts = Counter(value for row in grid for value in row)
    ranked = counts.most_common()
    if len(ranked) < 2:
        background = ranked[0][0]
        errors.append("expected a singleton non-background seed; found none")
    else:
        background = ranked[0][0]
        if ranked[0][1] == ranked[1][1]:
            errors.append("background must be the unique strict mode")
    if background == 0:
        errors.append(
            "background 0 is outside the selected Racket rule domain "
            "because its mode primitive ignores zero"
        )

    seed_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != background
    ]
    seed_row = seed_col = seed_color = None
    if len(seed_cells) != 1:
        errors.append(
            f"expected exactly one non-background seed; found {len(seed_cells)}"
        )
    else:
        seed_row, seed_col = seed_cells[0]
        seed_color = grid[seed_row][seed_col]
        if seed_color not in CYCLE:
            errors.append(
                f"seed color {seed_color} is not in the fixed cycle {CYCLE}"
            )
        if seed_color == background:
            errors.append("seed color equals background")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "background": background,
        "seed_row": seed_row,
        "seed_col": seed_col,
        "seed_color": seed_color,
        "seed_region": (
            _classify_region(height, width, seed_row, seed_col)
            if seed_row is not None and seed_col is not None
            else None
        ),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return diagnostics for grids outside the generator's lawful manifold."""
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """All generated and canonical inputs belong to the same strict manifold."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact advertised axis from returned pixels."""
    info = _analyze(grid)
    if info["errors"]:
        return {}
    return {
        "grid_h": info["height"],
        "grid_w": info["width"],
        "bg_color": info["background"],
        "seed_color": info["seed_color"],
        "seed_region": info["seed_region"],
    }


def _require_lawful(grid) -> dict[str, Any]:
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("invalid task input: " + "; ".join(info["errors"]))
    return info


def _distance_output(
    grid,
    *,
    metric: str = "manhattan",
    fixed_phase: int | None = None,
    fixed_anchor: tuple[int, int] | None = None,
) -> list[list[int]]:
    info = _require_lawful(grid)
    anchor = fixed_anchor or (info["seed_row"], info["seed_col"])
    start = CYCLE.index(info["seed_color"]) if fixed_phase is None else fixed_phase
    output: list[list[int]] = []
    for row in range(info["height"]):
        result_row: list[int] = []
        for col in range(info["width"]):
            dr, dc = abs(row - anchor[0]), abs(col - anchor[1])
            if metric == "manhattan":
                distance = dr + dc
            elif metric == "chebyshev":
                distance = max(dr, dc)
            else:
                raise ValueError(f"unknown metric: {metric}")
            result_row.append(CYCLE[(start + distance) % len(CYCLE)])
        output.append(result_row)
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python diagnostic mirror of the authoritative Racket rule."""
    return _distance_output(grid)


def _chebyshev_distance(grid) -> list[list[int]]:
    return _distance_output(grid, metric="chebyshev")


def _fixed_zero_phase(grid) -> list[list[int]]:
    return _distance_output(grid, fixed_phase=0)


def _fixed_grid_center(grid) -> list[list[int]]:
    info = _require_lawful(grid)
    return _distance_output(
        grid,
        fixed_anchor=(info["height"] // 2, info["width"] // 2),
    )


def _canonical_profile_only(grid) -> list[list[int]]:
    """Shortcut that memorizes the original 8x8/background-7 envelope."""
    info = _require_lawful(grid)
    if (
        info["height"] == 8
        and info["width"] == 8
        and info["background"] == 7
    ):
        return rule_mirror(grid)
    return [list(row) for row in grid]


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "chebyshev_distance": _chebyshev_distance,
    "fixed_zero_phase": _fixed_zero_phase,
    "fixed_grid_center": _fixed_grid_center,
    "canonical_profile_only": _canonical_profile_only,
}


def _rival_differs(name: str, grid) -> bool:
    try:
        return SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)
    except (TypeError, ValueError):
        return False


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "diagonal_separates_metrics": lambda grid: _rival_differs(
        "chebyshev_distance", grid
    ),
    "seed_color_controls_phase": lambda grid: _rival_differs(
        "fixed_zero_phase", grid
    ),
    "actual_seed_controls_center": lambda grid: _rival_differs(
        "fixed_grid_center", grid
    ),
    "off_canonical_profile": lambda grid: _rival_differs(
        "canonical_profile_only", grid
    ),
}

WITNESS_RIVALS = {
    "diagonal_separates_metrics": ["chebyshev_distance"],
    "seed_color_controls_phase": ["fixed_zero_phase"],
    "actual_seed_controls_center": ["fixed_grid_center"],
    "off_canonical_profile": ["canonical_profile_only"],
}

CANONICAL_SHORTCUTS = {
    "canonical_profile_only": _canonical_profile_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Check labelled demonstrations against declared plausible competitors."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        try:
            intended = rule_mirror(pair["input"])
        except (TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is invalid: {exc}")
            continue
        if pair["output"] != intended:
            reasons.append(f"demo {index} output disagrees with authoritative rule")

    if reasons:
        return reasons

    try:
        query_answer = rule_mirror(query["input"])
    except (TypeError, ValueError) as exc:
        return [f"query is invalid: {exc}"]
    if "output" in query and query["output"] != query_answer:
        reasons.append("query output disagrees with authoritative rule")

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                competitor(pair["input"]) == pair["output"] for pair in demos
            )
            differs_query = competitor(query["input"]) != query_answer
        except Exception as exc:  # diagnostics must surface a broken declaration
            reasons.append(f"competitor {name} failed: {type(exc).__name__}: {exc}")
            continue
        if fits_demos and differs_query:
            reasons.append(
                f"competitor {name} fits every demonstration but differs on query"
            )
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    if type(seed) is not int or isinstance(seed, bool):
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or isinstance(sample_index, bool):
        raise TypeError("sample_index must be an integer (not bool)")
    _validate_overrides(overrides)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_dimension(ctx, "grid_h", seed, sample_index, difficulty)
    width = _draw_dimension(ctx, "grid_w", seed, sample_index, difficulty)
    background = _draw_background(ctx, seed, sample_index)
    seed_color = _draw_seed_color(ctx, seed, sample_index, background)
    region = _draw_seed_region(ctx, seed, sample_index)

    positions = _region_cells(height, width, region)
    position_rng = ctx.draw_rng("seed_position")
    seed_row, seed_col = position_rng.choice(positions)

    grid = full_grid(height, width, background)
    grid[seed_row][seed_col] = seed_color
    return grid
