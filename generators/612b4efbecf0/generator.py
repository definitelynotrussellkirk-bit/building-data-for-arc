"""Generator for puzzle a87f7484.

Rule: input is 3 × (3*N) (or (3*N) × 3) composed of N 3x3 zones. Find
the zone whose binary shape (color-blind) is unique among all zones;
output that zone.

Combinatorial axes (8): n_zones, orientation, shape_pair_kind,
unique_position, palette_kind, anchor_corner, asymmetry_force,
include_decoy.
Degenerates: all_unique, all_identical, single_zone.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "612b4efbecf0"
VERSION = "2.0.1"
TASK_ID = "612b4efbecf0"
SUMMARY = "3 × (3*N) grid; one 3x3 zone has unique shape, others share."

INVARIANTS = [
    "h=3 (or w=3) and the other dim = 3*N for N in [3, 7]",
    "exactly 1 zone has a unique non-zero binary shape",
    "all other zones share a different binary shape",
    "each zone uses a distinct non-bg color",
]

ORIENTATIONS = ("horizontal", "vertical")
SHAPE_PAIR_KINDS = ("dense_vs_sparse", "rotated", "checker_vs_diag",
                    "L_vs_T", "random")
DEGENERATE_TEXTURES = ("all_unique", "all_identical", "single_zone")
HELPFUL_TEXTURES = SHAPE_PAIR_KINDS

AXES = {
    "n_zones":         {"type": "int", "default": "rng 4..6", "valid": "3..7"},
    "orientation":     {"type": "str", "default": "rng helpful",
                        "valid": "|".join(ORIENTATIONS)},
    "shape_pair_kind": {"type": "str", "default": "rng helpful",
                        "valid": "|".join(SHAPE_PAIR_KINDS)},
    "palette_kind":    {"type": "str", "default": "broad",
                        "valid": "warm|cool|broad"},
    "unique_position": {"type": "str", "default": "rng",
                        "valid": "first|middle|last|random"},
    "anchor_corner":   {"type": "bool", "default": "false",
                        "valid": "true|false"},
    "asymmetry_force": {"type": "bool", "default": "false",
                        "valid": "true|false"},
    "texture":         {"type": "str", "default": "alias for shape_pair_kind",
                        "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


SHAPE_PATTERNS = [
    [[1, 0, 0], [0, 1, 1], [0, 1, 0]],
    [[1, 0, 0], [0, 1, 1], [1, 0, 0]],
    [[1, 0, 1], [1, 1, 1], [1, 0, 1]],
    [[0, 1, 1], [1, 1, 0], [1, 0, 1]],
    [[1, 1, 0], [0, 1, 0], [0, 1, 1]],
    [[1, 0, 1], [0, 1, 0], [1, 0, 1]],
    [[1, 1, 1], [1, 0, 1], [1, 1, 1]],
    [[0, 1, 0], [1, 1, 1], [0, 1, 0]],
]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        n_lo, n_hi = 3, 4
    elif difficulty == "hard":
        n_lo, n_hi = 5, 7
    else:
        n_lo, n_hi = 4, 6
    n = int(overrides.get("n_zones",
                          ctx.draw_int("n_zones", n_lo, n_hi)))
    n = max(3, min(7, n))
    orientation = overrides.get("orientation",
                                ctx.draw_choice("orientation",
                                                list(ORIENTATIONS)))
    pair_kind = (overrides.get("texture") or
                 overrides.get("shape_pair_kind")
                 or ctx.draw_choice("shape_pair_kind",
                                    list(SHAPE_PAIR_KINDS)))
    palette_kind = overrides.get("palette_kind", "broad")
    palette = _build_palette(palette_kind, n, rng)
    common, unique = _pick_pair(pair_kind, rng)
    unique_pos = overrides.get("unique_position", "random")
    if unique_pos == "first":
        unique_idx = 0
    elif unique_pos == "middle":
        unique_idx = n // 2
    elif unique_pos == "last":
        unique_idx = n - 1
    else:
        unique_idx = rng.randint(0, n - 1)
    if orientation == "vertical":
        h = 3 * n
        w = 3
        g = full_grid(h, w, 0)
        for i in range(n):
            shape = unique if i == unique_idx else common
            color = palette[i]
            for r in range(3):
                for c in range(3):
                    if shape[r][c] == 1:
                        g[i * 3 + r][c] = color
    else:
        h = 3
        w = 3 * n
        g = full_grid(h, w, 0)
        for i in range(n):
            shape = unique if i == unique_idx else common
            color = palette[i]
            for r in range(3):
                for c in range(3):
                    if shape[r][c] == 1:
                        g[r][i * 3 + c] = color
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """h=3 or w=3; other dim = 3*N; exactly one unique zone among N."""
    if not grid or not grid[0]:
        return ["grid is empty"]
    h, w = len(grid), len(grid[0])
    errors = []
    if h == 3:
        n = w // 3
        if w != 3 * n or n < 3:
            errors.append(f"expected w=3*N (N>=3) for h=3, got w={w}")
            return errors
        # extract zones horizontally
        zones = []
        for i in range(n):
            zone = tuple(grid[r][i*3 + c] for r in range(3) for c in range(3))
            zones.append(zone)
    elif w == 3:
        n = h // 3
        if h != 3 * n or n < 3:
            errors.append(f"expected h=3*N (N>=3) for w=3, got h={h}")
            return errors
        zones = []
        for i in range(n):
            zone = tuple(grid[i*3 + r][c] for r in range(3) for c in range(3))
            zones.append(zone)
    else:
        errors.append(f"expected h=3 or w=3, got {h}x{w}")
        return errors
    # normalize to binary shape (color-blind) for uniqueness test
    bin_zones = [tuple(1 if v != 0 else 0 for v in z) for z in zones]
    from collections import Counter
    counts = Counter(bin_zones)
    n_unique = sum(1 for v in counts.values() if v == 1)
    if n_unique != 1:
        errors.append(f"expected exactly 1 unique binary-shape zone, found {n_unique}")
    return errors


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    while len(pool) < n:
        for c in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            if c not in pool:
                pool.append(c)
    return pool[:n]


def _rand_shape(rng):
    """A random non-empty 3x3 binary shape."""
    while True:
        s = [[rng.randint(0, 1) for _ in range(3)] for _ in range(3)]
        if any(v for row in s for v in row):
            return s


def _pick_pair(kind, rng):
    # random distinct non-empty 3x3 shapes -> the unique zone's output varies
    common = _rand_shape(rng)
    for _ in range(50):
        unique = _rand_shape(rng)
        if unique != common:
            return common, unique
    return common, [[1, 1, 1], [0, 0, 0], [0, 0, 0]]


def _draw_from_degenerate(name, rng):
    n = 4
    h = 3; w = 3 * n
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    if name == "all_unique":
        # Every zone has a different shape — multiple "unique" candidates
        shapes = rng.sample(SHAPE_PATTERNS, n)
        for i, shape in enumerate(shapes):
            for r in range(3):
                for c in range(3):
                    if shape[r][c] == 1:
                        g[r][i * 3 + c] = palette[i]
        return g
    if name == "all_identical":
        # Every zone has the same shape — no unique zone
        shape = rng.choice(SHAPE_PATTERNS)
        for i in range(n):
            for r in range(3):
                for c in range(3):
                    if shape[r][c] == 1:
                        g[r][i * 3 + c] = palette[i]
        return g
    if name == "single_zone":
        # Only one zone exists
        h2 = 3; w2 = 3
        g2 = full_grid(h2, w2, 0)
        shape = rng.choice(SHAPE_PATTERNS)
        for r in range(3):
            for c in range(3):
                if shape[r][c] == 1:
                    g2[r][c] = palette[0]
        return g2
    return g
