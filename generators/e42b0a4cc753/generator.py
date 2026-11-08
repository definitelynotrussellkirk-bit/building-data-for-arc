"""Teaching generator for ARC task ``e42b0a4cc753``.

A complete color-8 border encloses two to five pairwise-distinct colored
singleton seeds.  Every blank interior cell takes the color of its nearest seed
under Manhattan distance.  Equal-distance ties are resolved by seed position in
row-major reading order.

Normal draws follow a three-slot teaching schedule.  Every cyclic three-example
window contains: (A) a tie where reading order disagrees with lower-color order,
(B) a consequential third seed, and (C) a Manhattan/Euclidean discriminator.
Exact caller overrides remain valid but intentionally bypass those lesson roles.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "e42b0a4cc753"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "f23844d6433c"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.95

SUMMARY = (
    "A 6..10 by 7..12 grid has a complete color-8 outer border and 2..5 "
    "pairwise-distinct colored singleton seeds in its otherwise-zero interior. "
    "Fill each blank interior cell with the color of its Manhattan-nearest "
    "seed. On equal distances, choose the seed appearing first in row-major "
    "reading order. Preserve the border and all seed cells."
)

INVARIANTS = [
    "the complete outer border is color 8 and no interior cell is color 8",
    "there are exactly 2..5 pairwise-distinct nonzero seed colors",
    "every seed uniquely owns at least one initially blank interior cell",
    "ties are resolved by seed position in row-major order, not by seed color",
    "every cyclic three-example lesson refutes the declared shortcut rivals",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, int]] = []

# Every public axis is exact and recoverable from returned pixels.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "three-slot canonical-profile schedule",
        "valid": "6..10",
    },
    "grid_w": {
        "type": "int",
        "default": "three-slot canonical-profile schedule",
        "valid": "7..12",
    },
    "n_seeds": {
        "type": "int",
        "default": "three-slot 2/3/2-seed schedule",
        "valid": "2..5",
    },
}

# (height, width, seed count, pedagogical role).  These dimensions reproduce
# all three canonical input profiles while the middle slot adds the missing
# third-seed evidence.
_SCHEDULE = (
    (6, 7, 2, "tie_order"),
    (6, 8, 3, "extra_seed"),
    (7, 9, 2, "metric_diff"),
)
SCHEDULE_PROFILES = tuple(slot[3] for slot in _SCHEDULE)

Grid = list[list[int]]
Point = tuple[int, int]
Seed = tuple[int, int, int]


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the role in the deterministic three-example curriculum."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis/axes: " + ", ".join(unknown))
    bounds = {"grid_h": (6, 10), "grid_w": (7, 12), "n_seeds": (2, 5)}
    for name, value in overrides.items():
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside supported range {lo}..{hi}")


def _scheduled_defaults(sample_index: int) -> dict[str, int]:
    h, w, n_seeds, _role = _SCHEDULE[int(sample_index) % len(_SCHEDULE)]
    return {"grid_h": h, "grid_w": w, "n_seeds": n_seeds}


def _interior_points(h: int, w: int) -> list[Point]:
    return [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]


def _nearest_indices_for_points(
    h: int,
    w: int,
    seed_points: Sequence[Point],
    *,
    metric: str = "manhattan",
) -> dict[Point, tuple[int, ...]]:
    seed_set = set(seed_points)
    result: dict[Point, tuple[int, ...]] = {}
    for r, c in _interior_points(h, w):
        if (r, c) in seed_set:
            continue
        distances: list[int] = []
        for sr, sc in seed_points:
            dr, dc = abs(r - sr), abs(c - sc)
            if metric == "manhattan":
                distances.append(dr + dc)
            elif metric == "euclidean2":
                distances.append(dr * dr + dc * dc)
            else:  # pragma: no cover - internal misuse guard
                raise ValueError(f"unknown metric {metric!r}")
        best = min(distances)
        result[(r, c)] = tuple(
            index for index, distance in enumerate(distances) if distance == best
        )
    return result


def _every_seed_owns_blank(h: int, w: int, seed_points: Sequence[Point]) -> bool:
    owners = {
        nearest[0]
        for nearest in _nearest_indices_for_points(h, w, seed_points).values()
        if len(nearest) == 1
    }
    return owners == set(range(len(seed_points)))


def _has_manhattan_tie(h: int, w: int, seed_points: Sequence[Point]) -> bool:
    return any(
        len(nearest) >= 2
        for nearest in _nearest_indices_for_points(h, w, seed_points).values()
    )


def _metric_outputs_differ(h: int, w: int, seed_points: Sequence[Point]) -> bool:
    manhattan = _nearest_indices_for_points(h, w, seed_points, metric="manhattan")
    euclidean = _nearest_indices_for_points(h, w, seed_points, metric="euclidean2")
    return any(manhattan[point][0] != euclidean[point][0] for point in manhattan)


@lru_cache(maxsize=12)
def _role_layouts(
    h: int, w: int, n_seeds: int, role: str
) -> tuple[tuple[Point, ...], ...]:
    """Enumerate the small scheduled geometry spaces once per process."""
    layouts: list[tuple[Point, ...]] = []
    for points in combinations(_interior_points(h, w), n_seeds):
        if not _every_seed_owns_blank(h, w, points):
            continue
        if role == "tie_order" and not _has_manhattan_tie(h, w, points):
            continue
        if role == "metric_diff" and not _metric_outputs_differ(h, w, points):
            continue
        layouts.append(points)
    return tuple(layouts)


def _generic_layout(h: int, w: int, n_seeds: int, rng) -> list[Point]:
    """Find a broad lawful layout, with a constructive fallback."""
    interior = _interior_points(h, w)
    for _attempt in range(160):
        points = sorted(rng.sample(interior, n_seeds))
        if _every_seed_owns_blank(h, w, points):
            return points

    # The four interior corners plus center work for every advertised size and
    # seed count.  This is a deterministic safety net, not the normal path.
    anchors = [
        (1, 1),
        (1, w - 2),
        (h - 2, 1),
        (h - 2, w - 2),
        ((h - 1) // 2, (w - 1) // 2),
    ]
    points = sorted(anchors[:n_seeds])
    if not _every_seed_owns_blank(h, w, points):  # pragma: no cover - invariant guard
        raise RuntimeError("constructive seed-layout fallback lost an owner")
    return points


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one lawful input; the canonical Racket rule supplies outputs."""
    _validate_overrides(overrides)
    band = _band(difficulty)
    slot = int(sample_index) % len(_SCHEDULE)
    _scheduled_h, _scheduled_w, _scheduled_n, scheduled_role = _SCHEDULE[slot]

    # Schedule defaults pass through GenCtx's regular exact-override path.
    # Explicit caller values take precedence and disable the teaching role.
    effective = _scheduled_defaults(sample_index)
    effective.update(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    h = ctx.draw_int("grid_h", 6, 10)
    w = ctx.draw_int("grid_w", 7, 12)
    n_seeds = ctx.draw_int("n_seeds", 2, 5)

    role = None if overrides else scheduled_role
    rng = ctx.draw_rng(f"layout_{band}")
    if role is None:
        seed_points = _generic_layout(h, w, n_seeds, rng)
    else:
        candidates = _role_layouts(h, w, n_seeds, role)
        if not candidates:
            raise RuntimeError(
                "no teachable layout for "
                f"h={h}, w={w}, n_seeds={n_seeds}, role={role!r}"
            )
        seed_points = list(rng.choice(candidates))

    colors = list(
        ctx.draw_distinct_colors("seed_colors", n=n_seeds, exclude=(0, 8))
    )
    if role == "tie_order":
        # Seed points are row-major sorted.  Descending colors force every
        # two-seed tie to distinguish reading order from lower-color order.
        colors.sort(reverse=True)

    grid = full_grid(h, w, 0)
    for c in range(w):
        grid[0][c] = 8
        grid[h - 1][c] = 8
    for r in range(h):
        grid[r][0] = 8
        grid[r][w - 1] = 8
    for (r, c), color in zip(seed_points, colors):
        grid[r][c] = int(color)
    return grid


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    """Validate the complete chamber-and-seed input grammar."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return {}, ["grid must be a non-empty rectangular sequence"]
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return {}, ["every grid row must be a sequence"]
    width = len(grid[0]) if grid[0] else 0
    if width == 0 or any(len(row) != width for row in grid):
        return {}, ["grid must be rectangular and non-empty"]

    height = len(grid)
    errors: list[str] = []
    if not 6 <= height <= 10:
        errors.append("grid height must be within the supported 6..10 envelope")
    if not 7 <= width <= 12:
        errors.append("grid width must be within the supported 7..12 envelope")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("all cells must be ARC integer colors 0..9")
        return {}, errors

    border = [
        grid[r][c]
        for r in range(height)
        for c in range(width)
        if r in (0, height - 1) or c in (0, width - 1)
    ]
    if any(value != 8 for value in border):
        errors.append("the complete outer border must be color 8")

    interior = [
        (r, c, int(grid[r][c]))
        for r in range(1, height - 1)
        for c in range(1, width - 1)
    ]
    if any(value == 8 for _r, _c, value in interior):
        errors.append("color 8 is reserved for the chamber border")
    seeds = [(r, c, value) for r, c, value in interior if value != 0]
    colors = [value for _r, _c, value in seeds]
    if not 2 <= len(seeds) <= 5:
        errors.append("expected exactly 2..5 interior seed cells")
    if len(colors) != len(set(colors)):
        errors.append("interior seed colors must be pairwise distinct")
    if not any(value == 0 for _r, _c, value in interior):
        errors.append("the chamber must retain at least one blank cell to fill")

    seed_points = [(r, c) for r, c, _value in seeds]
    nearest: dict[Point, tuple[int, ...]] = {}
    owners: set[int] = set()
    if len(seed_points) >= 2:
        nearest = _nearest_indices_for_points(height, width, seed_points)
        owners = {
            hits[0] for hits in nearest.values() if len(hits) == 1
        }
        missing = sorted(set(range(len(seed_points))) - owners)
        if missing:
            errors.append(
                "every seed must uniquely own at least one blank cell; missing indices "
                + ",".join(str(index) for index in missing)
            )

    return {
        "grid_h": height,
        "grid_w": width,
        "n_seeds": len(seeds),
        "seeds": seeds,
        "seed_points": seed_points,
        "nearest": nearest,
        "owners": owners,
    }, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return structural violations for one generated or canonical input."""
    del difficulty, meta
    _info, errors = _analyse(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The supported sampler manifold is the selected rule's lawful domain."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from returned pixels."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("cannot observe overrides on invalid grid: " + "; ".join(errors))
    return {
        "grid_h": int(info["grid_h"]),
        "grid_w": int(info["grid_w"]),
        "n_seeds": int(info["n_seeds"]),
    }


def _seed_cells(grid: Sequence[Sequence[int]]) -> list[Seed]:
    return [
        (r, c, int(value))
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 8)
    ]


def _fill_by_metric(
    grid: Sequence[Sequence[int]],
    *,
    metric: str,
    tie: str = "reading",
    limit_seeds: int | None = None,
) -> Grid:
    seeds = _seed_cells(grid)
    active = seeds if limit_seeds is None else seeds[:limit_seeds]
    out = [list(row) for row in grid]
    if not active:
        return out
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            if grid[r][c] != 0:
                continue
            scored: list[tuple[int, Seed]] = []
            for seed in active:
                sr, sc, _color = seed
                dr, dc = abs(r - sr), abs(c - sc)
                distance = dr + dc if metric == "manhattan" else dr * dr + dc * dc
                scored.append((distance, seed))
            best = min(distance for distance, _seed in scored)
            hits = [seed for distance, seed in scored if distance == best]
            if tie == "reading":
                chosen = min(hits, key=lambda item: (item[0], item[1]))
            elif tie == "lower_color":
                chosen = min(hits, key=lambda item: item[2])
            else:  # pragma: no cover - internal misuse guard
                raise ValueError(f"unknown tie rule {tie!r}")
            out[r][c] = chosen[2]
    return out


def rule_mirror(grid: Sequence[Sequence[int]]) -> Grid:
    """Independent Python mirror used only for semantic auditing."""
    _info, errors = _analyse(grid)
    if errors:
        raise ValueError("invalid nearest-seed input: " + "; ".join(errors))
    return _fill_by_metric(grid, metric="manhattan", tie="reading")


def _rival_lower_color_tie(grid: Sequence[Sequence[int]]) -> Grid:
    return _fill_by_metric(grid, metric="manhattan", tie="lower_color")


def _rival_ignore_after_first_two(grid: Sequence[Sequence[int]]) -> Grid:
    return _fill_by_metric(
        grid, metric="manhattan", tie="reading", limit_seeds=2
    )


def _rival_euclidean(grid: Sequence[Sequence[int]]) -> Grid:
    return _fill_by_metric(grid, metric="euclidean2", tie="reading")


CANONICAL_SHORTCUTS: dict[str, Callable[[Any], Grid]] = {
    "lower_color_tie": _rival_lower_color_tie,
    "ignore_after_first_two": _rival_ignore_after_first_two,
}

SEMANTIC_RIVALS: dict[str, Callable[[Any], Grid]] = {
    **CANONICAL_SHORTCUTS,
    "euclidean_distance": _rival_euclidean,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _valid_witness(grid: Any, rival: Callable[[Any], Grid]) -> bool:
    return self_check(grid) == [] and rival(grid) != rule_mirror(grid)


def _witness_reading_order(grid: Any) -> bool:
    return _valid_witness(grid, _rival_lower_color_tie)


def _witness_third_seed(grid: Any) -> bool:
    return len(_seed_cells(grid)) >= 3 and _valid_witness(
        grid, _rival_ignore_after_first_two
    )


def _witness_manhattan(grid: Any) -> bool:
    return _valid_witness(grid, _rival_euclidean)


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "reading_order_over_lower_color": _witness_reading_order,
    "third_seed_controls_blank": _witness_third_seed,
    "manhattan_over_euclidean": _witness_manhattan,
}

WITNESS_RIVALS = {
    "reading_order_over_lower_color": ["lower_color_tie"],
    "third_seed_controls_blank": ["ignore_after_first_two"],
    "manhattan_over_euclidean": ["euclidean_distance"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require three demonstrations that collectively refute all competitors."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    refuted = {name: False for name in LESSON_COMPETITORS}
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or not {"input", "output"} <= set(pair):
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input invalid: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(
                f"demo {index} output is not the exact Manhattan/read-order fill"
            )
            continue
        for name, rival in LESSON_COMPETITORS.items():
            refuted[name] = refuted[name] or rival(pair["input"]) != expected

    for name, was_refuted in refuted.items():
        if not was_refuted:
            reasons.append(f"demonstrations do not refute rival {name}")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    else:
        query_errors = self_check(query["input"])
        if query_errors:
            reasons.append(f"query input invalid: {query_errors[0]}")
    return reasons
