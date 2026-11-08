"""Generator for easy_k07: fill matching border-marker intersections.

The top row names selected columns and the left column names selected rows.
For every color present on both borders, the output paints the full Cartesian
product of that color's selected rows and columns.  The output is built on a
blank grid: source border markers are selectors, not pixels to preserve.

The canonical task uses two colors and deliberately repeats markers.  Four
scheduled multiplicity profiles cover the observed canonical branches plus the
missing top/left mirror, preventing a one-intersection-per-color shortcut from
fitting generated lessons.
"""
from __future__ import annotations

import copy
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a546ac859141"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "4c10680df81c"  # sha256[:12] of whitespace-normalized canonical rule

SUMMARY = (
    "A 0-background HxW grid has exactly two nonzero colors on the top row "
    "and the left column; the corner and all interior cells start at 0. Each "
    "color occurs one or two times on each border, with a scheduled repeated-"
    "marker profile. For each shared color k, collect every left-border row "
    "R_k and every top-border column C_k, then paint k at every cell in "
    "R_k x C_k on a fresh blank output grid. Border markers are erased in the "
    "output. Repeated markers therefore expand to multiple intersections."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the grid is rectangular, 6..9 rows by 7..10 columns",
    "the corner and every interior cell are background 0",
    "exactly two nonzero colors occur, and both occur on both selector borders",
    "each color occurs one or two times on each border",
    "the joint multiplicities match one of four canonical-like profiles",
    "at least one color expands to more than one output intersection",
]

# Multiplicity pairs are (top_count, left_count), one pair per color.  The
# colors themselves are arbitrary; sorting the two pairs makes the profile
# recoverable from the returned grid without depending on color identity.
_PROFILE_SIGNATURES: dict[str, tuple[tuple[int, int], tuple[int, int]]] = {
    "block_and_single": ((1, 1), (2, 2)),
    "crossed": ((1, 2), (2, 1)),
    "left_full": ((1, 2), (2, 2)),
    "top_full": ((2, 1), (2, 2)),
}
PROFILE_NAMES = tuple(_PROFILE_SIGNATURES)
_PROFILE_CYCLE = PROFILE_NAMES
_DIFFICULTY_OFFSETS = {None: 0, "easy": 0, "medium": 1, "hard": 2}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware draw over full legal range",
        "valid": "6..9",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware draw over full legal range",
        "valid": "7..10",
    },
    "multiplicity_profile": {
        "type": "str",
        "default": "four-profile sample_index schedule",
        "valid": "block_and_single|crossed|left_full|top_full",
    },
}

# All declared axes are independently compatible.  Declaring the empty tuple
# opts into the strict override-contract policy rather than the legacy warning
# path for unexplained multi-axis rejections.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()


