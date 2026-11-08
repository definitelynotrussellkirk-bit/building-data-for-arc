"""Generator for arc_puzzle_bank_21_set12_s:S12_M4 — connect blue and red via contact chain.

Rule: find the blue(1) and red(2) components; BFS the shortest path through the
object-adjacency graph (components touching by 4-adjacency) connecting them;
paint all components on that path color 8; erase everything else.

The earlier generator placed a straight LINE of single cells [1,3,4,6,2] plus a
disconnected distractor — so components were single cells (canonical uses
multi-cell blobs) and the shortest-path BFS was trivial (one linear route). This
version uses multi-cell blob segments AND adds connected DEAD-END branches
(adjacent to a chain node but off the shortest path, like canonical pair0's 7),
which the rule's BFS excludes — exercising the path discriminator.

Degenerates: no_blue, no_red, no_chain.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ee37b0acdd32"
VERSION = "3.1.0"  # multi-cell blob chain + connected dead-end branches (was single-cell line + disconnected distractor)
TASK_ID = "ee37b0acdd32"

SUMMARY = (
    "0-bg grid with a CONTACT CHAIN of multi-cell components from a blue(1) end "
    "to a red(2) end (intermediate colors 3/4/5/6), consecutive segments "
    "touching. Plus connected DEAD-END branches (a blob touching one chain node "
    "but off the path) and optional disconnected distractors. Rule: BFS the "
    "shortest blue->red object path, paint it 8, erase the rest. Chain length, "
    "blob sizes, colors, branches, orientation and grid shape vary."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly one blue(1) and one red(2) component",
    "consecutive chain segments touch (4-adjacency); non-consecutive do not",
    "dead-end branches touch one chain node but are off the shortest path",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blue", "no_red", "no_chain")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..14", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "rng 10..16", "valid": "9..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful", "valid": "|".join(PALETTE_KINDS)},
    "orientation":    {"type": "str", "default": "rng horizontal|vertical", "valid": "horizontal|vertical"},
    "chain_len":      {"type": "int", "default": "rng 4..6", "valid": "3..7"},
    "n_branch":       {"type": "int", "default": "rng 1..3", "valid": "0..4"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "3..8"},
    "position_bias":  {"type": "str", "default": "blue_red_chain_with_branches",
                       "valid": "blue_red_chain_with_branches"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "3..8"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _transpose(g):
    return [list(row) for row in zip(*g)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 11, 13)
        clen = ctx.draw_int("chain_len", 3, 4); nb = ctx.draw_int("n_branch", 0, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 14, 18)
        clen = ctx.draw_int("chain_len", 5, 7); nb = ctx.draw_int("n_branch", 2, 4)
    else:
        h = ctx.draw_int("grid_h", 10, 13); w = ctx.draw_int("grid_w", 12, 15)
        clen = ctx.draw_int("chain_len", 4, 6); nb = ctx.draw_int("n_branch", 1, 3)
    orientation = ctx.draw_choice("orientation", ["horizontal", "vertical"])
    rng = ctx.draw_rng("layout")

    # build horizontally; transpose at the end for vertical. Work on a tall-enough
    # canvas (W wide, H tall); for vertical we swap roles.
    H, W = (h, w) if orientation == "horizontal" else (w, h)
    g = full_grid(H, W, 0)
    th = rng.randint(1, 2)                              # band thickness
    # segment widths so the chain fits with room for a left margin
    widths = [rng.randint(1, 2) for _ in range(clen)]
    while sum(widths) > W - 2 and len(widths) > 3:
        widths.pop()
    clen = len(widths)
    total = sum(widths)
    r0 = rng.randint(1, max(1, H - th - 1))
    c0 = rng.randint(1, max(1, W - total - 1))
    mids = rng.sample([3, 4, 5, 6], min(4, max(0, clen - 2)))
    while len(mids) < clen - 2:
        mids.append(rng.choice([3, 4, 5, 6]))
    colors = [1] + mids[:clen - 2] + [2]

    seg_cols = []                                      # (color, col_lo, col_hi)
    cc = c0
    for color, wseg in zip(colors, widths):
        for r in range(r0, r0 + th):
            for c in range(cc, cc + wseg):
                g[r][c] = color
        seg_cols.append((color, cc, cc + wseg - 1))
        cc += wseg

    # dead-end branches: a blob just above/below a MIDDLE segment (off the path).
    # Use color 7 (never a chain endpoint and not used by the middle palette) so
    # the branch remains a separate component instead of merging into a same-color
    # chain segment.  The branch is important pedagogy: the shortest-path rule must
    # discard connected-but-off-path objects.
    placed_branch = 0
    for _ in range(nb):
        if clen <= 2:
            break
        idx = rng.randint(1, clen - 2)
        _, lo, hi = seg_cols[idx]
        candidates = []
        for bc in range(lo, hi + 1):
            for br in (r0 - 1, r0 + th):
                if 0 <= br < H and g[br][bc] == 0:
                    candidates.append((br, bc))
        rng.shuffle(candidates)
        if not candidates:
            continue
        br, bc = candidates[0]
        g[br][bc] = 7
        placed_branch += 1
    if nb > 0 and placed_branch == 0 and clen > 2:
        # The chosen random sites can be blocked in very tight grids; fail loudly
        # rather than silently emitting the old no-branch teaching shortcut.
        raise ValueError("could not place a dead-end branch")

    out = g if orientation == "horizontal" else _transpose(g)
    return out


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_blue":
        for i, color in enumerate([3, 4, 6, 2]):
            g[3][3 + i] = color
        g[h - 2][w - 3] = 7
        return g
    if name == "no_red":
        for i, color in enumerate([1, 3, 4, 6]):
            g[3][3 + i] = color
        g[h - 2][w - 3] = 7
        return g
    if name == "no_chain":
        g[2][2] = 1
        g[7][9] = 2
        g[h - 2][w - 3] = 7
        return g
    return g

def _count_components(grid, color):
    h = len(grid); w = len(grid[0]) if h else 0; seen = set(); n = 0
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            n += 1; stack = [(r, c)]; seen.add((r, c))
            while stack:
                rr, cc = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
    return n


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if _count_components(grid, 1) != 1:
        msgs.append("expected exactly one blue endpoint component")
    if _count_components(grid, 2) != 1:
        msgs.append("expected exactly one red endpoint component")
    has_branch = any(v == 7 for row in grid for v in row)
    if difficulty in (None, "hard") and not has_branch:
        msgs.append("default/hard instance has no visible dead-end branch")
    return msgs
