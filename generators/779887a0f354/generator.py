"""Generator for ARC task 779887a0f354 — cells seen by two emitters.

Each yellow (4) cell emits rays in the four cardinal directions.  A ray stops
before a gray (5) blocker or at the grid boundary.  Count ray visits per cell;
the output is color 2 exactly where at least two rays arrive and 0 elsewhere.

Ordinary lessons cycle five marker geometries.  Together they distinguish
horizontal and vertical collinearity, perpendicular crossings, the >=2
threshold (including >=3 hits), local blocker effects, and marker erasure.
"""
from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "779887a0f354"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "b3cb42e1cb6f"

SUMMARY = (
    "Yellow (4) emitters cast cardinal rays until a gray (5) blocker or the "
    "edge.  Replace the whole canvas by 2 exactly at cells reached by at least "
    "two rays; all other cells become 0."
)

INVARIANTS = [
    "ordinary inputs are square 7..11 grids using exactly colors {0,4,5}",
    "ordinary inputs contain 3 or 4 separated yellow emitters and 1 or 2 gray blockers",
    "every ordinary input has at least two cells reached by two or more rays",
    "scene_profile, grid_size, and n_blockers are exactly recoverable from the returned grid",
    "every five consecutive sample indices cover all five decisive marker geometries",
]

EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0
DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

SCENE_PROFILES = (
    "row_pair",
    "column_pair",
    "cross_anchor",
    "rectangle",
    "triple_line",
)
GRID_SIZES = ("7x7", "8x8", "9x9", "10x10", "11x11")
SCHEDULE_PROFILES = SCENE_PROFILES

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "cyclic row/column/cross/rectangle/triple by sample_index",
        "valid": "|".join(SCENE_PROFILES),
    },
    "grid_size": {
        "type": "str",
        "default": "permuted 7x7..11x11 cycle",
        "valid": "|".join(GRID_SIZES),
    },
    "n_blockers": {
        "type": "int",
        "default": "alternating 1..2",
        "valid": "1..2",
    },
}

_DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Exact ordinary scene schedule; every length-five window covers all profiles."""
    _band(difficulty)
    return SCENE_PROFILES[sample_index % len(SCENE_PROFILES)]


def _scheduled_size(seed: int, sample_index: int, difficulty: str) -> str:
    # Multiplication by two permutes the five sizes, so every consecutive
    # five-index lesson sees every canonical and expanded scale once.
    offset = {"easy": 0, "medium": 1, "hard": 2}[difficulty]
    index = (2 * sample_index + int(seed) + offset) % len(GRID_SIZES)
    return GRID_SIZES[index]


def _draw_axis(ctx, overrides: dict[str, Any], name: str, scheduled: Any, values: tuple[Any, ...]):
    if name in overrides:
        return ctx.draw_choice(name, list(values))
    return ctx.draw_choice(name, [scheduled])


def _copy_grid(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _count_grid(grid: list[list[int]], *, blockers: bool = True) -> list[list[int]]:
    """Return cardinal-ray visit counts; only color 5 blocks when requested."""
    h, w = len(grid), len(grid[0])
    counts = full_grid(h, w, 0)
    emitters = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 4]
    for r, c in emitters:
        for dr, dc in _DIRECTIONS:
            rr, cc = r + dr, c + dc
            while 0 <= rr < h and 0 <= cc < w:
                if blockers and grid[rr][cc] == 5:
                    break
                counts[rr][cc] += 1
                rr += dr
                cc += dc
    return counts


def _render_from_counts(counts: list[list[int]], predicate: Callable[[int], bool]) -> list[list[int]]:
    return [[2 if predicate(value) else 0 for value in row] for row in counts]


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    return _render_from_counts(_count_grid(grid), lambda value: value >= 2)


def _n_positive(grid: list[list[int]]) -> int:
    return sum(value == 2 for row in rule_mirror(grid) for value in row)


def _separated_choices(values: list[int], count: int, minimum_gap: int) -> list[tuple[int, ...]]:
    return [
        choice
        for choice in combinations(values, count)
        if all(b - a >= minimum_gap for a, b in zip(choice, choice[1:]))
    ]


def _choose_marker_layout(profile: str, size: int, rng) -> list[tuple[int, int]]:
    interior = list(range(1, size - 1))
    far_pairs = _separated_choices(interior, 2, 3)
    medium_pairs = _separated_choices(interior, 2, 2)
    triples = _separated_choices(interior, 3, 2)
    if not far_pairs or not medium_pairs or not triples:
        raise RuntimeError(f"grid size {size} cannot realize the marker grammar")

    if profile == "row_pair":
        row, other_row = rng.choice(medium_pairs)
        if rng.random() < 0.5:
            row, other_row = other_row, row
        c1, c2 = rng.choice(far_pairs)
        extras = [c for c in interior if c not in (c1, c2)]
        return [(row, c1), (row, c2), (other_row, rng.choice(extras))]

    if profile == "column_pair":
        col, other_col = rng.choice(medium_pairs)
        if rng.random() < 0.5:
            col, other_col = other_col, col
        r1, r2 = rng.choice(far_pairs)
        extras = [r for r in interior if r not in (r1, r2)]
        return [(r1, col), (r2, col), (rng.choice(extras), other_col)]

    if profile == "cross_anchor":
        r1, r2 = rng.choice(far_pairs)
        c1, c2 = rng.choice(far_pairs)
        corners = [(r1, c1), (r1, c2), (r2, c1), (r2, c2)]
        missing = rng.randrange(4)
        return [point for index, point in enumerate(corners) if index != missing]

    if profile == "rectangle":
        r1, r2 = rng.choice(far_pairs)
        c1, c2 = rng.choice(far_pairs)
        return [(r1, c1), (r1, c2), (r2, c1), (r2, c2)]

    if profile == "triple_line":
        row, other_row = rng.choice(medium_pairs)
        if rng.random() < 0.5:
            row, other_row = other_row, row
        c1, c2, c3 = rng.choice(triples)
        extras = [c for c in interior if c not in (c1, c2, c3)]
        return [(row, c1), (row, c2), (row, c3), (other_row, rng.choice(extras))]

    raise ValueError(f"unknown scene_profile: {profile!r}")


def _marker_rows_cols(grid: list[list[int]]) -> tuple[set[int], set[int]]:
    rows = {r for r, row in enumerate(grid) if 4 in row}
    cols = {
        c
        for c in range(len(grid[0]))
        if any(grid[r][c] == 4 for r in range(len(grid)))
    }
    return rows, cols


def _candidate_blockers(grid: list[list[int]]) -> tuple[list[tuple[int, int, int]], list[tuple[int, int]]]:
    """Return effective candidates (with answer-delta size) and ray-free decoys."""
    h, w = len(grid), len(grid[0])
    baseline = rule_mirror(grid)
    marker_rows, marker_cols = _marker_rows_cols(grid)
    markers = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 4]
    effective: list[tuple[int, int, int]] = []
    decoys: list[tuple[int, int]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                continue
            trial = _copy_grid(grid)
            trial[r][c] = 5
            output = rule_mirror(trial)
            delta = sum(
                baseline[rr][cc] != output[rr][cc]
                for rr in range(h)
                for cc in range(w)
            )
            if delta and _n_positive(trial) >= 2:
                distance = min(abs(r - mr) + abs(c - mc) for mr, mc in markers)
                # Prefer visibly separated blockers, but retain all candidates.
                effective.append((r, c, delta * 10 + min(distance, 9)))
            elif r not in marker_rows and c not in marker_cols:
                decoys.append((r, c))
    return effective, decoys


def _place_blockers(grid: list[list[int]], count: int, sample_index: int, rng) -> list[list[int]]:
    if count not in (1, 2):
        raise ValueError(f"n_blockers must be 1 or 2, got {count}")
    result = _copy_grid(grid)

    # A one-blocker schedule alternates a decisive blocker and a ray-free
    # distractor.  Two-blocker scenes contain one of each.  Every five-example
    # lesson therefore proves both that blockers matter and that they are local.
    need_effective = count == 2 or sample_index % 4 == 0
    need_decoy = count == 2 or not need_effective

    if need_decoy:
        _, decoys = _candidate_blockers(result)
        if not decoys:
            raise RuntimeError("could not place a ray-free distractor blocker")
        r, c = rng.choice(decoys)
        result[r][c] = 5

    if need_effective:
        effective, _ = _candidate_blockers(result)
        if not effective:
            raise RuntimeError("could not place an answer-changing blocker")
        # Prefer the smallest answer-changing truncation: it proves that gray
        # matters without erasing the other branch witnesses in the scene.
        min_delta = min(score // 10 for _, _, score in effective)
        shortlist = [(r, c, score % 10) for r, c, score in effective if score // 10 == min_delta]
        best_distance = max(distance for _, _, distance in shortlist)
        r, c, _ = rng.choice([item for item in shortlist if item[2] == best_distance])
        result[r][c] = 5

    if sum(value == 5 for row in result for value in row) != count:
        raise RuntimeError("blocker placement did not realize the requested count")
    return result


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = _draw_axis(
        ctx,
        overrides,
        "scene_profile",
        schedule_profile(seed, sample_index, band),
        SCENE_PROFILES,
    )
    size_name = _draw_axis(
        ctx,
        overrides,
        "grid_size",
        _scheduled_size(seed, sample_index, band),
        GRID_SIZES,
    )
    blocker_count = ctx.draw_int("n_blockers", 1, 2) if "n_blockers" in overrides else ctx.draw_choice(
        "n_blockers", [1 + (sample_index % 2)]
    )
    size = int(str(size_name).split("x", 1)[0])
    rng = ctx.draw_rng("layout")

    for _ in range(96):
        grid = full_grid(size, size, 0)
        for r, c in _choose_marker_layout(profile, size, rng):
            grid[r][c] = 4
        try:
            grid = _place_blockers(grid, int(blocker_count), sample_index, rng)
        except RuntimeError:
            continue
        errors = strict_canonical_like(grid)
        if errors:
            continue
        info, _ = _analyse(grid)
        if profile == "triple_line" and info["max_hits"] < 3:
            continue
        observed = observe_overrides(grid)
        requested = {
            "scene_profile": profile,
            "grid_size": size_name,
            "n_blockers": int(blocker_count),
        }
        if observed != requested:
            continue
        return grid
    raise ValueError(
        "could not realize requested ray lesson "
        f"profile={profile} size={size_name} blockers={blocker_count}"
    )


def _validate_grid(grid: Any) -> tuple[int, int, list[list[int]], list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, [], ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, [], ["grid rows must be non-empty"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return h, w, [], ["grid must be rectangular"]
    normalized = [list(row) for row in grid]
    errors: list[str] = []
    if h != w:
        errors.append(f"input must be square, got {h}x{w}")
    if not 7 <= h <= 11 or not 7 <= w <= 11:
        errors.append(f"input dimensions must be 7..11, got {h}x{w}")
    for r, row in enumerate(normalized):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) is not an ARC color: {value!r}")
                return h, w, normalized, errors
    return h, w, normalized, errors


def _classify_scene(markers: list[tuple[int, int]]) -> str | None:
    row_counts = Counter(r for r, _ in markers)
    col_counts = Counter(c for _, c in markers)
    if max(row_counts.values(), default=0) >= 3 or max(col_counts.values(), default=0) >= 3:
        return "triple_line"
    if len(markers) == 4:
        repeated_rows = [r for r, count in row_counts.items() if count == 2]
        repeated_cols = [c for c, count in col_counts.items() if count == 2]
        if len(repeated_rows) == 2 and len(repeated_cols) == 2:
            rectangle = {(r, c) for r in repeated_rows for c in repeated_cols}
            if set(markers) == rectangle:
                return "rectangle"
    has_row_pair = any(count >= 2 for count in row_counts.values())
    has_col_pair = any(count >= 2 for count in col_counts.values())
    if has_row_pair and has_col_pair:
        return "cross_anchor"
    if has_row_pair:
        return "row_pair"
    if has_col_pair:
        return "column_pair"
    return None


def _blocker_roles(grid: list[list[int]]) -> tuple[int, int]:
    baseline = rule_mirror(grid)
    effective = 0
    distractor = 0
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 5:
                continue
            trial = _copy_grid(grid)
            trial[r][c] = 0
            if rule_mirror(trial) != baseline:
                effective += 1
            else:
                distractor += 1
    return effective, distractor


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    h, w, normalized, errors = _validate_grid(grid)
    info: dict[str, Any] = {"h": h, "w": w, "grid": normalized}
    if not normalized:
        return info, errors

    colors = {value for row in normalized for value in row}
    if not colors <= {0, 4, 5}:
        errors.append(f"input uses colors outside {{0,4,5}}: {sorted(colors)}")

    markers = [(r, c) for r in range(h) for c in range(w) if normalized[r][c] == 4]
    blockers = [(r, c) for r in range(h) for c in range(w) if normalized[r][c] == 5]
    if not 3 <= len(markers) <= 4:
        errors.append(f"input must contain 3 or 4 emitters, got {len(markers)}")
    if len(blockers) > 2:
        errors.append(f"input may contain at most 2 blockers, got {len(blockers)}")

    adjacent_pairs = [
        (a, b)
        for a, b in combinations(markers, 2)
        if abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1
    ]
    if adjacent_pairs:
        errors.append(f"emitters must be separated; adjacent pair {adjacent_pairs[0]}")

    scene_profile = _classify_scene(markers)
    if scene_profile is None:
        errors.append("emitters do not exhibit a declared row/column relation")

    counts = _count_grid(normalized) if normalized else []
    output = _render_from_counts(counts, lambda value: value >= 2) if counts else []
    positive = sum(value == 2 for row in output for value in row)
    if positive < 2:
        errors.append(f"rays must create at least 2 output cells, got {positive}")

    row_marker_counts = Counter(r for r, _ in markers)
    col_marker_counts = Counter(c for _, c in markers)
    perpendicular_cells = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if normalized[r][c] == 0
        and counts[r][c] >= 2
        and row_marker_counts[r] == 1
        and col_marker_counts[c] == 1
    ] if counts else []
    effective, distractor = _blocker_roles(normalized) if blockers else (0, 0)
    marker_zero_cells = [
        (r, c) for r, c in markers if output and output[r][c] == 0
    ]
    info.update(
        {
            "colors": colors,
            "markers": markers,
            "blockers": blockers,
            "scene_profile": scene_profile,
            "grid_size": f"{h}x{w}",
            "n_blockers": len(blockers),
            "counts": counts,
            "output": output,
            "positive_cells": positive,
            "max_hits": max((value for row in counts for value in row), default=0),
            "row_marker_counts": row_marker_counts,
            "col_marker_counts": col_marker_counts,
            "perpendicular_cells": perpendicular_cells,
            "effective_blockers": effective,
            "distractor_blockers": distractor,
            "marker_zero_cells": marker_zero_cells,
        }
    )
    return info, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    _band(difficulty)
    return list(_analyse(grid)[1])


def strict_canonical_like(grid: Any) -> list[str]:
    info, errors = _analyse(grid)
    reasons = list(errors)
    if info.get("colors") != {0, 4, 5}:
        reasons.append(f"strict lessons must use exactly colors {{0,4,5}}, got {sorted(info.get('colors', set()))}")
    if info.get("n_blockers") not in (1, 2):
        reasons.append(f"strict lessons require 1 or 2 blockers, got {info.get('n_blockers')}")
    return reasons


def observe_overrides(grid: Any) -> dict[str, Any]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    if info["scene_profile"] not in SCENE_PROFILES:
        raise ValueError(f"unobservable scene profile: {info['scene_profile']!r}")
    if info["grid_size"] not in GRID_SIZES:
        raise ValueError(f"unobservable grid size: {info['grid_size']!r}")
    if info["n_blockers"] not in (1, 2):
        raise ValueError(f"unobservable blocker count: {info['n_blockers']!r}")
    return {
        "scene_profile": info["scene_profile"],
        "grid_size": info["grid_size"],
        "n_blockers": info["n_blockers"],
    }


def _rival_exactly_two(grid: list[list[int]]) -> list[list[int]]:
    return _render_from_counts(_count_grid(grid), lambda value: value == 2)


def _rival_ignore_blockers(grid: list[list[int]]) -> list[list[int]]:
    return _render_from_counts(_count_grid(grid, blockers=False), lambda value: value >= 2)


def _rival_row_only(grid: list[list[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    counts = full_grid(h, w, 0)
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 4:
                continue
            for dc in (-1, 1):
                cc = c + dc
                while 0 <= cc < w and grid[r][cc] != 5:
                    counts[r][cc] += 1
                    cc += dc
    return _render_from_counts(counts, lambda value: value >= 2)


def _rival_column_only(grid: list[list[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    counts = full_grid(h, w, 0)
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 4:
                continue
            for dr in (-1, 1):
                rr = r + dr
                while 0 <= rr < h and grid[rr][c] != 5:
                    counts[rr][c] += 1
                    rr += dr
    return _render_from_counts(counts, lambda value: value >= 2)


def _rival_collinear_only(grid: list[list[int]]) -> list[list[int]]:
    counts = _count_grid(grid)
    markers = [(r, c) for r in range(len(grid)) for c in range(len(grid[0])) if grid[r][c] == 4]
    row_counts = Counter(r for r, _ in markers)
    col_counts = Counter(c for _, c in markers)
    return [
        [
            2 if counts[r][c] >= 2 and (row_counts[r] >= 2 or col_counts[c] >= 2) else 0
            for c in range(len(grid[0]))
        ]
        for r in range(len(grid))
    ]


def _rival_preserve_markers(grid: list[list[int]]) -> list[list[int]]:
    output = rule_mirror(grid)
    return [
        [4 if grid[r][c] == 4 else output[r][c] for c in range(len(grid[0]))]
        for r in range(len(grid))
    ]


def _rival_any_blocker_zero(grid: list[list[int]]) -> list[list[int]]:
    if any(value == 5 for row in grid for value in row):
        return full_grid(len(grid), len(grid[0]), 0)
    return rule_mirror(grid)


def _witness_horizontal(grid: Any) -> bool:
    info, errors = _analyse(grid)
    if errors:
        return False
    return any(count >= 2 for count in info["row_marker_counts"].values()) and any(
        info["output"][r][c] == 2
        and info["row_marker_counts"][r] >= 2
        and info["col_marker_counts"][c] == 0
        for r in range(info["h"])
        for c in range(info["w"])
    )


def _witness_vertical(grid: Any) -> bool:
    info, errors = _analyse(grid)
    if errors:
        return False
    return any(count >= 2 for count in info["col_marker_counts"].values()) and any(
        info["output"][r][c] == 2
        and info["col_marker_counts"][c] >= 2
        and info["row_marker_counts"][r] == 0
        for r in range(info["h"])
        for c in range(info["w"])
    )


def _witness_perpendicular(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and bool(info["perpendicular_cells"])


def _witness_effective_blocker(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and info["effective_blockers"] >= 1


def _witness_distractor_blocker(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and info["distractor_blockers"] >= 1


def _witness_three_hits(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and info["max_hits"] >= 3


def _witness_marker_erasure(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and bool(info["marker_zero_cells"])


SEMANTIC_WITNESSES = {
    "horizontal_collinear_overlap": _witness_horizontal,
    "vertical_collinear_overlap": _witness_vertical,
    "perpendicular_ray_crossing": _witness_perpendicular,
    "effective_blocker_changes_answer": _witness_effective_blocker,
    "distractor_blocker_is_local": _witness_distractor_blocker,
    "three_or_more_rays_still_paint_two": _witness_three_hits,
    "unseen_emitters_are_erased": _witness_marker_erasure,
}

SEMANTIC_RIVALS = {
    "paint_only_exactly_two_hits": _rival_exactly_two,
    "gray_cells_do_not_block": _rival_ignore_blockers,
    "horizontal_rays_only": _rival_row_only,
    "vertical_rays_only": _rival_column_only,
    "paint_only_collinear_overlap": _rival_collinear_only,
    "preserve_yellow_emitters": _rival_preserve_markers,
    "any_gray_cell_cancels_all_rays": _rival_any_blocker_zero,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "paint_only_exactly_two_hits": _rival_exactly_two,
    "gray_cells_do_not_block": _rival_ignore_blockers,
    "paint_only_collinear_overlap": _rival_collinear_only,
}
WITNESS_RIVALS = {
    "horizontal_collinear_overlap": ["vertical_rays_only"],
    "vertical_collinear_overlap": ["horizontal_rays_only"],
    "perpendicular_ray_crossing": ["paint_only_collinear_overlap"],
    "effective_blocker_changes_answer": ["gray_cells_do_not_block"],
    "distractor_blocker_is_local": ["any_gray_cell_cancels_all_rays"],
    "three_or_more_rays_still_paint_two": ["paint_only_exactly_two_hits"],
    "unseen_emitters_are_erased": ["preserve_yellow_emitters"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    profiles: set[str] = set()
    sizes: set[str] = set()
    blocker_counts: set[int] = set()
    saw_effective = False
    saw_distractor = False
    saw_three_hits = False
    valid_pairs: list[tuple[list[list[int]], list[list[int]]]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        info, errors = _analyse(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output does not match the selected Racket authority")
            continue
        valid_pairs.append((pair["input"], pair["output"]))
        profiles.add(info["scene_profile"])
        sizes.add(info["grid_size"])
        blocker_counts.add(info["n_blockers"])
        saw_effective |= info["effective_blockers"] >= 1
        saw_distractor |= info["distractor_blockers"] >= 1
        saw_three_hits |= info["max_hits"] >= 3

    missing_profiles = set(SCENE_PROFILES) - profiles
    if missing_profiles:
        reasons.append(f"demonstrations miss scene profiles: {sorted(missing_profiles)}")
    if len(sizes) < 3:
        reasons.append(f"demonstrations show only {len(sizes)} grid sizes; need at least 3")
    if blocker_counts != {1, 2}:
        reasons.append(f"demonstrations must show blocker counts 1 and 2, got {sorted(blocker_counts)}")
    if not saw_effective:
        reasons.append("demonstrations lack an answer-changing blocker")
    if not saw_distractor:
        reasons.append("demonstrations lack a local distractor blocker")
    if not saw_three_hits:
        reasons.append("demonstrations never distinguish >=2 from exactly 2 ray hits")

    for name, rival in LESSON_COMPETITORS.items():
        if valid_pairs and all(rival(grid) == output for grid, output in valid_pairs):
            reasons.append(f"named rival survives every demonstration: {name}")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        query_errors = strict_canonical_like(query["input"])
        if query_errors:
            reasons.append(f"query malformed: {query_errors[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output does not match the selected Racket authority")
    return reasons
