"""Generator for ``tile_transformed_templates_inside_colored_frames``.

Executable rule authority
-------------------------
A full colour-5 row separates a 2x2 colour-2/3 template from two hollow
rectangular frames.  The output is the region below the separator.  Inside
frame colour 1 the template is tiled unchanged; colour 2 uses a 90-degree
clockwise rotation; colour 3 uses a 180-degree rotation; and colour 4 uses a
transpose before periodic tiling.  Only non-zero template cells are painted.

The canonical prose calls colour 4 a 270-degree rotation, but the synchronized
canonical/base Racket program and the official colour-4 grids implement
``transpose``.  This generator follows the executable/output authority and
keeps the discrepancy explicit rather than silently minting contradictory
labels.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "40e128dec2ec"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "990d84e223bd"  # sha256(normalized canonical program_solution)[:12]

SUMMARY = (
    "A 2x2 colour-2/3 template above a full colour-5 separator is tiled into "
    "two hollow frames below: frame colours 1/2/3/4 select identity, 90° CW, "
    "180°, and transpose respectively; the output is the lower region only."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.08

INVARIANTS = [
    "the rectangular input uses ARC colours 0..5 with background 0",
    "row 2 is the unique full-width colour-5 separator",
    "the cropped template above the separator is exactly 2x2, contains both colours 2 and 3, and contains at least one zero",
    "below the separator are exactly two separated hollow rectangular frames with distinct colours from 1..4",
    "every frame is at least 4x4, so its interior can receive the 2x2 periodic template",
    "three consecutive demonstrations cover all four executable transform branches; colour 4 is transpose, not 270° rotation",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-prior 10 or difficulty-aware 9..18",
        "valid": "9..18",
        "doc": "Input height. Exact overrides are honoured in every difficulty band.",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-prior 14 or difficulty-aware 13..24",
        "valid": "13..24",
        "doc": "Input width. Exact overrides are honoured in every difficulty band.",
    },
}

# Slot 0/1/2 are the three demonstrations materialized by the runner; slot 3
# is the query.  Thus every lesson demonstrates all four marker transforms.
_FRAME_COLOR_SCHEDULE = (
    (1, 2),
    (3, 4),
    (1, 3),
    (2, 4),
)

_CANONICAL_TEMPLATE = ((2, 0), (0, 3))
_ASYMMETRIC_TEMPLATES = (
    ((2, 2), (3, 0)),
    ((2, 3), (2, 0)),
    ((2, 0), (3, 3)),
    ((3, 2), (0, 3)),
)

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _has_override(ctx: Any, label: str) -> bool:
    return label in ctx.overrides and ctx.overrides[label] is not None


def _draw_axis_int(
    ctx: Any,
    label: str,
    default_bounds: tuple[int, int],
    valid_bounds: tuple[int, int],
) -> int:
    bounds = valid_bounds if _has_override(ctx, label) else default_bounds
    return ctx.draw_int(label, *bounds)


def _transpose(grid: Iterable[Iterable[int]]) -> list[list[int]]:
    rows = [list(row) for row in grid]
    return [list(row) for row in zip(*rows)]


def _rotate_cw(grid: Iterable[Iterable[int]]) -> list[list[int]]:
    rows = [list(row) for row in grid]
    return [list(row) for row in zip(*rows[::-1])]


def _rotate_180(grid: Iterable[Iterable[int]]) -> list[list[int]]:
    rows = [list(row) for row in grid]
    return [row[::-1] for row in rows[::-1]]


def _rotate_ccw(grid: Iterable[Iterable[int]]) -> list[list[int]]:
    rows = [list(row) for row in grid]
    return [list(row) for row in zip(*rows)][::-1]


def _normal_transform(template: list[list[int]], marker: int) -> list[list[int]]:
    if marker == 1:
        return [row[:] for row in template]
    if marker == 2:
        return _rotate_cw(template)
    if marker == 3:
        return _rotate_180(template)
    if marker == 4:
        return _transpose(template)
    raise ValueError(f"unsupported frame marker {marker}")


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _same_color_components(grid: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    out: list[dict[str, Any]] = []
    for r0 in range(h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            queue = deque([(r0, c0)])
            seen.add((r0, c0))
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in _DIRS4:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            out.append({"color": color, "cells": tuple(sorted(cells))})
    return out


def _frame_record(component: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    color = component["color"]
    cells = set(component["cells"])
    r1, c1, r2, c2 = _bbox(cells)
    fh, fw = r2 - r1 + 1, c2 - c1 + 1
    if fh < 4 or fw < 4:
        return None, f"colour-{color} component is only {fh}x{fw}; frames must be at least 4x4"
    perimeter = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }
    if cells != perimeter:
        missing = sorted(perimeter - cells)
        extra = sorted(cells - perimeter)
        detail = f"missing={missing[:2]} extra={extra[:2]}"
        return None, f"colour-{color} component is not an exact hollow rectangle ({detail})"
    return {
        "color": color,
        "cells": tuple(sorted(cells)),
        "r1": r1,
        "c1": c1,
        "r2": r2,
        "c2": c2,
        "h": fh,
        "w": fw,
        "interior_h": fh - 2,
        "interior_w": fw - 2,
    }, None


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    info: dict[str, Any] = {}
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return info, ["grid must be a non-empty list of non-empty rows"]
    w = len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return info, ["grid is ragged"]
    h = len(grid)
    info.update(grid_h=h, grid_w=w)
    errors: list[str] = []
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return info, ["grid values must be integer ARC colours 0..9"]

    divider_rows = [r for r in range(h) if all(value == 5 for value in grid[r])]
    if len(divider_rows) != 1:
        return info, [f"expected exactly one full colour-5 separator row, found {len(divider_rows)}"]
    sep = divider_rows[0]
    info["separator_row"] = sep
    if sep != 2:
        errors.append(f"separator must be row 2, found row {sep}")

    above = [row[:] for row in grid[:sep]]
    bad_above = sorted({value for row in above for value in row if value not in (0, 2, 3)})
    if bad_above:
        errors.append(f"above-separator colours must be 0/2/3, found {bad_above}")
    template_cells = [
        (r, c)
        for r, row in enumerate(above)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not template_cells:
        errors.append("template above the separator is empty")
        template: list[list[int]] = []
    else:
        tr1, tc1, tr2, tc2 = _bbox(template_cells)
        template = [row[tc1 : tc2 + 1] for row in above[tr1 : tr2 + 1]]
        info["template_bbox"] = (tr1, tc1, tr2, tc2)
        if (tr2 - tr1 + 1, tc2 - tc1 + 1) != (2, 2):
            errors.append(
                "cropped template must be exactly 2x2, found "
                f"{tr2 - tr1 + 1}x{tc2 - tc1 + 1}"
            )
        template_values = [value for row in template for value in row]
        if set(value for value in template_values if value != 0) != {2, 3}:
            errors.append("template must contain both and only non-zero colours 2 and 3")
        nonzero_count = sum(value != 0 for value in template_values)
        if not 2 <= nonzero_count <= 3:
            errors.append(f"template must contain 2 or 3 non-zero cells, found {nonzero_count}")
        if 0 not in template_values:
            errors.append("template must contain at least one zero to expose sparse periodic tiling")
    info["template"] = tuple(tuple(row) for row in template)

    if sep + 1 >= h:
        errors.append("separator leaves no lower region")
        return info, errors
    lower = [row[:] for row in grid[sep + 1 :]]
    components = _same_color_components(lower)
    frames: list[dict[str, Any]] = []
    if len(components) != 2:
        errors.append(f"expected exactly two non-zero lower components, found {len(components)}")
    for component in components:
        if component["color"] not in (1, 2, 3, 4):
            errors.append(f"lower component colour {component['color']} is not a transform key 1..4")
            continue
        frame, error = _frame_record(component)
        if error:
            errors.append(error)
        elif frame is not None:
            frames.append(frame)
    if len(frames) == 2:
        colors = [frame["color"] for frame in frames]
        if len(set(colors)) != 2:
            errors.append(f"frame colours must be distinct, found {colors}")
        a, b = frames
        separated = (
            a["r2"] + 1 < b["r1"]
            or b["r2"] + 1 < a["r1"]
            or a["c2"] + 1 < b["c1"]
            or b["c2"] + 1 < a["c1"]
        )
        if not separated:
            errors.append("the two frames must have at least one full background row or column between them")
    info["frames"] = tuple(sorted(frames, key=lambda frame: (frame["c1"], frame["r1"])))
    info["frame_colors"] = tuple(sorted(frame["color"] for frame in frames))
    return info, errors


def observe_overrides(grid: Any) -> dict[str, int]:
    """Recover every declared exact axis from the returned input grid."""
    if not isinstance(grid, list) or not grid:
        return {"grid_h": 0, "grid_w": 0}
    return {"grid_h": len(grid), "grid_w": len(grid[0]) if grid[0] else 0}


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Reject malformed/rule-hiding scenes and accept every canonical input."""
    info, errors = _analyse(grid)
    if errors:
        return errors
    h, w = info["grid_h"], info["grid_w"]
    if not 9 <= h <= 18:
        errors.append(f"grid height {h} outside declared 9..18")
    if not 13 <= w <= 24:
        errors.append(f"grid width {w} outside declared 13..24")
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Linked empirical canonical manifold, broad only over nuisance position."""
    info, errors = _analyse(grid)
    if errors:
        return errors
    h, w = info["grid_h"], info["grid_w"]
    template = info["template"]
    descriptors = tuple(sorted((f["color"], f["h"], f["w"]) for f in info["frames"]))
    if template != _CANONICAL_TEMPLATE:
        return [f"canonical template is {_CANONICAL_TEMPLATE}, found {template}"]
    allowed = {
        (10, 14, ((1, 4, 4), (2, 4, 4))),
        (10, 14, ((1, 4, 4), (2, 4, 5))),
        (9, 13, ((3, 5, 5), (4, 5, 4))),
    }
    linked = (h, w, descriptors)
    if linked not in allowed:
        return [f"linked canonical profile mismatch: {linked!r}"]
    return []


def _template_orbit(template: tuple[tuple[int, ...], ...]) -> set[tuple[tuple[int, ...], ...]]:
    matrix = [list(row) for row in template]
    return {
        tuple(tuple(row) for row in matrix),
        tuple(tuple(row) for row in _rotate_cw(matrix)),
        tuple(tuple(row) for row in _rotate_180(matrix)),
        tuple(tuple(row) for row in _transpose(matrix)),
    }


def _has_marker(marker: int) -> Callable[[Any], bool]:
    def predicate(grid: Any) -> bool:
        info, errors = _analyse(grid)
        return not errors and marker in info["frame_colors"]
    return predicate


def _asymmetric_template(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and len(_template_orbit(info["template"])) == 4


def _transpose_differs_from_ccw(grid: Any) -> bool:
    info, errors = _analyse(grid)
    if errors:
        return False
    matrix = [list(row) for row in info["template"]]
    return _transpose(matrix) != _rotate_ccw(matrix)


def _periodic_repeat(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and any(
        frame["interior_h"] > 2 or frame["interior_w"] > 2
        for frame in info["frames"]
    )


def _unequal_frame_geometry(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and len({(f["h"], f["w"]) for f in info["frames"]}) > 1


SEMANTIC_WITNESSES = {
    "strict_canonical_profile": lambda grid: not strict_canonical_like(grid),
    "frame_colour_1_identity": _has_marker(1),
    "frame_colour_2_rotate_cw": _has_marker(2),
    "frame_colour_3_rotate_180": _has_marker(3),
    "frame_colour_4_transpose": _has_marker(4),
    "four_way_asymmetric_template": _asymmetric_template,
    "transpose_differs_from_270_degree_rotation": _transpose_differs_from_ccw,
    "periodic_repeat_beyond_one_template_tile": _periodic_repeat,
    "unequal_frame_geometry": _unequal_frame_geometry,
}


def _solve_with_mapping(
    grid: Any,
    transform_for_marker: Callable[[list[list[int]], int], list[list[int]]],
    *,
    periodic: bool = True,
) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    sep = info["separator_row"]
    out = [row[:] for row in grid[sep + 1 :]]
    template = [list(row) for row in info["template"]]
    for frame in info["frames"]:
        transformed = transform_for_marker(template, frame["color"])
        th, tw = len(transformed), len(transformed[0])
        for dr in range(frame["interior_h"]):
            for dc in range(frame["interior_w"]):
                if not periodic and (dr >= th or dc >= tw):
                    continue
                value = transformed[dr % th][dc % tw]
                if value != 0:
                    out[frame["r1"] + 1 + dr][frame["c1"] + 1 + dc] = value
    return out


def _official_solution(grid: Any) -> list[list[int]]:
    return _solve_with_mapping(grid, _normal_transform)


def _all_identity(template: list[list[int]], marker: int) -> list[list[int]]:
    return [row[:] for row in template]


def _colour4_ccw(template: list[list[int]], marker: int) -> list[list[int]]:
    if marker == 4:
        return _rotate_ccw(template)
    return _normal_transform(template, marker)


def _colour2_transpose(template: list[list[int]], marker: int) -> list[list[int]]:
    if marker == 2:
        return _transpose(template)
    return _normal_transform(template, marker)


def _position_transform_solution(grid: Any) -> list[list[int]]:
    """Rival: left frame identity, right frame CW, ignoring marker colours."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    sep = info["separator_row"]
    out = [row[:] for row in grid[sep + 1 :]]
    template = [list(row) for row in info["template"]]
    frames = sorted(info["frames"], key=lambda frame: frame["c1"])
    for index, frame in enumerate(frames):
        transformed = template if index == 0 else _rotate_cw(template)
        for dr in range(frame["interior_h"]):
            for dc in range(frame["interior_w"]):
                value = transformed[dr % 2][dc % 2]
                if value != 0:
                    out[frame["r1"] + 1 + dr][frame["c1"] + 1 + dc] = value
    return out


