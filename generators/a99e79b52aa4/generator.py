"""Generator for arc_puzzle_bank_21_set4_d:hard_d07.

Each rectangular frame contains a small interior pattern. The rule extracts the
interiors, crops them to content, sorts by frame color, and builds a gallery.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_frames,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_frames, empty_interiors, equal_frame_colors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "a99e79b52aa4"
VERSION = "3.0.2"  # shape-locked-in + few out shapes: FIXED frame boxes + FIXED interior patterns on fixed 15x16. Rule packs each frame's interior crop into a gallery; now varied frame size/position + random interior patterns + varied grid."
TASK_ID = "a99e79b52aa4"
SUMMARY = (
    "15×16 grid (0-bg) with 2-3 hollow rectangular FRAMES (border-"
    "only rectangles) in distinct non-zero colors. Each frame's "
    "interior contains 2-4 non-zero pattern cells in a color "
    "DIFFERENT from its frame color (and different from any other "
    "frame's color). Frames don't overlap. Rule: detect all "
    "rectangular hollow frames. Sort them by frame color ascending. "
    "For each frame, extract its interior (cells strictly inside "
    "the border): keep cells whose color is not 0 and not the "
    "frame color. Crop the interior to its bounding box. Build a "
    "gallery: stack all cropped interiors LEFT-TO-RIGHT, TOP-"
    "ALIGNED, with a 1-cell gap between them. Output height = max "
    "of crop heights; width = sum of crop widths + (n-1) gaps."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "variable-size grid with 2-3 rectangular hollow frames",
    "frame colors are distinct and non-zero",
    "each frame has 2-4 non-zero interior cells",
    "interior pattern color ≠ this frame's color AND ≠ any other frame's color",
    "frames don't overlap",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "empty_interiors", "equal_frame_colors")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng by difficulty", "valid": "11..22"},
    "grid_w":         {"type": "int", "default": "rng by difficulty", "valid": "12..26"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_frames":       {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "palette_size":   {"type": "int", "default": "rng 5..7", "valid": "5..7"},
    "position_bias":  {"type": "str", "default": "three_frames_with_interiors",
                       "valid": "three_frames_with_interiors"},
    "n_distinct_colors": {"type": "int", "default": "rng 5..7", "valid": "5..7"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_FRAME_BOXES = [
    (1, 1, 6, 6),
    (1, 9, 6, 14),
    (8, 4, 13, 9),
]

_PATTERNS = [
    [(1, 1, 8), (1, 2, 8), (2, 1, 5)],
    [(1, 1, 6), (2, 1, 6), (2, 2, 7), (3, 2, 7)],
    [(1, 2, 3), (2, 1, 3), (2, 2, 9), (2, 3, 9)],
]


def _find_hollow_frames(grid):
    h, w = len(grid), len(grid[0])
    frames = []
    for color in sorted({v for row in grid for v in row if v != 0}):
        cells = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
        if len(cells) < 8:
            continue
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        if r1 - r0 < 3 or c1 - c0 < 3:
            continue
        border = {(r0, c) for c in range(c0, c1 + 1)} | {(r1, c) for c in range(c0, c1 + 1)} | {(r, c0) for r in range(r0, r1 + 1)} | {(r, c1) for r in range(r0, r1 + 1)}
        if cells == border:
            frames.append((color, r0, c0, r1, c1))
    return frames


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify 2-3 hollow frames with non-frame interior content."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        return [f"grid too large: {h}x{w}"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    frames = _find_hollow_frames(grid)
    expected = 3 if difficulty == "hard" else 2 if difficulty == "easy" else None
    if expected is not None and len(frames) != expected:
        errs.append(f"expected {expected} hollow frames, got {len(frames)}")
    elif expected is None and not (2 <= len(frames) <= 3):
        errs.append(f"expected 2-3 hollow frames, got {len(frames)}")
    frame_colors = [f[0] for f in frames]
    if len(frame_colors) != len(set(frame_colors)):
        errs.append("frame colors are not distinct")
    occupied_boxes = []
    for color, r0, c0, r1, c1 in frames:
        for p0, p1, p2, p3 in occupied_boxes:
            if r0 <= p2 and p0 <= r1 and c0 <= p3 and p1 <= c1:
                errs.append("frame bounding boxes overlap")
        occupied_boxes.append((r0, c0, r1, c1))
        interior = [(r, c, grid[r][c]) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1) if grid[r][c] != 0]
        if not (2 <= len(interior) <= 4):
            errs.append(f"frame color {color} has {len(interior)} interior cells; expected 2..4")
        for _, _, v in interior:
            if v in (0, color) or v in frame_colors:
                errs.append(f"frame color {color} has unsafe interior color {v}")
                break
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        n_frames = ctx.draw_int("n_frames", 2, 2)
    elif difficulty == "hard":
        n_frames = ctx.draw_int("n_frames", 3, 3)
    else:
        n_frames = ctx.draw_int("n_frames", 2, 3)
    # Rule: extract each frame's interior pattern, pack the crops side-by-side.
    # v1.x used FIXED frame boxes + FIXED interior patterns (only color varied) on
    # a fixed 15x16 grid -> shape-locked-in + few output shapes. Now place frames
    # of varied size/position with RANDOM interior patterns so the packed gallery
    # output varies in shape and content.
    available = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    frame_colors = rng.sample(available, n_frames)
    interior_pool = [c for c in available if c not in frame_colors]
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 14); w = ctx.draw_int("grid_w", 12, 16); fmin, fmax = 4, 6
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 16, 22); w = ctx.draw_int("grid_w", 18, 26); fmin, fmax = 4, 7
    else:
        h = ctx.draw_int("grid_h", 12, 18); w = ctx.draw_int("grid_w", 14, 22); fmin, fmax = 4, 7
    g = full_grid(h, w, 0)
    placed = []
    made = 0
    for i in range(n_frames * 250):
        if made >= n_frames:
            break
        fh = rng.randint(fmin, fmax); fw = rng.randint(fmin, fmax)
        if fh > h or fw > w:
            continue
        r0 = rng.randint(0, h - fh); c0 = rng.randint(0, w - fw)
        r1, c1 = r0 + fh - 1, c0 + fw - 1
        if any(r0 <= p2 + 1 and p0 <= r1 + 1 and c0 <= p3 + 1 and p1 <= c1 + 1
               for p0, p1, p2, p3 in placed):
            continue
        draw_frame(g, r0, c0, r1, c1, frame_colors[made])
        # random interior pattern (2-4 cells), colors from the safe pool
        cells = [(r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)]
        k = rng.randint(2, min(4, len(cells)))
        for (r, c) in rng.sample(cells, k):
            g[r][c] = rng.choice(interior_pool)
        placed.append((r0, c0, r1, c1))
        made += 1
    if made != n_frames:
        g = full_grid(h, w, 0)
        if n_frames == 2:
            split = max(4, min(w - 5, (w - 1) // 2))
            zones = [(0, 0, h, split), (0, split + 1, h, w)]
        else:
            top_h = max(4, min(h - 5, h // 2))
            split = max(4, min(w - 5, (w - 1) // 2))
            zones = [(0, 0, top_h, split), (0, split + 1, top_h, w), (top_h + 1, 0, h, w)]
        for idx, (zr0, zc0, zr1, zc1) in enumerate(zones[:n_frames]):
            fh = min(max(4, fmin), max(4, zr1 - zr0))
            fw = min(max(4, fmin), max(4, zc1 - zc0))
            r0 = zr0 + max(0, (zr1 - zr0 - fh) // 2)
            c0 = zc0 + max(0, (zc1 - zc0 - fw) // 2)
            r1, c1 = r0 + fh - 1, c0 + fw - 1
            draw_frame(g, r0, c0, r1, c1, frame_colors[idx])
            cells = [(r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)]
            for r, c in rng.sample(cells, min(2 + idx % 3, len(cells))):
                g[r][c] = rng.choice(interior_pool)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(15, 16, 0)
    if name == "no_frames":
        # patterns scattered without frames → no boundaries to extract by
        for r, c, v in [(2, 2, 8), (5, 5, 6), (10, 7, 3)]:
            g[r][c] = v
        return g
    if name == "empty_interiors":
        # frames present but no interior patterns → nothing to extract
        for box, color in zip(_FRAME_BOXES[:2], [1, 2]):
            r1, c1, r2, c2 = box
            draw_frame(g, r1, c1, r2, c2, color)
        return g
    if name == "equal_frame_colors":
        # 2 frames share color → "distinct frame colors" precondition fails
        for box in _FRAME_BOXES[:2]:
            r1, c1, r2, c2 = box
            draw_frame(g, r1, c1, r2, c2, 1)
        for r, c, v in [(2, 2, 8), (3, 11, 6)]:
            g[r][c] = v
        return g
    return g
