"""High-integrity generator for ``transform_the_object_according_to_the_key_color``.

The input contains exactly one isolated key cell in colors 1..4 and a separate
colored shape in colors 5..9.  Remove the key, crop every remaining non-zero
cell as one composite canvas, then apply the key-selected transform:

* 1 -> rotate 90 degrees clockwise
* 2 -> rotate 180 degrees
* 3 -> flip left/right
* 4 -> transpose

Four consecutive examples schedule all four keys.  A five-slot shape schedule
also guarantees multicolor and disconnected-composite demonstrations, so the
lesson cannot be solved by a fixed transform, largest-component extraction,
modal-color echo, or key-position proxy.
"""
from __future__ import annotations

from collections import Counter, deque
from itertools import permutations
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4b693000db29"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "3ae7680c3158"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.15

SUMMARY = (
    "Exactly one isolated key cell selects a transform: 1=rotate clockwise, "
    "2=rotate 180, 3=flip left/right, 4=transpose. Remove the key, tightly "
    "crop all remaining non-zero cells as one possibly multicolor and "
    "disconnected composite shape, then transform that cropped canvas."
)

INVARIANTS = [
    "the square input is 5..9 cells on a side",
    "exactly one isolated key cell has color 1, 2, 3, or 4",
    "all shape cells use 1..3 colors chosen from 5..9",
    "the key lies outside the shape bounding box with at least one blank row or column of separation",
    "the cropped shape contains 4..10 cells and at least one internal background cell",
    "the selected transform changes the cropped shape rather than hiding behind symmetry",
    "four consecutive sample indices cover all four key-to-transform branches",
    "every five consecutive sample indices include a multicolor disconnected composite shape",
]

AXES = {
    "grid_size": {
        "type": "int",
        "default": "difficulty-aware 5..9 with canonical 5/6 anchors",
        "valid": "5..9",
    },
    "shape_cells": {
        "type": "int",
        "default": "five-slot schedule 4,6,5,4,6",
        "valid": "4..10",
    },
    "shape_colors": {
        "type": "int",
        "default": "five-slot schedule 1,2,1,1,3",
        "valid": "1..3",
    },
    "key": {
        "type": "int",
        "default": "sample_index modulo four + 1",
        "valid": "1..4",
    },
}

_SHAPE_CELL_SCHEDULE = (4, 6, 5, 4, 6)
_SHAPE_COLOR_SCHEDULE = (1, 2, 1, 1, 3)
_CANONICAL_SIZE_SCHEDULE = (5, 6, 5, 6, None)
_SIDE_SCHEDULE = ("top", "right", "bottom", "left", "right")


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid[::-1]]


def _flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid]


def _transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)]


_TRANSFORMS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "rotate_cw": _rotate_cw,
    "rotate_180": _rotate_180,
    "flip_lr": _flip_lr,
    "transpose": _transpose,
}
_INTENDED_MAPPING = {
    1: "rotate_cw",
    2: "rotate_180",
    3: "flip_lr",
    4: "transpose",
}


def _transform(shape: list[list[int]], key: int) -> list[list[int]]:
    return _TRANSFORMS[_INTENDED_MAPPING[key]](shape)


