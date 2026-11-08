"""Generator for arc_puzzle_bank_21_set7_s:S7_H7 — sort shapes into labeled frames.

Rule: color-8 objects are rectangular FRAMES. Each frame whose bbox interior
holds EXACTLY ONE non-{0,8} cell defines a BAY labeled by that cell's color.
The free-standing colored SHAPES elsewhere on the grid are then moved: each
shape is stamped (normalized, top-left anchored) into the interior of the frame
whose label color equals the shape's color, on a blank output that keeps only
the frames.

The old docstring ("multi-motif gallery pack ... vertical pack") was WRONG: it
scattered random motifs with no frames and no labels, so the rule degenerated
(it silently dropped cells). This rewrite CONSTRUCTS the real structure: N
color-8 hollow rectangles, each with one interior label pixel of a distinct
color, plus one matching-color free-standing shape (sized to fit the frame
interior) per frame, placed outside every frame.

Combinatorial axes: frame count, frame sizes (incl. non-square), label colors,
the per-frame shape shapes/sizes/positions, grid size.
Degenerates: no_frames, single_pair, frame_no_label.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import color_rect_frames, components_cells as components

GENERATOR_ID = "4be9bade27fe"
VERSION = "3.1.0"  # fail closed unless all frames and matching free-standing shapes are placed  # WRONG-TASK ('gallery pack' docstring): rule sorts free-standing shapes INTO color-8 frames matched by an interior label pixel's colour. Old gen scattered random motifs (no frames/labels) -> rule degenerated/dropped cells. Now N hollow-8 frames each with a distinct interior label + one matching-colour shape sized to fit, placed outside every frame.
TASK_ID = "4be9bade27fe"

SUMMARY = (
    "0-bg grid (size varies) with N color-8 hollow rectangular FRAMES "
    "(2..4). Each frame's bbox interior holds exactly ONE label pixel in a "
    "distinct non-{0,8} color. Elsewhere on the grid sit N free-standing "
    "SHAPES (random connected polyominoes), one per frame color, each sized "
    "to fit its frame's interior and isolated by a 1-cell gap. Rule: each "
    "shape is moved into the interior top-left of the frame whose label "
    "matches its color; output keeps the frames and the relocated shapes."
)

INVARIANTS = [
    "background is 0",
    "each frame is a color-8 hollow rectangle (interior >= 2x2)",
    "each frame interior holds exactly one non-{0,8} label pixel",
    "each label color has exactly one matching free-standing shape that "
    "fits the frame interior, placed outside every frame bbox",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "single_pair", "frame_no_label")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "10..20"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..24"},
    "n_frames":       {"type": "int", "default": "rng 2..4", "valid": "2..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "= n_frames", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "frames_and_shapes",
                       "valid": "frames_and_shapes"},
    "n_distinct_colors": {"type": "int", "default": "= n_frames", "valid": "2..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _hollow_rect(fh, fw):
    cells = []
    for c in range(fw):
        cells.append((0, c)); cells.append((fh - 1, c))
    for r in range(1, fh - 1):
        cells.append((r, 0)); cells.append((r, fw - 1))
    return cells


def _rand_poly(rng, maxh, maxw, k):
    """Connected polyomino normalized to (0,0), bbox <= maxh x maxw."""
    cells = [(0, 0)]; seen = {(0, 0)}
    tries = 0
    while len(cells) < k and tries < 300:
        tries += 1
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) in seen:
            continue
        rs = [x for x, _ in cells] + [nr]; cs = [y for _, y in cells] + [nc]
        if max(rs) - min(rs) + 1 <= maxh and max(cs) - min(cs) + 1 <= maxw:
            cells.append((nr, nc)); seen.add((nr, nc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        n = ctx.draw_int("n_frames", 2, 2)
        h = ctx.draw_int("grid_h", 10, 12); w = ctx.draw_int("grid_w", 12, 15)
    elif difficulty == "hard":
        n = ctx.draw_int("n_frames", 3, 4)
        h = ctx.draw_int("grid_h", 15, 20); w = ctx.draw_int("grid_w", 18, 24)
    else:
        n = ctx.draw_int("n_frames", 2, 3)
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 14, 19)
    rng = ctx.draw_rng("layout")

    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], n)
    for _layout in range(60):
        g = full_grid(h, w, 0)
        reserved: set[tuple[int, int]] = set()   # frame bboxes (incl. interior)
        frames = []  # (top, left, fh, fw, color)

        for color in colors:
            for _ in range(250):
                fh = rng.randint(4, 6); fw = rng.randint(4, 7)
                if fh > h or fw > w:
                    continue
                top = rng.randint(0, h - fh); left = rng.randint(0, w - fw)
                bb = {(top + r, left + c) for r in range(fh) for c in range(fw)}
                halo = {(r + dr, c + dc) for (r, c) in bb
                        for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
                if any(p in reserved for p in halo):
                    continue
                if any(g[r][c] != 0 for (r, c) in bb if 0 <= r < h and 0 <= c < w):
                    continue
                for (r, c) in _hollow_rect(fh, fw):
                    g[top + r][left + c] = 8
                ir = rng.randint(top + 1, top + fh - 2)
                ic = rng.randint(left + 1, left + fw - 2)
                g[ir][ic] = color                       # the single interior label
                reserved |= bb
                frames.append((top, left, fh, fw, color))
                break
        if len(frames) != n:
            continue

        ok = True
        # one matching-color free-standing shape per frame, sized to fit interior
        for (top, left, fh, fw, color) in frames:
            maxh, maxw = fh - 2, fw - 2
            k = rng.randint(2, max(2, min(5, maxh * maxw)))
            poly = _rand_poly(rng, maxh, maxw, k)
            sh = max(r for r, _ in poly) + 1; sw = max(c for _, c in poly) + 1
            placed = False
            for _ in range(300):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                cells = {(r0 + r, c0 + c) for r, c in poly}
                halo = {(r + dr, c + dc) for (r, c) in cells
                        for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
                if any(p in reserved for p in halo):
                    continue
                if any(g[r][c] != 0 for (r, c) in halo if 0 <= r < h and 0 <= c < w):
                    continue
                for (r, c) in cells:
                    g[r][c] = color
                reserved |= cells
                placed = True
                break
            if not placed:
                ok = False
                break
        if ok:
            return g
    raise ValueError("could not place all labeled frames and matching shapes")


def _draw_from_degenerate(name, rng):
    h, w = 11, 14
    g = full_grid(h, w, 0)
    if name == "no_frames":
        # no color-8 frames and no shapes -> rule yields a blank grid
        return g
    if name == "single_pair":
        # one frame + label + one matching shape (minimal valid instance)
        for (r, c) in _hollow_rect(5, 5):
            g[1 + r][1 + c] = 8
        g[2][2] = 4                       # interior label
        for (r, c) in [(8, 8), (8, 9), (9, 8)]:
            g[r][c] = 4                   # matching free-standing shape
        return g
    if name == "frame_no_label":
        # a frame with an EMPTY interior (no bay) and no shapes -> safe no-op
        for (r, c) in _hollow_rect(5, 6):
            g[2 + r][3 + c] = 8
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    min_expected = 3 if difficulty == "hard" else 2
    frames = color_rect_frames(grid, 8, min_outer_h=4, min_outer_w=4)
    msgs = []
    if len(frames) < min_expected:
        msgs.append(f"too few labeled frames: expected at least {min_expected}, found {len(frames)}")
    labels = []
    for r1, c1, r2, c2 in frames:
        interior = [(r, c, grid[r][c]) for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)
                    if grid[r][c] not in (0, 8)]
        if len(interior) != 1:
            msgs.append("frame interior does not contain exactly one label")
        else:
            labels.append(interior[0][2])
    if len(labels) != len(set(labels)):
        msgs.append("frame label colors are not distinct")
    for color in labels:
        comps = components([[v if v == color else 0 for v in row] for row in grid])
        if len(comps) < 2:  # one singleton label plus one free-standing shape
            msgs.append(f"missing free-standing shape for label color {color}")
            break
    return msgs
