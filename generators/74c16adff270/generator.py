"""Semantic generator for ARC task ``74c16adff270``.

Treat the connected blue(1) object as a normalized template.  A single
control color encodes clockwise quarter-turns (2→0, 3→1, 4→2, 6→3).  Stamp
the rotated template in gray(8) with its normalized top-left at the single
orange(7) anchor on an otherwise blank output grid.

Ordinary draws choose one complete canonical profile first (dimensions,
control, and template morphology stay linked), then vary only observable
nuisance placement axes.  A four-slot sample-index schedule exposes all four
control branches in every four-example sliding window.
"""
from __future__ import annotations

import hashlib
from collections import deque
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "74c16adff270"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "69c529d368d9"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Read the unique control cell: 2 means identity, 3 one clockwise turn, "
    "4 a half-turn, and 6 one counterclockwise turn. Normalize the connected "
    "blue(1) template, apply that rotation, and stamp it in gray(8) with its "
    "top-left at the orange(7) anchor on a fresh zero background. Ordinary "
    "draws preserve one of the five linked canonical dimension/control/shape "
    "profiles while varying role order and horizontal placement."
)

INVARIANTS = [
    "literal color 0 is the background",
    "exactly one 4-connected blue(1) template is present",
    "exactly one orange(7) anchor is present",
    "exactly one control cell has color 2, 3, 4, or 6",
    "the normalized rotated template fits at the anchor without touching another input role",
    "ordinary draws use one complete canonical dimension/control/template profile",
]


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _rotate_once(cells: Sequence[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = _normalize(cells)
    height = max(row for row, _ in cells) + 1
    return _normalize((col, height - 1 - row) for row, col in cells)


def _rotate(cells: Sequence[tuple[int, int]], turns: int) -> tuple[tuple[int, int], ...]:
    result = _normalize(cells)
    for _ in range(int(turns) % 4):
        result = _rotate_once(result)
    return result


def _shape_dims(cells: Sequence[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(cells)
    return max(row for row, _ in cells) + 1, max(col for _, col in cells) + 1


_PROFILE_ROWS = (
    (
        "ctrl2_stair6_w14",
        12,
        14,
        2,
        ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2)),
    ),
    (
        "ctrl3_t4_w15",
        12,
        15,
        3,
        ((0, 1), (1, 0), (1, 1), (1, 2)),
    ),
    (
        "ctrl4_cap5_w13",
        12,
        13,
        4,
        ((0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    ),
    (
        "ctrl6_hook5_w14",
        12,
        14,
        6,
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
    ),
    (
        "ctrl6_zig5_w12",
        12,
        12,
        6,
        ((0, 1), (1, 0), (1, 1), (2, 0), (2, 1)),
    ),
)
CANONICAL_PROFILES = tuple(row[0] for row in _PROFILE_ROWS)
_PROFILE_BY_NAME = {
    name: {"height": height, "width": width, "control": control, "shape": _normalize(shape)}
    for name, height, width, control, shape in _PROFILE_ROWS
}
_PROFILE_BY_SIGNATURE = {
    (height, width, control, _normalize(shape)): name
    for name, height, width, control, shape in _PROFILE_ROWS
}
_CANONICAL_SIGNATURES = frozenset(_PROFILE_BY_SIGNATURE)
_PROFILES_BY_CONTROL = {
    control: tuple(name for name, _, _, value, _ in _PROFILE_ROWS if value == control)
    for control in (2, 3, 4, 6)
}

_ROLE_NAMES = ("template", "anchor", "control")
LAYOUT_PROFILES = (
    "template_anchor_control",
    "template_control_anchor",
    "anchor_template_control",
    "anchor_control_template",
    "control_template_anchor",
    "control_anchor_template",
)
COLUMN_ZONES = ("left", "center", "right")
ROW_PROFILES = ("rows_0_4_8", "rows_0_4_9", "rows_0_5_9", "rows_1_5_9")
_ROW_STARTS = {
    "rows_0_4_8": (0, 4, 8),
    "rows_0_4_9": (0, 4, 9),
    "rows_0_5_9": (0, 5, 9),
    "rows_1_5_9": (1, 5, 9),
}
_ROW_PROFILE_BY_STARTS = {starts: name for name, starts in _ROW_STARTS.items()}

AXES = {
    "canonical_profile": {
        "type": "str",
        "default": "four-slot control schedule over linked canonical profiles",
        "valid": "ctrl2_stair6_w14|ctrl3_t4_w15|ctrl4_cap5_w13|ctrl6_hook5_w14|ctrl6_zig5_w12",
    },
    "layout_profile": {
        "type": "str",
        "default": "difficulty-rotated teaching schedule",
        "valid": "template_anchor_control|template_control_anchor|anchor_template_control|anchor_control_template|control_template_anchor|control_anchor_template",
    },
    "row_profile": {
        "type": "str",
        "default": "deterministic keyed choice",
        "valid": "rows_0_4_8|rows_0_4_9|rows_0_5_9|rows_1_5_9",
    },
    "template_col_zone": {
        "type": "str",
        "default": "deterministic keyed choice",
        "valid": "left|center|right",
    },
    "anchor_col_zone": {
        "type": "str",
        "default": "deterministic keyed choice",
        "valid": "left|center|right",
    },
    "control_col_zone": {
        "type": "str",
        "default": "deterministic keyed choice",
        "valid": "left|center|right",
    },
}


HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_CONTROL_TURNS = {2: 0, 3: 1, 4: 2, 6: 3}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def schedule_layout(sample_index: int, difficulty=None) -> str:
    """Use difficulty only to rotate the observable role-order curriculum."""
    band = _band(difficulty)
    offset = {"easy": 0, "medium": 2, "hard": 4}[band]
    return LAYOUT_PROFILES[(int(sample_index) + offset) % len(LAYOUT_PROFILES)]


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the linked profile used by the four-slot teaching schedule."""
    del difficulty
    control = (2, 3, 4, 6)[int(sample_index) % 4]
    options = _PROFILES_BY_CONTROL[control]
    if len(options) == 1:
        return options[0]
    digest = hashlib.sha256(f"{seed}|{sample_index}|ctrl6-profile".encode()).digest()
    return options[digest[0] % len(options)]


def _zone_ranges(width: int, object_width: int) -> dict[str, range]:
    max_start = width - object_width
    if max_start < 5:
        raise ValueError("grid is too narrow for observable column zones")
    count = max_start + 1
    first_cut = max(1, count // 3)
    second_cut = min(count - 1, count - count // 3)
    return {
        "left": range(0, first_cut),
        "center": range(first_cut, second_cut),
        "right": range(second_cut, count),
    }


def _col_candidates(zone: str, width: int, object_width: int) -> tuple[int, ...]:
    try:
        values = tuple(_zone_ranges(width, object_width)[zone])
    except KeyError as exc:
        raise ValueError(f"unknown column zone {zone!r}") from exc
    if not values:
        raise ValueError(f"no legal {zone} placement for width={width}, object_width={object_width}")
    return values


def _column_zone(start: int, width: int, object_width: int) -> str:
    for zone, values in _zone_ranges(width, object_width).items():
        if start in values:
            return zone
    raise ValueError("column start is outside the declared zones")


def _component(cells: set[tuple[int, int]], start: tuple[int, int]) -> set[tuple[int, int]]:
    seen = {start}
    queue = deque([start])
    while queue:
        row, col = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nxt = (row + dr, col + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen


def _min_chebyshev(left: Iterable[tuple[int, int]], right: Iterable[tuple[int, int]]) -> int:
    left = tuple(left)
    right = tuple(right)
    return min(max(abs(ar - br), abs(ac - bc)) for ar, ac in left for br, bc in right)


def _coerce_grid(grid) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, list) or not grid:
        return None, ["grid must be a non-empty list"]
    if not all(isinstance(row, list) for row in grid):
        return None, ["every row must be a list"]
    width = len(grid[0]) if grid[0] else 0
    if width == 0 or any(len(row) != width for row in grid):
        return None, ["grid must be non-empty and rectangular"]
    if any(not isinstance(value, int) for row in grid for value in row):
        return None, ["grid values must be integers"]
    return [row[:] for row in grid], []


def _analyze(grid) -> dict[str, Any]:
    copied, errors = _coerce_grid(grid)
    result: dict[str, Any] = {"errors": errors}
    if copied is None:
        return result

    height = len(copied)
    width = len(copied[0])
    palette = {value for row in copied for value in row}
    template = {(row, col) for row, values in enumerate(copied) for col, value in enumerate(values) if value == 1}
    anchors = [(row, col) for row, values in enumerate(copied) for col, value in enumerate(values) if value == 7]
    controls = [
        (row, col, value)
        for row, values in enumerate(copied)
        for col, value in enumerate(values)
        if value in _CONTROL_TURNS
    ]
    result.update(
        {
            "grid": copied,
            "height": height,
            "width": width,
            "palette": palette,
            "template_cells": template,
            "anchors": anchors,
            "controls": controls,
        }
    )

    if not (8 <= height <= 30 and 8 <= width <= 30):
        errors.append(f"grid dimensions must be within 8..30; got {height}x{width}")
    illegal = sorted(palette - {0, 1, 2, 3, 4, 6, 7})
    if illegal:
        errors.append(f"unexpected input colors: {illegal}")
    if not template:
        errors.append("expected one non-empty blue(1) template")
    elif _component(template, next(iter(template))) != template:
        errors.append("blue(1) template must be one 4-connected component")
    if len(anchors) != 1:
        errors.append(f"expected exactly one orange(7) anchor; got {len(anchors)}")
    if len(controls) != 1:
        errors.append(f"expected exactly one control cell in {{2,3,4,6}}; got {len(controls)}")
    if errors:
        return result

    anchor = anchors[0]
    control_row, control_col, control = controls[0]
    shape = _normalize(template)
    turns = _CONTROL_TURNS[control]
    rotated = _rotate(shape, turns)
    stamp = {(anchor[0] + dr, anchor[1] + dc) for dr, dc in rotated}
    result.update(
        {
            "anchor": anchor,
            "control": control,
            "control_cell": (control_row, control_col),
            "shape": shape,
            "rotated_shape": rotated,
            "stamp_cells": stamp,
        }
    )

    if len(template) < 3 or len(template) > 8:
        errors.append(f"template must contain 3..8 cells; got {len(template)}")
    if any(not (0 <= row < height and 0 <= col < width) for row, col in stamp):
        errors.append("rotated template must fit fully at the anchor")
    if _min_chebyshev(template, [anchor]) <= 1:
        errors.append("template and anchor must be separated by at least one background cell")
    if _min_chebyshev(template, [(control_row, control_col)]) <= 1:
        errors.append("template and control must be separated by at least one background cell")
    if _min_chebyshev([anchor], [(control_row, control_col)]) <= 1:
        errors.append("anchor and control must be separated by at least one background cell")
    occupied_other = template | {(control_row, control_col)}
    if stamp & occupied_other:
        errors.append("the output stamp footprint must not overlap the template or control")
    return result


def canonical_profile_signature(grid) -> tuple[Any, ...] | None:
    """Return the linked canonical signature, or ``None`` for malformed input."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    return (
        analysis["height"],
        analysis["width"],
        analysis["control"],
        analysis["shape"],
    )


def _construct_scene(
    ctx,
    *,
    profile_name: str,
    layout_profile: str,
    row_profile: str,
    template_col_zone: str,
    anchor_col_zone: str,
    control_col_zone: str,
) -> list[list[int]]:
    profile = _PROFILE_BY_NAME[profile_name]
    height = profile["height"]
    width = profile["width"]
    control = profile["control"]
    shape = profile["shape"]
    rotated = _rotate(shape, _CONTROL_TURNS[control])
    shape_height, shape_width = _shape_dims(shape)
    stamp_height, stamp_width = _shape_dims(rotated)
    clearance_width = max(shape_height, shape_width)

    roles = layout_profile.split("_")
    if tuple(sorted(roles)) != tuple(sorted(_ROLE_NAMES)):
        raise ValueError(f"invalid layout_profile {layout_profile!r}")
    try:
        starts = _ROW_STARTS[row_profile]
    except KeyError as exc:
        raise ValueError(f"invalid row_profile {row_profile!r}") from exc
    row_base = {role: starts[index] for index, role in enumerate(roles)}
    rng = ctx.draw_rng("placement")

    template_row = row_base["template"]
    anchor_row = row_base["anchor"]
    control_row = row_base["control"]
    template_col = rng.choice(_col_candidates(template_col_zone, width, shape_width))
    anchor_col = rng.choice(_col_candidates(anchor_col_zone, width, clearance_width))
    control_col = rng.choice(_col_candidates(control_col_zone, width, 1))

    grid = full_grid(height, width, 0)
    for dr, dc in shape:
        grid[template_row + dr][template_col + dc] = 1
    grid[anchor_row][anchor_col] = 7
    grid[control_row][control_col] = control
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, fresh, structurally valid task input."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    band = _band(difficulty)
    scheduled = dict(overrides)
    scheduled.setdefault("canonical_profile", schedule_profile(seed, sample_index, band))
    scheduled.setdefault("layout_profile", schedule_layout(sample_index, band))
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=scheduled,
    )
    profile_name = ctx.draw_choice("canonical_profile", CANONICAL_PROFILES)
    layout_profile = ctx.draw_choice("layout_profile", LAYOUT_PROFILES)
    row_profile = ctx.draw_choice("row_profile", ROW_PROFILES)
    template_col_zone = ctx.draw_choice("template_col_zone", COLUMN_ZONES)
    anchor_col_zone = ctx.draw_choice("anchor_col_zone", COLUMN_ZONES)
    control_col_zone = ctx.draw_choice("control_col_zone", COLUMN_ZONES)

    grid = _construct_scene(
        ctx,
        profile_name=profile_name,
        layout_profile=layout_profile,
        row_profile=row_profile,
        template_col_zone=template_col_zone,
        anchor_col_zone=anchor_col_zone,
        control_col_zone=control_col_zone,
    )
    errors = self_check(grid, difficulty=band, meta=ctx.recorded_draws())
    if errors:
        raise AssertionError("generated invalid scene: " + "; ".join(errors))
    if strict_canonical_like(grid):
        raise AssertionError("ordinary draw left the canonical linked profile manifold")
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-valid structural grammar and exact axis claims."""
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
    """Recover every exact AXES value from a returned grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    signature = canonical_profile_signature(grid)
    profile_name = _PROFILE_BY_SIGNATURE.get(signature)
    if profile_name is None:
        raise ValueError("dimension/control/template tuple is not a declared canonical_profile")

    template_top = min(row for row, _ in analysis["template_cells"])
    role_rows = {
        "template": template_top,
        "anchor": analysis["anchor"][0],
        "control": analysis["control_cell"][0],
    }
    ordered_roles = tuple(sorted(role_rows, key=role_rows.get))
    layout_profile = "_".join(ordered_roles)
    starts = tuple(role_rows[role] for role in ordered_roles)
    row_profile = _ROW_PROFILE_BY_STARTS.get(starts)
    if row_profile is None:
        raise ValueError("role row starts do not name a declared row_profile")
    shape_height, shape_width = _shape_dims(analysis["shape"])
    del shape_height
    shape_height, shape_width = _shape_dims(analysis["shape"])
    clearance_width = max(shape_height, shape_width)
    template_left = min(col for _, col in analysis["template_cells"])
    return {
        "canonical_profile": profile_name,
        "layout_profile": layout_profile,
        "row_profile": row_profile,
        "template_col_zone": _column_zone(template_left, analysis["width"], shape_width),
        "anchor_col_zone": _column_zone(analysis["anchor"][1], analysis["width"], clearance_width),
        "control_col_zone": _column_zone(analysis["control_cell"][1], analysis["width"], 1),
    }


def strict_canonical_like(grid) -> list[str]:
    """Reject scenes outside the five linked empirical canonical profiles."""
    errors = self_check(grid)
    if errors:
        return errors
    signature = canonical_profile_signature(grid)
    if signature not in _CANONICAL_SIGNATURES:
        return [
            "(height, width, control, normalized template morphology) is not one linked canonical profile"
        ]
    return []


def _render_with_turns(grid, turns: int) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    shape = _rotate(analysis["shape"], turns)
    output = full_grid(analysis["height"], analysis["width"], 0)
    anchor_row, anchor_col = analysis["anchor"]
    for dr, dc in shape:
        row = anchor_row + dr
        col = anchor_col + dc
        if 0 <= row < analysis["height"] and 0 <= col < analysis["width"]:
            output[row][col] = 8
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python audit mirror of the canonical Racket authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _render_with_turns(grid, _CONTROL_TURNS[analysis["control"]])


def _rival_no_rotation(grid) -> list[list[int]]:
    return _render_with_turns(grid, 0)


def _rival_reverse_rotation(grid) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    turns = {2: 0, 3: 3, 4: 2, 6: 1}[analysis["control"]]
    return _render_with_turns(grid, turns)


def _rival_always_clockwise(grid) -> list[list[int]]:
    return _render_with_turns(grid, 1)


def _differs(grid, rival: Callable[[Any], list[list[int]]]) -> bool:
    try:
        return rival(grid) != rule_mirror(grid)
    except (TypeError, ValueError, IndexError):
        return False


def _witness_control(grid, control: int, rivals: Sequence[Callable[[Any], list[list[int]]]]) -> bool:
    analysis = _analyze(grid)
    return (
        not analysis["errors"]
        and analysis["control"] == control
        and all(_differs(grid, rival) for rival in rivals)
    )


SEMANTIC_RIVALS = {
    "ignore_control_no_rotation": _rival_no_rotation,
    "reverse_rotation_direction": _rival_reverse_rotation,
    "always_one_clockwise_turn": _rival_always_clockwise,
}

SEMANTIC_WITNESSES = {
    "control_2_identity": lambda grid: _witness_control(
        grid, 2, (_rival_always_clockwise,)
    ),
    "control_3_clockwise": lambda grid: _witness_control(
        grid, 3, (_rival_no_rotation, _rival_reverse_rotation)
    ),
    "control_4_half_turn": lambda grid: _witness_control(
        grid, 4, (_rival_no_rotation, _rival_always_clockwise)
    ),
    "control_6_counterclockwise": lambda grid: _witness_control(
        grid, 6, (_rival_no_rotation, _rival_reverse_rotation, _rival_always_clockwise)
    ),
}

WITNESS_RIVALS = {
    "control_2_identity": ["always_one_clockwise_turn"],
    "control_3_clockwise": ["ignore_control_no_rotation", "reverse_rotation_direction"],
    "control_4_half_turn": ["ignore_control_no_rotation", "always_one_clockwise_turn"],
    "control_6_counterclockwise": [
        "ignore_control_no_rotation",
        "reverse_rotation_direction",
        "always_one_clockwise_turn",
    ],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a plausible named rival survives all demos."""
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
