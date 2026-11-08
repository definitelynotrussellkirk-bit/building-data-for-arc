"""Generator for 4b:m24 — keep even-area 4-connected components.

The output authority keeps every nonzero 4-connected component whose number of
cells is even and erases every odd-area component.  Ordinary four-example
lessons deliberately vary area, shape, color role, and diagonal contact so the
rule cannot be replaced by a color, position, rectangle, bounding-box, or
8-connectivity shortcut.
"""
from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bbb0f21653d8"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "42e06f7977db"
EXAMPLES_NEEDED = 4

SUMMARY = (
    "Keep exactly the nonzero 4-connected components with even cell count; "
    "erase odd-area components while preserving each kept cell's color."
)

INVARIANTS = [
    "background is 0 and the grid is 7..14 by 8..14",
    "there are 4..6 isolated monochromatic 4-connected components",
    "component areas are 2..8 with at least two even and two odd areas",
    "exactly four nonzero colors are used",
    "ordinary four-sample lessons include canonical scale, repeated-color role swaps, bounding-box counterexamples, and decisive diagonal contact",
]

PALETTES = {
    "canonical": (2, 3, 4, 5),
    "warm": (1, 2, 3, 4),
    "cool": (5, 6, 8, 9),
    "varied": (1, 4, 7, 9),
}
PALETTE_KINDS = tuple(PALETTES)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware; every fourth sample uses a canonical profile",
        "valid": "7..14",
        "doc": "Returned grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware; every fourth sample uses a canonical profile",
        "valid": "8..14",
        "doc": "Returned grid width.",
    },
    "n_blobs": {
        "type": "int",
        "default": "four-sample cycle 4,5,6,5 subject to explicit small dimensions",
        "valid": "4..6",
        "doc": "Number of nonzero 4-connected components.",
    },
    "palette_kind": {
        "type": "enum",
        "default": "four-sample cycle canonical,warm,cool,varied",
        "valid": "canonical|warm|cool|varied",
        "doc": "Exact four-color set, recoverable from the returned grid.",
    },
    "diagonal_touch": {
        "type": "bool",
        "default": "alternates false,true,false,true over each lesson",
        "valid": "false|true",
        "doc": "Whether two distinct 4-components touch diagonally.",
    },
}

_BAND_H = {"easy": (8, 10), "medium": (9, 12), "hard": (11, 14)}
_BAND_W = {"easy": (9, 11), "medium": (10, 13), "hard": (12, 14)}
_CANONICAL_PROFILES = (
    (9, 11, (2, 3, 4, 5)),
    (10, 10, (3, 4, 4, 5)),
    (9, 12, (2, 3, 4, 5)),
    (11, 11, (2, 3, 4, 5)),
    (10, 12, (3, 4, 4, 5)),
)
_CANONICAL_PROFILE_SET = {
    (height, width, tuple(sorted(sizes)))
    for height, width, sizes in _CANONICAL_PROFILES
}
_MIN_DIMS = {
    (4, False): (7, 8),
    (4, True): (7, 8),
    (5, False): (8, 9),
    (5, True): (8, 9),
    (6, False): (9, 10),
    (6, True): (8, 9),
}
_SIZE_PLANS = {
    4: (2, 3, 4, 5),
    5: (2, 3, 4, 5, 8),
    6: (2, 3, 4, 5, 8, 7),
}

# Multiple templates per area prevent a shape-name shortcut.  Every template is
# 4-connected; rotations/reflections are generated below.
_SHAPE_TEMPLATES = {
    2: (
        ((0, 0), (0, 1)),
    ),
    3: (
        ((0, 0), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 1), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (1, 0), (1, 1), (2, 1)),
    ),
    5: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    ),
    6: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2)),
    ),
    7: (
        ((0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1), (2, 2)),
    ),
    8: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
    ),
}

MIN_STRICT_FRAC = 0.20


