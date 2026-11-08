"""Generator for ARC task dfc7297269cc: horizontal sandwich fill.

The selected rule examines the *original* grid.  Every zero whose immediate
horizontal neighbours are the same nonzero color is replaced by that color;
all other cells remain unchanged.  Generated scenes always contain positive
examples plus three canonical-fitting negative witnesses:

* a same-color pair separated by two zeros (refutes filling a whole span),
* a one-zero gap with different endpoint colors (refutes ignoring equality),
* a vertical same-color sandwich (refutes applying the rule vertically).

The four advertised controls are exact and recoverable from returned pixels.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dfc7297269cc"
TASK_ID = GENERATOR_ID
RULE_HASH = "80ec61287499"
VERSION = "2.0.0"
SUMMARY = (
    "Fill a zero exactly between equal nonzero horizontal neighbours; "
    "generated scenes include wide-gap, mismatched, and vertical negatives."
)

INVARIANTS = [
    "background is 0 and every cell is an integer ARC color 0..9",
    "there are 1..4 active horizontal equal-color sandwiches",
    "the selected rule changes exactly the advertised number of motif centers",
    "every generated input refutes span-fill, unequal-endpoint, and vertical shortcuts",
    "all advertised controls are observable from returned pixels",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile weighted over 5..14",
        "valid": "5..14",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile weighted over 7..16",
        "valid": "7..16",
    },
    "motifs": {
        "type": "int",
        "default": "canonical-profile weighted over 1..4",
        "valid": "1..4",
    },
    "n_colors": {
        "type": "int",
        "default": "canonical-profile weighted over 2..4 nonzero colors",
        "valid": "2..4",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 3

# (height, width, number of nonzero colors, active motif count).  These mirror
# the three public profiles without copying their layouts.
_CANONICAL_PROFILES = (
    (5, 7, 2, 2),
    (5, 8, 3, 3),
    (6, 9, 3, 4),
)


def _profile_options(difficulty) -> tuple[tuple[int, int, int, int], ...]:
    """Difficulty changes emphasis, never the legal support of an axis."""
    if difficulty == "easy":
        weights = (10, 7, 3)
    elif difficulty == "hard":
        weights = (3, 7, 10)
    else:
        weights = (6, 6, 6)
    return tuple(
        profile
        for profile, weight in zip(_CANONICAL_PROFILES, weights)
        for _ in range(weight)
    )


def _weighted_axis(ctx, name: str, lo: int, hi: int, anchor: int) -> int:
    """Expose the full exact domain while strongly retaining canonical scale."""
    options = tuple(range(lo, hi + 1)) + (anchor,) * 12
    return ctx.draw_choice(name, options)


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    bounds = {
        "grid_h": (5, 14),
        "grid_w": (7, 16),
        "motifs": (1, 4),
        "n_colors": (2, 4),
    }
    for name, (lo, hi) in bounds.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(
                f"{name} must be an integer, not {type(value).__name__}"
            )
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo},{hi}]")


def _active_motifs(grid) -> list[tuple[int, int, int]]:
    hits: list[tuple[int, int, int]] = []
    for row_index, row in enumerate(grid):
        for col in range(1, len(row) - 1):
            color = row[col - 1]
            if color != 0 and row[col] == 0 and row[col + 1] == color:
                hits.append((row_index, col, color))
    return hits


def _draw_active(template, motifs: int, palette: tuple[int, ...], rng) -> None:
    """Draw exactly ``motifs`` positives in the top two rows of a 5x7 tile."""
    first = palette[0]
    second = palette[1]
    if motifs == 1:
        template[0][0] = first
        template[0][2] = first
    elif motifs == 2 and rng.choice((False, True)):
        # Two adjacent motifs sharing an endpoint.
        for col in (0, 2, 4):
            template[0][col] = first
    elif motifs == 2:
        # Two isolated motifs; the different middle endpoint colors prevent an
        # accidental third motif at column 3.
        template[0][0] = first
        template[0][2] = first
        template[0][4] = second
        template[0][6] = second
    elif motifs == 3:
        for col in (0, 2, 4, 6):
            template[0][col] = first
    elif motifs == 4 and rng.choice((False, True)):
        for col in (0, 2, 4, 6):
            template[0][col] = first
        template[1][0] = second
        template[1][2] = second
    elif motifs == 4:
        for col in (0, 2, 4):
            template[0][col] = first
        for col in (2, 4, 6):
            template[1][col] = second
    else:  # pragma: no cover - guarded by override/domain validation
        raise ValueError(f"unsupported motif count {motifs}")


def _microtemplate(motifs: int, palette: tuple[int, ...], rng):
    """Return a 5x7 scene with positives and all three rival witnesses."""
    tile = full_grid(5, 7, 0)
    _draw_active(tile, motifs, palette, rng)

    # Wide same-color gap: the selected rule leaves both zeros unchanged.
    tile[2][0] = palette[0]
    tile[2][3] = palette[0]

    # Mismatched one-zero gap: equality of endpoints is essential.
    tile[3][1] = palette[0]
    tile[3][3] = palette[1]

    # Colors 0 and 1 already occur in the positives/mismatch, and color 2
    # (when present) is the vertical witness.  Only a fourth color needs an
    # extra singleton; avoiding redundant palette markers keeps component
    # counts at canonical scale.
    if len(palette) == 4:
        tile[4][0] = palette[3]

    # Vertical same-color sandwich: orientation is essential.  Choosing a
    # third color when available also avoids accidental horizontal equality.
    vertical_color = palette[2] if len(palette) >= 3 else palette[1]
    tile[2][6] = vertical_color
    tile[4][6] = vertical_color

    actual = len(_active_motifs(tile))
    if actual != motifs:  # construction assertion, never a resampling filter
        raise AssertionError(f"microtemplate has {actual} motifs, expected {motifs}")
    return tile


def _transform_and_embed(tile, height: int, width: int, rng):
    if rng.choice((False, True)):
        tile = [row[::-1] for row in tile]
    if rng.choice((False, True)):
        tile = tile[::-1]
    top = rng.randrange(height - len(tile) + 1)
    left = rng.randrange(width - len(tile[0]) + 1)
    grid = full_grid(height, width, 0)
    for row, values in enumerate(tile):
        for col, value in enumerate(values):
            grid[top + row][left + col] = value
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    anchor_h, anchor_w, anchor_colors, anchor_motifs = ctx.draw_choice(
        "curriculum_profile", _profile_options(difficulty)
    )
    height = _weighted_axis(ctx, "grid_h", 5, 14, anchor_h)
    width = _weighted_axis(ctx, "grid_w", 7, 16, anchor_w)
    motifs = _weighted_axis(ctx, "motifs", 1, 4, anchor_motifs)
    n_colors = _weighted_axis(ctx, "n_colors", 2, 4, anchor_colors)

    palette = tuple(
        ctx.draw_rng("palette").sample(list(range(1, 10)), n_colors)
    )
    tile = _microtemplate(motifs, palette, ctx.draw_rng("active_layout"))
    return _transform_and_embed(tile, height, width, ctx.draw_rng("placement"))


def _shape(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None
    first = grid[0]
    if not isinstance(first, (list, tuple)) or not first:
        return None
    width = len(first)
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width for row in grid
    ):
        return None
    return len(grid), width


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the positive task-linked manifold used for training lessons."""
    del difficulty, meta
    shape = _shape(grid)
    if shape is None:
        return ["expected a nonempty rectangular grid"]
    height, width = shape
    errors: list[str] = []
    if not 5 <= height <= 14:
        errors.append(f"grid_h={height} outside [5,14]")
    if not 7 <= width <= 16:
        errors.append(f"grid_w={width} outside [7,16]")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
        return errors
    colors = {value for row in grid for value in row if value != 0}
    if len(colors) < 2:
        errors.append("expected at least two distinct nonzero colors")
    if not _active_motifs(grid):
        errors.append("expected at least one horizontal equal-color sandwich")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The selected rule is local, so its lawful domain is shape/palette based."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact advertised control from returned pixels."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "motifs": len(_active_motifs(grid)),
        "n_colors": len({value for row in grid for value in row if value != 0}),
    }


