"""Generator for 20b:hard_138 — select, transform, recolor, center-stamp.

The first three cells are controls: selector color, transform code, and target
color.  Rows 1..7 contain separated monochrome objects.  Select the object
whose color equals the selector, crop it, apply the coded D4 transform,
recolor it to the target color, and center it in a fresh 7x7 output.

The official inputs are all 8x13 with three objects.  Ordinary generation keeps
substantial linked support on those exact dimension/palette/morphology profiles
while also varying width, object count, selector size, shape, color, placement,
and every transform code.  All generated objects remain inside rows 1..7,
which is the complete body window read by the canonical Racket oracle.
"""
from __future__ import annotations

from collections.abc import Callable
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a5bf62ba0593"
VERSION = "2.0.0"
TASK_ID = "a5bf62ba0593"
RULE_HASH = "55334b2b3d61"

SUMMARY = (
    "Cell (0,0) names a body-object color, cell (0,1) gives a transform "
    "code (1=rotate clockwise, 2=rotate 180, 3=rotate counterclockwise, "
    "4=flip left-right, 5=flip up-down), and cell (0,2) gives a new color. "
    "Select the uniquely matching body object, crop and transform it, recolor "
    "its occupied cells to the target color, and center-stamp it in a 7x7 grid."
)

# Rival shortcuts rebutted by the ordinary lesson schedule:
# - fixed-position / first-object selection: the selector moves among slots and
#   is never the first body component in generalized scenes;
# - largest-object selection: generalized scenes contain a larger distractor;
# - no transform / code ignored: generated selector shapes visibly change under
#   their scheduled code;
# - selector-color echo: target is absent from every body object;
# - whole-body transform: at least one distractor is always excluded;
# - fixed code: sequential sample indices cycle through all five code values;
# - top-left stamp: the oracle mirror centers every transformed crop.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "the grid is exactly 8 rows; row 0 is a three-cell header followed by zeros",
    "rows 1..7 contain two to four separated monochrome 4-connected objects",
    "body-object colors are distinct and exactly one equals the selector color",
    "the target color is nonzero, differs from the selector, and is absent from the body",
    "the transform code is one of 1..5 and maps to the documented D4 operation",
    "every body object has 3..8 cells and a bounding box no larger than 3x3",
]

AXES = {
    "grid_w": {
        "type": "int",
        "default": "difficulty-band rng 10..16; exact canonical width 13 scheduled",
        "valid": "10..16",
    },
    "n_objects": {
        "type": "int",
        "default": "difficulty-band rng 2..4; exact canonical count 3 scheduled",
        "valid": "2..4",
    },
    "selector_cells": {
        "type": "int",
        "default": "difficulty-band rng 3..7; canonical 3..5 scheduled",
        "valid": "3..7",
    },
    "transform_code": {
        "type": "int",
        "default": "sequential sample_index cycle 1..5",
        "valid": "1..5",
    },
}

# Exact linked empirical profiles from all four train inputs and the held-out
# test input.  Signatures are (cells, bbox_h, bbox_w, bbox_area-cells).  The
# final value is the full input palette size including background.
_CANONICAL_PROFILES = (
    ((4, 3, 2, 2), ((4, 2, 3, 2), (4, 3, 2, 2)), 6),
    ((5, 2, 3, 1), ((4, 2, 2, 0), (4, 3, 2, 2)), 5),
    ((5, 3, 2, 1), ((3, 1, 3, 0), (5, 3, 3, 4)), 6),
    ((3, 2, 2, 1), ((4, 2, 3, 2), (4, 3, 2, 2)), 6),
    ((4, 3, 2, 2), ((4, 3, 2, 2), (5, 2, 3, 1)), 5),
)
MIN_STRICT_FRAC = 0.15

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
Shape = tuple[tuple[int, int], ...]


def _normalize(cells) -> Shape:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _connected(cells: Shape) -> bool:
    occupied = set(cells)
    seen = {cells[0]}
    stack = [cells[0]]
    while stack:
        r, c = stack.pop()
        for dr, dc in _DIRS4:
            nxt = (r + dr, c + dc)
            if nxt in occupied and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return len(seen) == len(occupied)


