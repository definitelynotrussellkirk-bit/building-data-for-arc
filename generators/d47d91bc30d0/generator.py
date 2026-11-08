"""Generator for 9b5080bb — container tabs recolored to the OTHER container's bg.

Rule (LIVE): two rectangular containers with background colors BG1/BG2 each
hold a solid blob of the same inner color IN. Each blob carries 2-cell "tab"
dominoes: a PROTRUSION of IN into the container background, or a DENT of the
background into the blob. The rule detects each tab's tip (a cell whose four
neighbors split 3-vs-1 between two colors) plus its partner, and recolors the
tab to the OTHER container's background color.

Combinatorial axes: grid_h/w, orientation (stacked/side-by-side), the four
colors (filler, BG1, BG2, IN), blob sizes/positions, tab count/kind/side.
Degenerates: no_tabs, one_container, solid_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d47d91bc30d0"
# 3.0.0: WRONG-TASK rewrite (defect-lint identity_demo). The old generator
# stamped 5x5 windows of a MEMORIZED lookup table for a rule that has since
# been replaced by the real containers/tabs rule — its instances usually had
# no detectable tab tips (tips need four in-bounds neighbors), so the live
# rule no-opped. New scene mirrors the canonical demos: filler frame, two
# touching containers, one IN blob each, and guaranteed detectable tabs in
# BOTH containers (the rule needs both backgrounds represented).
# 3.0.1: drop the dishonest HELPFUL_TEXTURES=palette-kinds declaration (colors
# are already free-drawn); caught by the defect-lint texture-override probe.
VERSION = "3.0.1"
TASK_ID = "d47d91bc30d0"
RULE_HASH = "0a09f9d1b4c9"  # canonical rule this generator was written against
SUMMARY = (
    "Filler-framed grid split into two touching rectangular containers "
    "(colors BG1/BG2), each holding a solid blob of the shared inner color "
    "IN with a margin. Each blob carries 1-3 tab dominoes: IN protrusions "
    "into the background or background dents into the blob, on straight edge "
    "segments away from corners. Rule: every tab is recolored to the OTHER "
    "container's background color. Both containers always carry at least one "
    "tab (the rule needs both backgrounds among the tab pairs)."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "four distinct colors: filler, BG1, BG2, shared inner IN",
    "two touching rectangular containers, each with one solid IN blob",
    "every tab tip has four in-bounds neighbors splitting 3-vs-1",
    "each container carries at least one tab",
]

# Colors are already free-drawn (draw_distinct_colors over all of 1..9) —
# palette-kind "helpful" textures would be a dishonest no-op declaration
# (defect-lint texture-dead).
DEGENERATE_TEXTURES = ("no_tabs", "one_container", "solid_grid")
HELPFUL_TEXTURES = ()

AXES = {
    "grid_h":      {"type": "int", "default": "18-20 easy / 19-23 med / 21-26 hard",
                    "valid": "18..26"},
    "grid_w":      {"type": "int", "default": "18-20 easy / 19-23 med / 21-26 hard",
                    "valid": "18..26"},
    "orientation": {"type": "str", "default": "rng", "valid": "stacked|side_by_side"},
    "n_tabs":      {"type": "int", "default": "1-2 easy / 1-3 med+hard (per blob)",
                    "valid": "1..3"},
    "texture":     {"type": "str", "default": "none",
                    "valid": "no_tabs|one_container|solid_grid"},
}


def _add_tabs(g, rng, blob, bg, inner, n_tabs):
    """Add tab dominoes on straight edge segments of a solid blob rect.

    blob = (r1, c1, r2, c2) inclusive. A PROTRUSION paints one IN cell just
    outside an edge (tip outside, partner on the edge); a DENT paints one
    edge cell to bg (tip on the edge, partner just outside). Rows/cols are
    chosen away from blob corners so the partner's neighborhood stays uniform,
    and used rows/cols are spaced >= 2 so tab neighborhoods never interact.
    Returns the number of tabs added.
    """
    r1, c1, r2, c2 = blob
    made = 0
    used: list[tuple[str, int]] = []
    for _try in range(60):
        if made >= n_tabs:
            break
        side = rng.choice(["left", "right", "top", "bottom"])
        if side in ("left", "right") and r2 - r1 >= 2:
            pos = rng.randint(r1 + 1, r2 - 1)
        elif side in ("top", "bottom") and c2 - c1 >= 2:
            pos = rng.randint(c1 + 1, c2 - 1)
        else:
            continue
        if any(s == side and abs(p - pos) < 2 for s, p in used):
            continue
        kind = rng.choice(["protrusion", "dent"])
        if side == "left":
            tip, edge = (pos, c1 - 1), (pos, c1)
        elif side == "right":
            tip, edge = (pos, c2 + 1), (pos, c2)
        elif side == "top":
            tip, edge = (r1 - 1, pos), (r1, pos)
        else:
            tip, edge = (r2 + 1, pos), (r2, pos)
        if kind == "protrusion":
            g[tip[0]][tip[1]] = inner
        else:
            g[edge[0]][edge[1]] = bg
        used.append((side, pos))
        made += 1
    return made


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 18, 20); w = ctx.draw_int("grid_w", 18, 20)
        tabs_hi = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 21, 26); w = ctx.draw_int("grid_w", 21, 26)
        tabs_hi = 3
    else:
        h = ctx.draw_int("grid_h", 19, 23); w = ctx.draw_int("grid_w", 19, 23)
        tabs_hi = 3
    filler, bg1, bg2, inner = ctx.draw_distinct_colors("colors", n=4, exclude={0})
    stacked = ctx.draw_choice("orientation", ["stacked", "side_by_side"]) == "stacked"

    for _layout in range(60):
        g = full_grid(h, w, filler)
        # Two touching containers filling most of the grid (1-cell filler frame).
        if stacked:
            split = rng.randint(7, h - 9)
            regions = [(1, 1, split, w - 2), (split + 1, 1, h - 2, w - 2)]
        else:
            split = rng.randint(7, w - 9)
            regions = [(1, 1, h - 2, split), (1, split + 1, h - 2, w - 2)]
        ok = True
        for (rr1, cc1, rr2, cc2), bg in zip(regions, (bg1, bg2)):
            for r in range(rr1, rr2 + 1):
                for c in range(cc1, cc2 + 1):
                    g[r][c] = bg
            # Solid IN blob with >=2 margin inside the container: a tab sticks
            # out 1 cell and its tip still needs one clean bg cell beyond.
            bh = rng.randint(3, max(3, min(6, rr2 - rr1 - 3)))
            bw = rng.randint(3, max(3, min(6, cc2 - cc1 - 3)))
            br = rng.randint(rr1 + 2, rr2 - 2 - bh + 1)
            bc = rng.randint(cc1 + 2, cc2 - 2 - bw + 1)
            for r in range(br, br + bh):
                for c in range(bc, bc + bw):
                    g[r][c] = inner
            if _add_tabs(g, rng, (br, bc, br + bh - 1, bc + bw - 1),
                         bg, inner, rng.randint(1, tabs_hi)) == 0:
                ok = False
                break
        if ok:
            return g
    raise ValueError("could not lay out two containers with tabs")


def _draw_from_degenerate(name, rng):
    g = full_grid(18, 18, 8)
    for r in range(1, 9):
        for c in range(1, 17):
            g[r][c] = 4
    for r in range(9, 17):
        for c in range(1, 17):
            g[r][c] = 2
    for r in range(3, 6):
        for c in range(4, 8):
            g[r][c] = 1
    for r in range(11, 14):
        for c in range(9, 13):
            g[r][c] = 1
    if name == "no_tabs":
        return g
    if name == "one_container":
        for r in range(9, 17):
            for c in range(1, 17):
                g[r][c] = 4
        g[4][8] = 1
        return g
    if name == "solid_grid":
        return full_grid(18, 18, 4)
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Mirror the rule's tip detector: both containers must carry >=1 detectable
    tab (tip with four in-bounds neighbors, 3-vs-1 split, uniform partner)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    dirs = ((1, 0), (-1, 0), (0, 1), (0, -1))
    pairs = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            vs = [grid[r + dr][c + dc] for dr, dc in dirs]
            uniq = set(vs)
            if len(uniq) != 2:
                continue
            x, y = sorted(uniq)
            cx = vs.count(x)
            if cx not in (1, 3):
                continue
            a, b = (x, y) if cx == 3 else (y, x)          # a = majority
            if grid[r][c] != b:
                continue
            partner = next(((r + dr, c + dc) for dr, dc in dirs
                            if grid[r + dr][c + dc] == b), None)
            if partner is None:
                continue
            pr, pc = partner
            pvs = [grid[pr + dr][pc + dc] for dr, dc in dirs
                   if 0 <= pr + dr < h and 0 <= pc + dc < w]
            if len(pvs) == 4 and all(v == b for v in pvs):
                pairs.append((a, b))
    if not pairs:
        return ["no detectable tab tips — the rule would be an identity"]
    inner = next((col for col in {c for p in pairs for c in p}
                  if all(col in p for p in pairs)), None)
    if inner is None:
        return ["tab pairs share no common inner color — the rule cannot resolve IN"]
    bgs = {c for p in pairs for c in p if c != inner}
    if len(bgs) != 2:
        return [f"tab pairs cover {len(bgs)} background(s); the rule needs exactly 2"]
    return []