def lesson_identifiable(demos: list[dict[str, Any]], query: dict[str, Any]) -> list[str]:
    """Reject lessons where a named shortcut still fits demos but misses query."""
    errors: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    seen_markers: set[int] = set()
    templates: set[tuple[tuple[int, ...], ...]] = set()
    frame_profiles: set[tuple[tuple[int, int, int], ...]] = set()
    periodic_seen = False
    colour4_disambiguated = False

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"demo {index} is not an input/output pair")
            continue
        info, bad = _analyse(pair["input"])
        if bad:
            errors.append(f"demo {index} malformed: {bad[0]}")
            continue
        expected = _official_solution(pair["input"])
        if pair["output"] != expected:
            errors.append(f"demo {index} output disagrees with executable transform-and-tile rule")
        seen_markers.update(info["frame_colors"])
        templates.add(info["template"])
        frame_profiles.add(tuple(sorted((f["color"], f["h"], f["w"]) for f in info["frames"])))
        periodic_seen = periodic_seen or _periodic_repeat(pair["input"])
        colour4_disambiguated = colour4_disambiguated or (
            4 in info["frame_colors"] and _transpose_differs_from_ccw(pair["input"])
        )

    if errors:
        return errors
    if seen_markers != {1, 2, 3, 4}:
        errors.append(f"demonstrations must cover frame colours 1..4, saw {sorted(seen_markers)}")
    if len(templates) < 2:
        errors.append("template geometry/colour arrangement is fixed across demonstrations")
    if len(frame_profiles) < 2:
        errors.append("frame colour/geometry linkage is fixed across demonstrations")
    if not periodic_seen:
        errors.append("demonstrations never require periodic repetition beyond a single 2x2 tile")
    if not colour4_disambiguated:
        errors.append("no colour-4 demonstration distinguishes transpose from the prose's 270° rival")

    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        errors.append("query is not an input/output pair")
        return errors
    qinfo, qbad = _analyse(query["input"])
    if qbad:
        errors.append(f"query malformed: {qbad[0]}")
        return errors
    official = _official_solution(query["input"])
    if query["output"] != official:
        errors.append("query output disagrees with executable transform-and-tile rule")

    rivals: dict[str, Callable[[Any], list[list[int]]]] = {
        "ignore-frame-colour/all-identity": lambda grid: _solve_with_mapping(grid, _all_identity),
        "colour-4-is-270-degree-rotation": lambda grid: _solve_with_mapping(grid, _colour4_ccw),
        "colour-2-is-transpose": lambda grid: _solve_with_mapping(grid, _colour2_transpose),
        "single-tile-without-periodic-repeat": lambda grid: _solve_with_mapping(grid, _normal_transform, periodic=False),
        "left-right-position-code": _position_transform_solution,
    }
    for name, rival in rivals.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != official:
                errors.append(f"{name} fits every demo but predicts a different query answer")
    return errors


