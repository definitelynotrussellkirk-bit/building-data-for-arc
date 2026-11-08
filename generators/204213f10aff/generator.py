"""Generator for arc_additional_puzzles_21_set3:H20.

The nonzero top-row cells are a sparse ordered legend.  Each listed color
selects exactly one body component; the reference crops those components and
packs them left-to-right.  Ordinary lessons also contain unlisted body-color
distractors, so the legend is semantically necessary.
"""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "204213f10aff"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "7e1018f60923"

SUMMARY = "Sparse legend colors select body pieces; crop and pack only those pieces in legend order."

INVARIANTS = [
    "row 0 contains 2-4 unique legend colors at non-prefix sparse positions",
    "row 1 is a blank separator between legend and body",
    "every body color forms exactly one four-connected component",
    "every legend color has exactly one matching body component",
    "ordinary generated scenes include 1-3 unlisted-color distractor components",
    "legend order, body position, color value, shape size and bbox size vary independently",
    "selected crop widths plus one-column gaps fit within the ARC 30-column output bound",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-skewed 9..30", "valid": "9..30"},
    "grid_w": {"type": "int", "default": "difficulty-skewed 12..30", "valid": "12..30"},
    "piece_count": {"type": "int", "default": "difficulty-skewed 2..4", "valid": "2..4"},
    "distractor_count": {"type": "int", "default": "difficulty-skewed 1..3", "valid": "1..3"},
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Connected, normalized footprints.  The bank deliberately crosses occupied
# area, bbox area, width, height and density; some shapes contain internal zeros.
_BASE_SHAPES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 3)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
)


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _transform(shape: tuple[tuple[int, int], ...], code: int) -> tuple[tuple[int, int], ...]:
    cells = list(shape)
    if code >= 4:
        cells = [(r, -c) for r, c in cells]
        code -= 4
    for _ in range(code):
        cells = [(c, -r) for r, c in cells]
    return _normalize(cells)


