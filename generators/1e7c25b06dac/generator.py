"""Varied inputs for blank-preserving main-diagonal reflection.

The authoritative Racket rule is unchanged: copy a transposed source only into
an empty cell. Ordinary samples contain sources in both triangles, optional
diagonal anchors, and repeated colors. Identity-only diagnostic textures are
intentionally rejected by self_check and must not become supervised lessons.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "1e7c25b06dac"
VERSION = "2.1.0"
SUMMARY = (
    "Square 3..30 grids with varied nonzero positions and counts. Fill each "
    "blank cell from its transposed partner; keep every occupied cell. Ordinary "
    "samples use both triangles and may include diagonal anchors and repeated "
    "colors. Occupied reciprocal pairs are preserved by the reference but are "
    "not sampled."
)
INVARIANTS = [
    "square grid of exact integer colors 0..9, at most 30 on a side",
    "ordinary samples have blank partners for every off-diagonal source",
    "ordinary samples have sources in both triangles and change under the rule",
]
DEGENERATE_TEXTURES = ("no_marks", "full_diagonal", "full_grid")
HELPFUL_TEXTURES = ("scattered",)
AXES = {
    "grid_size": {"type": "int", "default": "rng 6..30", "valid": "3..30"},
    "grid_h": {"type": "int", "default": "grid_size", "valid": "3..30; square aliases must agree"},
    "grid_w": {"type": "int", "default": "grid_size", "valid": "3..30; square aliases must agree"},
    "palette_size": {"type": "int", "default": "3", "valid": "1..9 available nonzero colors"},
    "texture": {"type": "str", "default": "scattered", "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate ARC cells and require at least one informative missing mirror.

    Canonical examples may have different counts and diagonal anchors. The
    reference also preserves occupied reciprocal cells; this validator permits
    them if some other blank mirror makes the input informative. Such pairs are
    a validator/reference boundary, not claimed ordinary sampling coverage.
    """
    if type(grid) is not list or not grid:
        return ["expected a nonempty list of rows"]
    if any(type(row) is not list or not row for row in grid):
        return ["expected nonempty list rows"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if h != w:
        return [f"grid not square: {h}x{w}"]
    if h > 30:
        return [f"grid too large: {h}x{w}"]
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        return ["cells must be exact integers in 0..9 (not bool)"]
    if not any(grid[r][c] != 0 and grid[c][r] == 0
               for r in range(h) for c in range(w) if r != c):
        return ["identity-only input: no nonzero source with a blank transposed partner"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unsupported overrides: {', '.join(sorted(unknown))}")
    sizes = {key: value for key, value in overrides.items()
             if key in ("grid_size", "grid_h", "grid_w") and value is not None}
    for key, value in sizes.items():
        if type(value) is not int:
            raise TypeError(f"{key} must be an integer (not bool)")
        if not 3 <= value <= 30:
            raise ValueError(f"{key} must be in 3..30")
    if len(set(sizes.values())) > 1:
        raise ValueError("grid_size/grid_h/grid_w must agree for a square grid")
    normalized = dict(overrides)
    if sizes:
        normalized["grid_size"] = next(iter(sizes.values()))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=normalized)
    # Exact overrides span the full supported domain, independently of the
    # difficulty used for default sampling.
    lo, hi = (3, 30) if sizes else {
        "easy": (6, 10), "medium": (11, 19), "hard": (20, 30)
    }.get(difficulty, (6, 30))
    n = ctx.draw_int_strict("grid_size", lo, hi)
    palette_size = ctx.draw_int_strict("palette_size", 1, 9) if overrides.get("palette_size") is not None else 3
    texture = overrides.get("texture")
    if texture is None:
        texture = "scattered"
    if type(texture) is not str or texture not in HELPFUL_TEXTURES + DEGENERATE_TEXTURES:
        raise ValueError(f"unsupported texture: {texture!r}")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, n)
    rng = ctx.draw_rng("layout")
    colors = list(ctx.draw_distinct_colors("colors", n=palette_size, exclude=[0]))
    grid = full_grid(n, n, 0)
    orbits = [(r, c) for r in range(1, n) for c in range(r)]
    rng.shuffle(orbits)
    source_count = rng.randint(2, min(n, 12, len(orbits)))
    for index, (r, c) in enumerate(orbits[:source_count]):
        # Two different unordered pairs guarantee both copy directions. The
        # remaining positions vary independently; no fixed-coordinate shortcut.
        if index == 1 or (index >= 2 and rng.randrange(2)):
            r, c = c, r
        grid[r][c] = rng.choice(colors)
    for d in rng.sample(range(n), rng.randint(0, min(2, n))):
        grid[d][d] = rng.choice(colors)
    return grid


def _draw_from_degenerate(name, n):
    grid = full_grid(n, n, 0)
    if name == "full_diagonal":
        for i in range(n):
            grid[i][i] = 3
    elif name == "full_grid":
        grid = full_grid(n, n, 3)
    return grid
