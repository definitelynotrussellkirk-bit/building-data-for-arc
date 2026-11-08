"""Generator for d1dd527dba87 — normalized XOR of the largest blue/red shapes.

The canonical rule selects the largest 4-connected color-1 object and largest
4-connected color-2 object, translates each occupancy mask to its own bbox
origin, takes the symmetric difference, tightly crops it, and paints the result
color 8.  A singleton object in an unrelated color is ignored.

Ordinary lessons always make XOR identifiable: the selected shapes share at
least one normalized cell and each also owns at least one exclusive cell.
Scheduled same-color decoys prove that selection is by largest object, while
three spatial layouts prove that absolute position is irrelevant.
"""
from __future__ import annotations

from itertools import combinations
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d1dd527dba87"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "a9d6dd158d01"

SUMMARY = (
    "On a 0-background grid, select the largest blue (1) object and the "
    "largest red (2) object. Normalize each selected object's cells to its "
    "own top-left bbox origin, take their symmetric difference, tightly crop "
    "that mask, and paint its occupied cells cyan (8). Smaller same-color "
    "objects and the singleton unrelated-color distractor are ignored."
)

INVARIANTS = [
    "background is 0; dimensions stay in the canonical 9-10 by 11-13 envelope",
    "a unique largest connected color-1 object and color-2 object each have 3-5 cells",
    "the selected normalized shapes partially overlap: shared and exclusive cells both exist",
    "exactly one singleton distractor uses one of colors 4,5,6,7,9",
    "optional same-color domino decoys are strictly smaller than the selected objects",
    "the selected objects are spatially separated, so normalization is answer-bearing",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.05

_CANONICAL_DIMS = ((9, 11), (9, 12), (10, 12), (10, 13))
_DISTRACTOR_COLORS = (4, 5, 6, 7, 9)
_LAYOUTS = ("blue_above_red", "red_above_blue", "blue_left_red")
_DECOY_MODES = ("none", "blue", "red", "both")
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical joint profile",
        "valid": "9..10",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical joint profile",
        "valid": "11..13",
    },
    "blue_cells": {
        "type": "int",
        "default": "difficulty-skewed 3..5",
        "valid": "3..5",
    },
    "red_cells": {
        "type": "int",
        "default": "difficulty-skewed 3..5",
        "valid": "3..5",
    },
    "distractor_color": {
        "type": "color",
        "default": "keyed choice",
        "valid": "4|5|6|7|9",
    },
    "decoy_mode": {
        "type": "enum",
        "default": "sample_index schedule",
        "valid": "none|blue|red|both",
    },
    "layout": {
        "type": "enum",
        "default": "sample_index schedule",
        "valid": "blue_above_red|red_above_blue|blue_left_red",
    },
}


def _unknown_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")


def _recorded_default_int(ctx, label: str, lo: int, hi: int, default: int) -> int:
    """Consume an exact int override or record a deterministic linked default."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        value = int(ctx.overrides[label])
        if not lo <= value <= hi:
            raise ValueError(f"{label} override {value} outside [{lo}, {hi}]")
        return int(ctx._record(label, value, from_override=True))
    return int(ctx._record(label, int(default), from_override=False))


def _scheduled_choice(ctx, label: str, options: tuple[str, ...], index: int) -> str:
    """Consume an exact override or record a lesson-covering schedule value."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        value = str(ctx.overrides[label])
        if value not in options:
            raise ValueError(f"{label} override {value!r} not in {options!r}")
        return str(ctx._record(label, value, from_override=True))
    return str(ctx._record(label, options[index % len(options)], from_override=False))


