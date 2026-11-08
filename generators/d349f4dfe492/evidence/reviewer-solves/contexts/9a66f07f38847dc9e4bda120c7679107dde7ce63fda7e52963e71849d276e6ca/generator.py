"""Generator for d349f4dfe492 — per-seed Manhattan distance-two shells.

Every nonzero input cell is an independent colored seed.  In row-major seed
order, the selected rule preserves the input and paints each still-empty cell
at Manhattan distance exactly two from the seed with that seed's color.

Generated seeds are deliberately separated by L1 distance at least five.  This
keeps their closed radius-two influence zones disjoint, matching the task's
teaching grammar while still including clipped border shells, repeated seed
colors, and lessons with more than the two seeds shown canonically.
"""
from __future__ import annotations

from collections.abc import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d349f4dfe492"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "e47d7c8767c3"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A zero-background grid contains 1-5 separated colored singleton seeds. "
    "Preserve every seed and paint each original empty cell at Manhattan "
    "distance exactly two with that seed's color. Seeds are processed "
    "row-major and only still-empty output cells are painted. The ordinary "
    "teaching grammar keeps closed radius-two influence zones disjoint."
)

INVARIANTS = [
    "background is 0 and every nonzero cell is a singleton seed",
    "ordinary inputs contain 1-5 seeds using ARC colors 1..9",
    "a one-seed teaching input places that seed on the border to expose clipping",
    "every pair of seeds has Manhattan distance at least five",
    "the input grid is preserved in the output",
    "only original empty cells at exact Manhattan distance two are painted",
]

DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "three-profile schedule anchored to canonical dimensions",
        "valid": "7..18",
        "doc": "Exact input height; every value is override-safe in every band.",
    },
    "grid_w": {
        "type": "int",
        "default": "three-profile schedule anchored to canonical dimensions",
        "valid": "7..18",
        "doc": "Exact input width; every value is override-safe in every band.",
    },
    "n_seeds": {
        "type": "int",
        "default": "scheduled 2..5",
        "valid": "1..5",
        "doc": "Exact number of separated nonzero singleton seeds.",
    },
}

# All Cartesian combinations are feasible.  On the minimum 7x7 grid, the four
# corners plus center are pairwise at L1 distance >= 6.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

Grid = list[list[int]]
Seed = tuple[int, int, int]
Cell = tuple[int, int]

SCHEDULE_PROFILES = (
    "canonical_anchor",
    "clipped_border",
    "repeated_colors",
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Cycle profiles so every consecutive three-example window sees all."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _profile_defaults(sample_index: int, difficulty) -> tuple[int, int, int]:
    profile = schedule_profile(0, sample_index, difficulty)
    if profile == "canonical_anchor":
        return {
            "easy": (7, 7, 2),
            "medium": (8, 8, 2),
            "hard": (8, 9, 2),
        }.get(difficulty, (7, 7, 2))
    if profile == "clipped_border":
        return {
            "easy": (8, 8, 2),
            "medium": (9, 10, 3),
            "hard": (12, 12, 4),
        }.get(difficulty, (9, 9, 3))
    return {
        "easy": (9, 9, 3),
        "medium": (12, 13, 4),
        "hard": (16, 17, 5),
    }.get(difficulty, (11, 12, 4))


def _draw_axis(ctx, overrides, name: str, default: int, lo: int, hi: int) -> int:
    """Record exact axes in GenCtx while allowing the full override domain."""
    if name in overrides:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _seed_cells(grid: Grid) -> list[Seed]:
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the separated singleton-seed rule domain."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"]

    errors: list[str] = []
    width = len(grid[0])
    structurally_invalid = False
    for r, row in enumerate(grid):
        if not isinstance(row, list) or len(row) != width:
            errors.append(f"row {r} has inconsistent width")
            structurally_invalid = True
            continue
        for c, value in enumerate(row):
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append(f"cell ({r},{c}) is not an ARC color 0..9: {value!r}")
                structurally_invalid = True
                if len(errors) >= 6:
                    return errors
    if structurally_invalid:
        return errors

    seeds = _seed_cells(grid)
    if not 1 <= len(seeds) <= 5:
        errors.append(f"expected 1-5 nonzero singleton seeds, found {len(seeds)}")
        return errors

    if len(seeds) == 1:
        r, c, _color = seeds[0]
        h = len(grid)
        if r not in (0, h - 1) and c not in (0, width - 1):
            errors.append(
                "single-seed teaching inputs must place the seed on the border "
                "to expose clipped-shell behavior"
            )

    for i, (r, c, _color) in enumerate(seeds):
        for rr, cc, _other_color in seeds[i + 1 :]:
            distance = abs(r - rr) + abs(c - cc)
            if distance < 5:
                errors.append(
                    "radius-two influence zones overlap for seeds at "
                    f"({r},{c}) and ({rr},{cc}); L1 distance is {distance}, need >=5"
                )
    return errors