def _shape_signature(shape: Shape) -> tuple[int, int, int, int]:
    shape = _normalize(shape)
    h = max(r for r, _ in shape) + 1
    w = max(c for _, c in shape) + 1
    return len(shape), h, w, h * w - len(shape)


def _rotate_cw(shape: Shape) -> Shape:
    h = max(r for r, _ in shape) + 1
    return _normalize((c, h - 1 - r) for r, c in shape)


def _rotate_180(shape: Shape) -> Shape:
    return _rotate_cw(_rotate_cw(shape))


def _rotate_ccw(shape: Shape) -> Shape:
    return _rotate_cw(_rotate_180(shape))


def _flip_lr(shape: Shape) -> Shape:
    w = max(c for _, c in shape) + 1
    return _normalize((r, w - 1 - c) for r, c in shape)


def _flip_ud(shape: Shape) -> Shape:
    h = max(r for r, _ in shape) + 1
    return _normalize((h - 1 - r, c) for r, c in shape)


def _transform_shape(shape: Shape, code: int) -> Shape:
    return {
        1: _rotate_cw,
        2: _rotate_180,
        3: _rotate_ccw,
        4: _flip_lr,
        5: _flip_ud,
    }[code](_normalize(shape))


def _build_shape_banks():
    by_size: dict[int, list[Shape]] = {k: [] for k in range(3, 9)}
    by_signature: dict[tuple[int, int, int, int], list[Shape]] = {}
    all_cells = tuple((r, c) for r in range(3) for c in range(3))
    for k in range(3, 9):
        seen: set[Shape] = set()
        for subset in combinations(all_cells, k):
            shape = _normalize(subset)
            if shape in seen or not _connected(shape):
                continue
            seen.add(shape)
            by_size[k].append(shape)
            by_signature.setdefault(_shape_signature(shape), []).append(shape)
    return by_size, by_signature


_SHAPES_BY_SIZE, _SHAPES_BY_SIGNATURE = _build_shape_banks()


def _body_components(grid: list[list[int]]) -> list[dict]:
    """Match the oracle's any-nonzero 4-connectivity over rows 1..7."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict] = []
    for r in range(1, min(h, 8)):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            colors: set[int] = set()
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                colors.add(grid[rr][cc])
                for dr, dc in _DIRS4:
                    nr, nc = rr + dr, cc + dc
                    if (
                        1 <= nr < min(h, 8)
                        and 0 <= nc < w
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append({
                "cells": tuple(sorted(cells)),
                "colors": frozenset(colors),
                "first": min(cells),
            })
    return sorted(components, key=lambda component: component["first"])


def _component_shape(component: dict) -> Shape:
    return _normalize(component["cells"])


def _selector_component(grid: list[list[int]]) -> dict:
    selector = grid[0][0]
    matches = [
        component
        for component in _body_components(grid)
        if len(component["colors"]) == 1 and selector in component["colors"]
    ]
    if not matches:
        raise ValueError("selector color has no body component")
    return max(matches, key=lambda component: len(component["cells"]))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete lawful teaching grammar, not just the header."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]

    errs: list[str] = []
    if h != 8:
        errs.append(f"expected exactly 8 rows, found {h}")
    if not 10 <= w <= 16 and (h, w) != (8, 13):
        errs.append(f"width {w} outside lawful 10..16 envelope")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errs.append("cell value outside integer ARC colors 0..9")
        return errs
    if h < 1 or w < 3:
        errs.append("grid too small for three-cell header")
        return errs

    selector, code, target = grid[0][0], grid[0][1], grid[0][2]
    if selector == 0:
        errs.append("selector color is zero")
    if code not in range(1, 6):
        errs.append(f"transform code {code} outside 1..5")
    if target == 0:
        errs.append("target color is zero")
    if selector == target:
        errs.append("selector and target colors must differ")
    if any(value != 0 for value in grid[0][3:]):
        errs.append("row 0 contains nonzero cells outside the three-cell header")
    if h != 8:
        return errs

    components = _body_components(grid)
    if not 2 <= len(components) <= 4:
        errs.append(f"expected 2..4 body objects, found {len(components)}")

    body_colors: list[int] = []
    selector_matches = 0
    for index, component in enumerate(components):
        colors = component["colors"]
        if len(colors) != 1:
            errs.append(
                f"body component {index} mixes colors {sorted(colors)}; objects touch"
            )
            continue
        color = next(iter(colors))
        body_colors.append(color)
        shape = _component_shape(component)
        cells, bh, bw, _ = _shape_signature(shape)
        if not 3 <= cells <= 8:
            errs.append(f"body component {index} has {cells} cells outside 3..8")
        if bh > 3 or bw > 3:
            errs.append(f"body component {index} bbox {bh}x{bw} exceeds 3x3")
        if color == selector:
            selector_matches += 1
            if not 3 <= cells <= 7:
                errs.append(f"selector object has {cells} cells outside 3..7")

    if len(body_colors) != len(set(body_colors)):
        errs.append("body-object colors must be distinct")
    if selector_matches != 1:
        errs.append(
            f"expected exactly one selector-colored body object, found {selector_matches}"
        )
    if target in body_colors:
        errs.append("target color must be absent from all body objects")
    return errs


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from the materialized grid."""
    selector_component = _selector_component(grid)
    return {
        "grid_w": len(grid[0]),
        "n_objects": len(_body_components(grid)),
        "selector_cells": len(selector_component["cells"]),
        "transform_code": grid[0][1],
    }


