"""Generator for ``fc41c9b3a565`` — keep 180-degree symmetric objects.

The authoritative rule treats every nonzero monochrome 4-connected component
as an object, crops it to its bounding box, and keeps it in place exactly when
the occupied-cell mask is unchanged by a 180-degree rotation.  Other objects
are erased.

The curriculum deliberately alternates exact canonical-morphology anchors with
broader counterexamples.  Every ordinary scene contains a connected object
that is 180-degree symmetric but neither left-right nor up-down symmetric, plus
an asymmetric object with the same cell count and bounding-box dimensions.
This defeats color, position, size, aspect-ratio, axis-reflection, and prototype
shortcuts without changing the Racket authority.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fc41c9b3a565"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "735d17bb2ca5"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.15

SUMMARY = (
    "On a 0-background grid, treat each nonzero monochrome 4-connected "
    "component as an object. Normalize each object to its own bounding box. "
    "Keep it at the same cells and in the same color exactly when its occupied "
    "mask is invariant under a 180-degree rotation; erase every other object. "
    "Generated lessons include point-symmetric-only objects and matched "
    "asymmetric decoys, so reflection-axis, size, aspect, position, and "
    "canonical-prototype shortcuts disagree with the intended labels."
)

INVARIANTS = [
    "background is color 0 and every object has its own nonzero color",
    "there are 2..4 monochrome 4-connected objects",
    "at least one object is 180-degree symmetric and at least one is not",
    "the output keeps every and only 180-degree symmetric object in place",
    "ordinary scenes match kept and erased objects by cell count and bbox",
    "every fifth sample is an exact linked canonical morphology profile",
]

_PROFILE_OPTIONS = (
    "pair_1sym_1asym",
    "trio_2sym_1asym",
    "trio_1sym_2asym",
    "quartet_1sym_3asym",
)
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty/schedule 6..10",
        "valid": "6..10",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty/schedule 6..10",
        "valid": "6..10",
    },
    "scene_profile": {
        "type": "str",
        "default": "difficulty/sample-index schedule",
        "valid": "|".join(_PROFILE_OPTIONS),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# Canonical shapes, normalized to their bounding boxes.
_SQUARE = ((0, 0), (0, 1), (1, 0), (1, 1))
_CANON_POINT_T4 = ((0, 0), (1, 0), (1, 1), (2, 1))
_L3_SE = ((0, 0), (1, 0), (1, 1))
_L3_NW = ((0, 0), (0, 1), (1, 1))
_L3_SW = ((0, 0), (0, 1), (1, 0))

# The three distinct linked canonical morphology profiles.  The held-out 7x7
# example shares the first profile modulo color and translation.
_CANONICAL_PROFILE_SPECS = (
    {
        "dims": (7, 7),
        "profile": "quartet_1sym_3asym",
        "shapes": (
            (_SQUARE, True),
            (_L3_SE, False),
            (_L3_NW, False),
            (_L3_NW, False),
        ),
    },
    {
        "dims": (6, 6),
        "profile": "trio_2sym_1asym",
        "shapes": (
            (_SQUARE, True),
            (_CANON_POINT_T4, True),
            (_L3_SE, False),
        ),
    },
    {
        "dims": (6, 6),
        "profile": "trio_1sym_2asym",
        "shapes": (
            (_SQUARE, True),
            (_L3_SE, False),
            (_L3_SW, False),
        ),
    },
)

# Generalized semantic roles.  Every shape below has five cells in a 3x3
# bounding box.  The first is symmetric only under a 180-degree turn.  The
# next two are symmetric under exactly one reflection axis but not under 180.
# Matching coarse geometry across opposite labels makes size/aspect shortcuts
# impossible inside a single ordinary example.
_POINT_ONLY_Z5 = ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2))
_LR_ONLY_T5 = ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1))
_UD_ONLY_T5 = ((0, 0), (1, 0), (1, 1), (1, 2), (2, 0))
_PLUS_5 = ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1))
_ASYM_HOOK5 = ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2))
_ASYM_SKEW5 = ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2))

_PROFILE_COUNTS = {
    "pair_1sym_1asym": (2, 1),
    "trio_2sym_1asym": (3, 2),
    "trio_1sym_2asym": (3, 1),
    "quartet_1sym_3asym": (4, 1),
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _norm(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _dims(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _rotate_180(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    normalized = _norm(cells)
    height, width = _dims(normalized)
    return _norm((height - 1 - r, width - 1 - c) for r, c in normalized)


def _flip_lr(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    normalized = _norm(cells)
    _, width = _dims(normalized)
    return _norm((r, width - 1 - c) for r, c in normalized)


def _flip_ud(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    normalized = _norm(cells)
    height, _ = _dims(normalized)
    return _norm((height - 1 - r, c) for r, c in normalized)


def _rot180_symmetric(cells: Iterable[tuple[int, int]]) -> bool:
    normalized = _norm(cells)
    return bool(normalized) and normalized == _rotate_180(normalized)


def _lr_symmetric(cells: Iterable[tuple[int, int]]) -> bool:
    normalized = _norm(cells)
    return bool(normalized) and normalized == _flip_lr(normalized)


def _ud_symmetric(cells: Iterable[tuple[int, int]]) -> bool:
    normalized = _norm(cells)
    return bool(normalized) and normalized == _flip_ud(normalized)


def _component_sets(cells: Iterable[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        queue = deque([start])
        component = {start}
        remaining.remove(start)
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARDINAL:
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def _analyze_grid(grid: Any) -> tuple[list[str], dict[str, Any] | None]:
    """Analyze structure once for checks, observers, rivals, and mirrors."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"], None
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and non-empty"], None
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid contains a non-ARC color"], None

    height = len(grid)
    errors: list[str] = []
    if not 6 <= height <= 10:
        errors.append(f"grid height {height} outside 6..10")
    if not 6 <= width <= 10:
        errors.append(f"grid width {width} outside 6..10")

    object_infos: list[dict[str, Any]] = []
    used_colors = sorted({value for row in grid for value in row if value != 0})
    for color in used_colors:
        color_cells = {
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        }
        components = _component_sets(color_cells)
        if len(components) != 1:
            errors.append(
                f"color {color} forms {len(components)} disconnected components; "
                "each object must have its own color"
            )
        for component in components:
            normalized = _norm(component)
            obj_h, obj_w = _dims(normalized)
            object_infos.append(
                {
                    "color": color,
                    "cells": tuple(sorted(component)),
                    "signature": normalized,
                    "cell_count": len(component),
                    "bbox_h": obj_h,
                    "bbox_w": obj_w,
                    "rot180_symmetric": _rot180_symmetric(normalized),
                    "lr_symmetric": _lr_symmetric(normalized),
                    "ud_symmetric": _ud_symmetric(normalized),
                    "touches_border": any(
                        r in (0, height - 1) or c in (0, width - 1)
                        for r, c in component
                    ),
                    "min_r": min(r for r, _ in component),
                    "min_c": min(c for _, c in component),
                }
            )

    if not 2 <= len(object_infos) <= 4:
        errors.append(f"expected 2..4 objects, found {len(object_infos)}")
    if len(object_infos) != len(used_colors):
        errors.append("objects must use distinct colors")
    for index, obj in enumerate(object_infos):
        if obj["cell_count"] < 2:
            errors.append(f"object {index} is a singleton")
        if obj["bbox_h"] > 3 or obj["bbox_w"] > 3:
            errors.append(
                f"object {index} bbox {obj['bbox_h']}x{obj['bbox_w']} exceeds 3x3"
            )

    sym_count = sum(obj["rot180_symmetric"] for obj in object_infos)
    asym_count = len(object_infos) - sym_count
    if sym_count < 1:
        errors.append("need at least one 180-symmetric object to keep")
    if asym_count < 1:
        errors.append("need at least one asymmetric object to erase")

    profile = None
    for name, counts in _PROFILE_COUNTS.items():
        if counts == (len(object_infos), sym_count):
            profile = name
            break
    if profile is None and 2 <= len(object_infos) <= 4:
        errors.append(
            f"unsupported semantic role count: {sym_count} symmetric / "
            f"{asym_count} asymmetric"
        )

    return errors, {
        "height": height,
        "width": width,
        "objects": object_infos,
        "sym_count": sym_count,
        "asym_count": asym_count,
        "scene_profile": profile,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors, _ = _analyze_grid(grid)
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared exact axis from a valid generated grid."""
    errors, analysis = _analyze_grid(grid)
    if errors or analysis is None or analysis["scene_profile"] is None:
        raise ValueError("cannot observe axes from invalid grid: " + "; ".join(errors))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "scene_profile": analysis["scene_profile"],
    }


def rule_mirror(grid):
    """Pure Python semantic mirror; the Racket program remains authoritative.

    The rule itself is meaningful on all-symmetric/all-asymmetric recombinations,
    even though those examples are rejected by ``self_check`` as uninformative.
    """
    errors, analysis = _analyze_grid(grid)
    distribution_only = (
        "need at least one 180-symmetric object",
        "need at least one asymmetric object",
        "unsupported semantic role count",
    )
    blocking = [error for error in errors if not error.startswith(distribution_only)]
    if blocking or analysis is None:
        raise ValueError("outside rule domain: " + "; ".join(blocking or errors))
    output = full_grid(analysis["height"], analysis["width"], 0)
    for obj in analysis["objects"]:
        if obj["rot180_symmetric"]:
            for r, c in obj["cells"]:
                output[r][c] = obj["color"]
    return output


def _strict_profile_key(analysis: dict[str, Any]) -> tuple[Any, ...]:
    signatures = tuple(
        sorted(
            (bool(obj["rot180_symmetric"]), obj["signature"])
            for obj in analysis["objects"]
        )
    )
    return analysis["height"], analysis["width"], signatures


def _canonical_profile_keys() -> set[tuple[Any, ...]]:
    keys = set()
    for spec in _CANONICAL_PROFILE_SPECS:
        fake = {
            "height": spec["dims"][0],
            "width": spec["dims"][1],
            "objects": [
                {"rot180_symmetric": expected, "signature": _norm(shape)}
                for shape, expected in spec["shapes"]
            ],
        }
        keys.add(_strict_profile_key(fake))
    return keys


_CANONICAL_PROFILE_KEYS = _canonical_profile_keys()


def strict_canonical_like(grid) -> list[str]:
    """Exact linked canonical manifold, modulo translation and color relabeling."""
    reasons, analysis = _analyze_grid(grid)
    if reasons or analysis is None:
        return reasons
    if _strict_profile_key(analysis) not in _CANONICAL_PROFILE_KEYS:
        reasons.append(
            "dimensions plus the linked multiset of role-tagged normalized object "
            "signatures do not match a canonical train/test profile"
        )
    return reasons


def _analysis_if_valid(grid) -> dict[str, Any] | None:
    errors, analysis = _analyze_grid(grid)
    return None if errors else analysis


def _paint_selected(grid, predicate: Callable[[dict[str, Any]], bool]):
    analysis = _analysis_if_valid(grid)
    if analysis is None:
        return None
    output = full_grid(analysis["height"], analysis["width"], 0)
    for obj in analysis["objects"]:
        if predicate(obj):
            for r, c in obj["cells"]:
                output[r][c] = obj["color"]
    return output


def _rival_lr_symmetry(grid):
    return _paint_selected(grid, lambda obj: obj["lr_symmetric"])


def _rival_ud_symmetry(grid):
    return _paint_selected(grid, lambda obj: obj["ud_symmetric"])


def _rival_double_axis_only(grid):
    return _paint_selected(
        grid, lambda obj: obj["lr_symmetric"] and obj["ud_symmetric"]
    )


_CANONICAL_KEPT_PROTOTYPES = {_norm(_SQUARE), _norm(_CANON_POINT_T4)}


def _rival_canonical_prototypes(grid):
    return _paint_selected(
        grid, lambda obj: obj["signature"] in _CANONICAL_KEPT_PROTOTYPES
    )


def _rival_largest_objects(grid):
    analysis = _analysis_if_valid(grid)
    if analysis is None:
        return None
    largest = max(obj["cell_count"] for obj in analysis["objects"])
    return _paint_selected(grid, lambda obj: obj["cell_count"] == largest)


def _rival_even_sized_objects(grid):
    return _paint_selected(grid, lambda obj: obj["cell_count"] % 2 == 0)


def _rival_non_triominoes(grid):
    return _paint_selected(grid, lambda obj: obj["cell_count"] != 3)


def _rival_left_half(grid):
    analysis = _analysis_if_valid(grid)
    if analysis is None:
        return None
    midpoint = (analysis["width"] - 1) / 2
    return _paint_selected(
        grid,
        lambda obj: sum(c for _, c in obj["cells"]) / obj["cell_count"] <= midpoint,
    )


def _rival_wide_or_square(grid):
    return _paint_selected(grid, lambda obj: obj["bbox_w"] >= obj["bbox_h"])


def _witness_point_only_kept(grid) -> bool:
    analysis = _analysis_if_valid(grid)
    return bool(
        analysis
        and any(
            obj["rot180_symmetric"]
            and not obj["lr_symmetric"]
            and not obj["ud_symmetric"]
            for obj in analysis["objects"]
        )
        and _rival_double_axis_only(grid) != rule_mirror(grid)
    )


def _witness_axis_reflections_rebutted(grid) -> bool:
    intended = rule_mirror(grid)
    return bool(
        _witness_point_only_kept(grid)
        and _rival_lr_symmetry(grid) != intended
        and _rival_ud_symmetry(grid) != intended
    )


def _witness_prototype_shortcut_rebutted(grid) -> bool:
    rival = _rival_canonical_prototypes(grid)
    return rival is not None and rival != rule_mirror(grid)


def _witness_largest_shortcut_rebutted(grid) -> bool:
    analysis = _analysis_if_valid(grid)
    if analysis is None:
        return False
    sym_sizes = {
        obj["cell_count"]
        for obj in analysis["objects"]
        if obj["rot180_symmetric"]
    }
    asym_sizes = {
        obj["cell_count"]
        for obj in analysis["objects"]
        if not obj["rot180_symmetric"]
    }
    return bool(
        sym_sizes & asym_sizes
        and _rival_largest_objects(grid) != rule_mirror(grid)
    )


def _witness_even_size_shortcut_rebutted(grid) -> bool:
    rival = _rival_even_sized_objects(grid)
    return rival is not None and rival != rule_mirror(grid)


def _witness_non_triomino_shortcut_rebutted(grid) -> bool:
    rival = _rival_non_triominoes(grid)
    return rival is not None and rival != rule_mirror(grid)


def _witness_position_shortcut_rebutted(grid) -> bool:
    rival = _rival_left_half(grid)
    return rival is not None and rival != rule_mirror(grid)


def _witness_aspect_ratio_shortcut_rebutted(grid) -> bool:
    analysis = _analysis_if_valid(grid)
    if analysis is None:
        return False
    symmetric_geometry = {
        (obj["cell_count"], obj["bbox_h"], obj["bbox_w"])
        for obj in analysis["objects"]
        if obj["rot180_symmetric"]
    }
    asymmetric_geometry = {
        (obj["cell_count"], obj["bbox_h"], obj["bbox_w"])
        for obj in analysis["objects"]
        if not obj["rot180_symmetric"]
    }
    rival = _rival_wide_or_square(grid)
    return bool(
        symmetric_geometry & asymmetric_geometry
        and rival is not None
        and rival != rule_mirror(grid)
    )


SEMANTIC_WITNESSES = {
    "point_only_object_kept": _witness_point_only_kept,
    "axis_reflection_shortcuts_rebutted": _witness_axis_reflections_rebutted,
    "canonical_prototype_memorization_rebutted": _witness_prototype_shortcut_rebutted,
    "largest_object_shortcut_rebutted": _witness_largest_shortcut_rebutted,
    "even_size_shortcut_rebutted": _witness_even_size_shortcut_rebutted,
    "non_triomino_shortcut_rebutted": _witness_non_triomino_shortcut_rebutted,
    "left_half_position_shortcut_rebutted": _witness_position_shortcut_rebutted,
    "aspect_ratio_shortcut_rebutted": _witness_aspect_ratio_shortcut_rebutted,
}

SEMANTIC_RIVALS = {
    "keep_lr_symmetric": _rival_lr_symmetry,
    "keep_ud_symmetric": _rival_ud_symmetry,
    "keep_only_doubly_symmetric": _rival_double_axis_only,
    "memorize_canonical_kept_prototypes": _rival_canonical_prototypes,
    "keep_largest_objects": _rival_largest_objects,
    "keep_even_sized_objects": _rival_even_sized_objects,
    "keep_non_triominoes": _rival_non_triominoes,
    "keep_left_half_objects": _rival_left_half,
    "keep_wide_or_square_objects": _rival_wide_or_square,
}

WITNESS_RIVALS = {
    "point_only_object_kept": ["keep_only_doubly_symmetric"],
    "axis_reflection_shortcuts_rebutted": [
        "keep_lr_symmetric",
        "keep_ud_symmetric",
    ],
    "canonical_prototype_memorization_rebutted": [
        "memorize_canonical_kept_prototypes"
    ],
    "largest_object_shortcut_rebutted": ["keep_largest_objects"],
    "even_size_shortcut_rebutted": ["keep_even_sized_objects"],
    "non_triomino_shortcut_rebutted": ["keep_non_triominoes"],
    "left_half_position_shortcut_rebutted": ["keep_left_half_objects"],
    "aspect_ratio_shortcut_rebutted": ["keep_wide_or_square_objects"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "memorize_canonical_kept_prototypes": _rival_canonical_prototypes,
    "keep_largest_objects": _rival_largest_objects,
    "keep_even_sized_objects": _rival_even_sized_objects,
    "keep_non_triominoes": _rival_non_triominoes,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report named plausible rivals that fit every demo but change the query."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except ValueError as exc:
            reasons.append(f"demo {index} is outside the rule domain: {exc}")
            continue
        if expected != demo["output"]:
            reasons.append(
                f"demo {index} output disagrees with the 180-symmetry rule"
            )
    try:
        query_answer = rule_mirror(query["input"])
    except ValueError as exc:
        reasons.append(f"query is outside the rule domain: {exc}")
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo["output"] for demo in demos)
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule '{name}' fits every demo but answers the query differently"
            )
    return reasons


def _draw_axis_int(
    ctx,
    label: str,
    lo: int,
    hi: int,
    default_lo: int,
    default_hi: int,
) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _draw_axis_choice(
    ctx,
    label: str,
    all_options: tuple[str, ...],
    defaults: tuple[str, ...],
) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, all_options)
    return ctx.draw_choice(label, defaults)


def _canonical_schedule(seed: int, sample_index: int) -> dict[str, Any] | None:
    if sample_index % 5 != 0:
        return None
    return _CANONICAL_PROFILE_SPECS[
        (sample_index // 5 + seed) % len(_CANONICAL_PROFILE_SPECS)
    ]


def _general_role_shapes(
    profile: str,
    rng,
    sample_index: int,
) -> list[tuple[tuple[tuple[int, int], ...], bool]]:
    axis_only = _LR_ONLY_T5 if (sample_index + rng.randrange(2)) % 2 == 0 else _UD_ONLY_T5
    if profile == "pair_1sym_1asym":
        roles = [(_POINT_ONLY_Z5, True), (axis_only, False)]
    elif profile == "trio_2sym_1asym":
        roles = [(_POINT_ONLY_Z5, True), (_PLUS_5, True), (axis_only, False)]
    elif profile == "trio_1sym_2asym":
        roles = [(_POINT_ONLY_Z5, True), (_LR_ONLY_T5, False), (_UD_ONLY_T5, False)]
    elif profile == "quartet_1sym_3asym":
        roles = [
            (_POINT_ONLY_Z5, True),
            (_LR_ONLY_T5, False),
            (_UD_ONLY_T5, False),
            (rng.choice((_ASYM_HOOK5, _ASYM_SKEW5)), False),
        ]
    else:
        raise ValueError(f"unknown scene profile {profile!r}")

    transformed: list[tuple[tuple[tuple[int, int], ...], bool]] = []
    for shape, expected in roles:
        candidate = _norm(shape)
        if rng.randrange(2):
            candidate = _flip_lr(candidate)
        if rng.randrange(2):
            candidate = _flip_ud(candidate)
        if _rot180_symmetric(candidate) != expected:
            raise RuntimeError("shape transform changed its 180-symmetry role")
        transformed.append((candidate, expected))
    return transformed


def _slots(height: int, width: int, n: int, variant: int) -> list[tuple[int, int, int, int]]:
    """Return non-overlapping half-open placement rectangles."""
    if n == 2:
        if variant % 2 == 0:
            cut = width // 2
            return [(0, 0, height, cut), (0, cut, height, width)]
        cut = height // 2
        return [(0, 0, cut, width), (cut, 0, height, width)]
    if n == 3:
        rcut, ccut = height // 2, width // 2
        if variant % 4 == 0:
            return [
                (0, 0, rcut, width),
                (rcut, 0, height, ccut),
                (rcut, ccut, height, width),
            ]
        if variant % 4 == 1:
            return [
                (0, 0, rcut, ccut),
                (0, ccut, rcut, width),
                (rcut, 0, height, width),
            ]
        if variant % 4 == 2:
            return [
                (0, 0, height, ccut),
                (0, ccut, rcut, width),
                (rcut, ccut, height, width),
            ]
        return [
            (0, 0, rcut, ccut),
            (rcut, 0, height, ccut),
            (0, ccut, height, width),
        ]
    if n == 4:
        rcut, ccut = height // 2, width // 2
        return [
            (0, 0, rcut, ccut),
            (0, ccut, rcut, width),
            (rcut, 0, height, ccut),
            (rcut, ccut, height, width),
        ]
    raise ValueError(f"unsupported object count {n}")


def _place_roles(
    height: int,
    width: int,
    roles: list[tuple[tuple[tuple[int, int], ...], bool]],
    colors: tuple[int, ...],
    rng,
    sample_index: int,
) -> list[list[int]]:
    grid = full_grid(height, width, 0)
    slots = _slots(height, width, len(roles), sample_index)

    shift = sample_index % len(roles)
    ordered = roles[shift:] + roles[:shift]
    if rng.randrange(2):
        ordered = list(reversed(ordered))

    for slot, (shape, _expected), color in zip(slots, ordered, colors):
        r0, c0, r1, c1 = slot
        shape_h, shape_w = _dims(shape)
        if shape_h > r1 - r0 or shape_w > c1 - c0:
            raise ValueError(
                f"shape {shape_h}x{shape_w} does not fit slot "
                f"{r1-r0}x{c1-c0} on {height}x{width}"
            )
        top = rng.randint(r0, r1 - shape_h)
        left = rng.randint(c0, c1 - shape_w)
        for dr, dc in shape:
            if grid[top + dr][left + dc] != 0:
                raise RuntimeError("placement slots overlapped")
            grid[top + dr][left + dc] = color
    return grid


def _generated_quality_errors(grid, *, canonical_anchor: bool) -> list[str]:
    errors, analysis = _analyze_grid(grid)
    if errors or analysis is None:
        return errors
    if canonical_anchor:
        if strict_canonical_like(grid):
            errors.append("scheduled canonical anchor missed the linked profile")
        return errors

    object_infos = analysis["objects"]
    if not any(
        obj["rot180_symmetric"]
        and not obj["lr_symmetric"]
        and not obj["ud_symmetric"]
        for obj in object_infos
    ):
        errors.append("general scene lacks a point-only symmetric kept witness")

    sym_geometry = {
        (obj["cell_count"], obj["bbox_h"], obj["bbox_w"])
        for obj in object_infos
        if obj["rot180_symmetric"]
    }
    asym_geometry = {
        (obj["cell_count"], obj["bbox_h"], obj["bbox_w"])
        for obj in object_infos
        if not obj["rot180_symmetric"]
    }
    if not sym_geometry & asym_geometry:
        errors.append(
            "general scene lacks a symmetric/asymmetric matched-size-and-bbox pair"
        )

    intended = rule_mirror(grid)
    required_rivals = {
        "left-right reflection": _rival_lr_symmetry,
        "up-down reflection": _rival_ud_symmetry,
        "double-axis": _rival_double_axis_only,
        "canonical prototype": _rival_canonical_prototypes,
        "largest object": _rival_largest_objects,
        "even size": _rival_even_sized_objects,
        "non-triomino": _rival_non_triominoes,
        "left-half position": _rival_left_half,
        "wide-or-square": _rival_wide_or_square,
    }
    for name, rival in required_rivals.items():
        if rival(grid) == intended:
            errors.append(f"{name} shortcut still matches the intended output")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {sorted(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    canonical_spec = _canonical_schedule(seed, sample_index)
    canonical_anchor = canonical_spec is not None and not overrides

    if canonical_anchor:
        scheduled_h, scheduled_w = canonical_spec["dims"]
        profile_defaults = (canonical_spec["profile"],)
        default_h_lo = default_h_hi = scheduled_h
        default_w_lo = default_w_hi = scheduled_w
    elif difficulty == "easy":
        default_h_lo, default_h_hi = 6, 7
        default_w_lo, default_w_hi = 6, 7
        profile_defaults = ("pair_1sym_1asym", "trio_1sym_2asym")
    elif difficulty == "hard":
        default_h_lo, default_h_hi = 9, 10
        default_w_lo, default_w_hi = 9, 10
        profile_defaults = ("quartet_1sym_3asym", "trio_2sym_1asym")
    else:
        default_h_lo, default_h_hi = 7, 9
        default_w_lo, default_w_hi = 7, 9
        profile_defaults = ("trio_2sym_1asym", "trio_1sym_2asym")

    height = _draw_axis_int(ctx, "grid_h", 6, 10, default_h_lo, default_h_hi)
    width = _draw_axis_int(ctx, "grid_w", 6, 10, default_w_lo, default_w_hi)
    profile = _draw_axis_choice(
        ctx, "scene_profile", _PROFILE_OPTIONS, profile_defaults
    )

    layout_rng = ctx.draw_rng("layout")
    count, _ = _PROFILE_COUNTS[profile]
    colors = ctx.draw_distinct_colors("object_colors", n=count, exclude={0})

    if canonical_anchor and profile == canonical_spec["profile"]:
        roles = [
            (tuple(shape), expected)
            for shape, expected in canonical_spec["shapes"]
        ]
    else:
        canonical_anchor = False
        roles = _general_role_shapes(profile, layout_rng, sample_index)

    # Try several deterministic slot permutations.  Mirroring preserves every
    # object's 180-symmetry label and all declared axes while changing a
    # left-half position heuristic.
    last_errors: list[str] = []
    for attempt in range(8):
        grid = _place_roles(
            height,
            width,
            roles,
            colors,
            layout_rng,
            sample_index + attempt,
        )
        if not canonical_anchor and _rival_left_half(grid) == rule_mirror(grid):
            grid = [list(reversed(row)) for row in grid]
        last_errors = _generated_quality_errors(
            grid, canonical_anchor=canonical_anchor
        )
        if not last_errors:
            return grid

    raise RuntimeError(
        "generator constructed no valid scene after deterministic attempts: "
        + "; ".join(last_errors)
    )
