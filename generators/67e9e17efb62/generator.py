"""Generator for ARC task 5d588b4d / content hash 67e9e17efb62.

The input is a zero-background grid with one monochrome horizontal bar on the
first row.  If the bar has length L and color k, the oracle writes runs of k
with lengths 1,2,...,L,...,2,1, separates adjacent runs by one zero, then wraps
that one-dimensional stream row-major at the input width and pads the final row
with zeros.

Version 3 replaces an inaccurate spatial-pyramid description, duplicate weak
``self_check`` definitions, unused/inert axes, and difficulty-local override
bounds.  One quarter of ordinary sample indices use exact canonical
(height, width, bar-length, left-anchor) profiles; the remaining draws explore
lawful left/right anchored variants over the full declared boundary ranges.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "67e9e17efb62"
TASK_ID = "67e9e17efb62"
VERSION = "3.0.0"
RULE_HASH = "824697c034e9"

SUMMARY = (
    "A rectangular 0-background grid contains exactly one contiguous, "
    "single-color bar on row 0, touching either the left or right edge. "
    "Let its color be k and length be L. The output is the row-major wrapping "
    "of colored run lengths 1,2,...,L,L-1,...,2,1, with exactly one 0 between "
    "successive runs; the final output row is padded with 0s to the input "
    "width. The input height and bar position do not alter the run sequence."
)

INVARIANTS = [
    "all cells are literal ARC colors 0..9 and the background is 0",
    "grid height is 3..14 and width is 5..23",
    "row 0 contains one contiguous monochrome bar of length 3..8",
    "the bar touches exactly one horizontal edge and leaves at least one zero",
    "every row below row 0 is entirely zero",
]

POSITION_BIASES = ("left", "right")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed draw over 3..14; canonical prior at 7,8,13",
        "valid": "3..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed compatible draw over 5..23",
        "valid": "5..23",
    },
    "bar_len": {
        "type": "int",
        "default": "difficulty-skewed compatible draw over 3..8",
        "valid": "3..8",
    },
    "color": {
        "type": "color",
        "default": "keyed nonzero ARC color",
        "valid": "1..9",
    },
    "position_bias": {
        "type": "str",
        "default": "keyed left/right draw; canonical prior is left",
        "valid": "left|right",
    },
}

_ALLOWED_DIFFICULTIES = frozenset({None, "easy", "medium", "hard"})
_INT_OVERRIDE_RANGES = {
    "grid_h": (3, 14),
    "grid_w": (5, 23),
    "bar_len": (3, 8),
    "color": (1, 9),
}


def _validate_generate_request(seed, sample_index, difficulty, overrides) -> None:
    """Reject coerced scalars and undeclared controls before they reach GenCtx."""
    if type(seed) is not int:
        raise TypeError(f"seed must be a literal int, got {type(seed).__name__}")
    if type(sample_index) is not int:
        raise TypeError(
            f"sample_index must be a literal int, got {type(sample_index).__name__}"
        )
    if sample_index < 0:
        raise ValueError(f"sample_index must be nonnegative, got {sample_index}")
    if difficulty is not None and type(difficulty) is not str:
        raise TypeError(
            f"difficulty must be None or a literal str, got {type(difficulty).__name__}"
        )
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard', "
            f"got {difficulty!r}"
        )

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    for name, (lower, upper) in _INT_OVERRIDE_RANGES.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(
                f"{name} must be a literal int, got {type(value).__name__}"
            )
        if not lower <= value <= upper:
            raise ValueError(f"{name} must be in {lower}..{upper}, got {value}")

    position_bias = overrides.get("position_bias")
    if position_bias is not None:
        if type(position_bias) is not str:
            raise TypeError(
                "position_bias must be a literal str, "
                f"got {type(position_bias).__name__}"
            )
        if position_bias not in POSITION_BIASES:
            raise ValueError(
                "position_bias must be 'left' or 'right', "
                f"got {position_bias!r}"
            )


# Every official (height, width, bar length) profile.  Colors are deliberately
# not pinned: color is semantically irrelevant and broad palette support is
# useful.  sample_index % 4 == 0 selects this prior, making the strict joint
# canonical-like rate exactly 25% in every contiguous four-sample schedule.
_CANONICAL_PROFILES = (
    (8, 11, 6),
    (7, 23, 4),
    (8, 5, 3),
    (7, 23, 3),
    (13, 16, 8),
    (7, 10, 7),
)


def _analyze(grid: Any) -> tuple[dict[str, Any], list[str]]:
    """Extract the exact input grammar and return mutation-sensitive errors."""
    facts: dict[str, Any] = {
        "grid_h": None,
        "grid_w": None,
        "bar_len": None,
        "color": None,
        "position_bias": None,
        "start_col": None,
    }
    if not isinstance(grid, (list, tuple)) or not grid:
        return facts, ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return facts, ["grid must have at least one column"]

    h, w = len(grid), len(grid[0])
    facts["grid_h"], facts["grid_w"] = h, w
    errors: list[str] = []
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return facts, ["grid must be rectangular"]
    bad = sorted(
        {
            repr(value)
            for row in grid
            for value in row
            if isinstance(value, bool)
            or not isinstance(value, int)
            or not 0 <= value <= 9
        }
    )
    if bad:
        errors.append("all cells must be literal ARC colors 0..9: " + ", ".join(bad[:6]))
    if not 3 <= h <= 14:
        errors.append(f"grid height must be in 3..14, got {h}")
    if not 5 <= w <= 23:
        errors.append(f"grid width must be in 5..23, got {w}")

    top = grid[0]
    nz = [c for c, value in enumerate(top) if value != 0]
    if not nz:
        errors.append("row 0 must contain a nonzero bar")
    else:
        start, end = min(nz), max(nz)
        facts["start_col"] = start
        if nz != list(range(start, end + 1)):
            errors.append("row-0 bar must be contiguous")
        colors = {top[c] for c in nz}
        if len(colors) != 1:
            errors.append("row-0 bar must use exactly one color")
        else:
            facts["color"] = next(iter(colors))
        bar_len = len(nz)
        facts["bar_len"] = bar_len
        if not 3 <= bar_len <= 8:
            errors.append(f"bar length must be in 3..8, got {bar_len}")
        if bar_len >= w:
            errors.append("bar must leave at least one background cell")
        if start == 0 and end < w - 1:
            facts["position_bias"] = "left"
        elif end == w - 1 and start > 0:
            facts["position_bias"] = "right"
        else:
            errors.append("bar must touch exactly one horizontal edge")

    body_nz = [
        (r, c, grid[r][c])
        for r in range(1, h)
        for c in range(w)
        if grid[r][c] != 0
    ]
    if body_nz:
        errors.append(
            "all rows below row 0 must be zero; first nonzero body cells: "
            + repr(body_nz[:4])
        )
    return facts, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the full lawful input grammar, including all canonical rows."""
    del difficulty, meta
    return _analyze(grid)[1]


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every declared exact axis from a valid returned grid."""
    facts, errors = _analyze(grid)
    if errors:
        return {}
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "bar_len": facts["bar_len"],
        "color": facts["color"],
        "position_bias": facts["position_bias"],
    }


def semantic_profile(grid) -> dict[str, Any]:
    """Validated task-linked facts used by focused tests and visual review."""
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    length = int(facts["bar_len"])
    width = int(facts["grid_w"])
    stream_len = length * length + 2 * length - 2
    return {
        **facts,
        "stream_len": stream_len,
        "output_rows": (stream_len + width - 1) // width,
        "wrap_branch": "one_row" if stream_len <= width else "wrapped",
        "canonical_like": (
            facts["position_bias"] == "left"
            and (facts["grid_h"], width, length) in _CANONICAL_PROFILES
        ),
    }


def _render_run_lengths(width: int, color: int, lengths) -> list[list[int]]:
    """Serialize run lengths with one-zero separators, then wrap row-major."""
    stream: list[int] = []
    for index, run_len in enumerate(lengths):
        stream.extend([color] * run_len)
        if index + 1 < len(lengths):
            stream.append(0)
    out_h = (len(stream) + width - 1) // width
    stream.extend([0] * (out_h * width - len(stream)))
    return [stream[offset : offset + width] for offset in range(0, len(stream), width)]


def rule_mirror(grid):
    """Input-pure Python mirror of the canonical Racket transformation."""
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    width = int(facts["grid_w"])
    length = int(facts["bar_len"])
    color = int(facts["color"])
    lengths = [*range(1, length + 1), *range(length - 1, 0, -1)]
    return _render_run_lengths(width, color, lengths)


def strict_canonical_like(grid, *, difficulty=None, meta=None) -> list[str]:
    """Strict semantic-gate hook: the accepted language is the full grammar."""
    return self_check(grid, difficulty=difficulty, meta=meta)


def _ascending_only_rival(grid):
    """RIVAL: emits the rising side but omits the required descending tail."""
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    width = int(facts["grid_w"])
    length = int(facts["bar_len"])
    color = int(facts["color"])
    return _render_run_lengths(width, color, range(1, length + 1))


def _has_descending_tail_witness(grid) -> bool:
    """Every lawful instance has L>=3, so its answer must expose a tail."""
    facts, errors = _analyze(grid)
    return not errors and int(facts["bar_len"]) >= 3


SEMANTIC_WITNESSES = {
    "descending_tail": _has_descending_tail_witness,
}
SEMANTIC_RIVALS = {
    "ascending_only": _ascending_only_rival,
}
WITNESS_RIVALS = {
    "descending_tail": ["ascending_only"],
}
LESSON_COMPETITORS = {
    "ascending_only": _ascending_only_rival,
}


def _draw_dimensions(ctx, *, canonical_prior: bool) -> tuple[int, int, int]:
    """Draw exact, compatible dimensions while honoring every singleton override."""
    overrides = ctx.overrides
    if canonical_prior:
        profile = ctx.draw_rng("canonical_profile").choice(_CANONICAL_PROFILES)
        h = ctx.draw_int("grid_h", profile[0], profile[0])
        w = ctx.draw_int("grid_w", profile[1], profile[1])
        bar_len = ctx.draw_int("bar_len", profile[2], profile[2])
        return h, w, bar_len

    h = ctx.draw_int_diff("grid_h", 3, 14)
    has_w = overrides.get("grid_w") is not None
    has_l = overrides.get("bar_len") is not None
    if has_w and has_l:
        w = ctx.draw_int("grid_w", 5, 23)
        bar_len = ctx.draw_int("bar_len", 3, 8)
        if bar_len >= w:
            raise ValueError(
                f"bar_len={bar_len} is incompatible with grid_w={w}; "
                "the bar must leave at least one zero"
            )
    elif has_w:
        w = ctx.draw_int("grid_w", 5, 23)
        bar_len = ctx.draw_int_diff("bar_len", 3, min(8, w - 1))
    elif has_l:
        bar_len = ctx.draw_int("bar_len", 3, 8)
        w = ctx.draw_int_diff("grid_w", max(5, bar_len + 1), 23)
    else:
        bar_len = ctx.draw_int_diff("bar_len", 3, 8)
        w = ctx.draw_int_diff("grid_w", max(5, bar_len + 1), 23)
    return h, w, bar_len


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_generate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    dimension_or_position_override = any(
        overrides.get(name) is not None
        for name in ("grid_h", "grid_w", "bar_len", "position_bias")
    )
    canonical_prior = sample_index % 4 == 0 and not dimension_or_position_override
    h, w, bar_len = _draw_dimensions(ctx, canonical_prior=canonical_prior)
    color = ctx.draw_color("color", exclude={0})
    if canonical_prior:
        position_bias = ctx.draw_choice("position_bias", ("left",))
    else:
        position_bias = ctx.draw_choice("position_bias", POSITION_BIASES)

    grid = full_grid(h, w, 0)
    start = 0 if position_bias == "left" else w - bar_len
    for c in range(start, start + bar_len):
        grid[0][c] = color
    return grid
