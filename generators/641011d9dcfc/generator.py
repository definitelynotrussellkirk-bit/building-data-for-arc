"""Generator for arc_puzzle_bank_21_set4:S4_H2 — corner marker rotates template.

A top-left color-2 template is rotated into each color-5 frame according
to which interior corner contains a color-8 marker.

Combinatorial axes (8): n_frames, template, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_template, no_frames, no_marker.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "641011d9dcfc"
VERSION = "2.0.2"
TASK_ID = "641011d9dcfc"
SUMMARY = (
    "0-bg grid (~11-26 × 13-28) with: (a) ONE "
    "color-2 (red) TEMPLATE polyomino (4-cells) "
    "placed near the top-left; (b) 1-5 hollow color-5 "
    "(gray) RECTANGULAR FRAMES (5×5 or 6×6) at "
    "random non-overlapping positions, each with a "
    "single color-8 (cyan) MARKER in one of its 4 "
    "interior corners (TL, TR, BR, BL). Rule: for "
    "each frame, read the marker's corner and select "
    "the corresponding ROTATION of the template: "
    "TL=0°, TR=90° CW, BR=180°, BL=90° CCW. STAMP "
    "the rotated template (in color 2) inside the "
    "frame anchored at the frame's TL+1 interior. "
    "CLEAR the cyan marker. The original template + "
    "frame walls stay. Net: each frame gets a "
    "rotated copy of the template oriented by its "
    "corner marker."
)

# Rivals: 'output is input' refuted by demos (8 becomes 0, template
# stamps in frames). 'use color 5 for stamp' refuted by demos (uses
# 2). 'don't rotate' refuted by demos with TR/BR/BL marker producing
# rotated stamp. 'stamp without clearing 8' refuted by demos (8
# vanishes). 4 demos with markers at distinct corners cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "one color-2 template object appears before the frames in reading order",
    "all target frames are color-5 rectangular outlines",
    "each frame has one color-8 marker in an interior corner",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_template", "no_frames", "no_marker")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "n_frames":       {"type": "int", "default": "easy 1..2 / med 2..4 / hard 3..5",
                       "valid": "1..5"},
    "template":       {"type": "int", "default": "rng 0..2", "valid": "0..2"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "template_topleft_frames_below",
                       "valid": "template_topleft_frames_below"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

def _find_frames(grid):
    h, w = len(grid), len(grid[0])
    frames = []
    for r1 in range(h):
        for c1 in range(w):
            if grid[r1][c1] != 5:
                continue
            for r2 in range(r1 + 4, min(h, r1 + 6)):
                for c2 in range(c1 + 4, min(w, c1 + 6)):
                    if not (r2 - r1 + 1 in (5, 6) and c2 - c1 + 1 in (5, 6)):
                        continue
                    ok = True
                    for c in range(c1, c2 + 1):
                        if grid[r1][c] != 5 or grid[r2][c] != 5:
                            ok = False
                            break
                    if not ok:
                        continue
                    for r in range(r1, r2 + 1):
                        if grid[r][c1] != 5 or grid[r][c2] != 5:
                            ok = False
                            break
                    if not ok:
                        continue
                    frames.append((r1, c1, r2, c2))
    return frames


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify template plus the promised number of framed corner markers."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    c2 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 2)
    if c2 < 4:
        errs.append("no color-2 template cell found")
    frames = _find_frames(grid)
    markers = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    min_frames = 3 if difficulty == "hard" else (1 if difficulty == "easy" else 2)
    if len(frames) < min_frames:
        errs.append(f"expected at least {min_frames} color-5 frames for difficulty={difficulty}, found {len(frames)}")
    if len(markers) != len(frames):
        errs.append(f"expected one color-8 marker per frame, found {len(markers)} markers for {len(frames)} frames")
    for mr, mc in markers:
        containing = [fr for fr in frames if fr[0] < mr < fr[2] and fr[1] < mc < fr[3]]
        if len(containing) != 1:
            errs.append("color-8 marker is not inside exactly one frame")
            continue
        r1, c1, r2, c2 = containing[0]
        if (mr, mc) not in ((r1 + 1, c1 + 1), (r1 + 1, c2 - 1),
                            (r2 - 1, c2 - 1), (r2 - 1, c1 + 1)):
            errs.append("color-8 marker is not in an interior corner")
    return errs


_TEMPLATES = [
    [(0, 0), (1, 0), (1, 1), (2, 1)],
    [(0, 0), (0, 1), (1, 1), (2, 1)],
    [(0, 1), (1, 0), (1, 1), (1, 2)],
]


def _paint(g, top, left, cells, color):
    for r, c in cells:
        g[top + r][left + c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = rng.randint(11, 14); w = rng.randint(13, 16)
        n_frames = rng.randint(1, 2)
        frame_size = 5
    elif difficulty == "hard":
        h = rng.randint(20, 26); w = rng.randint(22, 28)
        n_frames = rng.randint(3, 5)
        frame_size = rng.choice([5, 6])
    else:
        h = rng.randint(14, 20); w = rng.randint(16, 22)
        n_frames = rng.randint(2, 4)
        frame_size = 5
    template = _TEMPLATES[ctx.draw_int("template", 0, len(_TEMPLATES) - 1)]
    template_h = max(r for r, _ in template) + 1
    template_w = max(c for _, c in template) + 1
    for _outer in range(80):
        g = full_grid(h, w, 0)
        # Place template top-left
        tr = rng.randint(1, max(1, min(3, h - template_h - frame_size - 2)))
        tc = rng.randint(1, max(1, min(3, w // 3)))
        _paint(g, tr, tc, template, 2)

        # Place n_frames frames.  Enumerating candidate boxes and searching a
        # non-touching subset is both faster and safer than the old random
        # dart-thrower, which sometimes returned partial boards.
        template_box = (tr, tc, tr + template_h - 1, tc + template_w - 1)

        def separated(a, b):
            ar1, ac1, ar2, ac2 = a
            br1, bc1, br2, bc2 = b
            return not (ar1 - 1 <= br2 and br1 <= ar2 + 1 and
                        ac1 - 1 <= bc2 and bc1 <= ac2 + 1)

        candidates = []
        for r0 in range(0, h - frame_size + 1):
            for c0 in range(0, w - frame_size + 1):
                box = (r0, c0, r0 + frame_size - 1, c0 + frame_size - 1)
                if separated(box, template_box):
                    candidates.append(box)
        rng.shuffle(candidates)

        chosen = []
        for box in candidates:
            if all(separated(box, prev) for prev in chosen):
                chosen.append(box)
                if len(chosen) == n_frames:
                    break
        if len(chosen) != n_frames:
            continue
        corners_left = ["tl", "tr", "br", "bl"]
        rng.shuffle(corners_left)
        for placed_frames, (r0, c0, r2, c2) in enumerate(chosen):
            draw_frame(g, r0, c0, r2, c2, 5)
            corner = corners_left[placed_frames % len(corners_left)]
            if corner == "tl":
                mr, mc = r0 + 1, c0 + 1
            elif corner == "tr":
                mr, mc = r0 + 1, c2 - 1
            elif corner == "br":
                mr, mc = r2 - 1, c2 - 1
            else:
                mr, mc = r2 - 1, c0 + 1
            g[mr][mc] = 8
        return g
    raise ValueError("could not place the requested frame count")


def _draw_from_degenerate(name, rng):
    g = full_grid(18, 18, 0)
    if name == "no_template":
        # Frames + markers but no color-2 template — rule has no shape
        # to rotate into the frames.
        draw_frame(g, 6, 1, 11, 6, 5)
        g[7][2] = 8
        return g
    if name == "no_frames":
        # Template present but no color-5 frames — rule has no
        # destination to place the rotated template into.
        _paint(g, 1, 1, _TEMPLATES[0], 2)
        return g
    if name == "no_marker":
        # Template + frame present but no corner color-8 marker — rule
        # has no rotation cue, can't determine orientation.
        _paint(g, 1, 1, _TEMPLATES[0], 2)
        draw_frame(g, 6, 1, 11, 6, 5)
        return g
    return g
