"""Generator for arc_puzzle_bank_21_set11_s:S11_E2 — fill frame
interiors with 8.

Rule: every object that is an exact rectangular outline (>=3x3,
cells == perimeter) gets its interior 0-cells filled with 8 — any
color of frame, INCLUDING 8 itself. Non-0 interior content is
preserved (only 0s fill). Non-frame objects are untouched.

Combinatorial axes: grid_h/w, n_frames, texture
(plain|occupied|nested|decoy_mix|eight_frame).
Degenerates: no_frames, solid_rects, frame_too_thin (all identity).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect_outline

GENERATOR_ID = "0ba3dcd34589"
VERSION = "2.0.1"
TASK_ID = "0ba3dcd34589"
SUMMARY = (
    "Rect outlines fill their empty interior with 8. occupied boards "
    "carry non-0 cells inside a frame (preserved - only 0s fill); "
    "nested boards put a frame INSIDE another's interior (both fill, "
    "the inner frame's border survives the outer fill); decoy_mix "
    "boards add broken rings / solid blocks (untouched) next to real "
    "frames; eight_frame boards use an 8-colored frame (still "
    "fills - the rule ignores frame color)."
)

# Rivals: 'interior content erased' refuted by occupied. 'only non-8
# frames count' refuted by eight_frame. 'any closed-ish shape fills'
# refuted by decoy_mix broken rings. 3 demos incl. >=1 occupied or
# nested board.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "frames are exact perimeter rectangles >=3x3",
    "occupied boards: >=1 non-0 cell strictly inside a frame",
    "nested boards: inner frame fully inside the outer interior",
]

DEGENERATE_TEXTURES = ("no_frames", "solid_rects", "frame_too_thin")
HELPFUL_TEXTURES = ("plain", "occupied", "nested", "decoy_mix",
                    "eight_frame")

AXES = {
    "grid_h":   {"type": "int", "default": "rng 7..13", "valid": "5..16"},
    "grid_w":   {"type": "int", "default": "rng 10..16", "valid": "9..20"},
    "n_frames": {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "texture":  {"type": "str", "default": "rng helpful",
                 "valid": "plain|occupied|nested|decoy_mix|eight_frame|"
                          "no_frames|solid_rects|frame_too_thin",
                 "doc": "occupied: interior content preserved; nested: "
                        "frame in a frame; decoy_mix: broken/solid "
                        "non-frames; eight_frame: 8-colored frame."},
}

_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)


def _mirror(g):
    h, w = len(g), len(g[0])
    seen = set()
    out = [row[:] for row in g]
    for r in range(h):
        for c in range(w):
            v = g[r][c]
            if v == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w \
                            and (nr, nc) not in seen and g[nr][nc] == v:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r1 = min(rr for rr, _ in cells)
            r2 = max(rr for rr, _ in cells)
            c1 = min(cc for _, cc in cells)
            c2 = max(cc for _, cc in cells)
            fh, fw = r2 - r1 + 1, c2 - c1 + 1
            perim = 2 * fw + 2 * (fh - 2)
            if fh >= 3 and fw >= 3 and len(cells) == perim and \
               all(rr in (r1, r2) or cc in (c1, c2) for rr, cc in cells):
                for rr in range(r1 + 1, r2):
                    for cc in range(c1 + 1, c2):
                        if out[rr][cc] == 0:
                            out[rr][cc] = 8
    return out


def _free(g, r0, c0, fh, fw):
    h, w = len(g), len(g[0])
    if r0 < 0 or c0 < 0 or r0 + fh > h or c0 + fw > w:
        return False
    return all(g[r][c] == 0
               for r in range(max(0, r0 - 1), min(h, r0 + fh + 1))
               for c in range(max(0, c0 - 1), min(w, c0 + fw + 1)))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain", "occupied",
                                              "nested", "decoy_mix",
                                              "eight_frame"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 10, 12)
        n_frames = ctx.draw_int("n_frames", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 14, 16)
        n_frames = ctx.draw_int("n_frames", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 7, 13)
        w = ctx.draw_int("grid_w", 10, 16)
        n_frames = ctx.draw_int("n_frames", 1, 3)
    rng = ctx.draw_rng("layout")

    for _attempt in range(150):
        g = full_grid(h, w, 0)
        colors = rng.sample(_COLORS, min(4, len(_COLORS)))
        if texture == "eight_frame":
            colors[0] = 8
        if texture == "nested":
            # outer frame big enough for an inner 3x3 + gap
            fh = rng.randint(7, min(9, h))
            fw = rng.randint(7, min(9, w))
            r0 = rng.randint(0, h - fh)
            c0 = rng.randint(0, w - fw)
            if not _free(g, r0, c0, fh, fw):
                continue
            draw_rect_outline(g, r0, c0, fh, fw, colors[0])
            ir = rng.randint(r0 + 2, r0 + fh - 5)
            ic = rng.randint(c0 + 2, c0 + fw - 5)
            draw_rect_outline(g, ir, ic, 3, 3, colors[1])
            n_left = n_frames - 1
        else:
            n_left = n_frames
        placed = 0
        first_frame = None
        for i in range(n_left):
            fh = rng.randint(3, min(6, h - 1))
            fw = rng.randint(3, min(6, w - 1))
            for _t in range(80):
                r0 = rng.randint(0, h - fh)
                c0 = rng.randint(0, w - fw)
                if _free(g, r0, c0, fh, fw):
                    draw_rect_outline(g, r0, c0, fh, fw,
                                      colors[(i + 2) % len(colors)]
                                      if texture == "nested" else
                                      colors[i % len(colors)])
                    if first_frame is None:
                        first_frame = (r0, c0, fh, fw)
                    placed += 1
                    break
        if texture != "nested" and placed == 0:
            continue
        if texture == "occupied" and first_frame:
            r0, c0, fh, fw = first_frame
            if fh > 2 and fw > 2:
                spots = [(r, c) for r in range(r0 + 1, r0 + fh - 1)
                         for c in range(c0 + 1, c0 + fw - 1)]
                rng.shuffle(spots)
                for r, c in spots[:rng.randint(1, min(2, len(spots)))]:
                    g[r][c] = rng.choice(_COLORS)
        if texture == "decoy_mix":
            kind = rng.choice(["solid", "broken"])
            if kind == "solid":
                bh, bw = rng.randint(3, 4), rng.randint(3, 4)
                for _t in range(60):
                    r0 = rng.randint(0, h - bh)
                    c0 = rng.randint(0, w - bw)
                    if _free(g, r0, c0, bh, bw):
                        for r in range(r0, r0 + bh):
                            for c in range(c0, c0 + bw):
                                g[r][c] = colors[-1]
                        break
            else:
                for _t in range(60):
                    r0 = rng.randint(0, h - 4)
                    c0 = rng.randint(0, w - 4)
                    if _free(g, r0, c0, 4, 4):
                        draw_rect_outline(g, r0, c0, 4, 4, colors[-1])
                        # punch a gap: no longer an exact outline
                        g[r0][c0 + rng.randint(1, 2)] = 0
                        break
        out = _mirror(g)
        if out == g:
            continue
        return g
    raise ValueError("could not realize frame-fill board")


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: >=1 valid rectangular frame (exact >=3x3 perimeter with
    >=1 interior 0-cell the rule would fill with 8)."""
    msgs = []
    h, w = len(grid), len(grid[0])
    def is_frame(r0, c0, fh, fw):
        if fh < 3 or fw < 3:
            return False
        for r in range(r0, r0 + fh):
            for c in range(c0, c0 + fw):
                on_edge = (r == r0 or r == r0 + fh - 1
                           or c == c0 or c == c0 + fw - 1)
                v = grid[r][c]
                if on_edge and v == 0:
                    return False
                if not on_edge and v == 0 and grid[r][c] == 0:
                    pass  # interior 0 — good
        # All edge cells non-zero; check they're the same color (frame)
        edge_colors = {grid[r][c]
                       for r in range(r0, r0 + fh)
                       for c in range(c0, c0 + fw)
                       if (r == r0 or r == r0 + fh - 1
                           or c == c0 or c == c0 + fw - 1)}
        return len(edge_colors) == 1  # monochrome perimeter
    found = False
    for r0 in range(h):
        for c0 in range(w):
            for fh in range(3, h - r0 + 1):
                for fw in range(3, w - c0 + 1):
                    if is_frame(r0, c0, fh, fw):
                        # Check >=1 interior 0-cell
                        interior_zeros = any(
                            grid[r][c] == 0
                            for r in range(r0 + 1, r0 + fh - 1)
                            for c in range(c0 + 1, c0 + fw - 1)
                        )
                        if interior_zeros:
                            found = True
                            break
                if found:
                    break
            if found:
                break
        if found:
            break
    if not found:
        msgs.append(
            "no valid >=3x3 monochrome rectangular frame with >=1 interior 0-cell "
            "(rule would produce identity output)"
        )
    return msgs


def _draw_from_degenerate(name, ctx):
    """All identity: no_frames (blank + dots), solid_rects (no
    interior 0s... solid blocks are not outlines), frame_too_thin
    (2x2 blocks fail the >=3 test). rng-varied."""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 7, 11)
    w = ctx.draw_int("grid_w", 10, 14)
    g = full_grid(h, w, 0)
    if name == "no_frames":
        for _ in range(rng.randint(0, 3)):
            g[rng.randrange(h)][rng.randrange(w)] = rng.choice(_COLORS)
        return g
    if name == "solid_rects":
        bh, bw = rng.randint(3, 4), rng.randint(3, 5)
        r0 = rng.randint(0, h - bh)
        c0 = rng.randint(0, w - bw)
        color = rng.choice(_COLORS)
        for r in range(r0, r0 + bh):
            for c in range(c0, c0 + bw):
                g[r][c] = color
        return g
    r0 = rng.randint(0, h - 2)
    c0 = rng.randint(0, w - 2)
    color = rng.choice(_COLORS)
    for r in range(r0, r0 + 2):
        for c in range(c0, c0 + 2):
            g[r][c] = color
    return g
