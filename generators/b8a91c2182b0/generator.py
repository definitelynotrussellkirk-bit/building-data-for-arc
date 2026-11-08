"""Generator for arc_additional_puzzle_bank_volume7:M49.

Rule: among the color-2 objects that have exactly one enclosed 0-hole,
pick the largest by cell count and paint its hole cells with 8 on a blank
grid.

This generator draws K hollow color-2 frames (each with one hole) of
distinct cell counts; the largest's hole is the output.

Combinatorial axes: grid size, frame count, the frame sizes/positions.
Degenerates: no_frames, solid_only, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_frame

GENERATOR_ID = "b8a91c2182b0"
VERSION = "2.1.1"
TASK_ID = "b8a91c2182b0"
SUMMARY = (
    "0-bg grid (size varies) with K (2-4) hollow color-2 frames, each "
    "enclosing one hole, of distinct cell counts. Rule: take the largest "
    "one-hole frame and paint its hole cells 8 on a blank grid. The grid "
    "size, frame count and sizes/positions vary freely (was a fixed setup, "
    "~26 distinct)."
)

INVARIANTS = [
    "every frame is a closed color-2 ring enclosing exactly one hole",
    "frames have distinct cell counts so the largest is unambiguous",
    "the output is the largest frame's hole in color 8",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "solid_only", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..24"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..24"},
    "n_frames":       {"type": "int", "default": "varies", "valid": "2..4"},
    "frame_size":     {"type": "int", "default": "varies", "valid": "3..8"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "scattered_frames",
                       "valid": "scattered_frames"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_frames|solid_only|full_grid"},
}


def _reserve(occ, top, left, sh, sw, h, w, margin=1):
    for r in range(top - margin, top + sh + margin):
        for c in range(left - margin, left + sw + margin):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + sh):
        for c in range(left, left + sw):
            occ[r][c] = True
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: all nonzero values are 2 (only color-2 frames/blocks allowed)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    bad = [(r, c, grid[r][c]) for r in range(h) for c in range(w)
           if grid[r][c] not in (0, 2)]
    if bad:
        return [f"non-{{0,2}} cells found: {bad[:3]}"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, wr, kr, fr = (12, 15), (12, 16), (2, 2), (3, 5)
    elif difficulty == "hard":
        hr, wr, kr, fr = (18, 24), (18, 24), (3, 4), (3, 8)
    else:
        hr, wr, kr, fr = (14, 19), (14, 20), (2, 3), (3, 6)

    for _attempt in range(40):
        K = rng.randint(*kr)
        # frames with distinct cell counts (perimeter = 2*(fh+fw)-4)
        frames = []; perims = set()
        for _t in range(80):
            fh = rng.randint(*fr); fw = rng.randint(*fr)
            per = 2 * (fh + fw) - 4
            if per in perims:
                continue
            perims.add(per); frames.append((fh, fw))
            if len(frames) == K:
                break
        if len(frames) < K:
            continue

        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        placed = 0
        for (fh, fw) in frames:
            for _p in range(50):
                if fh > h or fw > w:
                    break
                top = rng.randint(0, h - fh); left = rng.randint(0, w - fw)
                if _reserve(occ, top, left, fh, fw, h, w):
                    draw_frame(g, top, left, top + fh - 1, left + fw - 1, 2)
                    placed += 1
                    break
        if placed >= 2:
            # Optionally drop 1-2 SOLID color-2 blocks (no hole). The rule
            # filters to frames with exactly one enclosed hole, so solid
            # blocks are ignored regardless of size -> exercises the filter.
            n_solid = rng.randint(0, 2)
            for _s in range(n_solid):
                bh = rng.randint(2, 4); bw = rng.randint(2, 4)
                for _p in range(40):
                    if bh > h or bw > w:
                        break
                    top = rng.randint(0, h - bh); left = rng.randint(0, w - bw)
                    if _reserve(occ, top, left, bh, bw, h, w):
                        for r in range(top, top + bh):
                            for c in range(left, left + bw):
                                g[r][c] = 2
                        break
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(13, 13, 0)
    draw_frame(g, 1, 1, 5, 5, 2)
    draw_frame(g, 7, 7, 11, 11, 2)
    if name == "no_frames":
        return full_grid(13, 13, 0)
    if name == "solid_only":
        g2 = full_grid(13, 13, 0)
        for r in range(2, 5):
            for c in range(2, 5):
                g2[r][c] = 2
        return g2
    if name == "full_grid":
        return full_grid(13, 13, 2)
    return g
