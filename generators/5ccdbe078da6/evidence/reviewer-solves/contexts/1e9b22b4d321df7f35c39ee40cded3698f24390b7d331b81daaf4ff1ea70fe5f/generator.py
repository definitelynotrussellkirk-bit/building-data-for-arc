"""Same-color pairs expand to bbox borders, in first-appearance paint order.

Lines are lawful (two canonical examples contain them). Both diagonal signs,
intersections, and overwritten markers are sampled. Labels remain Racket-owned;
``rule_mirror`` is only an executable review/semantic contract.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "5ccdbe078da6"
VERSION = "3.0.0"
RULE_HASH = "d8da2d7cc24b"
SUMMARY = (
    "Zero-background grids with 1-3 distinct nonzero colors, each appearing "
    "twice. Pairs may be either diagonal or collinear. Paint each pair's "
    "bounding-box perimeter, in row-major first-color-occurrence order; "
    "later colors overwrite earlier borders, including original markers."
)
INVARIANTS = [
    "Rectangular integer grid, ARC colors 0..9, with background 0.",
    "1-3 nonzero colors, exactly two distinct markers per color.",
    "A pair may define a rectangle, a horizontal line, or a vertical line.",
    "Generated collinear pairs are separated by at least one cell (nonidentity).",
    "Overlaps are lawful; the canonical reading-order overwrite rule applies.",
]
PALETTES = {
    "default": tuple(range(1, 10)),
    "warm": (2, 4, 6, 9),
    "cool": (1, 3, 5, 8),
    "varied": (1, 2, 7, 8, 9),
}
PALETTE_KINDS = tuple(PALETTES)
PAIR_KINDS = ("mixed", "down_right", "down_left", "horizontal", "vertical")
AXES = {
    "grid_h": {"type": "int", "default": "core 5..6; extended 4..10", "valid": "4..10"},
    "grid_w": {"type": "int", "default": "core 6..7; extended 5..12", "valid": "5..12"},
    "n_pairs": {"type": "int", "default": "core 2; extended 1..3", "valid": "1..3"},
    "palette_kind": {"type": "str", "default": "uniform", "valid": "default|warm|cool|varied"},
    "pair_kind": {"type": "str", "default": "mixed-biased", "valid": "mixed|down_right|down_left|horizontal|vertical"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []  # Every declared tuple is realizable.


def _positions(grid):
    found = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 0:
                found.setdefault(color, []).append((r, c))
    return found


def _kind(cells):
    (r, c), (s, d) = sorted(cells)
    return ("horizontal" if r == s else "vertical" if c == d else
            "down_right" if c < d else "down_left")


def _draw_int(ctx, name, core_bounds, wide_bounds, core):
    """Difficulty/profile only affects defaults, never override validity."""
    bounds = wide_bounds if ctx.overrides.get(name) is not None or not core else core_bounds
    return ctx.draw_int(name, *bounds)


def _candidate_pairs(h, w, kind):
    """Finite complete candidate pool; no retry cap can discard a legal pin."""
    points = [(r, c) for r in range(h) for c in range(w)]
    out = []
    for i, a in enumerate(points):
        for b in points[i + 1:]:
            actual = _kind((a, b))
            if kind != "mixed" and actual != kind:
                continue
            if actual == "horizontal" and b[1] - a[1] < 2:
                continue
            if actual == "vertical" and b[0] - a[0] < 2:
                continue
            out.append((a, b))
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for key in ("grid_h", "grid_w", "n_pairs"):
        value = overrides.get(key)
        if value is not None and type(value) is not int:
            raise TypeError(f"{key} must be an integer, not {type(value).__name__}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    # Two-thirds anchor the canonical dimensions/count; one-third explores.
    core = ctx.draw_choice("profile", ("core", "core", "extended")) == "core"
    h = _draw_int(ctx, "grid_h", (5, 6), (4, 10), core)
    w = _draw_int(ctx, "grid_w", (6, 7), (5, 12), core)
    n = _draw_int(ctx, "n_pairs", (2, 2), (1, 3), core)
    palette = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    kind = ctx.draw_choice("pair_kind", ("mixed",) * 8 + PAIR_KINDS[1:])
    rng = ctx.draw_rng(f"layout/{difficulty or 'medium'}")
    colors = ctx.draw_rng("colors").sample(PALETTES[palette], n)
    grid = full_grid(h, w, 0)
    pairs = []
    # Constructive crossing cases prevent reliance on rare random collisions.
    # Numeric color assignment is independent of geometry and reading order.
    if kind == "mixed" and n >= 2:
        modes = ("scattered", "crossing", "marker_overlap")
        mode = rng.choice(modes)
        if mode != "scattered":
            a, b, c, d = sorted(rng.sample(range(h), 4))
            p, q, s, t = sorted(rng.sample(range(w), 4))
            last = d if mode == "crossing" else c
            # The second outline crosses the first. In marker_overlap its
            # bottom edge also repaints the first pair's bottom-right marker.
            first = ((a, p), (c, s))
            second = ((b, q), (last, t))
            if mode == "crossing" and rng.randrange(2):
                first = ((a, s), (c, p))
            if rng.randrange(2):
                second = ((b, t), (last, q))
            pairs.extend((first, second))
    used = {point for pair in pairs for point in pair}
    candidates = _candidate_pairs(h, w, kind)
    while len(pairs) < n:
        legal = [pair for pair in candidates if not (set(pair) & used)]
        if not legal:
            raise RuntimeError("no disjoint marker pair within the declared domain")
        pair = rng.choice(legal)
        pairs.append(pair)
        used.update(pair)
    for color, pair in zip(colors, pairs):
        for r, c in pair:
            grid[r][c] = color
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["empty or non-grid input"]
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return ["rows must be sequences"]
    w = len(grid[0])
    if w == 0 or any(len(row) != w for row in grid):
        return ["empty or ragged grid"]
    if len(grid) > 30 or w > 30:
        return ["grid exceeds ARC 30x30 bounds"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integer ARC colors 0..9 (not booleans)"]
    groups = _positions(grid)
    errors = []
    if not any(v == 0 for row in grid for v in row):
        errors.append("background 0 is absent")
    if not 1 <= len(groups) <= 3:
        errors.append(f"expected 1..3 pair colors, found {len(groups)}")
    errors.extend(f"color {color} has {len(cells)} markers, expected 2"
                  for color, cells in groups.items() if len(cells) != 2)
    return errors


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_pairs": len(_positions(grid))}


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    if len(_positions(grid)) != 2 or not (5 <= len(grid) <= 6 and 6 <= len(grid[0]) <= 7):
        return ["outside canonical dimensions / two-color profile"]
    return []


def _render(grid, *, order="reading", fill=False, keep_markers=False, skip_lines=False,
            skip_negative=False):
    groups = _positions(grid)
    colors = list(groups)
    if order == "ascending":
        colors.sort()
    elif order == "descending":
        colors.sort(reverse=True)
    out = full_grid(len(grid), len(grid[0]), 0)
    for color in colors:
        cells = groups[color]
        if len(cells) != 2 or (skip_lines and _kind(cells) in ("horizontal", "vertical")) or (
            skip_negative and _kind(cells) == "down_left"
        ):
            for r, c in cells:
                out[r][c] = color
            continue
        r0 = min(p[0] for p in cells); r1 = max(p[0] for p in cells)
        c0 = min(p[1] for p in cells); c1 = max(p[1] for p in cells)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if fill or r in (r0, r1) or c in (c0, c1):
                    out[r][c] = color
    if keep_markers:
        for color, cells in groups.items():
            for r, c in cells:
                out[r][c] = color
    return out


def rule_mirror(grid):
    """Full reference behavior on valid grids, including non-pair preservation."""
    return _render(grid)


def rival_numeric_descending(grid):
    return _render(grid, order="descending")


def rival_numeric_ascending(grid):
    return _render(grid, order="ascending")


def rival_keep_markers(grid):
    return _render(grid, keep_markers=True)


def rival_fill(grid):
    return _render(grid, fill=True)


def rival_skip_lines(grid):
    return _render(grid, skip_lines=True)


def rival_skip_negative(grid):
    return _render(grid, skip_negative=True)


SEMANTIC_RIVALS = {
    "numeric_descending": rival_numeric_descending,
    "numeric_ascending": rival_numeric_ascending,
    "keep_markers": rival_keep_markers,
    "filled_bbox": rival_fill,
    "ignore_lines": rival_skip_lines,
    "ignore_negative_diagonal": rival_skip_negative,
}
# Every declared witness is an actual output disagreement, not just morphology.
SEMANTIC_WITNESSES = {
    name: (lambda grid, rival=rival: rival(grid) != rule_mirror(grid))
    for name, rival in SEMANTIC_RIVALS.items()
}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}
CANONICAL_SHORTCUTS = {
    "numeric_descending": rival_numeric_descending,
    "keep_markers": rival_keep_markers,
    "ignore_negative_diagonal": rival_skip_negative,
}
# These are honest competitors, not a universal claim of rule identifiability.
LESSON_COMPETITORS = SEMANTIC_RIVALS


def mutation_fixtures():
    """Invalid scenes for validators, not selectable training textures."""
    empty = full_grid(6, 7, 0)
    single = full_grid(6, 7, 0); single[2][2] = 4
    triple = full_grid(6, 7, 0); triple[1][1] = triple[2][2] = triple[3][3] = 4
    invalid = full_grid(6, 7, 0); invalid[1][1] = invalid[3][3] = 10
    return [("empty", empty), ("singleton", single), ("triple", triple), ("invalid_color", invalid)]