def _normalize_difficulty(difficulty: str | None) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in _BAND_H:
        raise ValueError("difficulty must be easy, medium, hard, or None")
    return difficulty


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    for name, lo, hi in (("grid_h", 7, 14), ("grid_w", 8, 14), ("n_blobs", 4, 6)):
        if name not in overrides:
            continue
        try:
            value = int(overrides[name])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name} must be an integer") from exc
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")
    if "palette_kind" in overrides and overrides["palette_kind"] not in PALETTE_KINDS:
        raise ValueError(f"palette_kind must be one of {PALETTE_KINDS}")
    if "diagonal_touch" in overrides and not isinstance(overrides["diagonal_touch"], bool):
        raise ValueError("diagonal_touch must be true or false")


def _max_default_blobs_for_explicit_dims(overrides: dict[str, Any], diagonal_touch: bool) -> int:
    height = int(overrides.get("grid_h", 14))
    width = int(overrides.get("grid_w", 14))
    feasible = 4
    for count in (5, 6):
        min_height, min_width = _MIN_DIMS[(count, diagonal_touch)]
        if height >= min_height and width >= min_width:
            feasible = count
    return feasible


def _draw_axis_int(ctx, name: str, default_bounds: tuple[int, int], valid: tuple[int, int]) -> int:
    if name in ctx.overrides:
        return ctx.draw_int(name, *valid)
    return ctx.draw_int(name, *default_bounds)


def _draw_axes(ctx, band: str, sample_index: int, overrides: dict[str, Any]):
    cycle = sample_index % 4
    if not overrides and cycle == 0:
        height, width, sizes = ctx.draw_rng("canonical-profile").choice(_CANONICAL_PROFILES)
        ctx.draw_int("grid_h", height, height)
        ctx.draw_int("grid_w", width, width)
        ctx.draw_int("n_blobs", 4, 4)
        ctx.draw_choice("palette_kind", ("canonical",))
        ctx.draw_choice("diagonal_touch", (False,))
        return height, width, 4, "canonical", False, sizes

    if "diagonal_touch" in overrides:
        diagonal_touch = ctx.draw_choice("diagonal_touch", (False, True))
    else:
        diagonal_touch = ctx.draw_choice("diagonal_touch", ((False, True, False, True)[cycle],))

    if "n_blobs" in overrides:
        n_blobs = ctx.draw_int("n_blobs", 4, 6)
    else:
        scheduled = (4, 5, 6, 5)[cycle]
        scheduled = min(
            scheduled,
            _max_default_blobs_for_explicit_dims(overrides, diagonal_touch),
        )
        n_blobs = ctx.draw_int("n_blobs", scheduled, scheduled)

    min_height, min_width = _MIN_DIMS[(n_blobs, diagonal_touch)]
    if "grid_h" in overrides:
        height = ctx.draw_int("grid_h", 7, 14)
    else:
        lo, hi = _BAND_H[band]
        lo = max(lo, min_height)
        if lo > hi:
            hi = lo
        height = ctx.draw_int("grid_h", lo, hi)
    if "grid_w" in overrides:
        width = ctx.draw_int("grid_w", 8, 14)
    else:
        lo, hi = _BAND_W[band]
        lo = max(lo, min_width)
        if lo > hi:
            hi = lo
        width = ctx.draw_int("grid_w", lo, hi)

    if height < min_height or width < min_width:
        raise ValueError(
            f"n_blobs={n_blobs} with diagonal_touch={diagonal_touch} requires "
            f"at least {min_height}x{min_width}, got {height}x{width}"
        )

    if "palette_kind" in overrides:
        palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    else:
        palette_kind = ctx.draw_choice(
            "palette_kind",
            (("canonical", "warm", "cool", "varied")[cycle],),
        )
    return height, width, n_blobs, palette_kind, diagonal_touch, _SIZE_PLANS[n_blobs]


