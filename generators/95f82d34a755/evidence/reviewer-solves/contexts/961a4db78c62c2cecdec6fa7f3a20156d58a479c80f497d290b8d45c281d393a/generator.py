"""Generator for ARC task 95f82d34a755 — border equality matrix.

The top row (excluding the black corner) contains column labels and the left
column (excluding the corner) contains row labels.  The body is blank.  The
output removes the two header axes and writes the row label exactly where it
equals the corresponding column label, otherwise black.

A five-position lesson schedule deliberately varies the number and
multiplicity of shared labels.  This prevents a learner from succeeding with
fixed diagonals, one-marker, modal-color, or header-copy shortcuts.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "95f82d34a755"
TASK_ID = "95f82d34a755"
RULE_HASH = "2d47dff0a44c"  # normalized canonical program_solution hash
VERSION = "3.3.0"  # rotation-safe canonical-shortcut teaching schedule
SUMMARY = (
    "Read nonzero column labels from the top border and nonzero row labels "
    "from the left border. Remove those borders; at each output coordinate "
    "write the row label when it equals the column label, otherwise 0."
)

# Five consecutive demonstrations cover every profile below; runner.run_one
# uses consecutive sample indices, so each materialized lesson receives the
# complete semantic schedule regardless of its starting residue.
EXAMPLES_NEEDED = 5

INVARIANTS = [
    "the input is a rectangular ARC grid with at least four rows and columns",
    "cell (0,0) is black",
    "every remaining top-row and left-column header cell is nonzero",
    "all cells below/right of the header axes are black",
    "the two header axes share at least one label and also contain a mismatch",
    "the output shape is exactly one row and one column smaller than the input",
    "an output cell equals its row label iff the row and column labels match",
]

SCENE_PROFILES = (
    "single_shared",
    "left_repeat",
    "top_repeat",
    "multi_shared",
    "cross_repeat",
)
SCHEDULE_PROFILES = SCENE_PROFILES
PALETTE_BANDS = ("low", "high", "mixed")

# Every labeled canonical output is at most 4x5 and no canonical header label
# occurs more than twice on either axis.  These bounds define two executable
# canonical-fitting shortcuts below; the scheduled multi_shared anchor must
# exceed both bounds so generated lessons teach the intended generalization.
_CANONICAL_OUTPUT_MAX_H = 4
_CANONICAL_OUTPUT_MAX_W = 5

AXES = {
    "grid_h": {
        "type": "int",
        "default": "paired canonical anchors plus difficulty-weighted 4..9",
        "valid": "4..9",
    },
    "grid_w": {
        "type": "int",
        "default": "paired canonical anchors plus difficulty-weighted 5..9",
        "valid": "5..9",
    },
    "scene_profile": {
        "type": "str",
        "default": "sample_index cycles through all five lesson profiles",
        "valid": "|".join(SCENE_PROFILES),
    },
    "palette_band": {
        "type": "str",
        "default": "mixed favored, with low and high bands retained",
        "valid": "|".join(PALETTE_BANDS),
    },
}

# Every declared combination is constructible.  Declaring the empty matrix
# activates the strict override policy instead of the legacy "any ValueError
# is intentional" behavior.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[()] = ()


def _is_arc_grid(grid: Any) -> bool:
    return (
        isinstance(grid, (list, tuple))
        and bool(grid)
        and isinstance(grid[0], (list, tuple))
        and bool(grid[0])
        and all(isinstance(row, (list, tuple)) and len(row) == len(grid[0]) for row in grid)
        and all(
            isinstance(value, int)
            and not isinstance(value, bool)
            and 0 <= value <= 9
            for row in grid
            for value in row
        )
    )


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror used only for focused tests and rival analysis."""
    return [
        [grid[r][0] if grid[r][0] == grid[0][c] else 0 for c in range(1, len(grid[0]))]
        for r in range(1, len(grid))
    ]


