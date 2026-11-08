"""Constructive sampler for 4e102ec13fc8 — header palette by onion depth.

The first row is a palette: every nonzero header cell participates, even when
zeros separate entries.  In the body, every nonzero/non-9 cell belongs to a
binary 4-connected shape.  Each component is repeatedly peeled by its exposed
cardinal boundary; depth 1 receives palette[0], depth 2 palette[1], and depths
past the palette clamp to its final color.

This module only samples inputs.  The unchanged canonical Racket rule remains
output authority.  ``rule_mirror`` and the named rivals are executable review
contracts, not replacement labels.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from itertools import product
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4e102ec13fc8"
TASK_ID = GENERATOR_ID
RULE_HASH = "6a515fd5e427"
VERSION = "3.0.0"
SUMMARY = (
    "Row 0 contains 2..4 distinct nonzero palette colors, optionally separated "
    "by one or two zero gaps. Rows 1+ contain 1..3 separated, monochrome, often "
    "non-rectangular 4-connected components in a body color independent of the "
    "palette. Repeatedly peel each component's exposed cardinal boundary. Paint "
    "depth d with palette[min(d-1, last)], preserving the header and background."
)
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "8..18 rectangular ARC grid; row 0 is the header and rows 1+ are the body",
    "header has 2..4 distinct colors at column 0 onward with at most two interior zero gaps",
    "body has one monochrome color disjoint from the palette and 1..3 binary 4-components",
    "at least one body component has onion depth two or greater",
    "all advertised exact axes are recoverable from returned pixels",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical-profile schedule: 8 or 10", "valid": "8..18"},
    "grid_w": {"type": "int", "default": "canonical-profile schedule: 8 or 9", "valid": "8..18"},
    "palette_size": {"type": "int", "default": "canonical-profile schedule: 3 or 4", "valid": "2..4"},
    "header_gaps": {"type": "int", "default": "1..2", "valid": "0..2"},
    "component_count": {"type": "int", "default": "2..3", "valid": "1..3"},
    "shape_color": {"type": "int", "default": "2..8", "valid": "1..8"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
MIN_STRICT_FRAC = 0.50

_BOUNDS = {
    "grid_h": (8, 18),
    "grid_w": (8, 18),
    "palette_size": (2, 4),
    "header_gaps": (0, 2),
    "component_count": (1, 3),
    "shape_color": (1, 8),
}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_EIGHT = tuple(
    (dr, dc)
    for dr, dc in product((-1, 0, 1), repeat=2)
    if (dr, dc) != (0, 0)
)
_CANONICAL_PROFILES = {(8, 8, 5), (10, 9, 6)}


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be one of None/easy/medium/hard")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")
        lo, hi = _BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo},{hi}]")


def _axis(ctx, overrides: dict[str, Any], name: str, default_options: tuple[int, ...]) -> int:
    """Draw an exact axis; overrides retain the full advertised domain."""
    lo, hi = _BOUNDS[name]
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, default_options)


def _normalize(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = frozenset(cells)
    if not cells:
        return cells
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _rotate(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = _normalize(cells)
    max_r = max(r for r, _ in cells)
    return _normalize((c, max_r - r) for r, c in cells)


def _reflect(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = _normalize(cells)
    max_c = max(c for _, c in cells)
    return _normalize((r, max_c - c) for r, c in cells)


def _orientations(cells: Iterable[tuple[int, int]]) -> tuple[frozenset[tuple[int, int]], ...]:
    shape = _normalize(cells)
    variants = set()
    for reflected in (False, True):
        current = _reflect(shape) if reflected else shape
        for _ in range(4):
            variants.add(_normalize(current))
            current = _rotate(current)
    return tuple(sorted(variants, key=lambda s: tuple(sorted(s))))


def _diamond(size: int) -> frozenset[tuple[int, int]]:
    radius = size // 2
    return frozenset(
        (r, c)
        for r in range(size)
        for c in range(size)
        if abs(r - radius) + abs(c - radius) <= radius
    )


def _rounded_square(size: int) -> frozenset[tuple[int, int]]:
    corners = {(0, 0), (0, size - 1), (size - 1, 0), (size - 1, size - 1)}
    return frozenset(
        (r, c) for r in range(size) for c in range(size) if (r, c) not in corners
    )


def _thick_cross(size: int) -> frozenset[tuple[int, int]]:
    middle = size // 2
    return frozenset(
        (r, c)
        for r in range(size)
        for c in range(size)
        if abs(r - middle) <= 1 or abs(c - middle) <= 1
    )


def _notched_square(size: int) -> frozenset[tuple[int, int]]:
    cells = set(_rounded_square(size))
    middle = size // 2
    cells.remove((0, middle))
    if size >= 7:
        cells.remove((1, 0))
    return frozenset(cells)


def _main_shape(size: int, sample_index: int) -> frozenset[tuple[int, int]]:
    makers = (_diamond, _rounded_square, _thick_cross, _notched_square)
    return makers[sample_index % len(makers)](size)


def _shape_dims(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _chebyshev_separated(point: tuple[int, int], cells: Iterable[tuple[int, int]]) -> bool:
    r, c = point
    return all(max(abs(r - rr), abs(c - cc)) > 1 for rr, cc in cells)


def _place_components(
    body_h: int,
    width: int,
    main_shape: frozenset[tuple[int, int]],
    component_count: int,
    rng,
) -> list[frozenset[tuple[int, int]]]:
    """Place a teaching shape in one corner and satellites opposite it.

    The 8x8 lower bound leaves a two-cell corridor around every 5x5 main
    envelope; the 10x9 profile does the same for 7x7.  Four mirrored layouts
    therefore cover the complete advertised domain without rejection loops or
    expensive exhaustive packing.
    """
    need = component_count - 1
    layouts = []
    for oriented in _orientations(main_shape):
        shape_h, shape_w = _shape_dims(oriented)
        anchors = (
            (0, 0, ((0, width - 1), (body_h - 1, width - 1))),
            (0, width - shape_w, ((0, 0), (body_h - 1, 0))),
            (body_h - shape_h, 0, ((0, width - 1), (body_h - 1, width - 1))),
            (body_h - shape_h, width - shape_w, ((0, 0), (body_h - 1, 0))),
        )
        for top, left, satellites in anchors:
            placed = frozenset((top + r, left + c) for r, c in oriented)
            selected = tuple(satellites[:need])
            if all(point not in placed and _chebyshev_separated(point, placed) for point in selected):
                if len(selected) < 2 or _chebyshev_separated(selected[1], selected[:1]):
                    layouts.append((placed, selected))
    if not layouts:
        raise ValueError(
            f"cannot place {component_count} components in body {body_h}x{width}"
        )
    placed, satellites = rng.choice(layouts)
    return [placed, *(frozenset({point}) for point in satellites)]


def _header_positions(palette_size: int, gaps: int, rng) -> list[int]:
    between = [0] * (palette_size - 1)
    if gaps:
        # A gap immediately after the first entry makes the prefix shortcut an
        # observable error. Remaining gaps vary across the interior slots.
        between[0] = 1
        for _ in range(gaps - 1):
            between[rng.randrange(len(between))] += 1
    positions = [0]
    for gap in between:
        positions.append(positions[-1] + 1 + gap)
    return positions


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # Defaults alternate the two exact canonical (height,width,palette-size)
    # profiles. Each axis remains independently overridable over its full domain.
    small_profile = sample_index % 2 == 0
    h = _axis(ctx, overrides, "grid_h", (8,) if small_profile else (10,))
    w = _axis(ctx, overrides, "grid_w", (8,) if small_profile else (9,))
    palette_size = _axis(ctx, overrides, "palette_size", (3,) if small_profile else (4,))
    gaps = _axis(ctx, overrides, "header_gaps", (1, 2))
    component_count = _axis(ctx, overrides, "component_count", (2, 3))
    shape_color_defaults = {
        None: tuple(range(2, 9)),
        "easy": (2, 3),
        "medium": (4, 5),
        "hard": (6, 7, 8),
    }[difficulty]
    shape_color = _axis(ctx, overrides, "shape_color", shape_color_defaults)

    palette_rng = ctx.draw_rng("palette_colors")
    palette_pool = [color for color in range(1, 9) if color != shape_color]
    palette = palette_rng.sample(palette_pool, palette_size)

    grid = full_grid(h, w, 0)
    for position, color in zip(
        _header_positions(palette_size, gaps, ctx.draw_rng("header_layout")), palette
    ):
        grid[0][position] = color

    body_h = h - 1
    # A 7x7 profile fits exactly in the 10x9 canonical envelope while leaving
    # room for two separated components. All smaller/legal canvases use 5x5.
    size = 7 if body_h >= 9 and w >= 9 else 5
    difficulty_offset = {None: 0, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    main = _main_shape(size, sample_index + difficulty_offset)
    components = _place_components(
        body_h, w, main, component_count, ctx.draw_rng("component_layout")
    )
    for component in components:
        for body_r, c in component:
            grid[body_r + 1][c] = shape_color

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructive generator violated its grammar: {errors[0]}")
    return grid


def _components(cells: Iterable[tuple[int, int]]) -> list[frozenset[tuple[int, int]]]:
    unseen = set(cells)
    result: list[frozenset[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        component = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in _CARDINAL:
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    stack.append(point)
        result.append(frozenset(component))
    return result


def _body_components(grid: list[list[int]]) -> list[frozenset[tuple[int, int]]]:
    cells = {
        (r, c)
        for r in range(1, len(grid))
        for c, value in enumerate(grid[r])
        if value not in (0, 9)
    }
    return _components(cells)


def _depths_for_grid(grid: list[list[int]]) -> dict[tuple[int, int], int]:
    """Onion depth by explicit repeated erosion, matching the selected rule."""
    depths: dict[tuple[int, int], int] = {}
    for component in _body_components(grid):
        remaining = set(component)
        depth = 1
        while remaining:
            boundary = {
                (r, c)
                for r, c in remaining
                if any((r + dr, c + dc) not in remaining for dr, dc in _CARDINAL)
            }
            if not boundary:
                raise RuntimeError("finite component unexpectedly has no exposed boundary")
            for point in boundary:
                depths[point] = depth
            remaining.difference_update(boundary)
            depth += 1
    return depths


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the pinned Racket rule for tests and rivals."""
    out = deepcopy(grid)
    if not grid or not grid[0]:
        return out
    palette = [value for value in grid[0] if value != 0]
    if not palette:
        return out
    for (r, c), depth in _depths_for_grid(grid).items():
        out[r][c] = palette[min(depth - 1, len(palette) - 1)]
    return out


