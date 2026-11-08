"""Generator for c658a4bd — restack colored layers as concentric squares.

For each nonzero color, the oracle keeps the 4-connected component with the
largest bounding-box span, treats that span as a square side length, sorts the
colors from largest to smallest, and paints centered square outlines in that
order.  Canonical inputs contain 4-5 distinct layers whose spans decrease by
two; frames may overlap, be split by later colors, or be clipped by an input
edge, and the smallest layer may be a solid 1x1 or 2x2 block.

The default distribution carries a linked prior over all three official input
archetypes (with color permutations and D4 transforms) and also emits broader
scattered, overlapping, and edge-clipped layouts.  Exact axes are limited to
observable quantities: square canvas size and the number of colored layers.
"""
from __future__ import annotations

from collections import defaultdict

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import (
    flip_lr as _grid_mirror_horizontal,
    full_grid,
    rot180,
    rot90_ccw,
    rot90_cw,
)

GENERATOR_ID = "8291f3ee7e54"
VERSION = "3.0.0"
TASK_ID = "8291f3ee7e54"
RULE_HASH = "d9bb03e0e2ec"
SUMMARY = (
    "Square 0-background grids with 3-5 distinct colored layers. Each color's "
    "largest 4-connected component has a unique bbox span; spans descend by "
    "two. Layers are hollow square/rectangular frame remnants, except a 1x1 "
    "or 2x2 innermost block. Layouts may be scattered, overlapping, or "
    "edge-clipped. The rule restacks the spans as centered concentric square "
    "outlines, largest outside."
)

INVARIANTS = [
    "square 12..22 canvas with background 0",
    "3..5 distinct nonzero colors, one answer-bearing layer per color",
    "largest per-color bbox spans are unique and descend by exactly two",
    "visible cells of each layer lie on one bbox border, except 1x1/2x2 blocks",
]

LAYOUT_KINDS = ("canonical", "scattered", "overlap", "clipped")
PALETTE_KINDS = ("warm", "cool", "primary", "broad")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_size": {
        "type": "int",
        "default": "difficulty-shaped 12..22; linked canonical prior uses 13/16/19",
        "valid": "12..22",
    },
    "n_layers": {
        "type": "int",
        "default": "difficulty-shaped 3..5; linked canonical prior uses 4/5",
        "valid": "3..5",
    },
    "layout_kind": {
        "type": "str",
        "default": "band-weighted; canonical prior about 35% in every band",
        "valid": "|".join(LAYOUT_KINDS),
    },
    "palette_kind": {
        "type": "str",
        "default": "keyed random palette family",
        "valid": "|".join(PALETTE_KINDS),
    },
}

