"""Generator for 1a244afd — magenta docks to nearest blue; rotated offset becomes orange.

Rule: background is CYAN (8). For each magenta (6) marker, find its nearest unused
blue (1) marker (Manhattan). Recolor the magenta to 8 (it blends back into the
cyan background). Compute offset (dr,dc)=magenta-blue and paint the cell at
blue + 90deg-rotated offset (br-dc, bc+dr) with ORANGE (7). Blue stays 1.

Prior generator (<=2.0.0) was WRONG-DISTRIBUTION: it used background 0 (canonical
bg is 8) and locked blue anchors to a 4-corner pool. On bg=0 the magenta->8 cells
show up as spurious 8s; on the real (cyan) background they vanish. This version
uses bg=8, scatters blue/magenta pairs freely, and keeps blues >=5 apart so each
magenta's nearest blue is unambiguously its own.

Rule-safe diversity: grid size, pair count, blue positions, per-pair offset.
Degenerates: no_pairs, single_pair, all_magenta.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f413b017af40"
VERSION = "3.0.0"  # bg 0->8 (canonical is cyan-bg) + free scattered pairs (was 4-corner anchors)
TASK_ID = "f413b017af40"
SUMMARY = (
    "CYAN(8)-bg grid (8-16) with 1-4 PAIRS of a BLUE(1) anchor and a MAGENTA(6) "
    "marker at a small offset (Manhattan<=2). Blues are >=5 apart so each magenta's "
    "nearest blue is its own. Rule: recolor each magenta to 8 (blends into bg) and "
    "paint the 90deg-rotated blue->magenta offset cell (br-dc, bc+dr) ORANGE(7); "
    "blue stays 1. Net: blue + an orange at the rotated offset; magenta vanishes "
    "into the cyan field. (Was: bg 0, blues locked to 4 corners.)"
)

BG = 8

INVARIANTS = [
    "background is 8 (cyan)",
    "equal numbers of blue(1) and magenta(6) markers (>=1 pair)",
    "each magenta is within Manhattan 2 of its blue; blues are >=5 apart",
    "each blue's 90-deg rotated offset cell stays in-bounds (so an orange appears)",
    "marker and rotated-offset cells don't collide across pairs",
]

# offsets with Manhattan distance <= 2 (excludes 0,0) -> magenta near its blue
OFFSETS = [(dr, dc) for dr in range(-2, 3) for dc in range(-2, 3)
           if (dr, dc) != (0, 0) and abs(dr) + abs(dc) <= 2]
DEGENERATE_TEXTURES = ("no_pairs", "single_pair", "all_magenta")
HELPFUL_TEXTURES = ("compact", "spread", "rotated")

AXES = {
    "grid_h":     {"type": "int", "default": "8-10 easy / 10-13 med / 13-16 hard", "valid": "8..18"},
    "grid_w":     {"type": "int", "default": "8-10 easy / 10-13 med / 13-16 hard", "valid": "8..18"},
    "pair_count": {"type": "int", "default": "1-2 easy / 2-3 med / 3-4 hard", "valid": "1..5"},
    "position_bias": {"type": "str", "default": "scattered", "valid": "scattered"},
    "texture":    {"type": "str", "default": "alias for position_bias",
                   "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        hr, pr = (8, 10), (1, 2)
    elif difficulty == "hard":
        hr, pr = (13, 16), (3, 4)
    else:
        hr, pr = (10, 13), (2, 3)
    h = rng.randint(*hr); w = rng.randint(*hr)
    pair_count = ctx.draw_int("pair_count", *pr)
    g = full_grid(h, w, BG)
    used = set()           # blue + magenta + reserved rotated-offset cells
    blues = []             # blue anchor positions (for >=5 separation)
    placed = 0
    for _ in range(pair_count * 60):
        if placed >= pair_count:
            break
        br = rng.randint(0, h - 1); bc = rng.randint(0, w - 1)
        if (br, bc) in used:
            continue
        if any(abs(br - pb) + abs(bc - pc) < 5 for pb, pc in blues):
            continue
        offs = OFFSETS[:]; rng.shuffle(offs)
        for dr, dc in offs:
            mr, mc = br + dr, bc + dc
            rr, rc = br - dc, bc + dr      # rule paints orange here
            cells = {(br, bc), (mr, mc), (rr, rc)}
            if (0 <= mr < h and 0 <= mc < w and 0 <= rr < h and 0 <= rc < w
                    and not (cells & used)):
                g[br][bc] = 1
                g[mr][mc] = 6
                used |= cells
                blues.append((br, bc))
                placed += 1
                break
    if placed == 0:                        # guarantee >=1 pair
        g[2][2] = 1; g[2][4] = 6
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 11, BG)
    if name == "no_pairs":
        return g
    if name == "single_pair":
        g[3][3] = 1; g[3][5] = 6
        return g
    if name == "all_magenta":            # magentas with no blue -> all vanish, no orange
        g[2][2] = 6; g[5][7] = 6; g[8][4] = 6
        return g
    return g



def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    blues = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
    mags = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 6]
    if any(v not in (1, 6, BG) for row in grid for v in row):
        errors.append("only bg=8, blue=1, and magenta=6 should appear in the input")
    lo = 1 if difficulty == "easy" else (3 if difficulty == "hard" else 2)
    if len(blues) < lo:
        errors.append(f"expected at least {lo} blue/magenta pairs, got {len(blues)}")
    if len(blues) != len(mags):
        errors.append("blue and magenta marker counts must match")
    used: set[int] = set()
    for br, bc in blues:
        found = None
        for i, (mr, mc) in enumerate(mags):
            if i in used:
                continue
            dr, dc = mr - br, mc - bc
            rr, rc = br - dc, bc + dr
            if ((dr, dc) != (0, 0) and abs(dr) + abs(dc) <= 2
                    and 0 <= rr < h and 0 <= rc < w
                    and (rr, rc) not in {(br, bc), (mr, mc)}):
                found = i
                break
        if found is None:
            errors.append("each blue must have a unique nearby magenta whose rotated orange cell is in bounds")
            break
        used.add(found)
    return errors
