"""Generator for ARC task d66f6f5141d9 — color-directed edge translation.

A single 4-connected shape is translated rigidly until its bounding box is
flush with the edge encoded by its color: 3=left, 4=bottom, 6=top, 8=right.
The canonical 3x3 ring is deliberately common, while several asymmetric shape
families and both near/far starting distances prevent template memorization.
"""
from __future__ import annotations

from collections import deque
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d66f6f5141d9"
TASK_ID = "d66f6f5141d9"
VERSION = "3.0.0"
RULE_HASH = "8df4c346e899"

SUMMARY = (
    "Find the only nonzero 4-connected shape. Its color names the destination "
    "edge: 3 means left, 4 bottom, 6 top, and 8 right. Translate the complete "
    "shape as one rigid object until its bounding box is flush with that edge; "
    "preserve grid size, color, orientation, and every occupied-cell offset."
)

INVARIANTS = [
    "background is literal color 0",
    "there is exactly one 4-connected shape in exactly one color from {3,4,6,8}",
    "the shape belongs to the declared ring/U/T/Z/L/stair grammar",
    "the input shape is not already flush with its color-encoded target edge",
    "the rule is a rigid translation: size, color, orientation, and offsets are preserved",
    "standard 3-demo and 4-demo lessons always repeat the query color in a demonstration",
]

COLORS = (3, 4, 6, 8)
SHAPE_KINDS = ("ring", "U", "T", "Z", "L", "stair")
DISTANCE_PROFILES = ("near", "far")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted draw over the full valid range; 10 is common",
        "valid": "5..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted draw over the full valid range; 10 is common",
        "valid": "6..18",
    },
    "color": {
        "type": "color",
        "default": "seed-rotated four-example teaching schedule",
        "valid": "3|4|6|8",
    },
    "shape_kind": {
        "type": "str",
        "default": "rng with canonical ring intentionally common",
        "valid": "|".join(SHAPE_KINDS),
    },
    "distance_profile": {
        "type": "str",
        "default": "seed-rotated near/far teaching schedule",
        "valid": "near|far",
    },
}

# One representative per family. A deterministic D8 transform is applied after
# selection. The families remain disjoint under D8, so shape_kind is recoverable
# from the returned grid and can be audited as an exact override axis.
_SHAPES = {
    "ring": ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
    "U": ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2)),
    "T": ((0, 0), (1, 0), (1, 1), (1, 2)),
    "Z": ((0, 0), (0, 1), (1, 1), (1, 2)),
    "L": ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    "stair": ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
}

_TARGET_EDGE = {3: "left", 4: "bottom", 6: "top", 8: "right"}
_ALLOWED_DIFFICULTIES = (None, "easy", "medium", "hard")


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    pts = tuple(cells)
    if not pts:
        return tuple()
    min_r = min(r for r, _ in pts)
    min_c = min(c for _, c in pts)
    return tuple(sorted((r - min_r, c - min_c) for r, c in pts))


def _transform(cells: Iterable[tuple[int, int]], transform_index: int) -> tuple[tuple[int, int], ...]:
    """Apply one of the eight square symmetries, then normalize."""
    pts = _normalize(cells)
    if not pts:
        return tuple()
    size = max(max(r for r, _ in pts), max(c for _, c in pts))
    transformed = []
    for r, c in pts:
        if transform_index == 0:
            nr, nc = r, c
        elif transform_index == 1:
            nr, nc = c, size - r
        elif transform_index == 2:
            nr, nc = size - r, size - c
        elif transform_index == 3:
            nr, nc = size - c, r
        elif transform_index == 4:
            nr, nc = r, size - c
        elif transform_index == 5:
            nr, nc = size - r, c
        elif transform_index == 6:
            nr, nc = c, r
        elif transform_index == 7:
            nr, nc = size - c, size - r
        else:  # defensive; callers use 0..7
            raise ValueError(f"invalid transform_index {transform_index}")
        transformed.append((nr, nc))
    return _normalize(transformed)


def _variants(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[tuple[int, int], ...]]:
    return frozenset(_transform(cells, i) for i in range(8))


_SHAPE_VARIANTS = {name: _variants(cells) for name, cells in _SHAPES.items()}
_VARIANT_TO_KIND = {
    variant: name
    for name, variants in _SHAPE_VARIANTS.items()
    for variant in variants
}
if len(_VARIANT_TO_KIND) != sum(len(v) for v in _SHAPE_VARIANTS.values()):
    raise AssertionError("shape families overlap under D8 and are not recoverable")


