"""Input generator for completing exact red L-triominoes.

The immutable Racket authority finds same-color four-connected components,
selects red (2) components with exactly three cells and a 2x2 bounding box,
and paints every cell of each selected bounding box green (3).  The input
sampler below deliberately includes same-color and same-shape counterexamples,
occupied missing corners, and edge cases so four linked demonstrations identify
that exact rule instead of a color-only, size-only, or empty-corner shortcut.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "dadeacb21d08"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "4dc2707cc06e"

SUMMARY = (
    "Complete only red (2) same-color components that are exact three-cell "
    "L-triominoes in a 2x2 box. Paint the entire box green (3), overwriting "
    "even a non-red cell in the missing corner. Red lines, dominos, and full "
    "squares, plus non-red Ls and other components, remain unchanged. Four "
    "linked profiles expose shape, color, occupancy, count, and edge contrasts."
)

INVARIANTS = [
    "background is 0; generated inputs never contain output color 3",
    "every input contains 2..4 exact red L-triomino targets",
    "every input contains 1..3 red non-target components and 1..2 non-red decoy components",
    "target missing corners may be empty, occupied, or mixed; occupied corners are overwritten",
    "every four consecutive default examples cover all four curriculum profiles",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "linked four-profile schedule",
        "valid": "10..16",
        "doc": "Input grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "linked four-profile schedule",
        "valid": "10..16",
        "doc": "Input grid width.",
    },
    "n_target_l": {
        "type": "int",
        "default": "2, 3, 3, 4 by profile",
        "valid": "2..4",
        "doc": "Number of exact red L-triomino target components.",
    },
    "n_red_decoys": {
        "type": "int",
        "default": "3, 3, 2, 2 by profile",
        "valid": "1..3",
        "doc": "Number of red components that are deliberately not target Ls.",
    },
    "n_colored_decoys": {
        "type": "int",
        "default": "1, 2, 2, 2 by profile",
        "valid": "1..2",
        "doc": "Number of non-red decoy components, excluding occupied target holes.",
    },
    "hole_mode": {
        "type": "enum",
        "default": "linked four-profile schedule",
        "valid": ["empty", "occupied", "mixed"],
        "doc": "Whether target missing corners are empty, occupied, or include both states.",
    },
    "target_position": {
        "type": "enum",
        "default": "linked four-profile schedule",
        "valid": ["interior", "edge"],
        "doc": "Whether all target boxes are interior or at least one touches an edge.",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20
SCHEDULE_PROFILES = (0, 1, 2, 3)


_L_SHAPES: dict[str, tuple[tuple[int, int], ...]] = {
    "missing_nw": ((0, 1), (1, 0), (1, 1)),
    "missing_ne": ((0, 0), (1, 0), (1, 1)),
    "missing_sw": ((0, 0), (0, 1), (1, 1)),
    "missing_se": ((0, 0), (0, 1), (1, 0)),
}
_L_BY_CELLS = {cells: name for name, cells in _L_SHAPES.items()}
_ORIENTATIONS = tuple(_L_SHAPES)
_PROFILE_TARGET_ORIENTATIONS = (
    ("missing_se", "missing_nw", "missing_ne", "missing_sw"),
    ("missing_ne", "missing_sw", "missing_se", "missing_nw"),
    ("missing_nw", "missing_se", "missing_sw", "missing_ne"),
    ("missing_sw", "missing_ne", "missing_nw", "missing_se"),
)

_STRAIGHT_H = ((0, 0), (0, 1), (0, 2))
_STRAIGHT_V = ((0, 0), (1, 0), (2, 0))
_SQUARE = ((0, 0), (0, 1), (1, 0), (1, 1))
_DOMINO_H = ((0, 0), (0, 1))
_DOMINO_V = ((0, 0), (1, 0))
_NONRED_COLORS = (1, 4, 5, 6, 7, 8, 9)
_CANONICAL_DIMS = {(10, 10), (11, 11), (12, 12)}
_CANONICAL_PALETTES = (
    frozenset({0, 2, 5, 7, 8}),
    frozenset({0, 2, 5, 6, 9}),
    frozenset({0, 2, 8, 9}),
    frozenset({0, 2, 5}),
    frozenset({0, 2, 6, 7, 8}),
)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Return the seed-independent linked profile for this sample index."""
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _draw_int_axis(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _draw_choice_axis(ctx, overrides, label: str, default: str, options) -> str:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, tuple(options))
    return ctx.draw_choice(label, (default,))