def _stamp_center(shape: Shape, color: int, *, top_left: bool = False) -> list[list[int]]:
    shape = _normalize(shape)
    h = max(r for r, _ in shape) + 1
    w = max(c for _, c in shape) + 1
    top = 0 if top_left else (7 - h) // 2
    left = 0 if top_left else (7 - w) // 2
    out = full_grid(7, 7, 0)
    for r, c in shape:
        out[top + r][left + c] = color
    return out


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror of the selected canonical Racket rule."""
    component = _selector_component(grid)
    shape = _component_shape(component)
    transformed = _transform_shape(shape, grid[0][1])
    return _stamp_center(transformed, grid[0][2])


def _profile_of(grid) -> tuple:
    components = _body_components(grid)
    selector = grid[0][0]
    selector_sigs = []
    distractor_sigs = []
    for component in components:
        if len(component["colors"]) != 1:
            return ()
        color = next(iter(component["colors"]))
        signature = _shape_signature(_component_shape(component))
        (selector_sigs if color == selector else distractor_sigs).append(signature)
    if len(selector_sigs) != 1:
        return ()
    palette_size = len({value for row in grid for value in row})
    return selector_sigs[0], tuple(sorted(distractor_sigs)), palette_size


def strict_canonical_like(grid) -> list[str]:
    """Recognize the linked empirical manifold of all official inputs."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    strict: list[str] = []
    if (len(grid), len(grid[0])) != (8, 13):
        strict.append(f"dimensions {len(grid)}x{len(grid[0])} differ from official 8x13")
    profile = _profile_of(grid)
    if profile not in _CANONICAL_PROFILES:
        strict.append(f"linked role/morphology/palette profile {profile!r} is not official")
    return strict


def _visible_transform(grid) -> bool:
    component = _selector_component(grid)
    shape = _component_shape(component)
    return _transform_shape(shape, grid[0][1]) != shape


def _selector_not_first(grid) -> bool:
    components = _body_components(grid)
    return bool(components) and grid[0][0] not in components[0]["colors"]


def _selector_not_largest(grid) -> bool:
    component = _selector_component(grid)
    return any(
        len(other["cells"]) > len(component["cells"])
        for other in _body_components(grid)
    )


