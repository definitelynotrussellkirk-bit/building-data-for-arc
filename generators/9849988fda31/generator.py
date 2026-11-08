"""Generator for ARC task e9afcf9a / content hash 9849988fda31.

The canonical inputs are two uniform horizontal rows.  Their two colors are
role labels, not fixed ARC colors.  The Racket rule reads the labels from the
first column and emits a checkerboard whose phase is ``(row + column) mod 2``.

The teaching grammar deliberately keeps the rows uniform.  On that lawful
grammar, "read the whole row color" and "read column 0" are answer-equivalent;
malformed decoy textures are rejected instead of being mixed into training.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "9849988fda31"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "961ad1f06f1a"

SUMMARY = (
    "Read the two distinct nonzero role colors from the two uniform input "
    "rows (equivalently from column 0), then fill the same 2xW canvas with "
    "those colors in checkerboard phase: output[r][c] uses role "
    "(r + c) mod 2."
)

INVARIANTS = [
    "input has exactly two rows and width 5..30",
    "each row is uniform and therefore agrees with its column-0 role color",
    "the two role colors are distinct nonzero ARC colors",
    "the output is non-identity and visibly alternates for every lawful width",
]

AXES = {
    "grid_w": {
        "type": "int",
        "default": "difficulty-biased draw with a canonical-width prior",
        "valid": "5..30",
    },
    "stripe_color_a": {
        "type": "color",
        "default": "rng nonzero ARC color",
        "valid": "1..9",
    },
    "stripe_color_b": {
        "type": "color",
        "default": "rng nonzero ARC color distinct from stripe_color_a",
        "valid": "1..9",
    },
}

# The Cartesian override checker legitimately reaches equal-color pairs.  Such
# pairs hide the checker transformation and are outside the teaching grammar.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"stripe_color_a": 1, "stripe_color_b": 1},
    {"stripe_color_a": 2, "stripe_color_b": 2},
    {"stripe_color_a": 3, "stripe_color_b": 3},
    {"stripe_color_a": 4, "stripe_color_b": 4},
    {"stripe_color_a": 5, "stripe_color_b": 5},
    {"stripe_color_a": 6, "stripe_color_b": 6},
    {"stripe_color_a": 7, "stripe_color_b": 7},
    {"stripe_color_a": 8, "stripe_color_b": 8},
    {"stripe_color_a": 9, "stripe_color_b": 9},
]

# Two demonstrations are the canonical teaching shape: one establishes the
# checker phase and a second shows that the role colors are variable.
EXAMPLES_NEEDED = 2

# All official inputs are 2x6.  Every difficulty band keeps a substantial 2x6
# prior while also teaching width generalization, so a 25% pooled floor is a
# truthful promise rather than a generic quality threshold.
MIN_STRICT_FRAC = 0.25


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or len(grid) != 2:
        return ["grid must contain exactly two rows"]
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return ["grid rows must be sequences"]
    width = len(grid[0])
    if width < 5 or width > 30:
        return [f"grid width must be in 5..30, found {width}"]
    if len(grid[1]) != width:
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers in 0..9"]
    return []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or rule-hiding stripe scenes."""
    errors = _grid_errors(grid)
    if errors:
        return errors

    top, bottom = grid[0][0], grid[1][0]
    if top == 0 or bottom == 0:
        errors.append("both row-role colors must be nonzero")
    if top == bottom:
        errors.append("row-role colors must be distinct")
    if any(value != top for value in grid[0]):
        errors.append("row 0 must be a uniform stripe matching its column-0 role")
    if any(value != bottom for value in grid[1]):
        errors.append("row 1 must be a uniform stripe matching its column-0 role")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Official empirical manifold: lawful two-row stripes at width six."""
    errors = self_check(grid)
    if errors:
        return errors
    if len(grid[0]) != 6:
        return [f"canonical train/test inputs are width 6, found {len(grid[0])}"]
    return []


def observe_overrides(grid) -> dict[str, object]:
    """Recover every exact semantic axis from the returned grid."""
    if self_check(grid):
        return {
            "grid_w": None,
            "stripe_color_a": None,
            "stripe_color_b": None,
        }
    return {
        "grid_w": len(grid[0]),
        "stripe_color_a": grid[0][0],
        "stripe_color_b": grid[1][0],
    }


def _width_options(difficulty: str | None) -> tuple[int, ...]:
    """Weighted but full-support width domain for each difficulty band."""
    all_widths = tuple(range(5, 31))
    canonical_prior = (6,) * 40
    if difficulty == "easy":
        band_bias = tuple(range(5, 11)) * 3
    elif difficulty == "hard":
        band_bias = tuple(range(12, 31)) * 3
    else:
        band_bias = tuple(range(5, 19)) * 2
    # Boundaries 5 and 30 remain legal in every band; repeated entries only
    # alter the ordinary draw distribution.
    return canonical_prior + band_bias + all_widths


def _draw_role_colors(ctx, overrides: dict[str, object]) -> tuple[int, int]:
    a_override = overrides.get("stripe_color_a")
    b_override = overrides.get("stripe_color_b")
    if a_override is not None and b_override is not None:
        try:
            same = int(a_override) == int(b_override)
        except (TypeError, ValueError):
            same = False
        if same:
            raise ValueError(
                "stripe_color_a and stripe_color_b are incompatible when equal"
            )

    # When only the bottom color is overridden, draw it first so the random top
    # color can avoid it.  This makes every individually valid color override
    # realizable rather than spuriously rejecting it due to draw order.
    if b_override is not None and a_override is None:
        bottom = ctx.draw_color("stripe_color_b", exclude={0})
        top = ctx.draw_color("stripe_color_a", exclude={0, bottom})
    else:
        top = ctx.draw_color("stripe_color_a", exclude={0})
        bottom = ctx.draw_color("stripe_color_b", exclude={0, top})
    return top, bottom


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic lawful input; the Racket rule owns outputs."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    width = ctx.draw_choice("grid_w", _width_options(difficulty))
    top, bottom = _draw_role_colors(ctx, overrides)
    grid = [[top] * width, [bottom] * width]
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"constructed invalid stripe scene: {errors}")
    return [row[:] for row in grid]


# ---------------------------------------------------------------------------
# Task-linked semantic contract
# ---------------------------------------------------------------------------

def _copy_horizontal_stripes(grid):
    """Wrong rival: preserve the two horizontal stripes unchanged."""
    return [list(row) for row in grid]


def _same_phase_rows(grid):
    """Wrong rival: alternate colors, but start both rows with the top role."""
    width = len(grid[0])
    top, bottom = grid[0][0], grid[1][0]
    row = [top if col % 2 == 0 else bottom for col in range(width)]
    return [row[:], row[:]]


def _swapped_checker_phase(grid):
    """Wrong rival: use the checker operation with both phases swapped."""
    width = len(grid[0])
    top, bottom = grid[0][0], grid[1][0]
    return [
        [bottom if col % 2 == 0 else top for col in range(width)],
        [top if col % 2 == 0 else bottom for col in range(width)],
    ]


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "copy_horizontal_stripes": _copy_horizontal_stripes,
    "same_phase_rows": _same_phase_rows,
    "swapped_checker_phase": _swapped_checker_phase,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _is_canonical_width(grid) -> bool:
    return not self_check(grid) and len(grid[0]) == 6


def _is_generalized_width(grid) -> bool:
    return not self_check(grid) and len(grid[0]) != 6


SEMANTIC_WITNESSES = {
    "canonical_width_6": _is_canonical_width,
    "generalized_width": _is_generalized_width,
}
WITNESS_RIVALS = {
    "canonical_width_6": list(SEMANTIC_RIVALS),
    "generalized_width": list(SEMANTIC_RIVALS),
}


def _expected_checker(grid) -> list[list[int]]:
    """Python test mirror only; generation never uses this as output authority."""
    width = len(grid[0])
    top, bottom = grid[0][0], grid[1][0]
    return [
        [top if (row + col) % 2 == 0 else bottom for col in range(width)]
        for row in range(2)
    ]


def lesson_identifiable(demos, query) -> list[str]:
    """Require lawful examples that refute each named plausible wrong rule.

    Reading an entire uniform row versus reading its first cell is intentionally
    answer-equivalent on every lawful input, including the query.  That is the
    only retained ambiguity; malformed textures that would separate those
    formulations are rejected by ``self_check`` instead of being taught.
    """
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    if self_check(query["input"]):
        reasons.append("query input is outside the lawful stripe grammar")

    valid_demos: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        if self_check(demo["input"]):
            reasons.append(f"demo {index} input is outside the lawful stripe grammar")
            continue
        if demo["output"] != _expected_checker(demo["input"]):
            reasons.append(f"demo {index} output is not the authoritative checker pattern")
            continue
        valid_demos.append(demo)

    for name, competitor in LESSON_COMPETITORS.items():
        if valid_demos and all(
            competitor(demo["input"]) == demo["output"] for demo in valid_demos
        ):
            reasons.append(f"named competitor {name!r} survives every demonstration")
    return reasons