def _profile_defaults(profile: int, difficulty: str | None) -> dict[str, Any]:
    band = "medium" if difficulty is None else difficulty
    if profile == 0:
        side = {"easy": 10, "medium": 11, "hard": 12}[band]
        return {
            "grid_h": side,
            "grid_w": side,
            "n_target_l": 2,
            "n_red_decoys": 3,
            "n_colored_decoys": 1,
            "hole_mode": "mixed",
            "target_position": "interior",
        }
    bump = {"easy": 0, "medium": 2, "hard": 4}[band]
    if profile == 1:
        return {
            "grid_h": 10 + bump,
            "grid_w": 12 + bump,
            "n_target_l": 3,
            "n_red_decoys": 3,
            "n_colored_decoys": 2,
            "hole_mode": "empty",
            "target_position": "interior",
        }
    if profile == 2:
        return {
            "grid_h": 11 + bump,
            "grid_w": 10 + bump,
            "n_target_l": 3,
            "n_red_decoys": 2,
            "n_colored_decoys": 2,
            "hole_mode": "mixed",
            "target_position": "edge",
        }
    return {
        "grid_h": 12 + bump,
        "grid_w": 11 + bump,
        "n_target_l": 4,
        "n_red_decoys": 2,
        "n_colored_decoys": 2,
        "hole_mode": "occupied",
        "target_position": "edge",
    }


