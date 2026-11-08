"""Generator for ARC task a6953f00 / content hash a89702404b3c.

The official examples are dense, square color grids.  Width parity selects one
of two same-shaped candidates: odd width returns the top-left 2x2 crop; even
width returns the top-right 2x2 crop.  The generator therefore varies square
size and palette while keeping both corner candidates equally plausible.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "a89702404b3c"
TASK_ID = "a89702404b3c"
VERSION = "3.0.0"  # repair the 1x1/1x2 misread; add exact axes and lesson schedule
RULE_HASH = "72e9f9d3f0f6"  # sha256[:12] of whitespace-normalized canonical rule

SUMMARY = (
    "Given a dense square grid, inspect its width. If the width is odd, copy "
    "the top-left 2x2 crop. If the width is even, copy the top-right 2x2 crop. "
    "Both candidate corners are varied and non-degenerate, so parity—not "
    "corner content—selects the answer."
)

INVARIANTS = [
    "the input is a square grid with side length 3..12",
    "the grid uses 3..10 ARC colors with no overwhelmingly dominant color",
    "the top-left and top-right 2x2 candidates are distinct",
    "each candidate 2x2 contains at least three distinct colors",
    "sequential sample indices alternate odd/even parity so every lesson exposes both branches",
]

AXES = {
    "side": {
        "type": "int",
        "default": "lesson-scheduled, difficulty-aware 3..12",
        "valid": "3..12",
    },
    "parity": {
        "type": "str",
        "default": "alternates odd|even by sample_index",
        "valid": "odd|even",
    },
    "palette_size": {
        "type": "int",
        "default": "difficulty-aware 3..10, with canonical profile anchors",
        "valid": "3..10",
    },
}

_ALLOWED_OVERRIDES = frozenset(AXES)
_CANONICAL_PROFILES = ((3, 6), (4, 9), (5, 10), (8, 10))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic teaching input for the parity/corner rule."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unsupported override(s): {', '.join(unknown)}")

    side_override = _validated_int_override(overrides, "side", 3, 12)
    palette_override = _validated_int_override(overrides, "palette_size", 3, 10)
    parity_override = overrides.get("parity")
    if parity_override is not None and parity_override not in ("odd", "even"):
        raise ValueError("parity must be 'odd' or 'even'")
    if (
        side_override is not None
        and parity_override is not None
        and _parity(side_override) != parity_override
    ):
        raise ValueError(
            f"side={side_override} is {_parity(side_override)}, incompatible "
            f"with parity={parity_override!r}"
        )
    if (
        side_override is not None
        and palette_override is not None
        and palette_override > side_override * side_override
    ):
        raise ValueError(
            f"palette_size={palette_override} cannot fit in a "
            f"{side_override}x{side_override} grid"
        )

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # With no explicit controls, every fifth sample anchors one complete
    # canonical (side, palette-size) profile.  The other samples alternate
    # parity by sample_index, so each six-pair episode contains both branches.
    canonical_profile = None
    if not overrides and sample_index % 5 == 0:
        canonical_profile = _CANONICAL_PROFILES[
            (seed + sample_index // 5) % len(_CANONICAL_PROFILES)
        ]

    if parity_override is not None:
        desired_parity = parity_override
        parity_options = ("odd", "even")
    elif side_override is not None:
        desired_parity = _parity(side_override)
        parity_options = (desired_parity,)
    elif canonical_profile is not None:
        desired_parity = _parity(canonical_profile[0])
        parity_options = (desired_parity,)
    else:
        desired_parity = "odd" if sample_index % 2 == 0 else "even"
        parity_options = (desired_parity,)
    parity = ctx.draw_choice("parity", parity_options)

    if canonical_profile is not None:
        side_candidates = (canonical_profile[0],)
    elif side_override is not None:
        side_candidates = tuple(
            n
            for n in range(3, 13)
            if _parity(n) == parity
            and (palette_override is None or n * n >= palette_override)
        )
    else:
        lo, hi = {
            "easy": (3, 6),
            "medium": (3, 9),
            "hard": (5, 12),
            None: (3, 12),
        }[difficulty]
        side_candidates = tuple(
            n
            for n in range(lo, hi + 1)
            if _parity(n) == parity
            and (palette_override is None or n * n >= palette_override)
        )
    if not side_candidates:
        raise ValueError(
            f"no side in the requested difficulty band satisfies parity={parity!r} "
            f"and palette_size={palette_override!r}"
        )
    side = ctx.draw_choice("side", side_candidates)

    palette_cap = min(10, side * side)
    if canonical_profile is not None:
        palette_size = ctx.draw_choice("palette_size", (canonical_profile[1],))
    else:
        palette_size = ctx.draw_int_diff("palette_size", 3, palette_cap)

    palette = list(ctx.draw_distinct_colors("palette", n=palette_size))
    rng = ctx.draw_rng("cells")
    flat = [palette[index % palette_size] for index in range(side * side)]
    for _ in range(512):
        rng.shuffle(flat)
        grid = [flat[row * side : (row + 1) * side] for row in range(side)]
        if not _corner_errors(grid):
            return [row[:] for row in grid]
    raise ValueError("could not realize two non-degenerate corner candidates")


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover all exact semantic-axis values from a returned grid."""
    side = len(grid)
    return {
        "side": side,
        "parity": _parity(side),
        "palette_size": len({value for row in grid for value in row}),
    }