# Each profile stores (side, top, left, kind) in descending semantic-layer
# order, followed by the drawing order.  These are complete linked structural
# archetypes, not independently recombined marginals.
_CANONICAL_PROFILES = (
    (
        16,
        (
            (9, 9, 5, "frame"),
            (7, 7, 1, "frame"),
            (5, 1, 3, "frame"),
            (3, 2, 10, "frame"),
            (1, 2, 0, "solid"),
        ),
        (2, 3, 1, 0, 4),
    ),
    (
        13,
        (
            (8, 4, 3, "frame"),
            (6, 1, 0, "frame"),
            (4, 1, 8, "frame"),
            (2, 9, 0, "solid"),
        ),
        (1, 0, 2, 3),
    ),
    (
        19,
        (
            (10, 1, 2, "frame"),
            (8, 5, 5, "frame"),
            (6, 3, 4, "frame"),
            (4, 14, 11, "frame"),
            (2, 2, 15, "solid"),
        ),
        (0, 1, 2, 3, 4),
    ),
)

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    unseen = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == color
    }
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        cells = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in _DIRS4:
                nxt = (r + dr, c + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    stack.append(nxt)
        result.append(cells)
    return result


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _component_signature(cells):
    r0, c0, r1, c1 = _bbox(cells)
    bh, bw = r1 - r0 + 1, c1 - c0 + 1
    return len(cells), min(bh, bw), max(bh, bw)


def _layer_analysis(grid):
    """Color-invariant structural facts used by self_check and census tests."""
    colors = sorted({value for row in grid for value in row if value != 0})
    layers = []
    for color in colors:
        components = _components(grid, color)
        infos = []
        for cells in components:
            r0, c0, r1, c1 = _bbox(cells)
            bh, bw = r1 - r0 + 1, c1 - c0 + 1
            infos.append(
                {
                    "cells": cells,
                    "cell_count": len(cells),
                    "bbox": (r0, c0, r1, c1),
                    "bbox_h": bh,
                    "bbox_w": bw,
                    "span": max(bh, bw),
                }
            )
        best = max(
            infos,
            key=lambda info: (info["span"], info["cell_count"], -info["bbox"][0], -info["bbox"][1]),
        )
        all_cells = [cell for info in infos for cell in info["cells"]]
        ur0, uc0, ur1, uc1 = _bbox(all_cells)
        layers.append(
            {
                "color": color,
                "span": best["span"],
                "best_bbox": best["bbox"],
                "best_cells": best["cell_count"],
                "union_bbox": (ur0, uc0, ur1, uc1),
                "union_span": max(ur1 - ur0 + 1, uc1 - uc0 + 1),
                "all_cells": all_cells,
                "component_signatures": tuple(
                    sorted(_component_signature(info["cells"]) for info in infos)
                ),
            }
        )
    layers.sort(key=lambda layer: (-layer["span"], layer["color"]))
    return layers


def structural_signature(grid):
    """Complete linked, color/D4-invariant morphology signature."""
    if not grid or not grid[0]:
        return None
    h, w = len(grid), len(grid[0])
    if h != w or any(len(row) != w for row in grid):
        return None
    layers = _layer_analysis(grid)
    return (
        h,
        tuple(
            (
                layer["span"],
                layer["best_cells"],
                layer["component_signatures"],
            )
            for layer in layers
        ),
    )


def _paint_shape_clipped(grid, top, left, height, width, color, kind):
    h, w = len(grid), len(grid[0])
    for r in range(top, top + height):
        for c in range(left, left + width):
            if not (0 <= r < h and 0 <= c < w):
                continue
            if kind == "solid" or (
                r in (top, top + height - 1)
                or c in (left, left + width - 1)
            ):
                grid[r][c] = color


def _render_profile(profile, colors):
    size, layers, draw_order = profile
    grid = full_grid(size, size, 0)
    for index in draw_order:
        side, top, left, kind = layers[index]
        _paint_shape_clipped(
            grid,
            top,
            left,
            side,
            side,
            colors[index],
            kind,
        )
    return grid


def _d4(grid, index):
    transforms = (
        lambda g: [row[:] for row in g],
        rot90_cw,
        rot180,
        rot90_ccw,
        _grid_mirror_horizontal,
        lambda g: rot90_cw(_grid_mirror_horizontal(g)),
        lambda g: rot180(_grid_mirror_horizontal(g)),
        lambda g: rot90_ccw(_grid_mirror_horizontal(g)),
    )
    return transforms[index % len(transforms)](grid)


def _profile_signature(profile):
    colors = tuple(range(1, len(profile[1]) + 1))
    return structural_signature(_render_profile(profile, colors))


_CANONICAL_SIGNATURES = frozenset(
    _profile_signature(profile) for profile in _CANONICAL_PROFILES
)


def canonical_profile_signature(grid):
    signature = structural_signature(grid)
    return signature if signature in _CANONICAL_SIGNATURES else None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the semantic input grammar, including canonical occlusions."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["empty grid"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["ragged grid"]
    height = len(grid)
    errors = []
    if height != width or not 12 <= height <= 22:
        errors.append(f"expected square 12..22 grid; got {height}x{width}")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid values must be integer ARC colors 0..9")
        return errors
    colors = {value for row in grid for value in row if value != 0}
    if not 3 <= len(colors) <= 5:
        errors.append(f"expected 3..5 nonzero layer colors; found {len(colors)}")
        return errors
    layers = _layer_analysis(grid)
    spans = [layer["span"] for layer in layers]
    if any(a - b != 2 for a, b in zip(spans, spans[1:])):
        errors.append(f"layer spans must descend by two; found {spans}")
    for index, layer in enumerate(layers):
        span = layer["span"]
        if layer["union_span"] != span:
            errors.append(
                f"layer {index} color {layer['color']} has disconnected cells outside its primary span"
            )
            continue
        r0, c0, r1, c1 = layer["union_bbox"]
        cells = layer["all_cells"]
        if span <= 2:
            expected = (r1 - r0 + 1) * (c1 - c0 + 1)
            if len(cells) != expected:
                errors.append(
                    f"small layer {index} must be a solid 1x1/2x2 block"
                )
        else:
            if any(r not in (r0, r1) and c not in (c0, c1) for r, c in cells):
                errors.append(
                    f"layer {index} contains cells away from its bbox border"
                )
            if len(cells) < 2 * span - 2:
                errors.append(
                    f"layer {index} is too fragmentary for span {span}: {len(cells)} cells"
                )
    return errors


def observe_overrides(grid) -> dict:
    """Exact semantic axes recovered from the returned grid itself."""
    return {"n_layers": len({value for row in grid for value in row if value != 0})}


def _draw_banded_layout(ctx):
    explicit = ctx.overrides.get("layout_kind")
    if explicit is not None:
        return ctx.draw_choice("layout_kind", LAYOUT_KINDS)
    weights = {
        "easy": (0.38, 0.38, 0.16, 0.08),
        "medium": (0.35, 0.27, 0.24, 0.14),
        "hard": (0.34, 0.18, 0.29, 0.19),
    }.get(ctx.difficulty, (0.35, 0.27, 0.24, 0.14))
    requested_size = ctx.overrides.get("grid_size")
    requested_layers = ctx.overrides.get("n_layers")
    canonical_possible = any(
        (requested_size is None or profile[0] == int(requested_size))
        and (requested_layers is None or len(profile[1]) == int(requested_layers))
        for profile in _CANONICAL_PROFILES
    )
    choices = LAYOUT_KINDS if canonical_possible else LAYOUT_KINDS[1:]
    choice_weights = weights if canonical_possible else weights[1:]
    value = ctx.draw_rng("layout_kind").choices(
        choices,
        weights=choice_weights,
        k=1,
    )[0]
    ctx._draw_options["layout_kind"] = tuple(choices)
    return ctx._record("layout_kind", value, from_override=False)


def _record_profile_axis(ctx, label, value, lo, hi):
    ctx._draw_bounds[label] = (lo, hi)
    requested = ctx.overrides.get(label)
    if requested is not None:
        requested = int(requested)
        if not lo <= requested <= hi:
            raise ValueError(f"{label} override {requested} outside [{lo}, {hi}]")
        if requested != value:
            raise ValueError(
                f"layout_kind='canonical' has no linked profile with {label}={requested}"
            )
        return ctx._record(label, value, from_override=True)
    return ctx._record(label, value, from_override=False)


def _palette(kind, count, rng):
    pools = {
        "warm": [2, 3, 4, 6, 9],
        "cool": [1, 5, 7, 8, 9],
        "primary": [1, 2, 3, 4, 6],
        "broad": [1, 2, 3, 4, 5, 6, 7, 8, 9],
    }
    values = pools[kind][:]
    rng.shuffle(values)
    return values[:count]


def _choose_profile(ctx, rng):
    requested_size = ctx.overrides.get("grid_size")
    requested_layers = ctx.overrides.get("n_layers")
    candidates = [
        profile
        for profile in _CANONICAL_PROFILES
        if (requested_size is None or profile[0] == int(requested_size))
        and (requested_layers is None or len(profile[1]) == int(requested_layers))
    ]
    if not candidates:
        raise ValueError(
            "layout_kind='canonical' is incompatible with the requested grid_size/n_layers"
        )
    profile = rng.choice(candidates)
    _record_profile_axis(ctx, "grid_size", profile[0], 12, 22)
    _record_profile_axis(ctx, "n_layers", len(profile[1]), 3, 5)
    return profile


def _layer_sizes(grid_size, n_layers, rng):
    minimum = 2 * n_layers - 1
    maximum = min(11, grid_size - 1)
    if minimum > maximum:
        raise ValueError(
            f"cannot fit {n_layers} nested layer spans in grid_size={grid_size}"
        )
    largest = rng.randint(minimum, maximum)
    return [largest - 2 * index for index in range(n_layers)]


def _shape_dims(side, mode, rng):
    if side <= 2:
        return side, side, "solid"
    if mode == "overlap" and side >= 5 and rng.random() < 0.28:
        short = rng.randint(max(3, side - 3), side - 1)
        return (side, short, "frame") if rng.random() < 0.5 else (short, side, "frame")
    return side, side, "frame"


def _position_for(mode, grid_size, shape_h, shape_w, index, anchors, rng):
    if mode == "clipped" and index == 0:
        amount = rng.randint(1, min(2, shape_h - 2))
        if rng.random() < 0.5:
            top = -amount
            left = rng.randint(0, grid_size - shape_w)
        else:
            top = grid_size - shape_h + amount
            left = rng.randint(0, grid_size - shape_w)
        return top, left
    if mode == "overlap" and anchors:
        base_r, base_c = anchors[0]
        top = int(max(0, min(grid_size - shape_h, round(base_r + rng.randint(-2, 2)))))
        left = int(max(0, min(grid_size - shape_w, round(base_c + rng.randint(-2, 2)))))
        return top, left
    candidates = [
        (rng.randint(0, grid_size - shape_h), rng.randint(0, grid_size - shape_w))
        for _ in range(32)
    ]
    if not anchors:
        return candidates[0]
    def score(pos):
        pr, pc = pos
        center = (pr + shape_h / 2, pc + shape_w / 2)
        return min(
            abs(center[0] - ar) + abs(center[1] - ac)
            for ar, ac in anchors
        )
    return max(candidates, key=score)


def _general_candidate(grid_size, sizes, colors, mode, rng):
    grid = full_grid(grid_size, grid_size, 0)
    if mode == "clipped":
        amount = rng.randint(1, 2)
        outer = sizes[0]
        top = -amount if rng.random() < 0.5 else grid_size - outer + amount
        left = (grid_size - outer) // 2
        for side, color in zip(reversed(sizes[1:]), reversed(colors[1:])):
            inner_top = (grid_size - side) // 2
            inner_left = (grid_size - side) // 2
            kind = "solid" if side <= 2 else "frame"
            _paint_shape_clipped(
                grid, inner_top, inner_left, side, side, color, kind
            )
        _paint_shape_clipped(grid, top, left, outer, outer, colors[0], "frame")
        return _d4(grid, rng.randrange(8))

    specs = []
    anchors = []
    for index, (side, color) in enumerate(zip(sizes, colors)):
        shape_h, shape_w, kind = _shape_dims(side, mode, rng)
        top, left = _position_for(
            mode,
            grid_size,
            shape_h,
            shape_w,
            index,
            anchors,
            rng,
        )
        specs.append((top, left, shape_h, shape_w, color, kind))
        anchors.append((top + shape_h / 2, left + shape_w / 2))
    order = list(range(len(specs)))
    if mode == "overlap":
        rng.shuffle(order)
    for index in order:
        top, left, shape_h, shape_w, color, kind = specs[index]
        _paint_shape_clipped(
            grid,
            top,
            left,
            shape_h,
            shape_w,
            color,
            kind,
        )
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    layout_kind = _draw_banded_layout(ctx)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    palette_rng = ctx.draw_rng("palette")
    layout_rng = ctx.draw_rng("layout")

    if layout_kind == "canonical":
        profile = _choose_profile(ctx, layout_rng)
        colors = _palette(palette_kind, len(profile[1]), palette_rng)
        grid = _render_profile(profile, colors)
        return _d4(grid, ctx.draw_rng("d4").randrange(8))

    grid_size = ctx.draw_int_diff("grid_size", 12, 22)
    n_layers = ctx.draw_int_diff("n_layers", 3, 5)
    colors = _palette(palette_kind, n_layers, palette_rng)
    sizes = _layer_sizes(grid_size, n_layers, ctx.draw_rng("layer_sizes"))
    for _ in range(240):
        candidate = _general_candidate(
            grid_size,
            sizes,
            colors,
            layout_kind,
            layout_rng,
        )
        if (
            not self_check(candidate, difficulty=difficulty)
            and observe_overrides(candidate)["n_layers"] == n_layers
        ):
            return candidate
    raise ValueError(
        f"unable to realize layout_kind={layout_kind!r}, grid_size={grid_size}, n_layers={n_layers}"
    )
