"""Semantic generator for ARC task ``d65971416c2d``.

Read the first top-row value in 1..4 as a rotation code.  Select the first
4-connected red(2) component in row-major order, normalize and rotate it, then
stamp it in green(3) with its top-left cell at the cyan(8) anchor on an
otherwise blank output grid.

The control value 2 is itself red.  Because it is on the top row, that singleton
is intentionally the first red component; code-2 examples therefore stamp one
green cell even when a larger red shape appears later in the input.  The
curriculum makes that easily missed selection branch explicit.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "d65971416c2d"
TASK_ID = GENERATOR_ID
VERSION = "3.1.1"
RULE_HASH = "93b94c98bc36"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "Read the first top-row control in {1,2,3,4}. Select the first "
    "row-major 4-connected red(2) component, normalize it, rotate it by "
    "1=identity, 2=clockwise, 3=180 degrees, or 4=counterclockwise, and "
    "stamp the result in green(3) at the cyan(8) anchor on a blank grid. "
    "When the control is 2, the red control singleton itself is the selected "
    "component."
)

INVARIANTS = [
    "literal color 0 is the background",
    "exactly one top-row cell has a value in 1..4 and is the rotation control",
    "exactly one cyan(8) anchor marks the output stamp's top-left cell",
    "the first row-major 4-connected red(2) component is the selected shape",
    "a red control value 2 is intentionally selected before every later red component",
    "the selected normalized shape fits at the anchor after rotation",
    "all non-selected objects are distractors and the output is otherwise zero",
]

SIZE_PROFILES = (
    "h10_w12",
    "h11_w11",
    "h9_w13",
    "h12_w10",
    "h10_w10",
    "h13_w13",
)
_SIZE_ROWS = (
    ("h10_w12", 10, 12),
    ("h11_w11", 11, 11),
    ("h9_w13", 9, 13),
    ("h12_w10", 12, 10),
    ("h10_w10", 10, 10),
    ("h13_w13", 13, 13),
)
_SIZE_BY_PROFILE = {name: (height, width) for name, height, width in _SIZE_ROWS}
_PROFILE_BY_SIZE = {(height, width): name for name, height, width in _SIZE_ROWS}

TEMPLATE_PROFILES = ("tri_l", "tetra_t", "tetra_j", "tetra_l")
_TEMPLATE_ROWS = (
    ("tri_l", ((0, 0), (1, 0), (1, 1))),
    ("tetra_t", ((0, 1), (1, 0), (1, 1), (2, 1))),
    ("tetra_j", ((0, 0), (0, 1), (1, 1), (2, 1))),
    ("tetra_l", ((0, 0), (0, 1), (1, 0), (2, 0))),
)
_TEMPLATE_BY_PROFILE = {name: cells for name, cells in _TEMPLATE_ROWS}
_PROFILE_BY_TEMPLATE = {cells: name for name, cells in _TEMPLATE_ROWS}

ANCHOR_ZONES = ("upper_left", "upper_right", "lower_right", "lower_left")
SCHEDULE_PROFILES = (
    "identity_canonical_anchor",
    "red_control_singleton",
    "half_turn_canonical_anchor",
    "quarter_turn_selection_pressure",
)

AXES = {
    "size_profile": {
        "type": "str",
        "default": "deterministic keyed choice",
        "valid": "|".join(SIZE_PROFILES),
    },
    "control_code": {
        "type": "int",
        "default": "four-slot schedule",
        "valid": "1..4",
    },
    "template_profile": {
        "type": "str",
        "default": "deterministic keyed choice",
        "valid": "|".join(TEMPLATE_PROFILES),
    },
    "anchor_zone": {
        "type": "str",
        "default": "four-slot schedule",
        "valid": "|".join(ANCHOR_ZONES),
    },
    "extra_red": {
        "type": "bool",
        "default": "false,true,false,true schedule",
        "valid": "true|false",
    },
    "decoy_count": {
        "type": "int",
        "default": "1,2,1,2 schedule",
        "valid": "1..2",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_CANONICAL_LINKED_PROFILES = {
    (10, 12, 5),
    (11, 11, 4),
    (9, 13, 5),
    (12, 10, 5),
    (10, 10, 4),
}

_EXTRA_RED_SHAPE = (
    (0, 0),
    (0, 1),
    (1, 0),
    (2, 0),
    (2, 1),
    (2, 2),
)

_DECOY_SHAPES = (
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (0, 3)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
)


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Name the four-slot teaching schedule used by ordinary draws."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    materialized = tuple(cells)
    if not materialized:
        return ()
    min_row = min(row for row, _ in materialized)
    min_col = min(col for _, col in materialized)
    return tuple(sorted((row - min_row, col - min_col) for row, col in materialized))


def _turn_once(cells: Sequence[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _normalize((col, -row) for row, col in cells)


def _rotate(cells: Sequence[tuple[int, int]], code: int) -> tuple[tuple[int, int], ...]:
    result = _normalize(cells)
    turns = {1: 0, 2: 1, 3: 2, 4: 3}.get(int(code), 0)
    for _ in range(turns):
        result = _turn_once(result)
    return result


def _shape_dims(cells: Sequence[tuple[int, int]]) -> tuple[int, int]:
    return (
        max(row for row, _ in cells) + 1,
        max(col for _, col in cells) + 1,
    )


def _component_rows(grid: Sequence[Sequence[int]], color: int) -> list[dict[str, Any]]:
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))
            ordered = tuple(sorted(cells))
            result.append(
                {
                    "color": color,
                    "cells": frozenset(cells),
                    "first": ordered[0],
                    "size": len(cells),
                    "shape": _normalize(cells),
                    "bbox": (
                        min(r for r, _ in cells),
                        min(c for _, c in cells),
                        max(r for r, _ in cells),
                        max(c for _, c in cells),
                    ),
                }
            )
    return result


def _all_component_rows(grid: Sequence[Sequence[int]]) -> list[dict[str, Any]]:
    colors = sorted({value for row in grid for value in row if value != 0})
    result: list[dict[str, Any]] = []
    for color in colors:
        result.extend(_component_rows(grid, color))
    return sorted(result, key=lambda item: item["first"])


def _anchor_zone(row: int, col: int, height: int, width: int) -> str:
    vertical = "upper" if row < height // 2 else "lower"
    horizontal = "left" if col < width // 2 else "right"
    return f"{vertical}_{horizontal}"


def _coerce_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None, ["grid must be rectangular"]
    copied = [list(row) for row in grid]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in copied
        for value in row
    ):
        return None, ["cells must be integer ARC colors 0..9"]
    return copied, []


def _analyze(grid: Any) -> dict[str, Any]:
    copied, errors = _coerce_grid(grid)
    result: dict[str, Any] = {"errors": errors}
    if copied is None:
        return result

    height = len(copied)
    width = len(copied[0])
    palette = {value for row in copied for value in row}
    result.update({"grid": copied, "height": height, "width": width, "palette": palette})

    if not 8 <= height <= 16 or not 8 <= width <= 16:
        errors.append(f"grid dimensions must be within 8..16, found {height}x{width}")
    if 0 not in palette:
        errors.append("literal background color 0 is missing")
    if sum(value == 0 for row in copied for value in row) < height * width * 2 // 3:
        errors.append("background 0 must occupy at least two thirds of the grid")

    controls = [(col, copied[0][col]) for col in range(width) if copied[0][col] in (1, 2, 3, 4)]
    anchors = [(row, col) for row in range(height) for col in range(width) if copied[row][col] == 8]
    result.update({"controls": controls, "anchors": anchors})
    if len(controls) != 1:
        errors.append(f"expected exactly one top-row control in 1..4, found {len(controls)}")
    if len(anchors) != 1:
        errors.append(f"expected exactly one cyan(8) anchor cell, found {len(anchors)}")
    if errors and (len(controls) != 1 or len(anchors) != 1):
        return result

    control_col, control_code = controls[0]
    control_cell = (0, control_col)
    anchor = anchors[0]
    result.update(
        {
            "control_col": control_col,
            "control_code": control_code,
            "control_cell": control_cell,
            "anchor": anchor,
            "anchor_zone": _anchor_zone(anchor[0], anchor[1], height, width),
        }
    )
    if anchor[0] == 0:
        errors.append("cyan anchor must be below the control row")

    same_color_component = next(
        (component for component in _component_rows(copied, control_code) if control_cell in component["cells"]),
        None,
    )
    if same_color_component is None or same_color_component["size"] != 1:
        errors.append("the top-row control must be an isolated singleton of its color")

    red_components = _component_rows(copied, 2)
    noncontrol_red = [component for component in red_components if control_cell not in component["cells"]]
    result.update({"red_components": red_components, "noncontrol_red": noncontrol_red})
    if not red_components:
        errors.append("expected at least one red(2) component")
        return result
    if not 1 <= len(noncontrol_red) <= 2:
        errors.append(
            "expected one visible red template and at most one later red distractor"
        )
        return result

    visible_template = noncontrol_red[0]
    result["visible_template"] = visible_template
    template_profile = _PROFILE_BY_TEMPLATE.get(visible_template["shape"])
    result["template_profile"] = template_profile
    if template_profile is None:
        errors.append(
            "the first non-control red component must use a declared canonical template morphology"
        )
    if visible_template["first"][0] == 0:
        errors.append("the visible red template must be below the control row")
    if len(noncontrol_red) == 2 and noncontrol_red[1]["first"] <= visible_template["first"]:
        errors.append("the optional red distractor must occur after the visible template in row-major order")

    selected = red_components[0]
    result["selected_red"] = selected
    if control_code == 2 and control_cell not in selected["cells"]:
        errors.append("red control 2 must be the first red component")
    if control_code != 2 and selected is not visible_template:
        errors.append("the visible template must be the first red component for controls 1, 3, and 4")

    rotated = _rotate(selected["shape"], control_code)
    stamp_height, stamp_width = _shape_dims(rotated)
    result.update(
        {
            "rotated_selected_shape": rotated,
            "stamp_shape": (stamp_height, stamp_width),
            "extra_red": len(noncontrol_red) == 2,
        }
    )
    if anchor[0] + stamp_height > height or anchor[1] + stamp_width > width:
        errors.append("rotated selected shape must fit fully at the cyan anchor")

    components = _all_component_rows(copied)
    special_cells = set().union(*(component["cells"] for component in red_components))
    special_cells.add(anchor)
    special_cells.add(control_cell)
    decoys = [component for component in components if component["cells"].isdisjoint(special_cells)]
    result.update({"components": components, "decoys": decoys, "decoy_count": len(decoys)})
    if not 1 <= len(decoys) <= 2:
        errors.append(f"expected one or two non-special distractor components, found {len(decoys)}")
    for component in decoys:
        if not 2 <= component["size"] <= 6:
            errors.append("each distractor component must contain 2..6 cells")
        if component["color"] in (0, 2, 8):
            errors.append("distractors must not use background, red, or cyan")
        if any(row == 0 and copied[row][col] in (1, 2, 3, 4) for row, col in component["cells"]):
            errors.append("a distractor must not create a second top-row control")

    return result


def _expanded(
    cells: Iterable[tuple[int, int]],
    height: int,
    width: int,
    radius: int = 1,
) -> set[tuple[int, int]]:
    result: set[tuple[int, int]] = set()
    for row, col in cells:
        for delta_row in range(-radius, radius + 1):
            for delta_col in range(-radius, radius + 1):
                next_row = row + delta_row
                next_col = col + delta_col
                if 0 <= next_row < height and 0 <= next_col < width:
                    result.add((next_row, next_col))
    return result


def _translated(
    shape: Sequence[tuple[int, int]], top: int, left: int
) -> set[tuple[int, int]]:
    return {(top + row, left + col) for row, col in shape}


def _pick_shape_position(
    rng,
    shape: Sequence[tuple[int, int]],
    height: int,
    width: int,
    blocked: set[tuple[int, int]],
    *,
    minimum_row: int = 0,
    after: tuple[int, int] | None = None,
) -> set[tuple[int, int]] | None:
    shape_height, shape_width = _shape_dims(shape)
    candidates = [
        (top, left)
        for top in range(minimum_row, height - shape_height + 1)
        for left in range(0, width - shape_width + 1)
    ]
    rng.shuffle(candidates)
    for top, left in candidates:
        cells = _translated(shape, top, left)
        if after is not None and min(cells) <= after:
            continue
        if cells & blocked:
            continue
        return cells
    return None


def _anchor_candidates(
    height: int,
    width: int,
    stamp_height: int,
    stamp_width: int,
    zone: str,
) -> list[tuple[int, int]]:
    result = []
    for row in range(1, height - stamp_height + 1):
        for col in range(0, width - stamp_width + 1):
            if _anchor_zone(row, col, height, width) == zone:
                result.append((row, col))
    return result


def _construct_scene(
    ctx,
    *,
    height: int,
    width: int,
    code: int,
    template_shape: Sequence[tuple[int, int]],
    anchor_zone: str,
    extra_red: bool,
    decoy_count: int,
    strict_slot: bool,
    band: str,
) -> list[list[int]]:
    # Difficulty is not a semantic axis, but it must select a disjoint,
    # replayable layout stream so easy/medium/hard are not byte-identical.
    layout_rng = ctx.draw_rng(f"layout:{band}")
    control_col = 0 if strict_slot else layout_rng.randint(1, width - 1)
    selected_shape = ((0, 0),) if code == 2 else tuple(template_shape)
    rotated = _rotate(selected_shape, code)
    stamp_height, stamp_width = _shape_dims(rotated)
    # The code-2 answer is a singleton, but the anchor must also leave room
    # for the visible red template under the tempting skip-control rival.
    # Otherwise clipping can make that wrong rule produce the same one-cell
    # answer and hide the decisive red-control selection branch.
    teaching_shape = _rotate(template_shape, code)
    teaching_height, teaching_width = _shape_dims(teaching_shape)
    anchors = _anchor_candidates(
        height,
        width,
        max(stamp_height, teaching_height),
        max(stamp_width, teaching_width),
        anchor_zone,
    )
    layout_rng.shuffle(anchors)
    if not anchors:
        raise ValueError(
            f"no {anchor_zone} anchor fits a {stamp_height}x{stamp_width} stamp"
        )

    decoy_colors = ctx.draw_distinct_colors(
        "decoy_colors",
        n=decoy_count,
        exclude={0, 1, 2, 3, 4, 8},
    )
    decoy_shape_rng = ctx.draw_rng(f"decoy_shapes:{band}")
    decoy_shapes = [decoy_shape_rng.choice(_DECOY_SHAPES) for _ in range(decoy_count)]

    for anchor in anchors:
        grid = full_grid(height, width, 0)
        grid[0][control_col] = code
        grid[anchor[0]][anchor[1]] = 8

        stamp_cells = _translated(rotated, anchor[0], anchor[1])
        occupied = {(0, control_col), anchor}
        blocked = _expanded(occupied | stamp_cells, height, width)

        main_cells = _pick_shape_position(
            layout_rng,
            template_shape,
            height,
            width,
            blocked,
            minimum_row=2,
        )
        if main_cells is None:
            continue
        for row, col in main_cells:
            grid[row][col] = 2
        occupied.update(main_cells)
        blocked = _expanded(occupied | stamp_cells, height, width)

        if extra_red:
            extra_cells = _pick_shape_position(
                layout_rng,
                _EXTRA_RED_SHAPE,
                height,
                width,
                blocked,
                minimum_row=2,
                after=min(main_cells),
            )
            if extra_cells is None:
                continue
            for row, col in extra_cells:
                grid[row][col] = 2
            occupied.update(extra_cells)
            blocked = _expanded(occupied | stamp_cells, height, width)

        placed_decoys: list[set[tuple[int, int]]] = []
        failed = False
        for shape in decoy_shapes:
            cells = _pick_shape_position(
                layout_rng,
                shape,
                height,
                width,
                blocked,
                minimum_row=0,
            )
            if cells is None:
                failed = True
                break
            placed_decoys.append(cells)
            occupied.update(cells)
            blocked = _expanded(occupied | stamp_cells, height, width)
        if failed:
            continue

        for color, cells in zip(decoy_colors, placed_decoys):
            for row, col in cells:
                grid[row][col] = color
        return grid

    raise ValueError("could not place a separated control/template/anchor scene")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, replayable task input."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    band = _band(difficulty)
    slot = int(sample_index) % len(SCHEDULE_PROFILES)
    scheduled = dict(overrides)
    scheduled.setdefault("control_code", slot + 1)
    scheduled.setdefault("anchor_zone", ANCHOR_ZONES[slot])
    scheduled.setdefault("extra_red", slot in (1, 3))
    scheduled.setdefault("decoy_count", 1 if slot in (0, 2) else 2)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=scheduled,
    )
    size_profile = ctx.draw_choice("size_profile", SIZE_PROFILES)
    control_code = ctx.draw_int("control_code", 1, 4)
    template_profile = ctx.draw_choice("template_profile", TEMPLATE_PROFILES)
    anchor_zone = ctx.draw_choice("anchor_zone", ANCHOR_ZONES)
    extra_red = ctx.draw_choice("extra_red", (False, True))
    decoy_count = ctx.draw_int("decoy_count", 1, 2)

    height, width = _SIZE_BY_PROFILE[size_profile]
    grid = _construct_scene(
        ctx,
        height=height,
        width=width,
        code=control_code,
        template_shape=_TEMPLATE_BY_PROFILE[template_profile],
        anchor_zone=anchor_zone,
        extra_red=extra_red,
        decoy_count=decoy_count,
        strict_slot=slot in (0, 2),
        band=band,
    )
    errors = self_check(grid, difficulty=band, meta=ctx.recorded_draws())
    if errors:
        raise AssertionError("generated invalid scene: " + "; ".join(errors))
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete teaching grammar and optional exact-axis claims."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        requested.update({name: meta[name] for name in AXES if name in meta})
        nested = meta.get("overrides")
        if isinstance(nested, dict):
            requested.update({name: nested[name] for name in AXES if name in nested})
    if requested:
        try:
            observed = observe_overrides(grid)
        except ValueError as exc:
            errors.append(f"exact axes could not be observed: {exc}")
        else:
            for name, expected in requested.items():
                if expected is not None and observed.get(name) != expected:
                    errors.append(
                        f"axis {name!r} requested {expected!r}, realized {observed.get(name)!r}"
                    )
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact AXES value from the returned grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    try:
        size_profile = _PROFILE_BY_SIZE[(analysis["height"], analysis["width"])]
    except KeyError as exc:
        raise ValueError("grid dimensions do not name a declared size_profile") from exc
    if analysis["template_profile"] is None:
        raise ValueError("visible template does not name a declared template_profile")
    return {
        "size_profile": size_profile,
        "control_code": analysis["control_code"],
        "template_profile": analysis["template_profile"],
        "anchor_zone": analysis["anchor_zone"],
        "extra_red": analysis["extra_red"],
        "decoy_count": analysis["decoy_count"],
    }


def strict_canonical_like(grid) -> list[str]:
    """Return reasons when a scene leaves the linked empirical manifold."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analyze(grid)
    reasons: list[str] = []
    linked_profile = (
        analysis["height"],
        analysis["width"],
        len(analysis["palette"]),
    )
    if linked_profile not in _CANONICAL_LINKED_PROFILES:
        reasons.append(
            "(height, width, palette-size) is not one of the five canonical linked profiles"
        )
    if analysis["control_col"] != 0:
        reasons.append("canonical controls are all in column 0")
    if analysis["extra_red"]:
        reasons.append("canonical inputs contain exactly one non-control red component")
    if analysis["decoy_count"] != 1:
        reasons.append("canonical inputs contain exactly one non-special distractor component")
    if analysis["decoys"][0]["size"] not in (3, 4):
        reasons.append("canonical distractors contain three or four cells")
    return reasons


