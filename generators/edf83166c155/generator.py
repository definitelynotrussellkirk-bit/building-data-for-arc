"""Generator for edf83166c155 — crop the unique left/right-symmetric object.

The input contains three isolated monochromatic objects.  Exactly one object's
bbox-normalized binary mask is invariant under a left/right reflection.  The
canonical rule selects that object and returns its original-colour bbox crop.

The ordinary four-example schedule deliberately separates the true selector
from three plausible shortcuts: first object in reading order, largest object,
and first object symmetric under *any* common axis/half-turn. Target rank
varies across first, middle, and last under within-region jitter, preventing a fixed
reading-order-position rule.
"""
from __future__ import annotations

import hashlib

from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.palette import random_palette

GENERATOR_ID = "edf83166c155"
TASK_ID = "edf83166c155"
VERSION = "3.0.0"
RULE_HASH = "f276dac115e1"

SUMMARY = (
    "A 0-background grid contains exactly three 1-ring-isolated, differently "
    "coloured, 4-connected objects. Exactly one object has a non-solid crop "
    "whose binary mask is left/right mirror-symmetric. Crop that object to its "
    "bounding box without recolouring it. Four scheduled scene profiles keep "
    "canonical U/T examples common while refuting largest-object, reading-order, "
    "any-axis-symmetry, and fixed last-object shortcuts."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.40

INVARIANTS = [
    "background is 0 and all cells are integer colours 0..9",
    "exactly three monochromatic 4-connected objects in distinct colours",
    "objects are separated by a full one-cell Chebyshev ring",
    "exactly one object is LR-symmetric in its bbox-normalized binary mask",
    "the selected crop is non-solid and at least three columns wide",
]

# These are the only exact user-facing controls.  Difficulty changes the draw
# distribution, never the legal override domain.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware keyed draw 9..15 with canonical anchors",
        "valid": "9..15",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware keyed draw 10..17 with canonical anchors",
        "valid": "10..17",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

_PROFILE_CANONICAL_U = "canonical_u_reading_conflict"
_PROFILE_SIZE_CONFLICT = "size_conflict"
_PROFILE_CANONICAL_T = "canonical_t_reading_conflict"
_PROFILE_AXIS_CONFLICT = "axis_conflict"
SCHEDULE_PROFILES = (
    _PROFILE_CANONICAL_U,
    _PROFILE_SIZE_CONFLICT,
    _PROFILE_CANONICAL_T,
    _PROFILE_AXIS_CONFLICT,
)

# Canonical target masks.  The U is 2x3 with one hole; the T is 3x3 with four.
_U_TARGET = ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2))
_T_TARGET = ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1))

# Additional useful LR-symmetric, connected, non-solid target masks.  Every
# shape fits inside a 4x4 quadrant, including the minimum 9x10 canvas.
_GENERAL_SYM = (
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 1), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2)),
    ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)),
    ((0, 1), (1, 1), (2, 0), (2, 1), (2, 2)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2), (3, 1)),
)

# Canonical distractor masks, named by their coarse morphology.  The strict
# profile uses the linked multisets observed across all five canonical inputs.
_L4_TALL = ((0, 0), (1, 0), (2, 0), (2, 1))
_J4_WIDE = ((0, 0), (0, 1), (0, 2), (1, 0))
_S4_WIDE = ((0, 0), (0, 1), (1, 1), (1, 2))
_Z5_DIAG = ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2))
_STAIR5 = ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2))
_ASYM6 = ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (2, 2))
_L3 = ((0, 0), (1, 0), (1, 1))

# Half-turn symmetric but not LR-symmetric: a tempting "any symmetry" decoy.
_ROT180_ONLY = ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3))
# UD-symmetric but not LR-symmetric.  The middle row bridges the asymmetric
# top/bottom rows, keeping the whole ten-cell object 4-connected.
_UD_ONLY = (
    (0, 0), (0, 1), (0, 3),
    (1, 0), (1, 1), (1, 2), (1, 3),
    (2, 0), (2, 1), (2, 3),
)

_GENERAL_ASYM = (
    _L3,
    _L4_TALL,
    _J4_WIDE,
    _S4_WIDE,
    _Z5_DIAG,
    _STAIR5,
    _ASYM6,
    _ROT180_ONLY,
)

# (h, w, target, distractor_a, distractor_b).  Each row reproduces one exact
# canonical linked morphology profile; positions and colours remain nuisance.
_CANONICAL_U_PROFILES = (
    (10, 12, _U_TARGET, _L4_TALL, _J4_WIDE),
    (11, 13, _U_TARGET, _STAIR5, _L4_TALL),
    (10, 12, _U_TARGET, _ASYM6, _L4_TALL),
)
_CANONICAL_T_PROFILES = (
    (9, 11, _T_TARGET, _Z5_DIAG, _S4_WIDE),
    (10, 10, _T_TARGET, _J4_WIDE, _S4_WIDE),
)

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Four consecutive sample indices cover every decisive lesson profile."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise KeyError(f"unknown override axis/axes: {', '.join(unknown)}")


