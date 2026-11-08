"""Generator for arc_puzzle_bank_21_set20_s:S20_M2 — template search across a 9-divider.

Rule (ACTUAL, from the canonical Racket): split the grid at full-height
color-9 columns; panel 1 is a TEMPLATE (cropped to its non-{0,9} bbox),
panel 2 is a SEARCH BOARD. Find every placement of any D4 variant of
the template (8 orientations, 0s are wildcards, nonzero cells must
match EXACTLY incl. color) and output a board-sized grid with color 8
at every matched cell. Panels beyond the second are IGNORED.

Combinatorial axes: grid_h, board_w, tpl_w, n_copies, texture
(plain|extra_panels|no_match).
Degenerates: no_match (decoy-only board -> blank output). The old
no_dividers / single_panel / empty_panels all CRASH the rule
((second panels) -> #f, or crop of an empty panel applies a grid as a
procedure) and were dropped.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "05cfa1aabb8a"
VERSION = "3.0.1"
TASK_ID = "05cfa1aabb8a"

SUMMARY = (
    "Two panels split by a full color-9 column: left panel holds a "
    "small colored template, right panel is a search board with 1-3 "
    "D4-transformed exact-color copies plus decoy clutter. Output "
    "marks every matched cell with 8 on a board-sized canvas. (Was: "
    "4-7 independent random motif panels — the rule only reads the "
    "first two, so 19/20 outputs were blank; all 3 degenerates "
    "crashed the rule.)"
)

# Rivals: 'matches must keep orientation' refuted by rotated/flipped
# copies. 'match shape only' refuted by same-shape decoys in other
# colors that stay unmarked. 'all panels participate' refuted by
# extra_panels boards whose trailing panels change nothing. 'output
# keeps copy colors' refuted by everything turning 8.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    ">=2 panels always (the rule crashes on fewer)",
    "template panel is non-empty (crop of an empty panel crashes the rule)",
    "main-path boards contain >=1 exact D4 copy (output never blank)",
    "decoys never use template colors (no accidental matches; mirror-verified)",
]

DEGENERATE_TEXTURES = ("no_match",)
HELPFUL_TEXTURES = ("plain", "extra_panels")

AXES = {
    "grid_h":   {"type": "int", "default": "rng 5..8", "valid": "4..10"},
    "tpl_w":    {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "board_w":  {"type": "int", "default": "rng 9..14", "valid": "8..18"},
    "n_copies": {"type": "int", "default": "rng 1..3", "valid": "1..3",
                 "doc": "D4-transformed template copies hidden in the board."},
    "texture":  {"type": "str", "default": "rng helpful",
                 "valid": "plain|extra_panels|no_match",
                 "doc": "extra_panels: 1-2 trailing panels the rule ignores; "
                        "no_match: decoy-only board, output is blank."},
}

_COLORS = (1, 2, 3, 4, 5, 6, 7)


def _grow(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = cells[rng.randrange(len(cells))]
        dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc))
            seen.add((r + dr, c + dc))
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _rot_cw(t):
    return [list(row) for row in zip(*t[::-1])]


def _variants(t):
    """All 8 D4 orientations of grid t, deduplicated."""
    out, cur = [], t
    for _ in range(4):
        out.append(cur)
        cur = _rot_cw(cur)
    cur = [row[::-1] for row in t]
    for _ in range(4):
        out.append(cur)
        cur = _rot_cw(cur)
    uniq = []
    for v in out:
        if v not in uniq:
            uniq.append(v)
    return uniq


def _match_cells(board, tpl):
    """Mirror of the rule: union of nonzero template cells over every
    D4-variant placement that matches exactly (0s wildcard)."""
    h, w = len(board), len(board[0])
    hits = set()
    for t in _variants(tpl):
        th, tw = len(t), len(t[0])
        for r in range(h - th + 1):
            for c in range(w - tw + 1):
                ok = True
                for tr in range(th):
                    for tc in range(tw):
                        tv = t[tr][tc]
                        if tv != 0 and board[r + tr][c + tc] != tv:
                            ok = False
                            break
                    if not ok:
                        break
                if ok:
                    for tr in range(th):
                        for tc in range(tw):
                            if t[tr][tc] != 0:
                                hits.add((r + tr, c + tc))
    return hits


def _assemble(h, panels):
    w = sum(len(p[0]) for p in panels) + len(panels) - 1
    g = full_grid(h, w, 0)
    c0 = 0
    for i, p in enumerate(panels):
        for r in range(h):
            for c in range(len(p[0])):
                g[r][c0 + c] = p[r][c]
        c0 += len(p[0])
        if i < len(panels) - 1:
            for r in range(h):
                g[r][c0] = 9
            c0 += 1
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain", "plain",
                                              "extra_panels"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 6)
        tw = ctx.draw_int("tpl_w", 3, 3)
        bw = ctx.draw_int("board_w", 9, 11)
        n_copies = ctx.draw_int("n_copies", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 8)
        tw = ctx.draw_int("tpl_w", 3, 4)
        bw = ctx.draw_int("board_w", 12, 14)
        n_copies = ctx.draw_int("n_copies", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 5, 8)
        tw = ctx.draw_int("tpl_w", 3, 4)
        bw = ctx.draw_int("board_w", 9, 14)
        n_copies = ctx.draw_int("n_copies", 1, 3)
    rng = ctx.draw_rng("layout")

    for _attempt in range(80):
        # template motif: 2-4 cells, 1-2 colors, fits tpl panel
        shape = _grow(rng, rng.randint(2, 4))
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        if sh > h or sw > tw:
            continue
        tpl_colors = rng.sample(_COLORS, rng.randint(1, 2))
        colored = [(r, c, tpl_colors[i % len(tpl_colors)])
                   for i, (r, c) in enumerate(shape)]
        tpl_panel = full_grid(h, tw, 0)
        pr = rng.randint(0, h - sh)
        pc = rng.randint(0, tw - sw)
        for r, c, v in colored:
            tpl_panel[pr + r][pc + c] = v
        tpl = [[0] * sw for _ in range(sh)]
        for r, c, v in colored:
            tpl[r][c] = v

        board = full_grid(h, bw, 0)
        want = 0 if texture == "no_match" else n_copies
        placed = 0
        for _ in range(120):
            if placed >= want:
                break
            var = _variants(tpl)[rng.randrange(len(_variants(tpl)))]
            vh, vw = len(var), len(var[0])
            if vh > h or vw > bw:
                continue
            r0 = rng.randint(0, h - vh)
            c0 = rng.randint(0, bw - vw)
            spots = [(r0 + r, c0 + c, var[r][c]) for r in range(vh)
                     for c in range(vw) if var[r][c] != 0]
            if any(board[r][c] != 0 for r, c, _ in spots):
                continue
            for r, c, v in spots:
                board[r][c] = v
            placed += 1
        if placed < want:
            continue

        # decoy clutter in non-template colors only
        decoy_pool = [v for v in _COLORS if v not in tpl_colors]
        for _ in range(rng.randint(2, 6)):
            r = rng.randrange(h)
            c = rng.randrange(bw)
            if board[r][c] == 0:
                board[r][c] = rng.choice(decoy_pool)

        hits = _match_cells(board, tpl)
        if texture == "no_match":
            if hits:
                continue  # accidental match — rebuild
        elif not hits:
            continue

        panels = [tpl_panel, board]
        if texture == "extra_panels":
            for _ in range(rng.randint(1, 2)):
                ep = full_grid(h, rng.randint(3, 4), 0)
                eshape = _grow(rng, rng.randint(1, 3))
                eh = max(r for r, _ in eshape) + 1
                ew = max(c for _, c in eshape) + 1
                if eh <= h and ew <= len(ep[0]):
                    er = rng.randint(0, h - eh)
                    ec = rng.randint(0, len(ep[0]) - ew)
                    color = rng.choice(_COLORS)
                    for r, c in eshape:
                        ep[er + r][ec + c] = color
                panels.append(ep)
        return _assemble(h, panels)
    raise ValueError("could not realize template-search board")


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: >=1 full-height color-9 divider; template panel (left of
    first divider) is non-empty; board panel is non-empty."""
    msgs = []
    h, w = len(grid), len(grid[0])
    div_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if not div_cols:
        msgs.append("no full-height color-9 divider found (rule would crash)")
        return msgs
    # Template: left of first divider
    tpl_cells = [(r, c) for r in range(h) for c in range(div_cols[0]) if grid[r][c] != 0]
    if not tpl_cells:
        msgs.append("template panel is empty (crop of empty panel crashes the rule)")
    # Board: right of first divider (skip further dividers)
    board_start = div_cols[0] + 1
    board_cells = [grid[r][c] for r in range(h) for c in range(board_start, w)
                   if grid[r][c] not in (0, 9)]
    if not board_cells:
        msgs.append("board panel has no non-{0,9} cells")
    return msgs
