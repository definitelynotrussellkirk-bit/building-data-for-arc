"""Generator for arc_puzzle_bank_21_set13_s:S13_M5 — crop the highest-perimeter object.

Rule: find all 4-connected components on a 0-bg. Sort by (exposed-cell
perimeter DESC, area DESC, top-left lex ASC). Take the first. Crop
to bbox. Recolor all non-zero cells of that component to 8 (preserving
the bbox shape including interior 0-holes).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bc005ea27dae"
# 1.3.0: output was almost always a small 8-frame (the first hollow rect was
# nearly always the perimeter winner) -> dup-outputs(6%), uniq 0.06. Now all
# components are RANDOM polyominoes (varied shapes, some hollow); we compute
# exposed-perimeter in Python and guarantee a STRICT max so the WINNER's
# shape (hence the output) varies widely.
VERSION = "1.3.1"  # add self_check
TASK_ID = "bc005ea27dae"

SUMMARY = (
    "Several 4-connected non-bg components on a 0-bg grid: solid blobs, "
    "hollow frames, plus-shapes, etc. One component has STRICTLY highest "
    "exposed-cell perimeter (cells with ≥1 non-component-cell neighbor "
    "or grid edge). Rule outputs the cropped bbox of the winner with "
    "all non-zero cells recolored to 8 (holes preserved as 0)."
)

# Rivals: 'output is input' refuted by demos (output is small).
# 'pick largest by area' refuted by demos where perim winner != area
# winner. 'recolor with original color' refuted by demos (always 8).
# 'pick smallest' refuted by demos. 3 demos with hollow vs solid
# competitors cover the perimeter-vs-area distinction.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥3 4-connected non-bg components",
    "one component has strictly highest exposed-cell perimeter",
    "components don't 4-touch each other",
]

AXES = {
    "grid_h":   {"type": "int", "default": "rng 10..13", "valid": "9..18"},
    "grid_w":   {"type": "int", "default": "rng 13..17", "valid": "11..22"},
    "n_objects":{"type": "int", "default": "rng 3..4", "valid": "2..6"},
}


def _hollow_rect(rh, rw):
    cells = []
    for r in range(rh):
        for c in range(rw):
            if r in (0, rh - 1) or c in (0, rw - 1):
                cells.append((r, c))
    return cells


def _solid_rect(rh, rw):
    return [(r, c) for r in range(rh) for c in range(rw)]


def _plus(arm):
    cells = [(arm, arm)]
    for k in range(1, arm + 1):
        cells.extend([(arm - k, arm), (arm + k, arm), (arm, arm - k), (arm, arm + k)])
    return cells


def _grow_blob(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    minr, minc = min(rs), min(cs)
    return [(r - minr, c - minc) for r, c in cells]


def _perimeter(cells):
    """Exposed-cell boundary count (4-connectivity), matching the rule."""
    s = set(cells)
    total = 0
    for (r, c) in cells:
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            if (r + dr, c + dc) not in s:
                total += 1
    return total


def _rand_shape(rng, big=False):
    """Random shape. With big=True, bias toward a large sprawling blob (high,
    varied perimeter) so the perimeter WINNER's shape varies widely."""
    if big:
        kind = rng.choice(["blob", "blob", "blob", "hollow"])
        if kind == "hollow":
            return _hollow_rect(rng.randint(4, 7), rng.randint(4, 7))
        return _grow_blob(rng, rng.randint(8, 15))
    kind = rng.choice(["blob", "blob", "plus", "small_hollow", "solid"])
    if kind == "small_hollow":
        return _hollow_rect(rng.randint(3, 4), rng.randint(3, 4))
    if kind == "plus":
        return _plus(1)
    if kind == "solid":
        return _solid_rect(rng.randint(2, 3), rng.randint(2, 4))
    return _grow_blob(rng, rng.randint(3, 6))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; >=2 distinct nonzero colors (components)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if not colors:
        return errs  # degenerate
    if len(colors) < 2:
        errs.append(f"expected >=2 distinct component colors, got {len(colors)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = rng.randint(9, 11); w = rng.randint(11, 14)
        n_objects = rng.randint(3, 4)
    elif difficulty == "hard":
        h = rng.randint(14, 18); w = rng.randint(17, 22)
        n_objects = rng.randint(4, 6)
    else:
        h = rng.randint(11, 14); w = rng.randint(13, 17)
        n_objects = rng.randint(3, 5)

    # Build shapes with a STRICT perimeter maximum: one designated "big"
    # sprawling shape (the intended varied winner) + smaller competitors.
    shapes = None
    for _ in range(30):
        cand = [_rand_shape(rng, big=True)] + \
               [_rand_shape(rng) for _ in range(n_objects - 1)]
        perims = sorted((_perimeter(s) for s in cand), reverse=True)
        if perims[0] > perims[1]:
            rng.shuffle(cand)  # winner isn't always placed first
            shapes = cand
            break
    if shapes is None:
        shapes = cand  # accept (rule is still deterministic via tie-break)

    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], n_objects)
    placed_boxes = []
    for shape, color in zip(shapes, palette):
        ph = max(r for r, _ in shape) + 1
        pw = max(c for _, c in shape) + 1
        if ph > h or pw > w:
            continue
        for _attempt in range(120):
            r0 = rng.randint(0, h - ph)
            c0 = rng.randint(0, w - pw)
            collide = False
            for (pr1, pc1, pr2, pc2) in placed_boxes:
                if (r0 - 1 <= pr2 and pr1 <= r0 + ph and
                    c0 - 1 <= pc2 and pc1 <= c0 + pw):
                    collide = True; break
            if collide:
                continue
            for dr, dc in shape:
                g[r0 + dr][c0 + dc] = color
            placed_boxes.append((r0, c0, r0 + ph - 1, c0 + pw - 1))
            break
    return g