def _validate_request(difficulty, overrides: dict) -> None:
    if difficulty not in _DIFFICULTY_OFFSETS:
        raise ValueError(
            f"unknown difficulty {difficulty!r}; expected easy, medium, hard, or None"
        )
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {sorted(unknown)}")


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the deterministic branch schedule to the semantic census."""
    del seed
    if difficulty not in _DIFFICULTY_OFFSETS:
        raise ValueError(f"unknown difficulty {difficulty!r}")
    offset = _DIFFICULTY_OFFSETS[difficulty]
    return _PROFILE_CYCLE[(int(sample_index) + offset) % len(_PROFILE_CYCLE)]


SCHEDULE_PROFILES = PROFILE_NAMES


def _profile_counts(profile: str) -> tuple[tuple[int, int], tuple[int, int]]:
    """Return role-ordered counts for color A and color B.

    The stored signatures are sorted for observation.  Role order here is
    chosen explicitly so crossed and asymmetric scenes do not depend on color
    magnitude or marker position.
    """
    return {
        "block_and_single": ((2, 2), (1, 1)),
        "crossed": ((2, 1), (1, 2)),
        "left_full": ((2, 2), (1, 2)),
        "top_full": ((2, 2), (2, 1)),
    }[profile]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # Keep the full legal domain valid in every difficulty band.  Difficulty
    # changes the draw distribution, never the accepted override range.
    height = ctx.draw_int_diff("grid_h", 6, 9)
    width = ctx.draw_int_diff("grid_w", 7, 10)
    scheduled = schedule_profile(seed, sample_index, difficulty)
    choices = PROFILE_NAMES if "multiplicity_profile" in overrides else (scheduled,)
    profile = str(ctx.draw_choice("multiplicity_profile", choices))

    colors = tuple(ctx.draw_distinct_colors("marker_colors", n=2, exclude={0}))
    (top_a, left_a), (top_b, left_b) = _profile_counts(profile)
    top_total = top_a + top_b
    left_total = left_a + left_b

    rng = ctx.draw_rng("layout")
    top_columns = rng.sample(range(1, width), top_total)
    left_rows = rng.sample(range(1, height), left_total)
    rng.shuffle(top_columns)
    rng.shuffle(left_rows)

    grid = full_grid(height, width, 0)
    split = top_a
    for column in top_columns[:split]:
        grid[0][column] = colors[0]
    for column in top_columns[split:]:
        grid[0][column] = colors[1]

    split = left_a
    for row in left_rows[:split]:
        grid[row][0] = colors[0]
    for row in left_rows[split:]:
        grid[row][0] = colors[1]
    return grid


def _shape_error(grid) -> str | None:
    if not isinstance(grid, list) or not grid:
        return "grid must be a non-empty list of rows"
    if not isinstance(grid[0], list) or not grid[0]:
        return "grid rows must be non-empty lists"
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return "grid must be rectangular"
    return None


def _border_counts(grid) -> tuple[dict[int, int], dict[int, int]]:
    height, width = len(grid), len(grid[0])
    top: dict[int, int] = {}
    left: dict[int, int] = {}
    for column in range(1, width):
        color = grid[0][column]
        if color != 0:
            top[color] = top.get(color, 0) + 1
    for row in range(1, height):
        color = grid[row][0]
        if color != 0:
            left[color] = left.get(color, 0) + 1
    return top, left


def _multiplicity_signature(grid) -> tuple[tuple[int, int], ...]:
    top, left = _border_counts(grid)
    shared = set(top) & set(left)
    return tuple(sorted((top[color], left[color]) for color in shared))


def _profile_from_grid(grid) -> str:
    signature = _multiplicity_signature(grid)
    for name, expected in _PROFILE_SIGNATURES.items():
        if signature == expected:
            return name
    raise ValueError(f"unrecognized multiplicity signature {signature!r}")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-hiding selector scenes."""
    del difficulty, meta
    shape_error = _shape_error(grid)
    if shape_error:
        return [shape_error]

    errors: list[str] = []
    height, width = len(grid), len(grid[0])
    if not 6 <= height <= 9:
        errors.append(f"height {height} must be in 6..9")
    if not 7 <= width <= 10:
        errors.append(f"width {width} must be in 7..10")

    for row in grid:
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("grid contains a non-integer or ARC color outside 0..9")
                return errors

    if grid[0][0] != 0:
        errors.append("top-left corner must remain background 0")

    interior_noise = [
        (row, column, grid[row][column])
        for row in range(1, height)
        for column in range(1, width)
        if grid[row][column] != 0
    ]
    if interior_noise:
        errors.append(
            "interior must start blank; first nonzero cell is "
            f"{interior_noise[0]}"
        )

    top, left = _border_counts(grid)
    top_colors, left_colors = set(top), set(left)
    if top_colors != left_colors:
        errors.append(
            "top-row and left-column color sets must match exactly; "
            f"top={sorted(top_colors)}, left={sorted(left_colors)}"
        )
    if len(top_colors) != 2 or len(left_colors) != 2:
        errors.append(
            "expected exactly two shared nonzero marker colors, found "
            f"top={len(top_colors)}, left={len(left_colors)}"
        )

    for border_name, counts in (("top", top), ("left", left)):
        for color, count in sorted(counts.items()):
            if count not in (1, 2):
                errors.append(
                    f"{border_name} border color {color} occurs {count} times; "
                    "expected one or two"
                )
        total = sum(counts.values())
        if total not in (3, 4):
            errors.append(
                f"{border_name} border has {total} markers; expected three or four"
            )

    if top_colors == left_colors and len(top_colors) == 2:
        signature = _multiplicity_signature(grid)
        if signature not in set(_PROFILE_SIGNATURES.values()):
            errors.append(
                f"multiplicity signature {signature!r} is outside the teaching profiles"
            )
        intersection_count = sum(top[color] * left[color] for color in top_colors)
        if intersection_count <= len(top_colors):
            errors.append(
                "repeated markers must force more than one intersection per color total"
            )
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared axis exactly from the returned input grid."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "multiplicity_profile": _profile_from_grid(grid),
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror; the canonical Racket rule remains authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("grid is outside the rule domain: " + "; ".join(errors))
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    top, left = _border_counts(grid)
    for color in sorted(set(top) & set(left)):
        rows = [row for row in range(1, height) if grid[row][0] == color]
        columns = [
            column for column in range(1, width) if grid[0][column] == color
        ]
        for row in rows:
            for column in columns:
                output[row][column] = color
    return output


