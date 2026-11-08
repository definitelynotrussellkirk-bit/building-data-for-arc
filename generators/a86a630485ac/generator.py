"""Generator for arc_puzzle_bank_next21:M12 — keep LR-symmetric objects.

The authoritative rule preserves every nonzero monochrome connected object
whose cropped bitmap is invariant under left-right reflection through its own
bounding box, and erases every other object.

The curriculum alternates between exact canonical-morphology anchors and
broader shortcut-rebutting scenes.  Every ordinary non-anchor scene includes:

* an LR-symmetric but not up-down-symmetric object that must be kept;
* an up-down-symmetric but not LR-symmetric object that must be erased; and
* a symmetric/asymmetric pair with the same cell count and bounding box.

Those witnesses distinguish the intended rule from the strongest canonical
shortcuts: keeping only doubly-symmetric objects, memorizing the three kept
canonical prototypes, using horizontal rather than vertical symmetry, or
selecting objects by size, aspect ratio, or coarse geometry.  Half of the
ordinary schedule uses connected 3x4 objects, extending the earlier 3x3-only
bank.  ``sample_index % 5 == 0`` supplies an exact linked canonical profile, so
generalized examples augment rather than displace the empirical task manifold.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a86a630485ac"
TASK_ID = GENERATOR_ID
VERSION = "3.2.0"
RULE_HASH = "3cb323ae99fd"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.15

SUMMARY = (
    "On a 0-background grid, treat each nonzero monochrome 4-connected "
    "component as an object. Normalize each object to its bounding box and "
    "keep it in place exactly when its occupied cells are invariant under "
    "left-right reflection; erase every other object. Generated lessons pair "
    "vertical-only and horizontal-only reflection cases and match object sizes "
    "and bounding boxes across roles so color, position, prototype, size, "
    "aspect-ratio, and horizontal-symmetry shortcuts fail."
)

INVARIANTS = [
    "background is color 0 and every object has its own nonzero color",
    "there are 2..4 monochrome 4-connected objects",
    "at least one object is LR-symmetric and at least one is not",
    "the output keeps every and only LR-symmetric object at its original cells",
    "ordinary non-anchor scenes include vertical-only and horizontal-only objects with matched size and bounding box",
    "ordinary scenes alternate between 3x3 and connected 3x4 role pairs",
    "every fifth sample is an exact linked canonical morphology profile",
]

# Only exact, finite, grid-observable controls are declared.  Palette, shape,
# placement, and curriculum branch remain deterministic nuisance variation,
# not caller-facing axes that can silently become inert.
_PROFILE_OPTIONS = (
    "pair_1sym_1asym",
    "trio_2sym_1asym",
    "trio_1sym_2asym",
    "quartet_2sym_2asym",
)
AXES = {
    "grid_h": {"type": "int", "default": "difficulty/schedule 6..10", "valid": "6..10"},
    "grid_w": {"type": "int", "default": "difficulty/schedule 8..12", "valid": "8..12"},
    "scene_profile": {
        "type": "str",
        "default": "difficulty/sample-index schedule",
        "valid": "|".join(_PROFILE_OPTIONS),
    },
}

# Canonical normalized shapes.  Orientation matters: a 90-degree rotation can
# turn a horizontal-only object into a vertical-only one, changing the label.
_PLUS = ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1))
_VERTICAL_DOMINO = ((0, 0), (1, 0))
_SQUARE = ((0, 0), (0, 1), (1, 0), (1, 1))
_ASYM_J4 = ((0, 0), (0, 1), (1, 0), (2, 0))
_HORIZONTAL_ONLY_T4 = ((0, 0), (1, 0), (1, 1), (2, 0))
_ASYM_P5 = ((0, 0), (0, 1), (1, 0), (1, 1), (2, 1))
_ASYM_STAIR4 = ((0, 0), (0, 1), (1, 1), (1, 2))

_CANONICAL_PROFILE_SPECS = (
    {
        "dims": (7, 9),
        "profile": "trio_2sym_1asym",
        "shapes": ((_PLUS, True), (_VERTICAL_DOMINO, True), (_ASYM_J4, False)),
    },
    {
        "dims": (6, 8),
        "profile": "pair_1sym_1asym",
        "shapes": ((_SQUARE, True), (_HORIZONTAL_ONLY_T4, False)),
    },
    {
        "dims": (8, 10),
        "profile": "trio_1sym_2asym",
        "shapes": ((_PLUS, True), (_ASYM_P5, False), (_ASYM_STAIR4, False)),
    },
)

# Generalized role banks.  Each orientation pair contains one LR-only kept
# object and one UD-only erased object with exactly the same cell count and
# bounding-box dimensions.  This makes size, width, height, aspect ratio, and
# occupied-area shortcuts disagree with the labels inside every ordinary
# scene.  Only LR/UD flips are applied; these preserve the truth value of LR
# symmetry, unlike quarter turns.
_LR_ONLY_T5 = ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1))
_UD_ONLY_T5 = ((0, 0), (1, 0), (1, 1), (1, 2), (2, 0))
_LR_ONLY_WIDE8 = (
    (0, 0), (0, 1), (0, 2), (0, 3),
    (1, 1), (1, 2),
    (2, 1), (2, 2),
)
_UD_ONLY_WIDE8 = (
    (0, 0), (0, 1),
    (1, 0), (1, 1), (1, 2), (1, 3),
    (2, 0), (2, 1),
)
_ORIENTATION_ROLE_PAIRS = (
    (_LR_ONLY_T5, _UD_ONLY_T5),
    (_LR_ONLY_WIDE8, _UD_ONLY_WIDE8),
)
_DOUBLE_SYM_5 = (_PLUS,)
_ASYM_GENERAL_4 = (
    _ASYM_J4,
    _ASYM_STAIR4,
    ((0, 0), (1, 0), (2, 0), (2, 1)),
)
_ASYM_GENERAL_5 = (
    _ASYM_P5,
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),
)

_PROFILE_COUNTS = {
    "pair_1sym_1asym": (2, 1),
    "trio_2sym_1asym": (3, 2),
    "trio_1sym_2asym": (3, 1),
    "quartet_2sym_2asym": (4, 2),
}


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


def _flip_lr(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    normalized = _norm(cells)
    _, width = _dims(normalized)
    return _norm((r, width - 1 - c) for r, c in normalized)


def _flip_ud(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    normalized = _norm(cells)
    height, _ = _dims(normalized)
    return _norm((height - 1 - r, c) for r, c in normalized)


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
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def _analyze_grid(grid: Any) -> tuple[list[str], dict[str, Any] | None]:
    """Structural analysis shared by checking, observers, mirrors, and hooks."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"], None
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and non-empty"], None
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["grid contains a non-ARC color"], None

    height = len(grid)
    errors: list[str] = []
    if not 6 <= height <= 10:
        errors.append(f"grid height {height} outside 6..10")
    if not 8 <= width <= 12:
        errors.append(f"grid width {width} outside 8..12")

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
        if obj["bbox_h"] > 3 or obj["bbox_w"] > 4:
            errors.append(
                f"object {index} bbox {obj['bbox_h']}x{obj['bbox_w']} exceeds 3x4"
            )

    sym_count = sum(obj["lr_symmetric"] for obj in object_infos)
    asym_count = len(object_infos) - sym_count
    if sym_count < 1:
        errors.append("need at least one LR-symmetric object to keep")
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
    """Recover every declared exact axis from the returned grid."""
    errors, analysis = _analyze_grid(grid)
    if errors or analysis is None or analysis["scene_profile"] is None:
        raise ValueError("cannot observe axes from invalid grid: " + "; ".join(errors))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "scene_profile": analysis["scene_profile"],
    }


