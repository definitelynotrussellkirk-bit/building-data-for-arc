"""Semantic generator for ARC task 49f2e1c9f51a.

A straight green segment extends from the endpoint facing the red segment
through consecutive zero cells until the next nonzero cell or grid border.
The path then turns orthogonally toward the red segment and finishes across
that segment.  Every path cell becomes green, including crossed color-8
distractors, and the original red cells are restored afterward.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "49f2e1c9f51a"
TASK_ID = "49f2e1c9f51a"
VERSION = "3.0.0"
RULE_HASH = "f0623adfb8cc"
SUMMARY = "Extend the green segment until blocked, turn orthogonally toward the red segment, and restore the red target."
INVARIANTS = [
    "green and red each form one straight two-cell segment with the same orientation",
    "extension begins at the green endpoint facing the red segment",
    "the first leg continues only through zero cells and stops before a nonzero cell or at the border",
    "the remaining orthogonal legs paint through zeros and color-8 distractors alike",
    "all path cells become green and every original red cell is restored",
    "cells outside the constructed path remain unchanged",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4")
GENERAL_PROFILES = (
    "horizontal_right_blocked_cross",
    "horizontal_left_blocked_cross",
    "horizontal_right_border",
    "horizontal_left_border",
    "vertical_down_blocked_cross",
    "vertical_up_blocked_cross",
    "vertical_down_border",
    "vertical_up_border",
    "horizontal_aligned_target",
    "vertical_aligned_target",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four exact-public and ten recoverable blocked-path lessons",
        "valid": "public_1|public_2|public_3|public_4|horizontal_right_blocked_cross|horizontal_left_blocked_cross|horizontal_right_border|horizontal_left_border|vertical_down_blocked_cross|vertical_up_blocked_cross|vertical_down_border|vertical_up_border|horizontal_aligned_target|vertical_aligned_target",
    }
}

_PUBLIC_ROWS = (
    "0000000008/0380000000/0300000800/0000008008/0808000000/0008000000/0880020000/0080020000/0080000000/8000000000",
    "00008888800808880808/08000008000008080000/88888080800088800200/80880000008888880200/80088000000808000000/00080000000008000000/80000000000000000080/00800000000000000088/80000000000080000088/00000000080080000088/08000088808008088000/80000800008888888888/00000088800888080088/00000088000080008008/00030008080800800808/00030088800088880000/08000008088080808000/00000008000800000880/00080008080088800008/00008888008000088800",
    "000008080080080/000800800008088/800088800008880/000008080000000/000000000800080/033000008000800/000000000008080/088008008088000/080000000000000/822000000000080/800000088800000/080080800088880/000008080000000/000008808008008/080088000000000",
    "8888000008800/8000082200000/0800880000000/0080000080008/0080008000008/0008000080800/0000000000800/8083300000800/0880080000800/0000008800000/0880008000000/0008000000000/0000000000080",
)


def _decode(text):
    return [[int(value) for value in row] for row in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 8 <= len(grid) <= 30 or not 8 <= width <= 30:
        return ["input dimensions must be between 8 and 30"]
    if any(isinstance(value, bool) or not isinstance(value, int) or value not in (0, 2, 3, 8) for row in grid for value in row):
        return ["input cells must be literal 0, 2, 3, or 8"]
    return []


def _segment(cells):
    if len(cells) != 2:
        return None
    ordered = tuple(sorted(cells))
    rows = {row for row, _ in ordered}
    cols = {col for _, col in ordered}
    if len(rows) == 1 and ordered[0][1] + 1 == ordered[1][1]:
        return "horizontal"
    if len(cols) == 1 and ordered[0][0] + 1 == ordered[1][0]:
        return "vertical"
    return None


def _line_cells(row0, col0, row1, col1):
    if row0 == row1:
        low, high = sorted((col0, col1))
        return [(row0, col) for col in range(low, high + 1)]
    if col0 == col1:
        low, high = sorted((row0, row1))
        return [(row, col0) for row in range(low, high + 1)]
    raise ValueError("line endpoints must be cardinally aligned")


def _extract_facts(grid):
    threes = tuple((row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value == 3)
    twos = tuple((row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value == 2)
    source_orientation, target_orientation = _segment(threes), _segment(twos)
    if source_orientation is None or target_orientation is None or source_orientation != target_orientation:
        return {"errors": ["green and red must each form one straight two-cell segment with the same orientation"]}
    r3a, r3b = min(row for row, _ in threes), max(row for row, _ in threes)
    c3a, c3b = min(col for _, col in threes), max(col for _, col in threes)
    r2a, r2b = min(row for row, _ in twos), max(row for row, _ in twos)
    c2a, c2b = min(col for _, col in twos), max(col for _, col in twos)
    horizontal = source_orientation == "horizontal"
    dc = (1 if c2a + c2b >= c3a + c3b else -1) if horizontal else 0
    dr = 0 if horizontal else (1 if r2a + r2b > r3a + r3b else -1)
    start = (r3a, c3b if dc == 1 else c3a) if horizontal else (r3b if dr == 1 else r3a, c3a)
    target = (r2a, c2b if dc == 1 else c2a) if horizontal else (r2a if dr == 1 else r2b, c2a)
    height, width = len(grid), len(grid[0])
    row, col = start
    initial_leg = [start]
    while True:
        next_row, next_col = row + dr, col + dc
        if not (0 <= next_row < height and 0 <= next_col < width) or grid[next_row][next_col] != 0:
            break
        row, col = next_row, next_col
        initial_leg.append((row, col))
    corner1 = row, col
    stop_cell = (next_row, next_col) if 0 <= next_row < height and 0 <= next_col < width else None
    corner2 = (target[0], corner1[1]) if horizontal else (corner1[0], target[1])
    path = tuple(dict.fromkeys(
        _line_cells(start[0], start[1], corner1[0], corner1[1])
        + _line_cells(corner1[0], corner1[1], corner2[0], corner2[1])
        + _line_cells(corner2[0], corner2[1], target[0], target[1])
    ))
    output = [list(values) for values in grid]
    for path_row, path_col in path:
        output[path_row][path_col] = 3
    for target_row, target_col in twos:
        output[target_row][target_col] = 2
    overwritten_eights = tuple(cell for cell in path if grid[cell[0]][cell[1]] == 8)
    return {
        "errors": [],
        "height": height,
        "width": width,
        "threes": threes,
        "twos": twos,
        "orientation": source_orientation,
        "direction": dc or dr,
        "start": start,
        "target": target,
        "initial_leg": tuple(initial_leg),
        "corner1": corner1,
        "corner2": corner2,
        "stop_cell": stop_cell,
        "stop_value": grid[stop_cell[0]][stop_cell[1]] if stop_cell else None,
        "path": path,
        "overwritten_eights": overwritten_eights,
        "output": output,
    }


def rule_mirror(grid):
    """Exact Python mirror of the canonical Racket path construction."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    facts = _extract_facts(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return [row[:] for row in facts["output"]]


