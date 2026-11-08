"""Semantic generator for ARC task b9b63ae52d91.

Cyan cells whose top-bottom mirror is also cyan become red. Other cyan cells
become gray, and every non-cyan cell becomes black.
"""
from __future__ import annotations

from itertools import permutations, product

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "b9b63ae52d91"
VERSION = "2.1.0"
TASK_ID = "b9b63ae52d91"
RULE_HASH = "46194ba2dd2d"
SUMMARY = (
    "Recolor cyan cells red when the cell at the same column in the "
    "top-bottom mirrored row is cyan; recolor every other cyan cell gray."
)
EXAMPLES_NEEDED = 5
AXES = {
    "scene_family": {
        "type": "str",
        "default": "rng linked|generalized (3:6; one-third linked)",
        "valid": "linked|generalized",
        "doc": (
            "linked preserves one complete public 6x6 occupancy mask under "
            "mirror-law automorphisms; generalized varies size and orbit mix"
        ),
    },
}
INVARIANTS = [
    "all input cells are black(0) or cyan(8)",
    "at least one non-axis cyan mirror pair produces red(2)",
    "at least two asymmetric cyan cells produce gray(5)",
    "both output classes are visible on every returned grid",
    "linked scenes preserve a complete public occupancy relation",
]

BACKGROUND = 0
CYAN = 8
PAIR_COLOR = 2
SOLO_COLOR = 5
DIFFICULTIES = {None, "default", "easy", "medium", "hard"}

# Five unique public 6x6 input masks, in row-major bit order. Outputs are never
# stored: the executable vertical-mirror rule computes them live.
_PUBLIC_MASKS = (
    38046095354,
    44758189915,
    33348219366,
    52576398087,
    59639266792,
)
_GENERAL_PROFILES = (
    "balanced",
    "dense",
    "pair_heavy",
    "solo_heavy",
    "odd_axis",
    "edge_witness",
)


