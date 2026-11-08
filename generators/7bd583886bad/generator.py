"""Generator for 626c0bcc.

Rule: a connected color-8 mask has a unique exact cover by four legal
pieces — a 2x2 square (type 1) and three specific L-tromino orientations
(types 2/3/4).  Recolor every cell by the type of the piece covering it.

Combinatorial axes: small canonical-scale grid size, connected piece count,
piece-type mix, and cluster placement.  Degenerates: no_pieces,
single_piece, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7bd583886bad"
VERSION = "3.2.0"  # generate connected unique exact-cover masks at canonical scale
TASK_ID = "7bd583886bad"
SUMMARY = (
    "0-bg canonical-scale grid with one connected color-8 mask. The mask has a "
    "unique exact cover by the four legal pieces: a 2x2 square (type 1) and "
    "three L-tromino orientations (types 2/3/4). Rule: recolor covered cells "
    "by piece type."
)

INVARIANTS = [
    "background is 0; all source cells are color 8",
    "8-cells form one connected mask, not isolated pre-segmented pieces",
    "the mask has exactly one exact cover by the four legal piece shapes",
]

PALETTE_KINDS = ("fixed",)
DEGENERATE_TEXTURES = ("no_pieces", "single_piece", "full_grid")
HELPFUL_TEXTURES = ("connected_cover",)

# the 4 tileable shapes (exact orientations the canonical rule searches for), type 1..4
PIECES = [
    [(0, 0), (0, 1), (1, 0), (1, 1)],   # type 1: 2x2 square
    [(0, 1), (1, 0), (1, 1)],           # type 2
    [(0, 0), (0, 1), (1, 1)],           # type 3
    [(0, 0), (1, 0), (1, 1)],           # type 4
]

AXES = {
    "grid_h":         {"type": "int", "default": "canonical scale", "valid": "7..9"},
    "grid_w":         {"type": "int", "default": "canonical scale", "valid": "7..9"},
    "piece_count":    {"type": "int", "default": "varies", "valid": "3..7"},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "anchor_corner":  {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "true", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "connected", "valid": "connected"},
    "piece_kind":     {"type": "str", "default": "rng", "valid": "rng"},
    "texture":        {"type": "str", "default": "connected_cover",
                       "valid": "connected_cover|no_pieces|single_piece|full_grid"},
}


def _neighbors(cell):
    r, c = cell
    return ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))


def _components(mask):
    seen = set(); comps = []
    for cell in mask:
        if cell in seen:
            continue
        stack = [cell]; seen.add(cell); cells = []
        while stack:
            cur = stack.pop(); cells.append(cur)
            for nb in _neighbors(cur):
                if nb in mask and nb not in seen:
                    seen.add(nb); stack.append(nb)
        comps.append(cells)
    return comps


def _piece_cells(piece, top, left):
    return frozenset((top + r, left + c) for r, c in piece)


def _placement_candidates(h, w, occupied, *, require_touch):
    out = []
    for typ, piece in enumerate(PIECES, start=1):
        bh = max(r for r, _ in piece) + 1
        bw = max(c for _, c in piece) + 1
        for top in range(h - bh + 1):
            for left in range(w - bw + 1):
                cells = _piece_cells(piece, top, left)
                if cells & occupied:
                    continue
                if require_touch and not any(nb in occupied for cell in cells for nb in _neighbors(cell)):
                    continue
                out.append((typ, cells))
    return out


def _cover_candidates(mask, h, w):
    out = []
    for typ, piece in enumerate(PIECES, start=1):
        bh = max(r for r, _ in piece) + 1
        bw = max(c for _, c in piece) + 1
        for top in range(h - bh + 1):
            for left in range(w - bw + 1):
                cells = _piece_cells(piece, top, left)
                if cells <= mask:
                    out.append((typ, cells))
    return out


def _exact_cover_count(mask, h, w, *, limit=2):
    mask = frozenset(mask)
    if not mask:
        return 0
    by_cell = {cell: [] for cell in mask}
    for item in _cover_candidates(mask, h, w):
        for cell in item[1]:
            by_cell[cell].append(item)
    count = 0

    def search(uncovered):
        nonlocal count
        if count >= limit:
            return
        if not uncovered:
            count += 1
            return
        # Fail fast at the most constrained remaining cell.
        cell = min(uncovered, key=lambda x: sum(1 for _, cells in by_cell.get(x, []) if cells <= uncovered))
        options = [(typ, cells) for typ, cells in by_cell.get(cell, []) if cells <= uncovered]
        for _typ, cells in options:
            search(uncovered - cells)
            if count >= limit:
                return

    search(mask)
    return count


def _build_connected_unique_mask(rng, h, w, piece_count):
    for _attempt in range(500):
        occupied = frozenset()
        for i in range(piece_count):
            candidates = _placement_candidates(h, w, occupied, require_touch=(i > 0))
            rng.shuffle(candidates)
            if not candidates:
                break
            _typ, cells = candidates[0]
            occupied = occupied | cells
        else:
            if len(_components(occupied)) == 1 and _exact_cover_count(occupied, h, w, limit=2) == 1:
                return occupied
    raise ValueError("could not realize a connected unique exact-cover mask")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        h = w = 7; nr = (3, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        nr = (5, 7)
    else:
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        nr = (4, 6)
    piece_count = ctx.draw_int("piece_count", *nr)
    mask = _build_connected_unique_mask(rng, h, w, piece_count)
    g = full_grid(h, w, 0)
    for r, c in mask:
        g[r][c] = 8
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 7, 0)
    if name == "no_pieces":
        return g
    if name == "single_piece":
        for dr, dc in PIECES[0]:
            g[2 + dr][2 + dc] = 8
        return g
    if name == "full_grid":
        for r in range(7):
            for c in range(7):
                g[r][c] = 8
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify the default input is a connected, uniquely tileable 8-mask."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    errors = []
    h = len(grid); w = len(grid[0])
    if h > 12 or w > 12:
        errors.append(f"grid too large for canonical-scale exact-cover task: {h}x{w}")
    bad = sorted({v for row in grid for v in row if v not in (0, 8)})
    if bad:
        errors.append(f"unexpected input colors: {bad}")
    mask = frozenset((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 8)
    if not mask:
        errors.append("no color-8 mask cells")
        return errors
    comps = _components(mask)
    if len(comps) != 1:
        errors.append(f"expected one connected 8-mask, got {len(comps)} components")
    count = _exact_cover_count(mask, h, w, limit=2)
    if count != 1:
        errors.append(f"expected exactly one legal exact cover, got {count if count < 2 else '>=2'}")
    return errors