def _profile_for(grid, facts):
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if public:
        return public
    orientation, direction = facts["orientation"], facts["direction"]
    aligned = (
        orientation == "horizontal"
        and facts["start"][0] == facts["target"][0]
        or orientation == "vertical"
        and facts["start"][1] == facts["target"][1]
    )
    if aligned and facts["stop_value"] == 2:
        return f"{orientation}_aligned_target"
    direction_name = "right" if orientation == "horizontal" and direction == 1 else "left" if orientation == "horizontal" else "down" if direction == 1 else "up"
    if facts["stop_cell"] is None:
        return f"{orientation}_{direction_name}_border"
    if facts["stop_value"] == 8 and facts["overwritten_eights"]:
        return f"{orientation}_{direction_name}_blocked_cross"
    return None


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "facts": None, "scene_profile": None, "output": None}
    facts = _extract_facts(grid)
    if facts["errors"]:
        return {"errors": facts["errors"], "facts": facts, "scene_profile": None, "output": None}
    profile = _profile_for(grid, facts)
    if not any(8 in row for row in grid):
        errors.append("at least one color-8 blocker or distractor is required")
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared blocked-path profile")
    if facts["output"] == [list(row) for row in grid]:
        errors.append("generated lesson must visibly transform")
    changed = {(row, col) for row in range(facts["height"]) for col in range(facts["width"]) if grid[row][col] != facts["output"][row][col]}
    if not changed <= set(facts["path"]):
        errors.append("only path cells may change")
    if any(facts["output"][row][col] != 2 for row, col in facts["twos"]):
        errors.append("red target cells must be restored")
    facts["scene_profile"] = profile
    return {"errors": errors, "facts": facts, "scene_profile": profile, "output": facts["output"]}


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _dimensions(difficulty, orientation, rng):
    bands = {
        None: ((10, 16), (12, 20)),
        "easy": ((9, 11), (11, 13)),
        "medium": ((11, 14), (14, 16)),
        "hard": ((13, 16), (17, 20)),
    }
    (short0, short1), (long0, long1) = bands[difficulty]
    short = rng.randint(short0, short1)
    long = rng.randint(long0, long1)
    return (short, long) if orientation == "horizontal" else (long, short)