def _require_nonnegative_integer(name, value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")


def _copy_grid(grid):
    return [list(row) for row in grid]


def _mask_grid(mask):
    return [
        [
            CYAN if mask & (1 << (row * 6 + col)) else BACKGROUND
            for col in range(6)
        ]
        for row in range(6)
    ]


def _row_automorphisms():
    """All 48 row permutations preserving r <-> 5-r."""
    pairs = ((0, 5), (1, 4), (2, 3))
    mappings = []
    for target_order in permutations(range(3)):
        for swaps in product((False, True), repeat=3):
            mapping = [0] * 6
            for source_index, target_index in enumerate(target_order):
                source_top, source_bottom = pairs[source_index]
                target_top, target_bottom = pairs[target_index]
                if swaps[source_index]:
                    target_top, target_bottom = (
                        target_bottom,
                        target_top,
                    )
                mapping[source_top] = target_top
                mapping[source_bottom] = target_bottom
            mappings.append(tuple(mapping))
    return tuple(mappings)


_ROW_AUTOMORPHISMS = _row_automorphisms()


def _linked_signature(grid):
    if len(grid) != 6 or any(len(row) != 6 for row in grid):
        return None
    if any(value not in (BACKGROUND, CYAN) for row in grid for value in row):
        return None
    # Column order is irrelevant to this cellwise rule. For each legal row
    # automorphism, encode each column and sort the six column codes.
    candidates = []
    for mapping in _ROW_AUTOMORPHISMS:
        column_codes = []
        for col in range(6):
            code = 0
            for source_row, target_row in enumerate(mapping):
                if grid[source_row][col] == CYAN:
                    code |= 1 << target_row
            column_codes.append(code)
        candidates.append(tuple(sorted(column_codes)))
    return min(candidates)


_PUBLIC_SIGNATURE_TO_PROFILE = {
    _linked_signature(_mask_grid(mask)): f"public_{index}"
    for index, mask in enumerate(_PUBLIC_MASKS, 1)
}


def _analyze(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a nonempty rectangular matrix"], "facts": None}
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return {"errors": ["grid rows must be lists or tuples"], "facts": None}
    widths = {len(row) for row in grid}
    if len(widths) != 1 or 0 in widths:
        return {"errors": ["grid must be rectangular and nonempty"], "facts": None}
    height = len(grid)
    width = next(iter(widths))
    if not (5 <= height <= 30 and 5 <= width <= 30):
        errors.append("grid dimensions must be between 5 and 30")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or value not in (BACKGROUND, CYAN)
        for row in grid
        for value in row
    ):
        errors.append("input cells must be exactly black(0) or cyan(8)")
        return {"errors": errors, "facts": None}

    paired = []
    solo = []
    axis = []
    output = full_grid(height, width, BACKGROUND)
    for row in range(height):
        mirror_row = height - 1 - row
        for col in range(width):
            if grid[row][col] != CYAN:
                continue
            if grid[mirror_row][col] == CYAN:
                paired.append((row, col))
                if row == mirror_row:
                    axis.append((row, col))
                output[row][col] = PAIR_COLOR
            else:
                solo.append((row, col))
                output[row][col] = SOLO_COLOR
    non_axis_paired = len(paired) - len(axis)
    if non_axis_paired < 2:
        errors.append("need at least one non-axis cyan mirror pair")
    if len(solo) < 2:
        errors.append("need at least two asymmetric cyan cells")
    occupied = len(paired) + len(solo)
    if occupied == 0:
        errors.append("need visible cyan cells")
    if occupied > 0.80 * height * width:
        errors.append("cyan occupancy must leave substantial black context")

    signature = _linked_signature(grid)
    linked_profile = _PUBLIC_SIGNATURE_TO_PROFILE.get(signature)
    family = "linked" if linked_profile else "generalized"
    pair_orbits = non_axis_paired // 2
    density = occupied / (height * width)
    edge_witness = (
        grid[0][0] == CYAN
        and grid[-1][0] == CYAN
        and grid[0][-1] == CYAN
        and grid[-1][-1] == BACKGROUND
    )
    ratio = len(paired) / max(1, len(solo))
    if edge_witness:
        generalized_profile = "edge_witness"
    elif axis:
        generalized_profile = "odd_axis"
    elif density >= 0.62:
        generalized_profile = "dense"
    elif len(paired) >= 2 * len(solo):
        generalized_profile = "pair_heavy"
    elif len(solo) > len(paired):
        generalized_profile = "solo_heavy"
    elif 0.75 <= ratio <= 1.5:
        generalized_profile = "balanced"
    else:
        generalized_profile = "pair_heavy"
    facts = {
        "height": height,
        "width": width,
        "paired_cells": tuple(paired),
        "solo_cells": tuple(solo),
        "axis_cells": tuple(axis),
        "paired_count": len(paired),
        "non_axis_paired_count": non_axis_paired,
        "pair_orbits": pair_orbits,
        "solo_count": len(solo),
        "axis_count": len(axis),
        "occupied_count": occupied,
        "density": density,
        "output": output,
        "family": family,
        "linked_profile": linked_profile,
        "generalized_profile": generalized_profile,
    }
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analyze(grid)["errors"])


