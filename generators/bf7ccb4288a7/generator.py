"""Generator for arc_puzzle_bank_twelfth21:H83 — edge markers flood chambers.

Rule: color-5 walls form a grid of 0-filled chambers (with a 5 outer ring).
Each cell on the OUTER BORDER whose value is not 0/5 is a marker; it floods
its color into the adjacent chamber's 0-region. Chambers with no border
marker stay 0.

v1.1.0 was a WRONG-TASK generator: it drew a bg=0 "multi-motif gallery
pack" that has nothing to do with this rule (which needs 5-walls + chambers
+ border markers). Rewritten to construct exactly what the rule reads.

Combinatorial axes: macro_r / macro_c (chamber grid), ch / cw (chamber
size), n_markers, marker colors + border sides.
Degenerates: no_markers (chambers all stay 0), single_marker, full_walls.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bf7ccb4288a7"
VERSION = "2.0.0"  # WRONG-TASK rewrite: was bg=0 motif gallery; rule is 5-walled chamber grid with border markers that flood chambers. Now build 5-walls + 0-chambers + edge markers; vary macro grid / chamber size / marker count.
TASK_ID = "bf7ccb4288a7"

SUMMARY = ("Color-5 wall grid of 0-chambers (5 outer ring); border markers "
           "(non-0/5) flood the adjacent chamber with their color.")

INVARIANTS = [
    "walls are color 5; chamber interiors are 0",
    "outer ring is wall (5) except where markers sit",
    "each marker is on the outer border, inward-adjacent to a chamber 0-cell",
    "at most one marker per chamber (single flood color per region)",
]

DEGENERATE_TEXTURES = ("no_markers", "single_marker", "full_walls")
HELPFUL_TEXTURES = ()

AXES = {
    "macro_r":    {"type": "int", "default": "by difficulty", "valid": "2..4"},
    "macro_c":    {"type": "int", "default": "by difficulty", "valid": "2..4"},
    "ch":         {"type": "int", "default": "by difficulty", "valid": "2..4"},
    "cw":         {"type": "int", "default": "by difficulty", "valid": "2..4"},
    "n_markers":  {"type": "int", "default": "by difficulty", "valid": "1..N"},
    "texture":    {"type": "str", "default": "none",
                   "valid": "|".join(DEGENERATE_TEXTURES)},
}


def _border_marker_slots(macro_r, macro_c, ch, cw, rng):
    """All (chamber_key, border_row, border_col) options where a border cell is
    inward-adjacent to a chamber 0-cell. One slot per (chamber, side)."""
    h = macro_r * ch + (macro_r + 1)
    w = macro_c * cw + (macro_c + 1)
    slots = []
    for mr in range(macro_r):
        for mc in range(macro_c):
            r0 = 1 + mr * (ch + 1)
            c0 = 1 + mc * (cw + 1)
            key = (mr, mc)
            if mr == 0:                          # top border above this chamber
                slots.append((key, 0, c0 + rng.randrange(cw)))
            if mr == macro_r - 1:                # bottom border
                slots.append((key, h - 1, c0 + rng.randrange(cw)))
            if mc == 0:                          # left border
                slots.append((key, r0 + rng.randrange(ch), 0))
            if mc == macro_c - 1:                # right border
                slots.append((key, r0 + rng.randrange(ch), w - 1))
    return slots


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        macro_r = ctx.draw_int("macro_r", 2, 2); macro_c = ctx.draw_int("macro_c", 2, 2)
        ch = ctx.draw_int("ch", 2, 3); cw = ctx.draw_int("cw", 2, 3)
    elif difficulty == "hard":
        macro_r = ctx.draw_int("macro_r", 3, 4); macro_c = ctx.draw_int("macro_c", 3, 4)
        ch = ctx.draw_int("ch", 3, 4); cw = ctx.draw_int("cw", 3, 4)
    else:
        macro_r = ctx.draw_int("macro_r", 2, 4); macro_c = ctx.draw_int("macro_c", 2, 4)
        ch = ctx.draw_int("ch", 2, 4); cw = ctx.draw_int("cw", 2, 4)

    h = macro_r * ch + (macro_r + 1)
    w = macro_c * cw + (macro_c + 1)
    g = full_grid(h, w, 5)                        # everything is wall...
    for mr in range(macro_r):                     # ...carve 0-chambers
        for mc in range(macro_c):
            r0 = 1 + mr * (ch + 1)
            c0 = 1 + mc * (cw + 1)
            for r in range(r0, r0 + ch):
                for c in range(c0, c0 + cw):
                    g[r][c] = 0

    # one marker per chamber max: shuffle border slots, keep first per chamber.
    slots = _border_marker_slots(macro_r, macro_c, ch, cw, rng)
    rng.shuffle(slots)
    seen_keys = set()
    uniq = []
    for key, br, bc in slots:
        if key in seen_keys:
            continue
        seen_keys.add(key)
        uniq.append((br, bc))
    n_border = len(uniq)
    n_def = max(1, n_border // 2)
    n_markers = int(overrides.get("n_markers", n_def))
    n_markers = max(1, min(n_border, n_markers))
    colors = [1, 2, 3, 4, 6, 7, 8, 9]
    rng.shuffle(colors)
    for i, (br, bc) in enumerate(uniq[:n_markers]):
        g[br][bc] = colors[i % len(colors)]
    return g


def _zero_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 0
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def _bbox_cells(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def _is_border(r, c, h, w):
    return r == 0 or c == 0 or r == h - 1 or c == w - 1


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    markers = []
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v not in range(10):
                errors.append("grid values must be digits 0..9")
            if _is_border(r, c, h, w):
                if v == 0:
                    errors.append("outer border must be wall color 5 except marker cells")
                elif v != 5:
                    markers.append((r, c))
            elif v not in (0, 5):
                errors.append("non-wall marker colors must appear only on the outer border")
    if not markers:
        errors.append("normal sample must contain at least one border marker")
    comps = _zero_components(grid)
    if not comps:
        errors.append("normal sample must contain at least one 0-filled chamber")
        return errors
    owner = {}
    for i, cells in enumerate(comps):
        r0, c0, r1, c1 = _bbox_cells(cells)
        if r0 == 0 or c0 == 0 or r1 == h - 1 or c1 == w - 1:
            errors.append("0-chambers must not touch the outer border")
        for rr in range(r0, r1 + 1):
            for cc in range(c0, c1 + 1):
                if grid[rr][cc] != 0:
                    errors.append("each chamber component must be a solid rectangle of 0s")
                    break
        for cell in cells:
            owner[cell] = i
    marker_chambers = []
    for r, c in markers:
        adjacent = set()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and (nr, nc) in owner:
                adjacent.add(owner[(nr, nc)])
        if len(adjacent) != 1:
            errors.append("each border marker must be inward-adjacent to exactly one chamber")
        else:
            marker_chambers.append(next(iter(adjacent)))
    if len(marker_chambers) != len(set(marker_chambers)):
        errors.append("at most one marker may target each chamber")
    return errors


def _draw_from_degenerate(name, rng):
    # 2x2 chambers of 0 inside a 5-wall ring (ch=cw=2 -> 7x7).
    h = w = 7
    g = full_grid(h, w, 5)
    for r0 in (1, 4):
        for c0 in (1, 4):
            for r in range(r0, r0 + 2):
                for c in range(c0, c0 + 2):
                    g[r][c] = 0
    if name == "no_markers":
        return g                                  # chambers all stay 0
    if name == "single_marker":
        g[0][1] = 3                               # floods top-left chamber
        return g
    if name == "full_walls":
        return full_grid(h, w, 5)                 # no chambers at all
    return g