def _general_scene(difficulty, profile, rng):
    orientation = "horizontal" if profile.startswith("horizontal") else "vertical"
    direction = 1 if any(word in profile for word in ("right", "down")) else -1
    mode = "aligned_target" if profile.endswith("aligned_target") else "border" if profile.endswith("border") else "blocked_cross"
    height, width = _dimensions(difficulty, orientation, rng)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    if orientation == "horizontal":
        source_row = rng.choice((2, height - 3))
        target_row = source_row if mode == "aligned_target" else height - 3 if source_row == 2 else 2
        source_cols = (1, 2) if direction == 1 else (width - 3, width - 2)
        target_cols = (width - 3, width - 2) if direction == 1 else (1, 2)
        source = [(source_row, col) for col in source_cols]
        target = [(target_row, col) for col in target_cols]
        blocker = None
        if mode == "blocked_cross":
            blocker_col = rng.randint(5, width - 6) if direction == 1 else rng.randint(5, width - 6)
            blocker = source_row, blocker_col
    else:
        source_col = rng.choice((2, width - 3))
        target_col = source_col if mode == "aligned_target" else width - 3 if source_col == 2 else 2
        source_rows = (1, 2) if direction == 1 else (height - 3, height - 2)
        target_rows = (height - 3, height - 2) if direction == 1 else (1, 2)
        source = [(row, source_col) for row in source_rows]
        target = [(row, target_col) for row in target_rows]
        blocker = None
        if mode == "blocked_cross":
            blocker_row = rng.randint(5, height - 6) if direction == 1 else rng.randint(5, height - 6)
            blocker = blocker_row, source_col
    for row, col in source:
        grid[row][col] = 3
    for row, col in target:
        grid[row][col] = 2
    if blocker:
        grid[blocker[0]][blocker[1]] = 8
    clean = _extract_facts(grid)
    protected = set(clean["initial_leg"]) | set(source) | set(target)
    if blocker:
        protected.add(blocker)
    if mode != "aligned_target":
        cross_candidates = [cell for cell in clean["path"] if cell not in protected and grid[cell[0]][cell[1]] == 0]
        if not cross_candidates:
            raise AssertionError(f"no crossing cell for {profile}")
        for cell in (cross_candidates[len(cross_candidates) // 2],):
            grid[cell[0]][cell[1]] = 8
    desired_density = {None: 0.14, "easy": 0.08, "medium": 0.15, "hard": 0.22}[difficulty]
    candidates = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 0 and (row, col) not in protected
    ]
    rng.shuffle(candidates)
    desired = max(1, round(height * width * desired_density))
    existing = sum(value == 8 for values in grid for value in values)
    for row, col in candidates[: max(0, desired - existing)]:
        grid[row][col] = 8
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["scene_profile"] != profile:
        raise AssertionError((profile, analysis["errors"], analysis["scene_profile"]))
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = ctx.draw_choice("scene_profile", PUBLIC_PROFILES * 2 + GENERAL_PROFILES * 5)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general_scene(difficulty, profile, ctx.draw_rng("scene"))