def rule_mirror(grid):
    """Pure Python mirror for semantic tests only; Racket remains authority.

    The oracle's mathematical domain is broader than the teaching
    distribution: all-symmetric and all-asymmetric recombinations are
    executable even though ``self_check`` rejects them as uninformative.
    """
    errors, analysis = _analyze_grid(grid)
    distribution_only = (
        "need at least one LR-symmetric object",
        "need at least one asymmetric object",
        "unsupported semantic role count",
    )
    blocking = [error for error in errors if not error.startswith(distribution_only)]
    if blocking or analysis is None:
        raise ValueError("outside rule domain: " + "; ".join(blocking or errors))
    output = full_grid(analysis["height"], analysis["width"], 0)
    for obj in analysis["objects"]:
        if obj["lr_symmetric"]:
            for r, c in obj["cells"]:
                output[r][c] = obj["color"]
    return output


def _strict_profile_key(analysis: dict[str, Any]) -> tuple[Any, ...]:
    signatures = tuple(
        sorted(
            (bool(obj["lr_symmetric"]), obj["signature"])
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
                {"lr_symmetric": expected, "signature": _norm(shape)}
                for shape, expected in spec["shapes"]
            ],
        }
        keys.add(_strict_profile_key(fake))
    return keys


_CANONICAL_PROFILE_KEYS = _canonical_profile_keys()


