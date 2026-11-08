"""Generator for arc_puzzle_bank_21_set4:S4_H6.

A neutral color-1 template is copied into each color-5 frame and recolored to
the frame's interior marker color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_frames,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_template, no_frames, no_markers.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid
from puzzle_generators.helpers.selfcheck import components, interior_cells, is_full_frame_component

GENERATOR_ID = "cdb0009458df"
VERSION = "3.1.0"  # retry/scan placement until the promised frame count is realized  # shape-locked in+out: FIXED 18x18 + fixed frame origins/sizes (6x6) + template from a 3-bank + fixed marker offsets. Rule stamps the color-1 template into each color-5 frame interior in the marker colour; size-agnostic. Now vary grid + random template shape + 1-4 frames of varied sizes/positions + varied marker colours/positions. Output dims = input dims (varying grid clears the lock)."
TASK_ID = "cdb0009458df"
SUMMARY = (
    "A color-1 template motif plus several color-5 rectangular frames, each with "
    "one non-{0,5} interior marker. Rule: clear each marker and stamp the template "
    "into that frame's interior, recolored to the marker's color."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "one color-1 template object appears before the frames in reading order",
    "all target frames are color-5 rectangular outlines large enough to hold the template",
    "each frame has exactly one non-{0,1,5} interior marker",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_template", "no_frames", "no_markers")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 14..22", "valid": "12..28"},
    "grid_w":         {"type": "int", "default": "rng 14..22", "valid": "12..28"},
    "n_frames":       {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "tmpl_size":      {"type": "int", "default": "rng 3..6", "valid": "3..7"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "varied", "valid": "varied"},
    "position_bias":  {"type": "str", "default": "free", "valid": "free"},
    "n_distinct_colors": {"type": "int", "default": "varied", "valid": "varied"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_DEGEN_TEMPLATE = [(0, 0), (0, 1), (1, 0)]


def _paint(g, top, left, cells, color):
    for r, c in cells:
        g[top + r][left + c] = color


def _poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _place(g, rh, rw, draw_fn, rng):
    h, w = len(g), len(g[0])
    if rh > h or rw > w:
        return False
    for _ in range(1200):
        r0 = rng.randint(0, h - rh); c0 = rng.randint(0, w - rw)
        ok = True
        for r in range(max(0, r0 - 1), min(h, r0 + rh + 1)):
            for c in range(max(0, c0 - 1), min(w, c0 + rw + 1)):
                if g[r][c] != 0:
                    ok = False; break
            if not ok:
                break
        if ok:
            draw_fn(r0, c0); return True
    return False


def _place_scan(g, rh, rw, draw_fn):
    h, w = len(g), len(g[0])
    if rh > h or rw > w:
        return False
    for r0 in range(0, h - rh + 1):
        for c0 in range(0, w - rw + 1):
            ok = True
            for r in range(max(0, r0 - 1), min(h, r0 + rh + 1)):
                for c in range(max(0, c0 - 1), min(w, c0 + rw + 1)):
                    if g[r][c] != 0:
                        ok = False; break
                if not ok:
                    break
            if ok:
                draw_fn(r0, c0); return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        n_frames = ctx.draw_int("n_frames", 1, 2); h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 12, 16)
        tsz = ctx.draw_int("tmpl_size", 3, 4)
    elif difficulty == "hard":
        n_frames = ctx.draw_int("n_frames", 3, 4); h = ctx.draw_int("grid_h", 20, 28); w = ctx.draw_int("grid_w", 20, 28)
        tsz = ctx.draw_int("tmpl_size", 4, 7)
    else:
        n_frames = ctx.draw_int("n_frames", 1, 3); h = ctx.draw_int("grid_h", 14, 22); w = ctx.draw_int("grid_w", 14, 22)
        tsz = ctx.draw_int("tmpl_size", 3, 6)
    template = _poly(rng, tsz)
    th = max(r for r, _ in template) + 1; tw = max(c for _, c in template) + 1
    marker_colors = rng.sample([2, 3, 4, 6, 7, 8, 9], min(n_frames, 7))

    for _layout_attempt in range(40):
        g = full_grid(h, w, 0)
        if not _place(g, th, tw, lambda r0, c0: _paint(g, r0, c0, template, 1), rng):
            continue
        placed = 0
        for i in range(min(n_frames, len(marker_colors))):
            # each frame interior must hold the template -> interior >= th x tw
            fh = th + 2 + rng.randint(0, 3); fw = tw + 2 + rng.randint(0, 3)

            def _draw(r0, c0, fh=fh, fw=fw, col=marker_colors[i]):
                draw_frame(g, r0, c0, r0 + fh - 1, c0 + fw - 1, 5)
                # one interior marker at a random interior cell, distinct non-{0,1,5} color
                mr = rng.randint(r0 + 1, r0 + fh - 2); mc = rng.randint(c0 + 1, c0 + fw - 2)
                g[mr][mc] = col
            if _place(g, fh, fw, _draw, rng):
                placed += 1
        if placed == min(n_frames, len(marker_colors)):
            return g

    # Deterministic scan fallback: do not silently return a row with too few
    # frames just because random placement exhausted its attempts.
    g = full_grid(h, w, 0)
    _place_scan(g, th, tw, lambda r0, c0: _paint(g, r0, c0, template, 1))
    for i in range(min(n_frames, len(marker_colors))):
        fh = th + 2 + (i % 2)
        fw = tw + 2 + ((i // 2) % 2)

        def _draw(r0, c0, fh=fh, fw=fw, col=marker_colors[i]):
            draw_frame(g, r0, c0, r0 + fh - 1, c0 + fw - 1, 5)
            mr = min(r0 + fh - 2, r0 + 1 + (i % max(1, fh - 2)))
            mc = min(c0 + fw - 2, c0 + 1 + (i % max(1, fw - 2)))
            g[mr][mc] = col
        _place_scan(g, fh, fw, _draw)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(18, 18, 0)
    if name == "no_template":
        # frames without color-1 template → nothing to copy from
        draw_frame(g, 6, 1, 11, 6, 5)
        g[7][2] = 4
        return g
    if name == "no_frames":
        # template only, no frames → nowhere to copy template into
        _paint(g, 1, 1, _DEGEN_TEMPLATE, 1)
        return g
    if name == "no_markers":
        # template + frames but no interior markers → no recolor target
        _paint(g, 1, 1, _DEGEN_TEMPLATE, 1)
        draw_frame(g, 6, 1, 11, 6, 5)
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0] or len({len(row) for row in grid}) != 1:
        return ["grid must be a nonempty rectangle"]
    comps5 = components(grid, colors={5})
    frames = [comp for comp in comps5 if is_full_frame_component(comp, color=5, min_size=3)]
    n = len(frames)
    if difficulty == "easy":
        ok = 1 <= n <= 2
    elif difficulty == "hard":
        ok = 3 <= n <= 4
    else:
        ok = 1 <= n <= 3
    if not ok:
        msgs.append(f"unexpected frame count for {difficulty}: {n}")
    template = [comp for comp in components(grid, colors={1}) if comp["color"] == 1]
    if len(template) != 1:
        msgs.append(f"expected exactly one color-1 template object, found {len(template)}")
    else:
        tr1, tc1, tr2, tc2 = template[0]["bbox"]
        th, tw = tr2 - tr1 + 1, tc2 - tc1 + 1
        for comp in frames:
            r1, c1, r2, c2 = comp["bbox"]
            if (r2 - r1 - 1) < th or (c2 - c1 - 1) < tw:
                msgs.append(f"frame {comp['bbox']} interior cannot hold template {(th, tw)}")
    for comp in frames:
        vals = [grid[r][c] for r, c in interior_cells(comp["bbox"])
                if grid[r][c] not in (0, 1, 5)]
        if len(vals) != 1:
            msgs.append(f"frame {comp['bbox']} should have exactly one interior marker, found {vals}")
    return msgs
