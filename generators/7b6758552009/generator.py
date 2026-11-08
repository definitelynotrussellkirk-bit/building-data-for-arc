"""One palette entry per component, ordered by (leftmost column, top row).

Four interleaved lessons retain ordinary separated scenes and independently
exercise repeated colors, column ties, and overlapping horizontal projections.
The unchanged canonical Racket program remains the label authority.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "7b6758552009"
VERSION = "3.0.0"
RULE_HASH = "8afe6f5b77dd"
EXAMPLES_NEEDED = 4
SUMMARY = (
    "Zero-background grid with 2-5 separated monochromatic 4-connected blobs "
    "of 1-5 cells. Colors may repeat across disconnected blobs. Emit one color "
    "per component, sorted by its leftmost column then its top row. Sampling "
    "mixes separated columns, randomized left-column ties, repeated colors, "
    "and crossing horizontal projections; dimensions span 6-12 by 10-18."
)
INVARIANTS = [
    "background is 0; cells are integer colors 0..9",
    "at least two monochromatic 4-connected components, each of 1-5 cells",
    "different components have at least one background cell between them",
    "repeated colors remain separate components and separate output entries",
    "output order uses minimum column, then minimum row of each component",
]
AXES = {
    "grid_h": {"type": "int", "default": "band-dependent 6..12", "valid": "6..12"},
    "grid_w": {"type": "int", "default": "band-dependent 10..18", "valid": "10..18"},
    "components": {"type": "int", "default": "band-dependent 2..5", "valid": "2..5"},
    "color_policy": {"type": "str", "default": "scheduled distinct or repeated", "valid": "distinct|repeated"},
    "layout": {"type": "str", "default": "scheduled separated, tied or crossing", "valid": "separated|tied|crossing"},
}
SCHEDULE_PROFILES = ("canonical", "repeat", "tie", "crossing")


def schedule_profile(seed, sample_index, difficulty=None):
    """Every four consecutive indices cover the same four semantic profiles."""
    return SCHEDULE_PROFILES[((seed ^ (seed >> 1)) + sample_index) % len(SCHEDULE_PROFILES)]


def _components(grid):
    """Monochromatic 4-connectivity, with bounding-box coordinates."""
    seen = set()
    result = []
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if not color or (r, c) in seen:
                continue
            pending = [(r, c)]
            seen.add((r, c))
            cells = []
            while pending:
                rr, cc = pending.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            result.append({"color": color, "cells": tuple(sorted(cells)),
                           "left": min(cc for rr, cc in cells),
                           "top": min(rr for rr, cc in cells),
                           "right": max(cc for rr, cc in cells)})
    return sorted(result, key=lambda obj: (obj["left"], obj["top"]))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Check the scene grammar, not just the number of nonzero pixels.

The sampler's dimension/count bounds are not input-validity requirements.
Small lawful counterexamples and repeated-color scenes remain admissible.
"""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["empty or non-sequence grid"]
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return ["rows must be sequences"]
    w = len(grid[0])
    if not w or any(len(row) != w for row in grid):
        return ["empty or ragged grid"]
    if len(grid) > 30 or w > 30:
        return ["grid exceeds ARC size bound 30"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integer colors 0..9 (not booleans)"]
    blobs = _components(grid)
    if not 2 <= len(blobs) <= 30:
        return [f"expected 2..30 separated components; found {len(blobs)}"]
    if any(len(obj["cells"]) > 5 for obj in blobs):
        return ["component exceeds the 1..5-cell blob grammar"]
    owner = {cell: i for i, obj in enumerate(blobs) for cell in obj["cells"]}
    for (r, c), i in owner.items():
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if owner.get((r + dr, c + dc), i) != i:
                    return ["different components touch without a background gap"]
    return []


def rule_mirror(grid):
    """Diagnostic Python mirror only; production labels still use Racket."""
    findings = self_check(grid)
    if findings:
        raise ValueError("; ".join(findings))
    return [[obj["color"] for obj in _components(grid)]]


def _normalize(cells):
    r0, c0 = min(r for r, c in cells), min(c for r, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _shape_library():
    """All oriented polyominoes with 1..5 cells, not five fixed templates."""
    level = {((0, 0),)}
    shapes = set(level)
    for _ in range(4):
        following = set()
        for shape in level:
            occupied = set(shape)
            for r, c in shape:
                for cell in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if cell not in occupied:
                        following.add(_normalize(occupied | {cell}))
        shapes.update(following)
        level = following
    return tuple(sorted(shapes, key=lambda shape: (len(shape), shape)))


_SHAPES = _shape_library()


def _shape(rng, max_h, max_w):
    available = [shape for shape in _SHAPES
                 if max(r for r, c in shape) < max_h and max(c for r, c in shape) < max_w]
    sizes = sorted({len(shape) for shape in available})
    size = rng.choice(sizes)
    return rng.choice([shape for shape in available if len(shape) == size])


def _height(shape):
    return max(r for r, c in shape) + 1


def _width(shape):
    return max(c for r, c in shape) + 1


def _shift(shape, row, col):
    return tuple((r + row, c + col) for r, c in shape)


def _free(grid, cells):
    h, w = len(grid), len(grid[0])
    return all(
        0 <= r < h and 0 <= c < w and all(
            not grid[rr][cc]
            for rr in range(max(0, r - 1), min(h, r + 2))
            for cc in range(max(0, c - 1), min(w, c + 2))
        ) for r, c in cells
    )


def _mark(grid, cells):
    for r, c in cells:
        grid[r][c] = 1


def _separated(rng, h, w, count):
    widths = [1] * count
    gaps = [0] + [1] * (count - 1) + [0]
    for _ in range(w - (2 * count - 1)):
        slot = rng.randrange(2 * count + 1)
        if slot < count and widths[slot] < 5:
            widths[slot] += 1
        else:
            gaps[rng.randrange(count + 1)] += 1
    result, col = [], gaps[0]
    for i, available_width in enumerate(widths):
        shape = _shape(rng, h, available_width)
        left = col + rng.randrange(available_width - _width(shape) + 1)
        top = rng.randrange(h - _height(shape) + 1)
        result.append(_shift(shape, top, left))
        col += available_width + gaps[i + 1]
    return result


def _special(rng, h, w, count, layout):
    """Randomized two-object witness, with free-position additional blobs.

A bounded redraw handles occupied-space conflicts; there is no silent short
batch and no fallback to a different semantic profile.
"""
    for _ in range(80):
        split = rng.randint(2, h - 3)
        if layout == "tied":
            top_shape = _shape(rng, split, min(5, w))
            bottom_shape = _shape(rng, h - split - 1, min(5, w))
            left = rng.randrange(w - max(_width(top_shape), _width(bottom_shape)) + 1)
            top_left = bottom_left = left
        else:
            bar = tuple((0, c) for c in range(rng.randint(4, 5)))
            # Short blob fits strictly inside the long bar's column interval.
            inner = _shape(rng, 2, 2)
            left = rng.randrange(w - _width(bar) + 1)
            inner_left = left + rng.randint(1, _width(bar) - _width(inner) - 1)
            if rng.randrange(2):
                top_shape, bottom_shape = bar, inner
                top_left, bottom_left = left, inner_left
            else:
                top_shape, bottom_shape = inner, bar
                top_left, bottom_left = inner_left, left
        top = rng.randrange(split - _height(top_shape) + 1)
        bottom = rng.randint(split + 1, h - _height(bottom_shape))
        result = [_shift(top_shape, top, top_left), _shift(bottom_shape, bottom, bottom_left)]
        occupied = full_grid(h, w, 0)
        for cells in result:
            _mark(occupied, cells)
        used_left = {min(c for r, c in cells) for cells in result}
        while len(result) < count:
            candidate = None
            for _ in range(48):
                shape = _shape(rng, min(h, 4), min(w, 4))
                row = rng.randrange(h - _height(shape) + 1)
                col = rng.randrange(w - _width(shape) + 1)
                cells = _shift(shape, row, col)
                if col not in used_left and _free(occupied, cells):
                    candidate = cells
                    break
            if candidate is None:
                singles = [((r, c),) for r in range(h) for c in range(w)
                           if c not in used_left and _free(occupied, ((r, c),))]
                if not singles:
                    break
                candidate = rng.choice(singles)
            result.append(candidate)
            used_left.add(min(c for r, c in candidate))
            _mark(occupied, candidate)
        if len(result) == count:
            return result
    raise ValueError(f"cannot place layout={layout!r}, components={count}, grid={h}x{w}")


def _draw_int(ctx, name, bounds, band_bounds):
    lo, hi = bounds if name in ctx.overrides else band_bounds
    return ctx.draw_int(name, lo, hi)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(sorted(unknown))}")
    overrides = {name: value for name, value in overrides.items() if value is not None}
    for name, value in overrides.items():
        if AXES[name]["type"] == "int" and type(value) is not int:
            raise TypeError(f"{name} override must be an integer")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        bh, bw, bn = (6, 8), (10, 14), (2, 4)
    elif difficulty == "hard":
        bh, bw, bn = (8, 12), (12, 18), (3, 5)
    else:
        bh, bw, bn = (6, 10), (10, 16), (2, 5)
    profile = schedule_profile(seed, sample_index, difficulty)
    if profile == "canonical":
        # Preserve the observed size/count regime without copying any grid,
        # palette or coordinates. Other profiles retain the broader support.
        ch, cw, cn = ctx.draw_rng("canonical_scale").choice(
            ((6, 11, 2), (7, 10, 3), (8, 12, 3), (9, 13, 4)))
        bh, bw, bn = (ch, ch), (cw, cw), (cn, cn)
    h = _draw_int(ctx, "grid_h", (6, 12), bh)
    w = _draw_int(ctx, "grid_w", (10, 18), bw)
    count = _draw_int(ctx, "components", (2, 5), bn)
    default_layout = {"canonical": "separated", "repeat": "separated", "tie": "tied", "crossing": "crossing"}[profile]
    default_policy = "repeated" if profile == "repeat" else "distinct"
    layout = ctx.draw_choice("layout", ("separated", "tied", "crossing") if "layout" in overrides else (default_layout,))
    policy = ctx.draw_choice("color_policy", ("distinct", "repeated") if "color_policy" in overrides else (default_policy,))
    rng = ctx.draw_rng("geometry:" + str(difficulty))
    cells = _separated(rng, h, w, count) if layout == "separated" else _special(rng, h, w, count, layout)
    color_rng = ctx.draw_rng("colors")
    n_colors = count if policy == "distinct" else color_rng.randint(1, count - 1)
    palette = color_rng.sample(list(range(1, 10)), n_colors)
    colors = palette + [color_rng.choice(palette) for _ in range(count - n_colors)]
    color_rng.shuffle(colors)
    grid = full_grid(h, w, 0)
    for component, color in zip(cells, colors):
        for r, c in component:
            grid[r][c] = color
    return grid


def observe_overrides(grid):
    blobs = _components(grid)
    if len({obj["left"] for obj in blobs}) < len(blobs):
        layout = "tied"
    elif sorted(blobs, key=lambda obj: (obj["right"], obj["top"])) != blobs:
        layout = "crossing"
    else:
        layout = "separated"
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "components": len(blobs),
            "color_policy": "distinct" if len({obj["color"] for obj in blobs}) == len(blobs) else "repeated",
            "layout": layout}