def rule_mirror(grid):
    """Small test-only mirror of the official crop semantics."""
    width = len(grid[0])
    left = width - 2 if width % 2 == 0 else 0
    return [row[left : left + 2] for row in grid[:2]]


def self_check(grid, *, difficulty=None, meta=None):
    """Accept canonical inputs and reject malformed/shortcut teaching scenes."""
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and nonempty"]
    if len(grid) != width:
        errors.append(f"grid must be square, got {len(grid)}x{width}")
    if not 3 <= len(grid) <= 12 or not 3 <= width <= 12:
        errors.append("square side must be in 3..12")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid values must be ARC colors 0..9")
        return errors

    counts = Counter(value for row in grid for value in row)
    if not 3 <= len(counts) <= 10:
        errors.append(f"expected 3..10 distinct colors, got {len(counts)}")
    if counts and max(counts.values()) / (len(grid) * width) > 0.45:
        errors.append("one color dominates more than 45% of the grid")
    errors.extend(_corner_errors(grid))

    requested = {}
    if isinstance(meta, dict):
        if isinstance(meta.get("overrides"), dict):
            requested.update(meta["overrides"])
        for axis in AXES:
            if axis in meta:
                requested[axis] = meta[axis]
    if requested:
        observed = observe_overrides(grid)
        for axis, expected in requested.items():
            if axis in observed and observed[axis] != expected:
                errors.append(
                    f"{axis} requested {expected!r}, observed {observed[axis]!r}"
                )
    return errors



def strict_canonical_like(grid):
    """Expose the selected structural grammar to the semantic review gate."""
    return self_check(grid)

def _corner_errors(grid) -> list[str]:
    if not grid or not grid[0] or len(grid) < 2 or len(grid[0]) < 2:
        return ["grid must contain two-row, two-column corner candidates"]
    width = len(grid[0])
    top_left = [row[:2] for row in grid[:2]]
    top_right = [row[-2:] for row in grid[:2]]
    errors: list[str] = []
    if top_left == top_right:
        errors.append("top-left and top-right 2x2 candidates must differ")
    if len({value for row in top_left for value in row}) < 3:
        errors.append("top-left 2x2 candidate must contain at least three colors")
    if len({value for row in top_right for value in row}) < 3:
        errors.append("top-right 2x2 candidate must contain at least three colors")
    return errors


def _validated_int_override(overrides, name, lo, hi):
    raw = overrides.get(name)
    if raw is None:
        return None
    if type(raw) is not int or not lo <= raw <= hi:
        raise ValueError(f"{name} must be an integer in {lo}..{hi}")
    return raw


def _parity(side: int) -> str:
    return "even" if side % 2 == 0 else "odd"
