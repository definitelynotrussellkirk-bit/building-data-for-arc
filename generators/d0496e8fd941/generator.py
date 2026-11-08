"""Semantic generator for ARC task d0496e8fd941.

The selector is the nonzero color at the top-left cell.  The authoritative
rule segments the input into 4-connected monochrome objects.  Every selector-
colored object other than the object containing the selector cell is filled
inside its bounding rectangle *only when the object is exactly that rectangle's
perimeter*.  Other colors, broken selector outlines, touching/merged selector
frames, and the selector's own component are preserved.
"""
from __future__ import annotations

from collections import deque
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "d0496e8fd941"
TASK_ID = "d0496e8fd941"
VERSION = "3.0.0"
RULE_HASH = "20acc4020d08"
ALLOW_IDENTITY_OUTPUT = True
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Use the color at (0,0) as a selector.  For each other 4-connected "
    "object of that color, fill its bounding-box interior only when the "
    "object is exactly a complete rectangular perimeter; preserve all "
    "nonselected objects and malformed or merged selector-colored objects."
)

INVARIANTS = [
    "background is color 0 and (0,0) is a nonzero selector",
    "objects are 4-connected monochrome components",
    "a selected object is fillable iff it equals the full perimeter of its bounding rectangle",
    "the selector component itself is never filled",
    "other-colored frames and malformed or merged selected components are preserved",
    "ordinary three-demo lessons include both a positive fill and a selected-color non-frame counterexample",
]

PUBLIC_PROFILES = (
    "public_train_1",
    "public_train_2",
    "public_train_3",
    "public_train_4",
    "public_test_1",
)
GENERAL_PROFILES = (
    "selected_single",
    "selected_multiple",
    "adjacent_other_color",
    "valid_plus_touching_selected",
    "valid_plus_broken_selected",
    "selector_connected",
    "touching_selected_identity",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "scheduled positive, counterexample, reinforcement, then query",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_COLORS = tuple(range(1, 10))


def _decode(text: str) -> list[list[int]]:
    return [[int(value) for value in row] for row in text.split("/")]


# Exact visible canonical inputs.  They are accepted by self_check and can be
# requested explicitly, including the identity-output public test branch.
_PUBLIC_ROWS = (
    "2000000000/0000000000/0022227770/0020027070/0020027070/0022227070/0000007770/0000000000/0000000000/0000000000",
    "80000000000/00000000000/00888880000/00800084444/00800084004/00800084004/00888884004/00000004004/00000004444/00000000000/00000000000",
    "400000000000/000000000000/004444006660/004004006060/004004006060/004004006060/004444006060/000000006660/000000000000/000000000000",
    "700000000000/000000000000/007777700000/007000700000/007000700000/007000703333/007000703003/007777703003/000000003003/000000003333/000000000000/000000000000",
    "6000000000000/0000000000000/0066666000000/0060006044440/0060006040040/0060006040040/0060006040040/0066666040040/0666600040040/0600600044440/0666600000000/0000000000000",
)
_PUBLIC_INPUTS = {
    profile: _decode(text)
    for profile, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)
}
_PUBLIC_SIGNATURES = {
    tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()
}


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be nonempty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not (7 <= len(grid) <= 30 and 8 <= width <= 30):
        return ["grid dimensions must be within the supported 7..30 by 8..30 range"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be ARC integer colors 0..9"]
    return []


def _components(grid: list[list[int]]) -> tuple[dict[str, Any], ...]:
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    }
    records: list[dict[str, Any]] = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        queue = deque([start])
        cells: set[tuple[int, int]] = {start}
        while queue:
            row, col = queue.popleft()
            for dr, dc in _CARDINAL:
                neighbor = row + dr, col + dc
                if neighbor in unseen and grid[neighbor[0]][neighbor[1]] == color:
                    unseen.remove(neighbor)
                    cells.add(neighbor)
                    queue.append(neighbor)
        row0 = min(row for row, _ in cells)
        row1 = max(row for row, _ in cells)
        col0 = min(col for _, col in cells)
        col1 = max(col for _, col in cells)
        border = {
            (row, col)
            for row in range(row0, row1 + 1)
            for col in range(col0, col1 + 1)
            if row in (row0, row1) or col in (col0, col1)
        }
        frame = (
            row1 - row0 + 1 >= 3
            and col1 - col0 + 1 >= 3
            and cells == border
        )
        if not frame and cells < border and len(border - cells) <= 2:
            malformed_kind = "broken_border"
        elif not frame:
            malformed_kind = "compound"
        else:
            malformed_kind = None
        records.append(
            {
                "color": color,
                "cells": frozenset(cells),
                "bbox": (row0, col0, row1, col1),
                "border": frozenset(border),
                "is_frame": frame,
                "malformed_kind": malformed_kind,
                "contains_selector": (0, 0) in cells,
                "interior": tuple(
                    (row, col)
                    for row in range(row0 + 1, row1)
                    for col in range(col0 + 1, col1)
                ),
            }
        )
    return tuple(sorted(records, key=lambda record: min(record["cells"])))


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Input-pure Python mirror of the canonical Racket rule."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    target = grid[0][0]
    output = [list(row) for row in grid]
    for record in _components(grid):
        if (
            record["color"] == target
            and not record["contains_selector"]
            and record["is_frame"]
        ):
            for row, col in record["interior"]:
                output[row][col] = target
    return output


