"""Generator for cadfb7a1ae72 — pairwise object feature-match matrix.

Each non-zero color forms one isolated 4-connected object.  Objects are ordered
by top-left position.  The output is the square pairwise relation matrix:

* 1 on the diagonal (the same object index),
* 8 when two different objects have the same exact row/column symmetry class,
* 4 when their symmetry classes differ but their enclosed-hole counts match,
* 0 otherwise.

The ordinary curriculum is a four-residue schedule.  Every four consecutive
examples contains canonical-scale anchors plus counterexamples to three rivals:
axis-count instead of exact symmetry orientation, binary hollow/solid instead
of exact hole count, and hole-equality taking priority over symmetry-equality.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cadfb7a1ae72"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"  # replace unrelated motif-selection generator with canonical pairwise matrix curriculum
RULE_HASH = "b8842d5039be"  # sha256[:12] of whitespace-normalized canonical rule
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.40

SUMMARY = (
    "Extract the isolated same-color objects in top-left order and compare every "
    "ordered pair. Emit 1 on the diagonal, 8 for the same exact row/column "
    "symmetry class, 4 for equal enclosed-hole count when symmetry differs, and "
    "0 otherwise. Four scheduled profiles explicitly distinguish exact symmetry "
    "orientation, exact hole count, and the precedence of symmetry over holes."
)

INVARIANTS = [
    "background is color 0 and all cells use ARC colors 0..9",
    "3-5 isolated 4-connected objects use distinct non-zero colors",
    "objects are read in top-left order",
    "hole count is the number of enclosed zero regions in an object's bounding box",
    "symmetry class records row reflection and column reflection separately",
    "the output relation precedence is diagonal 1, same symmetry 8, same holes 4, else 0",
]

PROFILES = ("canonical3", "canonical4", "hole_priority", "binary_holes")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-residue schedule with canonical 10/11-row anchors",
        "valid": "10..20",
    },
    "grid_w": {
        "type": "int",
        "default": "four-residue schedule with canonical 16/17-column anchors",
        "valid": "16..24",
    },
    "profile": {
        "type": "enum",
        "default": "sample_index mod 4 curriculum schedule",
        "valid": PROFILES,
    },
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_PROFILES = {(10, 16, 4), (11, 17, 5)}

# (hole count, exact symmetry class), where symmetry class is bit-coded as
# row-symmetric=1 and column-symmetric=2.  Each profile contains 0/4/8 branches.
_PROFILE_SIGNATURES: dict[str, tuple[tuple[int, int], ...]] = {
    "canonical3": ((1, 3), (0, 3), (0, 1)),
    "canonical4": ((1, 3), (0, 3), (0, 1), (0, 2)),
    # Duplicate (1,3) signatures force 8 even though hole count also matches;
    # a holes-first rival emits 4 for that pair.
    "hole_priority": ((1, 3), (1, 3), (1, 1), (0, 0), (0, 2)),
    # (2,1) versus (1,2) distinguishes exact hole counts from hollow/solid.
    "binary_holes": ((1, 0), (2, 1), (0, 0), (1, 2), (0, 3)),
}

# Small, hand-audited connected masks. Axis-aligned flips add harmless surface
# variety while preserving both hole count and row/column symmetry orientation.
_SHAPE_BANK: dict[tuple[int, int], tuple[tuple[tuple[int, int], ...], ...]] = {
    (0, 0): (
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
    ),
    (0, 1): (
        ((0, 0), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1)),
    ),
    (0, 2): (
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2)),
    ),
    (0, 3): (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (0, 1), (0, 2)),
    ),
    (1, 0): (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 1), (2, 2)),
    ),
    (1, 1): (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (1, 3),
         (2, 0), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2),
         (2, 0), (2, 1), (2, 2), (2, 3)),
    ),
    (1, 2): (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0),
         (2, 1), (2, 2), (3, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0),
         (2, 1), (2, 2), (3, 0), (3, 2)),
    ),
    (1, 3): (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2),
         (2, 0), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 3),
         (2, 0), (2, 1), (2, 2), (2, 3)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0),
         (2, 2), (3, 0), (3, 1), (3, 2)),
    ),
    (2, 1): (
        ((0, 0), (0, 1), (1, 0), (1, 2), (2, 0), (2, 1),
         (2, 2), (3, 0), (3, 2), (4, 0), (4, 1)),
        ((0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1),
         (2, 2), (3, 0), (3, 2), (4, 1), (4, 2)),
    ),
}


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _shape_dims(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _axis_flips(cells: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    shape = _normalize(cells)
    height, width = _shape_dims(shape)
    variants = {
        shape,
        _normalize((height - 1 - r, c) for r, c in shape),
        _normalize((r, width - 1 - c) for r, c in shape),
        _normalize((height - 1 - r, width - 1 - c) for r, c in shape),
    }
    return tuple(sorted(variants))


def _hole_count(cells: Iterable[tuple[int, int]]) -> int:
    shape = _normalize(cells)
    if not shape:
        return 0
    height, width = _shape_dims(shape)
    occupied = set(shape)
    remaining = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if (r, c) not in occupied
    }
    holes = 0
    while remaining:
        start = remaining.pop()
        queue = deque([start])
        touches_border = False
        while queue:
            r, c = queue.popleft()
            touches_border = touches_border or r in (0, height - 1) or c in (0, width - 1)
            for dr, dc in _CARDINAL:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    queue.append(nxt)
        if not touches_border:
            holes += 1
    return holes


def _symmetry_class(cells: Iterable[tuple[int, int]]) -> int:
    shape = _normalize(cells)
    if not shape:
        return 0
    occupied = set(shape)
    height, width = _shape_dims(shape)
    row_symmetric = all((height - 1 - r, c) in occupied for r, c in occupied)
    col_symmetric = all((r, width - 1 - c) in occupied for r, c in occupied)
    return (1 if row_symmetric else 0) + (2 if col_symmetric else 0)


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            seen.add((row, col))
            queue = deque([(row, col)])
            cells = []
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
            normalized = _normalize(cells)
            shape_h, shape_w = _shape_dims(normalized)
            components.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "normalized_cells": normalized,
                    "area": len(cells),
                    "r1": min(r for r, _ in cells),
                    "c1": min(c for _, c in cells),
                    "r2": max(r for r, _ in cells),
                    "c2": max(c for _, c in cells),
                    "height": shape_h,
                    "width": shape_w,
                    "holes": _hole_count(normalized),
                    "symmetry_class": _symmetry_class(normalized),
                }
            )
    components.sort(key=lambda obj: (obj["r1"], obj["c1"]))
    for index, obj in enumerate(components):
        obj["index"] = index
    return components


def _profile_from_components(components: Iterable[dict[str, Any]]) -> str | None:
    signature = tuple(
        sorted((obj["holes"], obj["symmetry_class"]) for obj in components)
    )
    for name, expected in _PROFILE_SIGNATURES.items():
        if signature == tuple(sorted(expected)):
            return name
    return None


def _analyze(grid: Any) -> dict[str, Any]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid must be a nonempty list of nonempty rows"]}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    errors: list[str] = []
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"invalid ARC color {value!r} at ({row_index},{col_index})")
    if errors:
        return {"errors": errors, "grid_h": len(grid), "grid_w": width}

    components = _components(grid)
    color_counts = Counter(obj["color"] for obj in components)
    near_pairs = []
    for left in range(len(components)):
        left_cells = set(components[left]["cells"])
        for right in range(left + 1, len(components)):
            right_cells = set(components[right]["cells"])
            if any(
                (r + dr, c + dc) in right_cells
                for r, c in left_cells
                for dr in (-1, 0, 1)
                for dc in (-1, 0, 1)
            ):
                near_pairs.append((left, right))
    palette = tuple(sorted({value for row in grid for value in row}))
    return {
        "errors": errors,
        "grid_h": len(grid),
        "grid_w": width,
        "palette": palette,
        "objects": components,
        "object_count": len(components),
        "color_component_counts": dict(color_counts),
        "near_pairs": tuple(near_pairs),
        "profile": _profile_from_components(components),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the generated object grammar while accepting all canonical inputs."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors
    height, width = analysis["grid_h"], analysis["grid_w"]
    if not 10 <= height <= 20:
        errors.append(f"grid height must be 10..20, got {height}")
    if not 16 <= width <= 24:
        errors.append(f"grid width must be 16..24, got {width}")
    if not 3 <= analysis["object_count"] <= 5:
        errors.append(f"expected 3..5 objects, found {analysis['object_count']}")
    if any(count != 1 for count in analysis["color_component_counts"].values()):
        errors.append("each non-zero color must form exactly one connected object")
    nonzero_palette = [color for color in analysis["palette"] if color != 0]
    if len(nonzero_palette) != analysis["object_count"]:
        errors.append("objects must use distinct non-zero colors")
    if analysis["near_pairs"]:
        errors.append(f"objects must be separated by background; near pairs {analysis['near_pairs'][:3]}")
    for obj in analysis["objects"]:
        if not 3 <= obj["area"] <= 20:
            errors.append(f"object {obj['index']} area must be 3..20, got {obj['area']}")
        if obj["height"] > 5 or obj["width"] > 5:
            errors.append(f"object {obj['index']} bounding box exceeds 5x5")
        if not 0 <= obj["holes"] <= 2:
            errors.append(f"object {obj['index']} hole count outside 0..2")

    requested = meta.get("overrides") if isinstance(meta, dict) else None
    if isinstance(requested, dict) and not errors:
        observed = observe_overrides(grid)
        for key, value in requested.items():
            if key in AXES and observed.get(key) != value:
                errors.append(
                    f"override {key}={value!r} not realized; observed {observed.get(key)!r}"
                )
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every declared exact axis from a generated grid."""
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return {}
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "profile": analysis["profile"],
    }


