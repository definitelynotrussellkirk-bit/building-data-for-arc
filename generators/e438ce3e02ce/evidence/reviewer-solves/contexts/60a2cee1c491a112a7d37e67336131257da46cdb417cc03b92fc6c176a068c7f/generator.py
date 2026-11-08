"""Generator for ARC task ``e438ce3e02ce`` (Nearest-Seed Partition).

The input is a zero-filled rectangle containing three to five singleton seed
cells in pairwise-distinct colors other than 0 and 8.  The selected Racket rule
fills every zero with the color of its uniquely Manhattan-nearest seed; cells
with two or more equally nearest seeds become cyan (8), and seeds stay fixed.

Normal draws follow an eight-slot A/B/C/D teaching schedule.  Every cyclic
four-example window contains a three-way tie plus a 3-seed metric discriminator,
a 4-seed metric discriminator, a 3-seed Manhattan/Euclidean control, and a
5-seed metric discriminator.  Consequently each complete lesson refutes the
canonical shortcuts that ignore seeds after the first three or first four.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "e438ce3e02ce"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "866bf2f14b22"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.45

SUMMARY = (
    "A 9..10 by 9..12 zero-background grid contains 3..5 singleton seed "
    "cells in pairwise-distinct colors excluding 0 and 8. Fill each zero "
    "with the color of its uniquely nearest seed under Manhattan distance; "
    "if two or more seeds tie for minimum distance, paint the cell cyan (8). "
    "Preserve all seed cells."
)

INVARIANTS = [
    "there are exactly 3..5 singleton seeds in pairwise-distinct non-{0,8} colors",
    "every seed uniquely owns at least one blank cell",
    "every generated input has both uniquely-nearest blanks and at least one Manhattan tie blank",
    "every cyclic four-example schedule window contains 3-, 4-, and 5-seed cases",
    "every cyclic four-example schedule window refutes Euclidean distance and the first-three/first-four seed shortcuts",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Every declared axis is exact and recoverable from the returned grid.
AXES = {
    "grid_h": {"type": "int", "default": "eight-slot canonical-profile schedule", "valid": "9..10"},
    "grid_w": {"type": "int", "default": "eight-slot canonical-profile schedule", "valid": "9..12"},
    "n_seeds": {"type": "int", "default": "eight-slot 3/4/5-seed schedule", "valid": "3..5"},
}

# (height, width, seed count, pedagogical layout role)
#
# Roles repeat A/B/C/D.  Thus every cyclic window of four normal samples has:
# A: 3 seeds, a >=3-way Manhattan tie, and Manhattan/Euclidean disagreement.
# B: 4 seeds, metric disagreement, and a consequential fourth seed.
# C: 3 collinear seeds whose Manhattan and Euclidean output labels agree.
# D: 5 seeds, metric disagreement, and a consequential fifth seed.
_SCHEDULE = (
    (9, 9, 3, "triple_metric_diff"),
    (10, 10, 4, "metric_diff"),
    (9, 11, 3, "metric_same"),
    (10, 12, 5, "metric_diff"),
    (10, 10, 3, "triple_metric_diff"),
    (9, 12, 4, "metric_diff"),
    (10, 12, 3, "metric_same"),
    (9, 9, 5, "metric_diff"),
)
SCHEDULE_PROFILES = tuple(range(len(_SCHEDULE)))

_CANONICAL_PROFILES = {
    (9, 9, 3),
    (10, 10, 3),
    (9, 11, 3),
    (10, 12, 3),
}


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> int:
    """Return the deterministic curriculum slot for a sequential sample."""
    del seed, difficulty
    return int(sample_index) % len(_SCHEDULE)


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis/axes: " + ", ".join(unknown))


def _scheduled_defaults(sample_index: int) -> dict[str, int]:
    h, w, n_seeds, _role = _SCHEDULE[int(sample_index) % len(_SCHEDULE)]
    return {"grid_h": h, "grid_w": w, "n_seeds": n_seeds}


def _seed_cells(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    return [
        (r, c, int(value))
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]


def _nearest_hits(
    h: int,
    w: int,
    seed_pts: list[tuple[int, int]],
    *,
    metric: str = "manhattan",
) -> dict[tuple[int, int], tuple[int, ...]]:
    seed_set = set(seed_pts)
    result: dict[tuple[int, int], tuple[int, ...]] = {}
    for r in range(h):
        for c in range(w):
            if (r, c) in seed_set:
                continue
            distances: list[int] = []
            for sr, sc in seed_pts:
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


def _nearest_classes(
    h: int,
    w: int,
    seed_pts: list[tuple[int, int]],
    *,
    metric: str = "manhattan",
) -> tuple[list[tuple[int, int]], list[tuple[int, int]], dict[tuple[int, int], int]]:
    ties: list[tuple[int, int]] = []
    unique: list[tuple[int, int]] = []
    owners: dict[tuple[int, int], int] = {}
    for point, hits in _nearest_hits(h, w, seed_pts, metric=metric).items():
        if len(hits) == 1:
            unique.append(point)
            owners[point] = hits[0]
        else:
            ties.append(point)
    return ties, unique, owners


def _metric_labels(
    h: int,
    w: int,
    seed_pts: list[tuple[int, int]],
    metric: str,
) -> dict[tuple[int, int], int | None]:
    return {
        point: (hits[0] if len(hits) == 1 else None)
        for point, hits in _nearest_hits(h, w, seed_pts, metric=metric).items()
    }


def _metric_disagreement_count(h: int, w: int, seed_pts: list[tuple[int, int]]) -> int:
    manhattan = _metric_labels(h, w, seed_pts, "manhattan")
    euclidean = _metric_labels(h, w, seed_pts, "euclidean2")
    return sum(manhattan[point] != euclidean[point] for point in manhattan)


def _max_tie_arity(h: int, w: int, seed_pts: list[tuple[int, int]]) -> int:
    return max(
        (len(hits) for hits in _nearest_hits(h, w, seed_pts).values() if len(hits) >= 2),
        default=0,
    )


def _layout_is_teachable(
    h: int,
    w: int,
    seed_pts: list[tuple[int, int]],
    *,
    role: str | None,
    band: str,
) -> bool:
    if len(set(seed_pts)) != len(seed_pts):
        return False
    ties, unique, owners = _nearest_classes(h, w, seed_pts)
    if not ties or not unique:
        return False
    # If each seed owns a blank cell, deleting any one of them necessarily
    # changes the intended output somewhere; extra seeds cannot be decorative.
    if set(owners.values()) != set(range(len(seed_pts))):
        return False

    disagreement = _metric_disagreement_count(h, w, seed_pts)
    if role == "metric_same" and disagreement != 0:
        return False
    if role in {"metric_diff", "triple_metric_diff"}:
        minimum = {"easy": 1, "medium": 2, "hard": 3}[band]
        if disagreement < minimum:
            return False
    if role == "triple_metric_diff" and _max_tie_arity(h, w, seed_pts) < 3:
        return False
    return True


def _triple_tie_layout(h: int, w: int, rng, *, band: str) -> list[tuple[int, int]] | None:
    """Construct a translated/rotated 3-seed layout with a genuine 3-way tie."""
    orientations = (
        ((-2, 0), (1, -1), (1, 1)),
        ((0, 2), (-1, -1), (1, -1)),
        ((2, 0), (-1, 1), (-1, -1)),
        ((0, -2), (1, 1), (-1, 1)),
    )
    candidates: list[list[tuple[int, int]]] = []
    for offsets in orientations:
        for center_r in range(h):
            for center_c in range(w):
                points = [
                    (center_r + dr, center_c + dc) for dr, dc in offsets
                ]
                if all(0 <= r < h and 0 <= c < w for r, c in points):
                    candidates.append(points)
    rng.shuffle(candidates)
    for points in candidates:
        if _layout_is_teachable(
            h, w, points, role="triple_metric_diff", band=band
        ):
            return points
    return None


def _collinear_metric_same_layout(
    h: int, w: int, n_seeds: int, rng
) -> list[tuple[int, int]] | None:
    """Construct an even-spaced line where both metrics induce equal labels."""
    candidates: list[list[tuple[int, int]]] = []
    for step in (2, 4):
        span = step * (n_seeds - 1)
        if span < w:
            for row in range(h):
                for start in range(w - span):
                    candidates.append([(row, start + step * i) for i in range(n_seeds)])
        if span < h:
            for col in range(w):
                for start in range(h - span):
                    candidates.append([(start + step * i, col) for i in range(n_seeds)])
    rng.shuffle(candidates)
    for points in candidates:
        if _layout_is_teachable(
            h, w, points, role="metric_same", band="medium"
        ):
            return points
    return None


def _random_layout(
    h: int,
    w: int,
    n_seeds: int,
    rng,
    *,
    role: str | None,
    band: str,
) -> list[tuple[int, int]] | None:
    positions = [(r, c) for r in range(h) for c in range(w)]
    for _attempt in range(1200):
        points = rng.sample(positions, n_seeds)
        if any(
            abs(a[0] - b[0]) + abs(a[1] - b[1]) < 2
            for index, a in enumerate(points)
            for b in points[index + 1 :]
        ):
            continue
        if role in {"metric_diff", "triple_metric_diff"} and (
            len({r for r, _c in points}) == 1
            or len({c for _r, c in points}) == 1
        ):
            continue
        if _layout_is_teachable(h, w, points, role=role, band=band):
            return points
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one lawful input; the canonical Racket rule supplies outputs."""
    _validate_override_keys(overrides)
    band = _band(difficulty)
    slot = schedule_profile(seed, sample_index, difficulty)
    _scheduled_h, _scheduled_w, _scheduled_n, scheduled_role = _SCHEDULE[slot]

    # Route schedule defaults through GenCtx's ordinary override path so all
    # exact axes have keyed provenance. Explicit caller values take precedence.
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
    h = ctx.draw_int("grid_h", 9, 10)
    w = ctx.draw_int("grid_w", 9, 12)
    n_seeds = ctx.draw_int("n_seeds", 3, 5)

    # Pedagogical roles govern normal curriculum draws, not exact caller
    # overrides. An override combination remains constructively valid without
    # being silently forced into the scheduled metric relation.
    role = None if overrides else scheduled_role
    rng = ctx.draw_rng(f"layout_{band}")
    if role == "triple_metric_diff":
        seed_pts = _triple_tie_layout(h, w, rng, band=band)
    elif role == "metric_same":
        seed_pts = _collinear_metric_same_layout(h, w, n_seeds, rng)
    else:
        seed_pts = _random_layout(
            h, w, n_seeds, rng, role=role, band=band
        )
    if seed_pts is None:
        raise ValueError(
            "could not realize a teachable nearest-seed layout "
            f"(h={h}, w={w}, n_seeds={n_seeds}, role={role!r})"
        )

    colors = ctx.draw_distinct_colors(
        "seed_colors", n=n_seeds, exclude=(0, 8)
    )
    grid = full_grid(h, w, 0)
    for (r, c), color in zip(seed_pts, colors):
        grid[r][c] = int(color)
    return grid


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return {}, ["grid must be a non-empty list of rows"]
    h = len(grid)
    w = len(grid[0]) if grid[0] else 0
    if w == 0 or any(len(row) != w for row in grid):
        return {}, ["grid must be rectangular and non-empty"]
    if not (9 <= h <= 10):
        errors.append("grid height must be within the canonical 9..10 envelope")
    if not (9 <= w <= 12):
        errors.append("grid width must be within the canonical 9..12 envelope")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("all cells must be ARC integer colors 0..9")
        return {}, errors

    seeds = _seed_cells(grid)
    seed_colors = [value for _r, _c, value in seeds]
    if not (3 <= len(seeds) <= 5):
        errors.append("expected exactly 3..5 singleton seed cells")
    if any(value in (0, 8) for value in seed_colors):
        errors.append("seed colors must exclude background 0 and tie color 8")
    if len(seed_colors) != len(set(seed_colors)):
        errors.append("seed colors must be pairwise distinct and occur once each")

    seed_pts = [(r, c) for r, c, _value in seeds]
    tie_blanks: list[tuple[int, int]] = []
    unique_blanks: list[tuple[int, int]] = []
    owners: dict[tuple[int, int], int] = {}
    tie_arities: dict[tuple[int, int], int] = {}
    if len(seed_pts) >= 2:
        hits = _nearest_hits(h, w, seed_pts)
        tie_blanks = [point for point, nearest in hits.items() if len(nearest) >= 2]
        unique_blanks = [point for point, nearest in hits.items() if len(nearest) == 1]
        owners = {
            point: nearest[0]
            for point, nearest in hits.items()
            if len(nearest) == 1
        }
        tie_arities = {
            point: len(nearest)
            for point, nearest in hits.items()
            if len(nearest) >= 2
        }
        if not tie_blanks:
            errors.append("no blank Manhattan tie cell makes the cyan-8 branch observable")
        if not unique_blanks:
            errors.append("no blank uniquely-nearest cell makes seed-color filling observable")
        missing_owners = sorted(set(range(len(seed_pts))) - set(owners.values()))
        if missing_owners:
            errors.append(
                "every seed must uniquely own at least one blank cell; missing owner indices "
                + ",".join(str(index) for index in missing_owners)
            )

    info = {
        "grid_h": h,
        "grid_w": w,
        "n_seeds": len(seeds),
        "seeds": seeds,
        "seed_pts": seed_pts,
        "tie_blanks": tie_blanks,
        "unique_blanks": unique_blanks,
        "owners": owners,
        "tie_arities": tie_arities,
    }
    return info, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete generated input grammar."""
    del difficulty, meta
    _info, errors = _analyse(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Require canonical grammar and one of the four public input profiles."""
    info, errors = _analyse(grid)
    if errors:
        return errors
    profile = (info["grid_h"], info["grid_w"], info["n_seeds"])
    if profile not in _CANONICAL_PROFILES:
        return [f"profile {profile} is outside the four canonical profiles"]
    return []


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from a generated input."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("cannot observe overrides on invalid grid: " + "; ".join(errors))
    return {
        "grid_h": int(info["grid_h"]),
        "grid_w": int(info["grid_w"]),
        "n_seeds": int(info["n_seeds"]),
    }


