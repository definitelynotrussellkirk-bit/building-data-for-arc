"""Generator for arc_additional_puzzles_21_set15_bundle:H104 — anchor-aligned overlap.

Rule: each multicolor 4-connected non-bg component has one anchor (color 9).
Translate each component so its anchor is at the origin, overlay all on a
common canvas: single-claim cells keep their color, double-claim cells become 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_anchor (a component lacks color-9 anchor → rule
cannot translate that component); single_component (only 1 → no
overlap with anything, no double-claim 8-cells); identical_components
(both components identical after anchor-translation → all cells
double-claim, output is all-8 with no contrast).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "81057a65827d"
VERSION = "1.2.0"
TASK_ID = "81057a65827d"

SUMMARY = "2 isolated multicolor components, each with one color-9 anchor + tail cells."

INVARIANTS = [
    "background is 0",
    "exactly 2 isolated 4-connected non-bg components",
    "each component contains exactly one color-9 anchor cell",
    "each component has 2-4 additional cells in non-9, non-0 colors, 4-connected to the anchor",
    "the two components are 4-conn separated by at least 1 bg cell",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_anchor", "single_component", "identical_components")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "grid_w":            {"type": "int", "default": "rng 11..14", "valid": "10..18"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "position_bias":     {"type": "str", "default": "two_anchored_components",
                          "valid": "two_anchored_components"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _make_component(rng, k):
    cells = [(0, 0, 9)]
    seen = {(0, 0)}
    while len(cells) < k + 1:
        r, c, _ = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc, 0))
            seen.add((nr, nc))
    palette = [2, 3, 4, 5, 6, 7]
    out = []
    for r, c, v in cells:
        if v == 9:
            out.append((r, c, 9))
        else:
            out.append((r, c, rng.choice(palette)))
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 13, 14)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 11, 14)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        ok = True
        for ci in range(2):
            k = rng.randint(2, 4)
            comp = _make_component(rng, k)
            rs = [r for r, _, _ in comp]
            cs = [c for _, c, _ in comp]
            r0, c0 = -min(rs), -min(cs)
            sh = max(rs) - min(rs) + 1
            sw = max(cs) - min(cs) + 1
            placed = False
            for _ in range(80):
                ar = rng.randint(0, h - sh)
                ac = rng.randint(0, w - sw)
                if not _free(g, ar, ac, ar + sh - 1, ac + sw - 1):
                    continue
                for r, c, v in comp:
                    g[ar + r0 + r][ac + c0 + c] = v
                placed = True
                break
            if not placed:
                ok = False
                break
        if ok and _has_partial_anchor_overlay(g):
            return g
    raise ValueError("could not place 2 partially-overlapping anchor components in 40 attempts")


def _components(g):
    h, w = len(g), len(g[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or g[r][c] == 0:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and g[nr][nc] != 0
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append(cells)
    return out


def _anchor_overlay_counts(g):
    rel_counts = {}
    for cells in _components(g):
        anchors = [(r, c) for r, c in cells if g[r][c] == 9]
        if len(anchors) != 1:
            return None
        ar, ac = anchors[0]
        for r, c in cells:
            key = (r - ar, c - ac)
            rel_counts[key] = rel_counts.get(key, 0) + 1
    overlaps = sum(1 for n in rel_counts.values() if n > 1)
    singles = sum(1 for n in rel_counts.values() if n == 1)
    return overlaps, singles


def _has_partial_anchor_overlay(g):
    counts = _anchor_overlay_counts(g)
    return bool(counts and counts[0] >= 1 and counts[1] >= 1)


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    comps = _components(grid)
    if len(comps) != 2:
        msgs.append(f"expected exactly 2 nonzero components, got {len(comps)}")
    for idx, cells in enumerate(comps):
        anchors = [(r, c) for r, c in cells if grid[r][c] == 9]
        if len(anchors) != 1:
            msgs.append(f"component {idx} has {len(anchors)} anchors, expected 1")
        if not (3 <= len(cells) <= 5):
            msgs.append(f"component {idx} size {len(cells)} outside 3..5")
    counts = _anchor_overlay_counts(grid)
    if not counts:
        msgs.append("cannot compute anchor-aligned overlay")
    else:
        overlaps, singles = counts
        if overlaps < 1:
            msgs.append("anchor-aligned overlay has no overlap cells")
        if singles < 1:
            msgs.append("anchor-aligned overlay has no single-claim cells; rule collapses to all-8")
    return msgs


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_anchor":
        # Components lack color-9 anchors — rule cannot translate them.
        g[2][2] = 4; g[2][3] = 4; g[3][2] = 5
        g[6][8] = 6; g[7][8] = 7; g[7][9] = 4
        return g
    if name == "single_component":
        # Only 1 component — no overlap, no 8-cells generated.
        g[3][3] = 9; g[3][4] = 4; g[4][3] = 5
        return g
    if name == "identical_components":
        # Both components identical after anchor translation — output all-8.
        g[2][2] = 9; g[2][3] = 4; g[3][2] = 5
        g[6][8] = 9; g[6][9] = 4; g[7][8] = 5
        return g
    return g