def _paint_selected(
    grid: Grid,
    seeds: list[Seed],
    predicate: Callable[[int, int], bool],
) -> Grid:
    """Apply a row-major seed painter with the selected distance predicate."""
    source = [list(row) for row in grid]
    out = [row[:] for row in source]
    if not source or not source[0]:
        return out
    h, w = len(source), len(source[0])
    for r, c, color in seeds:
        for rr in range(h):
            for cc in range(w):
                if (
                    source[rr][cc] == 0
                    and out[rr][cc] == 0
                    and predicate(abs(rr - r), abs(cc - c))
                ):
                    out[rr][cc] = color
    return out


def rule_mirror(grid: Grid) -> Grid:
    """Pure Python mirror of the selected Racket authority."""
    return _paint_selected(
        grid,
        _seed_cells(grid),
        lambda dr, dc: dr + dc == 2,
    )


def strict_canonical_like(grid, *, difficulty=None, meta=None) -> list[str]:
    """Bounded teaching grammar shared by canonical inputs and ordinary draws."""
    reasons = list(self_check(grid, difficulty=difficulty, meta=meta))
    if reasons:
        return reasons
    h, w = len(grid), len(grid[0])
    if not (6 <= h <= 18 and 6 <= w <= 18):
        reasons.append(f"teaching dimensions must be within 6..18, found {h}x{w}")
    if rule_mirror(grid) == grid:
        reasons.append("distance-two transformation must change at least one cell")
    return reasons


def observe_overrides(grid: Grid) -> dict[str, int]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe axes from invalid grid: " + "; ".join(errors))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_seeds": len(_seed_cells(grid)),
    }


def _filled_radius_two(grid: Grid) -> Grid:
    return _paint_selected(
        grid,
        _seed_cells(grid),
        lambda dr, dc: 0 < dr + dc <= 2,
    )


def _chebyshev_radius_two(grid: Grid) -> Grid:
    return _paint_selected(
        grid,
        _seed_cells(grid),
        lambda dr, dc: max(dr, dc) == 2,
    )


def _axial_only_radius_two(grid: Grid) -> Grid:
    return _paint_selected(
        grid,
        _seed_cells(grid),
        lambda dr, dc: dr + dc == 2 and (dr == 0 or dc == 0),
    )


def _skip_border_seeds(grid: Grid) -> Grid:
    h = len(grid)
    w = len(grid[0]) if h else 0
    seeds = [
        seed
        for seed in _seed_cells(grid)
        if seed[0] not in (0, h - 1) and seed[1] not in (0, w - 1)
    ]
    return _paint_selected(grid, seeds, lambda dr, dc: dr + dc == 2)


def _first_two_seeds_only(grid: Grid) -> Grid:
    return _paint_selected(
        grid,
        _seed_cells(grid)[:2],
        lambda dr, dc: dr + dc == 2,
    )


def _deduplicate_seed_colors(grid: Grid) -> Grid:
    chosen: list[Seed] = []
    seen: set[int] = set()
    for seed in _seed_cells(grid):
        color = seed[2]
        if color not in seen:
            seen.add(color)
            chosen.append(seed)
    return _paint_selected(grid, chosen, lambda dr, dc: dr + dc == 2)


def _ignore_color_one(grid: Grid) -> Grid:
    seeds = [seed for seed in _seed_cells(grid) if seed[2] != 1]
    return _paint_selected(grid, seeds, lambda dr, dc: dr + dc == 2)


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "filled_radius_two": _filled_radius_two,
    "chebyshev_radius_two": _chebyshev_radius_two,
    "axial_only_radius_two": _axial_only_radius_two,
    "skip_border_seeds": _skip_border_seeds,
    "first_two_seeds_only": _first_two_seeds_only,
    "deduplicate_seed_colors": _deduplicate_seed_colors,
    "ignore_color_one": _ignore_color_one,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "skip_border_seeds",
        "first_two_seeds_only",
        "deduplicate_seed_colors",
        "ignore_color_one",
    )
}


