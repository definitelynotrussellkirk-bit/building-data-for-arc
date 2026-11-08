"""Generator for arc_puzzle_bank_next_21_bundle:easy_09_fill_plus_centers.

Rule: each hollow color-3 cardinal plus has its zero center filled with color 4.

The ordinary sampler keeps its historical difficulty bands. Explicit overrides
are validated against the full declared domain instead of the current sampling
band, so authoring controls do not change meaning with ``difficulty``.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8b595f6acd93"
VERSION = "1.3.2"
TASK_ID = "8b595f6acd93"
RULE_HASH = "bd39a99359bd"  # reverified canonical rule authority
SUMMARY = "Hollow 3-color plus signs with zero centers for the rule to fill."

INVARIANTS = [
    "background is 0",
    "each planted target is a radius-1 plus with four arms of color 3 and center 0",
    "planted plus neighborhoods do not overlap",
    "the number of fillable centers equals the requested n_pluses",
    "at least one center is fillable",
]

DEGENERATE_TEXTURES = ("no_pluses", "partial_arms", "mismatched_arms")
TEXTURES = ("default",) + DEGENERATE_TEXTURES

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-band rng 8..12", "valid": "7..16"},
    "grid_w": {"type": "int", "default": "difficulty-band rng 8..12", "valid": "7..16"},
    "n_pluses": {"type": "int", "default": "difficulty-band rng 2..4", "valid": "1..6"},
    "texture": {"type": "str", "default": "default", "valid": "|".join(TEXTURES)},
}


def _strict_int(value, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _validate_overrides(overrides: dict) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis: " + ", ".join(unknown))
    if "grid_h" in overrides and overrides["grid_h"] is not None:
        _strict_int(overrides["grid_h"], 7, 16, "grid_h")
    if "grid_w" in overrides and overrides["grid_w"] is not None:
        _strict_int(overrides["grid_w"], 7, 16, "grid_w")
    if "n_pluses" in overrides and overrides["n_pluses"] is not None:
        _strict_int(overrides["n_pluses"], 1, 6, "n_pluses")
    if "texture" in overrides and overrides["texture"] is not None:
        value = overrides["texture"]
        if type(value) is not str or value not in TEXTURES:
            raise ValueError("texture must be one of: " + ", ".join(TEXTURES))


def _sample_or_override(ctx, label: str, sample_low: int, sample_high: int,
                        valid_low: int, valid_high: int) -> int:
    """Preserve sampling bands while validating explicit values globally."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, valid_low, valid_high)
    return ctx.draw_int_strict(label, sample_low, sample_high)


def _lattice_capacity(height: int, width: int) -> int:
    """Capacity of the deterministic nonoverlapping 3-cell center lattice."""
    return len(range(1, height - 1, 3)) * len(range(1, width - 1, 3))


def _fit_unspecified_dimensions(height: int, width: int, count: int, overrides: dict):
    """Enlarge only sampled dimensions when an explicit count needs more room."""
    if _lattice_capacity(height, width) >= count:
        return height, width
    height_fixed = overrides.get("grid_h") is not None
    width_fixed = overrides.get("grid_w") is not None
    heights = (height,) if height_fixed else range(height, 17)
    widths = (width,) if width_fixed else range(width, 17)
    candidates = [
        ((candidate_h - height) + (candidate_w - width), candidate_h * candidate_w,
         candidate_h, candidate_w)
        for candidate_h in heights
        for candidate_w in widths
        if _lattice_capacity(candidate_h, candidate_w) >= count
    ]
    if not candidates:
        raise ValueError(
            f"cannot place {count} separated pluses in fixed {height}x{width} dimensions"
        )
    _, _, fitted_h, fitted_w = min(candidates)
    return fitted_h, fitted_w


def _clear(g, r, c) -> bool:
    h, w = len(g), len(g[0])
    # Reserve the center and a one-cell neighborhood, not just the four arms.
    # Otherwise a later plus can place an arm on an earlier plus center, turning
    # that center nonzero and making the intended fill operation a no-op.
    if not (1 <= r < h - 1 and 1 <= c < w - 1):
        return False
    for rr in range(r - 1, r + 2):
        for cc in range(c - 1, c + 2):
            if g[rr][cc] != 0:
                return False
    return True