def _bands(size: int) -> tuple[tuple[int, int], ...]:
    """Three disjoint bands with a one-cell moat, valid for size 10..16."""
    middle = max(4, (size - 3) // 2)
    middle = min(middle, size - 5)
    return ((0, 3), (middle, 3), (size - 2, 2))


def _slots(h: int, w: int) -> list[dict[str, int]]:
    return [
        {"index": index, "row": row, "col": col, "height": rh, "width": cw}
        for index, ((row, rh), (col, cw)) in enumerate(
            (pair for pair in ((rb, cb) for rb in _bands(h) for cb in _bands(w)))
        )
    ]


def _shape_extent(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return (
        max(row for row, _ in shape) + 1,
        max(col for _, col in shape) + 1,
    )


def _placement_candidates(
    spec: dict[str, Any], h: int, w: int, slots: list[dict[str, int]]
) -> list[tuple[int, tuple[tuple[int, int], ...]]]:
    shape = spec["shape"]
    shape_h, shape_w = _shape_extent(shape)
    candidates: list[tuple[int, tuple[tuple[int, int], ...]]] = []
    for slot in slots:
        if shape_h > slot["height"] or shape_w > slot["width"]:
            continue
        for drow in range(slot["height"] - shape_h + 1):
            for dcol in range(slot["width"] - shape_w + 1):
                row0 = slot["row"] + drow
                col0 = slot["col"] + dcol
                cells = tuple((row0 + row, col0 + col) for row, col in shape)
                if spec["kind"] == "target":
                    box_touches_edge = (
                        row0 == 0
                        or col0 == 0
                        or row0 + shape_h == h
                        or col0 + shape_w == w
                    )
                    if spec.get("require_edge") and not box_touches_edge:
                        continue
                    if spec.get("require_interior") and box_touches_edge:
                        continue
                candidates.append((slot["index"], cells))
    return candidates


def _place_specs(
    h: int, w: int, specs: list[dict[str, Any]], rng
) -> list[tuple[dict[str, Any], tuple[tuple[int, int], ...]]]:
    slots = _slots(h, w)
    candidate_lists = []
    for spec in specs:
        candidates = _placement_candidates(spec, h, w, slots)
        rng.shuffle(candidates)
        candidate_lists.append(candidates)
    order = sorted(
        range(len(specs)),
        key=lambda index: (len(candidate_lists[index]), -len(specs[index]["shape"]), index),
    )
    placed: list[tuple[dict[str, Any], tuple[tuple[int, int], ...]] | None] = [
        None
    ] * len(specs)
    used_slots: set[int] = set()

    def search(depth: int) -> bool:
        if depth == len(order):
            return True
        spec_index = order[depth]
        for slot_index, cells in candidate_lists[spec_index]:
            if slot_index in used_slots:
                continue
            used_slots.add(slot_index)
            placed[spec_index] = (specs[spec_index], cells)
            if search(depth + 1):
                return True
            placed[spec_index] = None
            used_slots.remove(slot_index)
        return False

    if not search(0):
        raise RuntimeError(
            f"constructive slot placement failed for {h}x{w} and {len(specs)} components"
        )
    return [item for item in placed if item is not None]


def _red_decoy_shapes(profile: int, count: int, rng):
    straight = _STRAIGHT_H if rng.randrange(2) == 0 else _STRAIGHT_V
    domino = _DOMINO_H if (profile + rng.randrange(2)) % 2 == 0 else _DOMINO_V
    return (straight, _SQUARE, domino)[:count]


def _colored_decoy_shapes(profile: int, count: int):
    first = _L_SHAPES[_PROFILE_TARGET_ORIENTATIONS[(profile + 1) % 4][0]]
    second = _DOMINO_V if profile % 2 == 0 else _STRAIGHT_H
    return (first, second)[:count]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            f"difficulty must be one of None/easy/medium/hard, got {difficulty!r}"
        )
    for name in ("grid_h", "grid_w", "n_target_l", "n_red_decoys", "n_colored_decoys"):
        value = overrides.get(name)
        if value is not None and (type(value) is not int):
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    for name in ("hole_mode", "target_position"):
        value = overrides.get(name)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"{name} must be a string, not {type(value).__name__}")

    profile = schedule_profile(seed, sample_index, difficulty)
    defaults = _profile_defaults(profile, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_int_axis(ctx, overrides, "grid_h", defaults["grid_h"], 10, 16)
    w = _draw_int_axis(ctx, overrides, "grid_w", defaults["grid_w"], 10, 16)
    n_targets = _draw_int_axis(
        ctx, overrides, "n_target_l", defaults["n_target_l"], 2, 4
    )
    n_red_decoys = _draw_int_axis(
        ctx, overrides, "n_red_decoys", defaults["n_red_decoys"], 1, 3
    )
    n_colored_decoys = _draw_int_axis(
        ctx, overrides, "n_colored_decoys", defaults["n_colored_decoys"], 1, 2
    )
    hole_mode = _draw_choice_axis(
        ctx,
        overrides,
        "hole_mode",
        defaults["hole_mode"],
        ("empty", "occupied", "mixed"),
    )
    target_position = _draw_choice_axis(
        ctx,
        overrides,
        "target_position",
        defaults["target_position"],
        ("interior", "edge"),
    )

    placement_rng = ctx.draw_rng("component_placement")
    shape_rng = ctx.draw_rng("decoy_shapes")
    palette_rng = ctx.draw_rng("nonred_palette")
    orientations = _PROFILE_TARGET_ORIENTATIONS[profile]
    specs: list[dict[str, Any]] = []
    for index in range(n_targets):
        specs.append(
            {
                "kind": "target",
                "orientation": orientations[index % len(orientations)],
                "shape": _L_SHAPES[orientations[index % len(orientations)]],
                "require_edge": target_position == "edge" and index == 0,
                "require_interior": target_position == "interior",
            }
        )
    for shape in _red_decoy_shapes(profile, n_red_decoys, shape_rng):
        specs.append({"kind": "red_decoy", "shape": shape})
    for shape in _colored_decoy_shapes(profile, n_colored_decoys):
        specs.append({"kind": "colored_decoy", "shape": shape})

    if len(specs) > 9:
        raise RuntimeError("declared axis maxima exceed the nine constructive slots")
    placed = _place_specs(h, w, specs, placement_rng)
    grid = full_grid(h, w, 0)

    if profile == 0 and not overrides:
        nonred_colors = (5,)
    else:
        nonred_colors = tuple(palette_rng.sample(_NONRED_COLORS, 3))
    colored_index = 0
    target_placements: list[tuple[dict[str, Any], tuple[tuple[int, int], ...]]] = []
    for spec, cells in placed:
        if spec["kind"] in ("target", "red_decoy"):
            color = 2
        else:
            color = nonred_colors[colored_index % len(nonred_colors)]
            colored_index += 1
        for row, col in cells:
            if grid[row][col] != 0:
                raise RuntimeError("constructive placement collision")
            grid[row][col] = color
        if spec["kind"] == "target":
            target_placements.append((spec, cells))

    occupied = []
    if hole_mode == "occupied":
        occupied = [True] * len(target_placements)
    elif hole_mode == "mixed":
        occupied = [index % 2 == 0 for index in range(len(target_placements))]
    else:
        occupied = [False] * len(target_placements)

    for index, ((spec, cells), fill_hole) in enumerate(zip(target_placements, occupied)):
        if not fill_hole:
            continue
        row0 = min(row for row, _ in cells)
        col0 = min(col for _, col in cells)
        corners = {
            (row0, col0),
            (row0, col0 + 1),
            (row0 + 1, col0),
            (row0 + 1, col0 + 1),
        }
        hole = next(iter(corners - set(cells)))
        if grid[hole[0]][hole[1]] != 0:
            raise RuntimeError("target hole unexpectedly occupied before hole-mode fill")
        grid[hole[0]][hole[1]] = nonred_colors[(colored_index + index) % len(nonred_colors)]

    return grid


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid rows must be non-empty and rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed 30x30"]
    bad = sorted(
        {
            value
            for row in grid
            for value in row
            if type(value) is not int or not (0 <= value <= 9)
        },
        key=repr,
    )
    if bad:
        return [f"grid contains non-ARC values: {bad[:4]}"]
    return []


def _component_kind(component: dict[str, Any]) -> str:
    size = len(component["cells"])
    height = component["height"]
    width = component["width"]
    if size == 1:
        return "singleton"
    if size == 2 and (height, width) in ((1, 2), (2, 1)):
        return "domino"
    if size == 3 and (height, width) in ((1, 3), (3, 1)):
        return "straight_triomino"
    if size == 3 and (height, width) == (2, 2):
        return "l_triomino"
    if size == 4 and (height, width) == (2, 2):
        return "square"
    return "other"


def _components(grid) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row in range(h):
        for col in range(w):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            cells_tuple = tuple(sorted(cells))
            row0 = min(r for r, _ in cells_tuple)
            row1 = max(r for r, _ in cells_tuple)
            col0 = min(c for _, c in cells_tuple)
            col1 = max(c for _, c in cells_tuple)
            component = {
                "color": color,
                "cells": cells_tuple,
                "bbox": (row0, col0, row1, col1),
                "height": row1 - row0 + 1,
                "width": col1 - col0 + 1,
                "shape": _normalize(cells_tuple),
            }
            component["kind"] = _component_kind(component)
            components.append(component)
    return components


def _analyze(grid) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    h, w = len(grid), len(grid[0])
    components = _components(grid)
    targets = [
        component
        for component in components
        if component["color"] == 2
        and len(component["cells"]) == 3
        and component["height"] == 2
        and component["width"] == 2
    ]
    target_holes = []
    for component in targets:
        row0, col0, row1, col1 = component["bbox"]
        corners = {
            (row0, col0),
            (row0, col1),
            (row1, col0),
            (row1, col1),
        }
        hole = next(iter(corners - set(component["cells"])))
        normalized_hole = (hole[0] - row0, hole[1] - col0)
        orientation = {
            (0, 0): "missing_nw",
            (0, 1): "missing_ne",
            (1, 0): "missing_sw",
            (1, 1): "missing_se",
        }[normalized_hole]
        component["orientation"] = orientation
        target_holes.append(
            {"cell": hole, "value": grid[hole[0]][hole[1]], "target": component}
        )
    red_decoys = [
        component
        for component in components
        if component["color"] == 2 and component not in targets
    ]
    nonred_components = [component for component in components if component["color"] != 2]
    hole_cells = {row["cell"] for row in target_holes if row["value"] != 0}
    hole_components = [
        component
        for component in nonred_components
        if any(cell in hole_cells for cell in component["cells"])
    ]
    colored_decoys = [
        component for component in nonred_components if component not in hole_components
    ]
    hole_values = [row["value"] for row in target_holes]
    if hole_values and all(value == 0 for value in hole_values):
        hole_mode = "empty"
    elif hole_values and all(value != 0 for value in hole_values):
        hole_mode = "occupied"
    else:
        hole_mode = "mixed"
    target_position = "edge" if any(
        row0 == 0 or col0 == 0 or row1 == h - 1 or col1 == w - 1
        for row0, col0, row1, col1 in (component["bbox"] for component in targets)
    ) else "interior"
    return {
        "errors": [],
        "grid_h": h,
        "grid_w": w,
        "colors": frozenset(value for row in grid for value in row),
        "components": components,
        "targets": targets,
        "target_holes": target_holes,
        "red_decoys": red_decoys,
        "nonred_components": nonred_components,
        "hole_components": hole_components,
        "colored_decoys": colored_decoys,
        "hole_mode": hole_mode,
        "target_position": target_position,
    }


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every advertised exact axis from the returned pixels."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n_target_l": len(analysis["targets"]),
        "n_red_decoys": len(analysis["red_decoys"]),
        "n_colored_decoys": len(analysis["colored_decoys"]),
        "hole_mode": analysis["hole_mode"],
        "target_position": analysis["target_position"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the canonical task domain, including same-color counterexamples."""
    del difficulty
    analysis = _analyze(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    reasons: list[str] = []
    if 0 not in analysis["colors"]:
        reasons.append("background color 0 is absent")
    if 3 in analysis["colors"]:
        reasons.append("input must not contain output color 3")
    if not analysis["targets"]:
        reasons.append("no exact red three-cell 2x2 L target is present")
    if not analysis["red_decoys"]:
        reasons.append("no red non-target component is present")
    if not analysis["colored_decoys"]:
        reasons.append("no non-red decoy component is present outside target holes")
    overrides = meta.get("overrides") if isinstance(meta, dict) else None
    if isinstance(overrides, dict):
        observed = observe_overrides(grid)
        for name, expected in overrides.items():
            if name in AXES and expected is not None and observed.get(name) != expected:
                reasons.append(
                    f"override {name}={expected!r} realized as {observed.get(name)!r}"
                )
    return reasons


def strict_canonical_like(grid) -> list[str]:
    """Recognize the measured canonical input envelope, not a replayed grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    reasons: list[str] = []
    if (analysis["grid_h"], analysis["grid_w"]) not in _CANONICAL_DIMS:
        reasons.append("canonical inputs are 10x10, 11x11, or 12x12")
    if analysis["colors"] not in _CANONICAL_PALETTES:
        reasons.append("palette does not match one of the five canonical input palettes")
    if not (2 <= len(analysis["targets"]) <= 3):
        reasons.append("canonical inputs contain two or three target L-triominoes")
    if not (2 <= len(analysis["red_decoys"]) <= 4):
        reasons.append("canonical inputs contain two to four red non-target components")
    if not (2 <= len(analysis["nonred_components"]) <= 4):
        reasons.append("canonical inputs contain two to four non-red components")
    return reasons


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    return {
        **observe_overrides(grid),
        "errors": [],
        "canonical_anchor": not strict_canonical_like(grid),
        "palette": sorted(analysis["colors"]),
        "target_orientations": sorted(
            component["orientation"] for component in analysis["targets"]
        ),
        "red_decoy_kinds": sorted(component["kind"] for component in analysis["red_decoys"]),
        "has_red_straight_triomino": any(
            component["kind"] == "straight_triomino" for component in analysis["red_decoys"]
        ),
        "has_red_square": any(
            component["kind"] == "square" for component in analysis["red_decoys"]
        ),
        "has_nonred_l": any(
            component["kind"] == "l_triomino" for component in analysis["colored_decoys"]
        ),
        "has_empty_hole": any(row["value"] == 0 for row in analysis["target_holes"]),
        "has_occupied_hole": any(row["value"] != 0 for row in analysis["target_holes"]),
    }


def _copy_grid(grid):
    return [list(row) for row in grid]


def _paint_box(out, bbox, color=3):
    row0, col0, row1, col1 = bbox
    for row in range(row0, row1 + 1):
        for col in range(col0, col1 + 1):
            out[row][col] = color


def rule_mirror(grid):
    """Pure Python oracle for tests/probes; Racket remains authoritative."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    out = _copy_grid(grid)
    for component in analysis["targets"]:
        _paint_box(out, component["bbox"], 3)
    return out


def _with_analysis(grid):
    analysis = _analyze(grid)
    return None if analysis["errors"] else analysis


def _complete_every_red_size3(grid):
    analysis = _with_analysis(grid)
    if analysis is None:
        return None
    out = _copy_grid(grid)
    for component in analysis["components"]:
        if component["color"] == 2 and len(component["cells"]) == 3:
            _paint_box(out, component["bbox"], 3)
    return out


def _complete_every_red_component(grid):
    analysis = _with_analysis(grid)
    if analysis is None:
        return None
    out = _copy_grid(grid)
    for component in analysis["components"]:
        if component["color"] == 2:
            _paint_box(out, component["bbox"], 3)
    return out


def _complete_every_l_any_color(grid):
    analysis = _with_analysis(grid)
    if analysis is None:
        return None
    out = _copy_grid(grid)
    for component in analysis["components"]:
        if component["kind"] == "l_triomino":
            _paint_box(out, component["bbox"], 3)
    return out


def _empty_holes_only(grid):
    analysis = _with_analysis(grid)
    if analysis is None:
        return None
    out = _copy_grid(grid)
    for row in analysis["target_holes"]:
        if row["value"] == 0:
            _paint_box(out, row["target"]["bbox"], 3)
    return out


def _recolor_red_cells_only(grid):
    analysis = _with_analysis(grid)
    if analysis is None:
        return None
    out = _copy_grid(grid)
    for component in analysis["targets"]:
        for row, col in component["cells"]:
            out[row][col] = 3
    return out


def _preserve_occupied_corner(grid):
    analysis = _with_analysis(grid)
    if analysis is None:
        return None
    out = rule_mirror(grid)
    for row in analysis["target_holes"]:
        if row["value"] != 0:
            r, c = row["cell"]
            out[r][c] = row["value"]
    return out


def _ignore_edge_targets(grid):
    analysis = _with_analysis(grid)
    if analysis is None:
        return None
    h, w = analysis["grid_h"], analysis["grid_w"]
    out = _copy_grid(grid)
    for component in analysis["targets"]:
        row0, col0, row1, col1 = component["bbox"]
        if row0 == 0 or col0 == 0 or row1 == h - 1 or col1 == w - 1:
            continue
        _paint_box(out, component["bbox"], 3)
    return out


def _ignore_orientation(orientation: str) -> Callable[[Any], Any]:
    def competitor(grid):
        analysis = _with_analysis(grid)
        if analysis is None:
            return None
        out = _copy_grid(grid)
        for component in analysis["targets"]:
            if component["orientation"] != orientation:
                _paint_box(out, component["bbox"], 3)
        return out

    return competitor


def _strict_envelope_only(grid):
    return rule_mirror(grid) if not strict_canonical_like(grid) else _copy_grid(grid)


def _at_most_three_targets(grid):
    analysis = _with_analysis(grid)
    if analysis is None:
        return None
    return rule_mirror(grid) if len(analysis["targets"]) <= 3 else _copy_grid(grid)


SEMANTIC_RIVALS = {
    "complete every red size-three component": _complete_every_red_size3,
    "complete every red component": _complete_every_red_component,
    "complete every L-triomino regardless of color": _complete_every_l_any_color,
    "complete only targets with empty missing corners": _empty_holes_only,
    "recolor only the three red cells": _recolor_red_cells_only,
    "preserve a non-red missing-corner cell": _preserve_occupied_corner,
    "ignore targets whose boxes touch an edge": _ignore_edge_targets,
    "ignore missing-NW targets": _ignore_orientation("missing_nw"),
    "ignore missing-NE targets": _ignore_orientation("missing_ne"),
    "ignore missing-SW targets": _ignore_orientation("missing_sw"),
    "ignore missing-SE targets": _ignore_orientation("missing_se"),
    "apply the rule only inside the canonical envelope": _strict_envelope_only,
    "apply the rule only when there are at most three targets": _at_most_three_targets,
}
CANONICAL_SHORTCUTS = {
    "apply the rule only inside the canonical envelope": _strict_envelope_only,
    "apply the rule only when there are at most three targets": _at_most_three_targets,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _witness(grid, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and bool(predicate(analysis))


SEMANTIC_WITNESSES = {
    "red_straight_triomino": lambda grid: _witness(
        grid,
        lambda a: any(c["kind"] == "straight_triomino" for c in a["red_decoys"]),
    ),
    "red_square": lambda grid: _witness(
        grid, lambda a: any(c["kind"] == "square" for c in a["red_decoys"])
    ),
    "nonred_l_triomino": lambda grid: _witness(
        grid, lambda a: any(c["kind"] == "l_triomino" for c in a["colored_decoys"])
    ),
    "occupied_target_hole": lambda grid: _witness(
        grid, lambda a: any(row["value"] != 0 for row in a["target_holes"])
    ),
    "empty_target_hole": lambda grid: _witness(
        grid, lambda a: any(row["value"] == 0 for row in a["target_holes"])
    ),
    "edge_target": lambda grid: _witness(grid, lambda a: a["target_position"] == "edge"),
    "four_targets": lambda grid: _witness(grid, lambda a: len(a["targets"]) == 4),
    "outside_canonical_envelope": lambda grid: _witness(
        grid, lambda a: bool(strict_canonical_like(grid))
    ),
    "target_missing_nw": lambda grid: _witness(
        grid, lambda a: any(c["orientation"] == "missing_nw" for c in a["targets"])
    ),
    "target_missing_ne": lambda grid: _witness(
        grid, lambda a: any(c["orientation"] == "missing_ne" for c in a["targets"])
    ),
    "target_missing_sw": lambda grid: _witness(
        grid, lambda a: any(c["orientation"] == "missing_sw" for c in a["targets"])
    ),
    "target_missing_se": lambda grid: _witness(
        grid, lambda a: any(c["orientation"] == "missing_se" for c in a["targets"])
    ),
}
WITNESS_RIVALS = {
    "red_straight_triomino": [
        "complete every red size-three component",
        "complete every red component",
    ],
    "red_square": ["complete every red component"],
    "nonred_l_triomino": ["complete every L-triomino regardless of color"],
    "occupied_target_hole": [
        "complete only targets with empty missing corners",
        "preserve a non-red missing-corner cell",
    ],
    "empty_target_hole": ["recolor only the three red cells"],
    "edge_target": ["ignore targets whose boxes touch an edge"],
    "four_targets": ["apply the rule only when there are at most three targets"],
    "outside_canonical_envelope": ["apply the rule only inside the canonical envelope"],
    "target_missing_nw": ["ignore missing-NW targets"],
    "target_missing_ne": ["ignore missing-NE targets"],
    "target_missing_sw": ["ignore missing-SW targets"],
    "target_missing_se": ["ignore missing-SE targets"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Check that demonstrations determine the exact query transformation."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    reasons: list[str] = []
    rows = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is unlawful: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the exact red-L rule")
            continue
        rows.append(semantic_observables(demo["input"]))
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is unlawful: {query_errors[0]}")
    if reasons:
        return reasons

    orientations = {
        orientation for row in rows for orientation in row["target_orientations"]
    }
    if orientations != set(_ORIENTATIONS):
        reasons.append(f"demonstrations omit target orientations {sorted(set(_ORIENTATIONS)-orientations)}")
    if not any(row["has_red_straight_triomino"] for row in rows):
        reasons.append("demonstrations omit a red straight-triomino counterexample")
    if not any(row["has_red_square"] for row in rows):
        reasons.append("demonstrations omit a red square counterexample")
    if not any(row["has_nonred_l"] for row in rows):
        reasons.append("demonstrations omit a non-red L-triomino counterexample")
    if not any(row["has_empty_hole"] for row in rows):
        reasons.append("demonstrations omit an empty target hole")
    if not any(row["has_occupied_hole"] for row in rows):
        reasons.append("demonstrations omit an occupied target hole")
    if not any(row["target_position"] == "edge" for row in rows):
        reasons.append("demonstrations omit an edge-touching target box")
    if not any(row["n_target_l"] == 4 for row in rows):
        reasons.append("demonstrations omit the four-target canonical-shortcut rebuttal")
    if sum(bool(row["canonical_anchor"]) for row in rows) != 1:
        reasons.append("demonstrations must contain exactly one canonical-envelope anchor")

    query_truth = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != query_truth:
                reasons.append(f"competitor survives demonstrations and changes query: {name}")
    return reasons