def _facts(grid: Any) -> dict[str, Any]:
    if not _is_arc_grid(grid):
        raise ValueError("grid must be a nonempty rectangular ARC grid")
    h, w = len(grid), len(grid[0])
    if h < 2 or w < 2:
        raise ValueError("grid must contain both header axes and a body")

    top = list(grid[0][1:])
    left = [grid[r][0] for r in range(1, h)]
    top_set, left_set = set(top), set(left)
    shared = top_set & left_set
    palette = top_set | left_set
    pivot = min(shared) if shared else None
    match_count = sum(rv == cv for rv in left for cv in top)
    mismatch_count = len(left) * len(top) - match_count

    if palette and max(palette) <= 4:
        palette_band = "low"
    elif palette and min(palette) >= 6:
        palette_band = "high"
    elif palette:
        # Any palette spanning the low/high boundary, or using neutral color 5,
        # is the observable mixed band.
        palette_band = "mixed"
    else:
        palette_band = "unclassified"

    scene_profile = "unclassified"
    if len(shared) == 1 and pivot is not None:
        if top.count(pivot) == 1 and left.count(pivot) == 1:
            scene_profile = "single_shared"
    elif len(shared) >= 3:
        scene_profile = "multi_shared"
    elif len(shared) == 2 and pivot is not None:
        left_repeat = left.count(pivot) >= 2
        top_repeat = top.count(pivot) >= 2
        if left_repeat and top_repeat:
            scene_profile = "cross_repeat"
        elif left_repeat:
            scene_profile = "left_repeat"
        elif top_repeat:
            scene_profile = "top_repeat"

    return {
        "grid_h": h,
        "grid_w": w,
        "top": top,
        "left": left,
        "top_set": top_set,
        "left_set": left_set,
        "shared": shared,
        "palette": palette,
        "pivot": pivot,
        "match_count": match_count,
        "mismatch_count": mismatch_count,
        "palette_band": palette_band,
        "scene_profile": scene_profile,
    }


def observe_overrides(grid: list[list[int]]) -> dict[str, Any]:
    """Recover every declared exact axis from the returned input grid."""
    facts = _facts(grid)
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "scene_profile": facts["scene_profile"],
        "palette_band": facts["palette_band"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the full teaching grammar, not only shape and palette."""
    del difficulty, meta
    if not _is_arc_grid(grid):
        return ["grid must be a nonempty rectangular ARC grid"]

    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if not (4 <= h <= 30 and 4 <= w <= 30):
        errors.append(f"grid dimensions {h}x{w} must be within 4..30")
    if grid[0][0] != 0:
        errors.append(f"corner cell (0,0) must be 0, found {grid[0][0]}")

    top = list(grid[0][1:])
    left = [grid[r][0] for r in range(1, h)]
    zero_top = [c + 1 for c, value in enumerate(top) if value == 0]
    zero_left = [r + 1 for r, value in enumerate(left) if value == 0]
    if zero_top:
        errors.append(f"top header contains zero at columns {zero_top}")
    if zero_left:
        errors.append(f"left header contains zero at rows {zero_left}")

    interior = [
        (r, c)
        for r in range(1, h)
        for c in range(1, w)
        if grid[r][c] != 0
    ]
    if interior:
        errors.append(
            f"interior must be all 0; found {len(interior)} nonzero cells, first {interior[:4]}"
        )

    if not zero_top and not zero_left:
        shared = set(top) & set(left)
        if not shared:
            errors.append("top and left headers have no shared label")
        if len(set(top) | set(left)) < 2:
            errors.append("headers use only one color, hiding equality-vs-fill behavior")
        match_count = sum(rv == cv for rv in left for cv in top)
        total = len(left) * len(top)
        if match_count == total:
            errors.append("every row/column pair matches, leaving no zero-output contrast")
        if match_count == 0:
            errors.append("no row/column pair matches, leaving an all-zero output")

    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize official-scale profiles inside the broader lawful grammar."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    facts = _facts(grid)
    if (facts["grid_h"], facts["grid_w"]) not in {(4, 5), (5, 6)}:
        reasons.append(
            f"dimensions {facts['grid_h']}x{facts['grid_w']} are outside official 4x5/5x6 profiles"
        )
    if not 3 <= len(facts["palette"]) <= 5:
        reasons.append(
            f"official examples use 3..5 header colors, found {len(facts['palette'])}"
        )
    return reasons


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")


def _validate_sample_index(sample_index: Any) -> None:
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic semantic role for an ordinary draw."""
    del seed, difficulty
    _validate_sample_index(sample_index)
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _weighted_dimensions(difficulty: str | None) -> tuple[list[int], list[int]]:
    if difficulty == "easy":
        return [4] * 5 + [5] * 5 + [6] * 3 + [7, 8, 9], [5] * 5 + [6] * 5 + [7] * 2 + [8, 9]
    if difficulty == "hard":
        return [4, 5, 6] + [7] * 2 + [8] * 3 + [9] * 5, [5, 6] + [7] * 2 + [8] * 3 + [9] * 5
    return [4] * 2 + [5] * 4 + [6] * 3 + [7] * 2 + [8, 9], [5] * 2 + [6] * 4 + [7] * 3 + [8] * 2 + [9]


def _palette(ctx, band: str) -> list[int]:
    rng = ctx.draw_rng("palette")
    if band == "low":
        values = rng.sample([1, 2, 3, 4], 4)
    elif band == "high":
        values = rng.sample([6, 7, 8, 9], 4)
    elif band == "mixed":
        mode = rng.randrange(3)
        if mode == 0:
            values = rng.sample([1, 2, 3, 4], 2) + rng.sample([6, 7, 8, 9], 2)
        elif mode == 1:
            values = rng.sample([1, 2, 3, 4], 1) + [5] + rng.sample([6, 7, 8, 9], 2)
        else:
            values = rng.sample([1, 2, 3, 4], 2) + [5] + rng.sample([6, 7, 8, 9], 1)
        rng.shuffle(values)
    else:  # guarded by ctx.draw_choice, kept loud for direct helper misuse
        raise ValueError(f"unsupported palette_band {band!r}")
    return values


def _fill_headers(
    length: int,
    required: list[int],
    fillers: list[int],
    rng,
) -> list[int]:
    if len(required) > length:
        raise ValueError(
            f"header length {length} cannot hold {len(required)} required labels"
        )
    if not fillers and len(required) < length:
        raise ValueError("header needs at least one lawful filler color")
    values = list(required)
    while len(values) < length:
        values.append(fillers[(len(values) - len(required)) % len(fillers)])
    rng.shuffle(values)
    return values


def _build_headers(
    profile: str,
    palette: list[int],
    top_len: int,
    left_len: int,
    rng,
) -> tuple[list[int], list[int]]:
    shuffled = list(palette)
    rng.shuffle(shuffled)

    if profile == "single_shared":
        pivot, top_a, top_b, left_a = shuffled
        top = _fill_headers(top_len, [pivot], [top_a, top_b], rng)
        left = _fill_headers(left_len, [pivot], [left_a], rng)
        return top, left

    if profile == "multi_shared":
        shared = sorted(shuffled[:3])
        extra = shuffled[3]
        if rng.randrange(2) == 0:
            top_fill, left_fill = [extra], [shared[-1]]
        else:
            top_fill, left_fill = [shared[-1]], [extra]
        top = _fill_headers(top_len, shared, top_fill, rng)
        left = _fill_headers(left_len, shared, left_fill, rng)
        return top, left

    shared = sorted(shuffled[:2])
    pivot, other = shared
    top_only, left_only = shuffled[2], shuffled[3]

    if profile == "cross_repeat":
        # Keep both shared labels and one axis-specific label observable, then
        # use the shared pivot as filler.  On the scheduled 8x9 anchor this
        # forces third occurrences and matches beyond the canonical 4x5 body,
        # providing an independent leave-one-out witness alongside multi_shared.
        top_required = [pivot, pivot, other]
        left_required = [pivot, pivot, other]
        if top_len >= 4:
            top_required.append(top_only)
        if left_len >= 4:
            left_required.append(left_only)
        return (
            _fill_headers(top_len, top_required, [pivot], rng),
            _fill_headers(left_len, left_required, [pivot], rng),
        )

    top_pivot_count = 2 if profile == "top_repeat" else 1
    left_pivot_count = 2 if profile == "left_repeat" else 1
    top = _fill_headers(
        top_len,
        [pivot] * top_pivot_count + [other],
        [top_only],
        rng,
    )
    left = _fill_headers(
        left_len,
        [pivot] * left_pivot_count + [other],
        [left_only],
        rng,
    )
    return top, left


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_sample_index(sample_index)
    _validate_call(difficulty, overrides)

    # Make the five-demo teaching schedule exact while preserving explicit
    # caller precedence.  The injected value still flows through GenCtx and
    # is therefore recorded in keyed provenance.
    effective = dict(overrides)
    residue = int(sample_index) % len(SCHEDULE_PROFILES)
    if effective.get("scene_profile") is None:
        effective["scene_profile"] = schedule_profile(seed, sample_index, difficulty)
    # Two positions anchor the official input shapes.  Two independent 8x9
    # adversarial positions (multi_shared and cross_repeat) force both a third
    # shared-label occurrence and a match outside the canonical 4x5 output
    # envelope.  Therefore holding out any one of six consecutive lesson items
    # still leaves a counterexample in the five demonstrations.
    if "grid_h" not in effective and "grid_w" not in effective:
        if residue == 0:
            effective["grid_h"], effective["grid_w"] = 4, 5
        elif residue == 1:
            effective["grid_h"], effective["grid_w"] = 5, 6
        elif residue in {3, 4}:
            effective["grid_h"], effective["grid_w"] = 8, 9

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )

    h_options, w_options = _weighted_dimensions(difficulty)
    h = ctx.draw_choice("grid_h", h_options)
    w = ctx.draw_choice("grid_w", w_options)
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    palette_band = ctx.draw_choice(
        "palette_band",
        ("mixed", "mixed", "mixed", "low", "high"),
    )

    palette = _palette(ctx, palette_band)
    header_rng = ctx.draw_rng("header_layout")
    top, left = _build_headers(profile, palette, w - 1, h - 1, header_rng)

    grid = full_grid(h, w, 0)
    for c, value in enumerate(top, start=1):
        grid[0][c] = value
    for r, value in enumerate(left, start=1):
        grid[r][0] = value

    errors = self_check(grid)
    if errors:
        raise ValueError(f"internal generator invariant failure: {errors}")
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "scene_profile": profile,
        "palette_band": palette_band,
    }
    if observed != expected:
        raise ValueError(
            f"internal observable-axis mismatch: expected {expected}, observed {observed}"
        )
    return grid


