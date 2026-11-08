"""Generator for arc_additional_puzzles_21_set11_bundle:H75.

Rule: cmds = leading non-zero cells in row 0. Bbox-crop body (r ≥ 1).
Apply each cmd: 1=cw, 2=flip-lr, 3=flip-ud, else=transpose.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_cmds,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_cmds, no_motif, invalid_cmd.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "26879f28ee60"
VERSION = "2.1.0"  # distinct=8: body was a FIXED 2x2 (values 1,2,3,4) -> only 8 dihedral orientations. Output = body (cells below row 0) transformed by the row-0 command chain. Now random multi-colour body (varied size/shape) + varied cmds.
TASK_ID = "26879f28ee60"
SUMMARY = (
    "0-bg grid (h ∈ 6-8, w ∈ 9-11) with: "
    "(a) ROW 0 CMD SEQUENCE — n_cmds ∈ "
    "1-3 NON-ZERO CMD CELLS in LEADING "
    "POSITIONS (cols 0..n_cmds-1), each "
    "value ∈ {1..4} (per demos: 1=cw90, "
    "2=flip-LR, 3=flip-UD, 4=transpose); "
    "cols n_cmds..w-1 of row 0 stay 0; "
    "(b) ONE RANDOM MULTI-COLOR "
    "BODY (2-5 x 2-5, varied shape, "
    "1-3 holes) placed below row 0. "
    "Rule "
    "(READ CMDS FROM ROW 0 LEADING "
    "CELLS, CROP THE BODY TO ITS "
    "BBOX, APPLY EACH CMD'S "
    "TRANSFORM IN ORDER, OUTPUT THE "
    "TRANSFORMED CROP): READ cmds "
    "from row 0 left-to-right "
    "(stop at first 0). CROP the "
    "body (rows ≥ 1) to the bbox "
    "of non-bg cells. APPLY EACH "
    "CMD IN ORDER to the cropped "
    "grid: 1=cw90, 2=flip-LR, "
    "3=flip-UD, other=transpose. "
    "OUTPUT the final transformed "
    "crop. Net: the body is "
    "transformed by the cmd "
    "sequence; output is its "
    "transformed version (dims + "
    "content vary with the body)."
)

INVARIANTS = [
    "row 0 starts with 1-3 non-zero cells (cmds ∈ 1..4) followed by 0s",
    "below row 0 is a small 2x2 multi-color motif",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_cmds", "no_motif", "invalid_cmd")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_cmds":         {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "row0_cmds",
                       "valid": "row0_cmds"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # output = the body shape (non-zero cells below row 0) transformed by the row-0
    # command chain. Body was a FIXED 2x2 (values 1,2,3,4) -> only the 8 orientations
    # (distinct=8). Now a RANDOM multi-colour body (varied size/shape) -> output dims
    # AND content vary, plus the command chain varies.
    if difficulty == "easy":
        n_cmds = ctx.draw_int("n_cmds", 1, 1)
        h = ctx.draw_int("grid_h", 6, 8); w = ctx.draw_int("grid_w", 8, 11)
        bmax = 3
    elif difficulty == "hard":
        n_cmds = ctx.draw_int("n_cmds", 2, 3)
        h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 11, 14)
        bmax = 5
    else:
        n_cmds = ctx.draw_int("n_cmds", 1, 3)
        h = ctx.draw_int("grid_h", 7, 10); w = ctx.draw_int("grid_w", 9, 12)
        bmax = 4
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    for i in range(n_cmds):
        g[0][i] = rng.randint(1, 4)
    # random multi-colour body block placed below row 0
    bh = rng.randint(2, bmax); bw = rng.randint(2, bmax)
    cols = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], rng.randint(2, 4))
    for _ in range(40):
        body = [[(rng.choice(cols) if rng.random() < 0.7 else 0) for _ in range(bw)]
                for _ in range(bh)]
        used_colors = {v for row in body for v in row if v}
        if sum(1 for row in body for v in row if v) >= 2 and len(used_colors) >= 2:
            break
    top = rng.randint(1, h - bh); left = rng.randint(0, w - bw)
    for r in range(bh):
        for c in range(bw):
            if body[r][c]:
                g[top + r][left + c] = body[r][c]
    # Avoid teaching an invisible no-op command chain.  Some sampled command
    # sequences are algebraic identities on a symmetric body (e.g. two flips),
    # which hides the transform branch even though parity passes.  When that
    # happens, force a one-step cw rotation and pin an asymmetric two-color
    # witness in the body crop.
    cmds = [v for v in g[0] if v != 0]
    cropped = _crop_body(g)
    if cropped and _apply_cmds(cropped, cmds) == cropped:
        for c in range(w):
            g[0][c] = 0
        g[0][0] = 1
        a, b = cols[0], (cols[1] if len(cols) > 1 else (cols[0] % 9) + 1)
        if b == a:
            b = 9 if a != 9 else 8
        g[top][left] = a
        g[top][left + bw - 1] = b
    return g


def _crop_body(grid):
    cells = [(r, c) for r in range(1, len(grid))
             for c, v in enumerate(grid[r]) if v != 0]
    if not cells:
        return []
    r0 = min(r for r, _ in cells); r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells); c1 = max(c for _, c in cells)
    return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]


def _cw(a):
    return [list(row) for row in zip(*a[::-1])]


def _flip_lr(a):
    return [list(reversed(row)) for row in a]


def _flip_ud(a):
    return [list(row) for row in reversed(a)]


def _transpose(a):
    return [list(row) for row in zip(*a)]


def _apply_cmds(body, cmds):
    out = [row[:] for row in body]
    for cmd in cmds:
        if cmd == 1:
            out = _cw(out)
        elif cmd == 2:
            out = _flip_lr(out)
        elif cmd == 3:
            out = _flip_ud(out)
        else:
            out = _transpose(out)
    return out


def _draw_from_degenerate(name, rng):
    h, w = 7, 10
    g = full_grid(h, w, 0)
    if name == "no_cmds":
        # row 0 is empty → no transform sequence, output is just the cropped body
        g[3][3] = 1; g[3][4] = 2
        g[4][3] = 3; g[4][4] = 4
        return g
    if name == "no_motif":
        # cmds present but no motif below → nothing to transform
        g[0][0] = 2; g[0][1] = 3
        return g
    if name == "invalid_cmd":
        # cmd value outside the 1-4 vocabulary → falls into default-transpose branch only
        g[0][0] = 7; g[0][1] = 9
        g[3][3] = 1; g[3][4] = 2
        g[4][3] = 3; g[4][4] = 4
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    cmds = []
    for v in grid[0]:
        if v == 0:
            break
        cmds.append(v)
    if not (1 <= len(cmds) <= 3):
        msgs.append(f"expected 1..3 leading command cells, found {len(cmds)}")
    if any(v not in (1, 2, 3, 4) for v in cmds):
        msgs.append("command cells must use the 1..4 transform vocabulary")
    body = _crop_body(grid)
    if sum(1 for row in body for v in row if v != 0) < 2:
        msgs.append("body crop must contain at least two non-background cells")
    if body and len({v for row in body for v in row if v != 0}) < 2:
        msgs.append("body crop should contain at least two colors")
    if body and cmds and _apply_cmds(body, cmds) == body:
        msgs.append("command chain is identity on the sampled body")
    return msgs
