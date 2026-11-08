"""Generator for ARC task 8604dc774d22: recolor green L-trominoes.

The authoritative rule examines each 4-connected colour-3 component.  A
component is recoloured to 4 exactly when it has three cells and fills three
corners of a 2x2 bounding box.  Horizontal and vertical green bars remain 3,
and geometrically identical components in other colours remain unchanged.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "8604dc774d22"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "9ef73bd801f3"

SUMMARY = (
    "On a 0-background grid, recolour every 4-connected colour-3 component "
    "that is an L-tromino (three cells in a 2x2 bounding box) to colour 4. "
    "Keep horizontal and vertical colour-3 bars unchanged. Keep every "
    "non-3 component unchanged, including an occasional non-3 L-tromino that "
    "rules out a colour-blind shape shortcut."
)

INVARIANTS = [
    "background is colour 0",
    "there are 1-4 isolated colour-3 L-tromino targets",
    "there is exactly one isolated horizontal colour-3 bar and one vertical colour-3 bar",
    "there is exactly one isolated non-3 decoration component",
    "all non-zero components are separated by at least one cardinal background cell",
    "the only colour-3 component shapes are L-tromino, horizontal I3, and vertical I3",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

# Every declared control is exact and recoverable from the returned grid.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical-weighted 8..13",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical-weighted 10..16",
        "valid": "10..16",
    },
    "n_l_trominoes": {
        "type": "int",
        "default": "scheduled 2|2|2|4",
        "valid": "1..4",
    },
    "decor_shape": {
        "type": "str",
        "default": "scheduled",
        "valid": "square|l_tromino|tee|singleton",
    },
    "decor_color": {
        "type": "color",
        "default": "scheduled canonical colours",
        "valid": "1..9 (≠3)",
    },
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_L_SHAPES = (
    ((0, 0), (0, 1), (1, 0)),   # missing bottom-right
    ((0, 0), (0, 1), (1, 1)),   # missing bottom-left
    ((0, 0), (1, 0), (1, 1)),   # missing top-right
    ((0, 1), (1, 0), (1, 1)),   # missing top-left
)
_HORIZONTAL_BAR = ((0, 0), (0, 1), (0, 2))
_VERTICAL_BAR = ((0, 0), (1, 0), (2, 0))
_DECOR_SHAPES = {
    "square": ((0, 0), (0, 1), (1, 0), (1, 1)),
    "l_tromino": _L_SHAPES[0],
    # This is the exact 2x3 four-cell decoration seen in canonical train 1.
    "tee": ((0, 0), (0, 1), (0, 2), (1, 1)),
    "singleton": ((0, 0),),
}
_DECOR_COLORS = (1, 2, 4, 5, 6, 7, 8, 9)

# Four consecutive sample indices cover the two canonical-negative bar
# orientations, a colour-blind-shape counterexample, target-count variation,
# all four target orientations, and all canonical decoration morphologies.
_PROFILES = (
    {"name": "canonical_square", "h": 8, "w": 10, "n_l": 2,
     "decor_shape": "square", "decor_color": 7},
    {"name": "color_blind_counterexample", "h": 9, "w": 12, "n_l": 2,
     "decor_shape": "l_tromino", "decor_color": 5},
    {"name": "canonical_tee", "h": 8, "w": 11, "n_l": 2,
     "decor_shape": "tee", "decor_color": 6},
    {"name": "extra_targets_singleton", "h": 10, "w": 13, "n_l": 4,
     "decor_shape": "singleton", "decor_color": 9},
)
SCHEDULE_PROFILES = tuple(profile["name"] for profile in _PROFILES)


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic curriculum profile used by the semantic gate."""
    del seed
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return _PROFILES[int(sample_index) % len(_PROFILES)]["name"]


def _profile_for(sample_index: int) -> dict[str, Any]:
    return _PROFILES[int(sample_index) % len(_PROFILES)]


def _draw_profile_int(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    """Use a scheduled default while accepting every declared exact boundary."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _draw_profile_choice(ctx, overrides, label: str, default: Any, options: tuple[Any, ...]):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


_L_NORMALIZED = frozenset(_normalize(shape) for shape in _L_SHAPES)
_DECOR_NORMALIZED = {name: _normalize(shape) for name, shape in _DECOR_SHAPES.items()}


def _rectangular_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _components(grid: Any) -> list[dict[str, Any]]:
    """Return monochrome 4-connected non-zero components in reading order."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in _CARDINAL:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            components.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "shape": _normalize(cells),
                    "height": max(rows) - min(rows) + 1,
                    "width": max(cols) - min(cols) + 1,
                    "anchor": (min(rows), min(cols)),
                }
            )
    return components


