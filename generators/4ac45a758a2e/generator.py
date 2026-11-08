"""Generator for ``arc_additional_puzzle_bank_volume8:H54``.

A magenta object is a template.  The number of blue cells selects a clockwise
rotation (1 -> 0 degrees, ..., 4 -> 270 degrees); the number of red cells
selects whether the rotated template is horizontally reflected (1 -> no,
2 -> yes).  The transformed template is stamped in cyan with its normalized
bounding-box origin at the orange anchor.

Ordinary lessons schedule all eight (rotation, reflection) combinations over
consecutive sample indexes.  Template area advances on an independent
four-cycle so it cannot replace the blue rotation control; shapes and
placements also vary while retaining the canonical control strips and fixed
ARC colour roles.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4ac45a758a2e"
VERSION = "3.1.0"
TASK_ID = "4ac45a758a2e"
RULE_HASH = "6259c8fd93a1"
EXAMPLES_NEEDED = 8

SUMMARY = (
    "Count blue(1) cells to choose 0/90/180/270 degrees clockwise, then count "
    "red(2) cells to choose no horizontal reflection/reflection. Normalize the "
    "magenta(6) template after each transform and stamp it in cyan(8) at the "
    "orange(7) anchor, preserving the rest of the input."
)

INVARIANTS = [
    "1..4 blue controls form a contiguous strip ending at the top-right corner",
    "1..2 red controls form a contiguous strip ending at the bottom-left corner",
    "one 4-connected magenta template has 4..7 cells and a two-dimensional bbox",
    "one orange anchor is the normalized origin of an in-bounds, collision-free stamp",
    "ordinary templates expose all eight rotation/reflection views",
    "ordinary template area varies independently of the blue rotation count",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile schedule or keyed 11..17",
        "valid": "11..17",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile schedule or keyed 11..17",
        "valid": "11..17",
    },
    "rot_count": {
        "type": "int",
        "default": "1 + sample_index mod 4",
        "valid": "1..4",
    },
    "ref_count": {
        "type": "int",
        "default": "1 for residues 0..3, 2 for residues 4..7",
        "valid": "1..2",
    },
    "template_cells": {
        "type": "int",
        "default": "32-residue orthogonal schedule over 4..7",
        "valid": "4..7",
    },
}

_PROFILE_ORDER = (
    (1, 1),
    (2, 1),
    (3, 1),
    (4, 1),
    (1, 2),
    (2, 2),
    (3, 2),
    (4, 2),
)
_CANONICAL_DIMS = ((13, 11), (11, 13), (12, 11), (11, 11), (13, 13))
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _normalize(cells: list[tuple[int, int]] | tuple[tuple[int, int], ...]):
    rows = [row for row, _col in cells]
    cols = [col for _row, col in cells]
    top, left = min(rows), min(cols)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _rotate_cw(cells):
    normalized = _normalize(cells)
    height = max(row for row, _col in normalized) + 1
    return _normalize([(col, height - 1 - row) for row, col in normalized])


def _flip_horizontal(cells):
    normalized = _normalize(cells)
    width = max(col for _row, col in normalized) + 1
    return _normalize([(row, width - 1 - col) for row, col in normalized])


def _transform(cells, rot_count: int, ref_count: int):
    transformed = _normalize(cells)
    for _ in range(rot_count - 1):
        transformed = _rotate_cw(transformed)
    if ref_count == 2:
        transformed = _flip_horizontal(transformed)
    return _normalize(transformed)


def _all_views(cells) -> set[tuple[tuple[int, int], ...]]:
    views: set[tuple[tuple[int, int], ...]] = set()
    current = _normalize(cells)
    for _ in range(4):
        views.add(current)
        views.add(_flip_horizontal(current))
        current = _rotate_cw(current)
    return views


def _scheduled_profile(sample_index: int) -> tuple[int, int]:
    return _PROFILE_ORDER[int(sample_index) % len(_PROFILE_ORDER)]


def _scheduled_template_cells(sample_index: int, band_shift: int) -> int:
    """Vary area independently across repeats of each control profile.

    Controls repeat every eight indexes.  Advancing the area phase on each
    repeat gives every rotation all four areas over 32 indexes, while the
    reflection half-cycle creates collisions inside each eight-demo lesson.
    Consequently a lookup from template area to rotation is contradicted by
    the demonstrations or by the same-profile query eight indexes later.
    """
    profile_index = int(sample_index) % len(_PROFILE_ORDER)
    cycle_index = (int(sample_index) // len(_PROFILE_ORDER)) % 4
    rotation_index = profile_index % 4
    reflection_index = profile_index // 4
    return 4 + (
        (rotation_index + reflection_index + cycle_index + int(band_shift)) % 4
    )


def _draw_axis(ctx, axis: str, lo: int, hi: int, scheduled: int) -> int:
    if axis in ctx.overrides and ctx.overrides[axis] is not None:
        return ctx.draw_int(axis, lo, hi)
    return ctx.draw_choice(axis, [scheduled])


def _build_template(cell_count: int, rng) -> tuple[tuple[int, int], ...]:
    """Build a small connected polyomino with eight distinct dihedral views."""
    for _attempt in range(512):
        cells = {(0, 0)}
        while len(cells) < cell_count:
            frontier = sorted(
                {
                    (row + drow, col + dcol)
                    for row, col in cells
                    for drow, dcol in _DIR4
                    if (row + drow, col + dcol) not in cells
                }
            )
            cells.add(rng.choice(frontier))
        normalized = _normalize(list(cells))
        height = max(row for row, _col in normalized) + 1
        width = max(col for _row, col in normalized) + 1
        if height < 2 or width < 2 or height > 4 or width > 4:
            continue
        if len(_all_views(normalized)) == 8:
            return normalized
    raise RuntimeError(
        f"could not construct an asymmetric connected {cell_count}-cell template"
    )


def _choose_template_origin(
    height: int,
    width: int,
    template,
    rng,
    *,
    canonical_layout: bool,
) -> tuple[int, int]:
    template_h = max(row for row, _col in template) + 1
    template_w = max(col for _row, col in template) + 1
    max_row = min(height // 2 - template_h, height - template_h - 5)
    max_col = min(width // 2 - template_w, width - template_w - 5)
    if max_row < 1 or max_col < 1:
        raise RuntimeError("grid cannot separate template and anchor zones")
    if canonical_layout:
        candidates = [
            (row, col)
            for row in range(1, min(2, max_row) + 1)
            for col in range(1, min(2, max_col) + 1)
        ]
    else:
        candidates = [
            (row, col)
            for row in range(1, max_row + 1)
            for col in range(1, max_col + 1)
        ]
    return rng.choice(candidates)


def _choose_anchor(
    grid: list[list[int]],
    transformed,
    template_bottom: int,
    template_right: int,
    rng,
) -> tuple[int, int]:
    height, width = len(grid), len(grid[0])
    shape_h = max(row for row, _col in transformed) + 1
    shape_w = max(col for _row, col in transformed) + 1
    candidates = []
    for row in range(max(template_bottom + 2, height // 2), height - shape_h + 1):
        for col in range(max(template_right + 2, width // 2), width - shape_w + 1):
            targets = [(row + drow, col + dcol) for drow, dcol in transformed]
            if all(grid[target_row][target_col] == 0 for target_row, target_col in targets):
                candidates.append((row, col))
    if not candidates:
        raise RuntimeError("no collision-free anchor for transformed template")
    return rng.choice(candidates)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; Racket remains output authority."""
    band = difficulty if difficulty in {"easy", "medium", "hard"} else "medium"
    band_shift = {"easy": 0, "medium": 1, "hard": 2}[band]
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    scheduled_rot, scheduled_ref = _scheduled_profile(sample_index)
    rot_count = _draw_axis(ctx, "rot_count", 1, 4, scheduled_rot)
    ref_count = _draw_axis(ctx, "ref_count", 1, 2, scheduled_ref)

    canonical_layout = not overrides and int(sample_index) % 3 != 2
    if canonical_layout:
        scheduled_h, scheduled_w = _CANONICAL_DIMS[
            (int(sample_index) + band_shift) % len(_CANONICAL_DIMS)
        ]
        height = ctx.draw_choice("grid_h", [scheduled_h])
        width = ctx.draw_choice("grid_w", [scheduled_w])
    else:
        height = ctx.draw_int("grid_h", 11, 17)
        width = ctx.draw_int("grid_w", 11, 17)

    if "template_cells" in overrides and overrides["template_cells"] is not None:
        template_cells = ctx.draw_int("template_cells", 4, 7)
    else:
        scheduled_cells = _scheduled_template_cells(sample_index, band_shift)
        template_cells = ctx.draw_choice("template_cells", [scheduled_cells])
    template = _build_template(template_cells, ctx.draw_rng("template_shape"))
    transformed = _transform(template, rot_count, ref_count)

    grid = full_grid(height, width, 0)
    for index in range(rot_count):
        grid[0][width - 1 - index] = 1
    for index in range(ref_count):
        grid[height - 1 - index][0] = 2

    layout_rng = ctx.draw_rng("layout")
    template_row, template_col = _choose_template_origin(
        height,
        width,
        template,
        layout_rng,
        canonical_layout=canonical_layout,
    )
    for row, col in template:
        grid[template_row + row][template_col + col] = 6
    template_bottom = template_row + max(row for row, _col in template)
    template_right = template_col + max(col for _row, col in template)

    anchor_row, anchor_col = _choose_anchor(
        grid,
        transformed,
        template_bottom,
        template_right,
        layout_rng,
    )
    grid[anchor_row][anchor_col] = 7
    return grid


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen: set[tuple[int, int]] = set()
    queue = deque([next(iter(cells))])
    while queue:
        cell = queue.popleft()
        if cell in seen:
            continue
        seen.add(cell)
        row, col = cell
        for drow, dcol in _DIR4:
            neighbor = (row + drow, col + dcol)
            if neighbor in cells and neighbor not in seen:
                queue.append(neighbor)
    return seen == cells