def _connected(cells: Iterable[tuple[int, int]]) -> bool:
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in _CARDINAL:
            nxt = (r + dr, c + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return len(seen) == len(cells)


def _normalize(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = tuple(cells)
    if not cells:
        return frozenset()
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return frozenset((r - min_r, c - min_c) for r, c in cells)


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _bbox_dims(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    r0, c0, r1, c1 = _bbox(cells)
    return r1 - r0 + 1, c1 - c0 + 1


def _enumerate_shapes() -> dict[int, tuple[frozenset[tuple[int, int]], ...]]:
    canvas = tuple((r, c) for r in range(3) for c in range(3))
    result: dict[int, tuple[frozenset[tuple[int, int]], ...]] = {}
    for size in range(3, 6):
        shapes = []
        for combo in combinations(canvas, size):
            shape = frozenset(combo)
            if min(r for r, _ in shape) != 0 or min(c for _, c in shape) != 0:
                continue
            if _connected(shape):
                shapes.append(shape)
        result[size] = tuple(sorted(shapes, key=lambda s: tuple(sorted(s))))
    return result


_SHAPES_BY_SIZE = _enumerate_shapes()


def _shape_pair_candidates(
    blue_cells: int,
    red_cells: int,
    *,
    strict_profile: bool,
    relation_slot: int,
) -> list[tuple[frozenset[tuple[int, int]], frozenset[tuple[int, int]]]]:
    candidates = []
    fallback = []
    for blue in _SHAPES_BY_SIZE[blue_cells]:
        for red in _SHAPES_BY_SIZE[red_cells]:
            shared = blue & red
            if not shared or not (blue - red) or not (red - blue):
                continue
            xor = blue ^ red
            xh, xw = _bbox_dims(xor)
            pair = (blue, red)
            fallback.append(pair)
            if strict_profile:
                if len(xor) not in (3, 4) or (xh, xw) not in {
                    (2, 3),
                    (3, 2),
                    (3, 3),
                }:
                    continue
            elif relation_slot == 0 and not xw > xh:
                continue
            elif relation_slot == 1 and not xh > xw:
                continue
            elif relation_slot == 2 and not xh == xw:
                continue
            candidates.append(pair)
    return candidates or fallback


def _absolute(shape: Iterable[tuple[int, int]], top: int, left: int) -> set[tuple[int, int]]:
    return {(top + r, left + c) for r, c in shape}


def _moat_free(cells: set[tuple[int, int]], occupied: set[tuple[int, int]], h: int, w: int) -> bool:
    if any(not (0 <= r < h and 0 <= c < w) for r, c in cells):
        return False
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if (r + dr, c + dc) in occupied:
                    return False
    return True


def _main_origin_pairs(
    blue: frozenset[tuple[int, int]],
    red: frozenset[tuple[int, int]],
    h: int,
    w: int,
    layout: str,
) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    bh, bw = _bbox_dims(blue)
    rh, rw = _bbox_dims(red)
    pairs = []
    for br in range(h - bh + 1):
        for bc in range(w - bw + 1):
            blue_box = (br, bc, br + bh - 1, bc + bw - 1)
            for rr in range(h - rh + 1):
                for rc in range(w - rw + 1):
                    red_box = (rr, rc, rr + rh - 1, rc + rw - 1)
                    if layout == "blue_above_red":
                        lawful = blue_box[2] + 1 < red_box[0]
                    elif layout == "red_above_blue":
                        lawful = red_box[2] + 1 < blue_box[0]
                    else:
                        vertical_overlap = not (
                            blue_box[2] < red_box[0] or red_box[2] < blue_box[0]
                        )
                        lawful = blue_box[3] + 1 < red_box[1] and vertical_overlap
                    if lawful:
                        pairs.append(((br, bc), (rr, rc)))
    return pairs


def _domino_candidates(h: int, w: int) -> list[set[tuple[int, int]]]:
    result = []
    for r in range(h):
        for c in range(w):
            if c + 1 < w:
                result.append({(r, c), (r, c + 1)})
            if r + 1 < h:
                result.append({(r, c), (r + 1, c)})
    return result


def _place_scene(
    *,
    h: int,
    w: int,
    blue: frozenset[tuple[int, int]],
    red: frozenset[tuple[int, int]],
    layout: str,
    decoy_mode: str,
    distractor_color: int,
    rng,
) -> list[list[int]]:
    origin_pairs = _main_origin_pairs(blue, red, h, w, layout)
    rng.shuffle(origin_pairs)
    dominoes = _domino_candidates(h, w)

    for (br, bc), (rr, rc) in origin_pairs:
        blue_abs = _absolute(blue, br, bc)
        red_abs = _absolute(red, rr, rc)
        if not _moat_free(red_abs, blue_abs, h, w):
            continue
        occupied = set(blue_abs | red_abs)
        placed: list[tuple[set[tuple[int, int]], int]] = [
            (blue_abs, 1),
            (red_abs, 2),
        ]
        failed = False
        for want, color in ((decoy_mode in {"blue", "both"}, 1),
                            (decoy_mode in {"red", "both"}, 2)):
            if not want:
                continue
            choices = [d for d in dominoes if _moat_free(d, occupied, h, w)]
            if not choices:
                failed = True
                break
            decoy = rng.choice(choices)
            occupied.update(decoy)
            placed.append((decoy, color))
        if failed:
            continue
        singles = [
            {(r, c)}
            for r in range(h)
            for c in range(w)
            if _moat_free({(r, c)}, occupied, h, w)
        ]
        if not singles:
            continue
        singleton = rng.choice(singles)
        placed.append((singleton, distractor_color))

        grid = full_grid(h, w, 0)
        for cells, color in placed:
            for r, c in cells:
                grid[r][c] = color
        return grid
    raise ValueError(
        f"could not place layout={layout} decoy_mode={decoy_mode} on {h}x{w}"
    )


def _components(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        component = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in _CARDINAL:
                nxt = (r + dr, c + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    component.add(nxt)
                    stack.append(nxt)
        result.append(component)
    return sorted(result, key=lambda x: (-len(x), _bbox(x)))


def _layout_name(blue: set[tuple[int, int]], red: set[tuple[int, int]]) -> str:
    bb = _bbox(blue)
    rb = _bbox(red)
    if bb[2] < rb[0]:
        return "blue_above_red"
    if rb[2] < bb[0]:
        return "red_above_blue"
    if bb[3] < rb[1]:
        return "blue_left_red"
    return "unsupported_overlap"


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be ARC colors 0..9"]
    return []


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _validate_grid(grid)
    if errors:
        return {"errors": errors}
    grid = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    if not (9 <= h <= 10 and 11 <= w <= 13):
        errors.append(f"dimensions {h}x{w} outside 9..10 x 11..13")

    palette = sorted({value for row in grid for value in row})
    extra_colors = [c for c in palette if c not in (0, 1, 2)]
    if len(extra_colors) != 1 or extra_colors[0] not in _DISTRACTOR_COLORS:
        errors.append(
            "need exactly one distractor color from 4,5,6,7,9; "
            f"found {extra_colors}"
        )
        distractor_color = extra_colors[0] if len(extra_colors) == 1 else None
    else:
        distractor_color = extra_colors[0]
        count = sum(value == distractor_color for row in grid for value in row)
        if count != 1:
            errors.append(f"distractor color {distractor_color} must be singleton, found {count}")

    blue_components = _components(grid, 1)
    red_components = _components(grid, 2)
    for name, components in (("blue", blue_components), ("red", red_components)):
        if not 1 <= len(components) <= 2:
            errors.append(f"need one selected {name} object and at most one decoy")
            continue
        sizes = [len(component) for component in components]
        if not 3 <= sizes[0] <= 5:
            errors.append(f"largest {name} object must have 3..5 cells, found {sizes[0]}")
        if len(sizes) == 2 and sizes[1] != 2:
            errors.append(f"{name} decoy must be a 2-cell domino, found size {sizes[1]}")
        if len(sizes) == 2 and sizes[0] <= sizes[1]:
            errors.append(f"largest {name} object must be unique")

    blue_main = blue_components[0] if blue_components else set()
    red_main = red_components[0] if red_components else set()
    blue_shape = _normalize(blue_main)
    red_shape = _normalize(red_main)
    shared = blue_shape & red_shape
    blue_only = blue_shape - red_shape
    red_only = red_shape - blue_shape
    xor = blue_shape ^ red_shape

    if blue_main and _bbox_dims(blue_main)[0] > 3 or blue_main and _bbox_dims(blue_main)[1] > 3:
        errors.append("largest blue object must fit a 3x3 bbox")
    if red_main and _bbox_dims(red_main)[0] > 3 or red_main and _bbox_dims(red_main)[1] > 3:
        errors.append("largest red object must fit a 3x3 bbox")
    if blue_main and red_main:
        if not shared:
            errors.append("normalized selected shapes need at least one shared cell")
        if not blue_only:
            errors.append("blue selected shape needs at least one exclusive cell")
        if not red_only:
            errors.append("red selected shape needs at least one exclusive cell")
    layout = _layout_name(blue_main, red_main) if blue_main and red_main else "missing"
    if layout == "unsupported_overlap":
        errors.append("selected objects must be separated in a declared spatial layout")

    blue_has_decoy = len(blue_components) == 2
    red_has_decoy = len(red_components) == 2
    if blue_has_decoy and red_has_decoy:
        decoy_mode = "both"
    elif blue_has_decoy:
        decoy_mode = "blue"
    elif red_has_decoy:
        decoy_mode = "red"
    else:
        decoy_mode = "none"

    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "palette": palette,
        "distractor_color": distractor_color,
        "blue_components": blue_components,
        "red_components": red_components,
        "blue_main": blue_main,
        "red_main": red_main,
        "blue_shape": blue_shape,
        "red_shape": red_shape,
        "shared": shared,
        "blue_only": blue_only,
        "red_only": red_only,
        "xor": xor,
        "xor_dims": _bbox_dims(xor) if xor else (1, 1),
        "layout": layout,
        "decoy_mode": decoy_mode,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or shortcut-hiding lesson inputs."""
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Strict empirical manifold shared by all five canonical inputs.

    Position is intentionally *not* quotiented here: every canonical selected
    blue object is above the selected red object. Generalized layouts remain in
    the teaching distribution and are measured separately as anti-shortcut
    witnesses.
    """
    analysis = _analysis(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    if (analysis["grid_h"], analysis["grid_w"]) not in _CANONICAL_DIMS:
        reasons.append("dimensions are outside the observed canonical joint profiles")
    if analysis["decoy_mode"] != "none":
        reasons.append("canonical inputs contain no same-color decoy object")
    if analysis["layout"] != "blue_above_red":
        reasons.append("canonical inputs place selected blue above selected red")
    if len(analysis["xor"]) not in (3, 4):
        reasons.append("canonical XOR masks contain 3 or 4 cells")
    if analysis["xor_dims"] not in {(2, 3), (3, 2), (3, 3)}:
        reasons.append("canonical XOR bbox is 2x3, 3x2, or 3x3")
    return reasons


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact declared axis from the returned input grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "blue_cells": len(analysis["blue_main"]),
        "red_cells": len(analysis["red_main"]),
        "distractor_color": analysis["distractor_color"],
        "decoy_mode": analysis["decoy_mode"],
        "layout": analysis["layout"],
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _unknown_overrides(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    band = "medium" if difficulty is None else difficulty
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    dims_rng = ctx.draw_rng("canonical_dims")
    default_h, default_w = dims_rng.choice(_CANONICAL_DIMS)
    h = _recorded_default_int(ctx, "grid_h", 9, 10, default_h)
    w = _recorded_default_int(ctx, "grid_w", 11, 13, default_w)
    blue_cells = ctx.draw_int_diff("blue_cells", 3, 5)
    red_cells = ctx.draw_int_diff("red_cells", 3, 5)
    distractor_color = ctx.draw_choice("distractor_color", _DISTRACTOR_COLORS)
    decoy_mode = _scheduled_choice(ctx, "decoy_mode", _DECOY_MODES, int(sample_index))
    layout = _scheduled_choice(ctx, "layout", _LAYOUTS, int(sample_index))

    strict_profile = decoy_mode == "none" and layout == "blue_above_red"
    candidates = _shape_pair_candidates(
        blue_cells,
        red_cells,
        strict_profile=strict_profile,
        relation_slot=int(sample_index) % 3,
    )
    shape_rng = ctx.draw_rng("shape_pair")
    blue_shape, red_shape = shape_rng.choice(candidates)
    grid = _place_scene(
        h=h,
        w=w,
        blue=blue_shape,
        red=red_shape,
        layout=layout,
        decoy_mode=decoy_mode,
        distractor_color=int(distractor_color),
        rng=ctx.draw_rng("layout_geometry"),
    )
    errors = self_check(grid, difficulty=band)
    if errors:
        raise AssertionError("generated invalid normalized-XOR lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    for label, value in ctx.recorded_draws().items():
        if label in AXES and observed.get(label) != value:
            raise AssertionError(
                f"axis {label!r}: requested/drawn {value!r}, observed {observed.get(label)!r}"
            )
    return grid


def _grid_from_mask(mask: Iterable[tuple[int, int]], *, dims: tuple[int, int] | None = None) -> list[list[int]]:
    mask = _normalize(mask)
    if not mask:
        return [[0]]
    if dims is None:
        h, w = _bbox_dims(mask)
    else:
        h, w = dims
    out = full_grid(h, w, 0)
    for r, c in mask:
        if 0 <= r < h and 0 <= c < w:
            out[r][c] = 8
    return out


def _truth_xor(grid) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [[0]]
    return _grid_from_mask(analysis["xor"])


def _normalized_union(grid) -> list[list[int]]:
    analysis = _analysis(grid)
    return _grid_from_mask(analysis.get("blue_shape", set()) | analysis.get("red_shape", set()))


def _normalized_intersection(grid) -> list[list[int]]:
    analysis = _analysis(grid)
    return _grid_from_mask(analysis.get("shared", set()))


def _blue_only(grid) -> list[list[int]]:
    return _grid_from_mask(_analysis(grid).get("blue_shape", set()))


def _red_only(grid) -> list[list[int]]:
    return _grid_from_mask(_analysis(grid).get("red_shape", set()))


def _smallest_blue_xor(grid) -> list[list[int]]:
    analysis = _analysis(grid)
    components = analysis.get("blue_components", [])
    blue = _normalize(components[-1]) if components else frozenset()
    return _grid_from_mask(blue ^ analysis.get("red_shape", frozenset()))


def _smallest_red_xor(grid) -> list[list[int]]:
    analysis = _analysis(grid)
    components = analysis.get("red_components", [])
    red = _normalize(components[-1]) if components else frozenset()
    return _grid_from_mask(analysis.get("blue_shape", frozenset()) ^ red)


def _spatial_xor(grid) -> list[list[int]]:
    analysis = _analysis(grid)
    return _grid_from_mask(analysis.get("blue_main", set()) ^ analysis.get("red_main", set()))


def _uncropped_three_by_three(grid) -> list[list[int]]:
    return _grid_from_mask(_analysis(grid).get("xor", set()), dims=(3, 3))


def _distractor_participates(grid) -> list[list[int]]:
    analysis = _analysis(grid)
    return _grid_from_mask(set(analysis.get("xor", set())) ^ {(0, 0)})


SEMANTIC_RIVALS = {
    "normalized_union": _normalized_union,
    "normalized_intersection": _normalized_intersection,
    "blue_only": _blue_only,
    "red_only": _red_only,
    "smallest_blue_xor": _smallest_blue_xor,
    "smallest_red_xor": _smallest_red_xor,
    "spatial_xor_without_normalization": _spatial_xor,
    "fixed_3x3_output": _uncropped_three_by_three,
    "distractor_participates": _distractor_participates,
}

CANONICAL_SHORTCUTS = {
    "normalized_union": _normalized_union,
    "normalized_intersection": _normalized_intersection,
    "blue_only": _blue_only,
    "red_only": _red_only,
    "spatial_xor_without_normalization": _spatial_xor,
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _valid_witness(grid, predicate) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and bool(predicate(analysis))


SEMANTIC_WITNESSES = {
    "shared_cells_cancel": lambda grid: _valid_witness(grid, lambda a: bool(a["shared"])),
    "both_sources_contribute": lambda grid: _valid_witness(
        grid,
        lambda a: bool(a["blue_only"] and a["red_only"])
        and _normalized_intersection(grid) != _truth_xor(grid),
    ),
    "normalization_ignores_positions": lambda grid: _valid_witness(
        grid, lambda a: _spatial_xor(grid) != _truth_xor(grid)
    ),
    "largest_blue_selected": lambda grid: _valid_witness(
        grid,
        lambda a: a["decoy_mode"] in {"blue", "both"}
        and _smallest_blue_xor(grid) != _truth_xor(grid),
    ),
    "largest_red_selected": lambda grid: _valid_witness(
        grid,
        lambda a: a["decoy_mode"] in {"red", "both"}
        and _smallest_red_xor(grid) != _truth_xor(grid),
    ),
    "tight_crop": lambda grid: _valid_witness(
        grid,
        lambda a: a["xor_dims"] != (3, 3)
        and _uncropped_three_by_three(grid) != _truth_xor(grid),
    ),
    "unrelated_color_ignored": lambda grid: _valid_witness(
        grid, lambda a: _distractor_participates(grid) != _truth_xor(grid)
    ),
    "strict_empirical_profile": lambda grid: strict_canonical_like(grid) == [],
}

WITNESS_RIVALS = {
    "shared_cells_cancel": ["normalized_union"],
    "both_sources_contribute": ["normalized_intersection"],
    "normalization_ignores_positions": ["spatial_xor_without_normalization"],
    "largest_blue_selected": ["smallest_blue_xor"],
    "largest_red_selected": ["smallest_red_xor"],
    "tight_crop": ["fixed_3x3_output"],
    "unrelated_color_ignored": ["distractor_participates"],
    "strict_empirical_profile": ["normalized_union", "normalized_intersection"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require each three-demo lesson to falsify the main rival rules."""
    reasons: list[str] = []
    if len(demos) < 3:
        return ["need at least three demonstrations"]

    analyses = []
    for index, pair in enumerate(demos):
        inp = pair.get("input")
        out = pair.get("output")
        analysis = _analysis(inp)
        if analysis["errors"]:
            reasons.append(f"demo {index} input outside teaching grammar")
            continue
        if out != _truth_xor(inp):
            reasons.append(f"demo {index} output is not the normalized tight XOR")
        if not analysis["shared"]:
            reasons.append(f"demo {index} does not refute normalized union")
        if not analysis["blue_only"] or not analysis["red_only"]:
            reasons.append(f"demo {index} does not refute normalized intersection")
        if _spatial_xor(inp) == out:
            reasons.append(f"demo {index} does not make normalization answer-bearing")
        analyses.append(analysis)

    if not any(a["decoy_mode"] in {"blue", "both"} for a in analyses):
        reasons.append("no demonstration proves largest-blue selection")
    if not any(a["decoy_mode"] in {"red", "both"} for a in analyses):
        reasons.append("no demonstration proves largest-red selection")
    layouts = {a["layout"] for a in analyses}
    if layouts != set(_LAYOUTS):
        reasons.append(f"three-demo schedule did not cover all spatial layouts: {sorted(layouts)}")
    if not any(a["xor_dims"] != (3, 3) for a in analyses):
        reasons.append("no demonstration makes tight cropping visible")

    query_analysis = _analysis(query.get("input"))
    if query_analysis["errors"]:
        reasons.append("query input outside teaching grammar")
    return reasons
