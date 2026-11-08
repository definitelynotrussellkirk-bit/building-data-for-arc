"""Semantic generator for ARC task c739fcbc6cbd.

Take the first two nonzero dots in color-major, then row-major, order.  Use
their smaller positive coordinate separation to select horizontal or vertical
bands (equal separations select columns), and repeat the two colored phases at
twice that separation after a blank prefix.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "c739fcbc6cbd"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "689b63050826"
SUMMARY = "Repeat the first two color-major dots as alternating row or column phases, using period twice the selected coordinate separation."
INVARIANTS = [
    "literal color 0 is the background",
    "at least two nonzero dots are present",
    "the first two dots are selected by color then row-major position",
    "row bands are selected only when dc is zero or 0 < dr < dc; equality selects columns",
    "cells before the earlier active-axis coordinate remain zero",
    "the two phases repeat with period twice their active-axis separation",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4", "public_5")
GENERAL_PROFILES = (
    "row_same_column",
    "row_diagonal",
    "column_same_row",
    "column_diagonal",
    "equal_distance_column",
    "row_nonzero_prefix",
    "column_nonzero_prefix",
    "adjacent_phases",
    "spatial_color_reverse",
    "same_color_phases",
    "high_color_decoys",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("row_major_counterexample", "broad")
_NON_COUNTEREXAMPLE_PROFILES = tuple(
    profile for profile in SCENE_PROFILES if profile != "high_color_decoys"
)
# Odd schedule slots preserve all non-witness profiles while favoring exact
# public morphology enough for the strict 20-draw profile-floor gate.
_BROAD_PROFILE_CHOICES = PUBLIC_PROFILES * 2 + tuple(
    profile for profile in GENERAL_PROFILES if profile != "high_color_decoys"
) * 2
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five exact-public and eleven observable phase-selection lessons",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_ROWS = {
    "public_1": "000000000/000000000/000000000/000000000/000000000/200000000/000000000/000000003/000000000/000000000/000000000/000000000/000000000/000000000/000000000/000000000/000000000/000000000/000000000/000000000/000000000/000000000",
    "public_2": "00000100000000000000000/00000000000000000000000/00000000000000000000000/00000000000000000000000/00000000000000000000000/00000000000000000000000/00000000300000000000000",
    "public_3": "00000000/00000000/00000000/00000000/00000000/00000000/00000000/40000000/00000000/00000000/00000000/10000000/00000000/00000000/00000000/00000000/00000000/00000000/00000000/00000000/00000000/00000000/00000000/00000000",
    "public_4": "0000020000000000000000000/0000000000000000000000000/0000000000000000000000000/0000000000000000000000000/0000000000000000000000000/0000000000000000000000000/0000000000000000000000000/0000000000000000000000000/0000000000000000000000000/0000000800000000000000000",
    "public_5": "000003000000000000000000000/000000000000000000000000000/000000000000000000000000000/000000000000000000000000000/000000000000000000000000000/000000000000000000000000000/000000000000000000000000000/000000000000000000000000000/000000000000000000000000000/000000000000000000000000000/000000000040000000000000000",
}


def _decode(rows):
    return [[int(value) for value in row] for row in rows.split("/")]


_PUBLIC_INPUTS = {name: _decode(rows) for name, rows in _PUBLIC_ROWS.items()}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}


def _valid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed 30"]
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _dots(grid):
    return [
        (row, col, color)
        for color in range(1, 10)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    ]


def _row_major_dots(grid):
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]


def _validate_call_arguments(seed, sample_index):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, or string)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool, float, or string)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")


def _phase_output(height, width, first, second):
    r1, c1, color1 = first
    r2, c2, color2 = second
    dr, dc = abs(r2 - r1), abs(c2 - c1)
    row_bands = dc == 0 or (dr > 0 and dr < dc)
    distance = dr if row_bands else dc
    if distance == 0:
        raise ValueError("selected dots must differ on the active axis")
    period = 2 * distance
    output = [[0 for _ in range(width)] for _ in range(height)]
    if row_bands:
        for row in range(min(r1, r2), height):
            color = color1 if (row - r1) % period == 0 else color2 if (row - r2) % period == 0 else 0
            if color:
                output[row] = [color for _ in range(width)]
    else:
        for col in range(min(c1, c2), width):
            color = color1 if (col - c1) % period == 0 else color2 if (col - c2) % period == 0 else 0
            if color:
                for row in range(height):
                    output[row][col] = color
    return {
        "r1": r1,
        "c1": c1,
        "color1": color1,
        "r2": r2,
        "c2": c2,
        "color2": color2,
        "dr": dr,
        "dc": dc,
        "row_bands": row_bands,
        "active_axis": "row" if row_bands else "column",
        "distance": distance,
        "period": period,
        "prefix": min(r1, r2) if row_bands else min(c1, c2),
        "output": output,
    }


def rule_mirror(grid):
    errors = _valid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    dots = _dots(grid)
    if len(dots) < 2:
        raise ValueError("expected at least two nonzero dots")
    return _phase_output(len(grid), len(grid[0]), dots[0], dots[1])["output"]


def _row_major_first_two(grid):
    """Plausible wrong rule: select markers by spatial scan, not by color."""
    errors = _valid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    dots = _row_major_dots(grid)
    if len(dots) < 2:
        raise ValueError("expected at least two nonzero dots")
    return _phase_output(len(grid), len(grid[0]), dots[0], dots[1])["output"]


def _row_major_order_matters(grid):
    """True exactly when the named row-major rival changes the answer."""
    try:
        return _row_major_first_two(grid) != rule_mirror(grid)
    except ValueError:
        return False


def _general_profile(dots, phase):
    if len(dots) > 2:
        return "high_color_decoys"
    if phase["color1"] == phase["color2"]:
        return "same_color_phases"
    if phase["distance"] == 1:
        return "adjacent_phases"
    if phase["dr"] == phase["dc"]:
        return "equal_distance_column"
    active_first = phase["r1"] if phase["row_bands"] else phase["c1"]
    active_second = phase["r2"] if phase["row_bands"] else phase["c2"]
    if active_first > active_second:
        return "spatial_color_reverse"
    if phase["row_bands"] and phase["prefix"] > 0:
        return "row_nonzero_prefix"
    if not phase["row_bands"] and phase["prefix"] > 0:
        return "column_nonzero_prefix"
    if phase["dc"] == 0:
        return "row_same_column"
    if phase["dr"] == 0:
        return "column_same_row"
    return "row_diagonal" if phase["row_bands"] else "column_diagonal"


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    dots = _dots(grid)
    if not 2 <= len(dots) <= 5:
        errors.append(f"expected 2..5 nonzero dots; got {len(dots)}")
        return result
    occupied = {(row, col): color for row, col, color in dots}
    for row, col, color in dots:
        if any(occupied.get((row + dr, col + dc)) == color for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))):
            errors.append("same-color marker cells must remain 4-disconnected dots")
            return result
    phase = _phase_output(len(grid), len(grid[0]), dots[0], dots[1])
    profile = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid))) or _general_profile(dots, phase)
    if profile not in SCENE_PROFILES:
        errors.append("dot geometry does not match a declared profile")
    result.update(phase)
    result.update({"dots": dots, "selected": dots[:2], "ignored": dots[2:], "scene_profile": profile, "errors": errors})
    return result


def self_check(grid, *, difficulty=None, meta=None):
    try:
        return list(_analysis(grid)["errors"])
    except ValueError as exc:
        return [str(exc)]


def strict_canonical_like(grid):
    """Accept the generator's full lawful task manifold."""
    return self_check(grid)