def _draw_or_pin_int(ctx, label: str, lo: int, hi: int, pinned: int | None) -> int:
    """Honor explicit full-domain overrides; otherwise record a chosen pin."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    if pinned is not None:
        return ctx.draw_int(label, pinned, pinned)
    return ctx.draw_int_diff(label, lo, hi)


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _shape_dims(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    norm = _normalize(cells)
    return max(row for row, _ in norm) + 1, max(col for _, col in norm) + 1


def _is_lr_symmetric(cells: Iterable[tuple[int, int]]) -> bool:
    norm = _normalize(cells)
    _, width = _shape_dims(norm)
    return norm == tuple(sorted((row, width - 1 - col) for row, col in norm))


def _is_ud_symmetric(cells: Iterable[tuple[int, int]]) -> bool:
    norm = _normalize(cells)
    height, _ = _shape_dims(norm)
    return norm == tuple(sorted((height - 1 - row, col) for row, col in norm))


def _is_rot180_symmetric(cells: Iterable[tuple[int, int]]) -> bool:
    norm = _normalize(cells)
    height, width = _shape_dims(norm)
    return norm == tuple(
        sorted((height - 1 - row, width - 1 - col) for row, col in norm)
    )


def _connected4(cells: Iterable[tuple[int, int]]) -> bool:
    remaining = set(cells)
    if not remaining:
        return False
    start = next(iter(remaining))
    seen = {start}
    stack = [start]
    while stack:
        row, col = stack.pop()
        for drow, dcol in _DIR4:
            neighbor = (row + drow, col + dcol)
            if neighbor in remaining and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return len(seen) == len(remaining)


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] == 0 or (start_row, start_col) in seen:
                continue
            colour = grid[start_row][start_col]
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells: list[tuple[int, int]] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for drow, dcol in _DIR4:
                    neighbor = (row + drow, col + dcol)
                    nrow, ncol = neighbor
                    if (
                        0 <= nrow < height
                        and 0 <= ncol < width
                        and neighbor not in seen
                        and grid[nrow][ncol] == colour
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            norm = _normalize(cells)
            bbox_h, bbox_w = _shape_dims(norm)
            components.append(
                {
                    "colour": colour,
                    "cells": tuple(sorted(cells)),
                    "norm": norm,
                    "top": min(row for row, _ in cells),
                    "left": min(col for _, col in cells),
                    "bbox_h": bbox_h,
                    "bbox_w": bbox_w,
                    "area": len(cells),
                    "holes": bbox_h * bbox_w - len(cells),
                    "lr": _is_lr_symmetric(norm),
                    "ud": _is_ud_symmetric(norm),
                    "rot180": _is_rot180_symmetric(norm),
                }
            )
    return sorted(components, key=lambda component: (component["top"], component["left"]))


def _analysis(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid must be a non-empty list of non-empty rows"]}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("all cells must be integer colours 0..9")
    if not any(value == 0 for row in grid for value in row):
        errors.append("background colour 0 is absent")
    if errors:
        return {"errors": errors}

    components = _components(grid)
    if len(components) != 3:
        errors.append(f"expected exactly three non-zero components, found {len(components)}")
    colours = [component["colour"] for component in components]
    if len(colours) != len(set(colours)):
        errors.append("component colours must be distinct")
    symmetric = [component for component in components if component["lr"]]
    if len(symmetric) != 1:
        errors.append(f"expected exactly one LR-symmetric component, found {len(symmetric)}")
    target = symmetric[0] if len(symmetric) == 1 else None
    if target is not None:
        if target["bbox_w"] < 3:
            errors.append("LR-symmetric target must be at least three columns wide")
        if target["holes"] == 0:
            errors.append("LR-symmetric target crop is solid and hides mask structure")

    cell_to_index: dict[tuple[int, int], int] = {}
    for index, component in enumerate(components):
        for cell in component["cells"]:
            cell_to_index[cell] = index
    for (row, col), index in cell_to_index.items():
        for drow in (-1, 0, 1):
            for dcol in (-1, 0, 1):
                if drow == 0 and dcol == 0:
                    continue
                other = cell_to_index.get((row + drow, col + dcol))
                if other is not None and other != index:
                    errors.append("components are not separated by a full one-cell ring")
                    return {
                        "errors": errors,
                        "components": components,
                        "target": target,
                    }
    return {
        "errors": errors,
        "height": len(grid),
        "width": width,
        "components": components,
        "target": target,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or rule-hiding scenes."""
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


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact semantic axis from the returned grid."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {}
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def _crop_component(grid: list[list[int]], component: dict[str, Any]) -> list[list[int]]:
    top, left = component["top"], component["left"]
    height, width = component["bbox_h"], component["bbox_w"]
    output = full_grid(height, width, 0)
    for row, col in component["cells"]:
        output[row - top][col - left] = component["colour"]
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for focused tests; Racket remains authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid grid: " + "; ".join(analysis["errors"]))
    return _crop_component(grid, analysis["target"])


