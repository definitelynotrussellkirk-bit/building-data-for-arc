"""Generator for ARC task 137eaa0f.

Rule: `(rule! (lambda (g) (set-cell (assemble-at g 5 3) 1 1 5)))`.
Scattered color-5 anchors carry local 3×3 fragments. The rule gathers
each fragment around its anchor into a single 3×3 tile (the assemble-at
step), then writes a 5 to cell (1, 1) of that tile.

Combinatorial axes:
  * grid_size           — outer canvas (kept at 11 × 11 in canonical)
  * anchor_count        — how many anchors to plant (1..5)
  * anchor_layout       — how anchors sit: random / row / column /
                          corners / center_plus
  * fragment_density    — how many cells per fragment (1..7)
  * fragment_palette    — colors used in fragments (excludes 5)
  * fragment_overlap    — how much each anchor's fragment can extend
                          (1-cell ring vs full 3×3 vs partial cells)
  * caller-opt-in degenerates: single_anchor (output is one fragment),
                               empty_fragments (anchors only, no cells around),
                               overlapping_anchors (anchors too close)
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "479002373caf"
VERSION = "3.0.1"  # shape-locked-in: grid was hardcoded 11x11. Output is intrinsically 3x3 (assemble-at g 5 3), but the rule finds color-5 anchors on ANY grid size, so the INPUT grid now varies (9..15) -> input-shape variety. Anchor layouts are computed relative to the grid size.
TASK_ID = "479002373caf"
SUMMARY = (
    "FIXED 11×11 0-bg grid with 1-5 SCATTERED COLOR-5 "
    "ANCHORS placed by one of 5 ANCHOR LAYOUTS "
    "(random with ≥3-cell margin, row at fixed cols "
    "[2,5,8], column at fixed rows [2,5,8], corners "
    "[(2,2),(2,8),(8,2),(8,8)], center_plus [(5,5),"
    "(2,5),(5,2),(5,8),(8,5)]). EACH ANCHOR carries a "
    "LOCAL FRAGMENT — a subset of the 8 cells "
    "immediately surrounding it (offsets ring_only / "
    "full_3x3 / partial), where each fragment cell is "
    "painted with a color from a small non-{0, 5} "
    "palette (2-4 distinct colors), with fragment_"
    "density controlling how many of the 8 ring cells "
    "are filled. Anchors are spatially separated so "
    "fragments don't overlap. Rule (assemble-at + "
    "set-cell): GATHER each anchor's local 3×3 "
    "fragment (the anchor + its 8 neighbors) and "
    "MERGE these fragments cell-by-cell into ONE "
    "OUTPUT 3×3 TILE — overlaying each fragment "
    "around its anchor center, with later anchors "
    "overwriting earlier where they collide (or "
    "non-bg wins). After assembly, WRITE COLOR 5 at "
    "cell (1, 1) of the output tile (the center). "
    "OUTPUT is the 3×3 tile (much smaller than the "
    "11×11 input). Net: scattered anchor fragments "
    "are gathered into a single small composite "
    "tile with a central 5 marker."
)

INVARIANTS = [
    "input is 11×11",
    "each anchor is color 5 with nearby nonzero fragment cells",
    "fragment colors exclude anchor color 5",
    "anchors are spatially separated (3-cell margin) so their fragments don't merge",
]

ANCHOR_LAYOUTS = ("random", "row", "column", "corners", "center_plus")
FRAGMENT_OVERLAPS = ("ring_only", "full_3x3", "partial")
DEGENERATE_TEXTURES = ("single_anchor", "empty_fragments", "overlapping_anchors")
HELPFUL_TEXTURES = ANCHOR_LAYOUTS

AXES = {
    "grid_size":         {"type": "int", "default": "11", "valid": "9..15"},
    "anchor_count":      {"type": "int", "default": "rng 2..5", "valid": "1..6"},
    "anchor_layout":     {"type": "str", "default": "rng helpful",
                          "valid": "|".join(ANCHOR_LAYOUTS)},
    "fragment_density":  {"type": "int", "default": "rng 2..7", "valid": "1..8"},
    "fragment_palette_size": {"type": "int", "default": "rng 2..4", "valid": "1..7"},
    "fragment_overlap":  {"type": "str", "default": "rng ring_only|full_3x3|partial",
                          "valid": "|".join(FRAGMENT_OVERLAPS)},
    "texture":           {"type": "str", "default": "alias for anchor_layout",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    if difficulty == "easy":
        a_lo, a_hi, p_lo, p_hi, d_lo, d_hi, g_lo, g_hi = 2, 3, 2, 3, 2, 4, 9, 11
    elif difficulty == "hard":
        a_lo, a_hi, p_lo, p_hi, d_lo, d_hi, g_lo, g_hi = 4, 5, 3, 4, 5, 7, 12, 15
    else:
        a_lo, a_hi, p_lo, p_hi, d_lo, d_hi, g_lo, g_hi = 2, 5, 2, 4, 2, 7, 10, 13

    rng = ctx.draw_rng("fragments")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng, ctx)
    G = int(overrides.get("grid_size", ctx.draw_int("grid_size", g_lo, g_hi)))

    n_anchors = int(overrides.get("anchor_count",
                                  ctx.draw_int("anchor_count", a_lo, a_hi)))
    layout = (overrides.get("texture")
              or overrides.get("anchor_layout")
              or ctx.draw_choice("anchor_layout", list(ANCHOR_LAYOUTS)))
    n_palette = int(overrides.get("fragment_palette_size",
                                  ctx.draw_int("fragment_palette_size", p_lo, p_hi)))
    palette = ctx.draw_distinct_colors(
        "fragment_palette", n=max(1, n_palette), exclude={0, 5})
    density = int(overrides.get("fragment_density",
                                ctx.draw_int("fragment_density", d_lo, d_hi)))
    overlap = overrides.get(
        "fragment_overlap",
        ctx.draw_choice("fragment_overlap", list(FRAGMENT_OVERLAPS)))

    g = full_grid(G, G, 0)
    anchors = _anchor_pool(layout, n_anchors, rng, G)

    for i, (ar, ac) in enumerate(anchors):
        g[ar][ac] = 5
        offsets = _offsets_for(overlap)
        rng.shuffle(offsets)
        n_frag = max(1, min(density, len(offsets)))
        for j, (dr, dc) in enumerate(offsets[:n_frag]):
            r = ar + dr; c = ac + dc
            if 0 <= r < G and 0 <= c < G and g[r][c] == 0:
                g[r][c] = palette[(i + j) % len(palette)]
    return g


def _anchor_pool(layout, n, rng, G):
    """Pick n (r, c) anchor positions on the GxG grid with >=3-cell margin,
    using low/mid/high positions computed relative to the grid size."""
    lo, hi, mid = 2, G - 3, G // 2
    if layout == "row":
        r = rng.randint(lo, hi)
        return [(r, c) for c in (lo, mid, hi)][:n]
    if layout == "column":
        c = rng.randint(lo, hi)
        return [(r, c) for r in (lo, mid, hi)][:n]
    if layout == "corners":
        return [(lo, lo), (lo, hi), (hi, lo), (hi, hi)][:n]
    if layout == "center_plus":
        return [(mid, mid), (lo, mid), (mid, lo), (mid, hi), (hi, mid)][:n]
    # random with separation guarantee
    placed = []
    candidates = [(r, c) for r in range(lo, hi + 1) for c in range(lo, hi + 1)]
    rng.shuffle(candidates)
    for (r, c) in candidates:
        if all(abs(r - pr) > 2 or abs(c - pc) > 2 for (pr, pc) in placed):
            placed.append((r, c))
            if len(placed) >= n:
                break
    return placed[:n]


def _offsets_for(overlap):
    if overlap == "ring_only":
        return [(-1, -1), (-1, 0), (-1, 1),
                (0, -1),           (0, 1),
                (1, -1),  (1, 0),  (1, 1)]
    if overlap == "full_3x3":
        return [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                if not (dr == 0 and dc == 0)]
    # partial — corners + cardinals (8 cells, but mixed gating)
    return [(-1, -1), (-1, 1), (1, -1), (1, 1),
            (-1, 0), (1, 0), (0, -1), (0, 1)]


def _draw_from_degenerate(name, rng, ctx):
    """Edge-case where the assemble-at signature is hidden.

    single_anchor       — only one anchor; the assembled tile is just
                          its fragment; the rule still works but
                          there's no "gathering" to demonstrate.
    empty_fragments     — anchors only, no nearby cells; output is mostly
                          empty with just a 5 written at center.
    overlapping_anchors — anchors too close so fragments overlap; the
                          assemble-at result is ambiguous.
    """
    g = full_grid(11, 11, 0)
    palette = ctx.draw_distinct_colors("palette", n=3, exclude={0, 5})
    if name == "single_anchor":
        ar, ac = 5, 5
        g[ar][ac] = 5
        for dr, dc in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1)]:
            g[ar + dr][ac + dc] = rng.choice(palette)
        return g
    if name == "empty_fragments":
        for (r, c) in [(2, 2), (2, 8), (8, 5)]:
            g[r][c] = 5
        return g
    if name == "overlapping_anchors":
        # Two anchors only 1 cell apart — fragments collide.
        g[5][4] = 5
        g[5][6] = 5
        for dr, dc in [(-1, -1), (-1, 0), (-1, 1)]:
            g[5 + dr][4 + dc] = rng.choice(palette)
            g[5 + dr][6 + dc] = rng.choice(palette)
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """bg=0; at least one color-5 anchor; at least one non-{0,5} fragment cell."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    anchors = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    if not anchors:
        errors.append("no color-5 anchor cells found")
    fragments = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 5)]
    if not fragments:
        errors.append("no fragment cells (non-{0,5}) found around anchors")
    return errors
