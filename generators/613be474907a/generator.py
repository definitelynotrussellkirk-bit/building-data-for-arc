"""Semantic generator for ARC task 613be474907a (source puzzle d968ffd4).

The modal color is background and the other two colors define two blocks.
When their bounding boxes are separated horizontally, each block extends
toward the other through half of the intervening columns, across the full
canvas height.  When they are separated vertically, the analogous extensions
fill complete rows.  An odd gap leaves its single middle line unchanged.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "613be474907a"
TASK_ID = "613be474907a"
VERSION = "3.0.0"
RULE_HASH = "adc52fde010d"
SUMMARY = "Extend two separated colored blocks toward one another by floor(half the gap), filling complete perpendicular lines and preserving an odd middle line."
INVARIANTS = [
    "the strict modal color is background and exactly two other colors are present",
    "each foreground color forms one solid rectangular block",
    "the two block bounding boxes are separated by at least three rows or columns",
    "horizontal separation takes precedence exactly as in the canonical rule",
    "each side fills floor(gap/2) complete perpendicular lines in its own color",
    "an even gap is completely bridged and an odd gap preserves exactly its middle background line",
    "all original block cells and all cells outside the intervening gap are preserved",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4", "public_5")
GENERAL_PROFILES = (
    "horizontal_left_even",
    "horizontal_left_odd",
    "horizontal_right_even",
    "horizontal_right_odd",
    "vertical_top_even",
    "vertical_top_odd",
    "vertical_bottom_even",
    "vertical_bottom_odd",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five exact-public and eight direction/parity bridge lessons",
        "valid": "public_1|public_2|public_3|public_4|public_5|horizontal_left_even|horizontal_left_odd|horizontal_right_even|horizontal_right_odd|vertical_top_even|vertical_top_odd|vertical_bottom_even|vertical_bottom_odd",
    }
}

_PUBLIC_ROWS = (
    "4444444444444444/4114444444444664/4114444444444664/4114444444444664/4444444444444444",
    "22222222222222222/21122222222222332/21122222222222332/22222222222222222",
    "888/828/828/888/888/888/888/888/888/888/888/888/888/888/888/888/818/818/888",
    "222/282/282/222/222/222/222/222/222/222/222/222/222/222/222/222/222/222/222/212/212/222",
    "333333/388883/388883/333333/333333/333333/333333/333333/333333/333333/333333/333333/333333/333333/322223/322223/333333",
)


def _decode(text):
    return [[int(value) for value in row] for row in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 3 <= len(grid) <= 30:
        return ["input must contain three through thirty rows"]
    if not isinstance(grid[0], (list, tuple)) or not 3 <= len(grid[0]) <= 30:
        return ["input must contain three through thirty columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        return ["input cells must be literal ARC color integers from zero through nine"]
    return []


def _bbox(grid, color):
    cells = [(row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value == color]
    if not cells:
        return None
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def _solid_rectangle(grid, color, box):
    row0, col0, row1, col1 = box
    cells = {(row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value == color}
    return cells == {(row, col) for row in range(row0, row1 + 1) for col in range(col0, col1 + 1)}


def _geometry_signature(grid):
    counts = Counter(value for row in grid for value in row)
    if len(counts) != 3:
        return None
    background = counts.most_common(1)[0][0]
    boxes = tuple(sorted(_bbox(grid, color) for color in counts if color != background))
    return len(grid), len(grid[0]), boxes


_PUBLIC_GEOMETRIES = {_geometry_signature(grid): name for name, grid in _PUBLIC_INPUTS.items()}


def _branch_facts(grid):
    flat = [value for row in grid for value in row]
    counts = Counter(flat)
    ordered = counts.most_common()
    if len(counts) != 3:
        return None, [f"expected exactly three colors, got {len(counts)}"]
    if len(ordered) < 2 or ordered[0][1] == ordered[1][1]:
        return None, ["background must be the unique modal color"]
    background = ordered[0][0]
    colors = sorted(color for color in counts if color != background)
    if len(colors) != 2:
        return None, ["expected exactly two non-background colors"]
    color1, color2 = colors
    box1, box2 = _bbox(grid, color1), _bbox(grid, color2)
    errors = []
    if not _solid_rectangle(grid, color1, box1) or not _solid_rectangle(grid, color2, box2):
        errors.append("each foreground color must form one solid rectangle")
    r10, c10, r11, c11 = box1
    r20, c20, r21, c21 = box2
    if c11 < c20:
        orientation, side, near_color, far_color = "horizontal", "left", color1, color2
        gap_start, gap_end = c11 + 1, c20 - 1
    elif c21 < c10:
        orientation, side, near_color, far_color = "horizontal", "right", color2, color1
        gap_start, gap_end = c21 + 1, c10 - 1
    elif r11 < r20:
        orientation, side, near_color, far_color = "vertical", "top", color1, color2
        gap_start, gap_end = r11 + 1, r20 - 1
    elif r21 < r10:
        orientation, side, near_color, far_color = "vertical", "bottom", color2, color1
        gap_start, gap_end = r21 + 1, r10 - 1
    else:
        return None, errors + ["foreground bounding boxes must be separated on at least one axis"]
    gap = gap_end - gap_start + 1
    if gap < 3:
        errors.append(f"intervening gap must contain at least three lines, got {gap}")
    facts = {
        "background": background,
        "colors": tuple(colors),
        "boxes": (box1, box2),
        "orientation": orientation,
        "side": side,
        "near_color": near_color,
        "far_color": far_color,
        "gap_start": gap_start,
        "gap_end": gap_end,
        "gap": gap,
        "parity": "even" if gap % 2 == 0 else "odd",
    }
    return facts, errors


def rule_mirror(grid):
    """Exact Python mirror of the canonical sorted-color/bounding-box rule."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    facts, errors = _branch_facts(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [list(row) for row in grid]
    half = facts["gap"] // 2
    if facts["orientation"] == "horizontal":
        for row in range(len(grid)):
            for col in range(facts["gap_start"], facts["gap_start"] + half):
                output[row][col] = facts["near_color"]
            for col in range(facts["gap_end"] - half + 1, facts["gap_end"] + 1):
                output[row][col] = facts["far_color"]
    else:
        for row in range(facts["gap_start"], facts["gap_start"] + half):
            output[row] = [facts["near_color"]] * len(grid[0])
        for row in range(facts["gap_end"] - half + 1, facts["gap_end"] + 1):
            output[row] = [facts["far_color"]] * len(grid[0])
    return output


