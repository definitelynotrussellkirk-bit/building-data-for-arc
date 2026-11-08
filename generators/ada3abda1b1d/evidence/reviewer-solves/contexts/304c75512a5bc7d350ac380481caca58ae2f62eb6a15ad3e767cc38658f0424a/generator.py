"""Generator for ``ada3abda1b1d`` — keep colors occurring exactly twice.

The transformation is global, not geometric: count every non-background color
in the whole input and preserve all cells of a color iff its total count is two.
The teaching schedule cycles singleton, triple, and mixed triple/quad
distractors. Every ordinary non-anchor sample also contains a compact
count-1/count-4/count-5 boundary bundle, so both production lessons and any
three-of-four query rotation rule out the principal near-miss counting rules.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ada3abda1b1d"
TASK_ID = GENERATOR_ID
VERSION = "3.2.0"
RULE_HASH = "761b29fec54a"

SUMMARY = (
    "On a zero-background grid, count all occurrences of each nonzero color. "
    "Keep every cell whose color occurs exactly twice and erase every color "
    "occurring once, three times, four times, or five times. Ordinary "
    "non-anchor samples contain count-1, count-4, and count-5 witnesses, "
    "while exact canonical anchors retain the public count profiles."
)

INVARIANTS = [
    "the grid is rectangular, uses ARC colors, and contains zero background",
    "four to six distinct nonzero colors are present",
    "one to three colors occur exactly twice and therefore survive",
    "at least one distractor color occurs once, three times, four times, or five times",
    "ordinary non-anchor samples jointly witness counts one, four, and five",
    "distractor counts follow a declared singleton, triple, or canonical-mixed profile",
    "the output is same-size, nonempty, and differs from the input",
]

COUNTER_HYPOTHESES = [
    "copy the input unchanged",
    "erase every non-background cell",
    "keep every repeated color (count at least two)",
    "keep colors occurring at most twice, including singletons",
    "keep colors with any even count",
    "keep colors occurring exactly twice or at least five times",
    "keep only the modal-frequency colors",
    "keep the first two cells of every repeated color",
    "use fixed positions, grid dimensions, or palette values instead of global counts",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20

COUNT_PROFILES = ("singletons", "triples", "canonical_mixed")
SCHEDULE_PROFILES = COUNT_PROFILES
HIGH_DISTRACTOR_COUNT = 5
BOUNDARY_COUNTS = (1, 4, HIGH_DISTRACTOR_COUNT)

# Every caller-visible control is exact, consumed by GenCtx, and recoverable
# from the returned grid through observe_overrides(). Layout and palette are
# deterministic nuisance variation, not pseudo-axes.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical anchor or difficulty-skewed",
        "valid": "4..12",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical anchor or difficulty-skewed",
        "valid": "5..16",
    },
    "n_colors": {
        "type": "int",
        "default": "scheduled canonical anchor or difficulty-skewed",
        "valid": "4..6",
    },
    "pair_colors": {
        "type": "int",
        "default": "scheduled canonical anchor or difficulty-skewed",
        "valid": "1..3",
    },
    "count_profile": {
        "type": "str",
        "default": "three-slot lesson schedule with count-1/4/5 boundary witnesses",
        "valid": "|".join(COUNT_PROFILES),
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[object, ...] = ()

_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_CANONICAL_SIGNATURES = {
    (1, 1, 2, 2, 2),
    (2, 2, 3, 3, 4),
    (2, 2, 2, 3),
}
# Three exact public-input profiles in a twelve-slot cycle: 25% strict support
# in every band while the remaining slots broaden dimensions and counts.
_CANONICAL_DEFAULTS = {
    0: {
        "grid_h": 5,
        "grid_w": 7,
        "n_colors": 5,
        "pair_colors": 3,
        "count_profile": "singletons",
    },
    4: {
        "grid_h": 5,
        "grid_w": 7,
        "n_colors": 4,
        "pair_colors": 3,
        "count_profile": "triples",
    },
    8: {
        "grid_h": 5,
        "grid_w": 7,
        "n_colors": 5,
        "pair_colors": 2,
        "count_profile": "canonical_mixed",
    },
}


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    for name, lo, hi in (
        ("grid_h", 4, 12),
        ("grid_w", 5, 16),
        ("n_colors", 4, 6),
        ("pair_colors", 1, 3),
    ):
        value = overrides.get(name)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name} must be an integer")
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")

    profile = overrides.get("count_profile")
    if profile is not None and profile not in COUNT_PROFILES:
        raise ValueError(
            "count_profile must be one of " + ", ".join(COUNT_PROFILES)
        )


def _scheduled_int(
    ctx,
    overrides: dict[str, Any],
    label: str,
    default: int,
    lo: int,
    hi: int,
) -> int:
    """Consume an explicit override, otherwise record the scheduled default."""
    if overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _scheduled_choice(
    ctx,
    overrides: dict[str, Any],
    label: str,
    default: str,
    options: Sequence[str],
) -> str:
    """Consume an explicit override, otherwise record the scheduled default."""
    if overrides.get(label) is not None:
        return str(ctx.draw_choice(label, options))
    return str(ctx.draw_choice(label, (default,)))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the decisive three-slot distractor schedule profile."""
    del seed, difficulty
    return COUNT_PROFILES[int(sample_index) % len(COUNT_PROFILES)]