def _components_touch(left: dict[str, Any], right: dict[str, Any]) -> bool:
    right_cells = right["cells"]
    return any(
        (row + dr, col + dc) in right_cells
        for row, col in left["cells"]
        for dr, dc in _CARDINAL
    )


def _extract_facts(grid: list[list[int]]) -> dict[str, Any]:
    target = grid[0][0]
    records = _components(grid)
    marker_records = tuple(record for record in records if record["contains_selector"])
    marker = marker_records[0] if marker_records else None
    selected_valid = tuple(
        record
        for record in records
        if record["color"] == target
        and not record["contains_selector"]
        and record["is_frame"]
    )
    selected_invalid = tuple(
        record
        for record in records
        if record["color"] == target
        and not record["contains_selector"]
        and not record["is_frame"]
    )
    decoy_frames = tuple(
        record
        for record in records
        if record["color"] != target and record["is_frame"]
    )
    other_invalid = tuple(
        record
        for record in records
        if record["color"] != target and not record["is_frame"]
    )
    adjacent_other = any(
        _components_touch(selected, decoy)
        for selected in selected_valid
        for decoy in decoy_frames
    )
    output = rule_mirror(grid)
    changed = tuple(
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if output[row][col] != grid[row][col]
    )
    profile = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if profile is None:
        marker_size = len(marker["cells"]) if marker else 0
        broken = sum(
            record["malformed_kind"] == "broken_border"
            for record in selected_invalid
        )
        compound = sum(
            record["malformed_kind"] == "compound"
            for record in selected_invalid
        )
        if marker_size > 1 and selected_valid and decoy_frames and not selected_invalid:
            profile = "selector_connected"
        elif marker_size == 1 and not selected_valid and compound and decoy_frames:
            profile = "touching_selected_identity"
        elif marker_size == 1 and selected_valid and compound and not broken:
            profile = "valid_plus_touching_selected"
        elif marker_size == 1 and selected_valid and broken and not compound:
            profile = "valid_plus_broken_selected"
        elif marker_size == 1 and len(selected_valid) >= 2 and not selected_invalid and decoy_frames:
            profile = "selected_multiple"
        elif marker_size == 1 and len(selected_valid) == 1 and not selected_invalid and decoy_frames and adjacent_other:
            profile = "adjacent_other_color"
        elif marker_size == 1 and len(selected_valid) == 1 and not selected_invalid and decoy_frames and not adjacent_other:
            profile = "selected_single"
    return {
        "target": target,
        "records": records,
        "marker": marker,
        "selected_valid": selected_valid,
        "selected_invalid": selected_invalid,
        "decoy_frames": decoy_frames,
        "other_invalid": other_invalid,
        "adjacent_other": adjacent_other,
        "changed": changed,
        "changed_count": len(changed),
        "output": output,
        "scene_profile": profile,
    }