def _relation_matrix(components: list[dict[str, Any]]) -> list[list[int]]:
    return [
        [
            1
            if row == col
            else 8
            if left["symmetry_class"] == right["symmetry_class"]
            else 4
            if left["holes"] == right["holes"]
            else 0
            for col, right in enumerate(components)
        ]
        for row, left in enumerate(components)
    ]


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror for tests; the unchanged canonical Racket is authority."""
    source = deepcopy(grid)
    analysis = _analyze(source)
    if analysis.get("errors"):
        raise ValueError("invalid task input: " + "; ".join(analysis["errors"]))
    if not analysis["objects"]:
        raise ValueError("invalid task input: no non-zero objects")
    return _relation_matrix(analysis["objects"])


def _rival_hole_priority(grid):
    """Plausible canonical-fit rival: equal holes is checked before symmetry."""
    components = _analyze(grid).get("objects", [])
    return [
        [
            1
            if row == col
            else 4
            if left["holes"] == right["holes"]
            else 8
            if left["symmetry_class"] == right["symmetry_class"]
            else 0
            for col, right in enumerate(components)
        ]
        for row, left in enumerate(components)
    ]


def _rival_binary_holes(grid):
    """Plausible canonical-fit rival: compare hollow versus solid only."""
    components = _analyze(grid).get("objects", [])
    return [
        [
            1
            if row == col
            else 8
            if left["symmetry_class"] == right["symmetry_class"]
            else 4
            if bool(left["holes"]) == bool(right["holes"])
            else 0
            for col, right in enumerate(components)
        ]
        for row, left in enumerate(components)
    ]


def _rival_axis_count(grid):
    """Rival that merges row-only and column-only into one one-axis class."""
    components = _analyze(grid).get("objects", [])

    def axis_count(obj):
        symmetry = obj["symmetry_class"]
        return int(bool(symmetry & 1)) + int(bool(symmetry & 2))

    return [
        [
            1
            if row == col
            else 8
            if axis_count(left) == axis_count(right)
            else 4
            if left["holes"] == right["holes"]
            else 0
            for col, right in enumerate(components)
        ]
        for row, left in enumerate(components)
    ]


def _refutes_hole_priority(grid) -> bool:
    return rule_mirror(grid) != _rival_hole_priority(grid)


def _refutes_binary_holes(grid) -> bool:
    return rule_mirror(grid) != _rival_binary_holes(grid)


def _refutes_axis_count(grid) -> bool:
    return rule_mirror(grid) != _rival_axis_count(grid)


def semantic_signature(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return {"errors": analysis["errors"]}
    return {
        "profile": analysis["profile"],
        "features": tuple(
            (obj["holes"], obj["symmetry_class"], obj["area"])
            for obj in analysis["objects"]
        ),
        "output_symbols": tuple(sorted({value for row in rule_mirror(grid) for value in row})),
        "strict_canonical_like": strict_canonical_like(grid) == [],
        "refutes_hole_priority": _refutes_hole_priority(grid),
        "refutes_binary_holes": _refutes_binary_holes(grid),
        "refutes_axis_count": _refutes_axis_count(grid),
    }


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    reasons = list(analysis.get("errors", []))
    if reasons:
        return reasons
    profile = (analysis["grid_h"], analysis["grid_w"], len(analysis["palette"]))
    if profile not in _CANONICAL_PROFILES:
        reasons.append(f"profile {profile} is outside canonical H/W/palette support")
    expected_objects = 3 if profile == (10, 16, 4) else 4 if profile == (11, 17, 5) else None
    if expected_objects is not None and analysis["object_count"] != expected_objects:
        reasons.append(
            f"canonical profile expects {expected_objects} objects, found {analysis['object_count']}"
        )
    if any(count != 1 for count in analysis["color_component_counts"].values()):
        reasons.append("canonical colors each form one connected object")
    height, width = analysis["grid_h"], analysis["grid_w"]
    if any(grid[0][col] != 0 or grid[height - 1][col] != 0 for col in range(width)):
        reasons.append("canonical outer rows are blank")
    if any(grid[row][0] != 0 or grid[row][width - 1] != 0 for row in range(height)):
        reasons.append("canonical outer columns are blank")
    return reasons


SEMANTIC_WITNESSES = {
    "refutes_hole_priority_shortcut": _refutes_hole_priority,
    "refutes_binary_hole_shortcut": _refutes_binary_holes,
    "refutes_axis_count_shortcut": _refutes_axis_count,
}
SEMANTIC_RIVALS = {
    "hole_priority": _rival_hole_priority,
    "binary_holes": _rival_binary_holes,
    "axis_count": _rival_axis_count,
}
WITNESS_RIVALS = {
    "refutes_hole_priority_shortcut": ["hole_priority"],
    "refutes_binary_hole_shortcut": ["binary_holes"],
    "refutes_axis_count_shortcut": ["axis_count"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# These two rivals reproduce all three official pairs; generated witnesses are
# therefore necessary to identify the intended generalization.
CANONICAL_SHORTCUTS = {
    "hole_priority": _rival_hole_priority,
    "binary_holes": _rival_binary_holes,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require a four-demo window to expose all symbols and kill all rivals."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    grids = []
    outputs = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} invalid: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with pairwise feature rule")
            continue
        grids.append(pair["input"])
        outputs.append(expected)
    if len(grids) != len(demos):
        return reasons

    symbols = {value for output in outputs for row in output for value in row}
    if not {0, 1, 4, 8} <= symbols:
        reasons.append("demonstrations do not expose all 0/1/4/8 relation symbols")
    if not any(_refutes_hole_priority(grid) for grid in grids):
        reasons.append("holes-first precedence rival survives every demonstration")
    if not any(_refutes_binary_holes(grid) for grid in grids):
        reasons.append("binary hollow/solid rival survives every demonstration")
    if not any(_refutes_axis_count(grid) for grid in grids):
        reasons.append("axis-count rival survives every demonstration")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not a pair with an input")
    else:
        query_errors = self_check(query["input"])
        if query_errors:
            reasons.append(f"query invalid: {query_errors[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output disagrees with pairwise feature rule")
    return reasons


def schedule_profile(seed, sample_index, difficulty=None):
    """Four-residue schedule; seed and difficulty do not alter coverage."""
    del seed, difficulty
    return PROFILES[int(sample_index) % len(PROFILES)]


SCHEDULE_PROFILES = PROFILES


def _scheduled_defaults(sample_index: int, difficulty: str | None) -> dict[str, Any]:
    profile = schedule_profile(0, sample_index, difficulty)
    band = difficulty if difficulty in ("easy", "medium", "hard") else "medium"
    if profile == "canonical3":
        return {"grid_h": 10, "grid_w": 16, "profile": profile}
    if profile == "canonical4":
        return {"grid_h": 11, "grid_w": 17, "profile": profile}
    if profile == "hole_priority":
        return {
            "grid_h": {"easy": 12, "medium": 15, "hard": 18}[band],
            "grid_w": {"easy": 18, "medium": 21, "hard": 24}[band],
            "profile": profile,
        }
    return {
        "grid_h": {"easy": 13, "medium": 16, "hard": 20}[band],
        "grid_w": {"easy": 19, "medium": 22, "hard": 24}[band],
        "profile": profile,
    }


def _draw_int_axis(ctx, overrides, name: str, default: int, lo: int, hi: int) -> int:
    if name in overrides and overrides[name] is not None:
        return int(ctx.draw_int(name, lo, hi))
    return int(ctx.draw_int(name, default, default))


def _draw_choice_axis(ctx, overrides, name: str, default: str, options) -> str:
    if name in overrides and overrides[name] is not None:
        return str(ctx.draw_choice(name, options))
    return str(ctx.draw_choice(name, (default,)))


def _shape_candidates(signature: tuple[int, int]) -> tuple[tuple[tuple[int, int], ...], ...]:
    variants = set()
    for base in _SHAPE_BANK[signature]:
        variants.update(_axis_flips(base))
    checked = []
    for shape in sorted(variants):
        if (_hole_count(shape), _symmetry_class(shape)) != signature:
            raise AssertionError(f"shape bank mismatch for {signature}: {shape}")
        checked.append(shape)
    return tuple(checked)


def _choose_shapes(signatures: list[tuple[int, int]], rng) -> list[tuple[tuple[int, int], ...]]:
    used: dict[tuple[int, int], set[tuple[tuple[int, int], ...]]] = {}
    result = []
    for signature in signatures:
        candidates = list(_shape_candidates(signature))
        available = [shape for shape in candidates if shape not in used.setdefault(signature, set())]
        chosen = rng.choice(available or candidates)
        used[signature].add(chosen)
        result.append(chosen)
    return result


def _place_shapes(
    height: int,
    width: int,
    shapes: list[tuple[tuple[int, int], ...]],
    colors: list[int],
    rng,
    *,
    canonical_margin: bool,
) -> list[list[int]]:
    grid = full_grid(height, width, 0)
    if len(shapes) == 3:
        row_sizes = (2, 1)
    elif len(shapes) == 4:
        row_sizes = (2, 2)
    elif len(shapes) == 5:
        row_sizes = (3, 2)
    else:
        raise ValueError(f"unsupported object count {len(shapes)}")
    groups = []
    cursor = 0
    for size in row_sizes:
        groups.append(list(zip(shapes[cursor:cursor + size], colors[cursor:cursor + size])))
        cursor += size

    row_heights = [max(_shape_dims(shape)[0] for shape, _ in group) for group in groups]
    total_height = sum(row_heights) + len(groups) - 1  # one blank row between bands
    margin = 1 if canonical_margin else 0
    if total_height + 2 * margin > height:
        margin = 0
    if total_height > height:
        raise ValueError(f"shapes require height {total_height}, grid has {height}")
    top = rng.randint(margin, height - total_height - margin)

    row_top = top
    for group, row_height in zip(groups, row_heights):
        widths = [_shape_dims(shape)[1] for shape, _ in group]
        total_width = sum(widths) + len(group) - 1  # one blank column between bboxes
        side_margin = 1 if canonical_margin and total_width + 2 <= width else 0
        if total_width > width:
            raise ValueError(f"shape row requires width {total_width}, grid has {width}")
        left = rng.randint(side_margin, width - total_width - side_margin)
        col = left
        for (shape, color), shape_width in zip(group, widths):
            shape_height, _ = _shape_dims(shape)
            object_top = row_top + rng.randint(0, row_height - shape_height)
            for rr, cc in shape:
                if grid[object_top + rr][col + cc] != 0:
                    raise ValueError("internal placement overlap")
                grid[object_top + rr][col + cc] = color
            col += shape_width + 1
        row_top += row_height + 1
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be one of None, easy, medium, hard")

    defaults = _scheduled_defaults(int(sample_index), difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_int_axis(ctx, overrides, "grid_h", defaults["grid_h"], 10, 20)
    width = _draw_int_axis(ctx, overrides, "grid_w", defaults["grid_w"], 16, 24)
    profile = _draw_choice_axis(ctx, overrides, "profile", defaults["profile"], PROFILES)

    signatures = list(_PROFILE_SIGNATURES[profile])
    order_rng = ctx.draw_rng("object_order")
    order_rng.shuffle(signatures)
    shape_rng = ctx.draw_rng("shape_variants")
    shapes = _choose_shapes(signatures, shape_rng)
    color_rng = ctx.draw_rng("colors")
    colors = color_rng.sample(list(range(1, 10)), len(shapes))
    layout_rng = ctx.draw_rng("layout")
    canonical_margin = (height, width, len(shapes) + 1) in _CANONICAL_PROFILES
    grid = _place_shapes(
        height,
        width,
        shapes,
        colors,
        layout_rng,
        canonical_margin=canonical_margin,
    )

    errors = self_check(grid)
    if errors:
        raise ValueError("generated invalid lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {"grid_h": height, "grid_w": width, "profile": profile}
    if observed != expected:
        raise ValueError(f"axis observation mismatch: expected {expected}, observed {observed}")
    return grid