def _serialize(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _component_sets(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        components.append(component)
    components.sort(key=lambda comp: (-len(comp), min(comp)))
    return components


def _normalize_cells(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return {(r - r0, c - c0) for r, c in cells}


def _matrix_from_cells(
    cells: set[tuple[int, int]],
    palette: tuple[int, ...],
    rng,
) -> list[list[int]]:
    cells = _normalize_cells(cells)
    h = max(r for r, _ in cells) + 1
    w = max(c for _, c in cells) + 1
    grid = full_grid(h, w, 0)
    ordered = sorted(cells)
    rng.shuffle(ordered)
    assignments = list(palette)
    assignments.extend(rng.choice(palette) for _ in range(len(ordered) - len(palette)))
    rng.shuffle(assignments)
    for (r, c), color in zip(ordered, assignments):
        grid[r][c] = color
    return grid


def _all_selected_transforms_distinct(shape: list[list[int]]) -> bool:
    variants = [
        shape,
        _rotate_cw(shape),
        _rotate_180(shape),
        _flip_lr(shape),
        _transpose(shape),
    ]
    return len({_serialize(item) for item in variants}) == len(variants)


def _build_shape(
    *,
    rng,
    n: int,
    cell_count: int,
    palette: tuple[int, ...],
    disconnected: bool,
) -> list[list[int]]:
    """Search a small finite canvas for an asymmetric lawful composite."""
    max_dim = n - 2
    for _ in range(4000):
        h = rng.randint(2, max_dim)
        w = rng.randint(2, max_dim)
        if h * w < cell_count + 1:
            continue
        coords = [(r, c) for r in range(h) for c in range(w)]
        cells = set(rng.sample(coords, cell_count))
        cells = _normalize_cells(cells)
        sh = max(r for r, _ in cells) + 1
        sw = max(c for _, c in cells) + 1
        if sh < 2 or sw < 2 or sh > max_dim or sw > max_dim:
            continue
        if sh * sw == cell_count:
            continue
        components = _component_sets(cells)
        if disconnected:
            if len(components) < 2 or len(components[0]) < 2:
                continue
        elif len(components) != 1:
            continue
        shape = _matrix_from_cells(cells, palette, rng)
        if len({v for row in shape for v in row if v}) != len(palette):
            continue
        if not _all_selected_transforms_distinct(shape):
            continue
        return shape
    raise RuntimeError(
        "could not construct an asymmetric shape for "
        f"n={n}, cells={cell_count}, colors={len(palette)}, "
        f"disconnected={disconnected}"
    )


def _minimum_grid_size(cell_count: int) -> int:
    for n in range(5, 10):
        if (n - 2) * (n - 2) >= cell_count + 1:
            return n
    raise ValueError(f"shape_cells={cell_count} cannot fit in a 9x9 teaching grid")


def _place_shape_and_key(
    *,
    n: int,
    shape: list[list[int]],
    key: int,
    side: str,
    rng,
) -> list[list[int]]:
    sh, sw = len(shape), len(shape[0])
    grid = full_grid(n, n, 0)

    if side == "top":
        r0 = rng.randint(2, n - sh)
        c0 = rng.randint(0, n - sw)
        kr = rng.randint(0, r0 - 2)
        kc = rng.randint(c0, c0 + sw - 1)
    elif side == "bottom":
        r0 = rng.randint(0, n - sh - 2)
        c0 = rng.randint(0, n - sw)
        kr = rng.randint(r0 + sh + 1, n - 1)
        kc = rng.randint(c0, c0 + sw - 1)
    elif side == "left":
        r0 = rng.randint(0, n - sh)
        c0 = rng.randint(2, n - sw)
        kr = rng.randint(r0, r0 + sh - 1)
        kc = rng.randint(0, c0 - 2)
    elif side == "right":
        r0 = rng.randint(0, n - sh)
        c0 = rng.randint(0, n - sw - 2)
        kr = rng.randint(r0, r0 + sh - 1)
        kc = rng.randint(c0 + sw + 1, n - 1)
    else:  # pragma: no cover - internal schedule is closed
        raise ValueError(f"unknown key side {side!r}")

    for r, row in enumerate(shape):
        for c, value in enumerate(row):
            if value:
                grid[r0 + r][c0 + c] = value
    grid[kr][kc] = key
    return grid


def _shape_bbox(
    grid: list[list[int]],
) -> tuple[int, int, int, int, list[tuple[int, int, int]]] | None:
    cells = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in (5, 6, 7, 8, 9)
    ]
    if not cells:
        return None
    return (
        min(r for r, _, _ in cells),
        min(c for _, c, _ in cells),
        max(r for r, _, _ in cells),
        max(c for _, c, _ in cells),
        cells,
    )


def _extract_shape(grid: list[list[int]]) -> tuple[int, list[list[int]]]:
    keys = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in (1, 2, 3, 4)
    ]
    if len(keys) != 1:
        raise ValueError(f"expected exactly one key, found {len(keys)}")
    bbox = _shape_bbox(grid)
    if bbox is None:
        raise ValueError("shape is absent")
    r0, c0, r1, c1, _ = bbox
    shape = [
        [grid[r][c] if grid[r][c] in (5, 6, 7, 8, 9) else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]
    return keys[0][2], shape


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for tests; Racket remains output authority."""
    key, shape = _extract_shape(grid)
    return _transform(shape, key)


def _analysis(grid) -> dict:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid must be a non-empty list of rows"]}
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular and non-empty"]}
    height = len(grid)
    if height != width or not 5 <= height <= 9:
        errors.append(f"expected a square 5..9 grid, got {height}x{width}")
    invalid = [
        value
        for row in grid
        for value in row
        if not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
    ]
    if invalid:
        errors.append("grid contains non-ARC colors")
        return {"errors": errors}

    keys = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in (1, 2, 3, 4)
    ]
    if len(keys) != 1:
        errors.append(f"expected exactly one transform key, found {len(keys)}")

    bbox = _shape_bbox(grid)
    shape: list[list[int]] | None = None
    shape_cells: list[tuple[int, int, int]] = []
    shape_colors: set[int] = set()
    components: list[set[tuple[int, int]]] = []
    if bbox is None:
        errors.append("expected a shape in colors 5..9")
        r0 = c0 = r1 = c1 = -1
    else:
        r0, c0, r1, c1, shape_cells = bbox
        shape_colors = {value for _, _, value in shape_cells}
        if not 4 <= len(shape_cells) <= 10:
            errors.append(f"shape has {len(shape_cells)} cells; expected 4..10")
        if not 1 <= len(shape_colors) <= 3:
            errors.append(f"shape uses {len(shape_colors)} colors; expected 1..3")
        if r1 == r0 or c1 == c0:
            errors.append("shape bounding box must span at least two rows and columns")
        shape = [
            [
                grid[r][c] if grid[r][c] in (5, 6, 7, 8, 9) else 0
                for c in range(c0, c1 + 1)
            ]
            for r in range(r0, r1 + 1)
        ]
        if all(value != 0 for row in shape for value in row):
            errors.append("shape fills its bounding box and hides the crop boundary")
        components = _component_sets({(r, c) for r, c, _ in shape_cells})

    key_side = None
    if len(keys) == 1 and bbox is not None:
        kr, kc, key = keys[0]
        if r0 <= kr <= r1 and c0 <= kc <= c1:
            errors.append("key lies inside the shape bounding box")
        if any(max(abs(kr - r), abs(kc - c)) <= 1 for r, c, _ in shape_cells):
            errors.append("key is not isolated from the shape by a blank gap")
        if kr < r0:
            key_side = "top"
        elif kr > r1:
            key_side = "bottom"
        elif kc < c0:
            key_side = "left"
        elif kc > c1:
            key_side = "right"
        else:
            key_side = "inside"
        if shape is not None and _transform(shape, key) == shape:
            errors.append("selected transform leaves the cropped shape unchanged")

    return {
        "errors": errors,
        "grid_size": height,
        "keys": keys,
        "key": keys[0][2] if len(keys) == 1 else None,
        "key_side": key_side,
        "shape": shape,
        "shape_cells": len(shape_cells),
        "shape_colors": len(shape_colors),
        "components": components,
        "component_count": len(components),
        "bbox": (r0, c0, r1, c1) if bbox is not None else None,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or shortcut-hiding teaching inputs."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from the returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_size": analysis["grid_size"],
        "shape_cells": analysis["shape_cells"],
        "shape_colors": analysis["shape_colors"],
        "key": analysis["key"],
    }


def strict_canonical_like(grid) -> list[str]:
    """Tight canonical-profile predicate, not merely a generic valid-grid check."""
    analysis = _analysis(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    if analysis["grid_size"] not in (5, 6):
        reasons.append("canonical grids are 5x5 or 6x6")
    if not 4 <= analysis["shape_cells"] <= 6:
        reasons.append("canonical shapes contain 4..6 cells")
    if not 1 <= analysis["shape_colors"] <= 2:
        reasons.append("canonical shapes use one or two colors")
    if analysis["key_side"] != "top":
        reasons.append("canonical keys are above the shape")
    return reasons


def _valid_analysis(grid) -> dict | None:
    analysis = _analysis(grid)
    return None if analysis["errors"] else analysis


def _witness_key(value: int):
    return lambda grid: bool((a := _valid_analysis(grid)) and a["key"] == value)


def _witness_multicolor(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and analysis["shape_colors"] >= 2)


def _witness_disconnected(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and analysis["component_count"] >= 2)


def _witness_non_top_key(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and analysis["key_side"] in {"left", "right", "bottom"})


def _witness_full_transform_separation(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and _all_selected_transforms_distinct(analysis["shape"]))


SEMANTIC_WITNESSES = {
    "key_1_rotate_clockwise": _witness_key(1),
    "key_2_rotate_180": _witness_key(2),
    "key_3_flip_left_right": _witness_key(3),
    "key_4_transpose": _witness_key(4),
    "multicolor_shape": _witness_multicolor,
    "disconnected_composite_shape": _witness_disconnected,
    "non_top_key_position": _witness_non_top_key,
    "all_transform_answers_distinct": _witness_full_transform_separation,
}


def _apply_mapping(grid, mapping: dict[int, str]) -> list[list[int]] | None:
    try:
        key, shape = _extract_shape(grid)
    except ValueError:
        return None
    return _TRANSFORMS[mapping[key]](shape)


def _largest_component_answer(grid) -> list[list[int]] | None:
    analysis = _valid_analysis(grid)
    if not analysis:
        return None
    component = analysis["components"][0]
    r0 = min(r for r, _ in component)
    c0 = min(c for _, c in component)
    r1 = max(r for r, _ in component)
    c1 = max(c for _, c in component)
    shape = [
        [grid[r][c] if (r, c) in component else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]
    return _transform(shape, analysis["key"])


def _modal_color_answer(grid) -> list[list[int]] | None:
    analysis = _valid_analysis(grid)
    if not analysis:
        return None
    counts = Counter(value for row in analysis["shape"] for value in row if value)
    if not counts:
        return None
    top = max(counts.values())
    modal = min(color for color, count in counts.items() if count == top)
    cells = [
        (r, c)
        for r, row in enumerate(analysis["shape"])
        for c, value in enumerate(row)
        if value == modal
    ]
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    r1 = max(r for r, _ in cells)
    c1 = max(c for _, c in cells)
    shape = [
        [
            analysis["shape"][r][c] if analysis["shape"][r][c] == modal else 0
            for c in range(c0, c1 + 1)
        ]
        for r in range(r0, r1 + 1)
    ]
    return _transform(shape, analysis["key"])


def lesson_identifiable(demos, query) -> list[str]:
    """Require demos to refute plausible rival rules before accepting a lesson."""
    reasons: list[str] = []
    if len(demos) < 4:
        return ["need four demonstrations to cover all key mappings"]

    demo_analyses: list[dict] = []
    for index, pair in enumerate(demos):
        inp = pair.get("input")
        out = pair.get("output")
        analysis = _analysis(inp)
        if analysis["errors"]:
            reasons.append(f"demo {index} input is outside teaching grammar")
            continue
        if rule_mirror(inp) != out:
            reasons.append(f"demo {index} output disagrees with the keyed transform")
        demo_analyses.append(analysis)

    query_input = query.get("input")
    query_output = query.get("output")
    query_analysis = _analysis(query_input)
    if query_analysis["errors"]:
        reasons.append("query input is outside teaching grammar")
    elif rule_mirror(query_input) != query_output:
        reasons.append("query output disagrees with the keyed transform")

    if {analysis["key"] for analysis in demo_analyses} != {1, 2, 3, 4}:
        reasons.append("demonstrations do not cover all four key colors")
    if not any(analysis["shape_colors"] >= 2 for analysis in demo_analyses):
        reasons.append("no demonstration rebuts a modal-color-only shortcut")
    if not any(analysis["component_count"] >= 2 for analysis in demo_analyses):
        reasons.append("no demonstration rebuts largest-component-only extraction")
    if len({analysis["key_side"] for analysis in demo_analyses}) < 3:
        reasons.append("key placement varies too little to rebut a position proxy")
    if not query_analysis["errors"]:
        same_key_sides = {
            analysis["key_side"]
            for analysis in demo_analyses
            if analysis["key"] == query_analysis["key"]
        }
        if same_key_sides and query_analysis["key_side"] in same_key_sides:
            reasons.append("query repeats the same key-position pairing as its matching demo")

    operation_names = tuple(_TRANSFORMS)
    consistent_mappings: list[dict[int, str]] = []
    for order in permutations(operation_names):
        mapping = dict(zip((1, 2, 3, 4), order))
        if all(_apply_mapping(pair["input"], mapping) == pair["output"] for pair in demos):
            consistent_mappings.append(mapping)
    if not consistent_mappings:
        reasons.append("no bijective key-to-transform mapping fits every demonstration")
    elif not query_analysis["errors"]:
        candidate_answers = {
            _serialize(_apply_mapping(query_input, mapping))
            for mapping in consistent_mappings
        }
        if len(candidate_answers) > 1:
            reasons.append(
                f"{len(consistent_mappings)} key mappings fit demos but disagree on query"
            )

    fixed_competitors = {
        f"fixed {name}": {key: name for key in (1, 2, 3, 4)}
        for name in operation_names
    }
    for name, mapping in fixed_competitors.items():
        if all(_apply_mapping(pair["input"], mapping) == pair["output"] for pair in demos):
            if _apply_mapping(query_input, mapping) != query_output:
                reasons.append(f"competitor remains plausible: {name}")

    competitor_functions = {
        "largest connected component only": _largest_component_answer,
        "modal shape color only": _modal_color_answer,
    }
    for name, fn in competitor_functions.items():
        if all(fn(pair["input"]) == pair["output"] for pair in demos):
            if fn(query_input) != query_output:
                reasons.append(f"competitor remains plausible: {name}")

    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")

    slot = int(sample_index) % 5
    effective = dict(overrides)
    effective.setdefault("key", int(sample_index) % 4 + 1)
    effective.setdefault("shape_cells", _SHAPE_CELL_SCHEDULE[slot])
    effective.setdefault("shape_colors", _SHAPE_COLOR_SCHEDULE[slot])

    requested_cells = int(effective["shape_cells"])
    min_grid = _minimum_grid_size(requested_cells)
    if "grid_size" not in effective:
        scheduled_size = _CANONICAL_SIZE_SCHEDULE[slot]
        if scheduled_size is not None:
            effective["grid_size"] = max(scheduled_size, min_grid)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    shape_cells = ctx.draw_int("shape_cells", 4, 10)
    shape_colors = ctx.draw_int("shape_colors", 1, 3)
    if shape_colors > shape_cells:
        raise ValueError("shape_colors cannot exceed shape_cells")
    min_grid = _minimum_grid_size(shape_cells)
    grid_size = ctx.draw_int_diff("grid_size", min_grid, 9)
    key = ctx.draw_int("key", 1, 4)
    palette = ctx.draw_distinct_colors(
        "shape_palette", n=shape_colors, exclude={0, 1, 2, 3, 4}
    )
    rng = ctx.draw_rng("layout")
    disconnected = slot in (1, 4)
    if grid_size == 5 and shape_cells > 6:
        disconnected = False
    shape = _build_shape(
        rng=rng,
        n=grid_size,
        cell_count=shape_cells,
        palette=palette,
        disconnected=disconnected,
    )
    grid = _place_shape_and_key(
        n=grid_size,
        shape=shape,
        key=key,
        side=_SIDE_SCHEDULE[slot],
        rng=rng,
    )
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generated invalid keyed-transform lesson: " + "; ".join(errors))
    return grid