def _normalize_shape(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _shape_variants(shape: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    variants = set()
    current = tuple(shape)
    for _ in range(4):
        variants.add(_normalize_shape(current))
        variants.add(_normalize_shape((row, -col) for row, col in current))
        current = tuple((col, -row) for row, col in current)
    return tuple(sorted(variants))


def _choose_shapes(sizes: tuple[int, ...], rng) -> tuple[tuple[tuple[int, int], ...], ...]:
    shapes = []
    for size in sizes:
        template = rng.choice(_SHAPE_TEMPLATES[size])
        shapes.append(rng.choice(_shape_variants(template)))
    return tuple(shapes)


def _neighbors(cells: Iterable[tuple[int, int]], deltas: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    return {
        (row + d_row, col + d_col)
        for row, col in cells
        for d_row, d_col in deltas
    }


_ORTHOGONAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIAGONAL = ((-1, -1), (-1, 1), (1, -1), (1, 1))


def _placements_for(shape, height: int, width: int):
    shape_height = max(row for row, _ in shape) + 1
    shape_width = max(col for _, col in shape) + 1
    return [
        frozenset((top + row, left + col) for row, col in shape)
        for top in range(height - shape_height + 1)
        for left in range(width - shape_width + 1)
    ]


def _has_diagonal_contact(left: Iterable[tuple[int, int]], right: set[tuple[int, int]] | frozenset[tuple[int, int]]) -> bool:
    return bool(_neighbors(left, _DIAGONAL) & set(right))


def _place_components(height: int, width: int, shapes, diagonal_touch: bool, rng):
    candidates = []
    for shape in shapes:
        placements = _placements_for(shape, height, width)
        rng.shuffle(placements)
        candidates.append(placements)

    # Keep the first two components first when a decisive diagonal witness is
    # requested; place the remaining larger shapes before smaller ones.
    if diagonal_touch:
        order = [0, 1] + sorted(range(2, len(shapes)), key=lambda i: -len(shapes[i]))
    else:
        order = sorted(range(len(shapes)), key=lambda i: -len(shapes[i]))

    chosen: list[frozenset[tuple[int, int]] | None] = [None] * len(shapes)
    occupied: set[tuple[int, int]] = set()
    node_budget = 250_000
    nodes = 0

    def search(depth: int) -> bool:
        nonlocal nodes
        if depth == len(order):
            return True
        component_index = order[depth]
        for cells in candidates[component_index]:
            nodes += 1
            if nodes > node_budget:
                return False
            if cells & occupied:
                continue
            if _neighbors(cells, _ORTHOGONAL) & occupied:
                continue
            if not diagonal_touch and _neighbors(cells, _DIAGONAL) & occupied:
                continue
            if diagonal_touch and component_index == 1:
                first = chosen[0]
                if first is None or not _has_diagonal_contact(cells, first):
                    continue
            chosen[component_index] = cells
            occupied.update(cells)
            if search(depth + 1):
                return True
            occupied.difference_update(cells)
            chosen[component_index] = None
        return False

    if not search(0):
        return None
    result = tuple(frozenset(cells) for cells in chosen if cells is not None)
    if len(result) != len(shapes):
        return None
    return result


def _component_colors(palette: tuple[int, ...], n_blobs: int, sample_index: int) -> tuple[int, ...]:
    offset = (sample_index + sample_index // 4) % len(palette)
    ordered = palette[offset:] + palette[:offset]
    if n_blobs == 4:
        return ordered
    if n_blobs == 5:
        return (ordered[0], ordered[0], ordered[1], ordered[2], ordered[3])
    return (ordered[0], ordered[0], ordered[1], ordered[1], ordered[2], ordered[3])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return a deterministic, structurally validated task input."""
    _validate_overrides(overrides)
    band = _normalize_difficulty(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    height, width, n_blobs, palette_kind, diagonal_touch, sizes = _draw_axes(
        ctx, band, sample_index, overrides
    )
    colors = _component_colors(PALETTES[palette_kind], n_blobs, sample_index)

    for attempt in range(32):
        shapes = _choose_shapes(tuple(sizes), ctx.draw_rng(f"shape-plan-{attempt}"))
        placements = _place_components(
            height,
            width,
            shapes,
            diagonal_touch,
            ctx.draw_rng(f"placement-{attempt}"),
        )
        if placements is None:
            continue
        grid = full_grid(height, width, 0)
        for cells, color in zip(placements, colors):
            for row, col in cells:
                grid[row][col] = color
        errors, _ = analyze_grid(grid)
        if errors:
            continue
        observed = observe_overrides(grid)
        expected = {
            "grid_h": height,
            "grid_w": width,
            "n_blobs": n_blobs,
            "palette_kind": palette_kind,
            "diagonal_touch": diagonal_touch,
        }
        if observed != expected:
            raise AssertionError(f"internal axis drift: expected={expected}, observed={observed}")
        return grid

    raise ValueError(
        f"could not place {n_blobs} components on {height}x{width} "
        f"with diagonal_touch={diagonal_touch}"
    )


def _nonzero_components(grid, *, diagonals: bool = False):
    height, width = len(grid), len(grid[0])
    deltas = _ORTHOGONAL + (_DIAGONAL if diagonals else ())
    seen: set[tuple[int, int]] = set()
    components = []
    for row in range(height):
        for col in range(width):
            start = (row, col)
            if grid[row][col] == 0 or start in seen:
                continue
            stack = [start]
            seen.add(start)
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for d_row, d_col in deltas:
                    neighbor = (current[0] + d_row, current[1] + d_col)
                    if not (0 <= neighbor[0] < height and 0 <= neighbor[1] < width):
                        continue
                    if neighbor in seen or grid[neighbor[0]][neighbor[1]] == 0:
                        continue
                    seen.add(neighbor)
                    stack.append(neighbor)
            components.append(tuple(sorted(cells)))
    return tuple(components)


def _component_record(grid, cells):
    colors = {grid[row][col] for row, col in cells}
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    bbox = (min(rows), min(cols), max(rows), max(cols))
    bbox_area = (bbox[2] - bbox[0] + 1) * (bbox[3] - bbox[1] + 1)
    return {
        "cells": tuple(cells),
        "colors": tuple(sorted(colors)),
        "color": next(iter(colors)) if len(colors) == 1 else None,
        "size": len(cells),
        "bbox": bbox,
        "bbox_area": bbox_area,
        "rectangular": len(cells) == bbox_area,
    }


def analyze_grid(grid) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"], {}
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and nonempty"], {}
    height = len(grid)
    if not 7 <= height <= 14:
        errors.append(f"grid_h must be 7..14, found {height}")
    if not 8 <= width <= 14:
        errors.append(f"grid_w must be 8..14, found {width}")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid cells must be integer ARC colors 0..9")
        return errors, {}
    if not any(value == 0 for row in grid for value in row):
        errors.append("background color 0 must be present")

    raw_components = _nonzero_components(grid)
    components = tuple(_component_record(grid, cells) for cells in raw_components)
    n_blobs = len(components)
    if not 4 <= n_blobs <= 6:
        errors.append(f"component count must be 4..6, found {n_blobs}")
    for index, component in enumerate(components):
        if len(component["colors"]) != 1:
            errors.append(f"component {index} is not monochromatic")
        if not 2 <= component["size"] <= 8:
            errors.append(f"component {index} area must be 2..8, found {component['size']}")

    palette = tuple(sorted({value for row in grid for value in row if value != 0}))
    palette_matches = [name for name, colors in PALETTES.items() if tuple(sorted(colors)) == palette]
    if len(palette_matches) != 1:
        errors.append(
            "nonzero palette must equal exactly one declared four-color palette; "
            f"found {palette}"
        )
        palette_kind = None
    else:
        palette_kind = palette_matches[0]

    even_count = sum(component["size"] % 2 == 0 for component in components)
    odd_count = len(components) - even_count
    if even_count < 2:
        errors.append(f"need at least two even-area components, found {even_count}")
    if odd_count < 2:
        errors.append(f"need at least two odd-area components, found {odd_count}")

    cell_owner = {
        cell: index
        for index, component in enumerate(components)
        for cell in component["cells"]
    }
    diagonal_pairs = set()
    for cell, owner in cell_owner.items():
        for neighbor in _neighbors((cell,), _DIAGONAL):
            other = cell_owner.get(neighbor)
            if other is not None and other != owner:
                diagonal_pairs.add(tuple(sorted((owner, other))))

    roles_by_color: dict[int, set[bool]] = defaultdict(set)
    for component in components:
        if component["color"] is not None:
            roles_by_color[component["color"]].add(component["size"] % 2 == 0)

    features = {
        "grid_h": height,
        "grid_w": width,
        "n_blobs": n_blobs,
        "palette_kind": palette_kind,
        "diagonal_touch": bool(diagonal_pairs),
        "diagonal_pairs": tuple(sorted(diagonal_pairs)),
        "components": components,
        "component_sizes": tuple(sorted(component["size"] for component in components)),
        "even_count": even_count,
        "odd_count": odd_count,
        "cross_parity_colors": tuple(
            sorted(color for color, roles in roles_by_color.items() if roles == {False, True})
        ),
        "bbox_parity_conflict": any(
            component["size"] % 2 != component["bbox_area"] % 2
            for component in components
        ),
        "irregular_count": sum(not component["rectangular"] for component in components),
    }
    return errors, features


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete task-specific input grammar without mutation."""
    errors, _ = analyze_grid(grid)
    return errors


def observe_overrides(grid) -> dict[str, int | str | bool]:
    """Recover every declared exact axis solely from the returned grid."""
    errors, features = analyze_grid(grid)
    if errors:
        raise ValueError("cannot observe axes on invalid grid: " + "; ".join(errors))
    return {
        "grid_h": features["grid_h"],
        "grid_w": features["grid_w"],
        "n_blobs": features["n_blobs"],
        "palette_kind": features["palette_kind"],
        "diagonal_touch": features["diagonal_touch"],
    }


def strict_canonical_like(grid) -> list[str]:
    """Return reasons when a grid is outside the exact canonical manifold."""
    errors, features = analyze_grid(grid)
    reasons = list(errors)
    if not features:
        return reasons or ["grid analysis failed"]
    signature = (
        features["grid_h"],
        features["grid_w"],
        features["component_sizes"],
    )
    if signature not in _CANONICAL_PROFILE_SET:
        reasons.append(f"profile {signature} is not one of the five canonical profiles")
    if features["palette_kind"] != "canonical":
        reasons.append("canonical nonzero palette must be exactly {2,3,4,5}")
    if features["n_blobs"] != 4:
        reasons.append("canonical examples contain exactly four components")
    if features["diagonal_touch"]:
        reasons.append("canonical components do not touch diagonally")
    return reasons


def _witness_cross_parity_color(grid) -> bool:
    errors, features = analyze_grid(grid)
    return not errors and bool(features["cross_parity_colors"])


def _witness_decisive_diagonal(grid) -> bool:
    errors, features = analyze_grid(grid)
    if errors:
        return False
    components = features["components"]
    return any(
        components[left]["size"] % 2 != components[right]["size"] % 2
        for left, right in features["diagonal_pairs"]
    )


def _witness_bbox_counterexample(grid) -> bool:
    errors, features = analyze_grid(grid)
    return not errors and bool(features["bbox_parity_conflict"])


def _witness_multiple_even_sizes(grid) -> bool:
    errors, features = analyze_grid(grid)
    if errors:
        return False
    return len({c["size"] for c in features["components"] if c["size"] % 2 == 0}) >= 2


def _witness_multiple_odd_sizes(grid) -> bool:
    errors, features = analyze_grid(grid)
    if errors:
        return False
    return len({c["size"] for c in features["components"] if c["size"] % 2 == 1}) >= 2


SEMANTIC_WITNESSES = {
    "same_color_kept_and_dropped": _witness_cross_parity_color,
    "decisive_4_vs_8_connectivity": _witness_decisive_diagonal,
    "cell_area_vs_bbox_area": _witness_bbox_counterexample,
    "multiple_even_areas": _witness_multiple_even_sizes,
    "multiple_odd_areas": _witness_multiple_odd_sizes,
}


def _paint_selected(grid, components, predicate: Callable[[dict[str, Any], int], bool]):
    output = full_grid(len(grid), len(grid[0]), 0)
    for index, component in enumerate(components):
        if not predicate(component, index):
            continue
        for row, col in component["cells"]:
            output[row][col] = grid[row][col]
    return output


def _official_output(grid):
    components = tuple(_component_record(grid, cells) for cells in _nonzero_components(grid))
    return _paint_selected(grid, components, lambda component, _: component["size"] % 2 == 0)


def _eight_connected_output(grid):
    components = tuple(_component_record(grid, cells) for cells in _nonzero_components(grid, diagonals=True))
    return _paint_selected(grid, components, lambda component, _: component["size"] % 2 == 0)


def _candidate_outputs(grid):
    components = tuple(_component_record(grid, cells) for cells in _nonzero_components(grid))
    height, width = len(grid), len(grid[0])
    candidates = {
        "keep_odd_area": _paint_selected(grid, components, lambda component, _: component["size"] % 2 == 1),
        "keep_even_bbox_area": _paint_selected(grid, components, lambda component, _: component["bbox_area"] % 2 == 0),
        "keep_rectangles": _paint_selected(grid, components, lambda component, _: component["rectangular"]),
        "keep_irregular": _paint_selected(grid, components, lambda component, _: not component["rectangular"]),
        "keep_even_color": _paint_selected(grid, components, lambda component, _: component["color"] % 2 == 0),
        "keep_top_half": _paint_selected(grid, components, lambda component, _: sum(r for r, _ in component["cells"]) / component["size"] < height / 2),
        "keep_left_half": _paint_selected(grid, components, lambda component, _: sum(c for _, c in component["cells"]) / component["size"] < width / 2),
        "keep_largest": _paint_selected(grid, components, lambda component, _: component["size"] == max(c["size"] for c in components)),
        "keep_smallest": _paint_selected(grid, components, lambda component, _: component["size"] == min(c["size"] for c in components)),
        "use_8_connectivity": _eight_connected_output(grid),
    }
    for threshold in range(2, 9):
        candidates[f"area_at_most_{threshold}"] = _paint_selected(
            grid, components, lambda component, _, t=threshold: component["size"] <= t
        )
        candidates[f"area_at_least_{threshold}"] = _paint_selected(
            grid, components, lambda component, _, t=threshold: component["size"] >= t
        )
    return candidates


def _fixed_color_candidates(demos):
    colors = sorted({value for pair in demos for row in pair["input"] for value in row if value})
    for size in range(len(colors) + 1):
        for subset in combinations(colors, size):
            keep = frozenset(subset)
            yield (
                "fixed_colors_" + "_".join(map(str, subset)),
                lambda grid, keep=keep: _paint_selected(
                    grid,
                    tuple(_component_record(grid, cells) for cells in _nonzero_components(grid)),
                    lambda component, _: component["color"] in keep,
                ),
            )


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons admitting a plausible different query answer."""
    reasons: list[str] = []
    all_pairs = list(demos) + [query]
    for index, pair in enumerate(all_pairs):
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"pair {index} input is outside the task grammar: {errors[:2]}")
            continue
        expected = _official_output(pair["input"])
        if pair.get("output") != expected:
            reasons.append(f"pair {index} output does not match even-area authority")
    if reasons:
        return reasons

    demo_features = [analyze_grid(pair["input"])[1] for pair in demos]
    if not any(features["cross_parity_colors"] for features in demo_features):
        reasons.append("demonstrations never show one color in both keep/drop roles")
    if not any(_witness_decisive_diagonal(pair["input"]) for pair in demos):
        reasons.append("demonstrations do not distinguish 4- from 8-connectivity")
    if not any(features["bbox_parity_conflict"] for features in demo_features):
        reasons.append("demonstrations do not distinguish cell area from bounding-box area")

    query_candidates = _candidate_outputs(query["input"])
    for name in sorted(query_candidates):
        matches_demos = all(
            _candidate_outputs(pair["input"])[name] == pair["output"]
            for pair in demos
        )
        if matches_demos and query_candidates[name] != query["output"]:
            reasons.append(f"competing rule {name} matches every demo but changes the query")

    for name, rule in _fixed_color_candidates(demos):
        if all(rule(pair["input"]) == pair["output"] for pair in demos):
            if rule(query["input"]) != query["output"]:
                reasons.append(f"competing rule {name} matches every demo but changes the query")
                break
    return reasons
