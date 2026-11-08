"""Cardinal center fill: all four original orthogonal neighbors must match.

Ordinary inputs have at least one target and, when a slot remains, a near-miss
motif. Named degenerate textures are explicit identity-only input grammars.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "68176b5eb124"
VERSION = "1.2.0"
SUMMARY = "Fill zero centers with four equal nonzero cardinal neighbors."
PALETTE_KINDS = ("default", "single_plus", "spread_pluses", "rainbow")
HELPFUL_TEXTURES = PALETTE_KINDS
DEGENERATE_TEXTURES = ("no_pluses", "plus_arms_mismatched", "plus_already_filled")
ARMS = ((-1, 0), (1, 0), (0, -1), (0, 1))
INVARIANTS = ["ordinary inputs contain a complete four-arm target",
              "motifs occupy separate three-by-three tiles",
              "near-miss arms do not qualify as fill targets"]
AXES = {
    "grid_h": {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w": {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "n_pluses": {"type": "int", "default": "rng 1..3 subject to capacity", "valid": "1..6", "description": "exact count, subject to separated tile capacity"},
    "palette_kind": {"type": "str", "default": "default", "valid": "|".join(PALETTE_KINDS)},
    "palette_size": {"type": "int", "default": "8", "valid": "8"},
    "position_bias": {"type": "str", "default": "grid_aligned", "valid": ["grid_aligned"], "description": "fixed layout policy; singleton, not a variation axis"},
    "n_distinct_colors": {"type": "int", "default": "min(3,n_pluses)", "valid": "1..8", "description": "target-arm colors only; at most n_pluses"},
    "plus_density": {"type": "str", "default": "medium", "valid": "sparse|medium|dense"},
    "texture": {"type": "str", "default": "alias for palette_kind", "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _targets(grid):
    return [(r, c) for r in range(1, len(grid)-1) for c in range(1, len(grid[0])-1)
            if grid[r][c] == 0 and grid[r-1][c] != 0 and
            all(grid[r+dr][c+dc] == grid[r-1][c] for dr, dc in ARMS)]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Ordinary domain requires a real target, and permits lawful distractors.

    This is a teaching-domain check, not a claim that the rule is undefined on
    identity-only grids. Explicit named identity modes validate their grammar.
    """
    if (not isinstance(grid, (list, tuple)) or not grid
            or not isinstance(grid[0], (list, tuple)) or not grid[0]):
        return ["empty or invalid grid"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    if not (5 <= h <= 14 and 5 <= w <= 14):
        return ["grid dimensions must be in 5..14"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["grid colors must be integers in 0..9"]
    texture = (meta or {}).get("texture", "")
    targets = _targets(grid)
    if texture not in DEGENERATE_TEXTURES:
        return [] if targets else ["no complete plus center (four equal nonzero cardinal arms)"]
    if targets:
        return ["identity texture contains a fill target"]
    cells = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    if texture == "no_pluses":
        if len(cells) == 2:
            (r, c), (rr, cc) = cells
            if abs(r-rr) + abs(c-cc) >= 3:
                return []
    else:
        for r in range(1, h-1):
            for c in range(1, w-1):
                arms = {(r+dr, c+dc) for dr, dc in ARMS}
                colors = {grid[rr][cc] for rr, cc in arms}
                if texture == "plus_arms_mismatched" and cells == arms and len(colors) >= 2:
                    return []
                if (texture == "plus_already_filled" and cells == arms | {(r, c)}
                        and colors == {grid[r][c]}):
                    return []
    return ["grid does not match named identity texture grammar"]



def observe_overrides(grid):
    """Derive exact realized target counts; distractor colors are excluded."""
    targets = _targets(grid)
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_pluses": len(targets),
            "n_distinct_colors": len({grid[r-1][c] for r, c in targets})}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    # Difficulty affects defaults only; explicit documented dimensions win.
    low, high = (7, 8) if difficulty == "easy" else ((9, 10) if difficulty == "hard" else (7, 10))
    h = ctx.draw_int_strict("grid_h", 5, 14) if overrides.get("grid_h") is not None else ctx.draw_int_strict("grid_h", low, high)
    w = ctx.draw_int_strict("grid_w", 5, 14) if overrides.get("grid_w") is not None else ctx.draw_int_strict("grid_w", low, high)
    texture = ctx.draw_choice("texture", HELPFUL_TEXTURES + DEGENERATE_TEXTURES) if overrides.get("texture") is not None else ctx.draw_choice("texture", HELPFUL_TEXTURES)
    kind = ctx.draw_choice("palette_kind", PALETTE_KINDS) if overrides.get("palette_kind") is not None else ctx.draw_choice("palette_kind", (texture if texture in HELPFUL_TEXTURES else "default",))
    if overrides.get("texture") in HELPFUL_TEXTURES and overrides.get("palette_kind") not in (None, texture):
        raise ValueError("texture and palette_kind aliases conflict")
    ctx.draw_int_strict("palette_size", 8, 8)
    ctx.draw_choice("position_bias", ("grid_aligned",))
    density = ctx.draw_choice("plus_density", ("sparse", "medium", "dense")) if overrides.get("plus_density") is not None else ctx.draw_choice("plus_density", ("medium",))
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    positions = [(r, c) for r in range(1, h-1, 3) for c in range(1, w-1, 3)]
    rng.shuffle(positions)
    if texture in DEGENERATE_TEXTURES:
        if any(overrides.get(key) is not None for key in ("n_pluses", "n_distinct_colors", "plus_density", "palette_kind")):
            raise ValueError("target controls do not apply to identity textures")
        r, c = positions[0]
        if texture == "no_pluses":
            g[0][0] = rng.randint(1, 8)
            g[h-1][w-1] = rng.randint(1, 8)
        else:
            color = rng.randint(1, 8)
            for dr, dc in ARMS:
                g[r+dr][c+dc] = color
            if texture == "plus_arms_mismatched":
                g[r-1][c] = color % 8 + 1
            else:
                g[r][c] = color
        return g
    capacity = len(positions)
    # Reserve two contrast tiles when possible for unpinned counts.
    max_default = min(6, max(1, capacity-2))
    if overrides.get("n_pluses") is not None:
        n = ctx.draw_int_strict("n_pluses", 1, min(6, capacity))
    elif density == "sparse":
        n = ctx.draw_int_strict("n_pluses", 1, 1)
    elif density == "dense":
        n = ctx.draw_int_strict("n_pluses", max_default, max_default)
    else:
        n = ctx.draw_int_strict("n_pluses", 1, min(3, max_default))
    if overrides.get("n_distinct_colors") is not None:
        distinct = ctx.draw_int_strict("n_distinct_colors", 1, min(8, n))
    else:
        default_distinct = 1 if kind == "single_plus" else (min(8, n) if kind in ("spread_pluses", "rainbow") else min(3, n))
        distinct = ctx.draw_int_strict("n_distinct_colors", default_distinct, default_distinct)
    palette = rng.sample(range(1, 9), distinct)
    if kind == "rainbow":
        palette.sort()
    for i, (r, c) in enumerate(positions[:n]):
        color = palette[i % distinct]
        for dr, dc in ARMS:
            g[r+dr][c+dc] = color
    # The first two spare tiles explicitly contrast horizontal and vertical
    # pair rivals. Larger layouts also include a three-arm or color mismatch.
    negatives = ["horizontal", "vertical", ctx.draw_rng("negative_kind").choice(("three", "mixed", "filled"))]
    if capacity - n == 1:
        negatives = [ctx.draw_rng("negative_orientation").choice(("horizontal", "vertical"))]
    for (r, c), negative in zip(positions[n:n+3], negatives):
        color = rng.choice(palette)
        arms = ((0, -1), (0, 1)) if negative == "horizontal" else (((-1, 0), (1, 0)) if negative == "vertical" else ARMS)
        if negative == "three":
            omitted = rng.randrange(4)
            arms = tuple(arm for j, arm in enumerate(ARMS) if j != omitted)
        for dr, dc in arms:
            g[r+dr][c+dc] = color
        if negative == "mixed":
            g[r-1][c] = color % 8 + 1
        elif negative == "filled":
            g[r][c] = color % 8 + 1
    return g