def lesson_identifiable(demos, query):
    """Reject a lesson only when the declared row-major rival stays viable."""
    try:
        rival_fits_demos = all(
            _row_major_first_two(pair["input"]) == pair["output"]
            for pair in demos
        )
        rival_changes_query = (
            _row_major_first_two(query["input"]) != query["output"]
        )
    except (KeyError, TypeError, ValueError) as exc:
        return [f"malformed lesson for row-major rival check: {exc}"]
    if rival_fits_demos and rival_changes_query:
        return [
            "row_major_first_two fits every demonstration but changes the query"
        ]
    return []


SEMANTIC_WITNESSES = {
    "row_major_order_matters": _row_major_order_matters,
}
SEMANTIC_RIVALS = {
    "row_major_first_two": _row_major_first_two,
}
WITNESS_RIVALS = {
    "row_major_order_matters": ["row_major_first_two"],
}
CANONICAL_SHORTCUTS = {
    "row_major_first_two": _row_major_first_two,
}
LESSON_COMPETITORS = {
    "row_major_first_two": _row_major_first_two,
}


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {"scene_profile": analysis["scene_profile"]}


def _general_scene(ctx, profile):
    ranges = {
        None: (12, 30),
        "easy": (12, 15),
        "medium": (16, 22),
        "hard": (23, 30),
    }
    low, high = ranges[ctx.difficulty]
    height = ctx.draw_int("canvas_height", low, high)
    width = ctx.draw_int("canvas_width", low, high)
    rng = ctx.draw_rng("geometry")
    colors = sorted(rng.sample(range(1, 10), 2))
    distance = rng.randint(2, 4)

    if profile == "row_same_column":
        distance = rng.randint(2, min(7, height - 1))
        col = rng.randrange(width)
        positions = [(0, col), (distance, col)]
    elif profile == "row_diagonal":
        across = rng.randint(distance + 1, min(width - 1, distance + 5))
        positions = [(0, 0), (distance, across)]
    elif profile == "column_same_row":
        row = rng.randrange(height)
        positions = [(row, 0), (row, distance)]
    elif profile == "column_diagonal":
        down = rng.randint(distance + 1, min(height - 1, distance + 5))
        positions = [(0, 0), (down, distance)]
    elif profile == "equal_distance_column":
        positions = [(0, 0), (distance, distance)]
    elif profile == "row_nonzero_prefix":
        prefix = rng.randint(1, min(3, height - distance - 1))
        across = rng.randint(distance + 1, min(width - 1, distance + 5))
        positions = [(prefix, 0), (prefix + distance, across)]
    elif profile == "column_nonzero_prefix":
        prefix = rng.randint(1, min(3, width - distance - 1))
        down = rng.randint(distance + 1, min(height - 1, distance + 5))
        positions = [(0, prefix), (down, prefix + distance)]
    elif profile == "adjacent_phases":
        if rng.choice((False, True)):
            col = rng.randrange(width)
            positions = [(0, col), (1, col)]
        else:
            row = rng.randrange(height)
            positions = [(row, 0), (row, 1)]
    elif profile == "spatial_color_reverse":
        col = rng.randrange(width)
        positions = [(distance, col), (0, col)]
    elif profile == "same_color_phases":
        col = rng.randrange(width)
        positions = [(0, col), (distance, col)]
        colors[1] = colors[0]
    elif profile == "high_color_decoys":
        # The intended first two colors remain the two smallest.  A later-color
        # marker is placed earlier in row-major order, giving a guaranteed
        # counterexample to the canonical-fitting spatial-order shortcut.
        colors = sorted(rng.sample(range(1, 7), 2))
        second_row = rng.randint(2, min(height - 1, 9))
        second_col = rng.randint(1, min(width - 1, 9))
        positions = [(0, 0), (second_row, second_col)]
    else:
        raise ValueError(f"unknown scene profile: {profile!r}")

    grid = [[0 for _ in range(width)] for _ in range(height)]
    for (row, col), color in zip(positions, colors):
        grid[row][col] = color
    if profile == "high_color_decoys":
        decoy_col = rng.randint(1, width - 1)
        available_colors = list(range(colors[1] + 1, 10))
        primary_decoy = rng.choice(available_colors)
        grid[0][decoy_col] = primary_decoy
        remaining_colors = [color for color in available_colors if color != primary_decoy]
        free = [
            (row, col)
            for row in range(height)
            for col in range(width)
            if grid[row][col] == 0
        ]
        rng.shuffle(free)
        extra_count = rng.randint(0, min(2, len(remaining_colors)))
        for color in rng.sample(remaining_colors, extra_count):
            row, col = free.pop()
            grid[row][col] = color
    return grid


def schedule_profile(seed, sample_index, difficulty=None):
    _validate_call_arguments(seed, sample_index)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call_arguments(seed, sample_index)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if "scene_profile" in overrides:
        choices = PUBLIC_PROFILES + GENERAL_PROFILES + GENERAL_PROFILES
    elif schedule_profile(seed, sample_index, difficulty) == "row_major_counterexample":
        choices = ("high_color_decoys",)
    else:
        choices = _BROAD_PROFILE_CHOICES
    profile = ctx.draw_choice("scene_profile", choices)
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    grid = _general_scene(ctx, profile)
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise AssertionError(f"internal invalid scene: {analysis['errors']}")
    if analysis["scene_profile"] != profile:
        raise AssertionError(f"profile drift: {profile} -> {analysis['scene_profile']}")
    return grid
