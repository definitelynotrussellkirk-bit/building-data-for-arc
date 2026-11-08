"""Generator for hard_141_decode_dual_code_library_and_center_stamp.

The first three cells encode ``(prototype color, transform code, output
color)``.  Three separated colored library objects sit above a cyan frame.
The canonical rule selects the object whose color matches the first control,
applies the transform encoded by the second control, recolors it with the
third control, and centers it in the returned 6x7 frame crop.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "a7de0ceaa136"
TASK_ID = GENERATOR_ID
RULE_HASH = "c167c8532293"
VERSION = "2.0.0"

SUMMARY = (
    "Row 0 cells 0..2 are (prototype color, transform code, output color). "
    "The transform map is 1=identity, 2=flip left-right, 3=flip up-down, "
    "4=rotate clockwise, 5=rotate 180 degrees, and 6=rotate counterclockwise. "
    "Select the matching object from a three-object color library, transform "
    "and recolor it, then center it inside the cropped 6x7 cyan frame."
)

INVARIANTS = [
    "row 0 contains exactly three nonzero controls followed by zeros",
    "three separated monochrome library objects have distinct colors",
    "the prototype control names exactly one library object",
    "the output color is distinct from every library color",
    "a hollow 6x7 cyan frame touches the bottom and right grid boundaries",
    "the transformed prototype fits inside the frame interior",
]

# Six consecutive demonstrations cover all six transform codes.  The keyed
# seed offset varies which code appears first, so the following query is not
# permanently an identity case.
EXAMPLES_NEEDED = 6
MIN_STRICT_FRAC = 1.0

PALETTE_KINDS = ("default", "warm", "cool", "varied")
_PALETTES = {
    # Three ordered library colors followed by an output color.  The complete
    # tuples are disjoint, making palette_kind exactly observable from a grid.
    "default": ((2, 3, 5), 6),
    "warm": ((2, 4, 6), 7),
    "cool": ((1, 3, 7), 5),
    "varied": ((3, 4, 6), 9),
}
_PALETTE_BY_SIGNATURE = {
    (tuple(library), output): name
    for name, (library, output) in _PALETTES.items()
}

AXES = {
    "shape": {
        "type": "int",
        "default": "scheduled across 0..7",
        "valid": "0..22",
    },
    "transform": {
        "type": "int",
        "default": "six-code lesson schedule",
        "valid": "1..6",
    },
    "palette_kind": {
        "type": "enum",
        "default": "scheduled across four exact palettes",
        "valid": ["default", "warm", "cool", "varied"],
    },
    "prototype_slot": {
        "type": "int",
        "default": "scheduled across the three library positions",
        "valid": "0..2",
    },
}

# Every generated prototype is asymmetric under the six transformations used
# by the rule.  This keeps every code visibly testable instead of letting a
# symmetric shape turn a rotation/flip lesson into an accidental identity.
_SOURCE_SHAPES = (
    ((0, 0), (0, 1), (0, 2), (1, 0)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 2), (1, 3)),
    ((0, 0), (0, 1), (1, 1), (1, 2), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (1, 3)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0)),
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 2), (1, 3), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 2), (1, 3), (2, 3)),
    ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 3)),
    ((0, 0), (0, 1), (1, 1), (1, 2), (1, 3), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2), (1, 3), (2, 2)),
    ((0, 0), (0, 1), (1, 1), (1, 2), (1, 3), (2, 3)),
    ((0, 0), (1, 0), (1, 1), (1, 2), (1, 3), (2, 1)),
    ((0, 0), (1, 0), (1, 1), (1, 2), (1, 3), (2, 2)),
)

# 23 free asymmetric polyomino families x six visible transforms x four
# output colors.  The finite codomain declaration lets generic diversity tools
# distinguish a lawful fixed-canvas task from a near-constant output task.
EXPECTED_OUTPUT_CODOMAIN = 23 * 6 * 4

# Distractors include canonical-like 4-, 5-, and 6-cell connected shapes.
_DISTRACTOR_SHAPES = (
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 2)),
)

_SHAPE_SIGNATURE_TO_INDEX = {
    tuple(sorted(shape)): index for index, shape in enumerate(_SOURCE_SHAPES)
}
_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
_PROFILES = {
    "easy": ((13, 15), (14, 15)),
    "medium": ((14, 16), (13, 15), (14, 15)),
    "hard": ((15, 17), (14, 16)),
}


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _shape_dims(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = _normalize(cells)
    if not cells:
        return 0, 0
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _transform_cells(
    cells: Iterable[tuple[int, int]], code: int
) -> tuple[tuple[int, int], ...]:
    """Apply the canonical 1..6 transform code to normalized cells."""
    cells = _normalize(cells)
    h, w = _shape_dims(cells)
    if code == 1:
        out = cells
    elif code == 2:
        out = ((r, w - 1 - c) for r, c in cells)
    elif code == 3:
        out = ((h - 1 - r, c) for r, c in cells)
    elif code == 4:
        out = ((c, h - 1 - r) for r, c in cells)
    elif code == 5:
        out = ((h - 1 - r, w - 1 - c) for r, c in cells)
    elif code == 6:
        out = ((w - 1 - c, r) for r, c in cells)
    else:
        raise ValueError(f"transform code must be in 1..6, got {code!r}")
    return _normalize(out)


def _components(cells: set[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    remaining = set(cells)
    out: list[list[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        component: list[tuple[int, int]] = []
        while queue:
            r, c = queue.popleft()
            component.append((r, c))
            for dr, dc in _DIRS4:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    queue.append(nxt)
        out.append(sorted(component))
    return out


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _validate_grid(grid)
    if errors:
        return {"errors": errors}

    h, w = len(grid), len(grid[0])
    if not (13 <= h <= 15 and 15 <= w <= 17):
        errors.append(f"dims {h}x{w} outside canonical envelope 13..15 x 15..17")
    if w < 3:
        errors.append("grid is too narrow for three controls")
        return {"errors": errors}

    proto_color, transform, out_color = grid[0][0], grid[0][1], grid[0][2]
    if any(grid[0][c] != 0 for c in range(3, w)):
        errors.append("row 0 must contain only the three controls")
    if h < 2 or any(value != 0 for value in grid[1]):
        errors.append("row 1 must separate controls from the library")
    if proto_color in (0, 8):
        errors.append(f"prototype color must be nonzero and non-cyan; got {proto_color}")
    if transform not in range(1, 7):
        errors.append(f"transform code must be in 1..6; got {transform}")
    if out_color in (0, 8):
        errors.append(f"output color must be nonzero and non-cyan; got {out_color}")
    if proto_color == out_color:
        errors.append("prototype and output colors must differ")

    frame_cells = {
        (r, c) for r in range(h) for c in range(w) if grid[r][c] == 8
    }
    frame_bbox = None
    if not frame_cells:
        errors.append("missing cyan frame")
    else:
        top = min(r for r, _ in frame_cells)
        left = min(c for _, c in frame_cells)
        bottom = max(r for r, _ in frame_cells)
        right = max(c for _, c in frame_cells)
        frame_bbox = (top, left, bottom, right)
        expected = {
            (r, c)
            for r in range(top, bottom + 1)
            for c in range(left, right + 1)
            if r in (top, bottom) or c in (left, right)
        }
        if frame_cells != expected:
            errors.append("cyan cells must form one complete hollow rectangle")
        if (bottom - top + 1, right - left + 1) != (6, 7):
            errors.append(
                f"frame must be 6x7; got {bottom - top + 1}x{right - left + 1}"
            )
        if bottom != h - 1 or right != w - 1:
            errors.append("frame must touch the bottom and right boundaries")
        if any(
            grid[r][c] != 0
            for r in range(top + 1, bottom)
            for c in range(left + 1, right)
        ):
            errors.append("frame interior must be empty in the input")

    controls = {(0, 0), (0, 1), (0, 2)}
    scene_cells = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] != 0 and (r, c) not in controls and (r, c) not in frame_cells
    }
    components = _components(scene_cells)
    library_objects: list[dict[str, Any]] = []
    if len(components) != 3:
        errors.append(f"need exactly three library objects; found {len(components)}")
    for index, cells in enumerate(components):
        colors = {grid[r][c] for r, c in cells}
        if len(colors) != 1:
            errors.append(f"library object {index} is not monochrome")
            color = None
        else:
            color = next(iter(colors))
            if color in (0, 8):
                errors.append(f"library object {index} uses reserved color {color}")
        if not (4 <= len(cells) <= 6):
            errors.append(f"library object {index} must have 4..6 cells; got {len(cells)}")
        obj_top = min(r for r, _ in cells)
        obj_left = min(c for _, c in cells)
        obj_bottom = max(r for r, _ in cells)
        obj_right = max(c for _, c in cells)
        if frame_bbox is not None and obj_bottom >= frame_bbox[0]:
            errors.append(f"library object {index} must sit above the frame")
        library_objects.append(
            {
                "cells": tuple(cells),
                "shape": _normalize(cells),
                "color": color,
                "bbox": (obj_top, obj_left, obj_bottom, obj_right),
                "size": len(cells),
            }
        )

    library_objects.sort(key=lambda obj: (obj["bbox"][1], obj["bbox"][0]))
    library_colors = [obj["color"] for obj in library_objects if obj["color"] is not None]
    if len(library_colors) == 3 and len(set(library_colors)) != 3:
        errors.append("library object colors must be distinct")
    if out_color in library_colors:
        errors.append("output color must not be a library color")

    prototype_objects = [obj for obj in library_objects if obj["color"] == proto_color]
    if len(prototype_objects) != 1:
        errors.append(
            f"prototype control must name exactly one library object; found {len(prototype_objects)}"
        )
        prototype = None
        prototype_slot = None
    else:
        prototype = prototype_objects[0]
        prototype_slot = library_objects.index(prototype)
        transformed = _transform_cells(prototype["shape"], transform)
        tile_h, tile_w = _shape_dims(transformed)
        if tile_h > 4 or tile_w > 5:
            errors.append(
                f"transformed prototype {tile_h}x{tile_w} does not fit frame interior 4x5"
            )

    palette_size = len({value for row in grid for value in row})
    if palette_size not in (6, 7):
        errors.append(f"canonical palette size must be 6 or 7; got {palette_size}")

    palette_kind = None
    if len(library_objects) == 3 and all(obj["color"] is not None for obj in library_objects):
        palette_kind = _PALETTE_BY_SIGNATURE.get(
            (tuple(obj["color"] for obj in library_objects), out_color)
        )

    shape_index = None
    if prototype is not None:
        shape_index = _SHAPE_SIGNATURE_TO_INDEX.get(prototype["shape"])

    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "proto_color": proto_color,
        "transform": transform,
        "out_color": out_color,
        "frame_bbox": frame_bbox,
        "frame_cells": frame_cells,
        "library_objects": library_objects,
        "prototype": prototype,
        "prototype_slot": prototype_slot,
        "shape": shape_index,
        "palette_kind": palette_kind,
        "palette_size": palette_size,
        "larger_distractor": bool(
            prototype is not None
            and any(obj["size"] > prototype["size"] for obj in library_objects if obj is not prototype)
        ),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete teaching grammar and reject structural impostors."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """This generator intentionally stays on the task's canonical manifold."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared exact semantic axis from the returned grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    if analysis["shape"] is None:
        raise ValueError("generated prototype shape is outside the declared shape catalog")
    if analysis["palette_kind"] is None:
        raise ValueError("generated palette does not match a declared palette_kind")
    return {
        "shape": analysis["shape"],
        "transform": analysis["transform"],
        "palette_kind": analysis["palette_kind"],
        "prototype_slot": analysis["prototype_slot"],
    }