def _weighted_dimension_values(axis: str, difficulty) -> tuple[int, ...]:
    """Return full-support weighted choices; every declared boundary remains legal."""
    if axis == "grid_h":
        full = tuple(range(5, 15))
    elif axis == "grid_w":
        full = tuple(range(6, 19))
    else:
        raise ValueError(f"unknown dimension axis {axis!r}")

    # Canonical 10x10 grids must be represented materially rather than only as
    # a vanishing tail. Difficulty changes secondary weights, never validity.
    canonical_weight = (10,) * 20
    if difficulty == "easy":
        band = tuple(v for v in full if v <= 10) * 2
    elif difficulty == "hard":
        band = tuple(v for v in full if v >= 10) * 2
    elif difficulty == "medium":
        band = tuple(v for v in full if 8 <= v <= 13) * 2
    else:
        band = full
    return full + band + canonical_weight


def _validate_call(difficulty, overrides: dict) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    if isinstance(difficulty, bool):
        raise ValueError(f"unsupported difficulty {difficulty!r}")
    if difficulty not in _ALLOWED_DIFFICULTIES:
        if not isinstance(difficulty, (int, float)) or not 0.0 <= float(difficulty) <= 1.0:
            raise ValueError(f"unsupported difficulty {difficulty!r}")


def _scheduled_choice(ctx, label: str, full_options: tuple, scheduled_value):
    """Consume overrides through GenCtx; otherwise record a deterministic lesson slot."""
    options = full_options if label in ctx.overrides and ctx.overrides[label] is not None else (scheduled_value,)
    return ctx.draw_choice(label, options)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the selected Racket rule is the oracle."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    h = ctx.draw_choice("grid_h", _weighted_dimension_values("grid_h", difficulty))
    w = ctx.draw_choice("grid_w", _weighted_dimension_values("grid_w", difficulty))

    # A three-slot cycle makes every standard 3-demo or 4-demo query repeat a
    # demonstrated color, even when run_one starts at a nonzero sample_index.
    # The seed rotates which three colors appear, so corpus-level branch counts
    # remain balanced and no query color is globally privileged.
    color_slot = int(sample_index) % 3
    color = _scheduled_choice(ctx, "color", COLORS, COLORS[(int(seed) + color_slot) % 4])
    distance_profile = _scheduled_choice(
        ctx,
        "distance_profile",
        DISTANCE_PROFILES,
        DISTANCE_PROFILES[(int(seed) + int(sample_index)) % 2],
    )
    shape_kind = ctx.draw_choice(
        "shape_kind",
        ("ring",) * 9 + SHAPE_KINDS,
    )

    transform_index = ctx.draw_rng("shape_transform").randrange(8)
    shape = _transform(_SHAPES[shape_kind], transform_index)
    shape_h = max(r for r, _ in shape) + 1
    shape_w = max(c for _, c in shape) + 1
    if shape_h > h or shape_w > w:
        raise ValueError(f"shape_kind={shape_kind!r} does not fit grid {h}x{w}")

    max_vertical = h - shape_h
    max_horizontal = w - shape_w
    if color in (4, 6) and max_vertical < 2:
        raise ValueError(f"grid {h}x{w} leaves no distinct near/far vertical starts")
    if color in (3, 8) and max_horizontal < 2:
        raise ValueError(f"grid {h}x{w} leaves no distinct near/far horizontal starts")

    layout_rng = ctx.draw_rng("orthogonal_position")
    if color == 6:  # top
        top = 1 if distance_profile == "near" else max_vertical
        left = layout_rng.randint(0, max_horizontal)
    elif color == 4:  # bottom
        top = max_vertical - 1 if distance_profile == "near" else 0
        left = layout_rng.randint(0, max_horizontal)
    elif color == 3:  # left
        top = layout_rng.randint(0, max_vertical)
        left = 1 if distance_profile == "near" else max_horizontal
    else:  # color == 8, right
        top = layout_rng.randint(0, max_vertical)
        left = max_horizontal - 1 if distance_profile == "near" else 0

    grid = full_grid(h, w, 0)
    for dr, dc in shape:
        grid[top + dr][left + dc] = color
    errors = self_check(grid)
    if errors:  # fail loudly instead of returning an off-contract sample
        raise AssertionError(f"internal generator invariant failure: {errors}")
    return grid