def _solve_intended(grid):
    out = deepcopy(grid)
    height, width = len(grid), len(grid[0])
    for row in range(height):
        for col in range(1, width - 1):
            color = grid[row][col - 1]
            if color != 0 and grid[row][col] == 0 and grid[row][col + 1] == color:
                out[row][col] = color
    return out


def _span_fill(grid):
    """RIVAL: fill the full horizontal span of every repeated color."""
    out = deepcopy(grid)
    for row_index, row in enumerate(grid):
        for color in sorted({value for value in row if value != 0}):
            positions = [col for col, value in enumerate(row) if value == color]
            if len(positions) < 2:
                continue
            for col in range(positions[0], positions[-1] + 1):
                if grid[row_index][col] == 0:
                    out[row_index][col] = color
    return out


def _any_nonzero_endpoints(grid):
    """RIVAL: ignore the requirement that the two endpoint colors match."""
    out = deepcopy(grid)
    height, width = len(grid), len(grid[0])
    for row in range(height):
        for col in range(1, width - 1):
            if grid[row][col] == 0 and grid[row][col - 1] != 0 and grid[row][col + 1] != 0:
                out[row][col] = grid[row][col - 1]
    return out


def _horizontal_or_vertical(grid):
    """RIVAL: apply the same local predicate in both orientations."""
    out = _solve_intended(grid)
    height, width = len(grid), len(grid[0])
    for row in range(1, height - 1):
        for col in range(width):
            color = grid[row - 1][col]
            if color != 0 and grid[row][col] == 0 and grid[row + 1][col] == color:
                out[row][col] = color
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "span_fill": _span_fill,
    "any_nonzero_endpoints": _any_nonzero_endpoints,
    "horizontal_or_vertical": _horizontal_or_vertical,
}
SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    name: (lambda grid, rival=rival: rival(grid) != _solve_intended(grid))
    for name, rival in SEMANTIC_RIVALS.items()
}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Report canonical-fitting competitors not refuted by the demonstrations."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                rival(deepcopy(pair["input"])) == pair["output"] for pair in demos
            )
            changes_query = rival(deepcopy(query["input"])) != query["output"]
        except Exception as exc:  # contract reports, rather than hides, bad rivals
            reasons.append(f"{name} raised {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
