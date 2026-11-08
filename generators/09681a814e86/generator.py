"""Generator for db118e2a — frame the motif twice on a 15x15 canvas.

Rule: bg = cell (0,0). frame-color = first row-0 cell that differs
from bg (falls back to bg if none). Interior non-bg cells form the
motif; its bbox pads up to 3x3 minimum. Output: 15x15 bg canvas with
two open-cornered frames (edges only) in the frame color at (2,2) and
(8,8), each wrapping a copy of the motif.

Combinatorial axes: motif size/colors, indicator col/color, texture
(plain|thin_motif|single_cell|big_motif).
Degenerates: no_indicator (frame color falls back to bg=0: invisible
frames, motifs copied alone). no_motif/full_grid CRASH the rule
((min-list '())) and are never generated.

NOTE: the old generator drew a FULL border frame, which made bg ==
frame color and turned every interior 0 into a 'motif cell' — the
frame-color detection branch was dead and the whole 7x7 interior got
copied. Rebuilt to the rule's natural reading.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "09681a814e86"
VERSION = "2.1.1"  # vary input grid dims (was fixed 9x9) to clear shape-locked-in; rule is input-size-agnostic
TASK_ID = "09681a814e86"
SUMMARY = (
    "Row-0 indicator picks the frame color; the interior motif (bbox "
    "up to 5x5, padded to >=3x3) is wrapped in two open-cornered "
    "frames at fixed canvas spots. thin/single-cell motifs exercise "
    "the padding; big 5x5 motifs fill the frame."
)

# Rivals: 'frame color comes from the motif' refuted by independent
# indicator colors. 'motif must be 3x3' refuted by padded thin/single
# motifs and 5x5 ones. 'frames have corners' refuted by every demo
# (edges only). 3 demos with varied motif sizes.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "(0,0) is 0 (bg) and row 0 holds exactly one non-zero indicator",
    ">=1 interior motif cell ALWAYS (none crashes the rule)",
    "motif bbox <= 5x5 so both frames fit the 15x15 canvas",
]

DEGENERATE_TEXTURES = ("no_indicator",)
HELPFUL_TEXTURES = ("plain", "thin_motif", "single_cell", "big_motif")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 8..11", "valid": "7..12"},
    "grid_w":  {"type": "int", "default": "rng 8..11", "valid": "7..12"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|thin_motif|single_cell|big_motif|no_indicator",
                "doc": "thin_motif: 1-row/1-col motif (bbox pads to 3); "
                       "single_cell: 1x1 motif; big_motif: 5x5 bbox."},
}

_COLORS = (1, 2, 3, 4, 5, 6, 7, 8, 9)


def _mirror(g):
    h, w = len(g), len(g[0])
    bg = g[0][0]
    frame = next((g[0][c] for c in range(1, w - 1) if g[0][c] != bg), bg)
    cells = [(r, c, g[r][c]) for r in range(1, h - 1)
             for c in range(1, w - 1) if g[r][c] != bg]
    if not cells:
        return None
    ir1 = min(r for r, _, _ in cells)
    ir2 = max(r for r, _, _ in cells)
    ic1 = min(c for _, c, _ in cells)
    ic2 = max(c for _, c, _ in cells)
    bh, bw = ir2 - ir1 + 1, ic2 - ic1 + 1
    if bh < 3:
        ir1 -= (3 - bh) // 2
        bh = 3
    if bw < 3:
        ic1 -= (3 - bw) // 2
        bw = 3
    out = [[bg] * 15 for _ in range(15)]

    def place(tr, tc):
        fr, fc = bh + 2, bw + 2
        for c in range(tc + 1, tc + fc - 1):
            if 0 <= tr < 15 and 0 <= c < 15:
                out[tr][c] = frame
            if 0 <= tr + fr - 1 < 15 and 0 <= c < 15:
                out[tr + fr - 1][c] = frame
        for r in range(tr + 1, tr + fr - 1):
            if 0 <= r < 15 and 0 <= tc < 15:
                out[r][tc] = frame
            if 0 <= r < 15 and 0 <= tc + fc - 1 < 15:
                out[r][tc + fc - 1] = frame
        for r, c, v in cells:
            rr, cc = tr + 1 + r - ir1, tc + 1 + c - ic1
            if 0 <= rr < 15 and 0 <= cc < 15:
                out[rr][cc] = v

    place(2, 2)
    place(8, 8)
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "thin_motif", "single_cell",
                        "big_motif"))
    rng = ctx.draw_rng("layout")
    # Input grid dims vary: the rule is input-size-agnostic (it reads
    # bg=(0,0), frame color from row 0, and the interior motif's bbox).
    # Output is always 15x15 (rule-intrinsic). Varying h/w clears the
    # shape-locked-IN flag while staying rule-safe (motif bbox <= 5x5,
    # interior is rows 1..h-2 / cols 1..w-2).
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 10, 12)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 8, 11)
    g = full_grid(h, w, 0)
    frame_color = rng.choice(_COLORS)
    g[0][rng.randint(1, w - 2)] = frame_color
    # interior usable region: rows 1..h-2, cols 1..w-2
    ri_hi, ci_hi = h - 2, w - 2  # inclusive max interior index

    if texture == "single_cell":
        g[rng.randint(2, ri_hi)][rng.randint(2, ci_hi)] = rng.choice(_COLORS)
        return g
    if texture == "thin_motif":
        k = rng.randint(2, 4)
        color = rng.choice(_COLORS)
        if rng.random() < 0.5:
            r = rng.randint(2, ri_hi)
            c0 = rng.randint(1, max(1, ci_hi - k + 1))
            for i in range(k):
                if c0 + i <= ci_hi:
                    g[r][c0 + i] = color if rng.random() < 0.7 \
                        else rng.choice(_COLORS)
        else:
            c = rng.randint(2, ci_hi)
            r0 = rng.randint(1, max(1, ri_hi - k + 1))
            for i in range(k):
                if r0 + i <= ri_hi:
                    g[r0 + i][c] = color if rng.random() < 0.7 \
                        else rng.choice(_COLORS)
        return g
    max_bh = min(5, ri_hi)        # motif rows must fit interior and <=5
    max_bw = min(5, ci_hi)
    bh = max_bh if texture == "big_motif" else rng.randint(3, max(3, max_bh))
    bw = max_bw if texture == "big_motif" else rng.randint(3, max(3, max_bw))
    bh = min(bh, ri_hi)
    bw = min(bw, ci_hi)
    r0 = rng.randint(1, max(1, ri_hi - bh + 1))
    c0 = rng.randint(1, max(1, ci_hi - bw + 1))
    colors = rng.sample(_COLORS, rng.randint(1, 3))
    # corners of the bbox always present so the bbox is realized
    for r, c in ((0, 0), (0, bw - 1), (bh - 1, 0), (bh - 1, bw - 1)):
        g[r0 + r][c0 + c] = rng.choice(colors)
    for r in range(bh):
        for c in range(bw):
            if g[r0 + r][c0 + c] == 0 and rng.random() < 0.35:
                g[r0 + r][c0 + c] = rng.choice(colors)
    return g


def _draw_from_degenerate(name, ctx):
    """no_indicator — row 0 all zero: frame color falls back to bg=0,
    the frames paint invisibly and only the motif copies appear."""
    rng = ctx.draw_rng("degenerate_layout")
    g = full_grid(9, 9, 0)
    color = rng.choice(_COLORS)
    r0 = rng.randint(2, 5)
    c0 = rng.randint(2, 5)
    for dr, dc in ((0, 0), (0, 1), (1, 0)):
        g[r0 + dr][c0 + dc] = color
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """(0,0) is bg(0), row 0 has >=1 non-zero indicator, interior has >=1 motif cell."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    if grid[0][0] != 0:
        errors.append(f"(0,0) = {grid[0][0]}; expected bg=0")
    indicator_count = sum(1 for c in range(1, w) if grid[0][c] != 0)
    if indicator_count == 0:
        errors.append("no non-zero indicator in row 0 — frame color falls back to bg")
    interior = any(grid[r][c] != 0 for r in range(1, h - 1) for c in range(1, w - 1))
    if not interior:
        errors.append("no interior motif cell — rule crashes at (min-list '())")
    return errors