def _draw_general_frame_sizes(
    rng: Any,
    lower_h: int,
    grid_w: int,
    slot: int,
) -> tuple[tuple[int, int], tuple[int, int]]:
    max_h = min(8, lower_h)
    max_w = min(8, (grid_w - 1) // 2)
    if max_h < 4 or max_w < 4:
        raise ValueError(f"grid {lower_h + 3}x{grid_w} is too small for two lawful frames")
    for _ in range(100):
        fh1 = rng.randint(4, max_h)
        fh2 = rng.randint(4, max_h)
        fw1 = rng.randint(4, max_w)
        fw2_max = min(8, grid_w - fw1 - 1)
        if fw2_max < 4:
            continue
        fw2 = rng.randint(4, fw2_max)
        periodic = any(value > 4 for value in (fh1, fh2, fw1, fw2))
        unequal = (fh1, fw1) != (fh2, fw2)
        if slot in (1, 2, 3) and not periodic:
            continue
        if slot in (2, 3) and not unequal:
            continue
        return (fh1, fw1), (fh2, fw2)
    raise ValueError("could not draw two frame geometries under the requested bounds")


def generate(seed: int, sample_index: int, *, difficulty: Any = None, **overrides: Any) -> list[list[int]]:
    unknown = sorted(key for key, value in overrides.items() if value is not None and key not in AXES)
    if unknown:
        raise ValueError(f"unknown overrides for {TASK_ID}: {unknown}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    slot = sample_index % 4
    profile_rng = ctx.draw_rng("canonical_profile")
    strict_profile = (
        slot == 0
        and not _has_override(ctx, "grid_h")
        and not _has_override(ctx, "grid_w")
        and profile_rng.random() < 0.65
    )

    if strict_profile:
        h = ctx.draw_int("grid_h", 10, 10)
        w = ctx.draw_int("grid_w", 14, 14)
    else:
        if difficulty == "easy":
            h_bounds, w_bounds = (9, 11), (13, 15)
        elif difficulty == "hard":
            h_bounds, w_bounds = (12, 18), (16, 24)
        else:
            h_bounds, w_bounds = (10, 14), (14, 19)
        h = _draw_axis_int(ctx, "grid_h", h_bounds, (9, 18))
        w = _draw_axis_int(ctx, "grid_w", w_bounds, (13, 24))

    sep = 2
    lower_h = h - sep - 1
    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)
    for c in range(w):
        grid[sep][c] = 5

    if strict_profile:
        template = _CANONICAL_TEMPLATE
        frame_sizes = ((4, 4), (4, 4 if rng.random() < 0.5 else 5))
    else:
        # Demonstration slots 1 and 2 draw from disjoint template families, so
        # every three-example lesson varies the template rather than allowing a
        # fixed-template shortcut by chance.  Other slots retain full variety.
        if slot == 1:
            template = rng.choice(_ASYMMETRIC_TEMPLATES[:2])
        elif slot == 2:
            template = rng.choice(_ASYMMETRIC_TEMPLATES[2:])
        else:
            template = rng.choice(_ASYMMETRIC_TEMPLATES)
        frame_sizes = _draw_general_frame_sizes(rng, lower_h, w, slot)

    template_col = rng.randint(0, w - 2)
    for dr in range(2):
        for dc in range(2):
            grid[dr][template_col + dc] = template[dr][dc]

    colors = list(_FRAME_COLOR_SCHEDULE[slot])
    if not strict_profile and rng.random() < 0.5:
        colors.reverse()
    (fh1, fw1), (fh2, fw2) = frame_sizes
    total_w = fw1 + 1 + fw2
    left = rng.randint(0, w - total_w)
    placements = [
        (rng.randint(0, lower_h - fh1), left, fh1, fw1, colors[0]),
        (rng.randint(0, lower_h - fh2), left + fw1 + 1, fh2, fw2, colors[1]),
    ]
    for local_r, c0, fh, fw, color in placements:
        r0 = sep + 1 + local_r
        draw_frame(grid, r0, c0, r0 + fh - 1, c0 + fw - 1, color)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError(f"internal generator invariant failure: {errors}")
    return grid
