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
VERSION = "4.1.0"
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
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = (
    "threshold_witness_a",
    "public_anchor",
    "threshold_witness_b",
    "broad",
)
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four-step teaching schedule: witness, exact-public, witness, broad",
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


def _validate_identity(seed, sample_index):
    if type(seed) is not int:
        raise ValueError("seed must be a plain Python integer (not bool/float/string)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative plain Python integer")


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic teaching role for this draw.

    Two witnesses per four-example window make every three-demo/query rotation
    retain a counterexample to the canonical-fitting panel-direction shortcut.
    """
    _validate_identity(seed, sample_index)
    _band(difficulty)
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _separators(rng, length, *, min_gap=4):
    first = rng.randint(2, length - min_gap - 2)
    second = rng.randint(first + min_gap, length - 2)
    return first, second


def _axis_target(rng, step, marker, first_separator, second_separator, length):
    if step < 0:
        return rng.randint(0, first_separator - 1)
    if step > 0:
        return rng.randint(second_separator + 1, length - 1)
    return max(first_separator + 1, min(second_separator - 1, marker + rng.choice((-1, 0, 1))))


def _same_panel_far_target(rng, step, marker, first_separator, second_separator):
    if step < 0:
        candidates = list(range(first_separator + 1, marker - 1))
    elif step > 0:
        candidates = list(range(marker + 2, second_separator))
    else:
        return max(first_separator + 1, min(second_separator - 1, marker + rng.choice((-1, 0, 1))))
    if not candidates:
        raise AssertionError("witness panel has no same-panel target at distance at least two")
    return rng.choice(candidates)


def _witness_marker(rng, step, first_separator, second_separator):
    if step < 0:
        low, high = first_separator + 3, second_separator - 2
    elif step > 0:
        low, high = first_separator + 2, second_separator - 3
    else:
        low, high = first_separator + 2, second_separator - 2
    if low > high:
        raise AssertionError("witness panel is too narrow for the requested direction")
    return rng.randint(low, high)


def _general(rng, profile, band, *, force_same_panel_far=False):
    ranges = {"easy": (8, 12), "medium": (11, 19), "hard": (18, 28)}
    low, high = ranges[band]
    if force_same_panel_far:
        low = max(low, 10)
    height, width = rng.randint(low, high), rng.randint(low, high)
    direction = _PROFILE_DIRECTION[profile]
    separator_rows = _separators(rng, height, min_gap=6 if force_same_panel_far else 4)
    separator_cols = _separators(rng, width, min_gap=6 if force_same_panel_far else 4)
    if force_same_panel_far:
        if direction == (0, 0):
            raise ValueError("threshold witnesses require a nonzero coarse direction")
        marker = (
            _witness_marker(rng, direction[0], *separator_rows),
            _witness_marker(rng, direction[1], *separator_cols),
        )
    else:
        marker = (
            rng.randint(separator_rows[0] + 2, separator_rows[1] - 2),
            rng.randint(separator_cols[0] + 2, separator_cols[1] - 2),
        )
    if direction == (0, 0):
        offsets = [(row, col) for row in (-1, 0, 1) for col in (-1, 0, 1) if (row, col) != (0, 0)]
        offset = rng.choice(offsets)
        target = marker[0] + offset[0], marker[1] + offset[1]
    elif force_same_panel_far:
        target = (
            _same_panel_far_target(rng, direction[0], marker[0], *separator_rows),
            _same_panel_far_target(rng, direction[1], marker[1], *separator_cols),
        )
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
    _validate_identity(seed, sample_index)
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    band = _band(difficulty)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=band, overrides=overrides)
    role = schedule_profile(seed, sample_index, difficulty)
    force_same_panel_far = False
    if requested is not None:
        profile = requested
    elif role == "public_anchor":
        profile = ctx.draw_choice("scene_profile", PUBLIC_PROFILES)
    elif role.startswith("threshold_witness"):
        profile = ctx.draw_choice("scene_profile", GENERAL_PROFILES[:-1])
        force_same_panel_far = True
    else:
        profile = ctx.draw_choice("scene_profile", GENERAL_PROFILES)
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general(ctx.draw_rng("layout"), profile, band, force_same_panel_far=force_same_panel_far)


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid):
    """Canonical-compatible teaching grammar for semantic review."""
    return list(_analysis(grid)["errors"])


def _panel_axis_step(target, separators):
    if target < separators[0]:
        return -1
    if target > separators[1]:
        return 1
    return 0


def _panel_direction_only(grid):
    """Plausible shortcut: move according to target panel, not distance."""
    errors = _valid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [list(row) for row in grid]
    nines, sixes = _positions(grid, 9), _positions(grid, 6)
    if not nines or not sixes:
        return output
    marker, target = nines[0], sixes[0]
    height, width = len(grid), len(grid[0])
    separator_rows = [row for row, values in enumerate(grid) if all(value == 0 for value in values)]
    separator_cols = [col for col in range(width) if all(grid[row][col] == 0 for row in range(height))]
    if len(separator_rows) != 2 or len(separator_cols) != 2:
        return rule_mirror(grid)
    row_step = _panel_axis_step(target[0], separator_rows)
    col_step = _panel_axis_step(target[1], separator_cols)
    next_cell = marker[0] + row_step, marker[1] + col_step
    output[marker[0]][marker[1]] = 5
    output[next_cell[0]][next_cell[1]] = 9
    output[target[0]][target[1]] = 9
    return output


def _same_panel_far_axis(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    marker, target = analysis["marker"], analysis["target"]
    row_same_far = (
        analysis["separator_rows"][0] < target[0] < analysis["separator_rows"][1]
        and abs(target[0] - marker[0]) > 1
    )
    col_same_far = (
        analysis["separator_cols"][0] < target[1] < analysis["separator_cols"][1]
        and abs(target[1] - marker[1]) > 1
    )
    return (row_same_far or col_same_far) and _panel_direction_only(grid) != analysis["output"]


SEMANTIC_RIVALS = {"panel_direction_only": _panel_direction_only}
CANONICAL_SHORTCUTS = {"panel_direction_only": _panel_direction_only}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {"same_panel_far_axis": _same_panel_far_axis}
WITNESS_RIVALS = {"same_panel_far_axis": ["panel_direction_only"]}


def lesson_identifiable(demos, query):
    """Require the visible demonstrations to refute the panel shortcut."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    reasons = []
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    else:
        query_errors = strict_canonical_like(query["input"])
        if query_errors:
            reasons.append(f"query input is outside teaching grammar: {query_errors[0]}")
        elif query.get("output") is not None and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output disagrees with the coarse-distance rule")

    refuted = {name: False for name in LESSON_COMPETITORS}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = strict_canonical_like(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is outside teaching grammar: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the coarse-distance rule")
            continue
        for name, rival in LESSON_COMPETITORS.items():
            if rival(demo["input"]) != expected:
                refuted[name] = True
    for name, killed in refuted.items():
        if not killed:
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons
