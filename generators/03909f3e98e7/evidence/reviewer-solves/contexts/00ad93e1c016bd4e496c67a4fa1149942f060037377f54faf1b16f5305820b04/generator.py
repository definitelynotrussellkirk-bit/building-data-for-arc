"""Inputs for E139: preserve and floor-center the entire nonzero bounding box.

Labels remain the selected Racket authority. Python transforms below are
diagnostic rivals and a mirror used to select teaching witnesses. Default
lessons alternate broad/core draws with redundant rich witnesses; explicit
controls request individual inputs and disable that lesson schedule.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "03909f3e98e7"
TASK_ID = GENERATOR_ID
RULE_HASH = "78ddb8aa1ad2"
VERSION = "4.0.0"
SUMMARY = (
    "Center the full nonzero bounding box on the original zero canvas using "
    "floor margins. Mix canonical profiles, broad connected/scattered shapes, "
    "and redundant skewed disconnected witnesses against mass, fixed-width, "
    "gap-removal and component shortcuts. Exact 6..14 dimensions and 3..8 cells."
)
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("core", "witness", "free")
DEGENERATE_TEXTURES = ("already_centered", "shape_fills_grid")
HELPFUL_TEXTURES = ("blob", "scatter")
INVARIANTS = [
    "rectangular 6..14 by 6..14 integer-color canvas with fixed background zero",
    "3..8 nonzero cells using exactly 2..3 foreground colors; visible translation",
    "preserve disconnected components, internal zero gaps, colors and relative positions",
    "default four-pair windows contain two rich witnesses; explicit controls disable this schedule",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical anchors or 6..14, band-weighted", "valid": "6..14"},
    "grid_w": {"type": "int", "default": "canonical anchors or 6..14, band-weighted", "valid": "6..14"},
    "shape_size": {"type": "int", "default": "core 4..5, witnesses 6..8, free 3..8", "valid": "3..8"},
    "texture": {"type": "str", "default": "core/witness scatter; free blob|scatter", "valid": "blob|scatter"},
}
# Every ordinary Cartesian product is constructive. Diagnostic full-canvas
# fixtures are outside AXES and cannot also request an ordinary 3..8 cell count.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
_CORE_PROFILES = ((8, 9, 3, 4, 2), (9, 9, 2, 4, 2), (10, 8, 2, 5, 3),
                  (7, 11, 2, 4, 2), (9, 10, 3, 5, 2))
_EXACT_PROFILES = frozenset((h, w, colors + 1) for h, w, colors, _, _ in _CORE_PROFILES)


def schedule_profile(seed, sample_index, difficulty=None):
    """Profile of an unoverridden draw; palette, geometry and position still vary."""
    return ("core", "witness", "free", "witness")[sample_index % 4]


def _occupied(grid):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]


def _crop(grid):
    cells = _occupied(grid)
    top, left = min(r for r, _ in cells), min(c for _, c in cells)
    bottom, right = max(r for r, _ in cells), max(c for _, c in cells)
    return [row[left:right + 1] for row in grid[top:bottom + 1]]


def _paste(crop, h, w, top, left, *, out=None):
    # Rival transforms remain total when an incorrect destination leaves the
    # canvas. Nonzero overlay is necessary for independently centered components.
    out = full_grid(h, w, 0) if out is None else out
    for r, row in enumerate(crop):
        for c, value in enumerate(row):
            if value and 0 <= top + r < h and 0 <= left + c < w:
                out[top + r][left + c] = value
    return out


def _bbox_center(grid):
    """Diagnostic mirror only; public generation obtains labels from Racket."""
    crop = _crop(grid)
    h, w = len(grid), len(grid[0])
    return _paste(crop, h, w, (h - len(crop)) // 2, (w - len(crop[0])) // 2)


def _floor_mass(grid):
    crop = _crop(grid)
    cells = _occupied(crop)
    h, w, k = len(grid), len(grid[0]), len(cells)
    top = ((h - 1) * k - 2 * sum(r for r, _ in cells)) // (2 * k)
    left = ((w - 1) * k - 2 * sum(c for _, c in cells)) // (2 * k)
    return _paste(crop, h, w, top, left)


def _fixed_width_three(grid):
    crop = _crop(grid)
    h, w = len(grid), len(grid[0])
    return _paste(crop, h, w, (h - len(crop)) // 2, (w - 3) // 2)


def _compact_empty_axes(grid):
    cells = _occupied(grid)
    rows = sorted({r for r, _ in cells})
    cols = sorted({c for _, c in cells})
    crop = [[grid[r][c] for c in cols] for r in rows]
    h, w = len(grid), len(grid[0])
    return _paste(crop, h, w, (h - len(rows)) // 2, (w - len(cols)) // 2)


def _components8(cells):
    remaining, components = set(cells), []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component, pending = {start}, [start]
        while pending:
            r, c = pending.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    point = r + dr, c + dc
                    if point in remaining:
                        remaining.remove(point)
                        component.add(point)
                        pending.append(point)
        components.append(tuple(sorted(component)))
    return sorted(components, key=lambda comp: (-len(comp), comp))


def _component_crop(grid, component):
    top, left = min(r for r, _ in component), min(c for _, c in component)
    h = max(r for r, _ in component) - top + 1
    w = max(c for _, c in component) - left + 1
    out = full_grid(h, w, 0)
    for r, c in component:
        out[r - top][c - left] = grid[r][c]
    return out


def _largest_eight_component(grid):
    crop = _component_crop(grid, _components8(_occupied(grid))[0])
    h, w = len(grid), len(grid[0])
    return _paste(crop, h, w, (h - len(crop)) // 2, (w - len(crop[0])) // 2)


def _center_eight_components(grid):
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for component in _components8(_occupied(grid)):
        crop = _component_crop(grid, component)
        _paste(crop, h, w, (h - len(crop)) // 2, (w - len(crop[0])) // 2, out=out)
    return out


def _identity(grid):
    return [row[:] for row in grid]


def _crop_only(grid):
    return _crop(grid)


def _ceil_row(grid):
    crop = _crop(grid)
    h, w = len(grid), len(grid[0])
    return _paste(crop, h, w, (h - len(crop) + 1) // 2, (w - len(crop[0])) // 2)


def _ceil_col(grid):
    crop = _crop(grid)
    h, w = len(grid), len(grid[0])
    return _paste(crop, h, w, (h - len(crop)) // 2, (w - len(crop[0]) + 1) // 2)


CANONICAL_SHORTCUTS = {
    "floor_mass": _floor_mass,
    "fixed_width_three": _fixed_width_three,
    "compact_empty_axes": _compact_empty_axes,
    "largest_eight_component": _largest_eight_component,
    "center_eight_components": _center_eight_components,
}
SEMANTIC_RIVALS = dict(CANONICAL_SHORTCUTS)
LESSON_COMPETITORS = {
    **CANONICAL_SHORTCUTS, "identity": _identity, "crop_only": _crop_only,
    "ceil_row": _ceil_row, "ceil_col": _ceil_col,
}


def _mass_witness(grid):
    return _floor_mass(grid) != _bbox_center(grid)


def _width_witness(grid):
    return _fixed_width_three(grid) != _bbox_center(grid)


def _gap_witness(grid):
    return _compact_empty_axes(grid) != _bbox_center(grid)


def _largest_witness(grid):
    return _largest_eight_component(grid) != _bbox_center(grid)


def _components_witness(grid):
    return _center_eight_components(grid) != _bbox_center(grid)


SEMANTIC_WITNESSES = {
    "floor_mass": _mass_witness, "fixed_width_three": _width_witness,
    "compact_empty_axes": _gap_witness, "largest_eight_component": _largest_witness,
    "center_eight_components": _components_witness,
}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_WITNESSES}


def lesson_identifiable(demos, query):
    """Finite rival check against supplied authoritative labels, not a proof."""
    return [f"{name} fits every demonstration but changes the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]


@lru_cache(maxsize=3)
def _rich_masks(k):
    """Immutable geometry pool, never a cache of sampled or colored instances."""
    spots = tuple((r, c) for r in (0, 1, 3) for c in (0, 1, 4))
    masks = set()
    for chosen in combinations(spots, k):
        if ({r for r, _ in chosen} != {0, 1, 3}
                or {c for _, c in chosen} != {0, 1, 4}):
            continue
        for flip_r, flip_c in ((False, False), (False, True), (True, False), (True, True)):
            cells = tuple(sorted((3 - r if flip_r else r, 4 - c if flip_c else c)
                                 for r, c in chosen))
            grid = full_grid(9, 10, 0)
            for r, c in cells:
                grid[r][c] = 1
            target = _bbox_center(grid)
            if all(rival(grid) != target for rival in LESSON_COMPETITORS.values()):
                masks.add(cells)
    if not masks:
        raise ValueError(f"No rich teaching mask for {k} cells")
    return tuple(sorted(masks))


@lru_cache(maxsize=4)
def _core_masks(ch, k):
    masks = []
    for cells in combinations(tuple((r, c) for r in range(ch) for c in range(3)), k):
        if ({r for r, _ in cells} == set(range(ch))
                and {c for _, c in cells} == {0, 1, 2}
                and len(_components8(cells)) == 1):
            masks.append(cells)
    return tuple(masks)


def _validate_request(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer, not bool or a coerced scalar")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer, not bool")
    if difficulty is not None and (type(difficulty) is not str or difficulty not in ("easy", "medium", "hard")):
        raise ValueError("difficulty must be None, easy, medium or hard")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"Unknown override keys: {sorted(unknown)}")
    for name in ("grid_h", "grid_w", "shape_size"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not bool or a coerced scalar")
        lo, hi = (3, 8) if name == "shape_size" else (6, 14)
        if value is not None and not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")
    texture = overrides.get("texture")
    if texture is not None and (type(texture) is not str or texture not in HELPFUL_TEXTURES + DEGENERATE_TEXTURES):
        raise ValueError("Unknown texture; expected blob, scatter or a named diagnostic fixture")
    if texture == "shape_fills_grid" and overrides.get("shape_size") is not None:
        raise ValueError("shape_fills_grid is incompatible with an ordinary shape_size control")


def _dimensions(ctx, difficulty):
    preferred = {"easy": (7, 8, 9, 10), "hard": (10, 11, 12, 13, 14)}.get(difficulty, (8, 9, 10, 11))
    options = tuple(range(6, 15)) + preferred * 3
    return ctx.draw_choice("grid_h", options), ctx.draw_choice("grid_w", options)


def _free_cells(rng, h, w, k, texture):
    # Constructive connected growth or exact subset sampling. Never clip a
    # requested size or replace an exhausted draw with a smaller corner L.
    ch, cw = min(h - 1, k, 6), min(w - 1, k, 6)
    if texture == "blob":
        cells = {(rng.randrange(ch), rng.randrange(cw))}
        while len(cells) < k:
            frontier = sorted({(r + dr, c + dc) for r, c in cells
                               for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                               if 0 <= r + dr < ch and 0 <= c + dc < cw} - cells)
            cells.add(rng.choice(frontier))
    else:
        cells = set(rng.sample([(r, c) for r in range(ch) for c in range(cw)], k))
    top, left = min(r for r, _ in cells), min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _place(ctx, cells, h, w, colors, *, centered=False):
    rng = ctx.draw_rng("placement")
    ch, cw = max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1
    center = (h - ch) // 2, (w - cw) // 2
    positions = [(r, c) for r in range(h - ch + 1) for c in range(w - cw + 1)
                 if (r, c) != center]
    top, left = center if centered else rng.choice(positions)
    palette = ctx.draw_rng("palette").sample(list(range(1, 10)), colors)
    order = list(cells)
    ctx.draw_rng("color_assignment").shuffle(order)
    out = full_grid(h, w, 0)
    for i, (r, c) in enumerate(order):
        out[top + r][left + c] = palette[i % colors]
    return out


def _draw_from_degenerate(name, ctx):
    h, w = _dimensions(ctx, ctx.difficulty)
    if name == "shape_fills_grid":
        palette = ctx.draw_rng("diagnostic_palette").sample(list(range(1, 10)), 2)
        return [[palette[(r + c) % 2] for c in range(w)] for r in range(h)]
    k = ctx.draw_int_strict("shape_size", 3, 8)
    cells = _free_cells(ctx.draw_rng("shape"), h, w, k, "scatter")
    return _place(ctx, cells, h, w, 2, centered=True)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    effective = {key: value for key, value in overrides.items() if value is not None}
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=effective)
    texture = effective.get("texture")
    if texture in DEGENERATE_TEXTURES:
        ctx.draw_choice("texture", (texture,))
        return _draw_from_degenerate(texture, ctx)
    profile = "free" if effective else schedule_profile(seed, sample_index, difficulty)
    if profile == "core":
        height, width, colors, size, ch = ctx.draw_choice("canonical_profile", _CORE_PROFILES)
        h, w = ctx.draw_choice("grid_h", (height,)), ctx.draw_choice("grid_w", (width,))
        k = ctx.draw_choice("shape_size", (size,))
        ctx.draw_choice("texture", ("scatter",))
        cells = ctx.draw_rng("shape").choice(_core_masks(ch, k))
    elif profile == "witness":
        h, w = ctx.draw_choice("grid_h", (9,)), ctx.draw_choice("grid_w", (10,))
        k = ctx.draw_choice("shape_size", (6, 7, 8))
        ctx.draw_choice("texture", ("scatter",))
        cells = ctx.draw_rng("shape").choice(_rich_masks(k))
        colors = 3
    else:
        h, w = _dimensions(ctx, difficulty)
        k = ctx.draw_int_strict("shape_size", 3, 8)
        texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)
        cells = _free_cells(ctx.draw_rng("shape"), h, w, k, texture)
        colors = ctx.draw_choice("foreground_colors", (2, 3))
    return _place(ctx, cells, h, w, colors)


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "shape_size": len(_occupied(grid))}


def self_check(grid, *, difficulty=None, meta=None):
    """Ordinary teaching domain. Centered/full fixtures are deliberate negatives."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must have nonempty list rows"]
    if any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid colors must be literal integers 0..9, not bool"]
    h, w = len(grid), len(grid[0])
    errors = []
    if not (6 <= h <= 14 and 6 <= w <= 14):
        errors.append("ordinary canvas dimensions must be 6..14")
    cells = _occupied(grid)
    if not 3 <= len(cells) <= 8:
        errors.append("ordinary shapes must have 3..8 nonzero cells")
    if not 2 <= len({grid[r][c] for r, c in cells}) <= 3:
        errors.append("ordinary shapes must have 2..3 nonzero colors")
    if cells:
        top, left = min(r for r, _ in cells), min(c for _, c in cells)
        ch = max(r for r, _ in cells) - top + 1
        cw = max(c for _, c in cells) - left + 1
        if (top, left) == ((h - ch) // 2, (w - cw) // 2):
            errors.append("shape is already centered; this is a diagnostic identity")
    return errors


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    crop = _crop(grid)
    cells = _occupied(grid)
    profile = len(grid), len(grid[0]), len({value for row in grid for value in row})
    if profile not in _EXACT_PROFILES:
        errors.append("not a canonical height/width/color-count profile")
    if len(cells) not in (4, 5) or len(crop) not in (2, 3) or len(crop[0]) != 3:
        errors.append("canonical crops have 4..5 cells in a 2..3 by 3 bounding box")
    if len(_components8(cells)) != 1:
        errors.append("canonical foreground is eight-connected")
    if any(not any(row) for row in crop) or any(not any(row[c] for row in crop) for c in range(len(crop[0]))):
        errors.append("canonical crops have no empty internal axis")
    return errors