def _scheduled_offset(seed: int, label: str, modulus: int) -> int:
    return stable_rng(seed, f"{TASK_ID}|{label}", VERSION).randrange(modulus)


def _draw_scheduled_int(ctx, label: str, lo: int, hi: int, scheduled: int) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _draw_scheduled_choice(ctx, label: str, options: tuple[str, ...], scheduled: str) -> str:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _paint(
    grid: list[list[int]], top: int, left: int,
    cells: Iterable[tuple[int, int]], color: int,
) -> None:
    for dr, dc in cells:
        grid[top + dr][left + dc] = color


def _choose_distractors(proto_shape: tuple[tuple[int, int], ...], rng) -> tuple:
    candidates = [shape for shape in _DISTRACTOR_SHAPES if _normalize(shape) != proto_shape]
    if len(proto_shape) == 4:
        larger = [shape for shape in candidates if len(shape) > len(proto_shape)]
        first = rng.choice(larger)
    else:
        first = rng.choice(candidates)
    remaining = [shape for shape in candidates if _normalize(shape) != _normalize(first)]
    second = rng.choice(remaining)
    return first, second


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    band = "medium" if difficulty is None else difficulty
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    transform = _draw_scheduled_int(
        ctx,
        "transform",
        1,
        6,
        1 + ((_scheduled_offset(seed, "transform", 6) + int(sample_index)) % 6),
    )
    lesson_position = int(sample_index) % EXAMPLES_NEEDED
    shortcut_position = _scheduled_offset(seed, "shortcut_witness", EXAMPLES_NEEDED)
    if lesson_position == shortcut_position:
        scheduled_shape = 0  # four cells; distractor selection guarantees a larger object
    else:
        scheduled_shape = 1 + (
            _scheduled_offset(seed, "shape", len(_SOURCE_SHAPES) - 1)
            + int(sample_index)
        ) % (len(_SOURCE_SHAPES) - 1)
    shape_index = _draw_scheduled_int(
        ctx,
        "shape",
        0,
        len(_SOURCE_SHAPES) - 1,
        scheduled_shape,
    )
    prototype_slot = _draw_scheduled_int(
        ctx,
        "prototype_slot",
        0,
        2,
        (_scheduled_offset(seed, "prototype_slot", 3) + int(sample_index)) % 3,
    )
    palette_scheduled = PALETTE_KINDS[
        (_scheduled_offset(seed, "palette_kind", len(PALETTE_KINDS)) + int(sample_index))
        % len(PALETTE_KINDS)
    ]
    palette_kind = _draw_scheduled_choice(
        ctx, "palette_kind", PALETTE_KINDS, palette_scheduled
    )

    profiles = _PROFILES[band]
    profile_index = (
        _scheduled_offset(seed, f"profile:{band}", len(profiles)) + int(sample_index)
    ) % len(profiles)
    h, w = profiles[profile_index]

    library_colors, out_color = _PALETTES[palette_kind]
    proto_color = library_colors[prototype_slot]
    proto_shape = _SOURCE_SHAPES[shape_index]
    layout_rng = ctx.draw_rng("layout")
    distractor_a, distractor_b = _choose_distractors(proto_shape, layout_rng)

    object_shapes = [distractor_a, distractor_b]
    object_shapes.insert(prototype_slot, proto_shape)

    grid = full_grid(h, w, 0)
    grid[0][0] = proto_color
    grid[0][1] = transform
    grid[0][2] = out_color

    # Three canonical library lanes.  Maximum shape width is four, so these
    # starts preserve a blank separator column even on the 15-column profile.
    lefts = (1, 6, 11)
    for slot, (shape, color) in enumerate(zip(object_shapes, library_colors)):
        shape_h, _ = _shape_dims(shape)
        top = 2 + layout_rng.randrange(max(1, 6 - shape_h))
        _paint(grid, top, lefts[slot], shape, color)

    draw_frame(grid, h - 6, w - 7, h - 1, w - 1, 8)

    errors = self_check(grid, difficulty=band)
    if errors:
        raise AssertionError("generated invalid lesson: " + "; ".join(errors))
    return grid


