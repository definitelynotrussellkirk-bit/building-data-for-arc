"""Single-cell hole fill: lawful rings, inert contrasts, and exact controls.

Labels remain the selected Racket rule. Difficulty changes sampling preferences,
not validity. Normal lessons show both the eight-neighbor and zero-center gates.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "d982cffd80f8"
VERSION = "3.0.0"
RULE_HASH = "58201e67a052"
SUMMARY = (
    "Fill a zero cell only when all eight original neighbors share one nonzero "
    "color. Sample 1-6 full rings with inert near-rings, nonzero centers, and "
    "optional singleton colors. Preserve distractions and original colored cells."
)
INVARIANTS = [
    "rectangular integer grid with zero background and colors 0..9",
    "one to six positive single-cell holes have eight equal nonzero neighbors",
    "all decisions inspect the original input, without cascading updates",
    "touching borders and inert colored distractions are lawful",
]
PALETTE_KINDS = ("default", "warm", "cool", "varied")
HELPFUL_TEXTURES = PALETTE_KINDS
DEGENERATE_TEXTURES = ("no_rings", "filled_centers", "partial_ring")
PALETTES = {
    "default": tuple(range(1, 10)),
    "warm": (2, 4, 6, 7, 9),
    "cool": (1, 3, 5, 8),
    "varied": tuple(range(1, 10)),
}
AXES = {
    "grid_h": {"type": "int", "default": "weighted 5..14; periodic 9", "valid": "5..14"},
    "grid_w": {"type": "int", "default": "weighted 5..16; periodic 9", "valid": "5..16"},
    "n_rings": {"type": "int", "default": "prefer 2 easy, 2..3 medium, 3 hard", "valid": "1..6"},
    "palette_size": {"type": "int", "default": "prefer 3 foreground colors, at least 2", "valid": "1..6"},
    "palette_kind": {"type": "str", "default": "rng palette family", "valid": "|".join(PALETTE_KINDS)},
    "texture": {"type": "str", "default": "alias for palette_kind", "valid": "|".join(PALETTE_KINDS)},
}
# Compatibility names do not add independent Cartesian sampling dimensions.
# Both names retain exact validation, keyed provenance and observation tests.
OVERRIDE_ALIASES = {"n_distinct_colors": "palette_size"}
# Strict classification: only actual, axis-bearing infeasibilities are accepted.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3


class IncompatibleOverrides(ValueError):
    def __init__(self, message, axes):
        super().__init__(message)
        self.incompatible_axes = tuple(axes)


def _alias(overrides, first, second):
    a, b = overrides.get(first), overrides.get(second)
    if a is not None and b is not None and a != b:
        raise IncompatibleOverrides(f"{first} and {second} are aliases and must agree", (first, second))
    return a if a is not None else b


def _weighted(options, preferred, repetitions=12):
    options = list(options)
    return options + [value for value in preferred if value in options] * repetitions


def _ring_cells(r0, c0):
    return [(r0 + dr, c0 + dc) for dr in range(3) for dc in range(3)
            if (dr, dc) != (1, 1)]


def _paint_ring(grid, r0, c0, color):
    for r, c in _ring_cells(r0, c0):
        grid[r][c] = color


def _neighbors(grid, r, c):
    return [grid[r + dr][c + dc] for dr in (-1, 0, 1) for dc in (-1, 0, 1)
            if dr or dc]


def _fillable_centers(grid):
    centers = []
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            ring = _neighbors(grid, r, c)
            if grid[r][c] == 0 and ring[0] != 0 and len(set(ring)) == 1:
                centers.append((r, c, ring[0]))
    return centers


def _shape(ctx, overrides, requested_rings, preferred_rings):
    heights = [overrides["grid_h"]] if "grid_h" in overrides else list(range(5, 15))
    widths = [overrides["grid_w"]] if "grid_w" in overrides else list(range(5, 17))
    minimum = requested_rings if requested_rings is not None else 1
    possible = [(h, w) for h in heights for w in widths if (h // 3) * (w // 3) >= minimum]
    if not possible:
        axes = [name for name in ("grid_h", "grid_w", "n_rings") if name in overrides]
        raise IncompatibleOverrides("pinned dimensions cannot hold the requested disjoint 3x3 rings", axes)
    # Prefer room for two teaching contrasts. Pinned narrow research cases may
    # legitimately have no room; their exact ring/dimension claims still hold.
    desired = (requested_rings if requested_rings is not None else preferred_rings) + 2
    teaching = [(h, w) for h, w in possible if (h // 3) * (w // 3) >= desired]
    if teaching:
        possible = teaching
    h_options = sorted({h for h, _ in possible})
    periodic = (ctx.seed + ctx.sample_index) % 5 == 0
    if periodic and "grid_h" not in overrides and 9 in h_options:
        h_options = [9]
    h = ctx.draw_choice("grid_h", _weighted(h_options, (7, 8, 9)))
    w_options = sorted({w for hh, w in possible if hh == h})
    if periodic and "grid_w" not in overrides and 9 in w_options:
        w_options = [9]
    w = ctx.draw_choice("grid_w", _weighted(w_options, (7, 8, 9, 10)))
    return h, w


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES) - set(OVERRIDE_ALIASES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    overrides = {key: value for key, value in overrides.items() if value is not None}
    supplied = set(overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        if supplied != {"texture"}:
            raise IncompatibleOverrides("negative fixtures cannot mix with normal controls", sorted(supplied))
        return _draw_from_degenerate(overrides["texture"], None)
    for name, lo, hi in (("grid_h", 5, 14), ("grid_w", 5, 16), ("n_rings", 1, 6),
                         ("palette_size", 1, 6), ("n_distinct_colors", 1, 6)):
        if name in overrides and (type(overrides[name]) is not int or not lo <= overrides[name] <= hi):
            raise ValueError(f"{name} must be an integer in {lo}..{hi} (not bool)")
    for name in ("palette_kind", "texture"):
        if name in overrides and overrides[name] not in PALETTE_KINDS:
            raise ValueError(f"{name} must be one of {PALETTE_KINDS}; negative fixtures are not normal textures")
    requested_colors = _alias(overrides, "palette_size", "n_distinct_colors")
    requested_kind = _alias(overrides, "palette_kind", "texture")
    if requested_colors is not None:
        overrides.update(palette_size=requested_colors, n_distinct_colors=requested_colors)
    if requested_kind is not None:
        overrides.update(palette_kind=requested_kind, texture=requested_kind)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    preferred = 3 if difficulty == "hard" else 2
    requested_rings = overrides.get("n_rings")
    h, w = _shape(ctx, overrides, requested_rings, preferred)
    capacity = (h // 3) * (w // 3)
    limit = min(6, capacity if requested_rings is not None else max(1, capacity - 2))
    target = ctx.draw_choice("n_rings", _weighted(range(1, limit + 1),
                             (2, 3) if difficulty in (None, "medium") else (preferred,)))
    kind_options = [kind for kind in PALETTE_KINDS
                    if requested_colors is None or len(PALETTES[kind]) >= requested_colors]
    if requested_kind is not None and requested_kind not in kind_options:
        axes = [key for key in ("palette_kind", "texture", "palette_size", "n_distinct_colors")
                if key in supplied]
        raise IncompatibleOverrides("requested palette family has too few distinct colors", axes)
    kind = ctx.draw_choice("palette_kind", kind_options)
    ctx.draw_choice("texture", (kind,))
    if requested_colors is None:
        choices = list(range(2, min(6, len(PALETTES[kind])) + 1))
        if (seed + sample_index) % 5 == 0:
            choices = [3]
    else:
        choices = [requested_colors]
    count = ctx.draw_choice("palette_size", _weighted(choices, (3,)))
    ctx.draw_choice("n_distinct_colors", (count,))
    rng = ctx.draw_rng("layout")
    palette_rng = ctx.draw_rng("palette:" + kind)
    colors = palette_rng.sample(list(PALETTES[kind]), count)
    # Varied palettes deliberately span warm/cool groups whenever count permits.
    if kind == "varied" and count >= 2:
        if not set(colors).intersection(PALETTES["warm"]):
            colors[0] = palette_rng.choice(PALETTES["warm"])
        if not set(colors).intersection(PALETTES["cool"]):
            colors[-1] = palette_rng.choice(PALETTES["cool"])
    row_offset = rng.randrange(h % 3 + 1)
    col_offset = rng.randrange(w % 3 + 1)
    anchors = [(r, c) for r in range(row_offset, h - 2, 3)
               for c in range(col_offset, w - 2, 3)]
    rng.shuffle(anchors)
    grid = full_grid(h, w, 0)
    used = []
    for i, (r, c) in enumerate(anchors[:target]):
        _paint_ring(grid, r, c, colors[i % count])
        used.append((r, c))
    decoys = anchors[target:target + 2]
    if decoys:
        r, c = decoys[0]
        border = colors[target % count]
        _paint_ring(grid, r, c, border)
        corner = rng.choice(((0, 0), (0, 2), (2, 0), (2, 2)))
        near_corner = (r + corner[0], c + corner[1])
        other = colors[(target + 1) % count]
        grid[near_corner[0]][near_corner[1]] = other if count > 1 and rng.randrange(2) else 0
        used.append((r, c))
    if len(decoys) > 1:
        r, c = decoys[1]
        border = colors[(target + 2) % count]
        _paint_ring(grid, r, c, border)
        grid[r + 1][c + 1] = colors[(target + 3) % count]
        used.append((r, c))
    # Realize every requested color; singleton distractors are canonical-lawful.
    occupied = {(r + dr, c + dc) for r, c in used for dr in range(3) for dc in range(3)}
    free = [(r, c) for r in range(h) for c in range(w) if (r, c) not in occupied]
    rng.shuffle(free)
    present = {value for row in grid for value in row if value}
    missing = [color for color in colors if color not in present]
    if len(free) < len(missing) and decoys and grid[near_corner[0]][near_corner[1]] == 0:
        # A fully occupied 6x6 canvas can still realize six colors: use a
        # different-colored corner instead of a missing corner. Both preserve
        # the cardinal/seven-neighbor counterexample and the exact ring count.
        grid[near_corner[0]][near_corner[1]] = missing.pop(0)
    if len(free) < len(missing):
        raise IncompatibleOverrides("no space for all requested foreground colors", sorted(supplied))
    for color, (r, c) in zip(missing, free):
        grid[r][c] = color
    return grid


def observe_overrides(grid):
    colors = {value for row in grid for value in row if value != 0}
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_rings": len(_fillable_centers(grid)),
            "palette_size": len(colors), "n_distinct_colors": len(colors)}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be nonempty and rectangular"]
    if any(not isinstance(row, (list, tuple)) or not row for row in grid):
        return ["rows must be nonempty sequences"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid values must be integer digits 0..9 (not bool)"]
    if not (3 <= len(grid) <= 30 and 3 <= len(grid[0]) <= 30):
        return ["grid dimensions must be within 3..30"]
    count = len(_fillable_centers(grid))
    errors = [] if 1 <= count <= 6 else ["normal input must contain 1..6 fillable centers"]
    if isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            observed = observe_overrides(grid)
            for axis, actual in observed.items():
                if axis in requested and requested[axis] is not None and requested[axis] != actual:
                    errors.append(f"{axis} requested {requested[axis]!r}, observed {actual!r}")
    return errors


def strict_canonical_like(grid):
    """The positive local-hole family; touching rings and inert cells are lawful."""
    return self_check(grid)


def _rival(grid, mode):
    out = [list(row) for row in grid]
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            if grid[r][c] != 0 and mode != "overwrite_nonzero":
                continue
            values = _neighbors(grid, r, c)
            if mode == "four_neighbors":
                values = [grid[r - 1][c], grid[r + 1][c], grid[r][c - 1], grid[r][c + 1]]
            if mode == "seven_neighbors":
                color, frequency = Counter(values).most_common(1)[0]
                if color != 0 and frequency >= 7:
                    out[r][c] = color
            elif values[0] != 0 and len(set(values)) == 1:
                out[r][c] = values[0]
    return out


def _four_neighbors(grid):
    return _rival(grid, "four_neighbors")


def _seven_neighbors(grid):
    return _rival(grid, "seven_neighbors")


def _overwrite_nonzero(grid):
    return _rival(grid, "overwrite_nonzero")


def _identity(grid):
    return [list(row) for row in grid]


def _positive_witness(grid):
    return bool(_fillable_centers(grid))


def _near_ring_witness(grid):
    return any(grid[r][c] == 0 and len(set(_neighbors(grid, r, c))) > 1
               and max(Counter(_neighbors(grid, r, c)).values()) == 7
               and grid[r - 1][c] != 0
               and len({grid[r - 1][c], grid[r + 1][c], grid[r][c - 1], grid[r][c + 1]}) == 1
               for r in range(1, len(grid) - 1) for c in range(1, len(grid[0]) - 1))


def _nonzero_center_witness(grid):
    return any(grid[r][c] != 0 and len(set(_neighbors(grid, r, c))) == 1
               and grid[r - 1][c] not in (0, grid[r][c])
               for r in range(1, len(grid) - 1) for c in range(1, len(grid[0]) - 1))


SEMANTIC_WITNESSES = {"positive_fill": _positive_witness,
                      "near_ring": _near_ring_witness,
                      "nonzero_center": _nonzero_center_witness}
SEMANTIC_RIVALS = {"four_neighbors": _four_neighbors, "seven_neighbors": _seven_neighbors,
                   "overwrite_nonzero": _overwrite_nonzero, "identity": _identity}
WITNESS_RIVALS = {"positive_fill": ["identity"],
                  "near_ring": ["four_neighbors", "seven_neighbors"],
                  "nonzero_center": ["overwrite_nonzero"]}
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name]
                      for name in ("four_neighbors", "seven_neighbors", "overwrite_nonzero")}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _draw_from_degenerate(name, rng):
    """Negative validator fixtures, deliberately outside normal AXES.texture."""
    grid = full_grid(8, 8, 0)
    if name == "filled_centers":
        _paint_ring(grid, 1, 1, 4)
        grid[2][2] = 3
    elif name == "partial_ring":
        _paint_ring(grid, 1, 1, 4)
        grid[1][1] = 0
    elif name != "no_rings":
        raise ValueError(f"unknown negative fixture: {name}")
    return grid