# ---------------------------------------------------------------------------
# Task-linked semantic contract
# ---------------------------------------------------------------------------


def strict_canonical_like(grid) -> list[str]:
    """This generator intentionally emits only the canonical-like manifold."""
    return self_check(grid)


def _witness_profile(name: str) -> Callable[[list[list[int]]], bool]:
    def predicate(grid) -> bool:
        return not self_check(grid) and _profile_from_grid(grid) == name

    return predicate


def _witness_border_erasure(grid) -> bool:
    return not self_check(grid) and any(value != 0 for value in grid[0])


def _witness_two_color_separation(grid) -> bool:
    if self_check(grid):
        return False
    top, left = _border_counts(grid)
    return len(set(top) & set(left)) == 2


SEMANTIC_WITNESSES = {
    "block_and_single_cartesian": _witness_profile("block_and_single"),
    "crossed_multiplicities": _witness_profile("crossed"),
    "left_full_asymmetry": _witness_profile("left_full"),
    "top_full_asymmetry": _witness_profile("top_full"),
    "border_selectors_are_erased": _witness_border_erasure,
    "two_colors_remain_separate": _witness_two_color_separation,
}


def _rival_one_intersection_per_color(grid):
    """Wrong shortcut: use only the first row/column selector for each color."""
    if self_check(grid):
        return None
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    top, left = _border_counts(grid)
    for color in sorted(set(top) & set(left)):
        row = next(r for r in range(1, height) if grid[r][0] == color)
        column = next(c for c in range(1, width) if grid[0][c] == color)
        output[row][column] = color
    return output


def _rival_zip_repeats(grid):
    """Wrong shortcut: zip repeated rows and columns instead of a product."""
    if self_check(grid):
        return None
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    top, left = _border_counts(grid)
    for color in sorted(set(top) & set(left)):
        rows = [r for r in range(1, height) if grid[r][0] == color]
        columns = [c for c in range(1, width) if grid[0][c] == color]
        for row, column in zip(rows, columns):
            output[row][column] = color
    return output


def _rival_preserve_border_markers(grid):
    """Wrong shortcut inherited from the old summary: keep source markers."""
    if self_check(grid):
        return None
    output = copy.deepcopy(grid)
    canonical = rule_mirror(grid)
    for row in range(len(grid)):
        for column in range(len(grid[0])):
            if canonical[row][column] != 0:
                output[row][column] = canonical[row][column]
    return output


def _rival_modal_color_echo(grid):
    """Wrong color-blind rule: paint all selected crossings one color."""
    if self_check(grid):
        return None
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    top, left = _border_counts(grid)
    color = min(set(top) & set(left))
    rows = [row for row in range(1, height) if grid[row][0] != 0]
    columns = [column for column in range(1, width) if grid[0][column] != 0]
    for row in rows:
        for column in columns:
            output[row][column] = color
    return output


def _rival_copy_top_color(grid):
    """Wrong relation: every selected row accepts every top-column color."""
    if self_check(grid):
        return None
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    rows = [row for row in range(1, height) if grid[row][0] != 0]
    columns = [column for column in range(1, width) if grid[0][column] != 0]
    for row in rows:
        for column in columns:
            output[row][column] = grid[0][column]
    return output


SEMANTIC_RIVALS = {
    "one_intersection_per_color": _rival_one_intersection_per_color,
    "zip_repeated_markers": _rival_zip_repeats,
    "preserve_border_markers": _rival_preserve_border_markers,
    "modal_color_echo": _rival_modal_color_echo,
    "ignore_left_marker_color": _rival_copy_top_color,
}