def _morphology(component: dict[str, Any]) -> tuple[int, int, int, int]:
    return (
        component["area"],
        component["bbox_h"],
        component["bbox_w"],
        component["holes"],
    )


_CANONICAL_DIMS = {(10, 12), (9, 11), (11, 13), (10, 10)}
_CANONICAL_TARGET_MASKS = {_normalize(_U_TARGET), _normalize(_T_TARGET)}
_CANONICAL_DISTRACTOR_MULTISETS = {
    tuple(sorted(((4, 3, 2, 2), (4, 2, 3, 2)))),
    tuple(sorted(((5, 3, 3, 4), (4, 2, 3, 2)))),
    tuple(sorted(((5, 3, 3, 4), (4, 3, 2, 2)))),
    tuple(sorted(((4, 2, 3, 2), (4, 2, 3, 2)))),
    tuple(sorted(((6, 3, 3, 3), (4, 3, 2, 2)))),
}


def strict_canonical_like(grid) -> list[str]:
    """Match dimensions and linked object morphology of the five canonical inputs."""
    analysis = _analysis(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    if (analysis["height"], analysis["width"]) not in _CANONICAL_DIMS:
        reasons.append("full-grid dimensions are outside the canonical joint profile set")
    target = analysis["target"]
    if target["norm"] not in _CANONICAL_TARGET_MASKS:
        reasons.append("target mask is not one of the two canonical U/T morphologies")
    distractors = tuple(
        sorted(_morphology(component) for component in analysis["components"] if not component["lr"])
    )
    if distractors not in _CANONICAL_DISTRACTOR_MULTISETS:
        reasons.append("linked distractor morphology multiset is not canonical")
    return reasons


def _largest_object_rule(grid: list[list[int]]) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid grid")
    winner = max(
        analysis["components"],
        key=lambda component: (component["area"], -component["top"], -component["left"]),
    )
    return _crop_component(grid, winner)


def _first_object_rule(grid: list[list[int]]) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid grid")
    return _crop_component(grid, analysis["components"][0])


def _last_object_rule(grid: list[list[int]]) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid grid")
    return _crop_component(grid, analysis["components"][-1])


def _any_axis_symmetry_rule(grid: list[list[int]]) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid grid")
    winner = next(
        component
        for component in analysis["components"]
        if component["lr"] or component["ud"] or component["rot180"]
    )
    return _crop_component(grid, winner)


def _target_not_largest(grid) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and analysis["target"]["area"] < max(component["area"] for component in analysis["components"])
    )


