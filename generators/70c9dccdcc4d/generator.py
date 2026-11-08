"""Generator for arc_puzzle_bank_21_set22_s:S22_H2 — diagonal-reflect 8-points across two L-frames.

Rule: input has two 3-cell L-frames:
  • SOURCE frame: corner cell color 2, with color 3 and color 4 on
    its two perpendicular cardinal neighbors (forming an L).
  • TARGET frame: corner cell color 5, with color 6 and color 7 on
    its two perpendicular cardinal neighbors (possibly different L
    orientation than source).
Plus some color-8 marker cells scattered near the source frame.
Rule extracts the 8-cells' (u, v) offsets from the source corner
in the source's local frame, diagonally reflects each (u, v) → (v, u),
remaps into the target frame's local axes, and paints 8 at those
positions in the output. Original frames + source 8-cells are
preserved.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "70c9dccdcc4d"
RULE_HASH = "06513d532f1c"  # sha256 of whitespace-normalized canonical rule
VERSION = "1.2.0"
TASK_ID = "70c9dccdcc4d"

SUMMARY = (
    "Two 3-cell L-frames in distinct color-triples ({2,3,4} for source "
    "with 2 at corner; {5,6,7} for target with 5 at corner). Several "
    "color-8 cells are placed near the source. Rule maps the 8-cells "
    "from source to target frame via diagonal reflection of their local "
    "(u, v) offsets, painting 8 at the corresponding target positions."
)

# Rivals: 'output is input' refuted by any demo where 8-cells appear
# near the target frame. 'use 5/6/7 as new 8-cells' refuted by any
# demo (output adds 8s, not target colors). 'translate without
# reflection' refuted by ≥1 demo where reflection vs translation
# differ. 'reflect across vertical only' refuted by ≥1 demo with
# off-axis 8-cells. 3 demos with varied frame orientations cover.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly one source L-frame in colors {2, 3, 4} (2 at the corner)",
    "exactly one target L-frame in colors {5, 6, 7} (5 at the corner)",
    "at least one color-8 cell near the source frame",
    "every color-8 source mark maps in-bounds to a blank target cell",
    "source and target frames are spatially separated",
]

AXES = {
    "grid_h": {"type": "int", "default": "easy 10..12; medium/None 11..14; hard 13..16", "valid": "9..18"},
    "grid_w": {"type": "int", "default": "easy 14..16; medium/None 16..20; hard 18..22", "valid": "12..24"},
    "n_marks": {"type": "int", "default": "easy 2..3; medium/None 3..5; hard 4..6", "valid": "1..6"},
}


def _l_frame_offsets(rng):
    """Return offsets relative to the corner for the two arms.

    Returns ((d1r, d1c), (d2r, d2c)) — two perpendicular unit dirs.
    """
    horiz = rng.choice([(0, -1), (0, 1)])
    vert = rng.choice([(-1, 0), (1, 0)])
    if rng.random() < 0.5:
        return horiz, vert
    return vert, horiz


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis: {', '.join(sorted(unknown))}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = rng.randint(10, 12); w = rng.randint(14, 16)
        n_marks = rng.randint(2, 3)
    elif difficulty == "hard":
        h = rng.randint(13, 16); w = rng.randint(18, 22)
        n_marks = rng.randint(4, 6)
    else:
        h = rng.randint(11, 14); w = rng.randint(16, 20)
        n_marks = rng.randint(3, 5)

    # Consume the original default draws even when an axis is pinned. This
    # preserves the existing unpinned seed stream and keeps VERSION unchanged.
    # Explicit pins use the full advertised domain, independently of difficulty,
    # and the shared strict draw records their provenance without coercion.
    if overrides.get("grid_h") is not None:
        h = ctx.draw_int_strict("grid_h", 9, 18)
    if overrides.get("grid_w") is not None:
        w = ctx.draw_int_strict("grid_w", 12, 24)
    if overrides.get("n_marks") is not None:
        n_marks = ctx.draw_int_strict("n_marks", 1, 6)

    g = full_grid(h, w, 0)

    # Place SOURCE frame somewhere in the left half (cols 2..w//2-2)
    for attempt in range(60):
        sr = rng.randint(3, h - 4)
        sc = rng.randint(3, w // 2 - 3)
        s2, s4 = _l_frame_offsets(rng)
        s2r, s2c = sr + s2[0], sc + s2[1]
        s4r, s4c = sr + s4[0], sc + s4[1]
        if not (0 <= s2r < h and 0 <= s2c < w and
                0 <= s4r < h and 0 <= s4c < w):
            continue
        break
    else:
        # Fallback
        sr, sc = h // 2, w // 4
        s2, s4 = (0, -1), (1, 0)
        s2r, s2c = sr, sc - 1
        s4r, s4c = sr + 1, sc
    # The canonical Racket rule calls find-frames with colors (2 3 4),
    # so 2 must be the frame origin/corner, with 3 and 4 on the two
    # perpendicular arms.  Earlier versions put 3 at the corner, which
    # made the generated source frame invisible to the real rule.
    g[sr][sc] = 2
    g[s2r][s2c] = 3
    g[s4r][s4c] = 4

    # Place TARGET frame in the right half (cols w//2+2..w-3)
    for attempt in range(60):
        tr = rng.randint(3, h - 4)
        tc = rng.randint(w // 2 + 2, w - 3)
        t6, t7 = _l_frame_offsets(rng)
        t6r, t6c = tr + t6[0], tc + t6[1]
        t7r, t7c = tr + t7[0], tc + t7[1]
        if not (0 <= t6r < h and 0 <= t6c < w and
                0 <= t7r < h and 0 <= t7c < w):
            continue
        # ensure target cells are still 0
        if g[tr][tc] != 0 or g[t6r][t6c] != 0 or g[t7r][t7c] != 0:
            continue
        break
    else:
        tr, tc = h // 2, w - w // 4
        t6, t7 = (0, 1), (1, 0)
        t6r, t6c = tr, tc + 1
        t7r, t7c = tr + 1, tc
    g[tr][tc] = 5
    g[t6r][t6c] = 6
    g[t7r][t7c] = 7

    # Place n_marks color-8 cells in SOURCE-LOCAL coordinates, not raw
    # grid offsets.  The rule extracts local (u, v) under the source frame,
    # swaps them, and renders (v, u) under the target frame.  Therefore each
    # chosen mark must have both a blank source cell and a blank in-bounds
    # reflected target cell; otherwise demos contain invisible/out-of-bounds
    # evidence or overwrite the target frame.
    source_frame_uv = {(0, 0), (1, 0), (0, 1)}
    target_frame_uv = {(0, 0), (1, 0), (0, 1)}
    candidates = [(u, v) for u in range(-3, 4) for v in range(-3, 4)
                  if (u, v) != (0, 0)
                  and (u, v) not in source_frame_uv
                  and (v, u) not in target_frame_uv]
    rng.shuffle(candidates)
    placed = 0
    used_source = set()
    used_target = set()
    for u, v in candidates:
        if placed >= n_marks:
            break
        mr = sr + u * s2[0] + v * s4[0]
        mc = sc + u * s2[1] + v * s4[1]
        trr = tr + v * t6[0] + u * t7[0]
        trc = tc + v * t6[1] + u * t7[1]
        if not (0 <= mr < h and 0 <= mc < w and 0 <= trr < h and 0 <= trc < w):
            continue
        if g[mr][mc] != 0 or g[trr][trc] != 0:
            continue
        if (trr, trc) == (mr, mc):
            continue
        if (mr, mc) in used_target or (trr, trc) in used_source or (trr, trc) in used_target:
            continue
        g[mr][mc] = 8
        used_source.add((mr, mc))
        used_target.add((trr, trc))
        placed += 1
    if placed != n_marks:
        raise RuntimeError(f"could place only {placed} of {n_marks} requested source marks")
    return g


_CARDINALS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _find_l_frames(g, colors):
    """Mirror the canonical Racket find-frames shape for a 3-cell L."""
    h, w = len(g), len(g[0])
    a, b, c = colors
    frames = []
    for r in range(h):
        for col in range(w):
            if g[r][col] != a:
                continue
            for vx in _CARDINALS:
                for vy in _CARDINALS:
                    if vx == vy or vx[0] * vy[0] + vx[1] * vy[1] != 0:
                        continue
                    br, bc = r + vx[0], col + vx[1]
                    cr, cc = r + vy[0], col + vy[1]
                    if (0 <= br < h and 0 <= bc < w and
                            0 <= cr < h and 0 <= cc < w and
                            g[br][bc] == b and g[cr][cc] == c):
                        frames.append(((r, col), vx, vy))
    return frames


def _local_pos(frame, p):
    (r0, c0), vx, vy = frame
    dr, dc = p[0] - r0, p[1] - c0
    return (dr * vx[0] + dc * vx[1], dr * vy[0] + dc * vy[1])


def _global_pos(frame, u, v):
    (r0, c0), vx, vy = frame
    return (r0 + u * vx[0] + v * vy[0], c0 + u * vx[1] + v * vy[1])


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be a non-empty rectangle"]
    h, w = len(grid), len(grid[0])
    sf = _find_l_frames(grid, (2, 3, 4))
    tf = _find_l_frames(grid, (5, 6, 7))
    if len(sf) != 1:
        msgs.append(f"expected exactly one 2/3/4 source L-frame; found {len(sf)}")
    if len(tf) != 1:
        msgs.append(f"expected exactly one 5/6/7 target L-frame; found {len(tf)}")
    marks = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 8]
    if not marks:
        msgs.append("expected at least one color-8 source mark")
    if len(sf) == 1 and len(tf) == 1:
        src, tgt = sf[0], tf[0]
        targets = []
        for mark in marks:
            u, v = _local_pos(src, mark)
            tr, tc = _global_pos(tgt, v, u)
            if not (0 <= tr < h and 0 <= tc < w):
                msgs.append("a reflected color-8 target is out of bounds")
                break
            if grid[tr][tc] != 0:
                msgs.append("a reflected color-8 target is not blank in the input")
                break
            targets.append((tr, tc))
        if len(set(targets)) != len(targets):
            msgs.append("two source marks collide after reflection into the target frame")
    return msgs
