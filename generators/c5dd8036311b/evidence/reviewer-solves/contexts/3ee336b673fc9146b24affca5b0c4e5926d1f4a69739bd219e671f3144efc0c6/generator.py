"""Semantic generator for ARC task c5dd8036311b (source 72a961c9).

The input contains a horizontal color-1 bar with color-2 and color-8
markers.  Each marker grows a column upward from the bar: color 8 creates a
three-cell column above the bar, while color 2 creates a four-cell column.
The marker color occupies the top of its column and every lower added cell is
color 1.  All pre-existing cells, including the marked bar, are preserved.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from math import comb

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "c5dd8036311b"
TASK_ID = "c5dd8036311b"
VERSION = "2.0.0"
RULE_HASH = "fd929da87d08"
SUMMARY = "Grow marker-tipped color-1 columns upward from a marked horizontal bar: height three for color 8 and four for color 2."
INVARIANTS = [
    "the calibrated input contains one horizontal bar made only of colors 1, 2, and 8",
    "every color-8 marker adds three cells immediately above its bar position",
    "every color-2 marker adds four cells immediately above its bar position",
    "the top added cell repeats the marker color and all lower added cells are color 1",
    "the marked bar and every cell outside the added columns remain unchanged",
    "calibrated scenes leave enough room above the bar for every column to be complete",
]

PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(1, 6))
GENERAL_PROFILES = (
    "double_8",
    "double_2",
    "triple_8",
    "triple_2",
    "four_8",
    "four_2",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five official marker-multiset families plus six same-height contrasts",
        "valid": "public_1|public_2|public_3|public_4|public_5|double_8|double_2|triple_8|triple_2|four_8|four_2",
    }
}

# Profiles are deliberately observable from the returned grid.  The five
# official families retain the exact (number of color-2 markers, number of
# color-8 markers) signatures seen in the canonical examples.
PROFILE_COUNTS = {
    "public_1": (0, 1),
    "public_2": (1, 0),
    "public_3": (1, 2),
    "public_4": (1, 1),
    "public_5": (2, 2),
    "double_8": (0, 2),
    "double_2": (2, 0),
    "triple_8": (0, 3),
    "triple_2": (3, 0),
    "four_8": (0, 4),
    "four_2": (4, 0),
}
COUNTS_PROFILE = {counts: profile for profile, counts in PROFILE_COUNTS.items()}
if len(COUNTS_PROFILE) != len(PROFILE_COUNTS):
    raise AssertionError("scene profiles must have distinct marker multisets")

_PUBLIC_ROWS = {
    "public_1": (
        "000000", "000000", "000000", "181111", "000000",
        "000000", "000000", "000000", "000000",
    ),
    "public_2": (
        "0000000", "0000000", "0000000", "0000000", "0000000",
        "1112111", "0000000", "0000000", "0000000", "0000000",
    ),
    "public_3": (
        "000000000", "000000000", "000000000", "000000000",
        "000000000", "000000000", "000000000", "181118121",
        "000000000",
    ),
    "public_4": (
        "0000000000", "0000000000", "0000000000", "0000000000",
        "0000000000", "0000000000", "0000000000", "0000000000",
        "0000000000", "1121118111", "0000000000", "0000000000",
        "0000000000",
    ),
    "public_5": (
        "00000000000", "00000000000", "00000000000", "00000000000",
        "00000000000", "00000000000", "12181118121", "00000000000",
        "00000000000",
    ),
}
_PUBLIC_INPUTS = {
    profile: [[int(value) for value in row] for row in rows]
    for profile, rows in _PUBLIC_ROWS.items()
}
_PUBLIC_EXACT = {
    tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()
}

# Difficulty is expressed only through geometry.  Disjoint height sets also
# prevent cross-band duplicate pairs in the shared 4,000-draw health schedule.
_HEIGHTS = {
    None: (10,),
    "easy": (8, 9),
    "medium": (11, 12),
    "hard": (13, 14),
}
_WIDTHS = tuple(range(6, 17))


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 1 <= len(grid) <= 30:
        return ["input must contain one through thirty rows"]
    if not isinstance(grid[0], (list, tuple)) or not 1 <= len(grid[0]) <= 30:
        return ["input must contain one through thirty columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["input cells must be literal ARC color integers from zero through nine"]
    return []


def _first_bar_row(grid):
    for row, values in enumerate(grid):
        if any(value == 1 for value in values):
            return row
    raise ValueError("upward-column rule requires a row containing color 1")


def _rule_facts(grid):
    bar_row = _first_bar_row(grid)
    markers = tuple(
        (col, value)
        for col, value in enumerate(grid[bar_row])
        if value not in (0, 1)
    )
    return {
        "bar_row": bar_row,
        "markers": markers,
        "marker_counts": (
            sum(value == 2 for _, value in markers),
            sum(value == 8 for _, value in markers),
        ),
    }


def rule_mirror(grid):
    """Broad, input-pure mirror of the canonical Racket rule."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    facts = _rule_facts(grid)
    output = [list(row) for row in grid]
    for col, color in facts["markers"]:
        height = 3 if color == 8 else 4
        start_row = facts["bar_row"] - height
        for offset in range(height):
            row = start_row + offset
            if 0 <= row < facts["bar_row"]:
                output[row][col] = color if offset == 0 else 1
    return output


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": {}, "output": None}
    height, width = len(grid), len(grid[0])
    if not 8 <= height <= 14:
        errors.append("calibrated scenes must contain eight through fourteen rows")
    if not 6 <= width <= 16:
        errors.append("calibrated scenes must contain six through sixteen columns")
    try:
        facts = _rule_facts(grid)
    except ValueError as exc:
        errors.append(str(exc))
        return {"errors": errors, "scene_profile": None, "facts": {}, "output": None}
    bar_row = facts["bar_row"]
    markers = facts["markers"]
    rows_with_one = [
        row for row, values in enumerate(grid) if any(value == 1 for value in values)
    ]
    if rows_with_one != [bar_row]:
        errors.append("calibrated input must contain color 1 only in its single bar row")
    if not 3 <= bar_row <= height - 2:
        errors.append("bar row must leave at least three rows above and one row below")
    if any(value not in (1, 2, 8) for value in grid[bar_row]):
        errors.append("bar row may contain only colors 1, 2, and 8")
    if not any(value == 1 for value in grid[bar_row]):
        errors.append("bar row must retain at least one color-1 cell")
    if any(
        value != 0
        for row, values in enumerate(grid) if row != bar_row
        for value in values
    ):
        errors.append("all calibrated input cells outside the bar must be zero")
    if not 1 <= len(markers) <= 4:
        errors.append("bar row must contain one through four markers")
    if any(value not in (2, 8) for _, value in markers):
        errors.append("calibrated markers must use only colors 2 and 8")
    if any(value == 2 for _, value in markers) and bar_row < 4:
        errors.append("color-2 markers require four complete rows above the bar")
    profile = COUNTS_PROFILE.get(facts["marker_counts"])
    if profile is None:
        errors.append("marker multiset does not match a declared semantic profile")
    output = rule_mirror(grid)
    changed = sum(
        before != after
        for before_row, after_row in zip(grid, output)
        for before, after in zip(before_row, after_row)
    )
    expected_changed = sum(3 if value == 8 else 4 for _, value in markers)
    if changed != expected_changed:
        errors.append(
            f"complete marker columns should change {expected_changed} cells, found {changed}"
        )
    facts = dict(facts)
    facts.update({
        "height": height,
        "width": width,
        "changed": changed,
        "marker_columns": tuple(col for col, _ in markers),
        "rows_below": height - bar_row - 1,
    })
    return {"errors": errors, "scene_profile": profile, "facts": facts, "output": output}


