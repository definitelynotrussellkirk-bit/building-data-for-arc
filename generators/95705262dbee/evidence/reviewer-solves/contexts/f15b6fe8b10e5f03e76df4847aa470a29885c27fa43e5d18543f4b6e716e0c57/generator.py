"""Lawful input sampler for sorting components by area and packing a gallery.

The unchanged Racket authority extracts every nonzero 4-connected component,
crops each component to its bounding box, sorts the crops by increasing cell
count, and packs them left-to-right with one background column between crops.
This sampler uses only the three distinct-size profiles and four grid profiles
seen in the canonical task, while varying colors, shapes, orientations, and
input order.  Generated lessons deliberately refute color-order, input-order,
descending-area, and bounding-box-area shortcuts.
"""
from __future__ import annotations

from itertools import permutations, product
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "95705262dbee"
TASK_ID = GENERATOR_ID
RULE_HASH = "7d39da4c591e"
VERSION = "2.0.1"
SUMMARY = (
    "Three isolated distinct-color components with canonical distinct-size "
    "profiles. Sort their cropped shapes by increasing cell count and pack "
    "them top-aligned from left to right with one zero column between shapes."
)

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 12
MIN_STRICT_FRAC = 1.0

CANONICAL_GRID_PROFILES = (
    (10, 12),
    (11, 13),
    (10, 14),
    (12, 12),
)
SIZE_PROFILES = (
    "canonical_345",
    "canonical_358",
    "canonical_458",
)
SIZE_PROFILE_SIZES = {
    "canonical_345": (3, 4, 5),
    "canonical_358": (3, 5, 8),
    "canonical_458": (4, 5, 8),
}
_SIZES_TO_PROFILE = {sizes: name for name, sizes in SIZE_PROFILE_SIZES.items()}

