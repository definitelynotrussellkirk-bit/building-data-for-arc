"""Generator for ARC task bda2d7a6 / content hash fb1e79984e59.

The input is a rectangle of uniform Chebyshev-depth rings.  The Racket oracle
reads the diagonal ring colors, removes duplicates while preserving first
occurrence, then maps each unique color to its cyclic predecessor.  Repeated
ring colors are deliberately included because they distinguish that rule from
a simpler positional rotation of ring depths.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx, stable_rng

GENERATOR_ID = "fb1e79984e59"
TASK_ID = "fb1e79984e59"
VERSION = "4.0.0"
RULE_HASH = "392773ffe271"

SUMMARY = (
    "Generate a 5..18 by 5..18 grid whose Chebyshev-depth rings are each "
    "uniform.  Four scheduled ring grammars are used: all distinct colors, "
    "innermost repeats outermost, innermost repeats its neighbor, and a "
    "two-color alternation.  A six-step schedule covers every grammar; every "
    "three consecutive demonstrations contain both an all-distinct and an "
    "outer/inner repeated-ring witness.  Zero is alternately included and "
    "excluded.  The oracle lists diagonal "
    "ring colors outer-to-inner, removes duplicate colors preserving first "
    "occurrence, and repaints every color with the preceding unique color "
    "cyclically."
)

INVARIANTS = [
    "input is a rectangular 5..18 by 5..18 ARC grid",
    "each Chebyshev-depth ring has one uniform color",
    "the ring-color sequence matches one declared teaching grammar",
    "at least two unique colors occur, so the oracle output is non-identity",
]

RING_PATTERNS = (
    "all_distinct",
    "outer_repeat",
    "inner_repeat",
    "alternating",
)

# Cyclic lesson schedule.  Every length-3 window contains an all-distinct
# witness (which distinguishes predecessor from successor for >=3 colors) and
# an outer/inner repeated-ring witness (which distinguishes unique-color
# mapping from positional depth rotation).  All four grammars occur in six
# consecutive sample indices.
RING_PATTERN_SCHEDULE = (
    "all_distinct",
    "outer_repeat",
    "alternating",
    "all_distinct",
    "inner_repeat",
    "outer_repeat",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "5-7 easy / 6-13 medium / 9-18 hard",
        "valid": "5..18",
    },
    "grid_w": {
        "type": "int",
        "default": "5-7 easy / 6-13 medium / 9-18 hard",
        "valid": "5..18",
    },
    "ring_pattern": {
        "type": "str",
        "default": "seed-offset six-step lesson-identifying schedule",
        "valid": "all_distinct|outer_repeat|inner_repeat|alternating",
    },
    "include_zero": {
        "type": "bool",
        "default": "seed-offset alternating schedule",
        "valid": "true|false",
    },
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _reject_unknown_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    lo, hi = _difficulty_bounds(difficulty)
    scheduled_pattern = _scheduled_value(
        seed,
        sample_index,
        "ring_pattern",
        RING_PATTERN_SCHEDULE,
    )
    explicit_pattern = overrides.get("ring_pattern")
    wants_alternating = (
        explicit_pattern == "alternating"
        or (explicit_pattern is None and scheduled_pattern == "alternating")
    )

    # A lawful alternating witness needs at least four rings.  On ordinary
    # draws, raise the lower size bound so the scheduled branch always fires.
    # Explicit small dimensions remain legal with other patterns; an explicit
    # alternating+small-size combination is rejected below.
    dim_lo = max(lo, 7) if wants_alternating else lo
    h = _draw_dimension(ctx, "grid_h", dim_lo, hi)
    w = _draw_dimension(ctx, "grid_w", dim_lo, hi)
    n_rings = (min(h, w) + 1) // 2

    if explicit_pattern is not None:
        pattern = ctx.draw_choice("ring_pattern", RING_PATTERNS)
    else:
        pattern = scheduled_pattern
        if pattern == "alternating" and n_rings < 4:
            # This only occurs when an explicit dimension overrides the ordinary
            # schedule.  Preserve the dimension request and record the actual,
            # compatible scheduled grammar rather than silently returning an
            # invalid alternating scene.
            compatible = RING_PATTERNS[:3]
            pattern = compatible[
                _schedule_offset(seed, "ring_pattern_fallback") % len(compatible)
            ]
        _record_scheduled_choice(ctx, "ring_pattern", pattern, RING_PATTERNS)

    if pattern == "alternating" and n_rings < 4:
        raise ValueError(
            "ring_pattern='alternating' requires grid_h and grid_w >= 7"
        )

    if "include_zero" in overrides and overrides["include_zero"] is not None:
        include_zero = ctx.draw_choice("include_zero", (False, True))
    else:
        include_zero = bool(
            _scheduled_value(seed, sample_index, "include_zero", (False, True))
        )
        _record_scheduled_choice(
            ctx,
            "include_zero",
            include_zero,
            (False, True),
        )

    rng = ctx.draw_rng("ring_colors")
    ring_colors = _make_ring_colors(
        pattern,
        n_rings,
        include_zero=include_zero,
        rng=rng,
    )
    return [
        [
            ring_colors[min(r, c, h - 1 - r, w - 1 - c)]
            for c in range(w)
        ]
        for r in range(h)
    ]


def observe_overrides(grid):
    """Recover every declared exact semantic axis from a returned grid."""
    h, w = len(grid), len(grid[0])
    ring_colors, problems = _extract_ring_colors(grid)
    if problems:
        raise ValueError("cannot observe malformed ring grid: " + "; ".join(problems))
    pattern = _classify_ring_pattern(ring_colors)
    if pattern is None:
        raise ValueError(f"unrecognized ring-color grammar: {ring_colors!r}")
    return {
        "grid_h": h,
        "grid_w": w,
        "ring_pattern": pattern,
        "include_zero": 0 in set(ring_colors),
    }


def self_check(grid, *, difficulty=None):
    problems = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"]
    h, w = len(grid), len(grid[0])
    if not (5 <= h <= 18 and 5 <= w <= 18):
        problems.append(f"grid size {h}x{w} outside 5..18")
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return problems + ["ragged grid"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                problems.append(f"cell ({r},{c}) is not an ARC color: {value!r}")
                return problems

    ring_colors, ring_problems = _extract_ring_colors(grid)
    problems.extend(ring_problems)
    if ring_problems:
        return problems
    if len(set(ring_colors)) < 2:
        problems.append("fewer than two unique ring colors hides the cyclic mapping")
    pattern = _classify_ring_pattern(ring_colors)
    if pattern is None:
        problems.append(
            "ring-color sequence is outside the declared teaching grammar: "
            f"{ring_colors!r}"
        )
    return problems


def _difficulty_bounds(difficulty):
    if difficulty == "easy":
        return 5, 7
    if difficulty == "hard":
        return 9, 18
    return 6, 13


def _draw_dimension(ctx, label, lo, hi):
    # Explicit dimension overrides are validated against the full declared axis
    # range, independent of the default difficulty band.
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, 5, 18)
    return ctx.draw_int(label, lo, hi)


def _schedule_offset(seed, label):
    return stable_rng(seed, f"{TASK_ID}|{label}", VERSION).randrange(1 << 30)


def _scheduled_value(seed, sample_index, label, options):
    offset = _schedule_offset(seed, label)
    return options[(offset + int(sample_index)) % len(options)]


def _record_scheduled_choice(ctx, label, value, options):
    ctx._draw_options[label] = tuple(options)
    return ctx._record(label, value, from_override=False)


def _reject_unknown_overrides(overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unsupported override axis/axes: {', '.join(unknown)}")


def _distinct_palette(count, *, include_zero, rng):
    if include_zero:
        if count > 10:
            raise ValueError(f"cannot draw {count} distinct ARC colors")
        colors = [0] + rng.sample(list(range(1, 10)), count - 1)
        rng.shuffle(colors)
        return colors
    if count > 9:
        raise ValueError(f"cannot draw {count} distinct nonzero ARC colors")
    return rng.sample(list(range(1, 10)), count)


def _make_ring_colors(pattern, n_rings, *, include_zero, rng):
    if pattern == "all_distinct":
        return _distinct_palette(n_rings, include_zero=include_zero, rng=rng)
    if pattern == "outer_repeat":
        base = _distinct_palette(n_rings - 1, include_zero=include_zero, rng=rng)
        return base + [base[0]]
    if pattern == "inner_repeat":
        base = _distinct_palette(n_rings - 1, include_zero=include_zero, rng=rng)
        return base + [base[-1]]
    if pattern == "alternating":
        if n_rings < 4:
            raise ValueError("alternating ring grammar requires at least four rings")
        a, b = _distinct_palette(2, include_zero=include_zero, rng=rng)
        return [a if i % 2 == 0 else b for i in range(n_rings)]
    raise ValueError(f"unknown ring pattern: {pattern!r}")


def _extract_ring_colors(grid):
    h, w = len(grid), len(grid[0])
    n_rings = (min(h, w) + 1) // 2
    ring_colors = []
    problems = []
    for depth in range(n_rings):
        values = {
            grid[r][c]
            for r in range(h)
            for c in range(w)
            if min(r, c, h - 1 - r, w - 1 - c) == depth
        }
        if len(values) != 1:
            problems.append(f"ring depth {depth} has colors {sorted(values)!r}")
        else:
            ring_colors.append(next(iter(values)))
    return ring_colors, problems


def _classify_ring_pattern(ring_colors):
    n = len(ring_colors)
    unique = set(ring_colors)
    if len(unique) == n:
        return "all_distinct"
    if (
        n >= 4
        and len(unique) == 2
        and ring_colors[0] != ring_colors[1]
        and all(ring_colors[i] == ring_colors[i % 2] for i in range(n))
    ):
        return "alternating"
    if (
        n >= 3
        and ring_colors[0] == ring_colors[-1]
        and ring_colors[0] not in ring_colors[1:-1]
        and len(set(ring_colors[1:-1])) == n - 2
    ):
        return "outer_repeat"
    if (
        n >= 3
        and ring_colors[-2] == ring_colors[-1]
        and ring_colors[-1] not in ring_colors[:-2]
        and len(set(ring_colors[:-1])) == n - 1
    ):
        return "inner_repeat"
    return None
