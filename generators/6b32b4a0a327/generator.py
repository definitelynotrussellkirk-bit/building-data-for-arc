"""Generator for 14b:m96 — key-row select-border-object extraction.

Rule: the first row contains the output key color.  The puzzle operates on
``base = input[1:]``: find the single non-background object whose bbox touches a
border of that base grid, and paint exactly that object's cells on an otherwise
empty output, using the key color.  Interior objects are distractors and vanish.

Combinatorial axes (8): grid_h, grid_w, key_color, n_interior,
palette_size, selected_side, selected_shape, texture.
Degenerates: no_border_blob, no_interior_blob, multiple_border_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "6b32b4a0a327"
VERSION = "1.3.0"
TASK_ID = "6b32b4a0a327"
SUMMARY = "Top key row + one border-touching base blob, with interior distractor blobs."

INVARIANTS = [
    "first row contains exactly one nonzero key color",
    "below the key row, exactly one nonzero blob touches the subgrid border",
    "below the key row, at least one fully-interior distractor blob exists",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
SELECTED_SIDES = ("top", "bottom", "left", "right")
DEGENERATE_TEXTURES = ("no_border_blob", "no_interior_blob", "multiple_border_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS + SELECTED_SIDES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "8..15"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "key_color":      {"type": "color", "default": "rng 1..9", "valid": "1..9"},
    "selected_side":  {"type": "str", "default": "rng", "valid": "|".join(SELECTED_SIDES)},
    "n_interior":     {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "palette_kind":   {"type": "str", "default": "rng helpful", "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..4"},
    "selected_shape": {"type": "str", "default": "varied", "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for palette_kind/side",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _selected_blob(side: str, h: int, w: int, rng):
    """Return connected offsets placed so the selected object touches one base border."""
    shapes = [
        [(0, 0), (0, 1), (1, 0)],
        [(0, 0), (1, 0), (2, 0), (2, 1)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
        [(0, 1), (1, 0), (1, 1), (2, 1)],
    ]
    cells = rng.choice(shapes)
    bh = max(r for r, _ in cells) + 1
    bw = max(c for _, c in cells) + 1
    if side == "top":
        top = 0
        left = rng.randint(1, max(1, w - bw - 2))
    elif side == "bottom":
        top = h - bh
        left = rng.randint(1, max(1, w - bw - 2))
    elif side == "left":
        top = rng.randint(1, max(1, h - bh - 2))
        left = 0
    else:
        top = rng.randint(1, max(1, h - bh - 2))
        left = w - bw
    return {(top + r, left + c) for r, c in cells}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        base_h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
        n_interior = 1
    elif difficulty == "hard":
        base_h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 11, 13)
        n_interior = rng.randint(2, 3)
    else:
        base_h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 9, 12)
        n_interior = rng.randint(1, 2)

    key = ctx.draw_color("key_color", exclude={0})
    palette = [c for c in rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 4) if c != key]
    while len(palette) < 3:
        palette.append(next(c for c in range(1, 10) if c != key and c not in palette))

    g = full_grid(base_h + 1, w, 0)
    key_col = rng.randint(1, w - 2)
    g[0][key_col] = key

    forced_side = overrides.get("selected_side")
    tex = overrides.get("texture")
    side = tex if tex in SELECTED_SIDES else (forced_side or rng.choice(list(SELECTED_SIDES)))
    selected = _selected_blob(side, base_h, w, rng)
    selected_color = palette[0]
    for r, c in selected:
        g[r + 1][c] = selected_color

    # Reserve the selected blob plus all base-border cells so distractors are
    # strictly interior and cannot accidentally become the selected object.
    used = set(selected)
    interior_used = set(selected)
    for r in range(base_h):
        interior_used.add((r, 0)); interior_used.add((r, w - 1))
    for c in range(w):
        interior_used.add((0, c)); interior_used.add((base_h - 1, c))

    for i in range(n_interior):
        color = palette[(i + 1) % len(palette)]
        cells = grow_blob(rng, base_h, w, interior_used, rng.randint(2, 4), max_attempts=120)
        if cells:
            for r, c in cells:
                g[r + 1][c] = color
            interior_used |= cells
    return g


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc)); stack.append((nr, nc))
            out.append((color, cells))
    return out


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    h, w = len(grid), len(grid[0])
    if h < 2:
        return ["input must include a key row plus a base grid"]
    key_cells = [(0, c, v) for c, v in enumerate(grid[0]) if v != 0]
    if len(key_cells) != 1:
        errs.append(f"expected exactly one nonzero key cell in first row, found {len(key_cells)}")
    base = grid[1:]
    bh = len(base)
    comps = _components(base)
    border = [(color, cells) for color, cells in comps
              if any(r in (0, bh - 1) or c in (0, w - 1) for r, c in cells)]
    interior = [(color, cells) for color, cells in comps
                if not any(r in (0, bh - 1) or c in (0, w - 1) for r, c in cells)]
    if len(border) != 1:
        errs.append(f"expected exactly one border-touching blob in base subgrid, found {len(border)}")
    elif len(border[0][1]) < 2:
        errs.append("selected border blob is too small; canonical examples select a real blob")
    if not interior:
        errs.append("expected at least one fully-interior distractor blob in base subgrid")
    if key_cells:
        key = key_cells[0][2]
        if any(color == key for color, _ in comps):
            errs.append("base reuses the key color, hiding the extraction-and-recolor step")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h + 1, w, 0)
    g[0][w // 2] = 8
    if name == "no_border_blob":
        # all blobs are fully interior → no selected base-border object
        paint_at(g, 3, 3, [(0, 0), (0, 1), (1, 0)], 4)
        paint_at(g, 6, 6, [(0, 0), (0, 1)], 6)
        return g
    if name == "no_interior_blob":
        # selected object present, but no contrast distractor to vanish
        paint_at(g, 1, 1, [(0, 0), (0, 1), (1, 0)], 4)
        return g
    if name == "multiple_border_blobs":
        # ≥2 base-border blobs → ambiguous first selected object
        paint_at(g, 1, 1, [(0, 0), (0, 1)], 4)
        paint_at(g, h - 1, 4, [(0, 0), (0, 1)], 6)
        paint_at(g, 4, 6, [(0, 0), (1, 0)], 7)
        return g
    return g