def strict_canonical_like(grid) -> list[str]:
    """Exact linked empirical manifold, modulo translation and color relabeling."""
    reasons, analysis = _analyze_grid(grid)
    if reasons or analysis is None:
        return reasons
    key = _strict_profile_key(analysis)
    if key not in _CANONICAL_PROFILE_KEYS:
        reasons.append(
            "dimensions plus the linked multiset of role-tagged normalized object "
            "signatures do not match any canonical train/test profile"
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


def _rival_horizontal_symmetry(grid):
    return _paint_selected(grid, lambda obj: obj["ud_symmetric"])


def _rival_double_axis_only(grid):
    return _paint_selected(
        grid, lambda obj: obj["lr_symmetric"] and obj["ud_symmetric"]
    )


_CANONICAL_KEPT_PROTOTYPES = {_norm(_PLUS), _norm(_VERTICAL_DOMINO), _norm(_SQUARE)}


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


def _witness_canonical_anchor(grid) -> bool:
    return strict_canonical_like(grid) == []


def _witness_lr_only_kept(grid) -> bool:
    analysis = _analysis_if_valid(grid)
    return bool(
        analysis
        and any(obj["lr_symmetric"] and not obj["ud_symmetric"] for obj in analysis["objects"])
        and _rival_double_axis_only(grid) != rule_mirror(grid)
    )


def _witness_horizontal_only_erased(grid) -> bool:
    analysis = _analysis_if_valid(grid)
    return bool(
        analysis
        and any(obj["ud_symmetric"] and not obj["lr_symmetric"] for obj in analysis["objects"])
        and _rival_horizontal_symmetry(grid) != rule_mirror(grid)
    )


def _witness_prototype_shortcut_rebutted(grid) -> bool:
    rival = _rival_canonical_prototypes(grid)
    return rival is not None and rival != rule_mirror(grid)


def _witness_size_shortcut_rebutted(grid) -> bool:
    analysis = _analysis_if_valid(grid)
    if analysis is None:
        return False
    sym_sizes = {obj["cell_count"] for obj in analysis["objects"] if obj["lr_symmetric"]}
    asym_sizes = {obj["cell_count"] for obj in analysis["objects"] if not obj["lr_symmetric"]}
    return bool(
        sym_sizes & asym_sizes
        and _rival_largest_objects(grid) != rule_mirror(grid)
    )


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
        if obj["lr_symmetric"]
    }
    asymmetric_geometry = {
        (obj["cell_count"], obj["bbox_h"], obj["bbox_w"])
        for obj in analysis["objects"]
        if not obj["lr_symmetric"]
    }
    rival = _rival_wide_or_square(grid)
    return bool(
        symmetric_geometry & asymmetric_geometry
        and rival is not None
        and rival != rule_mirror(grid)
    )


SEMANTIC_WITNESSES = {
    "lr_only_object_kept": _witness_lr_only_kept,
    "horizontal_only_object_erased": _witness_horizontal_only_erased,
    "canonical_prototype_memorization_rebutted": _witness_prototype_shortcut_rebutted,
    "largest_object_shortcut_rebutted": _witness_size_shortcut_rebutted,
    "left_half_position_shortcut_rebutted": _witness_position_shortcut_rebutted,
    "aspect_ratio_shortcut_rebutted": _witness_aspect_ratio_shortcut_rebutted,
}

SEMANTIC_RIVALS = {
    "keep_horizontal_symmetric": _rival_horizontal_symmetry,
    "keep_only_doubly_symmetric": _rival_double_axis_only,
    "memorize_canonical_kept_prototypes": _rival_canonical_prototypes,
    "keep_largest_objects": _rival_largest_objects,
    "keep_left_half_objects": _rival_left_half,
    "keep_wide_or_square_objects": _rival_wide_or_square,
}

