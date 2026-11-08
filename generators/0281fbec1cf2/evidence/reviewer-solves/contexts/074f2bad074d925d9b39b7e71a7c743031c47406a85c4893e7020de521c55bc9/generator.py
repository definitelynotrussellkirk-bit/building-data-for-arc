"""Semantic generator for ARC task 0281fbec1cf2.

A solid red rectangle emits red rays independently from each of its rows and
columns.  Any nonzero non-red cell aligned beyond one side blocks only that
lane and direction; markers elsewhere are inert and every original nonzero
cell is preserved.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "0281fbec1cf2"
TASK_ID = "0281fbec1cf2"
VERSION = "3.0.0"
RULE_HASH = "0c0061f8ed33"
SUMMARY = "Extend each red-rectangle row and column outward in every unblocked direction; aligned nonzero non-red markers block one direction only."
INVARIANTS = [
    "literal color 2 forms one solid interior rectangle and literal 0 is background",
    "every nonzero non-2 cell is a potential directional blocker",
    "a marker above or below blocks only that column and direction",
    "a marker left or right blocks only that row and direction",
    "markers outside both rectangle coordinate bands are inert",
    "unblocked rays paint only zero cells red and all original nonzero cells survive",
]

PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(1, 5))
GENERAL_PROFILES = (
    "open_with_decoys",
    "up_only",
    "down_only",
    "left_only",
    "right_only",
    "same_col_opposites",
    "split_col_opposites",
    "same_row_opposites",
    "split_row_opposites",
    "mixed_colors_four_sides",
    "aligned_with_decoys",
    "dense_four_sides",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four exact-public and twelve directional-blocking lessons",
        "valid": "public_1|public_2|public_3|public_4|open_with_decoys|up_only|down_only|left_only|right_only|same_col_opposites|split_col_opposites|same_row_opposites|split_row_opposites|mixed_colors_four_sides|aligned_with_decoys|dense_four_sides",
    }
}

_PUBLIC_ROWS = (
    "000000000000000/000030003000000/000000000000000/000000300000000/000000000000000/000022222000300/000022222000000/030022222000000/000022222000030/000022222000000/000000000000000/000000000000000/000000000000000/000000003000000/000000000000000/000000000000000/000003000000000/000000000000000/000000000000000/000000000000000",
    "0000000000000000000000000/0022222222000000000008000/0022222222000000000800000/0022222222000000000000000/0022222222000008000000000/0022222222000000000000000/0022222222000000000000000/0022222222000000008000000/0022222222000000000000000/0000000000000000000000000/0000000000000000000000000/0000000000000000000000000/0008000000000000000000000/0000000008000000000000000/0000000000000000000000000/0000080000000000000000000/0000000000000000000000000/0000000080000000000000000/0000000000000000000000000/0000000000000000000000000/0000000000000000000000000",
    "00000000000000000/00000040004000000/00000000000000000/00000000000000000/00400222222000000/00000222222000000/00000222222000000/04000222222000000/00400222222000000/00000222222000400/00000000000000000/00000000000000000/00000000000000000/00000400000000000/00000000040000000/00000000000000000/00000000000000000/00000000000000000/00000000000000000/00000000000000000",
    "00000000000000000000/00000000000000000000/00000010022222220000/00000000022222220001/00000100022222220000/00000000022222220000/00000000022222220000/01000000022222220000/00000000022222220001/00000000000000000000/00000000000000000000/00000000000000000000/00000000010000000000/00000000000000000000/00000000000000000000/00000000000000000000/00000000000000000000/00000000000001000000/00000000000000000000/00000000000000010000",
)


def _decode(text):
    return [[int(value) for value in line] for line in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed 30"]
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be literal ARC integers 0..9"]
    return []


def _extract_facts(grid):
    height, width = len(grid), len(grid[0])
    red = [(row, col) for row in range(height) for col in range(width) if grid[row][col] == 2]
    if not red:
        raise ValueError("no red cells")
    top = min(row for row, _ in red)
    bottom = max(row for row, _ in red)
    left = min(col for _, col in red)
    right = max(col for _, col in red)
    rectangle = {(row, col) for row in range(top, bottom + 1) for col in range(left, right + 1)}
    if set(red) != rectangle:
        raise ValueError("red cells must form one solid rectangle")
    if top == 0 or left == 0 or bottom == height - 1 or right == width - 1:
        raise ValueError("red rectangle must have space on every side")

    markers = [(row, col, grid[row][col]) for row in range(height) for col in range(width) if grid[row][col] not in (0, 2)]
    above, below, left_rows, right_rows = set(), set(), set(), set()
    decoys = []
    for row, col, value in markers:
        if row < top and left <= col <= right:
            above.add(col)
        elif row > bottom and left <= col <= right:
            below.add(col)
        elif col < left and top <= row <= bottom:
            left_rows.add(row)
        elif col > right and top <= row <= bottom:
            right_rows.add(row)
        else:
            decoys.append((row, col, value))

    output = [list(row) for row in grid]
    for col in range(left, right + 1):
        if col not in above:
            for row in range(0, top):
                if output[row][col] == 0:
                    output[row][col] = 2
        if col not in below:
            for row in range(bottom + 1, height):
                if output[row][col] == 0:
                    output[row][col] = 2
    for row in range(top, bottom + 1):
        if row not in left_rows:
            for col in range(0, left):
                if output[row][col] == 0:
                    output[row][col] = 2
        if row not in right_rows:
            for col in range(right + 1, width):
                if output[row][col] == 0:
                    output[row][col] = 2

    return {
        "bbox": (top, left, bottom, right),
        "rectangle_shape": (bottom - top + 1, right - left + 1),
        "markers": markers,
        "marker_colors": tuple(sorted({value for _, _, value in markers})),
        "above_cols": tuple(sorted(above)),
        "below_cols": tuple(sorted(below)),
        "left_rows": tuple(sorted(left_rows)),
        "right_rows": tuple(sorted(right_rows)),
        "decoys": decoys,
        "output": output,
        "changed": sum(a != b for before, after in zip(grid, output) for a, b in zip(before, after)),
    }


def _general_signature(facts):
    above = set(facts["above_cols"])
    below = set(facts["below_cols"])
    left = set(facts["left_rows"])
    right = set(facts["right_rows"])
    decoys = facts["decoys"]
    colors = facts["marker_colors"]
    rows, cols = facts["rectangle_shape"]
    occupied = tuple(bool(values) for values in (above, below, left, right))
    if occupied == (False, False, False, False) and decoys:
        return "open_with_decoys"
    if occupied == (True, False, False, False) and len(above) == 1 and not decoys and len(colors) == 1:
        return "up_only"
    if occupied == (False, True, False, False) and len(below) == 1 and not decoys and len(colors) == 1:
        return "down_only"
    if occupied == (False, False, True, False) and len(left) == 1 and not decoys and len(colors) == 1:
        return "left_only"
    if occupied == (False, False, False, True) and len(right) == 1 and not decoys and len(colors) == 1:
        return "right_only"
    if occupied == (True, True, False, False) and len(above) == len(below) == 1 and not decoys and len(colors) == 1:
        return "same_col_opposites" if above == below else "split_col_opposites"
    if occupied == (False, False, True, True) and len(left) == len(right) == 1 and not decoys and len(colors) == 1:
        return "same_row_opposites" if left == right else "split_row_opposites"
    if occupied == (True, True, True, True):
        if decoys and len(colors) == 1 and all(len(values) == 1 for values in (above, below, left, right)):
            return "aligned_with_decoys"
        if not decoys and len(colors) >= 2 and all(len(values) == 1 for values in (above, below, left, right)):
            return "mixed_colors_four_sides"
        if not decoys and len(colors) == 1 and (len(above), len(below), len(left), len(right)) == (cols - 1, cols - 1, rows - 1, rows - 1):
            return "dense_four_sides"
    return None


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None}
    try:
        facts = _extract_facts(grid)
    except (TypeError, ValueError) as exc:
        return {"errors": [str(exc)], "scene_profile": None}
    profile = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid))) or _general_signature(facts)
    if not facts["markers"]:
        errors.append("at least one blocker or inert marker is required")
    if facts["changed"] <= 0:
        errors.append("the canonical rule must visibly change the input")
    if profile is None:
        errors.append("scene does not match a declared semantic profile")
    return {"errors": errors, "scene_profile": profile, "facts": facts, "output": facts["output"]}


def rule_mirror(grid):
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _extract_facts(grid)["output"]


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _ranges(difficulty):
    if difficulty == "easy":
        return (12, 18, 2, 5)
    if difficulty == "medium":
        return (16, 24, 3, 7)
    if difficulty == "hard":
        return (20, 30, 4, 9)
    return (14, 26, 2, 8)


def _general_scene(ctx, profile, rng):
    low, high, rect_low, rect_high = _ranges(ctx.difficulty)
    for _ in range(80):
        height = rng.randint(low, high)
        width = rng.randint(low, high)
        rect_height = rng.randint(rect_low, min(rect_high, height - 4))
        rect_width = rng.randint(rect_low, min(rect_high, width - 4))
        top = rng.randint(2, height - rect_height - 2)
        left = rng.randint(2, width - rect_width - 2)
        bottom = top + rect_height - 1
        right = left + rect_width - 1
        grid = [[0 for _ in range(width)] for _ in range(height)]
        for row in range(top, bottom + 1):
            for col in range(left, right + 1):
                grid[row][col] = 2

        columns = list(range(left, right + 1))
        rows = list(range(top, bottom + 1))
        above = below = left_rows = right_rows = set()
        decoy_count = 0
        if profile == "open_with_decoys":
            decoy_count = rng.randint(2, 5)
        elif profile == "up_only":
            above = {rng.choice(columns)}
        elif profile == "down_only":
            below = {rng.choice(columns)}
        elif profile == "left_only":
            left_rows = {rng.choice(rows)}
        elif profile == "right_only":
            right_rows = {rng.choice(rows)}
        elif profile == "same_col_opposites":
            lane = rng.choice(columns)
            above = below = {lane}
        elif profile == "split_col_opposites":
            first, second = rng.sample(columns, 2)
            above, below = {first}, {second}
        elif profile == "same_row_opposites":
            lane = rng.choice(rows)
            left_rows = right_rows = {lane}
        elif profile == "split_row_opposites":
            first, second = rng.sample(rows, 2)
            left_rows, right_rows = {first}, {second}
        elif profile in {"mixed_colors_four_sides", "aligned_with_decoys"}:
            above, below = {rng.choice(columns)}, {rng.choice(columns)}
            left_rows, right_rows = {rng.choice(rows)}, {rng.choice(rows)}
            decoy_count = rng.randint(1, 4) if profile == "aligned_with_decoys" else 0
        elif profile == "dense_four_sides":
            above = set(columns) - {rng.choice(columns)}
            below = set(columns) - {rng.choice(columns)}
            left_rows = set(rows) - {rng.choice(rows)}
            right_rows = set(rows) - {rng.choice(rows)}
        else:
            raise ValueError(f"unknown scene_profile: {profile!r}")

        marker_entries = []
        marker_entries.extend((rng.randrange(0, top), col) for col in sorted(above))
        marker_entries.extend((rng.randrange(bottom + 1, height), col) for col in sorted(below))
        marker_entries.extend((row, rng.randrange(0, left)) for row in sorted(left_rows))
        marker_entries.extend((row, rng.randrange(right + 1, width)) for row in sorted(right_rows))
        legal_colors = [1, 3, 4, 5, 6, 7, 8, 9]
        if profile == "mixed_colors_four_sides":
            palette = rng.sample(legal_colors, rng.randint(2, 4))
        else:
            palette = [rng.choice(legal_colors)]
        for index, (row, col) in enumerate(marker_entries):
            grid[row][col] = palette[index % len(palette)]

        quadrants = [(row, col) for row in range(height) for col in range(width) if not top <= row <= bottom and not left <= col <= right and grid[row][col] == 0]
        rng.shuffle(quadrants)
        for row, col in quadrants[:decoy_count]:
            grid[row][col] = palette[0]

        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct {profile}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = ctx.draw_choice("scene_profile", PUBLIC_PROFILES + GENERAL_PROFILES * 4)
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general_scene(ctx, profile, ctx.draw_rng("geometry"))