def _profile_errors(facts: dict[str, Any]) -> list[str]:
    profile = facts["scene_profile"]
    errors: list[str] = []
    marker = facts["marker"]
    if marker is None:
        errors.append("selector cell is not part of a nonzero component")
        return errors
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared selected-frame lesson")
        return errors
    if profile in PUBLIC_PROFILES:
        return errors
    if facts["other_invalid"]:
        errors.append("nonselector colors must form complete frame distractors")
    if any(
        any(facts["output"][row][col] == facts["target"] for row, col in record["interior"])
        and any(
            facts["output"][row][col] != facts["target"]
            for row, col in record["interior"]
        )
        for record in facts["selected_valid"]
    ):
        errors.append("a selected frame interior was only partially filled")
    if profile == "selected_single":
        if len(facts["selected_valid"]) != 1 or facts["selected_invalid"] or facts["adjacent_other"]:
            errors.append("selected_single requires one isolated valid selected frame")
    elif profile == "selected_multiple":
        if len(facts["selected_valid"]) < 2 or facts["selected_invalid"]:
            errors.append("selected_multiple requires at least two valid selected frames")
    elif profile == "adjacent_other_color":
        if len(facts["selected_valid"]) != 1 or not facts["adjacent_other"]:
            errors.append("adjacent_other_color requires one selected frame touching a different-color frame")
    elif profile == "valid_plus_touching_selected":
        if not facts["selected_valid"] or not any(
            record["malformed_kind"] == "compound"
            for record in facts["selected_invalid"]
        ):
            errors.append("valid_plus_touching_selected requires both a valid frame and a merged selected component")
    elif profile == "valid_plus_broken_selected":
        if not facts["selected_valid"] or not any(
            record["malformed_kind"] == "broken_border"
            for record in facts["selected_invalid"]
        ):
            errors.append("valid_plus_broken_selected requires both a valid frame and a broken selected outline")
    elif profile == "selector_connected":
        if len(marker["cells"]) <= 1 or not facts["selected_valid"]:
            errors.append("selector_connected requires a nontrivial selector component plus a separate valid frame")
    elif profile == "touching_selected_identity":
        if facts["selected_valid"] or facts["changed_count"] != 0:
            errors.append("touching_selected_identity must contain no fillable selected component")
    if profile != "touching_selected_identity" and facts["changed_count"] == 0:
        errors.append("nonidentity profiles must visibly fill at least one selected interior")
    if not facts["decoy_frames"]:
        errors.append("every generated lesson needs a complete nonselector frame distractor")
    return errors


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors, "facts": None, "scene_profile": None}
    target = grid[0][0]
    if target == 0:
        errors.append("selector at (0,0) must be nonzero")
        return {"errors": errors, "facts": None, "scene_profile": None}
    facts = _extract_facts(grid)
    errors.extend(_profile_errors(facts))
    # All accepted canonical/general lessons use empty interiors before the
    # fill.  This keeps the curriculum faithful to the visible task rather
    # than teaching an unobserved overwrite generalization.
    for record in facts["selected_valid"]:
        if any(grid[row][col] != 0 for row, col in record["interior"]):
            errors.append("selected frame interiors must start empty")
            break
    flat = [value for row in grid for value in row]
    if flat.count(0) <= max((flat.count(color) for color in set(flat) if color != 0), default=0):
        errors.append("background 0 must be the unique modal color")
    return {
        "errors": errors,
        "facts": facts,
        "scene_profile": facts["scene_profile"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-prone lessons; accept all canonical inputs."""
    return _analysis(grid)["errors"]


def observe_overrides(grid) -> dict[str, str]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {"scene_profile": analysis["scene_profile"]}


def _draw_frame(
    grid: list[list[int]],
    row0: int,
    col0: int,
    frame_h: int,
    frame_w: int,
    color: int,
) -> tuple[int, int, int, int]:
    row1, col1 = row0 + frame_h - 1, col0 + frame_w - 1
    for row in range(row0, row1 + 1):
        grid[row][col0] = color
        grid[row][col1] = color
    for col in range(col0, col1 + 1):
        grid[row0][col] = color
        grid[row1][col] = color
    return row0, col0, row1, col1


def _canvas(difficulty: str | None, profile: str, rng) -> tuple[int, int]:
    minimums = {
        "selected_single": (9, 13),
        "selected_multiple": (14, 18),
        "adjacent_other_color": (10, 14),
        "valid_plus_touching_selected": (15, 21),
        "valid_plus_broken_selected": (13, 20),
        "selector_connected": (14, 20),
        "touching_selected_identity": (13, 17),
    }
    bands = {
        None: ((12, 20), (15, 24)),
        "easy": ((9, 15), (13, 20)),
        "medium": ((13, 21), (17, 26)),
        "hard": ((18, 27), (22, 30)),
    }
    (h0, h1), (w0, w1) = bands[difficulty]
    min_h, min_w = minimums[profile]
    h0, w0 = max(h0, min_h), max(w0, min_w)
    return rng.randint(h0, max(h0, h1)), rng.randint(w0, max(w0, w1))


def _colors(rng) -> tuple[int, int, int]:
    return tuple(rng.sample(_COLORS, 3))


def _selected_single(difficulty, rng):
    height, width = _canvas(difficulty, "selected_single", rng)
    target, decoy, _ = _colors(rng)
    grid = full_grid(height, width, 0)
    grid[0][0] = target
    target_h = rng.randint(3, min(7, height - 3))
    target_w = rng.randint(3, min(7, max(3, width // 2 - 2)))
    target_row = rng.randint(2, height - target_h - 1)
    target_col = rng.randint(2, max(2, width // 2 - target_w))
    _draw_frame(grid, target_row, target_col, target_h, target_w, target)
    decoy_h = rng.randint(3, min(7, height - 2))
    decoy_w = rng.randint(3, min(7, max(3, width - (width // 2 + 2))))
    decoy_row = rng.randint(1, height - decoy_h)
    decoy_col = width - decoy_w
    _draw_frame(grid, decoy_row, decoy_col, decoy_h, decoy_w, decoy)
    return grid


def _selected_multiple(difficulty, rng):
    height, width = _canvas(difficulty, "selected_multiple", rng)
    target, decoy, _ = _colors(rng)
    grid = full_grid(height, width, 0)
    grid[0][0] = target
    h1, w1 = rng.randint(3, 5), rng.randint(3, 6)
    h2, w2 = rng.randint(3, 5), rng.randint(3, 6)
    _draw_frame(grid, 2, 2, h1, w1, target)
    _draw_frame(grid, height - h2 - 1, 2, h2, w2, target)
    dh, dw = rng.randint(4, min(7, height - 2)), rng.randint(3, min(7, width - 10))
    _draw_frame(grid, rng.randint(1, height - dh), width - dw - 1, dh, dw, decoy)
    return grid


def _adjacent_other_color(difficulty, rng):
    height, width = _canvas(difficulty, "adjacent_other_color", rng)
    target, decoy, _ = _colors(rng)
    grid = full_grid(height, width, 0)
    grid[0][0] = target
    fh = rng.randint(4, min(7, height - 3))
    fw = rng.randint(3, min(6, (width - 3) // 2))
    dw = rng.randint(3, min(6, width - fw - 3))
    row = rng.randint(2, height - fh - 1)
    col = rng.randint(2, width - fw - dw - 1)
    _draw_frame(grid, row, col, fh, fw, target)
    _draw_frame(grid, row, col + fw, fh, dw, decoy)
    return grid


def _compound_pair(grid, row, col, target, rng):
    first_h, first_w = rng.randint(4, 6), rng.randint(4, 6)
    second_h, second_w = rng.randint(3, 5), rng.randint(4, 6)
    _draw_frame(grid, row, col, first_h, first_w, target)
    # The second frame begins one row below the first frame's bottom and
    # overlaps columns, creating a single non-rectangular 4-connected object.
    second_row = row + first_h
    second_col = max(1, col - 1)
    _draw_frame(grid, second_row, second_col, second_h, second_w, target)
    return second_row + second_h - 1, max(col + first_w - 1, second_col + second_w - 1)


def _valid_plus_touching(difficulty, rng):
    height, width = _canvas(difficulty, "valid_plus_touching_selected", rng)
    target, decoy, _ = _colors(rng)
    grid = full_grid(height, width, 0)
    grid[0][0] = target
    valid_h, valid_w = rng.randint(4, 7), rng.randint(3, 6)
    _draw_frame(grid, height - valid_h - 1, 2, valid_h, valid_w, target)
    compound_col = max(10, width - 8)
    bottom, right = _compound_pair(grid, 2, compound_col, target, rng)
    dh, dw = 3, 3
    decoy_row = min(height - dh, max(1, bottom - dh + 1))
    decoy_col = max(valid_w + 4, min(width - dw, compound_col - dw - 1))
    _draw_frame(grid, decoy_row, decoy_col, dh, dw, decoy)
    return grid


def _valid_plus_broken(difficulty, rng):
    height, width = _canvas(difficulty, "valid_plus_broken_selected", rng)
    target, decoy, _ = _colors(rng)
    grid = full_grid(height, width, 0)
    grid[0][0] = target
    vh, vw = rng.randint(4, 7), rng.randint(3, 6)
    _draw_frame(grid, rng.randint(2, height - vh - 1), 2, vh, vw, target)
    bh, bw = rng.randint(4, min(7, height - 3)), rng.randint(4, 7)
    br = rng.randint(2, height - bh - 1)
    bc = width - bw - 1
    _draw_frame(grid, br, bc, bh, bw, target)
    gap_col = bc + rng.randint(1, bw - 2)
    grid[br][gap_col] = 0
    dh, dw = 3, 3
    _draw_frame(grid, height - dh, max(vw + 4, width // 2 - 1), dh, dw, decoy)
    return grid


def _selector_connected(difficulty, rng):
    height, width = _canvas(difficulty, "selector_connected", rng)
    target, decoy, _ = _colors(rng)
    grid = full_grid(height, width, 0)
    grid[0][0] = target
    # A target-colored frame is connected to the selector by an L-shaped path;
    # the whole component is excluded by the official rule.
    connected_h, connected_w = 4, rng.randint(4, 6)
    connected_row, connected_col = 2, 2
    _draw_frame(grid, connected_row, connected_col, connected_h, connected_w, target)
    for col in range(0, connected_col + 1):
        grid[0][col] = target
    for row in range(0, connected_row + 1):
        grid[row][connected_col] = target
    valid_h, valid_w = rng.randint(4, 7), rng.randint(3, 6)
    _draw_frame(grid, height - valid_h - 1, 2, valid_h, valid_w, target)
    dh, dw = rng.randint(3, 5), rng.randint(3, 5)
    _draw_frame(grid, height - dh - 1, width - dw - 1, dh, dw, decoy)
    return grid


def _touching_identity(difficulty, rng):
    height, width = _canvas(difficulty, "touching_selected_identity", rng)
    target, decoy, _ = _colors(rng)
    grid = full_grid(height, width, 0)
    grid[0][0] = target
    _compound_pair(grid, 2, 2, target, rng)
    dh, dw = rng.randint(4, min(7, height - 2)), rng.randint(3, min(6, width - 11))
    _draw_frame(grid, rng.randint(1, height - dh), width - dw - 1, dh, dw, decoy)
    return grid


def _candidate(profile: str, difficulty: str | None, rng) -> list[list[int]]:
    if profile == "selected_single":
        return _selected_single(difficulty, rng)
    if profile == "selected_multiple":
        return _selected_multiple(difficulty, rng)
    if profile == "adjacent_other_color":
        return _adjacent_other_color(difficulty, rng)
    if profile == "valid_plus_touching_selected":
        return _valid_plus_touching(difficulty, rng)
    if profile == "valid_plus_broken_selected":
        return _valid_plus_broken(difficulty, rng)
    if profile == "selector_connected":
        return _selector_connected(difficulty, rng)
    if profile == "touching_selected_identity":
        return _touching_identity(difficulty, rng)
    raise ValueError(f"unknown scene_profile: {profile!r}")


_SLOT_POOLS = {
    0: ("selected_single", "selected_multiple", "adjacent_other_color"),
    1: (
        "valid_plus_touching_selected",
        "valid_plus_broken_selected",
        "selector_connected",
    ),
    2: ("selected_multiple", "adjacent_other_color", "selected_single"),
    3: tuple(profile for profile in GENERAL_PROFILES if profile != "touching_selected_identity"),
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic selected-frame lesson with exact profile replay."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
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
    options = SCENE_PROFILES if "scene_profile" in overrides else _SLOT_POOLS[int(sample_index) % 4]
    profile = ctx.draw_choice("scene_profile", options)
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    rng = ctx.draw_rng("geometry")
    for _ in range(80):
        grid = _candidate(profile, difficulty, rng)
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct valid scene_profile={profile!r}")