def _dims(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(shape)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _strict_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    for key in AXES:
        if key in overrides and overrides[key] is not None and type(overrides[key]) is not int:
            raise TypeError(f"{key} override must be an exact integer (not bool)")


def _legend_positions(width: int, count: int, rng, profile: int) -> list[int]:
    if profile == 0 and count >= 2:
        middle = list(range(2, width - 2))
        rng.shuffle(middle)
        positions = sorted([0, width - 1, *middle[: count - 2]])
    elif profile == 1:
        legal = list(range(1, width - 1))
        rng.shuffle(legal)
        positions = sorted(legal[:count])
    else:
        positions = sorted(rng.sample(range(width), count))
    # Force a genuine sparse/non-prefix legend.  This is a semantic lesson, not
    # a probabilistic hope, and directly repairs the retained shortcut finding.
    if positions == list(range(count)) or all(b == a + 1 for a, b in zip(positions, positions[1:])):
        positions[-1] = width - 1
        positions = sorted(set(positions))
    if len(positions) != count or positions == list(range(count)):
        # Deterministic fallback valid for every declared width/count.
        step = max(2, (width - 1) // max(1, count - 1))
        positions = [min(width - 1, i * step) for i in range(count)]
        positions[-1] = width - 1
    if len(set(positions)) != count:
        raise ValueError("could not construct distinct sparse legend positions")
    return positions


def _place_objects(
    height: int,
    width: int,
    objects: list[tuple[int, tuple[tuple[int, int], ...]]],
    rng,
    boundary_slot: int,
) -> list[list[int]]:
    body_top = 2
    grid = full_grid(height, width, 0)
    occupied: set[tuple[int, int]] = set()
    order = list(range(len(objects)))
    rng.shuffle(order)

    for ordinal, object_index in enumerate(order):
        color, shape = objects[object_index]
        sh, sw = _dims(shape)
        candidates = [
            (r, c)
            for r in range(body_top, height - sh + 1)
            for c in range(0, width - sw + 1)
        ]
        if ordinal == 0:
            if boundary_slot == 0:
                candidates = [(r, c) for r, c in candidates if c == 0] or candidates
            elif boundary_slot == 1:
                candidates = [(r, c) for r, c in candidates if c + sw == width] or candidates
            elif boundary_slot == 2:
                candidates = [(r, c) for r, c in candidates if r + sh == height] or candidates
        rng.shuffle(candidates)
        chosen = None
        for r0, c0 in candidates:
            absolute = {(r0 + r, c0 + c) for r, c in shape}
            if absolute.isdisjoint(occupied):
                chosen = absolute
                break
        if chosen is None:
            raise ValueError("could not place all colored components without overlap")
        occupied.update(chosen)
        for r, c in chosen:
            grid[r][c] = color
    return grid


def _components(grid: list[list[int]], *, start_row: int = 1) -> dict[int, list[set[tuple[int, int]]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: dict[int, list[set[tuple[int, int]]]] = defaultdict(list)
    for r in range(start_row, height):
        for c in range(width):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            comp = {(r, c)}
            seen.add((r, c))
            queue = deque([(r, c)])
            while queue:
                cr, cc = queue.popleft()
                for dr, dc in _CARDINAL:
                    nr, nc = cr + dr, cc + dc
                    if (start_row <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        comp.add((nr, nc))
                        queue.append((nr, nc))
            result[color].append(comp)
    return dict(result)


def analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return {"errors": ["empty grid"]}
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return {"errors": ["ragged grid"]}
    height = len(grid)
    if not (2 <= height <= 30 and 1 <= width <= 30):
        errors.append(f"grid dimensions must be within 2..30 by 1..30, got {height}x{width}")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        errors.append("grid cells must be exact integer ARC colors 0..9")
        return {"errors": errors, "grid_h": height, "grid_w": width}

    legend_positions = [c for c, value in enumerate(grid[0]) if value]
    legend_colors = [grid[0][c] for c in legend_positions]
    if not 2 <= len(legend_colors) <= 4:
        errors.append("legend must contain 2..4 nonzero colors")
    if len(set(legend_colors)) != len(legend_colors):
        errors.append("legend colors must be unique")
    if height > 1 and any(grid[1]):
        errors.append("row 1 must be a blank legend/body separator")

    components_by_color = _components(grid, start_row=1)
    body_colors = set(components_by_color)
    for color, comps in sorted(components_by_color.items()):
        if len(comps) != 1:
            errors.append(f"body color {color} must form exactly one component")
    for color in legend_colors:
        if color not in components_by_color:
            errors.append(f"legend color {color} has no body component")
        elif len(components_by_color[color]) != 1:
            errors.append(f"legend color {color} has ambiguous body components")

    widths: list[int] = []
    heights: list[int] = []
    for color in legend_colors:
        comps = components_by_color.get(color, [])
        if len(comps) == 1:
            cells = comps[0]
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            heights.append(max(rows) - min(rows) + 1)
            widths.append(max(cols) - min(cols) + 1)
    if widths and sum(widths) + len(widths) - 1 > 30:
        errors.append("selected crops would exceed the 30-column output bound")
    if heights and max(heights) > 30:
        errors.append("selected crop height exceeds the ARC bound")

    return {
        "errors": errors,
        "grid_h": height,
        "grid_w": width,
        "legend_positions": legend_positions,
        "legend_colors": legend_colors,
        "components_by_color": components_by_color,
        "body_colors": body_colors,
        "piece_count": len(legend_colors),
        "distractor_count": len(body_colors - set(legend_colors)),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    return list(analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, int]:
    analysis = analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "piece_count": analysis["piece_count"],
        "distractor_count": analysis["distractor_count"],
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _strict_overrides(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_int_diff("grid_h", 9, 30)
    width = ctx.draw_int_diff("grid_w", 12, 30)
    piece_count = ctx.draw_int_diff("piece_count", 2, 4)
    distractor_count = ctx.draw_int_diff("distractor_count", 1, 3)

    total = piece_count + distractor_count
    colors = list(ctx.draw_distinct_colors("scene_colors", n=total, exclude={0}))
    selected_colors = colors[:piece_count]
    distractor_colors = colors[piece_count:]

    shape_rng = ctx.draw_rng("shape_bank")
    shape_indices = list(range(len(_BASE_SHAPES)))
    shape_rng.shuffle(shape_indices)
    objects: list[tuple[int, tuple[tuple[int, int], ...]]] = []
    for index, color in enumerate(selected_colors + distractor_colors):
        base = _BASE_SHAPES[shape_indices[index % len(shape_indices)]]
        shape = _transform(base, shape_rng.randrange(8))
        objects.append((color, shape))

    grid = _place_objects(
        height,
        width,
        objects,
        ctx.draw_rng("body_layout"),
        int(sample_index) % 4,
    )

    legend_order = list(selected_colors)
    ctx.draw_rng("legend_order").shuffle(legend_order)
    positions = _legend_positions(width, piece_count, ctx.draw_rng("legend_positions"), int(sample_index) % 3)
    for position, color in zip(positions, legend_order):
        grid[0][position] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError("generated invalid lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    requested = ctx.overrides_used()
    for key, value in requested.items():
        if observed.get(key) != value:
            raise ValueError(f"override {key}={value!r} was not realized; observed {observed.get(key)!r}")
    return grid
