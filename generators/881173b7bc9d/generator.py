"""Sample complete monochromatic frames for the unchanged Racket authority.

Objects are FOUR-connected components of a single nonzero color. Only a full
rectangular perimeter qualifies; damaged rings and their contents are ignored.
The reference crops interiors, orders by left edge, and packs at the top with
one zero column between them. Python packing below is a tested diagnostic for
rivals, never the source of generated labels.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "881173b7bc9d"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "b87fde7ab095"
SUMMARY = (
    "Extract intact four-connected monochromatic frame interiors, order by "
    "left edge, and concatenate with one zero column and top alignment. "
    "Sample damaged distractors, diagonal same-color contacts, multicolor "
    "contents, canonical profiles, and broader frame counts and dimensions."
)
INVARIANTS = [
    "ordinary draws have 2..5 intact monochromatic rectangular frames",
    "nonzero cells are contained in intact frames or recognizable broken-ring boxes",
    "diagonal same-color contact is allowed; four-connected border attachments are not",
    "the palette has exactly the declared mode's colors; interiors exclude all border colors",
    "grid_h and n_frames overrides are exact in every difficulty band",
]
HELPFUL_TEXTURES = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ()
AXES = {
    "grid_h": {"type": "int", "default": "canonical 8..10 with a broader 7..18 branch", "valid": "7..18"},
    "n_frames": {"type": "int", "default": "2..3 core; up to 5 in broad draws", "valid": "1..5"},
    "palette_kind": {"type": "str", "default": "default or varied, with warm/cool broad support",
                     "valid": "default|warm|cool|varied"},
    "density": {"type": "str", "default": "sparse easy; mixed medium; dense hard", "valid": "sparse|dense"},
    "texture": {"type": "str", "default": "alias for palette_kind", "valid": "default|warm|cool|varied"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"palette_kind": left, "texture": right}
    for left in HELPFUL_TEXTURES for right in HELPFUL_TEXTURES if left != right
]
EXAMPLES_NEEDED = 4
# The core layout cycles through four phases. Broader topology and palettes
# also depend on the full sample index, so no finite semantic period is claimed.
MIN_STRICT_FRAC = 1.0
_WARM = (2, 4, 6, 8, 9)
_COOL = (1, 3, 5, 7, 8)


def _components(grid, *, connectivity=4, group_by_color=False):
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    offsets = ((-1, 0), (0, -1), (0, 1), (1, 0))
    if connectivity == 8:
        offsets += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    components = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        if group_by_color:
            cells = {p for p in remaining if grid[p[0]][p[1]] == color}
            remaining.difference_update(cells)
        else:
            cells, stack = set(), [start]
            remaining.remove(start)
            while stack:
                r, c = stack.pop()
                cells.add((r, c))
                for dr, dc in offsets:
                    p = (r + dr, c + dc)
                    if p in remaining and grid[p[0]][p[1]] == color:
                        remaining.remove(p)
                        stack.append(p)
        components.append({"r1": min(r for r, c in cells), "c1": min(c for r, c in cells),
                        "r2": max(r for r, c in cells), "c2": max(c for r, c in cells),
                        "color": color, "cells": cells})
    return components


def _ring(obj, *, broken=False):
    h, w = obj["r2"] - obj["r1"] + 1, obj["c2"] - obj["c1"] + 1
    if h < 3 or w < 3:
        return False
    perimeter = 2 * h + 2 * w - 4
    on_border = all(r in (obj["r1"], obj["r2"]) or c in (obj["c1"], obj["c2"])
                    for r, c in obj["cells"])
    return on_border and (len(obj["cells"]) == perimeter or
                          (broken and 3 * perimeter <= 5 * len(obj["cells"]) < 5 * perimeter))


def _frames(grid, *, connectivity=4, group_by_color=False):
    return sorted((o for o in _components(grid, connectivity=connectivity,
                                         group_by_color=group_by_color) if _ring(o)),
                  key=lambda o: o["c1"])


def _pack(grid, frames, *, gap=1, bottom=False, uniform=False):
    """Diagnostic mirror; every retained authority comparison uses real Racket."""
    if not frames:
        return [[0]]
    height = max(o["r2"] - o["r1"] - 1 for o in frames)
    width = sum(o["c2"] - o["c1"] - 1 for o in frames) + gap * (len(frames) - 1)
    out = full_grid(height, width, 0)
    left = 0
    for obj in frames:
        sub = [row[obj["c1"] + 1:obj["c2"]] for row in grid[obj["r1"] + 1:obj["r2"]]]
        counts = Counter(v for row in sub for v in row if v)
        main = min(counts, key=lambda v: (-counts[v], v)) if counts else 0
        top = height - len(sub) if bottom else 0
        for r, row in enumerate(sub):
            for c, value in enumerate(row):
                out[top + r][left + c] = main if uniform and value else value
        left += len(sub[0]) + gap
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) and row for row in grid):
        return ["expected a nonempty list of nonempty rows"]
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30 or any(len(row) != w for row in grid):
        return ["expected a rectangular grid within 30 by 30"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["colors must be Python integers 0..9, excluding booleans"]
    components = _components(grid)
    if not any(_ring(o) for o in components):
        return ["no intact rectangular frame"]
    boxes = [o for o in components if _ring(o, broken=True)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value and not any(o["r1"] <= r <= o["r2"] and o["c1"] <= c <= o["c2"] for o in boxes):
                return [f"unexplained nonzero cell outside intact or broken frame boxes at ({r},{c})"]
    return []


def strict_canonical_like(grid):
    errors = self_check(grid)
    if not errors and len(_frames(grid)) < 2:
        errors.append("ordinary training support requires at least two intact frames")
    return errors


def _exact_int(ctx, name, default, lo, hi):
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, (default,))


def _rect(r, c, h, w, role, valid=True):
    return {"r1": r, "c1": c, "r2": r + h - 1, "c2": c + w - 1,
            "role": role, "valid": valid}


def _layout(phase, h, count, rng):
    """Construction order matters only when a later frame overwrites a border."""
    if phase == 0:
        base_h, base_w = 8, 12
        rects = [_rect(0, 0, 4, 5, 0), _rect(1, 7, 5, 4, 1)]
    elif phase == 1:
        base_h, base_w = 10, 14
        rects = [_rect(0, 0, 5, 5, 0), _rect(5, 5, 4, 6, 0), _rect(0, 8, 4, 4, 1)]
    elif phase == 2:
        base_h, base_w = 9, 13
        rects = [_rect(1, 0, 4, 4, 0), _rect(0, 5, 5, 5, 2, False), _rect(4, 8, 4, 5, 1)]
    else:
        base_h, base_w = 10, 13
        rects = [_rect(0, 0, 5, 4, 1, False), _rect(4, 0, 6, 4, 0), _rect(0, 4, 4, 6, 0)]
    if h < base_h or count < sum(o["valid"] for o in rects):
        if count == 1:
            base_h, base_w = 4, 9
            rects = [_rect(0, 0, 4, 7, 0)]
        elif phase >= 2:
            base_h, base_w = 7, 10
            rects = [_rect(0, 0, 4, 4, 1, False), _rect(3, 0, 4, 4, 0),
                     _rect(0, 4, 3, 5, 0 if phase == 3 else 2)]
        elif phase == 1:
            base_h, base_w = 7, 10
            rects = [_rect(0, 0, 3, 4, 0), _rect(3, 4, 4, 5, 0)]
        else:
            base_h, base_w = 5, 12
            rects = [_rect(0, 0, 4, 5, 0), _rect(0, 7, 5, 4, 1)]
    row_shift = rng.randint(0, h - base_h)
    for obj in rects:
        obj["r1"] += row_shift
        obj["r2"] += row_shift
    width = base_w
    for _ in range(count - sum(o["valid"] for o in rects)):
        fh = rng.randint(3, min(h, 6))
        # Leave a zero column even when a core border occupies its last column.
        rects.append(_rect(rng.randint(0, h - fh), width + 1, fh, 3, 1))
        width += 4
    return rects, width


def _paint(grid, rects, palette, density, rng):
    roles = sorted({o["role"] for o in rects})
    border = dict(zip(roles, palette))
    interior_colors = list(palette[len(roles):])
    for obj in rects:
        color = border[obj["role"]]
        for r in range(obj["r1"], obj["r2"] + 1):
            for c in range(obj["c1"], obj["c2"] + 1):
                if r in (obj["r1"], obj["r2"]) or c in (obj["c1"], obj["c2"]):
                    grid[r][c] = color
    available = set()
    selected = set()
    for obj in rects:
        cells = [(r, c) for r in range(obj["r1"] + 1, obj["r2"])
                 for c in range(obj["c1"] + 1, obj["c2"]) if grid[r][c] == 0]
        if not cells:
            continue
        available.update(cells)
        rate = 0.35 if density == "sparse" else 0.8
        n = min(len(cells), max(2, round(len(cells) * rate)))
        chosen = rng.sample(cells, n)
        colors = rng.sample(interior_colors, len(interior_colors))
        for i, (r, c) in enumerate(chosen):
            grid[r][c] = colors[i % len(colors)]
            selected.add((r, c))
    # Realize the whole requested palette even for the one-frame boundary.
    # Reserve enough distinct interior cells and assign each fill color once.
    if len(selected) < len(interior_colors):
        extra = rng.sample(sorted(available - selected), len(interior_colors) - len(selected))
        selected.update(extra)
    present = {grid[r][c] for r, c in selected}
    missing = [v for v in interior_colors if v not in present]
    for color in missing:
        counts = Counter(grid[r][c] for r, c in selected)
        candidates = [p for p in sorted(selected) if grid[p[0]][p[1]] == 0 or counts[grid[p[0]][p[1]]] > 1]
        r, c = rng.choice(candidates)
        grid[r][c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    left, right = overrides.get("palette_kind"), overrides.get("texture")
    if left is not None and right is not None and left != right:
        raise ValueError("incompatible palette_kind and texture aliases")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    phase = sample_index % 4
    broad = ctx.draw_rng("scale_profile").randrange(4) == 0
    base_h, base_count = ((8, 2), (10, 3), (9, 2), (10, 2))[phase]
    h_default = ctx.draw_rng("broad_height").randint(base_h, 18) if broad else base_h
    count_default = ctx.draw_rng("broad_count").randint(base_count, 5) if broad else base_count
    h = _exact_int(ctx, "grid_h", h_default, 7, 18)
    count = _exact_int(ctx, "n_frames", count_default, 1, 5)
    anchor_kind = "default" if phase == 0 else "varied"
    kinds = HELPFUL_TEXTURES if broad else (anchor_kind,)
    requested = left if left is not None else right
    if requested is not None:
        if requested not in HELPFUL_TEXTURES:
            raise ValueError(f"unsupported palette/texture {requested!r}")
        kinds = (requested,)
    kind = ctx.draw_choice("palette_kind", kinds)
    ctx.draw_choice("texture", (kind,))
    density_choices = ("sparse",) if difficulty == "easy" else (("dense",) if difficulty == "hard" else ("sparse", "dense"))
    if overrides.get("density") is not None:
        density_choices = ("sparse", "dense")
    density = ctx.draw_choice("density", density_choices)
    palette_rng = ctx.draw_rng("palette")
    if kind == "warm":
        palette = palette_rng.sample(_WARM, len(_WARM))
    elif kind == "cool":
        palette = palette_rng.sample(_COOL, len(_COOL))
    else:
        palette = palette_rng.sample(range(1, 10), 4 if kind == "default" else 6)
    rects, width = _layout(phase, h, count, ctx.draw_rng("layout"))
    grid = full_grid(h, width, 0)
    _paint(grid, rects, palette, density, ctx.draw_rng("contents"))
    if len(_frames(grid)) != count:
        raise RuntimeError("constructed frame count differs from requested count")
    errors = self_check(grid)
    if errors:
        raise RuntimeError("constructed grid violates frame domain: " + "; ".join(errors))
    return grid


def observe_overrides(grid):
    colors = {v for row in grid for v in row if v}
    if colors == set(_WARM):
        kind = "warm"
    elif colors == set(_COOL):
        kind = "cool"
    elif len(colors) == 4:
        kind = "default"
    elif len(colors) == 6:
        kind = "varied"
    else:
        kind = "outside_declared_palette_modes"
    return {"grid_h": len(grid), "n_frames": len(_frames(grid)),
            "palette_kind": kind, "texture": kind}


def _global_color(grid):
    return _pack(grid, _frames(grid, group_by_color=True))


def _eight_connected(grid):
    return _pack(grid, _frames(grid, connectivity=8))


def _include_broken(grid):
    return _pack(grid, sorted((o for o in _components(grid) if _ring(o, broken=True)), key=lambda o: o["c1"]))


def _row_major(grid):
    return _pack(grid, sorted(_frames(grid), key=lambda o: (o["r1"], o["c1"])))


def _uniform_interior(grid):
    return _pack(grid, _frames(grid), uniform=True)


def _no_gap(grid):
    return _pack(grid, _frames(grid), gap=0)


def _bottom_align(grid):
    return _pack(grid, _frames(grid), bottom=True)


SEMANTIC_RIVALS = {
    "global_color": _global_color,
    "eight_connected": _eight_connected,
    "include_broken": _include_broken,
    "row_major": _row_major,
    "uniform_interior": _uniform_interior,
    "no_gap": _no_gap,
    "bottom_align": _bottom_align,
}
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name] for name in
                       ("global_color", "eight_connected", "uniform_interior")}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    name: (lambda grid, rival=rival: rival(grid) != _pack(grid, _frames(grid)))
    for name, rival in SEMANTIC_RIVALS.items()
}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}
