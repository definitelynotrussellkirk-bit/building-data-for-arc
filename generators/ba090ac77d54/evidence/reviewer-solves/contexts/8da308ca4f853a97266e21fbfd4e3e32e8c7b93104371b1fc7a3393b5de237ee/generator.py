"""Generator for ARC task ``ba090ac77d54`` (Voronoi Fill Inside the Frame).

The input is a zero-filled rectangle with a one-cell gray (5) frame and three
or four distinct colored seed cells in the interior.  The selected Racket rule
fills each interior zero with the color of its uniquely nearest seed under
Manhattan distance; cells tied for minimum distance become cyan (8).  Seeds and
the gray frame are preserved.

Normal draws follow an eight-slot teaching schedule.  Every four consecutive
slots contain all four decisive controls: three-seed/Euclidean-equivalent,
four-seed/Euclidean-equivalent, three-seed/Manhattan-vs-Euclidean disagreement,
and four-seed/Manhattan-vs-Euclidean disagreement.  The first equivalent pair
is collinear while the second is deliberately non-collinear, so metric controls
do not encode equivalence as a one-line geometry shortcut.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "ba090ac77d54"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "b8d93c3098e2"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.95

SUMMARY = (
    "A rectangular grid has a closed one-cell gray (5) frame, zero interior "
    "background, and three or four distinct non-{0,5,8} seed colors. Fill "
    "each interior zero with the color of its uniquely nearest seed by "
    "Manhattan distance; if two or more seeds tie for the minimum distance, "
    "paint cyan (8). Preserve the seed cells and the gray frame."
)

INVARIANTS = [
    "the complete outer boundary is color 5 and no interior cell is color 5",
    "there are exactly 3 or 4 interior seed cells in pairwise-distinct colors excluding 0, 5, and 8",
    "every seed owns at least one blank uniquely-nearest interior cell",
    "every generated input has at least one blank Manhattan tie cell, so the cyan-8 branch is observable",
    "every four consecutive scheduled samples include 3- and 4-seed cases plus Manhattan-vs-Euclidean disagreements at both seed counts",
    "metric-equivalent controls include both collinear and non-collinear seed layouts",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# These are the only caller-facing exact controls.  All three can be recovered
# from the returned input, so override verification is semantic rather than
# merely checking that a keyword was accepted.
AXES = {
    "grid_h": {"type": "int", "default": "eight-slot canonical-profile schedule", "valid": "9..11"},
    "grid_w": {"type": "int", "default": "eight-slot canonical-profile schedule", "valid": "9..12"},
    "n_seeds": {"type": "int", "default": "eight-slot 3/4-seed schedule", "valid": "3..4"},
}

# (height, width, seed count, metric relation)
#
# Roles repeat A/B/C/D.  Therefore every cyclic window of four samples contains
# both seed counts and one Manhattan-vs-Euclidean discriminator at each count.
# The five public (h, w, palette-size) profiles are all represented; 11x11/4
# seeds is repeated because it is the sole public four-seed profile.
_SCHEDULE = (
    (9, 9, 3, "metric_same"),
    (11, 11, 4, "metric_same"),
    (10, 10, 3, "metric_diff"),
    (11, 11, 4, "metric_diff"),
    (10, 11, 3, "metric_same"),
    (11, 11, 4, "metric_same"),
    (9, 12, 3, "metric_diff"),
    (11, 11, 4, "metric_diff"),
)
SCHEDULE_PROFILES = tuple(range(len(_SCHEDULE)))
_NONCOLLINEAR_METRIC_SAME_SLOTS = frozenset({4, 5})

_CANONICAL_PROFILES = {
    (9, 9, 3),
    (10, 11, 3),
    (11, 11, 4),
    (9, 12, 3),
    (10, 10, 3),
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
    h, w, n_seeds, _metric_class = _SCHEDULE[int(sample_index) % len(_SCHEDULE)]
    return {"grid_h": h, "grid_w": w, "n_seeds": n_seeds}


def _seed_cells(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    return [
        (r, c, int(value))
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5)
    ]


def _nearest_classes(
    h: int,
    w: int,
    seed_pts: list[tuple[int, int]],
    *,
    metric: str = "manhattan",
) -> tuple[list[tuple[int, int]], list[tuple[int, int]], dict[tuple[int, int], int]]:
    """Return (ties, unique cells, unique owner index) for non-seed interior cells."""
    seed_set = set(seed_pts)
    ties: list[tuple[int, int]] = []
    unique: list[tuple[int, int]] = []
    owners: dict[tuple[int, int], int] = {}
    for r in range(1, h - 1):
        for c in range(1, w - 1):
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
            hits = [index for index, distance in enumerate(distances) if distance == best]
            if len(hits) == 1:
                unique.append((r, c))
                owners[(r, c)] = hits[0]
            else:
                ties.append((r, c))
    return ties, unique, owners


def _metric_labels(
    h: int, w: int, seed_pts: list[tuple[int, int]], metric: str
) -> dict[tuple[int, int], int | None]:
    ties, unique, owners = _nearest_classes(h, w, seed_pts, metric=metric)
    labels: dict[tuple[int, int], int | None] = {pt: None for pt in ties}
    labels.update(owners)
    return labels


def _metric_disagreement_count(h: int, w: int, seed_pts: list[tuple[int, int]]) -> int:
    manhattan = _metric_labels(h, w, seed_pts, "manhattan")
    euclidean = _metric_labels(h, w, seed_pts, "euclidean2")
    return sum(manhattan.get(pt) != euclidean.get(pt) for pt in manhattan)


def _layout_is_teachable(
    h: int,
    w: int,
    seed_pts: list[tuple[int, int]],
    *,
    metric_class: str | None,
    band: str,
) -> bool:
    if len(set(seed_pts)) != len(seed_pts):
        return False
    ties, unique, owners = _nearest_classes(h, w, seed_pts)
    if not ties or not unique:
        return False
    # Every seed must control at least one blank cell; otherwise a fourth seed
    # can be decorative and an "ignore it" rival would survive the lesson.
    if set(owners.values()) != set(range(len(seed_pts))):
        return False

    disagreement = _metric_disagreement_count(h, w, seed_pts)
    if metric_class == "metric_same" and disagreement != 0:
        return False
    if metric_class == "metric_diff":
        minimum = {"easy": 1, "medium": 2, "hard": 3}[band]
        if disagreement < minimum:
            return False
    return True


def _collinear_metric_same_layout(
    h: int, w: int, n_seeds: int, rng
) -> list[tuple[int, int]] | None:
    """Construct a lawful layout where Manhattan and Euclidean agree exactly."""
    orientations = ["row", "col"]
    rng.shuffle(orientations)
    for orientation in orientations:
        if orientation == "row":
            span = 2 * (n_seeds - 1)
            max_start = (w - 2) - span
            if max_start < 1:
                continue
            start = rng.randint(1, max_start)
            row = rng.randint(1, h - 2)
            pts = [(row, start + 2 * i) for i in range(n_seeds)]
        else:
            span = 2 * (n_seeds - 1)
            max_start = (h - 2) - span
            if max_start < 1:
                continue
            start = rng.randint(1, max_start)
            col = rng.randint(1, w - 2)
            pts = [(start + 2 * i, col) for i in range(n_seeds)]
        if _layout_is_teachable(
            h, w, pts, metric_class="metric_same", band="medium"
        ):
            return pts
    return None


def _random_layout(
    h: int,
    w: int,
    n_seeds: int,
    rng,
    *,
    metric_class: str | None,
    band: str,
    require_noncollinear: bool = False,
) -> list[tuple[int, int]] | None:
    interior = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
    for _attempt in range(700):
        pts = rng.sample(interior, n_seeds)
        if any(
            abs(a[0] - b[0]) + abs(a[1] - b[1]) < 2
            for i, a in enumerate(pts)
            for b in pts[i + 1 :]
        ):
            continue
        if require_noncollinear and (
            len({r for r, _c in pts}) == 1 or len({c for _r, c in pts}) == 1
        ):
            continue
        # Avoid a single-line accidental layout in the discriminator branch.
        if metric_class == "metric_diff" and (
            len({r for r, _ in pts}) == 1 or len({c for _, c in pts}) == 1
        ):
            continue
        if _layout_is_teachable(
            h, w, pts, metric_class=metric_class, band=band
        ):
            return pts
    return None


def _noncollinear_metric_same_layout(
    h: int, w: int, n_seeds: int, rng
) -> list[tuple[int, int]] | None:
    """Find a non-collinear control whose Manhattan/Euclidean labels coincide."""
    pts = _random_layout(
        h,
        w,
        n_seeds,
        rng,
        metric_class="metric_same",
        band="medium",
        require_noncollinear=True,
    )
    if pts is not None:
        return pts

    # Deterministic fallback for the scheduled 3/4-seed controls.  Axis-aligned
    # rectangle corners give both metrics the same clipped Voronoi partition;
    # the random search above carries ordinary positional diversity.
    corners = [(1, 1), (1, w - 2), (h - 2, 1), (h - 2, w - 2)]
    if n_seeds == 4:
        candidates = [corners]
    elif n_seeds == 3:
        candidates = [corners[:index] + corners[index + 1 :] for index in range(4)]
    else:
        return None
    rng.shuffle(candidates)
    for candidate in candidates:
        candidate = list(candidate)
        rng.shuffle(candidate)
        if _layout_is_teachable(
            h, w, candidate, metric_class="metric_same", band="medium"
        ):
            return candidate
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one lawful input; the canonical Racket rule supplies outputs."""
    _validate_override_keys(overrides)
    band = _band(difficulty)
    slot = schedule_profile(seed, sample_index, difficulty)
    scheduled_h, scheduled_w, scheduled_n, metric_class = _SCHEDULE[slot]

    # Inject schedule defaults through GenCtx's normal override path so every
    # declared exact axis has keyed provenance on ordinary draws as well as on
    # explicit caller overrides.  Caller values still take precedence.
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
    h = ctx.draw_int("grid_h", 9, 11)
    w = ctx.draw_int("grid_w", 9, 12)
    n_seeds = ctx.draw_int("n_seeds", 3, 4)

    # The schedule's pedagogical class applies to ordinary draws.  Exact axis
    # overrides remain fully constructive even when they move away from the
    # scheduled profile; the metric class itself is not an override contract.
    has_explicit_override = bool(overrides)
    requested_metric_class = None if has_explicit_override else metric_class

    rng = ctx.draw_rng("layout")
    if requested_metric_class == "metric_same":
        if slot in _NONCOLLINEAR_METRIC_SAME_SLOTS:
            seed_pts = _noncollinear_metric_same_layout(h, w, n_seeds, rng)
        else:
            seed_pts = _collinear_metric_same_layout(h, w, n_seeds, rng)
            if seed_pts is None:
                seed_pts = _random_layout(
                    h, w, n_seeds, rng, metric_class="metric_same", band=band
                )
    else:
        seed_pts = _random_layout(
            h,
            w,
            n_seeds,
            rng,
            metric_class=requested_metric_class,
            band=band,
        )
    if seed_pts is None:
        raise ValueError(
            "could not realize a framed Voronoi layout with the required "
            f"teaching witnesses (h={h}, w={w}, n_seeds={n_seeds}, "
            f"metric_class={requested_metric_class!r})"
        )

    colors = ctx.draw_distinct_colors(
        "seed_colors", n=n_seeds, exclude=(0, 5, 8)
    )
    grid = full_grid(h, w, 0)
    for c in range(w):
        grid[0][c] = 5
        grid[h - 1][c] = 5
    for r in range(h):
        grid[r][0] = 5
        grid[r][w - 1] = 5
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
    if not (9 <= h <= 11):
        errors.append("grid height must be within the canonical 9..11 envelope")
    if not (9 <= w <= 12):
        errors.append("grid width must be within the canonical 9..12 envelope")
    if any(not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("all cells must be ARC integer colors 0..9")
        return {}, errors

    boundary = (
        list(grid[0])
        + list(grid[-1])
        + [grid[r][0] for r in range(1, h - 1)]
        + [grid[r][-1] for r in range(1, h - 1)]
    )
    if any(value != 5 for value in boundary):
        errors.append("outer boundary must be a complete color-5 frame")
    if any(grid[r][c] == 5 for r in range(1, h - 1) for c in range(1, w - 1)):
        errors.append("color 5 is reserved for the frame and may not appear in the interior")

    seeds = _seed_cells(grid)
    seed_colors = [value for _r, _c, value in seeds]
    if not (3 <= len(seeds) <= 4):
        errors.append("expected exactly 3 or 4 interior seed cells")
    if any(not (1 <= value <= 9) or value in (5, 8) for value in seed_colors):
        errors.append("seed colors must exclude 0, 5, and 8")
    if len(seed_colors) != len(set(seed_colors)):
        errors.append("seed colors must be pairwise distinct and occur once each")
    if any(r in (0, h - 1) or c in (0, w - 1) for r, c, _value in seeds):
        errors.append("all seed cells must lie strictly inside the gray frame")

    seed_pts = [(r, c) for r, c, _value in seeds]
    tie_blanks: list[tuple[int, int]] = []
    unique_blanks: list[tuple[int, int]] = []
    owners: dict[tuple[int, int], int] = {}
    if len(seed_pts) >= 2:
        ties, unique, owners = _nearest_classes(h, w, seed_pts)
        tie_blanks = [pt for pt in ties if grid[pt[0]][pt[1]] == 0]
        unique_blanks = [pt for pt in unique if grid[pt[0]][pt[1]] == 0]
        if not tie_blanks:
            errors.append("no blank Manhattan tie cell makes the cyan-8 branch observable")
        if not unique_blanks:
            errors.append("no blank uniquely-nearest cell makes seed-color filling observable")

    info = {
        "grid_h": h,
        "grid_w": w,
        "n_seeds": len(seeds),
        "seeds": seeds,
        "seed_pts": seed_pts,
        "tie_blanks": tie_blanks,
        "unique_blanks": unique_blanks,
        "owners": owners,
    }
    return info, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical input grammar, independently of curriculum slots."""
    del difficulty, meta
    _info, errors = _analyse(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Require canonical grammar plus one of the five public input profiles."""
    info, errors = _analyse(grid)
    if errors:
        return errors
    profile = (info["grid_h"], info["grid_w"], info["n_seeds"])
    if profile not in _CANONICAL_PROFILES:
        return [f"profile {profile} is outside the five canonical profiles"]
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
            elif tie_value is not None:
                out[r][c] = tie_value
    return out


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror used only for semantic auditing."""
    _info, errors = _analyse(grid)
    if errors:
        raise ValueError("invalid Voronoi input: " + "; ".join(errors))
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


def _rival_ignore_fourth_seed(grid):
    if len(_seed_cells(grid)) <= 3:
        return rule_mirror(grid)
    return _fill_by_metric(grid, metric="manhattan", tie_value=8, limit_seeds=3)


def _rival_ties_stay_blank(grid):
    return _fill_by_metric(grid, metric="manhattan", tie_value=None)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "euclidean_distance": _rival_euclidean,
    "euclidean_only_for_three_seeds": _rival_euclidean_three_only,
    "euclidean_only_for_four_seeds": _rival_euclidean_four_only,
    "ignore_fourth_seed": _rival_ignore_fourth_seed,
    "ties_stay_blank": _rival_ties_stay_blank,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _valid_info(grid) -> dict[str, Any] | None:
    info, errors = _analyse(grid)
    return None if errors else info


def _witness_tie_branch(grid) -> bool:
    info = _valid_info(grid)
    return info is not None and bool(info["tie_blanks"])


def _witness_three_seed_metric_disagreement(grid) -> bool:
    info = _valid_info(grid)
    return (
        info is not None
        and info["n_seeds"] == 3
        and _rival_euclidean(grid) != rule_mirror(grid)
    )


def _witness_four_seed_metric_disagreement(grid) -> bool:
    info = _valid_info(grid)
    return (
        info is not None
        and info["n_seeds"] == 4
        and _rival_euclidean(grid) != rule_mirror(grid)
    )


def _witness_fourth_seed_controls_region(grid) -> bool:
    info = _valid_info(grid)
    return (
        info is not None
        and info["n_seeds"] == 4
        and _rival_ignore_fourth_seed(grid) != rule_mirror(grid)
    )


SEMANTIC_WITNESSES = {
    "tie_boundary_requires_cyan_8": _witness_tie_branch,
    "three_seed_manhattan_not_euclidean": _witness_three_seed_metric_disagreement,
    "four_seed_manhattan_not_euclidean": _witness_four_seed_metric_disagreement,
    "fourth_seed_controls_nontrivial_region": _witness_fourth_seed_controls_region,
}

WITNESS_RIVALS = {
    "tie_boundary_requires_cyan_8": ["ties_stay_blank"],
    "three_seed_manhattan_not_euclidean": [
        "euclidean_distance",
        "euclidean_only_for_three_seeds",
    ],
    "four_seed_manhattan_not_euclidean": [
        "euclidean_distance",
        "euclidean_only_for_four_seeds",
    ],
    "fourth_seed_controls_nontrivial_region": ["ignore_fourth_seed"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations that refute every named plausible shortcut."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    refuted = {name: False for name in LESSON_COMPETITORS}
    profiles: set[tuple[int, int, int]] = set()
    seen_three = seen_four = False
    seen_three_metric_diff = seen_four_metric_diff = False

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
            reasons.append(f"demo {index} output is not the exact Manhattan Voronoi fill")
            continue
        profiles.add((info["grid_h"], info["grid_w"], info["n_seeds"]))
        seen_three = seen_three or info["n_seeds"] == 3
        seen_four = seen_four or info["n_seeds"] == 4
        metric_diff = _rival_euclidean(pair["input"]) != expected
        seen_three_metric_diff = seen_three_metric_diff or (
            info["n_seeds"] == 3 and metric_diff
        )
        seen_four_metric_diff = seen_four_metric_diff or (
            info["n_seeds"] == 4 and metric_diff
        )
        for name, rival in LESSON_COMPETITORS.items():
            refuted[name] = refuted[name] or rival(pair["input"]) != expected

    if len(profiles) < 3:
        reasons.append("demonstrations must span at least three size/seed-count profiles")
    if not seen_three or not seen_four:
        reasons.append("demonstrations must include both 3- and 4-seed inputs")
    if not seen_three_metric_diff:
        reasons.append("demonstrations need a 3-seed Manhattan-vs-Euclidean discriminator")
    if not seen_four_metric_diff:
        reasons.append("demonstrations need a 4-seed Manhattan-vs-Euclidean discriminator")
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