def _profile_defaults(ctx, sample_index: int, difficulty: str | None) -> dict[str, Any]:
    slot = int(sample_index) % 12
    if slot in _CANONICAL_DEFAULTS:
        return dict(_CANONICAL_DEFAULTS[slot])

    rng = ctx.draw_rng("profile_defaults")
    profile = schedule_profile(0, sample_index, difficulty)
    minimum_distractors = 3 if profile == "singletons" else 4
    if difficulty == "easy":
        h = rng.randint(5, 6)
        w = rng.randint(7, 9)
        n_colors = 5
        pair_colors = rng.randint(
            1,
            min(3, n_colors - minimum_distractors),
        )
    elif difficulty == "medium":
        h = rng.randint(6, 9)
        w = rng.randint(8, 12)
        n_colors = rng.choice((5, 6))
        pair_colors = rng.randint(
            1,
            min(3, n_colors - minimum_distractors),
        )
    elif difficulty == "hard":
        h = rng.randint(8, 12)
        w = rng.randint(11, 16)
        n_colors = 6
        pair_colors = rng.randint(
            1,
            min(3, n_colors - minimum_distractors),
        )
    else:
        h = rng.randint(5, 10)
        w = rng.randint(7, 13)
        n_colors = rng.randint(5, 6)
        pair_colors = rng.randint(
            1,
            min(3, n_colors - minimum_distractors),
        )

    return {
        "grid_h": h,
        "grid_w": w,
        "n_colors": n_colors,
        "pair_colors": pair_colors,
        "count_profile": profile,
    }


def _distractor_counts(
    profile: str,
    n_distractors: int,
    *,
    include_boundary_bundle: bool = False,
) -> list[int]:
    """Build a recoverable profile, optionally adding all boundary witnesses."""
    if n_distractors < 1:
        raise ValueError("at least one distractor color is required")
    if include_boundary_bundle:
        if profile == "singletons" and n_distractors >= 3:
            return [1] * (n_distractors - 2) + [4, HIGH_DISTRACTOR_COUNT]
        if profile == "triples" and n_distractors >= 4:
            return (
                [1]
                + [3] * (n_distractors - 3)
                + [4, HIGH_DISTRACTOR_COUNT]
            )
        if profile == "canonical_mixed" and n_distractors >= 4:
            return [1] + [4] * (n_distractors - 2) + [HIGH_DISTRACTOR_COUNT]
    if profile == "singletons":
        return [1] * n_distractors
    if profile == "triples":
        return [3] * n_distractors
    if profile == "canonical_mixed":
        # This exactly realizes the public [3,3,4] profile for three
        # distractors. With one distractor, the distinct quad branch remains
        # observable and recoverable as canonical_mixed.
        return [3] * (n_distractors - 1) + [4]
    raise ValueError(f"unknown count profile: {profile!r}")


def _grid_counts(grid: Sequence[Sequence[int]]) -> Counter[int]:
    return Counter(value for row in grid for value in row if value != 0)


def _classify_count_profile(distractor_counts: Sequence[int]) -> str | None:
    values = sorted(int(value) for value in distractor_counts)
    value_set = set(values)
    if set(BOUNDARY_COUNTS) <= value_set:
        if 3 in value_set:
            return "triples"
        if values.count(4) >= 2:
            return "canonical_mixed"
        return "singletons"
    if values and 1 in value_set and value_set <= {1, HIGH_DISTRACTOR_COUNT}:
        return "singletons"
    if values and 3 in value_set and value_set <= {3, HIGH_DISTRACTOR_COUNT}:
        return "triples"
    if values == [3] * (len(values) - 1) + [4]:
        return "canonical_mixed"
    return None


