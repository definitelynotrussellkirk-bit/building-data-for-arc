"""Generator for arc_additional_puzzle_bank_volume3:M15 — Replace each object with its filled bbox.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_rectangular, single_blob, bboxes_overlap.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7ae4da96dc92"
VERSION = "1.2.0"
TASK_ID = "7ae4da96dc92"
SUMMARY = "Several non-touching colored blobs (some non-rectangular); output fills each obj's bbox."

INVARIANTS = [
    "between 2 and 4 non-touching blobs",
    "at least one blob is non-rectangular (so output != input)",
    "blobs are bbox-isolated: their bounding rectangles do NOT overlap",
    "blobs use distinct non-bg colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_rectangular", "single_blob", "bboxes_overlap")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "7..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "bbox_isolated",
                       "valid": "bbox_isolated"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _has_neighbor(p, used, ignore=frozenset()):
    r, c = p
    for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
        if (r+dr, c+dc) in ignore: continue
        if (r+dr, c+dc) in used: return True
    return False


def _grow_blob(rng, h, w, used, target_size):
    for _ in range(50):
        seed = (rng.randint(0, h-1), rng.randint(0, w-1))
        if seed in used or _has_neighbor(seed, used): continue
        cells = {seed}
        frontier = [seed]
        while frontier and len(cells) < target_size:
            r, c = frontier.pop(rng.randint(0, len(frontier)-1))
            for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                nr, nc = r+dr, c+dc
                if not (0 <= nr < h and 0 <= nc < w): continue
                cand = (nr, nc)
                if cand in cells or cand in used: continue
                if _has_neighbor(cand, used, ignore=cells): continue
                cells.add(cand)
                frontier.append(cand)
                if len(cells) == target_size: break
        if len(cells) == target_size:
            return cells
    return None


def _bbox(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    return (min(rs), min(cs), max(rs), max(cs))


def _is_rectangular(cells):
    r1, c1, r2, c2 = _bbox(cells)
    return len(cells) == (r2 - r1 + 1) * (c2 - c1 + 1)


def _bbox_overlaps(bb1, bb2):
    r1a, c1a, r2a, c2a = bb1; r1b, c1b, r2b, c2b = bb2
    return not (r2a < r1b or r2b < r1a or c2a < c1b or c2b < c1a)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg 0, 2-5 distinct non-zero colors (blobs), each in isolated connected component."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    # Find connected components
    visited = [[False] * w for _ in range(h)]
    def bfs(sr, sc):
        col = grid[sr][sc]; q = [(sr, sc)]; visited[sr][sc] = True; cells = []
        while q:
            r, c = q.pop(); cells.append((r, c))
            for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
                nr, nc = r+dr, c+dc
                if 0<=nr<h and 0<=nc<w and not visited[nr][nc] and grid[nr][nc]==col:
                    visited[nr][nc]=True; q.append((nr, nc))
        return cells
    objects = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 and not visited[r][c]:
                objects.append(bfs(r, c))
    n_blobs = len(objects)
    if not (2 <= n_blobs <= 5):
        errs.append(f"found {n_blobs} blob(s); expected 2-5")
    bboxes = []
    nonrect = False
    seen_colors = set()
    for cells in objects:
        colors = {grid[r][c] for r, c in cells}
        if len(colors) != 1:
            errs.append(f"object has multiple colors {sorted(colors)}")
        else:
            color = next(iter(colors))
            if color in seen_colors:
                errs.append(f"color {color} is used by more than one object")
            seen_colors.add(color)
        bb = _bbox(cells)
        if any(_bbox_overlaps(bb, prior) for prior in bboxes):
            errs.append("object bounding boxes overlap")
        bboxes.append(bb)
        if not _is_rectangular(cells):
            nonrect = True
    if objects and not nonrect:
        errs.append("all blobs are rectangular, so bbox-fill would be identity")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        n_blobs = ctx.draw_int("n_blobs", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 11, 12)
        n_blobs = ctx.draw_int("n_blobs", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 8, 12)
        n_blobs = ctx.draw_int("n_blobs", 2, 4)

    rng = ctx.draw_rng("layout")
    colors = list(range(1, 10))
    rng.shuffle(colors)

    # Fail closed: the task only teaches bbox-fill when every requested object is
    # present, bbox-isolated, and at least one blob is non-rectangular.  The old
    # body accepted partial layouts and, on a few seeds, all blobs happened to be
    # rectangular, yielding output == input identity demos.
    for _ in range(80):
        g = full_grid(h, w, 0)
        used: set[tuple[int,int]] = set()
        bboxes: list[tuple[int,int,int,int]] = []
        blobs: list[set[tuple[int, int]]] = []
        sizes = [rng.randint(3, 5) for _ in range(n_blobs)]
        for size in sizes:
            placed = False
            for _attempt in range(30):
                blob = _grow_blob(rng, h, w, used, size)
                if blob is None:
                    break
                bb = _bbox(blob)
                if any(_bbox_overlaps(bb, ob) for ob in bboxes):
                    continue
                used |= blob
                bboxes.append(bb)
                blobs.append(blob)
                placed = True
                break
            if not placed:
                break
        if len(blobs) != n_blobs or all(_is_rectangular(blob) for blob in blobs):
            continue
        for i, blob in enumerate(blobs):
            color = colors[i % len(colors)]
            for r, c in blob:
                g[r][c] = color
        return g
    raise RuntimeError("failed to place bbox-isolated blobs with at least one non-rectangle")


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "all_rectangular":
        # all blobs are solid rects → bbox fill equals input, rule is identity
        for r in range(2, 5):
            for c in range(2, 5):
                g[r][c] = 4
        for r in range(6, 8):
            for c in range(6, 9):
                g[r][c] = 6
        return g
    if name == "single_blob":
        # one blob → no comparison among objects, rule still works trivially
        for r, c in [(3, 3), (3, 4), (4, 3), (5, 4), (6, 4)]:
            g[r][c] = 5
        return g
    if name == "bboxes_overlap":
        # blobs whose bboxes overlap → filled bboxes paint over each other, ambiguous result
        for r, c in [(2, 2), (2, 3), (3, 4)]:
            g[r][c] = 4
        for r, c in [(3, 5), (4, 4), (5, 3)]:
            g[r][c] = 6
        return g
    return g