def _draw_plus(g, r, c):
    for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
        g[rr][cc] = 3


def _try_draw_exact_plus(g, centers, r: int, c: int) -> bool:
    """Add one planted plus only when it creates exactly that one new target."""
    if not _clear(g, r, c):
        return False
    _draw_plus(g, r, c)
    expected = sorted([*centers, (r, c)])
    if _fillable_plus_centers(g) != expected:
        # _clear proved every arm cell was zero before this tentative draw.
        for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            g[rr][cc] = 0
        return False
    centers.append((r, c))
    centers.sort()
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    texture = overrides.get("texture", "default")
    if texture in DEGENERATE_TEXTURES:
        extras = sorted(set(overrides) - {"texture"})
        if extras:
            raise ValueError("degenerate texture cannot be combined with: " + ", ".join(extras))
        return _draw_from_degenerate(texture, None)

    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_band, w_band, n_band = (8, 9), (8, 9), (2, 2)
    elif difficulty == "hard":
        h_band, w_band, n_band = (11, 12), (11, 12), (3, 4)
    else:
        h_band, w_band, n_band = (8, 12), (8, 12), (2, 4)
    h = _sample_or_override(ctx, "grid_h", *h_band, 7, 16)
    w = _sample_or_override(ctx, "grid_w", *w_band, 7, 16)
    n_pluses = _sample_or_override(ctx, "n_pluses", *n_band, 1, 6)
    if overrides.get("n_pluses") is not None:
        h, w = _fit_unspecified_dimensions(h, w, n_pluses, overrides)

    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    centers = []
    for _ in range(120):
        if len(centers) >= n_pluses:
            break
        r = rng.randint(1, h - 2)
        c = rng.randint(1, w - 2)
        _try_draw_exact_plus(g, centers, r, c)
    # A failed random packing is restarted on a complete nonoverlapping lattice;
    # appending to a partial random packing can miss feasible placements.
    if len(centers) < n_pluses:
        g = full_grid(h, w, 0)
        centers = []
        candidates = [
            (r, c)
            for r in range(1, h - 1, 3)
            for c in range(1, w - 1, 3)
        ]
        rng.shuffle(candidates)
        for r, c in candidates:
            if len(centers) >= n_pluses:
                break
            _try_draw_exact_plus(g, centers, r, c)
    detected = _fillable_plus_centers(g)
    if len(centers) != n_pluses or detected != centers:
        raise ValueError(
            f"cannot place exactly {n_pluses} separated pluses in a {h}x{w} grid"
        )
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_pluses":
        return g
    if name == "partial_arms":
        g[1][3] = 3; g[2][2] = 3; g[2][4] = 3  # missing bottom arm
        g[5][6] = 3; g[5][8] = 3; g[6][7] = 3  # missing top arm
        return g
    if name == "mismatched_arms":
        g[1][3] = 4; g[3][3] = 4; g[2][2] = 4; g[2][4] = 4
        g[5][6] = 6; g[7][6] = 6; g[6][5] = 6; g[6][7] = 6
        return g
    raise ValueError(f"unknown degenerate texture: {name}")


def _fillable_plus_centers(grid, color=3):
    h, w = len(grid), len(grid[0])
    out = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] != 0:
                continue
            if (grid[r - 1][c] == color and grid[r + 1][c] == color
                    and grid[r][c - 1] == color and grid[r][c + 1] == color):
                out.append((r, c))
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return ["empty grid"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    height = len(grid)
    if not (7 <= height <= 16 and 7 <= width <= 16):
        errors.append("grid dimensions must each be in 7..16")
    if any(type(v) is not int or v not in (0, 3) for row in grid for v in row):
        errors.append("input should contain only 0 background and color-3 plus arms")
    centers = _fillable_plus_centers(grid, 3)
    if not centers:
        errors.append("no fillable hollow color-3 plus center")
    elif len(centers) > 6:
        errors.append("grid has more than 6 fillable hollow color-3 plus centers")
    if any(
        abs(r1 - r2) <= 2 and abs(c1 - c2) <= 2
        for i, (r1, c1) in enumerate(centers)
        for r2, c2 in centers[i + 1:]
    ):
        errors.append("fillable plus neighborhoods overlap")
    return errors
