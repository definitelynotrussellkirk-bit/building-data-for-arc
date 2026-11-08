"""Generator for f9d67f8b / 5062e4b74f17 — 4-fold symmetry inpainting.

Canonical rule: color 9 is damage.  For every damaged cell, recover the nearest
visible member of its orbit under the 4mm symmetry transforms
    (r,c) -> (31-r,c), (r,31-c), (c,31-r), (31-c,r).
The real task examples are 30x30 dense nonzero textures with dark-red occluders;
the previous generator emitted 11-14 square pasted 9x9 patches, which the rule
accepted only inconsistently and collapsed into duplicate pairs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5062e4b74f17"
VERSION = "2.0.0"
TASK_ID = "5062e4b74f17"

SUMMARY = (
    "30x30 nonzero texture with exact 4mm symmetry around the rule's off-center "
    "pivot. One to three connected color-9 damage rectangles occlude part of the "
    "texture; every damaged cell has at least one non-damaged same-orbit mate, "
    "so the canonical rule repairs the grid in place instead of leaving 9s or "
    "collapsing to duplicate/no-op pairs."
)

INVARIANTS = [
    "grid is exactly 30x30",
    "normal texture uses no black cells and reserves color 9 for damage",
    "all non-damaged cells are consistent on every in-bounds 4mm symmetry orbit",
    "every damaged cell has a visible same-orbit source cell",
    "damage is interior and non-empty",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_damage", "no_texture", "full_damage")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_size": {"type": "int", "default": "fixed 30", "valid": "30"},
    "palette_kind": {"type": "str", "default": "rng helpful", "valid": "default|warm|cool|varied"},
    "occluder_count": {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "occluder_h": {"type": "int", "default": "rng 3..7", "valid": "2..8"},
    "occluder_w": {"type": "int", "default": "rng 3..8", "valid": "2..9"},
    "bg_color": {"type": "int", "default": "not used: full dense texture", "valid": "1..8"},
    "palette_size": {"type": "int", "default": "rng 4..8", "valid": "3..8"},
    "position_bias": {"type": "str", "default": "interior_damage", "valid": "interior_damage"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..8", "valid": "3..8"},
    "density": {"type": "str", "default": "dense", "valid": "dense"},
    "texture": {"type": "str", "default": "alias for palette_kind", "valid": "default|warm|cool|varied|no_damage|no_texture|full_damage"},
}

_PALETTES = {
    "default": [1, 2, 3, 4, 5, 6, 7, 8],
    "warm": [1, 2, 3, 4, 6, 7, 8],
    "cool": [1, 3, 4, 5, 6, 7, 8],
    "varied": [1, 2, 3, 4, 5, 6, 7, 8],
}


def _transforms(p: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    r, c = p
    return ((31 - r, c), (r, 31 - c), (c, 31 - r), (31 - c, r))


def _orbit(p: tuple[int, int]) -> frozenset[tuple[int, int]]:
    """Finite closure under the canonical rule's transform generators.

    The rule explores out-of-bounds coordinates too, then tests visibility.  We
    therefore compute the algebraic closure first and filter to in-bounds later.
    """
    seen = {p}
    frontier = [p]
    while frontier:
        q = frontier.pop()
        for nxt in _transforms(q):
            if nxt not in seen:
                seen.add(nxt)
                frontier.append(nxt)
    return frozenset(seen)


def _in_bounds(p: tuple[int, int]) -> bool:
    r, c = p
    return 0 <= r < 30 and 0 <= c < 30


def _orbit_cells(p: tuple[int, int]) -> list[tuple[int, int]]:
    return sorted(q for q in _orbit(p) if _in_bounds(q))


def _palette(rng, palette_kind: str, palette_size: int) -> list[int]:
    colors = list(_PALETTES.get(palette_kind, _PALETTES["default"]))
    rng.shuffle(colors)
    return colors[:max(3, min(palette_size, len(colors)))]


def _make_symmetric_texture(rng, colors: list[int]) -> list[list[int]]:
    g = full_grid(30, 30, 1)
    assigned: set[tuple[int, int]] = set()
    for r in range(30):
        for c in range(30):
            if (r, c) in assigned:
                continue
            cells = _orbit_cells((r, c))
            color = rng.choice(colors)
            for rr, cc in cells:
                g[rr][cc] = color
                assigned.add((rr, cc))
    return g


def _damage_cells_have_sources(g: list[list[int]]) -> bool:
    damaged = [(r, c) for r in range(30) for c in range(30) if g[r][c] == 9]
    if not damaged:
        return False
    for p in damaged:
        if not any(g[r][c] != 9 for r, c in _orbit_cells(p)):
            return False
    return True


def _paint_damage(rng, g: list[list[int]], *, count: int, h_range: tuple[int, int], w_range: tuple[int, int]) -> bool:
    # Several attempts because a large rectangle near the center can cover an
    # entire tiny orbit.  In that case the rule legitimately cannot repair it.
    base = [row[:] for row in g]
    for _attempt in range(80):
        for r in range(30):
            g[r][:] = base[r][:]
        for _ in range(count):
            hh = rng.randint(*h_range)
            ww = rng.randint(*w_range)
            # Interior-biased but broad enough to vary corners/sides; exclude the
            # outer two rows/cols because many transform mates fall out of bounds.
            top = rng.randint(2, 29 - hh)
            left = rng.randint(2, 29 - ww)
            for r in range(top, top + hh):
                for c in range(left, left + ww):
                    # Ragged corners avoid a pure rectangle-only distribution.
                    if rng.random() < 0.88 or (r in (top, top + hh - 1) and c in (left, left + ww - 1)):
                        g[r][c] = 9
        if _damage_cells_have_sources(g):
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture)

    palette_kind = texture if texture in HELPFUL_TEXTURES else ctx.draw_choice("palette_kind", PALETTE_KINDS)
    if difficulty == "easy":
        count = ctx.draw_int("occluder_count", 1, 1)
        h_range, w_range = (3, 4), (3, 5)
        palette_size = ctx.draw_int("palette_size", 4, 6)
    elif difficulty == "hard":
        count = ctx.draw_int("occluder_count", 2, 3)
        h_range, w_range = (5, 7), (5, 8)
        palette_size = ctx.draw_int("palette_size", 6, 8)
    else:
        count = ctx.draw_int("occluder_count", 1, 3)
        h_range, w_range = (3, 7), (3, 8)
        palette_size = ctx.draw_int("palette_size", 4, 8)

    g = _make_symmetric_texture(rng, _palette(rng, palette_kind, palette_size))
    if not _paint_damage(rng, g, count=count, h_range=h_range, w_range=w_range):
        raise ValueError("could not place repairable damage")
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    issues: list[str] = []
    if len(grid) != 30 or any(len(row) != 30 for row in grid):
        return [f"expected 30x30 grid, got {len(grid)}x{len(grid[0]) if grid else 0}"]
    vals = {v for row in grid for v in row}
    if 0 in vals:
        issues.append("normal examples should be fully nonzero texture (no black cells)")
    bad = sorted(v for v in vals if not isinstance(v, int) or v < 0 or v > 9)
    if bad:
        issues.append(f"non-ARC colors: {bad[:5]}")
    damaged = [(r, c) for r in range(30) for c in range(30) if grid[r][c] == 9]
    if not damaged:
        issues.append("missing color-9 damage cells")
        return issues
    if any(r in (0, 1, 29) or c in (0, 1, 29) for r, c in damaged):
        issues.append("damage should stay away from edge rows/cols with mostly out-of-bounds orbits")
    for p in damaged:
        srcs = [(r, c) for r, c in _orbit_cells(p) if grid[r][c] != 9]
        if not srcs:
            issues.append(f"damaged cell {p} has no visible same-orbit source")
            break
    checked_orbits: set[frozenset[tuple[int, int]]] = set()
    for r in range(30):
        for c in range(30):
            if grid[r][c] == 9:
                continue
            orb = frozenset(_orbit_cells((r, c)))
            if orb in checked_orbits:
                continue
            checked_orbits.add(orb)
            visible_vals = {grid[rr][cc] for rr, cc in orb if grid[rr][cc] != 9}
            if len(visible_vals) > 1:
                issues.append(f"visible orbit has inconsistent colors: {sorted(visible_vals)}")
                break
    return issues


def _draw_from_degenerate(name):
    g = full_grid(30, 30, 4)
    if name == "no_damage":
        return g
    if name == "no_texture":
        for r in range(12, 18):
            for c in range(12, 18):
                g[r][c] = 9
        return g
    if name == "full_damage":
        for r in range(30):
            for c in range(30):
                g[r][c] = 9
        return g
    return g