def _has_single_shared(grid: list[list[int]]) -> bool:
    return len(_facts(grid)["shared"]) == 1


def _has_multiple_shared(grid: list[list[int]]) -> bool:
    return len(_facts(grid)["shared"]) >= 3


def _has_left_repeat(grid: list[list[int]]) -> bool:
    facts = _facts(grid)
    return bool(facts["pivot"] is not None and facts["left"].count(facts["pivot"]) >= 2)


def _has_top_repeat(grid: list[list[int]]) -> bool:
    facts = _facts(grid)
    return bool(facts["pivot"] is not None and facts["top"].count(facts["pivot"]) >= 2)


def _has_off_diagonal_match(grid: list[list[int]]) -> bool:
    facts = _facts(grid)
    return any(
        r != c and rv == cv
        for r, rv in enumerate(facts["left"])
        for c, cv in enumerate(facts["top"])
    )


def _has_match_and_mismatch(grid: list[list[int]]) -> bool:
    facts = _facts(grid)
    return facts["match_count"] > 0 and facts["mismatch_count"] > 0


def _has_third_shared_occurrence(grid: list[list[int]]) -> bool:
    facts = _facts(grid)
    return any(
        (facts["top"].count(value) >= 3 or facts["left"].count(value) >= 3)
        for value in facts["shared"]
    )


def _has_match_outside_canonical_extent(grid: list[list[int]]) -> bool:
    facts = _facts(grid)
    return any(
        rv == cv and (r >= _CANONICAL_OUTPUT_MAX_H or c >= _CANONICAL_OUTPUT_MAX_W)
        for r, rv in enumerate(facts["left"])
        for c, cv in enumerate(facts["top"])
    )


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "single_shared_color": _has_single_shared,
    "multiple_shared_colors": _has_multiple_shared,
    "repeated_row_label": _has_left_repeat,
    "repeated_column_label": _has_top_repeat,
    "off_diagonal_match": _has_off_diagonal_match,
    "both_match_and_mismatch": _has_match_and_mismatch,
    "third_shared_occurrence": _has_third_shared_occurrence,
    "match_outside_canonical_extent": _has_match_outside_canonical_extent,
}

# These six hooks describe positive branch coverage rather than a claim that a
# particular rival must disagree on every firing input.  Declaring them here
# keeps the semantic gate honest: presence is useful, but not rival evidence.
BRANCH_WITNESSES = (
    "single_shared_color",
    "multiple_shared_colors",
    "repeated_row_label",
    "repeated_column_label",
    "off_diagonal_match",
    "both_match_and_mismatch",
)

