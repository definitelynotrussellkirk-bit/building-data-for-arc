"""Generator for v0_original:medium_01 (task 005c7091fce2).

THE RULE (what a solver must learn to see):
  Among all 4-connected single-color objects (any colors), keep the
  LARGEST, recolored to 8 (cyan); erase everything else. Exact size
  ties are broken by bbox order — but helpful inputs keep the maximum
  unique.

WHAT MAKES AN INPUT TEACH THIS RULE (helpful textures):
  - NEAR-TIES (size_gap=narrow): the largest wins by a single cell, so
    "obviously the big one" fails — the model must actually count
  - grown-blob shapes (not a fixed library): size and shape decorrelate
  - color_policy=shared: several objects share a color (the rule is
    size, not color); color_policy=herring: a SMALL object is colored
    8 — keeping "the cyan one" is exactly wrong
  - 1-cell specks and mid-size decoys populate the size spectrum

WHAT HIDES IT (degenerate textures, reachable via texture=...):
  - tied_sizes     two objects share the max — the tie-break decides
  - single_object  trivially largest, no contrast
  - no_objects     blank grid (rule returns an empty canvas)
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob
from puzzle_generators.helpers.palette import random_palette

GENERATOR_ID = "005c7091fce2"
VERSION = "2.0.1"
TASK_ID = "005c7091fce2"
SUMMARY = (
    "0-bg grid with 2-5 grown-blob objects of strictly distinct sizes; "
    "the largest (sometimes only by ONE cell) is kept and recolored 8, "
    "the rest are erased. Colors vary freely, may repeat across "
    "objects, and a small object may itself be cyan as a red herring."
)

INVARIANTS = [
    "background is 0; objects are 4-connected, halo-separated",
    "the maximum object size is UNIQUE (helpful path)",
    ">=2 objects, so something is always erased",
    "size_gap=narrow boards: the largest wins by exactly 1 cell",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_sizes", "single_object", "no_objects")
HELPFUL_TEXTURES = PALETTE_KINDS

_WARM = (2, 4, 6, 7, 9)
_COOL = (1, 3, 5, 8)
_ALL = (1, 2, 3, 4, 5, 6, 7, 8, 9)

AXES = {
    "grid_h":       {"type": "int", "default": "rng 6..9 (easy 6..7, hard 9..12)",
                     "valid": "5..12", "doc": "Grid height."},
    "grid_w":       {"type": "int", "default": "rng 7..10 (easy 7..8, hard 10..14)",
                     "valid": "6..14", "doc": "Grid width."},
    "n_smalls":     {"type": "int", "default": "rng 1..3 (hard 2..4)",
                     "valid": "1..4", "doc": "Objects besides the largest."},
    "big_size":     {"type": "int", "default": "rng 5..9 (hard up to 12)",
                     "valid": "4..12", "doc": "Cell count of the largest object."},
    "size_gap":     {"type": "enum", "default": "rng (narrow ~1 in 2)",
                     "valid": "narrow|wide",
                     "doc": "narrow: the runner-up has big_size-1 cells — counting required."},
    "color_policy": {"type": "enum", "default": "rng",
                     "valid": "distinct|shared|herring",
                     "doc": "shared: colors repeat across objects; herring: a SMALL "
                            "object is colored 8 (the output color) — keeping 'the "
                            "cyan one' is wrong."},
    "palette_kind": {"type": "enum", "default": "rng helpful",
                     "valid": "default|warm|cool|varied", "doc": "Color pool."},
    "texture":      {"type": "enum", "default": "helpful",
                     "valid": "default|warm|cool|varied|tied_sizes|single_object|no_objects",
                     "doc": "Set to a degenerate name to build a rule-hiding input."},
}


def _pool(kind):
    if kind == "warm":
        return list(_WARM)
    if kind == "cool":
        return list(_COOL)
    return list(_ALL)


def _dims(ctx, difficulty):
    if difficulty == "easy":
        return ctx.draw_int("grid_h", 6, 7), ctx.draw_int("grid_w", 7, 8)
    if difficulty == "hard":
        return ctx.draw_int("grid_h", 9, 12), ctx.draw_int("grid_w", 10, 14)
    return ctx.draw_int("grid_h", 6, 9), ctx.draw_int("grid_w", 7, 10)


def _place_blob(g, rng, size, color):
    """Grow a blob of exactly `size` cells in free space (1-cell halo).
    Returns the cell count placed, or 0."""
    h, w = len(g), len(g[0])
    occupied = {(r, c) for r in range(h) for c in range(w) if g[r][c] != 0}
    halo = set(occupied)
    for r, c in occupied:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if 0 <= r + dr < h and 0 <= c + dc < w:
                    halo.add((r + dr, c + dc))
    for _attempt in range(25):
        blob = grow_blob(rng, h, w, halo, size)
        if blob is None or len(blob) != size:
            continue
        for r, c in blob:
            g[r][c] = color
        return size
    return 0


def _degenerate(ctx, name, difficulty):
    h, w = _dims(ctx, difficulty)
    rng = ctx.draw_rng("degenerate_layout")
    g = full_grid(h, w, 0)
    if name == "no_objects":
        return g
    pool = _pool(ctx.draw_choice("palette_kind", PALETTE_KINDS))
    if name == "single_object":
        _place_blob(g, rng, rng.randint(4, 8), rng.choice(pool))
        return g
    # tied_sizes: two blobs with the SAME cell count — tie-break decides
    size = rng.randint(3, 6)
    _place_blob(g, rng, size, rng.choice(pool))
    _place_blob(g, rng, size, rng.choice(pool))
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _degenerate(ctx, texture, difficulty)

    h, w = _dims(ctx, difficulty)
    n_smalls = ctx.draw_int("n_smalls", 2 if difficulty == "hard" else 1,
                            4 if difficulty == "hard" else 3)
    big_size = ctx.draw_int("big_size", 5, 12 if difficulty == "hard" else 9)
    big_size = max(4, min(big_size, (h * w) // 3))  # leave room for the rest
    gap = ctx.draw_choice("size_gap", ("narrow", "wide"))
    policy = ctx.draw_choice("color_policy", ("distinct", "shared", "herring"))
    pool = _pool(ctx.draw_choice("palette_kind", PALETTE_KINDS))
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    placed_big = _place_blob(g, rng, big_size, rng.choice(pool))
    if placed_big == 0:
        big_size = 5
        placed_big = _place_blob(g, rng, big_size, rng.choice(pool))

    # smaller objects: strictly below the max; narrow gap puts the
    # runner-up at big_size-1 so the contest is decided by one cell
    if policy == "distinct":
        small_colors = list(random_palette(rng, min(n_smalls, 8)))
    elif policy == "shared":
        base = rng.choice(pool)
        small_colors = [base] * n_smalls
    else:  # herring: one small is cyan — the OUTPUT color itself
        small_colors = [8] + [rng.choice(pool) for _ in range(max(0, n_smalls - 1))]
    rng.shuffle(small_colors)

    runner_up = big_size - 1 if gap == "narrow" else max(1, big_size - rng.randint(3, 4))
    sizes = [max(1, runner_up)]
    for _ in range(n_smalls - 1):
        sizes.append(rng.randint(1, max(1, runner_up - 1)))
    placed_any_small = False
    for size, color in zip(sizes, small_colors):
        if _place_blob(g, rng, min(size, big_size - 1), color):
            placed_any_small = True

    # invariant: something must be erased — guarantee a second object
    if not placed_any_small:
        _place_blob(g, rng, 1, rng.choice(pool))
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: >=2 4-connected objects; max object size is unique."""
    msgs = []
    h, w = len(grid), len(grid[0])
    seen = set()
    sizes = []
    for r0 in range(h):
        for c0 in range(w):
            if (r0, c0) in seen or grid[r0][c0] == 0:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            sz = 0
            while stack:
                r, c = stack.pop()
                sz += 1
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] != 0:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            sizes.append(sz)
    if len(sizes) < 2:
        msgs.append(f"expected >=2 objects, got {len(sizes)}")
        return msgs
    max_size = max(sizes)
    if sizes.count(max_size) > 1:
        msgs.append(f"max object size {max_size} is not unique ({sizes.count(max_size)} objects tied)")
    return msgs