WITNESS_RIVALS = {
    "block_and_single_cartesian": [
        "one_intersection_per_color",
        "zip_repeated_markers",
    ],
    "crossed_multiplicities": [
        "one_intersection_per_color",
        "zip_repeated_markers",
    ],
    "left_full_asymmetry": [
        "one_intersection_per_color",
        "zip_repeated_markers",
    ],
    "top_full_asymmetry": [
        "one_intersection_per_color",
        "zip_repeated_markers",
    ],
    "border_selectors_are_erased": ["preserve_border_markers"],
    "two_colors_remain_separate": [
        "modal_color_echo",
        "ignore_left_marker_color",
    ],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons under which a named plausible wrong rule survives."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the rule domain: {exc}")
            continue
        if expected != demo.get("output"):
            reasons.append(
                f"demo {index} output does not match the border Cartesian-product rule"
            )

    try:
        query_answer = rule_mirror(query["input"])
    except (KeyError, TypeError, ValueError) as exc:
        reasons.append(f"query is outside the rule domain: {exc}")
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo.get("output") for demo in demos
        )
        competitor_answer = competitor(query["input"])
        if survives and competitor_answer != query_answer:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
        elif survives:
            reasons.append(
                f"competing rule {name!r} is answer-equivalent across the whole lesson"
            )
    return reasons


def mutation_fixtures():
    """Named malformed scenes, including the pre-repair shortcut distribution."""
    valid = generate(
        7011,
        0,
        difficulty="easy",
        grid_h=7,
        grid_w=8,
        multiplicity_profile="block_and_single",
    )
    fixtures: list[tuple[str, list[list[int]]]] = []

    # Regression witness: v2 generated one marker per color on each border,
    # making Cartesian product indistinguishable from one-cell pairing.
    one_each = full_grid(7, 8, 0)
    one_each[0][2] = 2
    one_each[0][5] = 3
    one_each[2][0] = 2
    one_each[5][0] = 3
    fixtures.append(("pre_repair_one_marker_per_color", one_each))

    unmatched = copy.deepcopy(valid)
    used_colors = {value for row in unmatched for value in row if value != 0}
    replaced_color = next(color for color in range(1, 10) if color not in used_colors)
    first_top = next(c for c in range(1, len(unmatched[0])) if unmatched[0][c])
    unmatched[0][first_top] = replaced_color
    fixtures.append(("unmatched_border_color", unmatched))

    interior_noise = copy.deepcopy(valid)
    interior_noise[2][2] = 9
    fixtures.append(("interior_already_painted", interior_noise))

    nonzero_corner = copy.deepcopy(valid)
    nonzero_corner[0][0] = 4
    fixtures.append(("nonzero_corner", nonzero_corner))

    triple_repeat = copy.deepcopy(valid)
    top_counts, _ = _border_counts(triple_repeat)
    repeated = max(top_counts, key=top_counts.get)
    free_column = next(
        c for c in range(1, len(triple_repeat[0])) if triple_repeat[0][c] == 0
    )
    triple_repeat[0][free_column] = repeated
    fixtures.append(("three_same_color_top_markers", triple_repeat))

    third_color = copy.deepcopy(valid)
    free_column = next(
        c for c in range(1, len(third_color[0])) if third_color[0][c] == 0
    )
    free_row = next(r for r in range(1, len(third_color)) if third_color[r][0] == 0)
    used = {value for row in third_color for value in row}
    new_color = next(color for color in range(1, 10) if color not in used)
    third_color[0][free_column] = new_color
    third_color[free_row][0] = new_color
    fixtures.append(("third_shared_color", third_color))

    missing_left = copy.deepcopy(valid)
    for row in range(1, len(missing_left)):
        missing_left[row][0] = 0
    fixtures.append(("missing_left_selectors", missing_left))

    ragged = copy.deepcopy(valid)
    ragged[-1] = ragged[-1][:-1]
    fixtures.append(("ragged_grid", ragged))

    bad_color = copy.deepcopy(valid)
    bad_color[0][1] = 12
    fixtures.append(("color_outside_arc_palette", bad_color))
    return fixtures