def _expected_output(grid: Any) -> list[list[int]]:
    """Python mirror used only by semantic checks; Racket remains authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    top, left, bottom, right = analysis["frame_bbox"]
    output = [list(row[left : right + 1]) for row in grid[top : bottom + 1]]
    tile = _transform_cells(analysis["prototype"]["shape"], analysis["transform"])
    tile_h, tile_w = _shape_dims(tile)
    stamp_top = (len(output) - tile_h) // 2
    stamp_left = (len(output[0]) - tile_w) // 2
    for r, c in tile:
        output[stamp_top + r][stamp_left + c] = analysis["out_color"]
    return output


def _witness_transform(code: int):
    def predicate(grid) -> bool:
        analysis = _analyze(grid)
        return not analysis["errors"] and analysis["transform"] == code

    return predicate


def _witness_slot(slot: int):
    def predicate(grid) -> bool:
        analysis = _analyze(grid)
        return not analysis["errors"] and analysis["prototype_slot"] == slot

    return predicate


SEMANTIC_WITNESSES = {
    **{f"transform_{code}": _witness_transform(code) for code in range(1, 7)},
    **{f"prototype_slot_{slot}": _witness_slot(slot) for slot in range(3)},
    "larger_distractor_rebuts_largest_object": lambda grid: (
        not _analyze(grid)["errors"] and _analyze(grid)["larger_distractor"]
    ),
    "canonical_palette_6": lambda grid: (
        not _analyze(grid)["errors"] and _analyze(grid)["palette_size"] == 6
    ),
    "canonical_palette_7": lambda grid: (
        not _analyze(grid)["errors"] and _analyze(grid)["palette_size"] == 7
    ),
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require a lesson to pin selection, code mapping, and recoloring."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    analyses: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        analysis = _analyze(pair.get("input"))
        if analysis["errors"]:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        try:
            expected = _expected_output(pair["input"])
        except Exception as exc:
            reasons.append(f"demo {index} mirror failed: {type(exc).__name__}: {exc}")
            continue
        if pair.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with the canonical transform")
        analyses.append(analysis)

    codes = {analysis["transform"] for analysis in analyses}
    missing_codes = sorted(set(range(1, 7)) - codes)
    if missing_codes:
        reasons.append(f"demonstrations omit transform codes {missing_codes}")
    slots = {analysis["prototype_slot"] for analysis in analyses}
    if slots != {0, 1, 2}:
        reasons.append("demonstrations do not select all three library positions")
    if len({analysis["out_color"] for analysis in analyses}) < 3:
        reasons.append("output color varies fewer than three ways")
    if len({analysis["proto_color"] for analysis in analyses}) < 3:
        reasons.append("prototype color varies fewer than three ways")
    if not any(analysis["larger_distractor"] for analysis in analyses):
        reasons.append("no demonstration rebuts the largest-object shortcut")
    if len({analysis["palette_kind"] for analysis in analyses}) < 3:
        reasons.append("fewer than three palette families appear")

    query_analysis = _analyze(query.get("input"))
    if query_analysis["errors"]:
        reasons.append("query input is outside the teaching grammar")
    else:
        if query_analysis["transform"] not in codes:
            reasons.append("query transform code was not demonstrated")
        try:
            expected_query = _expected_output(query["input"])
            if query.get("output") != expected_query:
                reasons.append("query output disagrees with the canonical transform")
        except Exception as exc:
            reasons.append(f"query mirror failed: {type(exc).__name__}: {exc}")

    return sorted(set(reasons))
