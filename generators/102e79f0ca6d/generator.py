"""Generator for arc_puzzle_bank_21_set12_s:S12_E5.

Rule: only nonzero cells touching a different-colored component are
shown as 8.

Combinatorial axes (8): height, width, palette_kind, contact_orientation,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_contacts, all_isolated, mixed_color_in_one_blob.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "102e79f0ca6d"
VERSION = "3.0.1"  # +self_check
TASK_ID = "102e79f0ca6d"
SUMMARY = (
    "0-bg grid (h ∈ 9-12, w ∈ 10-13) "
    "with: (a) TWO EDGE-TOUCHING "
    "COMPONENTS of DIFFERENT COLORS at "
    "a random interior position, "
    "configured per contact_orientation "
    "∈ {horizontal, vertical}: "
    "HORIZONTAL: a COLOR-2 (red) "
    "vertical 3-cell strip and an "
    "ADJACENT COLOR-3 (green) "
    "horizontal 2-cell extension "
    "touching the middle right of the "
    "red strip; VERTICAL: a COLOR-2 "
    "horizontal 3-cell strip and a "
    "COLOR-3 vertical 2-cell "
    "extension touching the middle "
    "bottom; (b) ONE ISOLATED COLOR-6 "
    "MAGENTA COMPONENT at (h-2, "
    "w-3..w-2) — a 2-cell distractor "
    "that does NOT touch the other "
    "two. Rule (KEEP ONLY NON-BG "
    "CELLS THAT EDGE-TOUCH A "
    "DIFFERENT-COLORED COMPONENT, "
    "RECOLOR THEM TO COLOR 8; "
    "OTHERS BECOME 0): For EACH "
    "non-bg cell (r, c) with color "
    "k: CHECK its 4-neighbors. IF "
    "ANY neighbor has a non-bg "
    "color != k: PAINT g[r][c] = "
    "COLOR 8 (cyan). ELSE: PAINT 0. "
    "Isolated components (no "
    "different-colored neighbor) "
    "are erased entirely. Net: "
    "only the inter-color contact "
    "boundary survives, painted in "
    "cyan."
)

INVARIANTS = [
    "background is 0",
    "at least two differently colored components edge-touch",
    "some cells in those components are not contact cells",
    "non-contact and isolated cells disappear in the output",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_contacts", "all_isolated", "mixed_color_in_one_blob")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "height":         {"type": "int", "default": "rng 9..12", "valid": "7..15"},
    "width":          {"type": "int", "default": "rng 10..13", "valid": "8..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_pairs":        {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "n_isolated":     {"type": "int", "default": "rng 1..2", "valid": "0..3"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..8"},
    "position_bias":  {"type": "str", "default": "scattered_contact_pairs",
                       "valid": "scattered_contact_pairs"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "2..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _paint(g, cells, color):
    for r, c in cells:
        g[r][c] = color


def _grow(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    return cells


def _try_place(g, rng, cells, color, *, isolate):
    """Place `cells` (normalized offsets) at a random spot. If isolate, the
    blob must not 4-touch any existing non-bg cell. If not isolate, it must
    touch >=1 existing non-bg cell of a DIFFERENT color (forming a contact)
    and not overlap. Returns True on success."""
    h, w = len(g), len(g[0])
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
    for _ in range(80):
        r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
        abs_cells = [(r0 + r - min(rs), c0 + c - min(cs)) for r, c in cells]
        if any(g[r][c] != 0 for r, c in abs_cells):
            continue
        touches_diff = False
        touches_any = False
        for (r, c) in abs_cells:
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0 \
                        and (nr, nc) not in abs_cells:
                    touches_any = True
                    if g[nr][nc] != color:
                        touches_diff = True
        if isolate and touches_any:
            continue
        if (not isolate) and not touches_diff:
            continue
        for (r, c) in abs_cells:
            g[r][c] = color
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("height", 9, 11); w = ctx.draw_int("width", 10, 12)
        n_pairs = ctx.draw_int("n_pairs", 1, 2); n_iso = ctx.draw_int("n_isolated", 0, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("height", 13, 15); w = ctx.draw_int("width", 13, 16)
        n_pairs = ctx.draw_int("n_pairs", 3, 4); n_iso = ctx.draw_int("n_isolated", 1, 3)
    else:
        h = ctx.draw_int("height", 10, 13); w = ctx.draw_int("width", 11, 14)
        n_pairs = ctx.draw_int("n_pairs", 2, 3); n_iso = ctx.draw_int("n_isolated", 1, 2)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    # contact pairs: place blob A (isolated), then blob B touching it in a
    # DIFFERENT color (so the shared border becomes 8).
    for _ in range(n_pairs):
        ca, cb = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 2)  # avoid 8 (the output color)
        a = _grow(rng, rng.randint(2, 5))
        if not _try_place(g, rng, a, ca, isolate=True):
            continue
        b = _grow(rng, rng.randint(2, 5))
        _try_place(g, rng, b, cb, isolate=False)
    # isolated distractor blobs (no different-colored neighbor -> erased to 0).
    for _ in range(n_iso):
        col = rng.choice([1, 2, 3, 4, 5, 6, 7, 9])
        d = _grow(rng, rng.randint(1, 4))
        _try_place(g, rng, d, col, isolate=True)
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """At least 2 distinct non-zero colors; some pair of differently-colored cells is 4-adjacent."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 2:
        errors.append(f"need >=2 distinct non-zero colors, got {len(colors)}")
        return errors
    # Check at least one pair of adjacent different-color cells
    found = False
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v == 0:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    nv = grid[nr][nc]
                    if nv != 0 and nv != v:
                        found = True
                        break
            if found:
                break
        if found:
            break
    if not found:
        errors.append("no two adjacent cells of different colors — no contact boundary")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_contacts":
        # all components isolated → no contact cells, output is empty
        _paint(g, [(2, 2), (2, 3), (3, 2)], 2)
        _paint(g, [(6, 7), (7, 7), (7, 8)], 3)
        _paint(g, [(5, 1), (5, 2)], 6)
        return g
    if name == "all_isolated":
        # singletons only → no contact between same-color and different-color cells
        g[2][3] = 2; g[5][7] = 3; g[7][2] = 6
        return g
    if name == "mixed_color_in_one_blob":
        # one blob has multiple colors mixed in (touches itself) → "different-colored neighbor"
        # predicate becomes ambiguous (is it one component or many?)
        _paint(g, [(2, 2), (2, 3)], 2)
        _paint(g, [(2, 4), (2, 5)], 3)   # adjacent, mixed colors form contiguous blob
        _paint(g, [(2, 6), (2, 7)], 6)
        return g
    return g