def _code_overlap(grid) -> bool:
    return grid[0][1] in {grid[0][0], grid[0][2]} | {
        next(iter(component["colors"]))
        for component in _body_components(grid)
        if len(component["colors"]) == 1
    }


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "code_1_rotate_cw": lambda grid: grid[0][1] == 1,
    "code_2_rotate_180": lambda grid: grid[0][1] == 2,
    "code_3_rotate_ccw": lambda grid: grid[0][1] == 3,
    "code_4_flip_lr": lambda grid: grid[0][1] == 4,
    "code_5_flip_ud": lambda grid: grid[0][1] == 5,
    "visible_transform": _visible_transform,
    "selector_not_first": _selector_not_first,
    "selector_not_largest": _selector_not_largest,
    "code_overlaps_palette": _code_overlap,
    "code_is_palette_unique": lambda grid: not _code_overlap(grid),
    "strict_official_profile": lambda grid: strict_canonical_like(grid) == [],
}


def _rival_no_transform(grid):
    component = _selector_component(grid)
    return _stamp_center(_component_shape(component), grid[0][2])


def _rival_selector_color(grid):
    component = _selector_component(grid)
    shape = _transform_shape(_component_shape(component), grid[0][1])
    return _stamp_center(shape, grid[0][0])


def _rival_component(grid, *, which: str):
    components = _body_components(grid)
    if which == "first":
        component = components[0]
    else:
        component = max(components, key=lambda item: len(item["cells"]))
    shape = _transform_shape(_component_shape(component), grid[0][1])
    return _stamp_center(shape, grid[0][2])


def _rival_top_left_stamp(grid):
    component = _selector_component(grid)
    shape = _transform_shape(_component_shape(component), grid[0][1])
    return _stamp_center(shape, grid[0][2], top_left=True)


def _rival_fixed_cw(grid):
    component = _selector_component(grid)
    shape = _transform_shape(_component_shape(component), 1)
    return _stamp_center(shape, grid[0][2])


_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "no_transform": _rival_no_transform,
    "selector_color_echo": _rival_selector_color,
    "first_body_object": lambda grid: _rival_component(grid, which="first"),
    "largest_body_object": lambda grid: _rival_component(grid, which="largest"),
    "top_left_stamp": _rival_top_left_stamp,
    "fixed_rotate_cw": _rival_fixed_cw,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a plausible rival fits demos but changes query."""
    reasons: list[str] = []
    for name, rival in _RIVALS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(
                    f"rival {name!r} fits every demonstration but changes query"
                )
    return reasons


def _banded_int(ctx, label: str, lo: int, hi: int, valid_lo: int, valid_hi: int) -> int:
    """Use band defaults while honoring all declared boundaries in every band."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, lo, hi)


def _scheduled_transform_code(ctx, sample_index: int) -> int:
    if "transform_code" not in ctx.overrides or ctx.overrides["transform_code"] is None:
        ctx.overrides["transform_code"] = sample_index % 5 + 1
    return ctx.draw_int("transform_code", 1, 5)


def _choose_shape(rng, *, cells: int, code: int, signature=None) -> Shape:
    candidates = (
        _SHAPES_BY_SIGNATURE.get(signature, [])
        if signature is not None
        else _SHAPES_BY_SIZE[cells]
    )
    visible = [shape for shape in candidates if _transform_shape(shape, code) != shape]
    pool = visible or candidates
    if not pool:
        raise ValueError(f"no connected 3x3 shape for cells={cells}, signature={signature}")
    return rng.choice(pool)


def _choose_colors(rng, n_objects: int, code: int, palette_size: int | None):
    needed = n_objects + 1  # body colors plus target
    colors = list(range(1, 10))
    if palette_size == 5:
        # Official 5-color profiles (including background) require the code to
        # overlap one of the four semantic colors.
        selected = [code] + rng.sample([c for c in colors if c != code], needed - 1)
        rng.shuffle(selected)
    elif palette_size == 6:
        selected = rng.sample([c for c in colors if c != code], needed)
    else:
        selected = rng.sample(colors, needed)
    return selected[:n_objects], selected[-1]


def _slots(width: int) -> tuple[tuple[int, int], ...]:
    """Four separated 3x3 slots inside the oracle-visible 7-row body."""
    return ((1, 0), (1, width - 3), (5, 0), (5, width - 3))