def _grid_shape_errors(grid) -> tuple[list[str], int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"], 0, 0
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be nonempty and rectangular"], len(grid), width
    errors = []
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid values must be integer ARC colors 0..9")
    return errors, len(grid), width


def _component_count(cells: Iterable[tuple[int, int]]) -> int:
    remaining = set(cells)
    count = 0
    while remaining:
        count += 1
        start = remaining.pop()
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    queue.append(nxt)
    return count


def _analysis(grid) -> dict[str, object]:
    errors, h, w = _grid_shape_errors(grid)
    result: dict[str, object] = {"errors": errors, "grid_h": h, "grid_w": w}
    if errors:
        return result
    if not (5 <= h <= 14):
        errors.append(f"grid height must be 5..14, got {h}")
    if not (6 <= w <= 18):
        errors.append(f"grid width must be 6..18, got {w}")

    valued_cells = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not valued_cells:
        errors.append("expected one nonzero source shape")
        return result

    colors = {value for _, _, value in valued_cells}
    if len(colors) != 1:
        errors.append(f"shape must use exactly one nonzero color, got {sorted(colors)}")
        return result
    color = next(iter(colors))
    result["color"] = color
    if color not in COLORS:
        errors.append(f"shape color {color} is not a direction key in {COLORS}")

    cells = [(r, c) for r, c, _ in valued_cells]
    components = _component_count(cells)
    result["component_count"] = components
    if components != 1:
        errors.append(f"shape must be one 4-connected component, got {components}")

    rmin = min(r for r, _ in cells)
    rmax = max(r for r, _ in cells)
    cmin = min(c for _, c in cells)
    cmax = max(c for _, c in cells)
    normalized = _normalize(cells)
    shape_kind = _VARIANT_TO_KIND.get(normalized)
    result.update(
        {
            "shape_kind": shape_kind or "unknown",
            "cell_count": len(cells),
            "bbox": (rmin, cmin, rmax, cmax),
            "bbox_h": rmax - rmin + 1,
            "bbox_w": cmax - cmin + 1,
        }
    )
    if shape_kind is None:
        errors.append("shape is outside the declared ring/U/T/Z/L/stair grammar")

    if color in COLORS:
        if color == 3:
            distance = cmin
            max_distance = w - (cmax - cmin + 1)
        elif color == 8:
            distance = w - 1 - cmax
            max_distance = w - (cmax - cmin + 1)
        elif color == 6:
            distance = rmin
            max_distance = h - (rmax - rmin + 1)
        else:  # color == 4
            distance = h - 1 - rmax
            max_distance = h - (rmax - rmin + 1)
        result.update(
            {
                "target_edge": _TARGET_EDGE[color],
                "distance_to_target": distance,
                "max_distance_to_target": max_distance,
                "distance_profile": "near" if distance == 1 else "far" if distance == max_distance else "interior",
                "already_at_target": distance == 0,
            }
        )
        if distance == 0:
            errors.append(f"shape is already flush with target edge {_TARGET_EDGE[color]}")
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the exact structural teaching grammar, including canonicals."""
    return list(_analysis(grid)["errors"])


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared axis exactly from a generated return value."""
    info = _analysis(grid)
    return {
        "grid_h": int(info.get("grid_h", 0)),
        "grid_w": int(info.get("grid_w", 0)),
        "color": int(info.get("color", -1)),
        "shape_kind": str(info.get("shape_kind", "unknown")),
        "distance_profile": str(info.get("distance_profile", "unknown")),
    }


def semantic_observables(grid) -> dict[str, object]:
    """Expose task-linked census fields without mutating the input grid."""
    info = dict(_analysis(grid))
    errors = list(info.pop("errors"))
    bbox = info.get("bbox")
    if bbox and info.get("color") in COLORS:
        rmin, cmin, rmax, cmax = bbox
        h, w = int(info["grid_h"]), int(info["grid_w"])
        distances = {
            "top": rmin,
            "bottom": h - 1 - rmax,
            "left": cmin,
            "right": w - 1 - cmax,
        }
        target = str(info["target_edge"])
        info["edge_distances"] = distances
        info["target_is_nearest_edge"] = distances[target] == min(distances.values())
        info["target_is_farthest_edge"] = distances[target] == max(distances.values())
    info["valid"] = not errors
    info["errors"] = errors
    return info


def rule_mirror(grid) -> list[list[int]]:
    """Pure-Python mirror for focused parity tests; Racket remains runtime authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError(f"off-contract input: {errors}")
    info = _analysis(grid)
    h, w = int(info["grid_h"]), int(info["grid_w"])
    rmin, cmin, rmax, cmax = info["bbox"]
    color = int(info["color"])
    if color == 3:
        dr, dc = 0, -cmin
    elif color == 8:
        dr, dc = 0, (w - 1) - cmax
    elif color == 6:
        dr, dc = -rmin, 0
    else:  # color == 4
        dr, dc = (h - 1) - rmax, 0

    out = full_grid(h, w, 0)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                out[r + dr][c + dc] = value
    return out
