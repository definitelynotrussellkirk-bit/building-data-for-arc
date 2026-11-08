"""Semantic generator for ARC task a85f5274d2ae.

A modal-7 canvas is split into a 3x3 panel grid by two full zero rows
and columns.  A color-9 marker sits at the center of a 3x3 color-5 ring in
the middle panel; a color-6 marker lies in a coarse direction from it.  Paint
the old 9 position 5, move 9 one coarse step toward 6 (an axis moves only when
its absolute delta exceeds one), and recolor the 6 position 9.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "a85f5274d2ae"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "bba3b44960f2"
SUMMARY = "Move the central ring's 9 one coarse step toward 6 and recolor the destination marker 9."
INVARIANTS = [
    "background is modal color 7",
    "two full color-0 rows and columns define a 3x3 panel grid",
    "exactly one 9 is centered in a 3x3 color-5 ring in the middle panel",
    "exactly one 6 supplies the coarse movement direction",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4")
GENERAL_PROFILES = (
    "target_ul",
    "target_up",
    "target_ur",
    "target_left",
    "target_right",
    "target_ll",
    "target_down",
    "target_lr",
    "near_no_step",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted exact-public and all coarse movement directions",
        "valid": "public_1|public_2|public_3|public_4|target_ul|target_up|target_ur|target_left|target_right|target_ll|target_down|target_lr|near_no_step",
    }
}

_PUBLIC_ROWS = {
    "public_1": "777077707777/777077707747/772077707777/000000000000/477055507777/777059507778/777055507777/000000000000/777077707777/777077707777/778077707767/777077707777",
    "public_2": "17077407/77077707/00000000/67055507/77059507/77055507/00000000/73077707",
    "public_3": "777778077707777/777777071707727/767777077707777/000000000000000/777777055507777/777777059508777/777777055507777/000000000000000/777777077707777/747777077707777/777777077707771/777777077707777/777727071707771/777777077707777/777777077707777",
    "public_4": "7777707770777777777/7777707770777777777/7777707770777777777/7777707770777777777/7777708770777777777/7777707770777777777/7777707770777777777/0000000000000000000/7777705550777777377/7774705950777777777/7777705550777777777/0000000000000000000/7777707730777777777/7777707770777777777/7774706770772777777/7777707770777777777/7777707770777727777/7777707780777777777/7777707770777777778",
}


def _decode(rows):
    return [[int(value) for value in row] for row in rows.split("/")]


_PUBLIC_INPUTS = {name: _decode(rows) for name, rows in _PUBLIC_ROWS.items()}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}
_DIRECTION_PROFILES = {
    (-1, -1): "target_ul",
    (-1, 0): "target_up",
    (-1, 1): "target_ur",
    (0, -1): "target_left",
    (0, 1): "target_right",
    (1, -1): "target_ll",
    (1, 0): "target_down",
    (1, 1): "target_lr",
    (0, 0): "near_no_step",
}
_PROFILE_DIRECTION = {profile: direction for direction, profile in _DIRECTION_PROFILES.items()}


def _valid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be ARC colors"]
    return []


def _positions(grid, color):
    return [(row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value == color]


def _coarse_step(first, second):
    row_delta = second[0] - first[0]
    col_delta = second[1] - first[1]
    row_step = 0 if abs(row_delta) <= 1 else 1 if row_delta > 0 else -1
    col_step = 0 if abs(col_delta) <= 1 else 1 if col_delta > 0 else -1
    return row_step, col_step


def rule_mirror(grid):
    errors = _valid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    nines = _positions(grid, 9)
    sixes = _positions(grid, 6)
    output = [list(row) for row in grid]
    if not nines or not sixes:
        return output
    marker, target = nines[0], sixes[0]
    row_step, col_step = _coarse_step(marker, target)
    next_cell = marker[0] + row_step, marker[1] + col_step
    output[marker[0]][marker[1]] = 5
    output[next_cell[0]][next_cell[1]] = 9
    output[target[0]][target[1]] = 9
    return output


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    height, width = len(grid), len(grid[0])
    nines, sixes = _positions(grid, 9), _positions(grid, 6)
    if len(nines) != 1:
        errors.append(f"expected exactly one color-9 marker, found {len(nines)}")
    if len(sixes) != 1:
        errors.append(f"expected exactly one color-6 target, found {len(sixes)}")
    separator_rows = [row for row, values in enumerate(grid) if all(value == 0 for value in values)]
    separator_cols = [col for col in range(width) if all(grid[row][col] == 0 for row in range(height))]
    if len(separator_rows) != 2:
        errors.append(f"expected exactly two full color-0 separator rows, found {len(separator_rows)}")
    if len(separator_cols) != 2:
        errors.append(f"expected exactly two full color-0 separator columns, found {len(separator_cols)}")
    modal_nonzero = max(range(1, 10), key=lambda color: sum(value == color for row in grid for value in row))
    if modal_nonzero != 7:
        errors.append(f"modal non-separator background must be 7, found {modal_nonzero}")
    marker = nines[0] if nines else None
    target = sixes[0] if sixes else None
    if marker and len(separator_rows) == 2 and len(separator_cols) == 2:
        if not separator_rows[0] < marker[0] < separator_rows[1] or not separator_cols[0] < marker[1] < separator_cols[1]:
            errors.append("color-9 marker must lie in the middle panel")
        if not 1 <= marker[0] < height - 1 or not 1 <= marker[1] < width - 1:
            errors.append("color-9 marker must have a complete 3x3 ring")
        else:
            for row in range(marker[0] - 1, marker[0] + 2):
                for col in range(marker[1] - 1, marker[1] + 2):
                    if (row, col) == marker:
                        continue
                    expected = 6 if target == (row, col) else 5
                    if grid[row][col] != expected:
                        errors.append("the central 9 must be surrounded by a color-5 ring")
                        row = marker[0] + 2
                        break
                else:
                    continue
                break
    if target and (target[0] in separator_rows or target[1] in separator_cols):
        errors.append("color-6 target may not overwrite a separator")
    allowed = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}
    if any(value not in allowed for row in grid for value in row):
        errors.append("unexpected color")
    noise = sum(value in {1, 2, 3, 4, 8} for row in grid for value in row)
    if noise < 3:
        errors.append(f"expected at least three sparse distractors, found {noise}")
    direction = _coarse_step(marker, target) if marker and target else None
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    profile = public or _DIRECTION_PROFILES.get(direction)
    if profile not in SCENE_PROFILES:
        errors.append("marker/target relation does not match a declared direction")
    output = rule_mirror(grid)
    result.update(
        {
            "marker": marker,
            "target": target,
            "direction": direction,
            "separator_rows": tuple(separator_rows),
            "separator_cols": tuple(separator_cols),
            "noise_cells": noise,
            "output": output,
            "scene_profile": profile,
            "errors": errors,
        }
    )
    return result


def canonical_profile_signature(grid):
    analysis = _analysis(grid)
    profile = analysis.get("scene_profile")
    return profile if not analysis["errors"] and profile in PUBLIC_PROFILES else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {"scene_profile": analysis["scene_profile"]}


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _separators(rng, length):
    first = rng.randint(2, length - 6)
    second = rng.randint(first + 4, length - 2)
    return first, second


def _axis_target(rng, step, marker, first_separator, second_separator, length):
    if step < 0:
        return rng.randint(0, first_separator - 1)
    if step > 0:
        return rng.randint(second_separator + 1, length - 1)
    return max(first_separator + 1, min(second_separator - 1, marker + rng.choice((-1, 0, 1))))


def _general(rng, profile, band):
    ranges = {"easy": (8, 12), "medium": (11, 19), "hard": (18, 28)}
    low, high = ranges[band]
    height, width = rng.randint(low, high), rng.randint(low, high)
    separator_rows = _separators(rng, height)
    separator_cols = _separators(rng, width)
    marker = (
        rng.randint(separator_rows[0] + 2, separator_rows[1] - 2),
        rng.randint(separator_cols[0] + 2, separator_cols[1] - 2),
    )
    direction = _PROFILE_DIRECTION[profile]
    if direction == (0, 0):
        offsets = [(row, col) for row in (-1, 0, 1) for col in (-1, 0, 1) if (row, col) != (0, 0)]
        offset = rng.choice(offsets)
        target = marker[0] + offset[0], marker[1] + offset[1]
    else:
        target = (
            _axis_target(rng, direction[0], marker[0], *separator_rows, height),
            _axis_target(rng, direction[1], marker[1], *separator_cols, width),
        )
    grid = [[7] * width for _ in range(height)]
    for row in separator_rows:
        grid[row] = [0] * width
    for col in separator_cols:
        for row in range(height):
            grid[row][col] = 0
    for row in range(marker[0] - 1, marker[0] + 2):
        for col in range(marker[1] - 1, marker[1] + 2):
            grid[row][col] = 5
    grid[marker[0]][marker[1]] = 9
    grid[target[0]][target[1]] = 6
    candidates = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 7 and row not in separator_rows and col not in separator_cols
    ]
    rng.shuffle(candidates)
    noise_count = max(3, round(height * width * rng.uniform(0.018, 0.035)))
    colors = [1, 2, 3, 4, 8]
    rng.shuffle(colors)
    for index, (row, col) in enumerate(candidates[:noise_count]):
        grid[row][col] = colors[index % len(colors)]
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    band = _band(difficulty)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=band, overrides=overrides)
    profile = requested or ctx.draw_choice("scene_profile", list(PUBLIC_PROFILES) + [name for name in GENERAL_PROFILES for _ in range(4)])
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general(ctx.draw_rng("layout"), profile, band)


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analysis(grid)["errors"])
