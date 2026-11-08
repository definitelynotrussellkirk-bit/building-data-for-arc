"""Generator for ARC task 65d8d5108df1.

The top ``h - 3`` rows form a library of uniquely colored templates.  The
bottom rows encode template ID, transform code, and output color by column.
Commands are decoded left-to-right; each selected template is cropped,
transformed, recolored, and horizontally stacked with one-column gaps while
being vertically centered.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "65d8d5108df1"
TASK_ID = "65d8d5108df1"
VERSION = "3.0.0"
RULE_HASH = "d178b58b9106"

SUMMARY = (
    "A black grid contains a top library of 2–5 connected templates, each in a "
    "unique color that serves as its ID. The last three rows contain commands: "
    "template ID, transform code (1 identity, 2 clockwise, 3 half-turn, "
    "4 left-right flip, 5 up-down flip, 6 counterclockwise), and output color. "
    "Decode nonzero command columns from left to right, crop the named template, "
    "transform and recolor it, then stack all pieces horizontally with one black "
    "column between them and vertical center alignment."
)

INVARIANTS = [
    "the grid is 9..16 by 10..20 with ARC colors",
    "the top h-3 rows contain 2..5 connected templates with unique color IDs",
    "the final three rows are aligned ID, transform, and output-color commands",
    "1..5 command columns are active and inactive columns are all-zero",
    "every command references a library ID, uses transform 1..6, and a nonzero color",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware rng 9..16", "valid": "9..16"},
    "grid_w": {"type": "int", "default": "difficulty-aware rng 10..20", "valid": "10..20"},
    "n_templates": {"type": "int", "default": "difficulty-aware rng 2..5", "valid": "2..5"},
    "n_commands": {"type": "int", "default": "difficulty-aware rng 1..5", "valid": "1..5"},
}

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = (4, 5, 6)
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# The first shape is a deliberately asymmetric probe. The first command always
# references it, so codes 4/5/6 and the historical prose mapping are observable.
_PROBE_SHAPE = ((0, 0), (1, 0), (1, 1), (1, 2))
_SHAPES = (
    _PROBE_SHAPE,
    ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
)


def _validate_difficulty(difficulty: Any) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_call_indices(seed: Any, sample_index: Any) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")


def schedule_profile(seed, sample_index, difficulty=None):
    """The first command cycles through canonical codes 4, 5, and 6."""
    del seed
    _validate_difficulty(difficulty)
    offset = {None: 0, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    return SCHEDULE_PROFILES[(int(sample_index) + offset) % 3]


def _shape_errors(grid: Any) -> tuple[list[str], int, int]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"], 0, 0
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"], len(grid), 0
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if not 9 <= h <= 16:
        errors.append(f"grid height {h} outside 9..16")
    if not 10 <= w <= 20:
        errors.append(f"grid width {w} outside 10..20")
    for r, row in enumerate(grid):
        if not isinstance(row, list) or len(row) != w:
            errors.append("grid rows must be non-empty and rectangular")
            break
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")
    return errors, h, w


def _objects(grid: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            result.append(
                {
                    "color": color,
                    "cells": cells,
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return result


def _analysis(grid: Any) -> dict[str, Any]:
    errors, h, w = _shape_errors(grid)
    if errors:
        return {"errors": errors, "grid_h": h, "grid_w": w}

    library = [row[:] for row in grid[: h - 3]]
    objects = _objects(library)
    if not 2 <= len(objects) <= 5:
        errors.append(f"expected 2..5 library objects, got {len(objects)}")
    colors = [obj["color"] for obj in objects]
    if len(set(colors)) != len(colors):
        errors.append("each library color must identify exactly one connected template")

    ids_row, transforms_row, colors_row = grid[h - 3], grid[h - 2], grid[h - 1]
    active = [c for c, template_id in enumerate(ids_row) if template_id != 0]
    if not 1 <= len(active) <= 5:
        errors.append(f"expected 1..5 active command columns, got {len(active)}")
    inactive_payload = [
        c
        for c, template_id in enumerate(ids_row)
        if template_id == 0 and (transforms_row[c] != 0 or colors_row[c] != 0)
    ]
    if inactive_payload:
        errors.append(f"inactive command columns carry payload: {inactive_payload}")

    known = set(colors)
    missing = sorted({ids_row[c] for c in active if ids_row[c] not in known})
    if missing:
        errors.append(f"commands reference missing template IDs: {missing}")
    bad_transforms = sorted({transforms_row[c] for c in active if transforms_row[c] not in range(1, 7)})
    if bad_transforms:
        errors.append(f"command transforms outside 1..6: {bad_transforms}")
    bad_colors = sorted({colors_row[c] for c in active if colors_row[c] not in range(1, 10)})
    if bad_colors:
        errors.append(f"command output colors outside 1..9: {bad_colors}")

    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "library": library,
        "objects": objects,
        "active": active,
        "ids_row": ids_row,
        "transforms_row": transforms_row,
        "colors_row": colors_row,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n_templates": len(analysis["objects"]),
        "n_commands": len(analysis["active"]),
    }


def _crop_object(library: list[list[int]], obj: dict[str, Any]) -> list[list[int]]:
    r0, c0, r1, c1 = obj["bbox"]
    return [row[c0 : c1 + 1] for row in library[r0 : r1 + 1]]


def _crop_nonzero(grid: list[list[int]]) -> list[list[int]]:
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]
    if not cells:
        return [[0]]
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def _rotate_cw(grid):
    return [list(row) for row in zip(*reversed(grid))]


def _rotate_180(grid):
    return [list(reversed(row)) for row in reversed(grid)]


def _flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid):
    return [row[:] for row in reversed(grid)]


def _rotate_ccw(grid):
    return [list(row) for row in reversed(list(zip(*grid)))]


_CANONICAL_TRANSFORMS: dict[int, Callable[[list[list[int]]], list[list[int]]]] = {
    1: lambda grid: [row[:] for row in grid],
    2: _rotate_cw,
    3: _rotate_180,
    4: _flip_lr,
    5: _flip_ud,
    6: _rotate_ccw,
}

# This is the table implied by the old prose: code 4 was claimed as CCW, code 5
# as LR flip, and code 6 was omitted. Keeping it as a rival makes the corrected
# source table executable evidence rather than prose only.
_LEGACY_TRANSFORMS: dict[int, Callable[[list[list[int]]], list[list[int]]]] = {
    1: lambda grid: [row[:] for row in grid],
    2: _rotate_cw,
    3: _rotate_180,
    4: _rotate_ccw,
    5: _flip_lr,
    6: _flip_ud,
}


def _recolor(grid: list[list[int]], color: int) -> list[list[int]]:
    return [[color if value != 0 else 0 for value in row] for row in grid]


def _hstack_center(parts: list[list[list[int]]], *, top_align: bool = False) -> list[list[int]]:
    if not parts:
        return [[]]
    height = max(len(part) for part in parts)
    width = sum(len(part[0]) for part in parts) + len(parts) - 1
    output = full_grid(height, width, 0)
    left = 0
    for part in parts:
        top = 0 if top_align else (height - len(part)) // 2
        for r, row in enumerate(part):
            for c, value in enumerate(row):
                if value != 0:
                    output[top + r][left + c] = value
        left += len(part[0]) + 1
    return output


def _solve(
    grid: list[list[int]],
    *,
    transforms: dict[int, Callable[[list[list[int]]], list[list[int]]]] = _CANONICAL_TRANSFORMS,
    apply_transform: bool = True,
    apply_recolor: bool = True,
) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    objects_by_color = {obj["color"]: obj for obj in analysis["objects"]}
    parts: list[list[list[int]]] = []
    for c in analysis["active"]:
        template_id = analysis["ids_row"][c]
        part = _crop_object(analysis["library"], objects_by_color[template_id])
        code = analysis["transforms_row"][c]
        if apply_transform:
            part = transforms[code](part)
        if apply_recolor:
            part = _recolor(part, analysis["colors_row"][c])
        parts.append(_crop_nonzero(part))
    return _hstack_center(parts)


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    return _solve(grid)


def _draw_axis(ctx, label: str, full_bounds: tuple[int, int], difficulty_bounds, difficulty):
    if ctx.overrides.get(label) is not None:
        lo, hi = full_bounds
    else:
        lo, hi = difficulty_bounds[difficulty]
    return ctx.draw_int_strict(label, lo, hi)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call_indices(seed, sample_index)
    _validate_difficulty(difficulty)
    unknown = set(overrides) - set(AXES)
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
    h = _draw_axis(
        ctx,
        "grid_h",
        (9, 16),
        {None: (10, 13), "easy": (9, 11), "medium": (11, 14), "hard": (13, 16)},
        difficulty,
    )
    w = _draw_axis(
        ctx,
        "grid_w",
        (10, 20),
        {None: (12, 16), "easy": (10, 13), "medium": (13, 17), "hard": (15, 20)},
        difficulty,
    )
    n_templates = _draw_axis(
        ctx,
        "n_templates",
        (2, 5),
        {None: (3, 4), "easy": (2, 3), "medium": (3, 4), "hard": (4, 5)},
        difficulty,
    )
    n_commands = _draw_axis(
        ctx,
        "n_commands",
        (1, 5),
        {None: (2, 4), "easy": (1, 3), "medium": (2, 4), "hard": (4, 5)},
        difficulty,
    )

    library_h = h - 3
    slots = [
        (r0, c0)
        for r0 in range(0, library_h - 2, 3)
        for c0 in range(0, w - 2, 3)
    ]
    if len(slots) < n_templates:
        raise ValueError(
            f"grid {h}x{w} exposes only {len(slots)} 3x3 library slots for "
            f"n_templates={n_templates}"
        )

    library_rng = ctx.draw_rng("library")
    library_rng.shuffle(slots)
    template_ids = library_rng.sample(range(1, 10), n_templates)
    remaining_shapes = list(_SHAPES[1:])
    library_rng.shuffle(remaining_shapes)
    shapes = [_PROBE_SHAPE, *remaining_shapes[: n_templates - 1]]

    grid = full_grid(h, w, 0)
    for template_id, shape, (r0, c0) in zip(template_ids, shapes, slots):
        for dr, dc in shape:
            grid[r0 + dr][c0 + dc] = template_id

    command_rng = ctx.draw_rng("commands")
    columns = sorted(command_rng.sample(range(w), n_commands))
    first_code = schedule_profile(seed, sample_index, difficulty)
    for ordinal, c in enumerate(columns):
        template_id = template_ids[0] if ordinal == 0 else command_rng.choice(template_ids)
        code = first_code if ordinal == 0 else ((first_code + ordinal - 1) % 6) + 1
        output_color = command_rng.choice([color for color in range(1, 10) if color != template_id])
        grid[h - 3][c] = template_id
        grid[h - 2][c] = code
        grid[h - 1][c] = output_color

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid library lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    requested = ctx.recorded_draws()
    for axis in AXES:
        if observed.get(axis) != requested.get(axis):
            raise AssertionError(
                f"axis {axis!r} requested {requested.get(axis)!r}, "
                f"observed {observed.get(axis)!r}"
            )
    return grid


def _rival_no_transform(grid):
    return _solve(grid, apply_transform=False)


def _rival_legacy_code_table(grid):
    return _solve(grid, transforms=_LEGACY_TRANSFORMS)


def _rival_keep_library_colors(grid):
    return _solve(grid, apply_recolor=False)


SEMANTIC_RIVALS = {
    "no_transform": _rival_no_transform,
    "legacy_code_table": _rival_legacy_code_table,
    "keep_library_colors": _rival_keep_library_colors,
}

SEMANTIC_WITNESSES = {
    "transform_required": lambda grid: _rival_no_transform(grid) != rule_mirror(grid),
    "canonical_code_table": lambda grid: _rival_legacy_code_table(grid) != rule_mirror(grid),
    "recolor_required": lambda grid: _rival_keep_library_colors(grid) != rule_mirror(grid),
}

WITNESS_RIVALS = {
    "transform_required": ["no_transform"],
    "canonical_code_table": ["legacy_code_table"],
    "recolor_required": ["keep_library_colors"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    errors: list[str] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            errors.append(f"demo {index} must contain input and output")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            errors.append(f"demo {index} output does not match the canonical rule")
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        errors.append("query must contain input and output")
    elif query["output"] != rule_mirror(query["input"]):
        errors.append("query output does not match the canonical rule")
    if errors:
        return errors

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            errors.append(f"demonstrations do not eliminate rival {name!r}")
    return errors