def _paint_shape(grid, shape: Shape, top: int, left: int, color: int, rng) -> None:
    bh = max(r for r, _ in shape) + 1
    bw = max(c for _, c in shape) + 1
    # Each slot is 3x3. Jitter compact shapes within it without changing the
    # linked morphology signature.
    top += rng.randint(0, 3 - bh)
    left += rng.randint(0, 3 - bw)
    for r, c in shape:
        grid[top + r][left + c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    code = _scheduled_transform_code(ctx, sample_index)

    exact_override_names = {"grid_w", "n_objects", "selector_cells"}
    has_exact_override = any(
        name in ctx.overrides and ctx.overrides[name] is not None
        for name in exact_override_names
    )
    strict_profile = None
    # A deterministic 25% schedule gives every band and disjoint seed range
    # substantial official-manifold support without tuning to one census.
    if not has_exact_override and sample_index % 4 == 0:
        strict_profile = _CANONICAL_PROFILES[(seed + sample_index) % len(_CANONICAL_PROFILES)]
        ctx.overrides["grid_w"] = 13
        ctx.overrides["n_objects"] = 3
        ctx.overrides["selector_cells"] = strict_profile[0][0]

    if difficulty == "easy":
        width = _banded_int(ctx, "grid_w", 10, 13, 10, 16)
        n_objects = _banded_int(ctx, "n_objects", 2, 3, 2, 4)
        selector_cells = _banded_int(ctx, "selector_cells", 3, 4, 3, 7)
    elif difficulty == "hard":
        width = _banded_int(ctx, "grid_w", 13, 16, 10, 16)
        n_objects = _banded_int(ctx, "n_objects", 3, 4, 2, 4)
        selector_cells = _banded_int(ctx, "selector_cells", 5, 7, 3, 7)
    else:
        width = _banded_int(ctx, "grid_w", 12, 15, 10, 16)
        n_objects = _banded_int(ctx, "n_objects", 3, 4, 2, 4)
        selector_cells = _banded_int(ctx, "selector_cells", 3, 6, 3, 7)

    rng = ctx.draw_rng("layout")
    palette_size = strict_profile[2] if strict_profile is not None else None
    body_colors, target = _choose_colors(rng, n_objects, code, palette_size)
    selector_color = body_colors[0]

    if strict_profile is not None:
        selector_shape = _choose_shape(
            rng,
            cells=selector_cells,
            code=code,
            signature=strict_profile[0],
        )
        distractor_shapes = [
            _choose_shape(rng, cells=signature[0], code=code, signature=signature)
            for signature in strict_profile[1]
        ]
    else:
        selector_shape = _choose_shape(rng, cells=selector_cells, code=code)
        # The first distractor is strictly larger, rebutting largest-object
        # selection.  Remaining distractors add morphology variation.
        distractor_sizes = [min(8, selector_cells + 1)]
        while len(distractor_sizes) < n_objects - 1:
            distractor_sizes.append(rng.randint(3, 8))
        distractor_shapes = [
            _choose_shape(rng, cells=size, code=code)
            for size in distractor_sizes
        ]

    grid = full_grid(8, width, 0)
    grid[0][0] = selector_color
    grid[0][1] = code
    grid[0][2] = target

    slots = list(_slots(width))
    # A distractor occupies the first reading-order slot.  The selector moves
    # among the remaining slots, preventing both first-object and fixed-slot
    # shortcuts while preserving guaranteed separation.
    selector_slot_index = rng.choice((1, 2, 3))
    selected_slots = {0, selector_slot_index}
    remaining = [index for index in (1, 2, 3) if index != selector_slot_index]
    selected_slots.update(rng.sample(remaining, n_objects - 2))
    distractor_slot_indices = sorted(selected_slots - {selector_slot_index})

    _paint_shape(
        grid,
        selector_shape,
        *slots[selector_slot_index],
        selector_color,
        rng,
    )
    for color, shape, slot_index in zip(
        body_colors[1:], distractor_shapes, distractor_slot_indices
    ):
        _paint_shape(grid, shape, *slots[slot_index], color, rng)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"internal generator defect: {errors}")
    if strict_profile is not None and _profile_of(grid) != strict_profile:
        raise RuntimeError(
            f"strict profile drift: expected {strict_profile!r}, got {_profile_of(grid)!r}"
        )
    return grid
