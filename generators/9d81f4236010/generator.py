"""Generator for 9d81f4236010 — overlay frame markers in largest frame coords.

Rule: bg = mode color. frame_color = most-frequent non-bg color. Find
all solid-frame_color rectangular objects (frames). For each frame's
bbox, the cells inside may contain other-color "markers". Output: a
fresh canvas sized to the LARGEST frame's bbox, filled with frame_color.
For each frame, overlay its markers at local (r-r0, c-c0) coordinates.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9d81f4236010"
VERSION = "2.1.0"
TASK_ID = "9d81f4236010"
SUMMARY = (
    "Grid where the MODE color is the background (often 2, sometimes 5 "
    "or 0). The most-frequent non-bg color is the FRAME color. The grid "
    "contains 2-4 solid frame-color rectangular blocks at non-touching "
    "positions. Each block has 1-3 marker cells inside in OTHER colors "
    "(replacing frame-color cells). The frames may have different sizes; "
    "the largest determines the output bbox. Rule: output is sized to "
    "the LARGEST frame's bbox; start filled with frame_color. For each "
    "frame, overlay each marker at local coords (r-r0, c-c0) within "
    "the output canvas. Markers from different frames may be at "
    "different local coords; they merge onto the shared canvas."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "the mode color is the background",
    "the most-frequent non-bg color forms 2-4 SOLID rectangular blocks (the frames)",
    "exactly one frame is the largest (its bbox sets output dims)",
    "each frame has 1-3 marker cells inside (in colors NOT bg, NOT frame)",
    "frames don't overlap; markers fit within frame bboxes",
]

# Free axes the runner may override. Keys match the keyed draw_int labels in
# generate(); defaults are the medium band, valid spans easy..hard. (frame_count
# is a constant 2 in the easy band, so it's only keyed in medium/hard.)
AXES = {
    "grid_h":      {"type": "int", "default": "rng 13..17", "valid": "11..22",
                    "doc": "Canvas height (easy 11..14, medium 13..17, hard 16..22)."},
    "grid_w":      {"type": "int", "default": "rng 15..19", "valid": "13..24",
                    "doc": "Canvas width (easy 13..16, medium 15..19, hard 18..24)."},
    "frame_count": {"type": "int", "default": "rng 2..3", "valid": "2..4",
                    "doc": "Number of solid frame blocks (easy 2, medium 2..3, hard 3..4)."},
}


def _free(g, r1, c1, r2, c2, bg, buffer=1):
    h, w = len(g), len(g[0])
    for r in range(max(0, r1 - buffer), min(h, r2 + buffer + 1)):
        for c in range(max(0, c1 - buffer), min(w, c2 + buffer + 1)):
            if g[r][c] != bg:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h_can = ctx.draw_int("grid_h", 11, 14)
        w_can = ctx.draw_int("grid_w", 13, 16)
        frame_count = ctx.draw_int("frame_count", 2, 2)
    elif difficulty == "hard":
        h_can = ctx.draw_int("grid_h", 16, 22)
        w_can = ctx.draw_int("grid_w", 18, 24)
        frame_count = ctx.draw_int("frame_count", 3, 4)
    else:
        h_can = ctx.draw_int("grid_h", 13, 17)
        w_can = ctx.draw_int("grid_w", 15, 19)
        frame_count = ctx.draw_int("frame_count", 2, 3)

    bg = rng.choice([0, 2, 5])
    frame_color = rng.choice([c for c in [1, 2, 3, 4, 6, 7, 8, 9] if c != bg])
    marker_pool = [c for c in [1, 2, 3, 4, 5, 6, 7, 8, 9] if c != bg and c != frame_color]
    rng.shuffle(marker_pool)

    for outer in range(400):
        g = full_grid(h_can, w_can, bg)
        placed = []
        # Make sure one frame is biggest
        sizes = [(rng.randint(4, 6), rng.randint(4, 7)) for _ in range(frame_count)]
        # Boost one to be biggest
        biggest_idx = rng.randint(0, frame_count - 1)
        sizes[biggest_idx] = (rng.randint(5, 7), rng.randint(5, 8))
        # Cap sizes to fit within grid - 2 (for buffer)
        sizes = [(min(rh, h_can - 2), min(rw, w_can - 2)) for rh, rw in sizes]
        # Make biggest strictly largest
        big_area = sizes[biggest_idx][0] * sizes[biggest_idx][1]
        for i in range(frame_count):
            if i != biggest_idx:
                while sizes[i][0] * sizes[i][1] >= big_area:
                    sizes[i] = (max(3, sizes[i][0] - 1), max(3, sizes[i][1] - 1))
                    if sizes[i] == (3, 3):
                        break
        all_placed = True
        for rh, rw in sizes:
            placed_ok = False
            for _ in range(200):
                r = rng.randint(1, h_can - rh - 1)
                c = rng.randint(1, w_can - rw - 1)
                if not _free(g, r, c, r + rh - 1, c + rw - 1, bg, buffer=1):
                    continue
                # Place solid block
                for rr in range(r, r + rh):
                    for cc in range(c, c + rw):
                        g[rr][cc] = frame_color
                # Place markers inside (1-3, replacing some frame cells)
                interior = [(rr, cc) for rr in range(r, r + rh)
                            for cc in range(c, c + rw)]
                rng.shuffle(interior)
                n_marks = rng.randint(1, 3)
                for j, (rr, cc) in enumerate(interior[:n_marks]):
                    g[rr][cc] = rng.choice(marker_pool)
                placed.append((r, c, rh, rw))
                placed_ok = True
                break
            if not placed_ok:
                all_placed = False
                break
        if not all_placed:
            continue
        # Verify mode is bg (count cells)
        flat = [v for row in g for v in row]
        from collections import Counter
        cnt = Counter(flat)
        if cnt.most_common(1)[0][0] != bg:
            continue
        return g
    # Deterministic no-raise fallback: keep the rule executable even if random
    # scattered placement exhausts its retries on a tight canvas.
    return _fallback_layout(h_can, w_can, frame_count, bg, frame_color, marker_pool)


def _paint_frame(g, r, c, rh, rw, frame_color, marker_pool, rng=None):
    for rr in range(r, r + rh):
        for cc in range(c, c + rw):
            g[rr][cc] = frame_color
    marks = [(r + 1, c + 1), (r + rh - 2, c + rw - 2), (r + 1, c + rw - 2)]
    for i, (mr, mc) in enumerate(marks[:max(1, min(3, rh * rw // 10 + 1))]):
        g[mr][mc] = marker_pool[i % len(marker_pool)]


def _fallback_layout(h, w, frame_count, bg, frame_color, marker_pool):
    g = full_grid(h, w, bg)
    specs = [(5, 6), (4, 4), (3, 5), (3, 3)][:frame_count]
    positions = [
        (1, 1),
        (1, max(1, w - specs[1][1] - 1)) if len(specs) > 1 else (1, 1),
        (max(1, h - specs[2][0] - 1), 1) if len(specs) > 2 else (1, 1),
        (max(1, h - specs[3][0] - 1), max(1, w - specs[3][1] - 1)) if len(specs) > 3 else (1, 1),
    ]
    for (rh, rw), (r, c) in zip(specs, positions):
        rh = min(rh, h - r - 1); rw = min(rw, w - c - 1)
        _paint_frame(g, r, c, rh, rw, frame_color, marker_pool)
    return g


def _non_bg_components(grid, bg):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == bg or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                x, y = stack.pop(); cells.append((x, y))
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < h and 0 <= ny < w and (nx, ny) not in seen and grid[nx][ny] != bg:
                        seen.add((nx, ny)); stack.append((nx, ny))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    from collections import Counter
    h, w = len(grid), len(grid[0])
    cnt = Counter(v for row in grid for v in row)
    bg = cnt.most_common(1)[0][0]
    non_bg_counts = {c: n for c, n in cnt.items() if c != bg}
    if not non_bg_counts:
        return ["expected frame/marker content"]
    frame_color = max(non_bg_counts.items(), key=lambda kv: kv[1])[0]
    errs = []
    comps = _non_bg_components(grid, bg)
    frame_like = []
    areas = []
    for cells in comps:
        colors = Counter(grid[r][c] for r, c in cells)
        if colors[frame_color] == 0:
            continue
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        area = (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)
        areas.append(area)
        if any(grid[r][c] not in (bg, frame_color) for r, c in cells):
            frame_like.append(cells)
    if not (2 <= len(frame_like) <= 4):
        errs.append(f"expected 2-4 frame components with marker evidence, found {len(frame_like)}")
    if areas and areas.count(max(areas)) != 1:
        errs.append("expected exactly one largest frame bbox")
    if cnt[bg] <= max(non_bg_counts.values()):
        errs.append("background must be the modal color")
    return errs