def _valid_and_diff(grid: Grid, rival: Callable[[Grid], Grid]) -> bool:
    return not strict_canonical_like(grid) and rival(grid) != rule_mirror(grid)


def _witness_for(rival: Callable[[Grid], Grid]) -> Callable[[Grid], bool]:
    return lambda grid: _valid_and_diff(grid, rival)


SEMANTIC_WITNESSES = {
    name: _witness_for(rival)
    for name, rival in SEMANTIC_RIVALS.items()
}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos, query) -> list[str]:
    """Require each teaching window to falsify every declared rival rule."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]

    reasons: list[str] = []
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    else:
        query_errors = strict_canonical_like(query["input"])
        if query_errors:
            reasons.append(f"query input is outside teaching grammar: {query_errors[0]}")

    refuted = {name: False for name in SEMANTIC_RIVALS}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = strict_canonical_like(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is outside teaching grammar: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output is not the exact distance-two shell")
            continue
        for name, rival in SEMANTIC_RIVALS.items():
            if rival(demo["input"]) != expected:
                refuted[name] = True

    for name, killed in refuted.items():
        if not killed:
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons


def _positions_are_separated(cells: list[Cell]) -> bool:
    return all(
        abs(r - rr) + abs(c - cc) >= 5
        for i, (r, c) in enumerate(cells)
        for rr, cc in cells[i + 1 :]
    )


def _place_positions(h: int, w: int, n_seeds: int, profile: str, rng) -> list[Cell]:
    """Choose a guaranteed-valid profile layout for every exact override."""
    corners = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]
    rng.shuffle(corners)
    center = (h // 2, w // 2)

    # A singleton is intentionally a clipping lesson; this also keeps the
    # validator's one-seed grammar narrow and observable.
    if n_seeds == 1:
        return [corners[0]]

    if profile == "canonical_anchor" and n_seeds == 2:
        canonical_pair = [(2, 2), (h - 3, w - 2)]
        if _positions_are_separated(canonical_pair):
            return canonical_pair

    if profile == "repeated_colors":
        # Default repeated-colour profiles are at least 9x9, where these five
        # non-border anchors are pairwise separated and include a full-shell
        # center.  Small exact overrides fall back to the universal anchors.
        inset = [
            center,
            (1, 1),
            (1, w - 2),
            (h - 2, w - 2),
            (h - 2, 1),
        ][:n_seeds]
        if len(set(inset)) == n_seeds and _positions_are_separated(inset):
            return inset

    universal = [*corners, center] if profile == "clipped_border" else [center, *corners]
    chosen = universal[:n_seeds]
    if len(set(chosen)) != n_seeds or not _positions_are_separated(chosen):
        raise ValueError(f"{h}x{w} cannot realize {n_seeds} separated seed anchors")
    return chosen

def _colors_for_profile(profile: str, n_seeds: int, rng) -> list[int]:
    palette = [2, 3, 4, 5, 6, 7, 9]
    rng.shuffle(palette)
    if profile == "canonical_anchor":
        return [1, *palette][:n_seeds]
    if profile == "repeated_colors":
        repeated = palette[0]
        if n_seeds == 1:
            return [repeated]
        rest = [color for color in palette[1:] if color != repeated]
        return [repeated, repeated, *rest][:n_seeds]
    return palette[:n_seeds]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_h, default_w, default_n = _profile_defaults(sample_index, difficulty)
    h = _draw_axis(ctx, overrides, "grid_h", default_h, 7, 18)
    w = _draw_axis(ctx, overrides, "grid_w", default_w, 7, 18)
    n_seeds = _draw_axis(ctx, overrides, "n_seeds", default_n, 1, 5)

    profile = schedule_profile(seed, sample_index, difficulty)
    rng = ctx.draw_rng("layout")
    positions = _place_positions(h, w, n_seeds, profile, rng)
    colors = _colors_for_profile(profile, n_seeds, rng)

    grid = full_grid(h, w, 0)
    for (r, c), color in zip(positions, colors):
        grid[r][c] = color

    errors = strict_canonical_like(grid)
    if errors:
        raise RuntimeError(f"internal construction violated teaching grammar: {errors}")
    observed = observe_overrides(grid)
    expected = {"grid_h": h, "grid_w": w, "n_seeds": n_seeds}
    if observed != expected:
        raise RuntimeError(f"observable axis mismatch: expected {expected}, observed {observed}")
    return grid