def _analysis(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return {"errors": ["grid must be a non-empty rectangular sequence"]}

    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}

    height = len(grid)
    if not 4 <= height <= 12:
        errors.append(f"grid height {height} outside 4..12")
    if not 5 <= width <= 16:
        errors.append(f"grid width {width} outside 5..16")

    values = [value for row in grid for value in row]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for value in values
    ):
        errors.append("cells must be integer ARC colors 0..9")
        return {"errors": errors}
    if 0 not in values:
        errors.append("zero background is required")

    counts = Counter(value for value in values if value != 0)
    n_colors = len(counts)
    if not 4 <= n_colors <= 6:
        errors.append(f"need 4..6 distinct nonzero colors, found {n_colors}")

    pair_colors = sorted(color for color, count in counts.items() if count == 2)
    distractor_counts = sorted(count for count in counts.values() if count != 2)
    if not 1 <= len(pair_colors) <= 3:
        errors.append(
            f"need 1..3 exactly-twice colors, found {len(pair_colors)}"
        )
    if not distractor_counts:
        errors.append("at least one non-pair distractor color is required")

    count_profile = _classify_count_profile(distractor_counts)
    if distractor_counts and count_profile is None:
        errors.append(
            "distractor counts must match a declared singleton, triple, "
            "or canonical-mixed profile"
        )

    if sum(counts.values()) >= height * width:
        errors.append("at least one zero background cell must remain")

    return {
        "errors": errors,
        "grid_h": height,
        "grid_w": width,
        "counts": counts,
        "signature": tuple(sorted(counts.values())),
        "n_colors": n_colors,
        "pair_colors": len(pair_colors),
        "distractor_counts": tuple(distractor_counts),
        "count_profile": count_profile,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, degenerate, and rule-hiding lesson inputs."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Recognize the exact public dimension/count manifold, ignoring positions."""
    analysis = _analysis(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    if (analysis["grid_h"], analysis["grid_w"]) != (5, 7):
        reasons.append("canonical inputs are exactly 5x7")
    if analysis["signature"] not in _CANONICAL_SIGNATURES:
        reasons.append("nonzero color-count signature is not one of the public profiles")
    return reasons


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact AXES value from a returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n_colors": analysis["n_colors"],
        "pair_colors": analysis["pair_colors"],
        "count_profile": analysis["count_profile"],
    }


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python test mirror; the canonical Racket program is authoritative."""
    if self_check(grid):
        raise ValueError("rule_mirror expects a lawful lesson input")
    counts = _grid_counts(grid)
    return [
        [value if value != 0 and counts[value] == 2 else 0 for value in row]
        for row in grid
    ]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, nondegenerate counting lesson input."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    defaults = _profile_defaults(ctx, int(sample_index), difficulty)

    h = _scheduled_int(ctx, overrides, "grid_h", defaults["grid_h"], 4, 12)
    w = _scheduled_int(ctx, overrides, "grid_w", defaults["grid_w"], 5, 16)
    n_colors = _scheduled_int(
        ctx, overrides, "n_colors", defaults["n_colors"], 4, 6
    )
    pair_colors = _scheduled_int(
        ctx, overrides, "pair_colors", defaults["pair_colors"], 1, 3
    )
    count_profile = _scheduled_choice(
        ctx,
        overrides,
        "count_profile",
        defaults["count_profile"],
        COUNT_PROFILES,
    )

    n_distractors = n_colors - pair_colors
    minimum_distractors = 3 if count_profile == "singletons" else 4
    include_boundary_bundle = (
        int(sample_index) % 12 not in _CANONICAL_DEFAULTS
        and n_distractors >= minimum_distractors
    )
    distractor_counts = _distractor_counts(
        count_profile,
        n_distractors,
        include_boundary_bundle=include_boundary_bundle,
    )
    counts = [2] * pair_colors + distractor_counts
    if sum(counts) >= h * w and include_boundary_bundle:
        # Tiny explicit override grids may lack room for the optional boundary
        # witness. Preserve the requested profile rather than rejecting a
        # combination that was historically valid.
        distractor_counts = _distractor_counts(count_profile, n_distractors)
        counts = [2] * pair_colors + distractor_counts
    if sum(counts) >= h * w:
        # The declared domains are deliberately chosen so this is unreachable;
        # keep the assertion loud in case a later axis expansion breaks it.
        raise ValueError(
            f"requested counts need {sum(counts)} cells but grid is only {h}x{w}"
        )

    colors = list(ctx.draw_distinct_colors("colors", n=n_colors, exclude={0}))
    role_rng = ctx.draw_rng("color_roles")
    role_rng.shuffle(colors)
    layout_rng = ctx.draw_rng("layout")
    cells = [(row, col) for row in range(h) for col in range(w)]
    layout_rng.shuffle(cells)

    grid = full_grid(h, w, 0)

    # Canonical inputs include same-color runs of lengths two, three, and four.
    # Deliberately realize one such component in every draw so a learner cannot
    # mistake "isolated colored dots" for part of the rule. The decisive count
    # remains global; all other occurrences are placed independently.
    clustered_index = 0 if count_profile == "singletons" else len(counts) - 1
    clustered_count = counts[clustered_index]
    line_candidates = [
        [(row, col + offset) for offset in range(clustered_count)]
        for row in range(h)
        for col in range(w - clustered_count + 1)
    ] + [
        [(row + offset, col) for offset in range(clustered_count)]
        for row in range(h - clustered_count + 1)
        for col in range(w)
    ]
    clustered_cells = layout_rng.choice(line_candidates)
    clustered_color = colors[clustered_index]
    for row, col in clustered_cells:
        grid[row][col] = clustered_color

    occupied = set(clustered_cells)
    remaining_cells = [cell for cell in cells if cell not in occupied]
    cursor = 0
    for index, (color, count) in enumerate(zip(colors, counts)):
        if index == clustered_index:
            continue
        for row, col in remaining_cells[cursor : cursor + count]:
            grid[row][col] = color
        cursor += count

    errors = self_check(grid)
    if errors:
        raise AssertionError("constructed invalid grid: " + "; ".join(errors))
    return grid


def _mask_by_count(grid, predicate: Callable[[int, Counter[int]], bool]) -> list[list[int]]:
    counts = _grid_counts(grid)
    return [
        [
            value
            if value != 0 and predicate(counts[value], counts)
            else 0
            for value in row
        ]
        for row in grid
    ]


def _rival_identity(grid):
    return [list(row) for row in grid]


def _rival_erase_all(grid):
    return full_grid(len(grid), len(grid[0]), 0)


def _rival_keep_repeated(grid):
    return _mask_by_count(grid, lambda count, _: count >= 2)


def _rival_keep_at_most_two(grid):
    return _mask_by_count(grid, lambda count, _: count <= 2)


def _rival_keep_even(grid):
    return _mask_by_count(grid, lambda count, _: count % 2 == 0)


def _rival_keep_two_or_five_plus(grid):
    return _mask_by_count(
        grid,
        lambda count, _: count == 2 or count >= HIGH_DISTRACTOR_COUNT,
    )


def _rival_keep_modal(grid):
    counts = _grid_counts(grid)
    modal = max(counts.values())
    return _mask_by_count(grid, lambda count, _: count == modal)


def _rival_trim_to_two(grid):
    counts = _grid_counts(grid)
    remaining = {color: min(2, count) for color, count in counts.items() if count >= 2}
    output = full_grid(len(grid), len(grid[0]), 0)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value in remaining and remaining[value] > 0:
                output[row][col] = value
                remaining[value] -= 1
    return output


SEMANTIC_RIVALS = {
    "identity": _rival_identity,
    "erase_all": _rival_erase_all,
    "keep_repeated": _rival_keep_repeated,
    "keep_at_most_two": _rival_keep_at_most_two,
    "keep_even": _rival_keep_even,
    "keep_two_or_five_plus": _rival_keep_two_or_five_plus,
    "keep_modal": _rival_keep_modal,
    "trim_to_two": _rival_trim_to_two,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _profile_is(name: str):
    return lambda grid: _analysis(grid).get("count_profile") == name


SEMANTIC_WITNESSES = {
    "nondegenerate_change": lambda grid: not self_check(grid),
    "singleton_distractor_erased": _profile_is("singletons"),
    "triple_distractor_erased": _profile_is("triples"),
    "quad_distractor_erased": _profile_is("canonical_mixed"),
    "count_five_distractor_erased": (
        lambda grid: HIGH_DISTRACTOR_COUNT in _grid_counts(grid).values()
    ),
}

WITNESS_RIVALS = {
    "nondegenerate_change": ["identity", "erase_all"],
    "singleton_distractor_erased": ["keep_at_most_two"],
    "triple_distractor_erased": [
        "keep_repeated",
        "keep_modal",
        "trim_to_two",
    ],
    "quad_distractor_erased": [
        "keep_repeated",
        "keep_even",
        "keep_modal",
        "trim_to_two",
    ],
    "count_five_distractor_erased": ["keep_two_or_five_plus"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demos that reject every named plausible counting shortcut."""
    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input invalid: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with exact-two rule")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    else:
        errors = self_check(query["input"])
        if errors:
            reasons.append(f"query input invalid: {errors[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output disagrees with exact-two rule")

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"named competitor survives demonstrations: {name}")
    return reasons