def rule_mirror(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _copy_grid(analysis["facts"]["output"])


def horizontal_mirror_rule(grid):
    """Plausible rival: classify cyan cells by left-right mirroring."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty rectangle")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be a nonempty rectangle")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or value not in (BACKGROUND, CYAN)
        for row in grid
        for value in row
    ):
        raise ValueError("grid values must be exactly black(0) or cyan(8)")
    return [
        [
            PAIR_COLOR
            if value == CYAN and values[width - 1 - col] == CYAN
            else SOLO_COLOR if value == CYAN else BACKGROUND
            for col, value in enumerate(values)
        ]
        for values in grid
    ]


def strict_canonical_like(grid):
    """Return reasons when an input is outside this task's lawful manifold."""
    return list(_analyze(grid)["errors"])


def _vertical_not_horizontal(grid):
    return rule_mirror(grid) != horizontal_mirror_rule(grid)


SEMANTIC_WITNESSES = {
    "vertical_not_horizontal": _vertical_not_horizontal,
}
SEMANTIC_RIVALS = {
    "horizontal_mirror": horizontal_mirror_rule,
}
WITNESS_RIVALS = {
    "vertical_not_horizontal": ["horizontal_mirror"],
}
LESSON_COMPETITORS = {
    "horizontal_mirror": horizontal_mirror_rule,
}


def lesson_identifiable(demos, query):
    """Reject a lesson when the horizontal-mirror rival survives its demos."""
    try:
        rival_fits_demos = all(
            horizontal_mirror_rule(pair["input"]) == pair["output"]
            for pair in demos
        )
        rival_changes_query = (
            horizontal_mirror_rule(query["input"]) != query["output"]
        )
    except (KeyError, TypeError, ValueError) as exc:
        return [f"invalid labeled lesson: {exc}"]
    if rival_fits_demos and rival_changes_query:
        return [
            "horizontal-mirror rival fits every demonstration but predicts "
            "a different query output"
        ]
    return []


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return "invalid"
    return analysis["facts"]["family"]


def observe_overrides(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {"scene_family": analysis["facts"]["family"]}


def _build_linked(rng):
    source = _mask_grid(rng.choice(_PUBLIC_MASKS))
    mapping = rng.choice(_ROW_AUTOMORPHISMS)
    column_targets = rng.sample(range(6), 6)
    grid = full_grid(6, 6, BACKGROUND)
    for source_row in range(6):
        for source_col in range(6):
            if source[source_row][source_col] == CYAN:
                grid[mapping[source_row]][column_targets[source_col]] = CYAN
    return grid


def _general_shape(rng, band, profile):
    ranges = {
        "easy": ((6, 8), (6, 9)),
        "medium": ((9, 13), (9, 14)),
        "hard": ((14, 18), (14, 19)),
    }
    (height_low, height_high), (width_low, width_high) = ranges[band]
    height = rng.randint(height_low, height_high)
    width = rng.randint(width_low, width_high)
    if profile == "odd_axis" and height % 2 == 0:
        height = height + 1 if height < height_high else height - 1
    if profile != "odd_axis" and height % 2 == 1 and rng.random() < 0.5:
        height = height + 1 if height < height_high else height - 1
    return height, width


def _orbit_weights(profile):
    return {
        "balanced": (3, 2, 1, 1),
        "dense": (1, 4, 1, 1),
        "pair_heavy": (2, 5, 1, 1),
        "solo_heavy": (2, 1, 3, 3),
        "odd_axis": (3, 2, 1, 1),
        "edge_witness": (3, 2, 1, 1),
    }[profile]


def _build_generalized(rng, band):
    for _ in range(100):
        profile = rng.choice(_GENERAL_PROFILES)
        height, width = _general_shape(rng, band, profile)
        grid = full_grid(height, width, BACKGROUND)
        choices = ("none", "both", "top", "bottom")
        weighted = [
            choice
            for choice, count in zip(choices, _orbit_weights(profile))
            for _ in range(count)
        ]
        for top_row in range(height // 2):
            bottom_row = height - 1 - top_row
            for col in range(width):
                state = rng.choice(weighted)
                if state in ("both", "top"):
                    grid[top_row][col] = CYAN
                if state in ("both", "bottom"):
                    grid[bottom_row][col] = CYAN
        if height % 2 == 1:
            axis_row = height // 2
            axis_probability = 0.55 if profile == "odd_axis" else 0.12
            for col in range(width):
                if rng.random() < axis_probability:
                    grid[axis_row][col] = CYAN
        if profile == "edge_witness":
            grid[0][0] = CYAN
            grid[height - 1][0] = CYAN
            grid[0][width - 1] = CYAN
            grid[height - 1][width - 1] = BACKGROUND
        analysis = _analyze(grid)
        if (
            not analysis["errors"]
            and analysis["facts"]["family"] == "generalized"
        ):
            return grid
    raise RuntimeError("could not realize generalized mirror scene")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _require_nonnegative_integer("seed", seed)
    _require_nonnegative_integer("sample_index", sample_index)
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    family = ctx.draw_choice(
        "scene_family",
        (
            "linked",
            "linked",
            "linked",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
        ),
    )
    band = "medium" if difficulty in (None, "default") else difficulty
    rng = ctx.draw_rng("scene")
    grid = (
        _build_linked(rng)
        if family == "linked"
        else _build_generalized(rng, band)
    )
    analysis = _analyze(grid)
    if analysis["errors"] or analysis["facts"]["family"] != family:
        raise RuntimeError(
            "internal construction error: "
            + "; ".join(
                analysis["errors"]
                or [
                    f"wanted {family}, observed "
                    f"{analysis['facts']['family']}"
                ]
            )
        )
    return grid