WITNESS_RIVALS = {
    "lr_only_object_kept": ["keep_only_doubly_symmetric"],
    "horizontal_only_object_erased": ["keep_horizontal_symmetric"],
    "canonical_prototype_memorization_rebutted": ["memorize_canonical_kept_prototypes"],
    "largest_object_shortcut_rebutted": ["keep_largest_objects"],
    "left_half_position_shortcut_rebutted": ["keep_left_half_objects"],
    "aspect_ratio_shortcut_rebutted": ["keep_wide_or_square_objects"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "keep_only_doubly_symmetric": _rival_double_axis_only,
    "memorize_canonical_kept_prototypes": _rival_canonical_prototypes,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons for which a named plausible rival survives all demos."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except ValueError as exc:
            reasons.append(f"demo {index} is outside the rule domain: {exc}")
            continue
        if expected != demo["output"]:
            reasons.append(f"demo {index} output disagrees with the LR-symmetry rule")
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


def _draw_axis_int(ctx, label: str, lo: int, hi: int, default_lo: int, default_hi: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _draw_axis_choice(ctx, label: str, all_options: tuple[str, ...], defaults: tuple[str, ...]) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, all_options)
    return ctx.draw_choice(label, defaults)


def _canonical_schedule(seed: int, sample_index: int) -> dict[str, Any] | None:
    if sample_index % 5 != 0:
        return None
    return _CANONICAL_PROFILE_SPECS[(sample_index // 5 + seed) % len(_CANONICAL_PROFILE_SPECS)]


def _general_role_shapes(
    profile: str,
    rng,
    sample_index: int,
) -> list[tuple[tuple[tuple[int, int], ...], bool]]:
    lr_only, horizontal_only = _ORIENTATION_ROLE_PAIRS[
        sample_index % len(_ORIENTATION_ROLE_PAIRS)
    ]
    lr_only = tuple(lr_only)
    horizontal_only = tuple(horizontal_only)
    double5 = tuple(rng.choice(_DOUBLE_SYM_5))
    asym4 = tuple(rng.choice(_ASYM_GENERAL_4))
    asym5 = tuple(rng.choice(_ASYM_GENERAL_5))

    if profile == "pair_1sym_1asym":
        roles = [(lr_only, True), (horizontal_only, False)]
    elif profile == "trio_2sym_1asym":
        roles = [(lr_only, True), (double5, True), (horizontal_only, False)]
    elif profile == "trio_1sym_2asym":
        roles = [(lr_only, True), (horizontal_only, False), (asym4, False)]
    elif profile == "quartet_2sym_2asym":
        roles = [(lr_only, True), (double5, True), (horizontal_only, False), (asym5, False)]
    else:
        raise ValueError(f"unknown scene profile {profile!r}")

    transformed = []
    for shape, expected in roles:
        candidate = _norm(shape)
        if rng.randrange(2):
            candidate = _flip_lr(candidate)
        if rng.randrange(2):
            candidate = _flip_ud(candidate)
        if _lr_symmetric(candidate) != expected:
            raise RuntimeError("shape transform changed its LR-symmetry role")
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
        if variant % 4 == 0:  # one full-width top slot, two bottom slots
            rcut, ccut = height // 2, width // 2
            return [(0, 0, rcut, width), (rcut, 0, height, ccut), (rcut, ccut, height, width)]
        if variant % 4 == 1:  # mirrored vertically
            rcut, ccut = height // 2, width // 2
            return [(0, 0, rcut, ccut), (0, ccut, rcut, width), (rcut, 0, height, width)]
        if variant % 4 == 2:  # one full-height left slot, two right slots
            rcut, ccut = height // 2, width // 2
            return [(0, 0, height, ccut), (0, ccut, rcut, width), (rcut, ccut, height, width)]
        rcut, ccut = height // 2, width // 2
        return [(0, 0, rcut, ccut), (rcut, 0, height, ccut), (0, ccut, height, width)]
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

    # Rotate the semantic roles through slot positions deterministically, then
    # use the keyed RNG for a secondary permutation.  This prevents a fixed
    # location from being a stable label while preserving replay.
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
            errors.append("scheduled canonical anchor missed the exact linked profile")
        return errors

    object_infos = analysis["objects"]
    if not any(obj["lr_symmetric"] and not obj["ud_symmetric"] for obj in object_infos):
        errors.append("general scene lacks an LR-only kept witness")
    if not any(obj["ud_symmetric"] and not obj["lr_symmetric"] for obj in object_infos):
        errors.append("general scene lacks a horizontal-only erased witness")
    sym_sizes = {obj["cell_count"] for obj in object_infos if obj["lr_symmetric"]}
    asym_sizes = {obj["cell_count"] for obj in object_infos if not obj["lr_symmetric"]}
    if not sym_sizes & asym_sizes:
        errors.append("general scene lacks a symmetric/asymmetric matched-size pair")
    sym_geometry = {
        (obj["cell_count"], obj["bbox_h"], obj["bbox_w"])
        for obj in object_infos
        if obj["lr_symmetric"]
    }
    asym_geometry = {
        (obj["cell_count"], obj["bbox_h"], obj["bbox_w"])
        for obj in object_infos
        if not obj["lr_symmetric"]
    }
    if not sym_geometry & asym_geometry:
        errors.append(
            "general scene lacks a symmetric/asymmetric matched-size-and-bbox pair"
        )
    if _rival_canonical_prototypes(grid) == rule_mirror(grid):
        errors.append("canonical-prototype shortcut still matches the intended output")
    if _rival_largest_objects(grid) == rule_mirror(grid):
        errors.append("largest-object shortcut still matches the intended output")
    if _rival_left_half(grid) == rule_mirror(grid):
        errors.append("left-half position shortcut still matches the intended output")
    if _rival_wide_or_square(grid) == rule_mirror(grid):
        errors.append("aspect-ratio shortcut still matches the intended output")
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
    elif difficulty == "easy":
        scheduled_h, scheduled_w = 6, 8
        profile_defaults = ("pair_1sym_1asym",)
    elif difficulty == "hard":
        scheduled_h, scheduled_w = 9, 11
        profile_defaults = ("quartet_2sym_2asym", "trio_1sym_2asym")
    else:
        scheduled_h, scheduled_w = 7, 9
        profile_defaults = ("trio_2sym_1asym", "trio_1sym_2asym")

    if canonical_anchor:
        default_h_lo = default_h_hi = scheduled_h
        default_w_lo = default_w_hi = scheduled_w
    elif difficulty == "easy":
        default_h_lo, default_h_hi = 6, 7
        default_w_lo, default_w_hi = 8, 9
    elif difficulty == "hard":
        default_h_lo, default_h_hi = 8, 10
        default_w_lo, default_w_hi = 10, 12
    else:
        default_h_lo, default_h_hi = 7, 8
        default_w_lo, default_w_hi = 9, 10

    height = _draw_axis_int(ctx, "grid_h", 6, 10, default_h_lo, default_h_hi)
    width = _draw_axis_int(ctx, "grid_w", 8, 12, default_w_lo, default_w_hi)
    profile = _draw_axis_choice(ctx, "scene_profile", _PROFILE_OPTIONS, profile_defaults)

    layout_rng = ctx.draw_rng("layout")
    count, _ = _PROFILE_COUNTS[profile]
    colors = ctx.draw_distinct_colors("object_colors", n=count, exclude={0})

    if canonical_anchor and profile == canonical_spec["profile"]:
        roles = [(tuple(shape), expected) for shape, expected in canonical_spec["shapes"]]
    else:
        canonical_anchor = False
        roles = _general_role_shapes(profile, layout_rng, sample_index)

    grid = _place_roles(height, width, roles, colors, layout_rng, sample_index)
    # A left-half selector is a plausible shortcut on sparse object scenes.
    # If a generalized placement accidentally makes that rival exactly match
    # the intended labels, mirror the whole scene horizontally.  This preserves
    # every object's LR-symmetry role and all declared axes while forcing a
    # decisive position-rule disagreement.  Exact canonical anchors remain
    # orientation-faithful and are never mirrored by this safeguard.
    if not canonical_anchor and _rival_left_half(grid) == rule_mirror(grid):
        grid = [list(reversed(row)) for row in grid]
    quality_errors = _generated_quality_errors(grid, canonical_anchor=canonical_anchor)
    if quality_errors:
        raise RuntimeError("generator constructed invalid scene: " + "; ".join(quality_errors))
    return grid