def canonical_profile_signature(grid):
    try:
        return _PUBLIC_EXACT.get(tuple(tuple(row) for row in grid))
    except TypeError:
        return None


def canonical_family_signature(grid):
    analysis = _analysis(grid)
    profile = analysis["scene_profile"]
    return profile if profile in PUBLIC_PROFILES and not analysis["errors"] else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return _analysis(grid)["errors"]


@lru_cache(maxsize=None)
def _state_count(profile, difficulty):
    n2, n8 = PROFILE_COUNTS[profile]
    marker_count = n2 + n8
    assignments = comb(marker_count, n2)
    return sum(
        comb(width, marker_count) * assignments
        for height in _HEIGHTS[difficulty]
        for bar_row in range(4, height - 1)
        for width in _WIDTHS
    )


def _construct_scene(profile, difficulty, uniqueness_index):
    n2, n8 = PROFILE_COUNTS[profile]
    marker_count = n2 + n8
    color_assignments = tuple(combinations(range(marker_count), n2))
    state_index = uniqueness_index % _state_count(profile, difficulty)
    for height in _HEIGHTS[difficulty]:
        for bar_row in range(4, height - 1):
            for width in _WIDTHS:
                column_choices = tuple(combinations(range(width), marker_count))
                block = len(column_choices) * len(color_assignments)
                if state_index >= block:
                    state_index -= block
                    continue
                columns = column_choices[state_index // len(color_assignments)]
                twos = set(color_assignments[state_index % len(color_assignments)])
                grid = [[0] * width for _ in range(height)]
                grid[bar_row] = [1] * width
                for position, col in enumerate(columns):
                    grid[bar_row][col] = 2 if position in twos else 8
                return grid
    raise AssertionError("profile state index did not resolve")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - {"scene_profile"}
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
    band_index = {None: 0, "easy": 1, "medium": 2, "hard": 3}[difficulty]
    schedule_index = 19 * seed - 18 * sample_index + 10_000 * band_index
    if overrides.get("scene_profile") is not None:
        profile = ctx.draw_choice("scene_profile", list(SCENE_PROFILES))
        uniqueness_index = schedule_index
    else:
        # Cycle profiles exactly instead of allowing birthday collisions in
        # small one-marker families.  The quotient is that profile's unique
        # occurrence rank, so a 5k census visits 454/455 distinct states per
        # profile rather than hashing 5k draws into a finite state space.
        scheduled_profile = SCENE_PROFILES[schedule_index % len(SCENE_PROFILES)]
        profile = ctx.draw_choice("scene_profile", [scheduled_profile])
        uniqueness_index = schedule_index // len(SCENE_PROFILES)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if overrides.get("scene_profile") is not None and profile in PUBLIC_PROFILES:
        grid = [row[:] for row in _PUBLIC_INPUTS[profile]]
    else:
        grid = _construct_scene(profile, difficulty, uniqueness_index)
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid upward-column lesson: " + "; ".join(errors))
    return grid
