"""Constructive sampler for the diagonal-X bloom rule.

Every nonzero input cell is a seed.  The selected Racket authority builds a
fresh zero grid and paints the seed plus its four diagonal neighbours cyan,
clipping the stencil at the canvas boundary and taking the union of overlaps.

The five-scene schedule deliberately teaches three canonical-fitting shortcuts:
cyan input cells are real seeds, boundary seeds are real seeds, and seed color 3
is not special.  A mixed interior scene also exercises overlapping stencils.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cfd0943c5b14"
TASK_ID = GENERATOR_ID
RULE_HASH = "6e86df413712"
VERSION = "3.0.0"

SCENES = ("canonical", "edge_seed", "mixed_overlap", "corner_seed", "cyan_interior")
OFFSETS = ((0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1))

SUMMARY = (
    "6..12 by 6..12 zero-background grids with 2..5 sparse nonzero seeds. "
    "A deterministic five-scene curriculum alternates canonical interior "
    "color-3 seeds, non-cyan edge seeds, mixed-color interior seeds with "
    "overlapping X footprints, non-cyan corner seeds, and cyan interior seeds. "
    "Every nonzero cell grows into a cyan "
    "diagonal X on a fresh grid; out-of-bounds cells are clipped and overlaps "
    "are unioned."
)

INVARIANTS = [
    "background is 0 and every nonzero cell is a seed, including color 8",
    "2..5 seeds with no orthogonally adjacent pair",
    "at most one boundary seed; non-cyan edge and corner cases are scheduled explicitly",
    "two schedule scenes contain cyan seeds and three omit cyan from the input",
    "mixed_overlap contains cyan and non-cyan interior seeds whose X stencils overlap",
]

AXES = {
    "grid_h": {"type": "int", "default": "scene schedule", "valid": "6..12"},
    "grid_w": {"type": "int", "default": "scene schedule", "valid": "6..12"},
    "seed_count": {"type": "int", "default": "difficulty/scene schedule", "valid": "2..5"},
    "scene": {"type": "str", "default": "sample_index mod 5", "valid": SCENES},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.18
SCHEDULE_PROFILES = SCENES


def _grid_diagnostics(grid):
    if not isinstance(grid, list) or not grid:
        return None, ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return None, ["rows must be nonempty lists"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None, ["ragged grid"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                return None, [f"cell ({r},{c}) must be an integer color 0..9"]
    return (len(grid), width), []


def _seed_cells(grid):
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]


def _boundary_kind(h, w, r, c):
    if r in (0, h - 1) and c in (0, w - 1):
        return "corner"
    if r in (0, h - 1) or c in (0, w - 1):
        return "edge"
    return "interior"


def _footprint(h, w, r, c):
    return frozenset(
        (r + dr, c + dc)
        for dr, dc in OFFSETS
        if 0 <= r + dr < h and 0 <= c + dc < w
    )


def _overlap_pair_count(grid):
    h, w = len(grid), len(grid[0])
    points = _seed_cells(grid)
    count = 0
    for index, (r1, c1, _value1) in enumerate(points):
        first = _footprint(h, w, r1, c1)
        for r2, c2, _value2 in points[index + 1 :]:
            if first & _footprint(h, w, r2, c2):
                count += 1
    return count


def _has_orthogonal_pair(points):
    coords = {(r, c) for r, c, _value in points}
    return any(
        (r + dr, c + dc) in coords
        for r, c in coords
        for dr, dc in ((1, 0), (0, 1))
    )


def _classify_scene(grid):
    h, w = len(grid), len(grid[0])
    points = _seed_cells(grid)
    if not points:
        return None
    kinds = [_boundary_kind(h, w, r, c) for r, c, _value in points]
    values = {value for _r, _c, value in points}
    if values == {3} and set(kinds) == {"interior"}:
        return "canonical"
    if 8 not in values and kinds.count("edge") == 1 and kinds.count("corner") == 0:
        return "edge_seed"
    if 8 in values and len(values) >= 2 and set(kinds) == {"interior"} and _overlap_pair_count(grid):
        return "mixed_overlap"
    if 8 not in values and kinds.count("corner") == 1 and kinds.count("edge") == 0:
        return "corner_seed"
    if values == {8} and set(kinds) == {"interior"}:
        return "cyan_interior"
    return None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the compact four-scene input grammar and canonical examples."""
    dims, errors = _grid_diagnostics(grid)
    if errors:
        return errors
    h, w = dims
    if not (6 <= h <= 12 and 6 <= w <= 12):
        errors.append(f"grid dimensions {h}x{w} outside 6..12")
    points = _seed_cells(grid)
    if not (2 <= len(points) <= 5):
        errors.append(f"expected 2..5 seeds, found {len(points)}")
    if _has_orthogonal_pair(points):
        errors.append("seed cells must not be orthogonally adjacent")
    if points and _classify_scene(grid) is None:
        errors.append("seed colors/boundary placement do not match a declared scene")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the official 8x8/9x9, two interior color-3 seed manifold."""
    dims, errors = _grid_diagnostics(grid)
    if errors:
        return errors
    h, w = dims
    if (h, w) not in {(8, 8), (9, 9)}:
        errors.append("dimensions are not an official 8x8 or 9x9 profile")
    points = _seed_cells(grid)
    if len(points) != 2:
        errors.append(f"expected exactly two seeds, found {len(points)}")
    if {value for _r, _c, value in points} != {3}:
        errors.append("canonical seeds must all use color 3")
    if any(_boundary_kind(h, w, r, c) != "interior" for r, c, _value in points):
        errors.append("canonical seeds must be interior")
    if _has_orthogonal_pair(points):
        errors.append("canonical seeds must not be orthogonally adjacent")
    if points and _overlap_pair_count(grid):
        errors.append("canonical seed stencils must be disjoint")
    return errors


def observe_overrides(grid):
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "seed_count": len(_seed_cells(grid)),
        "scene": _classify_scene(grid) or "unclassified",
    }


def rule_mirror(grid):
    """Independent-style Python mirror used only for contracts and tests."""
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for r, c, _value in _seed_cells(grid):
        for rr, cc in _footprint(h, w, r, c):
            out[rr][cc] = 8
    return out


def _filtered_rule(grid, predicate):
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for r, c, value in _seed_cells(grid):
        if predicate(r, c, value, h, w):
            for rr, cc in _footprint(h, w, r, c):
                out[rr][cc] = 8
    return out


def _rival_ignore_cyan_seed(grid):
    return _filtered_rule(grid, lambda _r, _c, value, _h, _w: value != 8)


def _rival_ignore_boundary_seeds(grid):
    return _filtered_rule(
        grid,
        lambda r, c, _value, h, w: 0 < r < h - 1 and 0 < c < w - 1,
    )


def _rival_only_color_three(grid):
    return _filtered_rule(grid, lambda _r, _c, value, _h, _w: value == 3)


def _witness_cyan_seed(grid):
    return any(value == 8 for _r, _c, value in _seed_cells(grid))


def _witness_boundary_seed(grid):
    h, w = len(grid), len(grid[0])
    return any(_boundary_kind(h, w, r, c) != "interior" for r, c, _value in _seed_cells(grid))


def _witness_non_three_seed(grid):
    return any(value != 3 for _r, _c, value in _seed_cells(grid))


def _witness_overlapping_stamps(grid):
    return _overlap_pair_count(grid) > 0


SEMANTIC_RIVALS = {
    "ignore_cyan_seed": _rival_ignore_cyan_seed,
    "ignore_boundary_seeds": _rival_ignore_boundary_seeds,
    "only_color_three": _rival_only_color_three,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "cyan_seed": _witness_cyan_seed,
    "boundary_seed": _witness_boundary_seed,
    "non_three_seed": _witness_non_three_seed,
    "overlapping_stamps": _witness_overlapping_stamps,
}
WITNESS_RIVALS = {
    "cyan_seed": ["ignore_cyan_seed"],
    "boundary_seed": ["ignore_boundary_seeds"],
    "non_three_seed": ["only_color_three"],
}
BRANCH_WITNESSES = ("overlapping_stamps",)


def lesson_identifiable(demos, query):
    reasons = []
    query_input = query["input"]
    query_output = query.get("output", rule_mirror(query_input))
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query_input) != query_output:
                reasons.append(f"{name} fits every demonstration but changes the query answer")
    return reasons


def schedule_profile(seed, sample_index, difficulty=None):
    return SCENES[sample_index % len(SCENES)]


def _axis_int(ctx, overrides, label, lo, hi, default):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_choice(label, (default,))


def _axis_scene(ctx, overrides, default):
    if "scene" in overrides and overrides["scene"] is not None:
        return ctx.draw_choice("scene", SCENES)
    return ctx.draw_choice("scene", (default,))


def _default_dimensions(scene, sample_index):
    if scene == "canonical":
        size = 8 if (sample_index // len(SCENES)) % 2 == 0 else 9
        return size, size
    if scene == "edge_seed":
        return 9, 9
    if scene == "mixed_overlap":
        return 8, 9
    if scene == "corner_seed":
        return 9, 8
    return 8, 8


def _default_seed_count(scene, difficulty):
    if scene == "canonical":
        return 2
    if difficulty == "easy":
        return 2
    if difficulty == "hard":
        return 5
    if difficulty == "medium":
        return 3
    return 4


def _interior_cells(h, w, parity):
    return [
        (r, c)
        for r in range(1, h - 1)
        for c in range(1, w - 1)
        if (r + c) % 2 == parity
    ]


def _choose_nonoverlap_pair(h, w, candidates, rng):
    pairs = [
        (first, second)
        for index, first in enumerate(candidates)
        for second in candidates[index + 1 :]
        if not (_footprint(h, w, *first) & _footprint(h, w, *second))
    ]
    if not pairs:
        raise RuntimeError(f"no disjoint interior seed pair fits {h}x{w}")
    return list(rng.choice(pairs))


def _choose_overlap_pair(h, w, candidates, rng):
    pool = set(candidates)
    pairs = []
    for r, c in candidates:
        for dr, dc in ((0, 2), (2, 0)):
            other = (r + dr, c + dc)
            if other in pool:
                pairs.append(((r, c), other))
    if not pairs:
        raise RuntimeError(f"no overlapping-X interior pair fits {h}x{w}")
    return list(rng.choice(pairs))


def _fill_positions(initial, candidates, count, rng):
    chosen = list(initial)
    remaining = [cell for cell in candidates if cell not in chosen]
    rng.shuffle(remaining)
    chosen.extend(remaining[: count - len(chosen)])
    if len(chosen) != count:
        raise RuntimeError(f"could place only {len(chosen)} of {count} seeds")
    return chosen


def _positions_for_scene(h, w, count, scene, rng):
    if scene in {"canonical", "cyan_interior"}:
        parity = rng.randrange(2)
        candidates = _interior_cells(h, w, parity)
        initial = _choose_nonoverlap_pair(h, w, candidates, rng)
        return _fill_positions(initial, candidates, count, rng)

    if scene == "mixed_overlap":
        parity = rng.randrange(2)
        candidates = _interior_cells(h, w, parity)
        initial = _choose_overlap_pair(h, w, candidates, rng)
        cyan_anchor = initial[0]
        candidates = [
            cell
            for cell in candidates
            if cell in initial or cyan_anchor not in _footprint(h, w, *cell)
        ]
        return _fill_positions(initial, candidates, count, rng)

    if scene == "corner_seed":
        corners = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]
        anchor = rng.choice(corners)
    else:
        edges = (
            [(0, c) for c in range(1, w - 1)]
            + [(h - 1, c) for c in range(1, w - 1)]
            + [(r, 0) for r in range(1, h - 1)]
            + [(r, w - 1) for r in range(1, h - 1)]
        )
        anchor = rng.choice(edges)
    candidates = [
        cell
        for cell in _interior_cells(h, w, (anchor[0] + anchor[1]) % 2)
        if anchor not in _footprint(h, w, *cell)
    ]
    return _fill_positions([anchor], candidates, count, rng)


def _colors_for_scene(count, scene, rng):
    if scene in {"canonical", "edge_seed"}:
        return [3] * count
    if scene == "corner_seed":
        return [1] * count
    if scene == "cyan_interior":
        return [8] * count
    # Position zero is the cyan anchor chosen above.  Additional placements are
    # forbidden from stamping its center, so this seed always has a causal pixel.
    colors = [8, 3]
    palette = [1, 2, 3, 4, 5, 6, 7, 9]
    colors.extend(rng.choice(palette) for _ in range(count - 2))
    return colors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w", "seed_count"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool/float/string)")
    if "scene" in overrides and overrides["scene"] is not None and type(overrides["scene"]) is not str:
        raise TypeError("scene override must be a string")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled_scene = schedule_profile(seed, sample_index, difficulty)
    scene = _axis_scene(ctx, overrides, scheduled_scene)
    default_h, default_w = _default_dimensions(scene, sample_index)
    h = _axis_int(ctx, overrides, "grid_h", 6, 12, default_h)
    w = _axis_int(ctx, overrides, "grid_w", 6, 12, default_w)
    count = _axis_int(
        ctx,
        overrides,
        "seed_count",
        2,
        5,
        _default_seed_count(scene, difficulty),
    )

    positions = _positions_for_scene(h, w, count, scene, ctx.draw_rng("positions"))
    colors = _colors_for_scene(count, scene, ctx.draw_rng("colors"))
    grid = full_grid(h, w, 0)
    for (r, c), color in zip(positions, colors):
        if grid[r][c] != 0:
            raise RuntimeError("constructive seed placement overlap")
        grid[r][c] = color

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise RuntimeError(f"generated invalid grid: {errors}")
    return grid
