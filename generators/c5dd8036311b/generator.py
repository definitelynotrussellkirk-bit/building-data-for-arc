"""Semantic generator for ARC task c5dd8036311b (source 72a961c9).

The input contains a horizontal color-1 bar with color-2 and color-8
markers.  Each marker grows a column upward from the bar: color 8 creates a
three-cell column above the bar, while color 2 creates a four-cell column.
The marker color occupies the top of its column and every lower added cell is
color 1.  All pre-existing cells, including the marked bar, are preserved.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "c5dd8036311b"
TASK_ID = "c5dd8036311b"
VERSION = "2.1.0"
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
    "teaching_5",
    "teaching_7",
    "balanced_8",
    "six_mixed",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "alternating rich counterexamples and varied marker-multiset families",
        "valid": "public_1|public_2|public_3|public_4|public_5|double_8|double_2|triple_8|triple_2|four_8|four_2|teaching_5|teaching_7|balanced_8|six_mixed",
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
    "teaching_5": (3, 2),
    "teaching_7": (4, 3),
    "balanced_8": (4, 4),
    "six_mixed": (4, 2),
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

# Difficulty is a geometry hint, not a disjoint shape partition: every band
# must still include canonical-scale anchors. The teaching schedule is parity
# only; coordinates, color order, and dimensions vary independently.
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.95
_TEACHING_PROFILES = ("teaching_5", "teaching_7", "six_mixed")
_VARIATION_PROFILES = tuple(p for p in SCENE_PROFILES if p not in _TEACHING_PROFILES)
SCHEDULE_PROFILES = SCENE_PROFILES
LESSON_SCHEDULE_PERIOD = 2 * len(_VARIATION_PROFILES)


def schedule_profile(seed, sample_index, difficulty=None):
    del difficulty
    rank = (seed + sample_index) // 2
    profiles = _TEACHING_PROFILES if (seed + sample_index) % 2 == 0 else _VARIATION_PROFILES
    return profiles[(seed + rank) % len(profiles)]


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
    if not 8 <= height <= 30:
        errors.append("calibrated scenes must contain eight through thirty rows")
    if not 6 <= width <= 30:
        errors.append("calibrated scenes must contain six through thirty columns")
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
    if not 1 <= len(markers) <= 8:
        errors.append("bar row must contain one through eight markers")
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


def strict_canonical_like(grid):
    """The declared full-column task manifold, including lawful large scenes."""
    return self_check(grid)


def _rival(grid, mode):
    """Task-local counter-hypotheses; Racket remains the label authority."""
    facts = _rule_facts(grid)
    bar_row, markers = facts["bar_row"], facts["markers"]
    marker_cols = {col for col, _ in markers}
    counts = {2: 0, 8: 0}
    out = [list(row) for row in grid]
    for index, (col, color) in enumerate(markers):
        if mode == "ignore_boundary_markers" and col in (0, len(grid[0]) - 1):
            continue
        if mode == "ignore_adjacent_markers" and ({col - 1, col + 1} & marker_cols):
            continue
        if mode == "cap_four_markers" and index >= 4:
            continue
        counts[color] = counts.get(color, 0) + 1
        if mode == "cap_two_per_color" and counts[color] > 2:
            continue
        height = 3 if color == 8 else 4
        n2, n8 = facts["marker_counts"]
        if mode == "minority_8_uses_height4" and color == 8 and n2 > n8:
            height = 4
        for offset in range(height):
            row = bar_row - height + offset
            if 0 <= row < bar_row:
                out[row][col] = color if offset == 0 else 1
    return out


def _ignore_boundary_markers(grid):
    return _rival(grid, "ignore_boundary_markers")


def _ignore_adjacent_markers(grid):
    return _rival(grid, "ignore_adjacent_markers")


def _cap_four_markers(grid):
    return _rival(grid, "cap_four_markers")


def _cap_two_per_color(grid):
    return _rival(grid, "cap_two_per_color")


def _minority_8_uses_height4(grid):
    return _rival(grid, "minority_8_uses_height4")


def _boundary_marker(grid):
    cols = {col for col, _ in _rule_facts(grid)["markers"]}
    return bool(cols & {0, len(grid[0]) - 1})


def _adjacent_markers(grid):
    cols = {col for col, _ in _rule_facts(grid)["markers"]}
    return any(col + 1 in cols for col in cols)


def _many_markers(grid):
    return len(_rule_facts(grid)["markers"]) > 4


def _many_one_color(grid):
    return max(_rule_facts(grid)["marker_counts"]) > 2


def _minority_8(grid):
    n2, n8 = _rule_facts(grid)["marker_counts"]
    return n2 > n8 > 0


CANONICAL_SHORTCUTS = {
    "ignore_boundary_markers": _ignore_boundary_markers,
    "ignore_adjacent_markers": _ignore_adjacent_markers,
    "cap_four_markers": _cap_four_markers,
    "cap_two_per_color": _cap_two_per_color,
    "minority_8_uses_height4": _minority_8_uses_height4,
}
SEMANTIC_RIVALS = dict(CANONICAL_SHORTCUTS)
LESSON_COMPETITORS = dict(CANONICAL_SHORTCUTS)
SEMANTIC_WITNESSES = {
    "boundary_marker": _boundary_marker,
    "adjacent_markers": _adjacent_markers,
    "more_than_four_markers": _many_markers,
    "more_than_two_of_one_color": _many_one_color,
    "minority_8": _minority_8,
}
WITNESS_RIVALS = {
    "boundary_marker": ["ignore_boundary_markers"],
    "adjacent_markers": ["ignore_adjacent_markers"],
    "more_than_four_markers": ["cap_four_markers"],
    "more_than_two_of_one_color": ["cap_two_per_color"],
    "minority_8": ["minority_8_uses_height4"],
}


def lesson_identifiable(demos, query):
    """Check color coverage and the declared finite rivals, not all hypotheses."""
    reasons = []
    seen = {color for pair in demos for _, color in _rule_facts(pair["input"])["markers"]}
    needed = {color for _, color in _rule_facts(query["input"])["markers"]}
    if needed - seen:
        reasons.append("query marker colors lack a demonstrated height: " + str(sorted(needed - seen)))
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append("unrefuted query-changing rival: " + name)
    return reasons


def _draw_scene(ctx, profile, *, teaching):
    n2, n8 = PROFILE_COUNTS[profile]
    count = n2 + n8
    rng = ctx.draw_rng("geometry:" + str(ctx.difficulty))
    # Fifty percent canonical profile shapes. The remaining mass gives broad
    # rectangles and large scenes without displacing the canonical anchors.
    lane = rng.randrange(10)
    if lane < 5:
        shapes = ((9, 9), (9, 11), (13, 10)) if n2 and n8 else ((9, 6), (10, 7))
        height, width = rng.choice(shapes)
    elif lane < 7:
        lo, hi = {None: (8, 20), "easy": (8, 14), "medium": (11, 23), "hard": (18, 30)}[ctx.difficulty]
        height, width = rng.randint(lo, hi), rng.randint(max(6, count + 1), 30)
    elif lane < 9:
        height, width = rng.randint(21, 30), rng.randint(max(6, count + 1), 30)
    else:
        height, width = 30, 30
    width = max(width, count + 1)
    bar_row = rng.randint(4 if n2 else 3, height - 2)
    layout = ctx.draw_rng("marker_layout:" + str(ctx.difficulty))
    if teaching:
        # An adjacent pair at either edge refutes both positional shortcuts;
        # the remaining positions and all color assignments are unconstrained.
        forced = (0, 1) if layout.randrange(2) == 0 else (width - 2, width - 1)
        columns = list(forced) + layout.sample([c for c in range(width) if c not in forced], count - 2)
    else:
        columns = layout.sample(range(width), count)
    colors = [2] * n2 + [8] * n8
    layout.shuffle(colors)
    grid = [[0] * width for _ in range(height)]
    grid[bar_row] = [1] * width
    for col, color in zip(columns, colors):
        grid[bar_row][col] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise ValueError("seed must be a literal integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative literal integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    forced = overrides.get("scene_profile") is not None
    scheduled = schedule_profile(seed, sample_index, difficulty)
    teaching = not forced and scheduled in _TEACHING_PROFILES
    # Every four consecutive draws have four distinct marker multisets: the
    # two teaching profiles differ, the two variation profiles differ, and
    # their profile sets are disjoint. Thus within-lesson deduplication cannot
    # skip a witness in the declared three-demo/one-query assembly.
    options = list(SCENE_PROFILES) if forced else [scheduled]
    profile = ctx.draw_choice("scene_profile", options)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if forced and profile in PUBLIC_PROFILES:
        grid = [row[:] for row in _PUBLIC_INPUTS[profile]]
    else:
        grid = _draw_scene(ctx, profile, teaching=teaching)
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid upward-column lesson: " + "; ".join(errors))
    return grid