def strict_canonical_like(grid) -> list[str]:
    """Lawful written-rule manifold; does not require canonical coordinates."""
    return self_check(grid)


def _unique_colors(grid):
    # Deliberately no flood fill: this is the strongest canonical-compatible
    # shortcut, treating a color as an object even when it is disconnected.
    positions = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                positions.setdefault(value, []).append((r, c))
    return [sorted(positions, key=lambda value: (
        min(c for r, c in positions[value]), min(r for r, c in positions[value])
    ))]


def _one_per_column(grid):
    seen, colors = set(), []
    for obj in _components(grid):
        if obj["left"] not in seen:
            seen.add(obj["left"])
            colors.append(obj["color"])
    return [colors]


def _bottom_first_ties(grid):
    return [[obj["color"] for obj in sorted(_components(grid), key=lambda obj: (obj["left"], -obj["top"]))]]


def _right_edge_order(grid):
    return [[obj["color"] for obj in sorted(_components(grid), key=lambda obj: (obj["right"], obj["top"]))]]


SEMANTIC_RIVALS = {
    "unique_colors": _unique_colors,
    "one_per_left_column": _one_per_column,
    "bottom_first_ties": _bottom_first_ties,
    "right_edge_order": _right_edge_order,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _disagrees(grid, name):
    return not self_check(grid) and SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "repeated_color_components": lambda grid: _disagrees(grid, "unique_colors"),
    "multiple_components_in_one_column": lambda grid: _disagrees(grid, "one_per_left_column"),
    "visible_top_row_tiebreak": lambda grid: _disagrees(grid, "bottom_first_ties"),
    "right_edge_is_not_left_edge": lambda grid: _disagrees(grid, "right_edge_order"),
}
WITNESS_RIVALS = {
    "repeated_color_components": ["unique_colors"],
    "multiple_components_in_one_column": ["one_per_left_column"],
    "visible_top_row_tiebreak": ["bottom_first_ties"],
    "right_edge_is_not_left_edge": ["right_edge_order"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Relative to the four declared competitors, not all possible programs."""
    reasons = []
    try:
        for index, demo in enumerate(demos):
            if demo.get("output") != rule_mirror(demo["input"]):
                reasons.append(f"demo {index} output disagrees with component rule")
        expected = rule_mirror(query["input"])
        if "output" in query and query["output"] != expected:
            reasons.append("query output disagrees with component rule")
    except (KeyError, TypeError, ValueError) as exc:
        return [f"invalid lesson: {exc}"]
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if (all(rival(demo["input"]) == demo["output"] for demo in demos)
                and rival(query["input"]) != expected):
            reasons.append(f"rival {name!r} fits all demonstrations but changes the query answer")
    return reasons


def mutation_fixtures():
    return [
        ("blank", [[0] * 10 for _ in range(6)]),
        ("one_solid_object", [[3] * 10 for _ in range(6)]),
        ("single_component", [[0, 3, 3, 0]]),
        ("touching_colors", [[0, 3, 4, 0]]),
        ("diagonal_contact", [[3, 0], [0, 4]]),
        ("invalid_color", [[3, 0, 11]]),
        ("boolean_cell", [[3, 0, True]]),
    ]