def _first_control(grid: Sequence[Sequence[int]]) -> tuple[int, int]:
    for col, value in enumerate(grid[0]):
        if value in (1, 2, 3, 4):
            return col, value
    return -1, 1


def _first_anchor(grid: Sequence[Sequence[int]]) -> tuple[int, int]:
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 8:
                return row, col
    raise ValueError("no cyan anchor")


def _render_component_rule(
    grid: Sequence[Sequence[int]],
    component: dict[str, Any],
    code: int,
) -> list[list[int]]:
    height = len(grid)
    width = len(grid[0])
    anchor_row, anchor_col = _first_anchor(grid)
    shape = _rotate(component["shape"], code)
    output = full_grid(height, width, 0)
    for delta_row, delta_col in shape:
        row = anchor_row + delta_row
        col = anchor_col + delta_col
        if 0 <= row < height and 0 <= col < width:
            output[row][col] = 3
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python audit mirror of the canonical Racket authority."""
    copied, errors = _coerce_grid(grid)
    if copied is None:
        raise ValueError("; ".join(errors))
    _, code = _first_control(copied)
    red_components = _component_rows(copied, 2)
    if not red_components:
        raise ValueError("no red component")
    return _render_component_rule(copied, red_components[0], code)


def _rival_no_rotation(grid) -> list[list[int]]:
    copied, errors = _coerce_grid(grid)
    if copied is None:
        raise ValueError("; ".join(errors))
    red_components = _component_rows(copied, 2)
    return _render_component_rule(copied, red_components[0], 1)


def _rival_skip_control_red(grid) -> list[list[int]]:
    copied, errors = _coerce_grid(grid)
    if copied is None:
        raise ValueError("; ".join(errors))
    control_col, code = _first_control(copied)
    control_cell = (0, control_col)
    red_components = [
        component
        for component in _component_rows(copied, 2)
        if control_cell not in component["cells"]
    ]
    if not red_components:
        return rule_mirror(copied)
    return _render_component_rule(copied, red_components[0], code)


def _rival_largest_red(grid) -> list[list[int]]:
    copied, errors = _coerce_grid(grid)
    if copied is None:
        raise ValueError("; ".join(errors))
    _, code = _first_control(copied)
    red_components = _component_rows(copied, 2)
    largest = max(red_components, key=lambda component: component["size"])
    return _render_component_rule(copied, largest, code)


def _rival_control_at_col0(grid) -> list[list[int]]:
    copied, errors = _coerce_grid(grid)
    if copied is None:
        raise ValueError("; ".join(errors))
    code = copied[0][0] if copied[0][0] in (1, 2, 3, 4) else 1
    red_components = _component_rows(copied, 2)
    return _render_component_rule(copied, red_components[0], code)


def _rival_always_clockwise(grid) -> list[list[int]]:
    copied, errors = _coerce_grid(grid)
    if copied is None:
        raise ValueError("; ".join(errors))
    red_components = _component_rows(copied, 2)
    return _render_component_rule(copied, red_components[0], 2)


def _differs(grid, rival: Callable[[Any], list[list[int]]]) -> bool:
    try:
        return rival(grid) != rule_mirror(grid)
    except (TypeError, ValueError, IndexError):
        return False


def _witness_code(grid, code: int, rival: Callable[[Any], list[list[int]]]) -> bool:
    analysis = _analyze(grid)
    return (
        not analysis["errors"]
        and analysis["control_code"] == code
        and _differs(grid, rival)
    )


def _witness_first_not_largest(grid) -> bool:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return False
    red_components = analysis["red_components"]
    return (
        len(red_components) > 1
        and red_components[0]["size"] < max(component["size"] for component in red_components)
        and _differs(grid, _rival_largest_red)
    )


def _witness_control_not_col0(grid) -> bool:
    analysis = _analyze(grid)
    return (
        not analysis["errors"]
        and analysis["control_col"] != 0
        and _differs(grid, _rival_control_at_col0)
    )


SEMANTIC_RIVALS = {
    "always_identity": _rival_no_rotation,
    "skip_red_control": _rival_skip_control_red,
    "select_largest_red": _rival_largest_red,
    "control_only_at_col0": _rival_control_at_col0,
    "always_clockwise": _rival_always_clockwise,
}

SEMANTIC_WITNESSES = {
    "control_1_identity": lambda grid: _witness_code(grid, 1, _rival_always_clockwise),
    "control_2_selects_red_control": lambda grid: _witness_code(grid, 2, _rival_skip_control_red),
    "control_3_half_turn": lambda grid: _witness_code(grid, 3, _rival_no_rotation),
    "control_4_counterclockwise": lambda grid: _witness_code(grid, 4, _rival_no_rotation),
    "first_red_is_not_largest": _witness_first_not_largest,
    "control_is_not_fixed_to_col0": _witness_control_not_col0,
}

WITNESS_RIVALS = {
    "control_1_identity": ["always_clockwise"],
    "control_2_selects_red_control": ["skip_red_control"],
    "control_3_half_turn": ["always_identity"],
    "control_4_counterclockwise": ["always_identity"],
    "first_red_is_not_largest": ["select_largest_red"],
    "control_is_not_fixed_to_col0": ["control_only_at_col0"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named plausible rival survives its demos."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
            changes_query = rival(query["input"]) != query["output"]
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            reasons.append(f"competitor {name} could not be scored: {type(exc).__name__}: {exc}")
            continue
        if fits and changes_query:
            reasons.append(f"competitor {name} fits every demo but changes the query answer")
    return reasons