def _is_l(component: dict[str, Any]) -> bool:
    return component["shape"] in _L_NORMALIZED


def _is_horizontal_bar(component: dict[str, Any]) -> bool:
    return component["shape"] == _normalize(_HORIZONTAL_BAR)


def _is_vertical_bar(component: dict[str, Any]) -> bool:
    return component["shape"] == _normalize(_VERTICAL_BAR)


def _decor_shape_name(component: dict[str, Any]) -> str | None:
    matches = [name for name, shape in _DECOR_NORMALIZED.items() if component["shape"] == shape]
    return matches[0] if len(matches) == 1 else None


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_grid_errors(grid)
    if errors:
        return {"errors": errors, "components": []}

    height, width = len(grid), len(grid[0])
    if not 8 <= height <= 14:
        errors.append(f"height must be in 8..14, found {height}")
    if not 10 <= width <= 16:
        errors.append(f"width must be in 10..16, found {width}")

    components = _components(grid)
    green = [component for component in components if component["color"] == 3]
    targets = [component for component in green if _is_l(component)]
    horizontal = [component for component in green if _is_horizontal_bar(component)]
    vertical = [component for component in green if _is_vertical_bar(component)]
    illegal_green = [
        component
        for component in green
        if not (_is_l(component) or _is_horizontal_bar(component) or _is_vertical_bar(component))
    ]
    decorations = [component for component in components if component["color"] != 3]

    if not 1 <= len(targets) <= 4:
        errors.append(f"expected 1-4 green L-trominoes, found {len(targets)}")
    if len(horizontal) != 1:
        errors.append(f"expected exactly one horizontal green bar, found {len(horizontal)}")
    if len(vertical) != 1:
        errors.append(f"expected exactly one vertical green bar, found {len(vertical)}")
    if illegal_green:
        errors.append(
            "illegal green component shapes: "
            + ", ".join(str(component["shape"]) for component in illegal_green[:3])
        )
    if len(decorations) != 1:
        errors.append(f"expected exactly one non-green decoration component, found {len(decorations)}")

    decor_shape = None
    decor_color = None
    if len(decorations) == 1:
        decoration = decorations[0]
        decor_color = decoration["color"]
        decor_shape = _decor_shape_name(decoration)
        if decor_color not in _DECOR_COLORS:
            errors.append(f"decoration color must be in {_DECOR_COLORS}, found {decor_color}")
        if decor_shape is None:
            errors.append(f"unknown decoration shape: {decoration['shape']}")

    # Different-colour components can remain distinct while touching.  Reject
    # that ambiguity explicitly so every component boundary is visually clean.
    owner: dict[tuple[int, int], int] = {}
    for index, component in enumerate(components):
        for cell in component["cells"]:
            owner[cell] = index
    touching: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for (r, c), index in owner.items():
        for dr, dc in _CARDINAL:
            neighbor = (r + dr, c + dc)
            other = owner.get(neighbor)
            if other is not None and other != index:
                touching.append(((r, c), neighbor))
    if touching:
        errors.append(f"distinct components touch cardinally: {touching[:3]}")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "components": components,
        "green": green,
        "targets": targets,
        "horizontal": horizontal,
        "vertical": vertical,
        "decorations": decorations,
        "decor_shape": decor_shape,
        "decor_color": decor_color,
        "target_orientations": {component["shape"] for component in targets},
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared exact axis from a lawful returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_l_trominoes": len(analysis["targets"]),
        "decor_shape": analysis["decor_shape"],
        "decor_color": analysis["decor_color"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, shortcut-hiding, or off-contract scenes."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The lawful generated grammar is this task's strict teaching manifold."""
    return self_check(grid)


def rule_mirror(grid):
    """Independent Python mirror for tests; the canonical Racket is authority."""
    errors = _rectangular_grid_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    output = [list(row) for row in grid]
    for component in _components(grid):
        if component["color"] == 3 and _is_l(component):
            for row, col in component["cells"]:
                output[row][col] = 4
    return output


def _rival_identity(grid):
    return [list(row) for row in grid]


def _rival_recolor_all_green_threes(grid):
    return [[4 if value == 3 else value for value in row] for row in grid]


def _rival_color_blind_l(grid):
    output = [list(row) for row in grid]
    for component in _components(grid):
        if _is_l(component):
            for row, col in component["cells"]:
                output[row][col] = 4
    return output


def _rival_first_two_green_ls(grid):
    output = [list(row) for row in grid]
    targets = [
        component
        for component in _components(grid)
        if component["color"] == 3 and _is_l(component)
    ]
    for component in targets[:2]:
        for row, col in component["cells"]:
            output[row][col] = 4
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _rival_identity,
    "recolor_all_green_threes": _rival_recolor_all_green_threes,
    "color_blind_l": _rival_color_blind_l,
    "first_two_green_ls": _rival_first_two_green_ls,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS

# Both shortcuts fit every canonical pair: canonical contains no differently
# coloured L-tromino, and always contains exactly two green L targets.  The
# generated schedule deliberately supplies counterexamples to each.
CANONICAL_SHORTCUTS = {
    "color_blind_l": _rival_color_blind_l,
    "first_two_green_ls": _rival_first_two_green_ls,
}


def _lawful(grid) -> dict[str, Any] | None:
    analysis = _analysis(grid)
    return analysis if not analysis["errors"] else None


def _witness_target(grid) -> bool:
    analysis = _lawful(grid)
    return bool(analysis and analysis["targets"])


def _witness_horizontal_bar(grid) -> bool:
    analysis = _lawful(grid)
    return bool(analysis and analysis["horizontal"])


def _witness_vertical_bar(grid) -> bool:
    analysis = _lawful(grid)
    return bool(analysis and analysis["vertical"])


def _witness_other_color_l(grid) -> bool:
    analysis = _lawful(grid)
    return bool(
        analysis
        and analysis["decorations"]
        and _is_l(analysis["decorations"][0])
    )


def _witness_extra_targets(grid) -> bool:
    analysis = _lawful(grid)
    return bool(analysis and len(analysis["targets"]) > 2)


SEMANTIC_WITNESSES = {
    "target_l_recolors": _witness_target,
    "horizontal_bar_stays_green": _witness_horizontal_bar,
    "vertical_bar_stays_green": _witness_vertical_bar,
    "other_color_l_stays_unchanged": _witness_other_color_l,
    "more_than_two_targets": _witness_extra_targets,
}
WITNESS_RIVALS = {
    "target_l_recolors": ["identity"],
    "horizontal_bar_stays_green": ["recolor_all_green_threes"],
    "vertical_bar_stays_green": ["recolor_all_green_threes"],
    "other_color_l_stays_unchanged": ["color_blind_l"],
    "more_than_two_targets": ["first_two_green_ls"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require each materialized lesson to refute the plausible canonical rivals."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    if self_check(query["input"]):
        reasons.append("query input is outside the teaching grammar")

    saw_other_color_l = False
    saw_extra_targets = False
    target_orientations: set[tuple[tuple[int, int], ...]] = set()
    decor_colors: set[int] = set()
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        analysis = _analysis(demo["input"])
        if analysis["errors"]:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output does not match recolor-green-L-only")
        saw_other_color_l |= _witness_other_color_l(demo["input"])
        saw_extra_targets |= len(analysis["targets"]) > 2
        target_orientations.update(analysis["target_orientations"])
        decor_colors.add(analysis["decor_color"])

    if not saw_other_color_l:
        reasons.append("demonstrations do not refute the color-blind L-shape rival")
    if not saw_extra_targets:
        reasons.append("demonstrations do not refute the recolor-only-first-two-targets rival")
    if len(target_orientations) != 4:
        reasons.append("demonstrations do not cover all four L-tromino orientations")
    if len(decor_colors) < 2:
        reasons.append("demonstrations do not show that decoration colour is irrelevant")
    return reasons


def _translated(shape: tuple[tuple[int, int], ...], row: int, col: int) -> tuple[tuple[int, int], ...]:
    return tuple((row + dr, col + dc) for dr, dc in shape)


def _placement_candidates(shape, height: int, width: int) -> list[tuple[tuple[int, int], ...]]:
    shape_h = max(r for r, _ in shape) + 1
    shape_w = max(c for _, c in shape) + 1
    return [
        _translated(shape, row, col)
        for row in range(height - shape_h + 1)
        for col in range(width - shape_w + 1)
    ]


def _blocked_by(cells: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    blocked = set(cells)
    for row, col in tuple(cells):
        for dr, dc in _CARDINAL:
            blocked.add((row + dr, col + dc))
    return blocked


def _place_objects(height: int, width: int, scene_objects: list[dict[str, Any]], rng) -> list[tuple[dict[str, Any], tuple[tuple[int, int], ...]]]:
    """Backtrack over isolated placements; all declared boundary tuples fit."""
    candidate_table: dict[int, list[tuple[tuple[int, int], ...]]] = {}
    for index, obj in enumerate(scene_objects):
        candidates = _placement_candidates(obj["shape"], height, width)
        rng.shuffle(candidates)
        # Profile 3 deliberately puts the first target on a border, while the
        # other profiles leave all positions free.  This prevents a fixed-
        # interior-position shortcut without creating another exact axis.
        if obj.get("prefer_border"):
            border = [
                cells
                for cells in candidates
                if any(r in (0, height - 1) or c in (0, width - 1) for r, c in cells)
            ]
            interior = [cells for cells in candidates if cells not in border]
            candidates = border + interior
        candidate_table[index] = candidates

    def search(remaining: tuple[int, ...], blocked: set[tuple[int, int]]):
        if not remaining:
            return []
        valid_by_index: dict[int, list[tuple[tuple[int, int], ...]]] = {}
        for index in remaining:
            valid = [cells for cells in candidate_table[index] if not (set(cells) & blocked)]
            if not valid:
                return None
            valid_by_index[index] = valid
        chosen = min(remaining, key=lambda index: len(valid_by_index[index]))
        rest = tuple(index for index in remaining if index != chosen)
        for cells in valid_by_index[chosen]:
            result = search(rest, blocked | _blocked_by(cells))
            if result is not None:
                return [(scene_objects[chosen], cells)] + result
        return None

    result = search(tuple(range(len(scene_objects))), set())
    if result is None:
        raise ValueError(
            f"no isolated layout for {height}x{width} with "
            f"{len(scene_objects)} components"
        )
    return result


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the canonical Racket owns output."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    profile = _profile_for(sample_index)
    band_delta = {None: 0, "easy": 0, "medium": 1, "hard": 3}[difficulty]
    default_h = min(14, int(profile["h"]) + band_delta)
    default_w = min(16, int(profile["w"]) + band_delta)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_profile_int(ctx, overrides, "grid_h", default_h, 8, 14)
    width = _draw_profile_int(ctx, overrides, "grid_w", default_w, 10, 16)
    n_l = _draw_profile_int(ctx, overrides, "n_l_trominoes", int(profile["n_l"]), 1, 4)
    decor_shape_name = _draw_profile_choice(
        ctx, overrides, "decor_shape", profile["decor_shape"], tuple(_DECOR_SHAPES)
    )
    decor_color = _draw_profile_choice(
        ctx, overrides, "decor_color", int(profile["decor_color"]), _DECOR_COLORS
    )

    layout_rng = ctx.draw_rng(f"layout:{difficulty or 'medium'}")
    base_orientation = int(sample_index) % 4
    scene_objects: list[dict[str, Any]] = []
    for index in range(n_l):
        scene_objects.append(
            {
                "label": f"target_{index}",
                "color": 3,
                "shape": _L_SHAPES[(base_orientation + index) % 4],
                "prefer_border": int(sample_index) % 4 == 3 and index == 0,
            }
        )
    scene_objects.extend(
        [
            {"label": "horizontal_bar", "color": 3, "shape": _HORIZONTAL_BAR},
            {"label": "vertical_bar", "color": 3, "shape": _VERTICAL_BAR},
            {
                "label": "decoration",
                "color": decor_color,
                "shape": _DECOR_SHAPES[decor_shape_name],
            },
        ]
    )
    placements = _place_objects(height, width, scene_objects, layout_rng)
    grid = full_grid(height, width, 0)
    for obj, cells in placements:
        for row, col in cells:
            grid[row][col] = obj["color"]

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": {name: value for name, value in overrides.items()}},
    )
    if errors:
        raise ValueError("constructed invalid instance: " + "; ".join(errors))
    return [row[:] for row in grid]