def _analyze(grid: Any) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {}, ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return {}, ["grid must be rectangular and nonempty"]
    height = len(grid)
    if not 11 <= height <= 17:
        errors.append(f"height must be in 11..17, got {height}")
    if not 11 <= width <= 17:
        errors.append(f"width must be in 11..17, got {width}")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("all cells must be integer ARC colours 0..9")
        return {}, errors

    palette = {value for row in grid for value in row}
    if not palette <= {0, 1, 2, 6, 7}:
        errors.append(f"unexpected input colours {sorted(palette - {0, 1, 2, 6, 7})}")

    blue = [(row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value == 1]
    red = [(row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value == 2]
    template_cells = {(row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value == 6}
    anchors = [(row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value == 7]

    if not 1 <= len(blue) <= 4:
        errors.append(f"expected 1..4 blue controls, got {len(blue)}")
    elif blue != [(0, col) for col in range(width - len(blue), width)]:
        errors.append("blue controls must be contiguous and end at the top-right corner")
    if not 1 <= len(red) <= 2:
        errors.append(f"expected 1..2 red controls, got {len(red)}")
    elif red != [(row, 0) for row in range(height - len(red), height)]:
        errors.append("red controls must be contiguous and end at the bottom-left corner")

    normalized_template: tuple[tuple[int, int], ...] = ()
    template_top = template_left = template_bottom = template_right = -1
    if not 4 <= len(template_cells) <= 7:
        errors.append(f"expected a 4..7-cell magenta template, got {len(template_cells)}")
    elif not _connected(template_cells):
        errors.append("magenta template must be one 4-connected object")
    else:
        template_top = min(row for row, _col in template_cells)
        template_bottom = max(row for row, _col in template_cells)
        template_left = min(col for _row, col in template_cells)
        template_right = max(col for _row, col in template_cells)
        normalized_template = _normalize(list(template_cells))
        if template_top < 1 or template_left < 1:
            errors.append("template must be separated from the control edges")
        if template_bottom >= height // 2 + 1 or template_right >= width // 2 + 1:
            errors.append("template must occupy the upper-left teaching zone")
        template_h = template_bottom - template_top + 1
        template_w = template_right - template_left + 1
        if template_h < 2 or template_w < 2:
            errors.append("template bounding box must be at least 2x2")
        if len(_all_views(normalized_template)) < 4:
            errors.append("template is too symmetric to expose the control transformation")

    if len(anchors) != 1:
        errors.append(f"expected exactly one orange anchor, got {len(anchors)}")

    targets: list[tuple[int, int]] = []
    if blue and red and normalized_template and len(anchors) == 1:
        anchor_row, anchor_col = anchors[0]
        transformed = _transform(normalized_template, len(blue), len(red))
        targets = [(anchor_row + row, anchor_col + col) for row, col in transformed]
        if anchor_row <= template_bottom + 1 or anchor_col <= template_right + 1:
            errors.append("anchor must be separated below and right of the template")
        if any(not (0 <= row < height and 0 <= col < width) for row, col in targets):
            errors.append("anchor clips the transformed stamp")
        else:
            forbidden = [
                (row, col)
                for row, col in targets
                if grid[row][col] not in (0, 7)
            ]
            if forbidden:
                errors.append(f"transformed stamp collides with input role cells at {forbidden[:3]}")

    facts = {
        "grid_h": height,
        "grid_w": width,
        "rot_count": len(blue),
        "ref_count": len(red),
        "template_cells": len(template_cells),
        "template": normalized_template,
        "template_view_count": len(_all_views(normalized_template)) if normalized_template else 0,
        "anchor": anchors[0] if len(anchors) == 1 else None,
        "targets": targets,
        "palette": palette,
    }
    return facts, errors


def _meta_overrides(meta: Any) -> dict[str, Any]:
    requested: dict[str, Any] = {}
    if not isinstance(meta, dict):
        return requested
    nested = meta.get("overrides")
    if isinstance(nested, dict):
        requested.update(nested)
    for axis in AXES:
        if axis in meta:
            requested[axis] = meta[axis]
    return requested


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact axis from the returned pixels."""
    facts, errors = _analyze(grid)
    if errors:
        return {}
    return {axis: int(facts[axis]) for axis in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed/rule-hiding scenes and verify requested exact axes."""
    del difficulty
    facts, errors = _analyze(grid)
    if facts:
        observed = observe_overrides(grid)
        for axis, requested in _meta_overrides(meta).items():
            if axis in AXES and observed.get(axis) != requested:
                errors.append(
                    f"override {axis} requested {requested!r}, observed {observed.get(axis)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the complete lawful task grammar, including every canonical input."""
    return self_check(grid)


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for tests; the Racket program is authoritative."""
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    output = [list(row) for row in grid]
    for row, col in facts["targets"]:
        output[row][col] = 8
    return output


def _rival_output(grid, *, rot_count: int | None = None, ref_count: int | None = None):
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid rival scene: " + "; ".join(errors))
    rotation = facts["rot_count"] if rot_count is None else rot_count
    reflection = facts["ref_count"] if ref_count is None else ref_count
    transformed = _transform(facts["template"], rotation, reflection)
    anchor_row, anchor_col = facts["anchor"]
    output = [list(row) for row in grid]
    for drow, dcol in transformed:
        row, col = anchor_row + drow, anchor_col + dcol
        if 0 <= row < facts["grid_h"] and 0 <= col < facts["grid_w"]:
            output[row][col] = 8
    return output


def _rival_fixed_orientation(grid):
    return _rival_output(grid, rot_count=1, ref_count=1)


def _rival_rotation_only(grid):
    return _rival_output(grid, ref_count=1)


def _rival_reflection_only(grid):
    return _rival_output(grid, rot_count=1)


def _rival_off_by_one_rotation(grid):
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid rival scene: " + "; ".join(errors))
    wrong_rotation = 1 + (facts["rot_count"] % 4)
    return _rival_output(grid, rot_count=wrong_rotation)


def _rival_flip_before_rotate(grid):
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid rival scene: " + "; ".join(errors))
    shape = facts["template"]
    if facts["ref_count"] == 2:
        shape = _flip_horizontal(shape)
    for _ in range(facts["rot_count"] - 1):
        shape = _rotate_cw(shape)
    anchor_row, anchor_col = facts["anchor"]
    output = [list(row) for row in grid]
    for drow, dcol in _normalize(shape):
        output[anchor_row + drow][anchor_col + dcol] = 8
    return output


SEMANTIC_RIVALS: dict[str, Callable] = {
    "fixed_orientation": _rival_fixed_orientation,
    "rotation_only": _rival_rotation_only,
    "reflection_only": _rival_reflection_only,
    "off_by_one_rotation": _rival_off_by_one_rotation,
    "flip_before_rotate": _rival_flip_before_rotate,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS


def _branch_witness(grid, rot_count: int, ref_count: int) -> bool:
    facts, errors = _analyze(grid)
    return not errors and (
        facts["rot_count"] == rot_count
        and facts["ref_count"] == ref_count
        and facts["template_view_count"] == 8
    )


SEMANTIC_WITNESSES = {
    f"rotation_{rotation}_reflection_{reflection}": (
        lambda grid, rotation=rotation, reflection=reflection: _branch_witness(
            grid, rotation, reflection
        )
    )
    for rotation, reflection in _PROFILE_ORDER
}
WITNESS_RIVALS = {
    "rotation_1_reflection_1": ["off_by_one_rotation"],
    "rotation_2_reflection_1": ["fixed_orientation"],
    "rotation_3_reflection_1": ["fixed_orientation"],
    "rotation_4_reflection_1": ["fixed_orientation"],
    "rotation_1_reflection_2": ["rotation_only"],
    "rotation_2_reflection_2": ["rotation_only"],
    "rotation_3_reflection_2": ["rotation_only"],
    "rotation_4_reflection_2": ["rotation_only"],
}


def _template_size_rotation_shortcut_survives(demos, query_facts) -> bool:
    """Return whether template area alone reproduces all observed rotations."""
    size_to_rotation: dict[int, int] = {}
    for pair in demos:
        facts, errors = _analyze(pair["input"])
        if errors:
            continue
        template_size = int(facts["template_cells"])
        rotation = int(facts["rot_count"])
        previous = size_to_rotation.setdefault(template_size, rotation)
        if previous != rotation:
            return False
    return (
        size_to_rotation.get(int(query_facts["template_cells"]))
        == int(query_facts["rot_count"])
    )


def lesson_identifiable(demos, query) -> list[str]:
    """Require all eight control pairs and eliminate named plausible rivals."""
    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must be an input/output pair"]

    seen: set[tuple[int, int]] = set()
    valid_demos = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        facts, errors = _analyze(pair["input"])
        if errors:
            reasons.append(f"demo {index} input invalid: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the task rule")
            continue
        seen.add((facts["rot_count"], facts["ref_count"]))
        valid_demos.append(pair)

    missing = sorted(set(_PROFILE_ORDER) - seen)
    if missing:
        reasons.append(f"demonstrations omit control pair(s) {missing}")

    query_facts, query_errors = _analyze(query["input"])
    if query_errors:
        reasons.append(f"query input invalid: {query_errors[0]}")
        return reasons
    query_truth = rule_mirror(query["input"])
    if query["output"] != query_truth:
        reasons.append("query output disagrees with the task rule")
    query_pair = (query_facts["rot_count"], query_facts["ref_count"])
    if query_pair not in seen:
        reasons.append(f"query control pair {query_pair} has no demonstration")

    if _template_size_rotation_shortcut_survives(valid_demos, query_facts):
        reasons.append(
            "template size predicts rotation across every demo and the query, "
            "making the blue controls redundant"
        )

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in valid_demos)
        if survives and competitor(query["input"]) != query_truth:
            reasons.append(
                f"competing rule '{name}' matches every demo but changes the query answer"
            )
    return sorted(set(reasons))


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Expose the exact eight-residue control schedule used by lessons."""
    del seed, difficulty
    rotation, reflection = _scheduled_profile(sample_index)
    return f"r{rotation}_f{reflection}"


SCHEDULE_PROFILES = tuple(f"r{rotation}_f{reflection}" for rotation, reflection in _PROFILE_ORDER)


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Named structural impostors that must be rejected by ``self_check``."""
    base = generate(991, 0, grid_h=13, grid_w=13, rot_count=2, ref_count=2, template_cells=5)

    missing_blue = [list(row) for row in base]
    for col in range(len(missing_blue[0])):
        if missing_blue[0][col] == 1:
            missing_blue[0][col] = 0

    split_blue = [list(row) for row in base]
    blue_cols = [col for col, value in enumerate(split_blue[0]) if value == 1]
    split_blue[0][blue_cols[0]] = 0
    split_blue[1][blue_cols[0]] = 1

    disconnected_template = [list(row) for row in base]
    sixes = [(row, col) for row, values in enumerate(base) for col, value in enumerate(values) if value == 6]
    row, col = sixes[-1]
    disconnected_template[row][col] = 0
    disconnected_template[1][len(base[0]) // 2] = 6

    clipped_anchor = [list(row) for row in base]
    anchor = next((row, col) for row, values in enumerate(base) for col, value in enumerate(values) if value == 7)
    clipped_anchor[anchor[0]][anchor[1]] = 0
    clipped_anchor[-1][-1] = 7

    extra_anchor = [list(row) for row in base]
    extra_anchor[-2][-2] = 7

    target_collision = [list(row) for row in base]
    facts, _ = _analyze(base)
    collision = next(cell for cell in facts["targets"] if cell != facts["anchor"])
    target_collision[collision[0]][collision[1]] = 6

    return [
        ("missing_blue_controls", missing_blue),
        ("split_blue_controls", split_blue),
        ("disconnected_template", disconnected_template),
        ("clipped_anchor", clipped_anchor),
        ("multiple_anchors", extra_anchor),
        ("stamp_collision", target_collision),
    ]