def _target_not_first(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["components"][0] is not analysis["target"]


def _target_not_last(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["components"][-1] is not analysis["target"]


def _has_earlier_non_lr_axis_symmetric_distractor(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    target_index = analysis["components"].index(analysis["target"])
    return any(
        not component["lr"] and (component["ud"] or component["rot180"])
        for component in analysis["components"][:target_index]
    )


SEMANTIC_WITNESSES = {
    "target_not_largest": _target_not_largest,
    "target_not_first": _target_not_first,
    "target_not_last": _target_not_last,
    "earlier_non_lr_axis_symmetric_distractor": _has_earlier_non_lr_axis_symmetric_distractor,
}

SEMANTIC_RIVALS = {
    "largest_object": _largest_object_rule,
    "first_reading_order_object": _first_object_rule,
    "last_reading_order_object": _last_object_rule,
    "any_axis_symmetry": _any_axis_symmetry_rule,
}
WITNESS_RIVALS = {
    "target_not_largest": ["largest_object"],
    "target_not_first": ["first_reading_order_object"],
    "target_not_last": ["last_reading_order_object"],
    "earlier_non_lr_axis_symmetric_distractor": ["any_axis_symmetry"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"any_axis_symmetry": _any_axis_symmetry_rule}


def lesson_identifiable(demos, query) -> list[str]:
    """Require a complete four-profile lesson that defeats named rival selectors."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    if self_check(query["input"]):
        reasons.append("query input is outside the teaching grammar")

    target_masks: set[tuple[tuple[int, int], ...]] = set()
    target_colours: set[int] = set()
    witness_hits = {name: False for name in SEMANTIC_WITNESSES}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        analysis = _analysis(demo["input"])
        if analysis["errors"]:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output is not the LR-symmetric object crop")
        target_masks.add(analysis["target"]["norm"])
        target_colours.add(analysis["target"]["colour"])
        for name, predicate in SEMANTIC_WITNESSES.items():
            witness_hits[name] |= predicate(demo["input"])

    for name, hit in witness_hits.items():
        if not hit:
            reasons.append(f"demonstrations do not refute the {name.replace('_', ' ')} shortcut")
    if not {_normalize(_U_TARGET), _normalize(_T_TARGET)} <= target_masks:
        reasons.append("demonstrations do not include both canonical U and T target masks")
    if len(target_colours) < 2:
        reasons.append("target colour does not vary across demonstrations")
    return reasons


def _quadrants(height: int, width: int) -> dict[str, tuple[int, int, int, int]]:
    top_height = (height - 1) // 2
    left_width = (width - 1) // 2
    return {
        "tl": (0, top_height, 0, left_width),
        "tr": (0, top_height, left_width + 1, width),
        "bl": (top_height + 1, height, 0, left_width),
        "br": (top_height + 1, height, left_width + 1, width),
    }


def _place_in_region(
    grid: list[list[int]],
    region: tuple[int, int, int, int],
    shape: tuple[tuple[int, int], ...],
    colour: int,
    rng,
) -> None:
    row0, row1, col0, col1 = region
    shape_h, shape_w = _shape_dims(shape)
    if shape_h > row1 - row0 or shape_w > col1 - col0:
        raise ValueError(
            f"shape {shape_h}x{shape_w} does not fit region {row1-row0}x{col1-col0}"
        )
    top = rng.randint(row0, row1 - shape_h)
    left = rng.randint(col0, col1 - shape_w)
    paint_at(grid, top, left, shape, colour)


def _profile_spec(profile: str, rng):
    """Return optional pinned dimensions and three (role, region, shape) rows."""
    if profile == _PROFILE_CANONICAL_U:
        height, width, target, asym_a, asym_b = rng.choice(_CANONICAL_U_PROFILES)
        return height, width, (
            ("asym", "tl", asym_a),
            ("target", "tr", target),
            ("asym", "br", asym_b),
        )
    if profile == _PROFILE_CANONICAL_T:
        height, width, target, asym_a, asym_b = rng.choice(_CANONICAL_T_PROFILES)
        return height, width, (
            ("asym", "tl", asym_a),
            ("target", "bl", target),
            ("asym", "br", asym_b),
        )
    if profile == _PROFILE_SIZE_CONFLICT:
        target = rng.choice(tuple(shape for shape in _GENERAL_SYM if len(shape) <= 7))
        # Put the true selector in the previously absent top-left quadrant.
        # The large top-right distractor preserves the size conflict while
        # breaking the retained region/width scaffold shortcut.
        return None, None, (
            ("target", "tl", target),
            ("asym", "tr", _UD_ONLY),
            ("asym", "br", rng.choice(_GENERAL_ASYM)),
        )
    if profile == _PROFILE_AXIS_CONFLICT:
        target = rng.choice(_GENERAL_SYM)
        return None, None, (
            ("asym", "tl", rng.choice((_UD_ONLY, _ROT180_ONLY))),
            ("asym", "bl", rng.choice((_L3, _L4_TALL, _S4_WIDE))),
            ("target", "br", target),
        )
    raise ValueError(f"unknown schedule profile {profile!r}")



def _target_colour(seed: Any, sample_index: int) -> int:
    """Seed-keyed permutation keeps each lesson colour-varied across episodes."""
    colours = list(range(1, 10))
    colours.sort(
        key=lambda colour: hashlib.sha256(
            f"{TASK_ID}:{VERSION}:target-colour:{seed!r}:{colour}".encode()
        ).digest()
    )
    return colours[int(sample_index) % len(colours)]

def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the canonical Racket rule owns output."""
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    profile_rng = ctx.draw_rng("profile")
    pinned_h, pinned_w, placements = _profile_spec(profile, profile_rng)
    height = _draw_or_pin_int(ctx, "grid_h", 9, 15, pinned_h)
    width = _draw_or_pin_int(ctx, "grid_w", 10, 17, pinned_w)

    grid = full_grid(height, width, 0)
    regions = _quadrants(height, width)
    # Consecutive lesson examples receive distinct target colours, so colour can
    # never stand in for the geometric selector.  Distractor colours remain
    # keyed nuisance variation and are distinct from the target and each other.
    target_colour = _target_colour(seed, int(sample_index))
    distractor_colours = list(
        random_palette(ctx.draw_rng("palette"), 2, exclude={target_colour})
    )
    layout_rng = ctx.draw_rng("layout")
    layout_rng.shuffle(distractor_colours)
    for role, region_name, shape in placements:
        colour = target_colour if role == "target" else distractor_colours.pop()
        _place_in_region(grid, regions[region_name], shape, colour, layout_rng)

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise ValueError("constructed invalid LR-symmetry scene: " + "; ".join(errors))
    return grid
