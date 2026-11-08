"""Generator for arc_additional_puzzle_bank_volume12:E81.

Rule: recolor to 6 every color-7 object that touches EXACTLY 2 of the grid
borders (top/bottom/left/right); objects touching 0, 1, 3 or 4 borders
stay 7.

This generator mixes color-7 objects touching exactly 2 borders (corner or
edge-spanning) with distractors touching 0 or 1 border.

Combinatorial axes: grid size, the object shapes, their border-touch
counts, and positions.
Degenerates: no_objects, all_interior, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "9d98a8d91a63"
VERSION = "2.0.1"  # diversity: mix of 2-border-touch color-7 objects + other-touch distractors (was fixed ~24)
TASK_ID = "9d98a8d91a63"
SUMMARY = (
    "0-bg grid (size varies) with color-7 objects. Rule: recolor to 6 every "
    "object touching EXACTLY 2 grid borders (corner or edge-spanning); "
    "objects touching 0/1/3/4 borders stay 7. The grid size, object shapes, "
    "border-touch counts and positions vary freely (was a fixed setup, ~24 "
    "distinct)."
)

INVARIANTS = [
    "color-7 objects with various border-touch counts",
    "objects touching exactly 2 borders recolor to 6; others stay 7",
    "at least one object touches exactly 2 borders",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_objects", "all_interior", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..22"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..24"},
    "n_targets":      {"type": "int", "default": "varies", "valid": "1..2"},
    "n_distractors":  {"type": "int", "default": "varies", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "border_mix", "valid": "border_mix"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_objects|all_interior|full_grid"},
}


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _poly(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    return _norm(cells)


def _reserve(occ, top, left, sh, sw, h, w, margin=1):
    for r in range(top - margin, top + sh + margin):
        for c in range(left - margin, left + sw + margin):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + sh):
        for c in range(left, left + sw):
            occ[r][c] = True
    return True


def _touch(cells, h, w):
    return (any(r == 0 for r, c in cells) + any(r == h - 1 for r, c in cells)
            + any(c == 0 for r, c in cells) + any(c == w - 1 for r, c in cells))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, wr, tr, dr_ = (12, 14), (12, 15), (1, 1), (1, 2)
    elif difficulty == "hard":
        hr, wr, tr, dr_ = (16, 22), (18, 24), (1, 2), (2, 3)
    else:
        hr, wr, tr, dr_ = (13, 18), (14, 20), (1, 2), (1, 3)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        targets = 0

        for _ in range(rng.randint(*tr)):
            kind = rng.choice(["corner", "vspan", "hspan"])
            placed = False
            for _t in range(40):
                if kind == "corner":
                    sp = _poly(rng, rng.randint(3, 6))
                    sh = max(r for r, c in sp) + 1; sw = max(c for r, c in sp) + 1
                    if sh + 1 >= h or sw + 1 >= w:
                        continue
                    corner = rng.choice([(0, 0), (0, w - sw), (h - sh, 0), (h - sh, w - sw)])
                    top, left = corner
                    cells = [(top + r, left + c) for r, c in sp]
                elif kind == "vspan":
                    col = rng.randint(1, w - 2); cells = [(r, col) for r in range(h)]
                    sh, sw, top, left = h, 1, 0, col
                else:
                    row = rng.randint(1, h - 2); cells = [(row, c) for c in range(w)]
                    sh, sw, top, left = 1, w, row, 0
                if _touch(cells, h, w) != 2:
                    continue
                if _reserve(occ, top, left, sh, sw, h, w):
                    paint_at(g, 0, 0, cells, 7)
                    targets += 1; placed = True; break

        # distractors: touch 0 (interior) or 1 (mid-edge)
        for _ in range(rng.randint(*dr_)):
            for _t in range(40):
                sp = _poly(rng, rng.randint(3, 5))
                sh = max(r for r, c in sp) + 1; sw = max(c for r, c in sp) + 1
                want = rng.choice([0, 1])
                if want == 0:
                    if sh + 2 > h or sw + 2 > w:
                        continue
                    top = rng.randint(1, h - sh - 1); left = rng.randint(1, w - sw - 1)
                else:
                    edge = rng.choice(["top", "bottom", "left", "right"])
                    if edge == "top":
                        top = 0; left = rng.randint(1, w - sw - 1)
                    elif edge == "bottom":
                        top = h - sh; left = rng.randint(1, w - sw - 1)
                    elif edge == "left":
                        top = rng.randint(1, h - sh - 1); left = 0
                    else:
                        top = rng.randint(1, h - sh - 1); left = w - sw
                cells = [(top + r, left + c) for r, c in sp]
                if _touch(cells, h, w) != want:
                    continue
                if _reserve(occ, top, left, sh, sw, h, w):
                    paint_at(g, 0, 0, cells, 7)
                    break

        if targets >= 1:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 12, 0)
    paint_at(g, 0, 0, [(0, 0), (0, 1), (1, 0)], 7)    # corner: touch 2
    if name == "no_objects":
        return full_grid(12, 12, 0)
    if name == "all_interior":
        g2 = full_grid(12, 12, 0); paint_at(g2, 5, 5, [(0, 0), (0, 1), (1, 0)], 7)
        return g2
    if name == "full_grid":
        return full_grid(12, 12, 7)
    paint_at(g, 5, 5, [(0, 0), (0, 1)], 7)            # interior: touch 0
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: bg=0; at least one color-7 cell; no non-{0,7} cells."""
    msgs = []
    h, w = len(grid), len(grid[0])
    count_7 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 7)
    other = set(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] not in (0, 7))
    if count_7 == 0:
        msgs.append("no color-7 cells found")
    if other:
        msgs.append(f"unexpected non-{{0,7}} colors in grid: {sorted(other)}")
    return msgs
