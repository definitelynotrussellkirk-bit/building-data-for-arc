"""Generator for 776ffc46 — match template inside gray frame, recolor matching candidates.

Rule: find a color-5 hollow rectangular frame. Inside it, the template
= non-{0, 5} colored cells (one color = template_color). Then find
all color-1 components outside the frame. For each one whose normalized
cells exactly match the normalized template cells, recolor it to
template_color. Other 1-components stay as 1.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b75f0b915b2b"
# 2.1.0: template can also be a random connected polyomino (3-5 cells, fits the
# frame interior); non-matching candidates always differ from it -> richer
# template/candidate shapes while keeping the match-vs-non-match discriminator.
VERSION = "2.1.1"
TASK_ID = "b75f0b915b2b"
SUMMARY = (
    "0-bg grid (h, w~14-18) with: (a) "
    "ONE HOLLOW COLOR-5 (gray) "
    "RECTANGULAR FRAME (5-7 × 5-7) "
    "drawn at random interior "
    "position; (b) INSIDE the frame "
    "(with 1-cell buffer from walls), "
    "a TEMPLATE SHAPE (3-4 cells from "
    "a bank of 8 templates) painted "
    "in TEMPLATE_COLOR (random non-"
    "{0, 1, 5}); (c) OUTSIDE the "
    "frame, 2-5 BLUE (color-1) "
    "CANDIDATE SHAPES — at least one "
    "with normalized cells matching "
    "the template, and at least one "
    "with a different shape. Rule "
    "(MATCH TEMPLATE → RECOLOR "
    "CANDIDATES): identify the gray "
    "FRAME and TEMPLATE inside. "
    "NORMALIZE the template's cells. "
    "For EACH BLUE CANDIDATE outside "
    "the frame, NORMALIZE its cells "
    "and compare. If they MATCH the "
    "template's normalized pattern, "
    "RECOLOR the candidate to "
    "TEMPLATE_COLOR. Non-matching "
    "blue candidates stay color 1. "
    "Frame + template stay. Net: "
    "blue shapes matching the framed "
    "template get template's color; "
    "others stay blue."
)

# Rivals: 'output is input' refuted by demos with ≥1 matching cand.
# 'recolor ALL blue shapes' refuted by demos with non-matching blues
# staying blue. 'use color 1 for recolor' refuted by demos. 'pattern
# matching uses size only' refuted by demos with same-size different-
# shape blues that stay blue. 3 demos with ≥1 match + ≥1 non-match
# cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly one color-5 hollow rectangular frame (≥5x5)",
    "the frame's interior contains exactly one connected non-{0,5} template",
    "≥2 color-1 candidate components outside the frame",
    "≥1 candidate matches the template (normalized)",
    "≥1 candidate has a different normalized pattern",
]

AXES = {
    "grid_h":   {"type": "int", "default": "rng 14..18", "valid": "12..22"},
    "grid_w":   {"type": "int", "default": "rng 14..18", "valid": "12..22"},
    "n_candidates": {"type": "int", "default": "rng 3..5", "valid": "2..6"},
}


_TEMPLATES = [
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 1)],
    [(0, 1), (1, 0), (1, 1)],
    [(0, 0), (1, 0), (1, 1), (2, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 0)],
    [(0, 0), (1, 0), (2, 0), (2, 1)],
]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 color-5 frame cell; ≥2 color-1 candidates; ≥1 template cell (not 0/1/5)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    n5 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 5)
    n1 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 1)
    n_tpl = sum(1 for r in range(h) for c in range(w)
                if grid[r][c] not in (0, 1, 5))
    if n5 < 1:
        errs.append("no color-5 frame cells found")
    if n1 < 2:
        errs.append(f"found {n1} color-1 candidate cells, expected ≥2")
    if n_tpl < 1:
        errs.append("no template cells (non-{0,1,5}) found")
    return errs


def _poly(rng, n, max_dim):
    """Random connected polyomino of n cells within max_dim x max_dim."""
    for _ in range(40):
        cells = {(0, 0)}; frontier = [(0, 0)]
        while len(cells) < n and frontier:
            r, c = rng.choice(frontier)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            cand = cells | {(r + dr, c + dc)}
            rs = [p[0] for p in cand]; cs = [p[1] for p in cand]
            if (max(rs) - min(rs) + 1) <= max_dim and \
               (max(cs) - min(cs) + 1) <= max_dim and (r + dr, c + dc) not in cells:
                cells.add((r + dr, c + dc)); frontier.append((r + dr, c + dc))
        if len(cells) == n:
            r0 = min(p[0] for p in cells); c0 = min(p[1] for p in cells)
            return [(r - r0, c - c0) for (r, c) in sorted(cells)]
    return [(0, 0), (0, 1), (1, 0)]


def _normalize(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    minr, minc = min(rs), min(cs)
    return tuple(sorted((r - minr, c - minc) for r, c in cells))


def _free(g, r0, c0, cells, pad=1):
    h, w = len(g), len(g[0])
    for dr, dc in cells:
        rr, cc = r0 + dr, c0 + dc
        if not (0 <= rr < h and 0 <= cc < w):
            return False
        for ddr in range(-pad, pad + 1):
            for ddc in range(-pad, pad + 1):
                nr, nc = rr + ddr, cc + ddc
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0:
                    return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = rng.randint(12, 14); w = rng.randint(12, 14)
        n_match = rng.randint(1, 2); n_non = rng.randint(1, 2)
    elif difficulty == "hard":
        h = rng.randint(18, 24); w = rng.randint(18, 24)
        n_match = rng.randint(3, 5); n_non = rng.randint(3, 5)
    else:
        h = rng.randint(15, 18); w = rng.randint(15, 18)
        n_match = rng.randint(2, 3); n_non = rng.randint(2, 3)

    # template: either a bank template or a random small polyomino
    if rng.random() < 0.5:
        template = rng.choice(_TEMPLATES)
    else:
        template = _poly(rng, rng.randint(3, 5), 3)
    template_norm = _normalize(template)
    template_color = rng.choice([2, 3, 4, 6, 7, 8, 9])

    g = full_grid(h, w, 0)
    # Place frame at a random position. Frame size: 5x5 to 7x7.
    fh = rng.randint(5, 7); fw = rng.randint(5, 7)
    fr = rng.randint(0, h - fh)
    fc = rng.randint(0, w - fw)
    for c in range(fc, fc + fw):
        g[fr][c] = 5
        g[fr + fh - 1][c] = 5
    for r in range(fr, fr + fh):
        g[r][fc] = 5
        g[r][fc + fw - 1] = 5
    # Place template inside the frame (with 1-cell buffer from frame walls)
    th = max(r for r, _ in template) + 1
    tw = max(c for _, c in template) + 1
    inner_h = fh - 2
    inner_w = fw - 2
    if th > inner_h or tw > inner_w:
        template = [(0, 0), (0, 1), (1, 0)]
        template_norm = _normalize(template)
        th, tw = 2, 2
    tr = fr + 1 + rng.randint(0, inner_h - th)
    tc = fc + 1 + rng.randint(0, inner_w - tw)
    for dr, dc in template:
        g[tr + dr][tc + dc] = template_color

    # Place blue candidates outside the frame. Some match template, some don't.
    non_matching_pool = [t for t in _TEMPLATES if _normalize(t) != template_norm]
    placed = 0
    for _ in range(200):
        if placed >= n_match:
            break
        shape = template
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        # Must not overlap frame area
        if fr - 1 <= r0 + sh and r0 <= fr + fh and fc - 1 <= c0 + sw and c0 <= fc + fw:
            continue
        if not _free(g, r0, c0, shape):
            continue
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = 1
        placed += 1
    placed = 0
    for _ in range(200):
        if placed >= n_non:
            break
        shape = rng.choice(non_matching_pool)
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        if fr - 1 <= r0 + sh and r0 <= fr + fh and fc - 1 <= c0 + sw and c0 <= fc + fw:
            continue
        if not _free(g, r0, c0, shape):
            continue
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = 1
        placed += 1
    return g