def _fill_by_metric(
    grid: list[list[int]],
    *,
    metric: str,
    tie_value: int | None = 8,
    limit_seeds: int | None = None,
    multiway_lowest: bool = False,
) -> list[list[int]]:
    seeds = _seed_cells(grid)
    active = seeds if limit_seeds is None else seeds[:limit_seeds]
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            scored: list[tuple[int, int]] = []
            for sr, sc, color in active:
                dr, dc = abs(r - sr), abs(c - sc)
                distance = dr + dc if metric == "manhattan" else dr * dr + dc * dc
                scored.append((distance, color))
            best = min(distance for distance, _color in scored)
            hits = [color for distance, color in scored if distance == best]
            if len(hits) == 1:
                out[r][c] = hits[0]
            elif multiway_lowest and len(hits) >= 3:
                out[r][c] = min(hits)
            elif tie_value is not None:
                out[r][c] = tie_value
    return out


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror used for semantic auditing."""
    _info, errors = _analyse(grid)
    if errors:
        raise ValueError("invalid nearest-seed input: " + "; ".join(errors))
    return _fill_by_metric(grid, metric="manhattan", tie_value=8)


def _rival_euclidean(grid):
    return _fill_by_metric(grid, metric="euclidean2", tie_value=8)


def _rival_euclidean_three_only(grid):
    if len(_seed_cells(grid)) == 3:
        return _rival_euclidean(grid)
    return rule_mirror(grid)


def _rival_euclidean_four_only(grid):
    if len(_seed_cells(grid)) == 4:
        return _rival_euclidean(grid)
    return rule_mirror(grid)


def _rival_euclidean_five_only(grid):
    if len(_seed_cells(grid)) == 5:
        return _rival_euclidean(grid)
    return rule_mirror(grid)


def _rival_ignore_after_first_three(grid):
    if len(_seed_cells(grid)) <= 3:
        return rule_mirror(grid)
    return _fill_by_metric(
        grid, metric="manhattan", tie_value=8, limit_seeds=3
    )


def _rival_ignore_after_first_four(grid):
    if len(_seed_cells(grid)) <= 4:
        return rule_mirror(grid)
    return _fill_by_metric(
        grid, metric="manhattan", tie_value=8, limit_seeds=4
    )


def _rival_ties_stay_blank(grid):
    return _fill_by_metric(grid, metric="manhattan", tie_value=None)


def _rival_multiway_ties_choose_lowest(grid):
    return _fill_by_metric(
        grid, metric="manhattan", tie_value=8, multiway_lowest=True
    )


CANONICAL_SHORTCUTS: dict[str, Callable[[Any], list[list[int]]]] = {
    "ignore_after_first_three": _rival_ignore_after_first_three,
    "ignore_after_first_four": _rival_ignore_after_first_four,
}

SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    **CANONICAL_SHORTCUTS,
    "euclidean_distance": _rival_euclidean,
    "euclidean_only_for_three_seeds": _rival_euclidean_three_only,
    "euclidean_only_for_four_seeds": _rival_euclidean_four_only,
    "euclidean_only_for_five_seeds": _rival_euclidean_five_only,
    "ties_stay_blank": _rival_ties_stay_blank,
    "three_way_ties_choose_lowest": _rival_multiway_ties_choose_lowest,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _valid_info(grid) -> dict[str, Any] | None:
    info, errors = _analyse(grid)
    return None if errors else info


def _witness_tie_branch(grid) -> bool:
    info = _valid_info(grid)
    return info is not None and bool(info["tie_blanks"])


def _witness_multiway_tie(grid) -> bool:
    info = _valid_info(grid)
    return info is not None and max(info["tie_arities"].values(), default=0) >= 3


def _witness_metric_disagreement(seed_count: int):
    def witness(grid) -> bool:
        info = _valid_info(grid)
        return (
            info is not None
            and info["n_seeds"] == seed_count
            and _rival_euclidean(grid) != rule_mirror(grid)
        )

    return witness


def _witness_ignored_tail(limit: int):
    def witness(grid) -> bool:
        info = _valid_info(grid)
        if info is None or info["n_seeds"] <= limit:
            return False
        rival = (
            _rival_ignore_after_first_three
            if limit == 3
            else _rival_ignore_after_first_four
        )
        return rival(grid) != rule_mirror(grid)

    return witness


SEMANTIC_WITNESSES = {
    "tie_boundary_requires_cyan_8": _witness_tie_branch,
    "three_way_tie_uses_same_cyan_marker": _witness_multiway_tie,
    "three_seed_manhattan_not_euclidean": _witness_metric_disagreement(3),
    "four_seed_manhattan_not_euclidean": _witness_metric_disagreement(4),
    "five_seed_manhattan_not_euclidean": _witness_metric_disagreement(5),
    "fourth_seed_controls_nontrivial_region": _witness_ignored_tail(3),
    "fifth_seed_controls_nontrivial_region": _witness_ignored_tail(4),
}

WITNESS_RIVALS = {
    "tie_boundary_requires_cyan_8": ["ties_stay_blank"],
    "three_way_tie_uses_same_cyan_marker": ["three_way_ties_choose_lowest"],
    "three_seed_manhattan_not_euclidean": [
        "euclidean_distance",
        "euclidean_only_for_three_seeds",
    ],
    "four_seed_manhattan_not_euclidean": [
        "euclidean_distance",
        "euclidean_only_for_four_seeds",
    ],
    "five_seed_manhattan_not_euclidean": [
        "euclidean_distance",
        "euclidean_only_for_five_seeds",
    ],
    "fourth_seed_controls_nontrivial_region": ["ignore_after_first_three"],
    "fifth_seed_controls_nontrivial_region": ["ignore_after_first_four"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require four demonstrations that refute every declared competitor."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    refuted = {name: False for name in LESSON_COMPETITORS}
    profiles: set[tuple[int, int, int]] = set()
    seen_counts: set[int] = set()
    metric_diff_counts: set[int] = set()
    seen_multiway_tie = False

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or not {"input", "output"} <= set(pair):
            reasons.append(f"demo {index} must contain input and output")
            continue
        info, errors = _analyse(pair["input"])
        if errors:
            reasons.append(f"demo {index} input invalid: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(
                f"demo {index} output is not the exact Manhattan nearest-seed fill"
            )
            continue
        profile = (info["grid_h"], info["grid_w"], info["n_seeds"])
        profiles.add(profile)
        seen_counts.add(info["n_seeds"])
        if _rival_euclidean(pair["input"]) != expected:
            metric_diff_counts.add(info["n_seeds"])
        seen_multiway_tie = seen_multiway_tie or (
            max(info["tie_arities"].values(), default=0) >= 3
        )
        for name, rival in LESSON_COMPETITORS.items():
            refuted[name] = refuted[name] or rival(pair["input"]) != expected

    if len(profiles) < 4:
        reasons.append("demonstrations must span four distinct size/seed-count profiles")
    if not {3, 4, 5} <= seen_counts:
        reasons.append("demonstrations must include 3-, 4-, and 5-seed inputs")
    if not {3, 4, 5} <= metric_diff_counts:
        reasons.append(
            "demonstrations need Manhattan-vs-Euclidean discriminators at 3, 4, and 5 seeds"
        )
    if not seen_multiway_tie:
        reasons.append("demonstrations need a tie involving at least three nearest seeds")
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