def _variant_output(
    grid: list[list[int]], *, prefix_palette=False, blue_only=False, largest_only=False
) -> list[list[int]]:
    out = deepcopy(grid)
    if prefix_palette:
        palette = []
        for value in grid[0]:
            if value == 0:
                break
            palette.append(value)
    else:
        palette = [value for value in grid[0] if value != 0]
    if not palette:
        return out
    depths = _depths_for_grid(grid)
    allowed = set(depths)
    if largest_only:
        components = _body_components(grid)
        if components:
            allowed = set(max(components, key=lambda cells: (len(cells), tuple(sorted(cells)))))
    for (r, c), depth in depths.items():
        if (r, c) not in allowed or (blue_only and grid[r][c] != 1):
            continue
        out[r][c] = palette[min(depth - 1, len(palette) - 1)]
    return out


def _prefix_palette_output(grid):
    return _variant_output(grid, prefix_palette=True)


def _blue_cells_only_output(grid):
    return _variant_output(grid, blue_only=True)


def _largest_component_only_output(grid):
    return _variant_output(grid, largest_only=True)


def observe_overrides(grid: list[list[int]]) -> dict[str, int]:
    palette_positions = [c for c, value in enumerate(grid[0]) if value != 0]
    body_colors = {
        value for row in grid[1:] for value in row if value not in (0, 9)
    }
    if not palette_positions or len(body_colors) != 1:
        raise ValueError("grid does not expose a unique header/body grammar")
    first, last = min(palette_positions), max(palette_positions)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "palette_size": len(palette_positions),
        "header_gaps": sum(grid[0][c] == 0 for c in range(first, last + 1)),
        "component_count": len(_body_components(grid)),
        "shape_color": next(iter(body_colors)),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the complete ordinary teaching grammar and reject impostors."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["empty or non-grid value"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]

    errors: list[str] = []
    height = len(grid)
    if not 8 <= height <= 18 or not 8 <= width <= 18:
        errors.append(f"dimensions {height}x{width} outside 8..18")
    if any(value == 9 for row in grid for value in row):
        errors.append("ordinary teaching inputs do not use sentinel color 9")

    positions = [c for c, value in enumerate(grid[0]) if value != 0]
    if not 2 <= len(positions) <= 4:
        errors.append(f"header must contain 2..4 nonzero colors; found {len(positions)}")
        palette: list[int] = []
    else:
        palette = [grid[0][c] for c in positions]
        if positions[0] != 0:
            errors.append("header palette must begin at column 0")
        gaps = sum(grid[0][c] == 0 for c in range(positions[0], positions[-1] + 1))
        if gaps > 2:
            errors.append(f"header has {gaps} interior gaps; maximum is 2")
        if len(set(palette)) != len(palette):
            errors.append("header palette colors must be distinct")

    body_colors = {
        value for row in grid[1:] for value in row if value not in (0, 9)
    }
    if len(body_colors) != 1:
        errors.append(f"body must use exactly one shape color; found {sorted(body_colors)}")
    elif palette and next(iter(body_colors)) in palette:
        errors.append("body shape color must be disjoint from the header palette")

    components = _body_components(grid)
    if not 1 <= len(components) <= 3:
        errors.append(f"body must contain 1..3 components; found {len(components)}")
    if components:
        depths = _depths_for_grid(grid)
        if max(depths.values(), default=0) < 2:
            errors.append("at least one component must expose depth 2 or greater")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Canonical exact size/palette profile inside the lawful teaching grammar."""
    errors = self_check(grid)
    if errors:
        return errors
    profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
    if profile not in _CANONICAL_PROFILES:
        return [f"profile {profile} is outside canonical profiles {sorted(_CANONICAL_PROFILES)}"]
    return []


def _witness(prefix=False, blue=False, largest=False):
    def predicate(grid) -> bool:
        if self_check(grid):
            return False
        rival = _variant_output(
            grid, prefix_palette=prefix, blue_only=blue, largest_only=largest
        )
        return rival != rule_mirror(grid)
    return predicate


SEMANTIC_WITNESSES = {
    "gapped_header": _witness(prefix=True),
    "nonblue_body": _witness(blue=True),
    "multiple_components": _witness(largest=True),
}
SEMANTIC_RIVALS = {
    "contiguous_header_prefix": _prefix_palette_output,
    "blue_cells_only": _blue_cells_only_output,
    "largest_component_only": _largest_component_only_output,
}
WITNESS_RIVALS = {
    "gapped_header": ["contiguous_header_prefix"],
    "nonblue_body": ["blue_cells_only"],
    "multiple_components": ["largest_component_only"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson only when a named canonical-fitting rival is unresolved."""
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict):
            reasons.append(f"{role} is not a labeled pair")
            continue
        input_grid = pair.get("input")
        output_grid = pair.get("output")
        errors = self_check(input_grid)
        if errors:
            reasons.append(f"{role} input is outside the teaching grammar: {errors[0]}")
            continue
        if output_grid != rule_mirror(input_grid):
            reasons.append(f"{role} output disagrees with the pinned depth-palette rule")
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
        if survives and rival(query["input"]) != query["output"]:
            reasons.append(f"competitor {name!r} fits every demo but changes the query answer")
    return reasons