def _profile_for(grid, facts):
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if public:
        return public
    public_family = _PUBLIC_GEOMETRIES.get(_geometry_signature(grid))
    if public_family:
        return public_family
    candidate = f'{facts["orientation"]}_{facts["side"]}_{facts["parity"]}'
    return candidate if candidate in GENERAL_PROFILES else None


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "facts": None, "scene_profile": None, "output": None}
    facts, branch_errors = _branch_facts(grid)
    errors.extend(branch_errors)
    if facts is None:
        return {"errors": errors, "facts": None, "scene_profile": None, "output": None}
    profile = _profile_for(grid, facts)
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared direction/parity profile")
    output = None
    if not errors:
        output = rule_mirror(grid)
        changed = sum(before != after for in_row, out_row in zip(grid, output) for before, after in zip(in_row, out_row))
        expected = 2 * (facts["gap"] // 2) * (len(grid) if facts["orientation"] == "horizontal" else len(grid[0]))
        if changed != expected:
            errors.append(f"bridge must change exactly {expected} cells, got {changed}")
        if changed == 0:
            errors.append("every accepted lesson must visibly change")
        facts = {**facts, "changed": changed}
    return {"errors": errors, "facts": facts, "scene_profile": profile, "output": output}


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def canonical_family_signature(grid):
    return _PUBLIC_GEOMETRIES.get(_geometry_signature(grid))


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _limits(difficulty):
    if difficulty == "easy":
        return (12, 18), (4, 7)
    if difficulty == "medium":
        return (15, 24), (4, 10)
    if difficulty == "hard":
        return (18, 30), (5, 14)
    return (14, 26), (4, 12)


def _interval_containing(extent, pivot, rng):
    maximum = min(5, extent - 2)
    length = rng.randint(1, maximum)
    lo = max(1, pivot - length + 1)
    hi = min(pivot, extent - length - 1)
    start = rng.randint(lo, hi)
    return start, start + length - 1


def _general_scene(profile, difficulty, rng):
    orientation, side, parity = profile.split("_")
    long_limits, cross_limits = _limits(difficulty)
    long_extent = rng.randint(*long_limits)
    cross_extent = rng.randint(*cross_limits)
    if orientation == "horizontal":
        height, width = cross_extent, long_extent
    else:
        height, width = long_extent, cross_extent
    palette = rng.sample(range(10), 3)
    background = palette[0]
    color1, color2 = sorted(palette[1:])
    grid = [[background] * width for _ in range(height)]

    maximum_gap = long_extent - 4
    candidates = [gap for gap in range(3, maximum_gap + 1) if (gap % 2 == 0) == (parity == "even")]
    gap = rng.choice(candidates)
    available = long_extent - gap - 2
    first_length = rng.randint(1, min(4, available - 1))
    second_length = rng.randint(1, min(4, available - first_length))
    free = long_extent - gap - first_length - second_length
    before = rng.randint(0, free)
    first_start = before
    second_start = first_start + first_length + gap
    pivot = rng.randint(1, cross_extent - 2)
    cross_a = _interval_containing(cross_extent, pivot, rng)
    cross_b = _interval_containing(cross_extent, pivot, rng)

    near_color, far_color = (color1, color2) if side in ("left", "top") else (color2, color1)
    if orientation == "horizontal":
        for row in range(cross_a[0], cross_a[1] + 1):
            for col in range(first_start, first_start + first_length):
                grid[row][col] = near_color
        for row in range(cross_b[0], cross_b[1] + 1):
            for col in range(second_start, second_start + second_length):
                grid[row][col] = far_color
    else:
        for row in range(first_start, first_start + first_length):
            for col in range(cross_a[0], cross_a[1] + 1):
                grid[row][col] = near_color
        for row in range(second_start, second_start + second_length):
            for col in range(cross_b[0], cross_b[1] + 1):
                grid[row][col] = far_color
    return grid


def _public_nuisance(profile, rng):
    grid = _PUBLIC_INPUTS[profile]
    counts = Counter(value for row in grid for value in row)
    old_background = counts.most_common(1)[0][0]
    old_colors = sorted(color for color in counts if color != old_background)
    new_background, new_first, new_second = rng.sample(range(10), 3)
    mapping = {
        old_background: new_background,
        old_colors[0]: new_first,
        old_colors[1]: new_second,
    }
    return [[mapping[value] for value in row] for row in grid]


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
    profile = ctx.draw_choice("scene_profile", PUBLIC_PROFILES * 3 + GENERAL_PROFILES * 5)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        if overrides.get("scene_profile") is not None:
            return [row[:] for row in _PUBLIC_INPUTS[profile]]
        grid = _public_nuisance(profile, ctx.draw_rng("public_palette"))
        errors = self_check(grid)
        if errors:
            raise AssertionError("generated invalid canonical-family lesson: " + "; ".join(errors))
        return grid
    grid = _general_scene(profile, difficulty, ctx.draw_rng("scene"))
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid bridge lesson: " + "; ".join(errors))
    return grid