INVARIANTS = [
    "background is 0 and all cells are literal ARC colors 0..9",
    "exactly three monochromatic 4-connected components use distinct colors",
    "component sizes are one of (3,4,5), (3,5,8), or (4,5,8)",
    "different components do not touch orthogonally",
    "the packed gallery is at most four rows and ten columns",
    "ordinary lessons break input-position and color-order shortcuts",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "periodic canonical profile",
        "valid": "10..12",
    },
    "grid_w": {
        "type": "int",
        "default": "periodic canonical profile",
        "valid": "12..14",
    },
    "size_profile": {
        "type": "str",
        "default": "periodic canonical size profile",
        "valid": "|".join(SIZE_PROFILES),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# Base polyominoes.  Dihedral variants are derived below and de-duplicated.
_BASE_SHAPES = {
    3: (
        ((0, 0), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 1), (0, 2), (1, 0), (1, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
    ),
    5: (
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    ),
    8: (
        tuple((r, c) for r in range(3) for c in range(3) if (r, c) != (1, 1)),
        tuple((r, c) for r in range(2) for c in range(4)),
    ),
}

# For profiles containing both sizes 5 and 8, force bbox-area disagreement:
# the size-5 shape spans a 3x3 box (area 9) while the size-8 rectangle spans
# a 2x4 box (area 8).  A bbox-area sorter therefore cannot imitate cell area.
_SPREAD_SIZE5 = _BASE_SHAPES[5][1:]
_COMPACT_SIZE8 = (_BASE_SHAPES[8][1],)
_NON_IDENTITY_PERMS = tuple(p for p in permutations(range(3)) if p != (0, 1, 2))
_BAND_COLOR_RANK_ORDERS = {
    "easy": (1, 0, 2),
    "medium": (2, 0, 1),
    "hard": (2, 1, 0),
}
_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    if not points:
        return ()
    min_r = min(r for r, _ in points)
    min_c = min(c for _, c in points)
    return tuple(sorted((r - min_r, c - min_c) for r, c in points))


def _dihedral_variants(shape: Sequence[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    variants = set()
    original = tuple(shape)
    for reflected in (False, True):
        current = _normalize((r, -c if reflected else c) for r, c in original)
        for _ in range(4):
            variants.add(current)
            current = _normalize((c, -r) for r, c in current)
    return tuple(sorted(variants))


def _bbox_dims(cells: Sequence[tuple[int, int]]) -> tuple[int, int]:
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


_SHAPE_VARIANTS = {
    size: tuple(sorted({variant for shape in shapes for variant in _dihedral_variants(shape)}))
    for size, shapes in _BASE_SHAPES.items()
}
_SPREAD5_VARIANTS = tuple(
    sorted({variant for shape in _SPREAD_SIZE5 for variant in _dihedral_variants(shape)})
)
_COMPACT8_VARIANTS = tuple(
    sorted({variant for shape in _COMPACT_SIZE8 for variant in _dihedral_variants(shape)})
)


def _shape_choices(profile: str, width: int, rng) -> tuple[tuple[tuple[int, int], ...], ...]:
    sizes = SIZE_PROFILE_SIZES[profile]
    banks = []
    for size in sizes:
        if size == 5 and 8 in sizes:
            banks.append(_SPREAD5_VARIANTS)
        elif size == 8 and 5 in sizes:
            banks.append(_COMPACT8_VARIANTS)
        else:
            banks.append(_SHAPE_VARIANTS[size])

    candidates = []
    for shapes in product(*banks):
        dims = tuple(_bbox_dims(shape) for shape in shapes)
        packed_width = sum(w for _, w in dims) + 2
        if packed_width > min(width, 10):
            continue
        if max(h for h, _ in dims) > 4:
            continue
        candidates.append(shapes)
    if not candidates:
        raise RuntimeError(f"no shape combination fits profile {profile!r} at width {width}")
    return rng.choice(candidates)


def _slot_zones(height: int, width: int) -> tuple[tuple[int, int, int, int], ...]:
    """Three separated zones in stable row-major order: NW, NE, south."""
    return (
        (1, 0, 4, 5),
        (1, width - 5, 4, 5),
        (height - 4, (width - 6) // 2, 4, 6),
    )


def _place_in_zone(shape, zone, rng) -> tuple[tuple[int, int], ...]:
    top, left, zone_h, zone_w = zone
    shape_h, shape_w = _bbox_dims(shape)
    if shape_h > zone_h or shape_w > zone_w:
        raise RuntimeError("shape does not fit its constructive placement zone")
    # Keep every slot's row fixed so NW, NE, south remain the actual row-major
    # component order; horizontal jitter still varies the absolute positions.
    col = left + rng.randint(0, zone_w - shape_w)
    return tuple((top + r, col + c) for r, c in shape)


def _scheduled_defaults(sample_index: int) -> tuple[int, int, str]:
    h, w = CANONICAL_GRID_PROFILES[sample_index % len(CANONICAL_GRID_PROFILES)]
    profile = SIZE_PROFILES[sample_index % len(SIZE_PROFILES)]
    return h, w, profile


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    for name in ("grid_h", "grid_w"):
        if name in overrides and overrides[name] is not None and type(overrides[name]) is not int:
            raise TypeError(f"{name} must be an integer")
    if (
        "size_profile" in overrides
        and overrides["size_profile"] is not None
        and type(overrides["size_profile"]) is not str
    ):
        raise TypeError("size_profile must be a string")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=dict(overrides),
    )
    scheduled_h, scheduled_w, scheduled_profile = _scheduled_defaults(sample_index)
    if ctx.overrides.get("grid_h") is None:
        ctx.overrides["grid_h"] = scheduled_h
    if ctx.overrides.get("grid_w") is None:
        ctx.overrides["grid_w"] = scheduled_w
    if ctx.overrides.get("size_profile") is None:
        ctx.overrides["size_profile"] = scheduled_profile

    height = ctx.draw_int("grid_h", 10, 12)
    width = ctx.draw_int("grid_w", 12, 14)
    profile = ctx.draw_choice("size_profile", SIZE_PROFILES)
    sizes = SIZE_PROFILE_SIZES[profile]

    shapes = _shape_choices(profile, width, ctx.draw_rng("shape_geometry"))

    # The numeric color order is intentionally a non-identity permutation of
    # the increasing-size ranks, so a color sorter fails on every normal draw.
    palette = sorted(ctx.draw_rng("palette_values").sample(range(1, 10), 3))
    # Counterbalance the three difficulty bands with different guaranteed
    # non-identity color/size associations.  The semantic rule and canonical
    # profile coverage stay identical, but banded draws are observably distinct
    # and every band still defeats the color-order shortcut.
    color_rank_order = _BAND_COLOR_RANK_ORDERS.get(difficulty)
    if color_rank_order is None:
        color_rank_order = ctx.draw_rng("color_rank_order").choice(_NON_IDENTITY_PERMS)
    colors_by_rank = [0, 0, 0]
    for color, rank in zip(palette, color_rank_order):
        colors_by_rank[rank] = color

    # Likewise, the row-major input order never equals increasing-size order.
    input_rank_order = ctx.draw_rng("input_rank_order").choice(_NON_IDENTITY_PERMS)
    zones = _slot_zones(height, width)
    position_rng = ctx.draw_rng("position_jitter")
    grid = full_grid(height, width, 0)
    for slot_index, rank in enumerate(input_rank_order):
        cells = _place_in_zone(shapes[rank], zones[slot_index], position_rng)
        for r, c in cells:
            if grid[r][c] != 0:
                raise RuntimeError("constructive placement collision")
            grid[r][c] = colors_by_rank[rank]

    errors = self_check(grid)
    if errors:
        raise RuntimeError("constructed an invalid grid: " + "; ".join(errors))
    if tuple(sorted(len(comp["cells"]) for comp in _components(grid))) != sizes:
        raise RuntimeError("constructed size profile drifted from the selected schedule")
    return grid


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty list/tuple of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty lists/tuples"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not (10 <= len(grid) <= 12 and 12 <= width <= 14):
        return ["grid dimensions must be within 10..12 rows and 12..14 columns"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be literal integer ARC colors from 0 through 9"]
    return []


def _components(grid) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _DIRS:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            result.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "top": min(rows),
                    "left": min(cols),
                    "bottom": max(rows),
                    "right": max(cols),
                }
            )
    return result


def _packed_dims(components) -> tuple[int, int]:
    heights = [comp["bottom"] - comp["top"] + 1 for comp in components]
    widths = [comp["right"] - comp["left"] + 1 for comp in components]
    return max(heights), sum(widths) + len(widths) - 1


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors
    components = _components(grid)
    if len(components) != 3:
        errors.append(f"expected exactly three components, found {len(components)}")
        return errors

    colors = [comp["color"] for comp in components]
    if len(set(colors)) != 3:
        errors.append("the three components must have distinct colors")
    sizes = tuple(sorted(len(comp["cells"]) for comp in components))
    if sizes not in _SIZES_TO_PROFILE:
        errors.append(f"unsupported component-size profile {sizes}")

    owner = {cell: index for index, comp in enumerate(components) for cell in comp["cells"]}
    for (r, c), index in owner.items():
        for dr, dc in _DIRS:
            neighbor = owner.get((r + dr, c + dc))
            if neighbor is not None and neighbor != index:
                errors.append("different components must not touch orthogonally")
                return errors

    packed_h, packed_w = _packed_dims(components)
    if packed_h > 4 or packed_w > 10:
        errors.append(f"packed gallery {packed_h}x{packed_w} exceeds canonical 4x10 envelope")
    return errors


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    profile = (len(grid), len(grid[0]))
    if profile not in CANONICAL_GRID_PROFILES:
        return [f"grid profile {profile} is outside the canonical profile set"]
    if len({value for row in grid for value in row}) != 4:
        return ["canonical grammar requires background plus exactly three colors"]
    return []


def observe_overrides(grid) -> dict[str, Any]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe axes on an invalid grid: " + "; ".join(errors))
    sizes = tuple(sorted(len(comp["cells"]) for comp in _components(grid)))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "size_profile": _SIZES_TO_PROFILE[sizes],
    }


def _crop(grid, component) -> list[list[int]]:
    height = component["bottom"] - component["top"] + 1
    width = component["right"] - component["left"] + 1
    piece = full_grid(height, width, 0)
    for r, c in component["cells"]:
        piece[r - component["top"]][c - component["left"]] = component["color"]
    return piece


def _pack_ordered(grid, components) -> list[list[int]]:
    pieces = [_crop(grid, component) for component in components]
    out_h = max(len(piece) for piece in pieces)
    out_w = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    output = full_grid(out_h, out_w, 0)
    left = 0
    for piece in pieces:
        for r, row in enumerate(piece):
            for c, value in enumerate(row):
                if value != 0:
                    output[r][left + c] = value
        left += len(piece[0]) + 1
    return output


def _validated_components(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("grid outside rule mirror domain: " + "; ".join(errors))
    return _components(grid)


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for tests/rivals; Racket remains authority."""
    components = _validated_components(grid)
    ordered = sorted(
        components,
        key=lambda comp: (len(comp["cells"]), comp["top"], comp["left"]),
    )
    return _pack_ordered(grid, ordered)


def _rival_descending_area(grid):
    components = _validated_components(grid)
    ordered = sorted(
        components,
        key=lambda comp: (-len(comp["cells"]), comp["top"], comp["left"]),
    )
    return _pack_ordered(grid, ordered)


def _rival_input_order(grid):
    components = _validated_components(grid)
    ordered = sorted(components, key=lambda comp: (comp["top"], comp["left"]))
    return _pack_ordered(grid, ordered)


def _rival_color_order(grid):
    components = _validated_components(grid)
    ordered = sorted(components, key=lambda comp: comp["color"])
    return _pack_ordered(grid, ordered)


def _rival_bbox_area(grid):
    components = _validated_components(grid)
    ordered = sorted(
        components,
        key=lambda comp: (
            (comp["bottom"] - comp["top"] + 1) * (comp["right"] - comp["left"] + 1),
            comp["top"],
            comp["left"],
        ),
    )
    return _pack_ordered(grid, ordered)


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "descending_area": _rival_descending_area,
    "input_order": _rival_input_order,
    "color_order": _rival_color_order,
    "bbox_area": _rival_bbox_area,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _rival_differs(name: str, grid) -> bool:
    try:
        return SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)
    except (TypeError, ValueError):
        return False


SEMANTIC_WITNESSES = {
    "ascending_not_descending": lambda grid: _rival_differs("descending_area", grid),
    "area_not_input_order": lambda grid: _rival_differs("input_order", grid),
    "area_not_color_order": lambda grid: _rival_differs("color_order", grid),
    "cell_area_not_bbox_area": lambda grid: _rival_differs("bbox_area", grid),
}
WITNESS_RIVALS = {
    "ascending_not_descending": ["descending_area"],
    "area_not_input_order": ["input_order"],
    "area_not_color_order": ["color_order"],
    "cell_area_not_bbox_area": ["bbox_area"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} labeled demonstrations are required"]

    valid_demos = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or not {"input", "output"} <= set(demo):
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = strict_canonical_like(demo["input"])
        if errors:
            reasons.append(f"demo {index} input: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the size-sort rule")
        valid_demos.append(demo)

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input")
        query_truth = None
    else:
        errors = strict_canonical_like(query["input"])
        if errors:
            reasons.append("query input: " + errors[0])
            query_truth = None
        else:
            query_truth = rule_mirror(query["input"])

    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in valid_demos):
            if rival(query["input"]) != query_truth:
                reasons.append(f"rival {name!r} fits every demo but changes the query")
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    blank = full_grid(10, 12, 0)

    tied = full_grid(10, 12, 0)
    for r, c in ((1, 1), (1, 2), (2, 1)):
        tied[r][c] = 2
    for r, c in ((1, 8), (1, 9), (2, 8)):
        tied[r][c] = 4
    for r, c in ((7, 4), (7, 5), (7, 6), (8, 4), (8, 5)):
        tied[r][c] = 6

    repeated_color = full_grid(10, 12, 0)
    for r, c in ((1, 1), (1, 2), (2, 1)):
        repeated_color[r][c] = 2
    for r, c in ((1, 8), (1, 9), (2, 8), (2, 9)):
        repeated_color[r][c] = 2
    for r, c in ((7, 4), (7, 5), (7, 6), (8, 4), (8, 5)):
        repeated_color[r][c] = 6

    touching = full_grid(10, 12, 0)
    for r, c in ((1, 1), (1, 2), (2, 1)):
        touching[r][c] = 2
    for r, c in ((2, 2), (2, 3), (3, 2), (3, 3)):
        touching[r][c] = 4
    for r, c in ((7, 4), (7, 5), (7, 6), (8, 4), (8, 5)):
        touching[r][c] = 6

    wrong_profile = full_grid(10, 12, 0)
    for r, c in ((1, 1), (1, 2)):
        wrong_profile[r][c] = 2
    for r, c in ((1, 8), (1, 9), (2, 8), (2, 9)):
        wrong_profile[r][c] = 4
    for r, c in ((7, 3), (7, 4), (7, 5), (7, 6), (8, 3), (8, 4), (8, 5), (8, 6)):
        wrong_profile[r][c] = 6

    return [
        ("blank", blank),
        ("tied_sizes", tied),
        ("repeated_color", repeated_color),
        ("orthogonal_touch", touching),
        ("unsupported_size_profile", wrong_profile),
    ]