WITNESS_RIVALS = {
    "third_shared_occurrence": ["first_two_occurrences_only"],
    "match_outside_canonical_extent": ["canonical_extent_only"],
}


def _all_pairs_nonzero(grid: list[list[int]]) -> list[list[int]]:
    facts = _facts(grid)
    return [[rv for _cv in facts["top"]] for rv in facts["left"]]


def _mark_matches_with_one(grid: list[list[int]]) -> list[list[int]]:
    facts = _facts(grid)
    return [[1 if rv == cv else 0 for cv in facts["top"]] for rv in facts["left"]]


def _diagonal_only(grid: list[list[int]]) -> list[list[int]]:
    facts = _facts(grid)
    return [
        [rv if r == c and rv == cv else 0 for c, cv in enumerate(facts["top"])]
        for r, rv in enumerate(facts["left"])
    ]


def _first_shared_only(grid: list[list[int]]) -> list[list[int]]:
    facts = _facts(grid)
    chosen = min(facts["shared"])
    return [
        [rv if rv == cv == chosen else 0 for cv in facts["top"]]
        for rv in facts["left"]
    ]


def _canonical_extent_only(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting shortcut: ignore matches beyond the seen 4x5 body."""
    output = rule_mirror(grid)
    return [
        [
            value if r < _CANONICAL_OUTPUT_MAX_H and c < _CANONICAL_OUTPUT_MAX_W else 0
            for c, value in enumerate(row)
        ]
        for r, row in enumerate(output)
    ]


def _first_two_occurrences_only(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting shortcut: never generalize to a third repeated label."""
    facts = _facts(grid)

    top_ranks: list[int] = []
    top_seen: Counter[int] = Counter()
    for value in facts["top"]:
        top_seen[value] += 1
        top_ranks.append(top_seen[value])

    left_ranks: list[int] = []
    left_seen: Counter[int] = Counter()
    for value in facts["left"]:
        left_seen[value] += 1
        left_ranks.append(left_seen[value])

    return [
        [
            rv
            if rv == cv and left_ranks[r] <= 2 and top_ranks[c] <= 2
            else 0
            for c, cv in enumerate(facts["top"])
        ]
        for r, rv in enumerate(facts["left"])
    ]


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "canonical_extent_only": _canonical_extent_only,
    "first_two_occurrences_only": _first_two_occurrences_only,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "fill_each_row": _all_pairs_nonzero,
    "mark_matches_with_one": _mark_matches_with_one,
    "diagonal_matches_only": _diagonal_only,
    "only_smallest_shared_color": _first_shared_only,
    **SEMANTIC_RIVALS,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Confirm that a materialized lesson refutes the named shortcut rules."""
    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    try:
        query_input = query["input"]
        if self_check(query_input):
            reasons.append("query input is outside the calibrated teaching grammar")
        for name, competitor in LESSON_COMPETITORS.items():
            if all(competitor(demo["input"]) == demo["output"] for demo in demos):
                reasons.append(f"competitor {name!r} fits every demonstration")
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        reasons.append(f"lesson analysis failed: {type(exc).__name__}: {exc}")
    return sorted(set(reasons))


def mutation_impostors(grid: list[list[int]]) -> list[tuple[str, list[list[int]]]]:
    """Targeted malformed scenes used by focused tests and review evidence."""
    facts = _facts(grid)
    impostors: list[tuple[str, list[list[int]]]] = []

    corner = [list(row) for row in grid]
    corner[0][0] = facts["top"][0]
    impostors.append(("nonzero_corner", corner))

    interior = [list(row) for row in grid]
    interior[1][1] = facts["top"][0]
    impostors.append(("nonzero_interior", interior))

    zero_header = [list(row) for row in grid]
    zero_header[0][1] = 0
    impostors.append(("zero_top_header", zero_header))

    disjoint = [list(row) for row in grid]
    top_colors = set(disjoint[0][1:])
    replacement = next(color for color in range(1, 10) if color not in top_colors)
    for r in range(1, len(disjoint)):
        disjoint[r][0] = replacement
    impostors.append(("disjoint_headers", disjoint))

    all_shared = [list(row) for row in grid]
    fill = all_shared[0][1]
    for c in range(1, len(all_shared[0])):
        all_shared[0][c] = fill
    for r in range(1, len(all_shared)):
        all_shared[r][0] = fill
    impostors.append(("all_pairs_match", all_shared))

    return impostors
