"""Generator for 678b4a951150 — fill one-cell horizontal orange gaps.

The input uses a black (0) background, orange (7) markers, and blue-gray (6)
distractors.  Every black cell immediately flanked by orange on its left and
right becomes green (3); all other cells remain unchanged.

Ordinary draws cycle through the four canonical size/count profiles.  The
cycle also supplies explicit negative evidence against plausible shortcuts:
vertical orange gaps, longer horizontal gaps, adjacent orange pairs,
``6,0,6`` gaps, edge-touching targets, boundary-row targets, target rows that
also contain a 6, and rows containing several targets.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "678b4a951150"
TASK_ID = "678b4a951150"
VERSION = "2.2.0"
RULE_HASH = "f5f03a3a484b"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.95

SUMMARY = (
    "A canonical-sized black grid contains four to eight horizontal orange "
    "7-0-7 gaps and three or four color-6 distractors. Each qualifying zero "
    "becomes 3. Vertical 7-0-7 gaps, adjacent 7s, longer 7...7 gaps, and "
    "6-0-6 gaps are unchanged negative evidence. The four-profile lesson "
    "schedule duplicates that color-control witness so every five-pair query "
    "rotation remains identifiable."
)

INVARIANTS = [
    "grid dimensions and target/distractor counts follow one of four canonical profiles",
    "the input palette is exactly a subset of {0, 6, 7}; color 3 is output-only",
    "there are exactly 4..8 horizontal 7-0-7 target cells",
    "there are exactly 3..4 color-6 distractor cells",
    "at least one orange cell is negative evidence rather than part of a target",
    "ordinary four-example lessons cover column-edge, row-edge, same-row-6, multi-target-row, vertical-gap, long-gap, and 6-gap counterexamples",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical profile",
        "valid": "8..10",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical profile",
        "valid": "11..14",
    },
    "n_targets": {
        "type": "int",
        "default": "scheduled canonical profile",
        "valid": "4..8",
    },
    "n_sixes": {
        "type": "int",
        "default": "scheduled canonical profile",
        "valid": "3..4",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
SCHEDULE_PROFILES = (0, 1, 2, 3)

# (height, width, number of changed cells, number of color-6 distractors)
# These are the four public profile families, including the held-out query.
_PROFILES = (
    (8, 14, 4, 3),
    (10, 13, 7, 4),
    (9, 12, 5, 3),
    (10, 11, 8, 3),
)
_CANONICAL_PROFILES = frozenset(_PROFILES)


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> int:
    """Expose a four-way curriculum schedule to the semantic gate.

    Any four consecutive sample indexes visit every profile. Difficulty only
    rotates the starting point, so every band retains complete lesson coverage.
    """
    del seed
    offset = {None: 0, "easy": 0, "medium": 1, "hard": 2}.get(difficulty)
    if offset is None:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return (int(sample_index) + offset) % len(_PROFILES)


def _draw_profile_int(ctx, overrides: dict[str, Any], label: str,
                      default: int, lo: int, hi: int) -> int:
    """Pin the scheduled default while preserving the full override domain."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _rectangular_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, list) or not grid:
        return None, ["grid must be a nonempty list"]
    if not all(isinstance(row, list) and row for row in grid):
        return None, ["each row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None, ["grid must be rectangular"]
    if any(isinstance(value, bool) or not isinstance(value, int)
           for row in grid for value in row):
        return None, ["all grid cells must be integers"]
    return grid, []


def _target_centers(grid: list[list[int]]) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row in range(len(grid))
        for col in range(1, len(grid[0]) - 1)
        if grid[row][col] == 0
        and grid[row][col - 1] == 7
        and grid[row][col + 1] == 7
    ]


def _vertical_gap_centers(grid: list[list[int]]) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row in range(1, len(grid) - 1)
        for col in range(len(grid[0]))
        if grid[row][col] == 0
        and grid[row - 1][col] == 7
        and grid[row + 1][col] == 7
    ]


def _six_gap_centers(grid: list[list[int]]) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row in range(len(grid))
        for col in range(1, len(grid[0]) - 1)
        if grid[row][col] == 0
        and grid[row][col - 1] == 6
        and grid[row][col + 1] == 6
    ]


def _long_gap_pairs(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    """Orange endpoints with at least two all-zero cells between them."""
    pairs: list[tuple[int, int, int]] = []
    width = len(grid[0])
    for row in range(len(grid)):
        for left in range(width - 3):
            if grid[row][left] != 7:
                continue
            for right in range(left + 3, width):
                if grid[row][right] == 7 and all(
                    grid[row][col] == 0 for col in range(left + 1, right)
                ):
                    pairs.append((row, left, right))
                    break
    return pairs


def _target_endpoint_cells(grid: list[list[int]]) -> set[tuple[int, int]]:
    return {
        endpoint
        for row, col in _target_centers(grid)
        for endpoint in ((row, col - 1), (row, col + 1))
    }


def _has_dangling_orange(grid: list[list[int]]) -> bool:
    endpoints = _target_endpoint_cells(grid)
    return any(
        value == 7 and (row, col) not in endpoints
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
    )


def _analyze(grid: Any) -> dict[str, Any]:
    normalized, errors = _rectangular_grid(grid)
    if errors:
        return {"errors": errors}
    assert normalized is not None
    height, width = len(normalized), len(normalized[0])
    palette = {value for row in normalized for value in row}
    targets = _target_centers(normalized)
    target_rows = Counter(row for row, _ in targets)
    endpoints = _target_endpoint_cells(normalized)
    vertical_gaps = _vertical_gap_centers(normalized)
    vertical_only_gaps = [cell for cell in vertical_gaps if cell not in set(targets)]
    adjacent_pairs = sum(
        normalized[row][col] == normalized[row][col + 1] == 7
        for row in range(height)
        for col in range(width - 1)
    )
    return {
        "errors": [],
        "grid_h": height,
        "grid_w": width,
        "palette": palette,
        "n_targets": len(targets),
        "target_centers": targets,
        "target_rows": target_rows,
        "n_sixes": sum(value == 6 for row in normalized for value in row),
        "n_sevens": sum(value == 7 for row in normalized for value in row),
        "target_endpoints": endpoints,
        "vertical_gaps": vertical_gaps,
        "vertical_only_gaps": vertical_only_gaps,
        "six_gaps": _six_gap_centers(normalized),
        "long_gaps": _long_gap_pairs(normalized),
        "adjacent_pairs": adjacent_pairs,
        "has_dangling_orange": _has_dangling_orange(normalized),
        "has_edge_target": any(col in (1, width - 2) for _, col in targets),
        "has_boundary_row_target": any(row in (0, height - 1) for row, _ in targets),
        "has_target_row_with_six": any(6 in normalized[row] for row, _ in targets),
        "max_targets_in_row": max(target_rows.values(), default=0),
    }


def _target_run_lengths(profile: int, n_targets: int) -> list[int]:
    if profile == 0:
        return [1] * n_targets
    if profile == 1:
        chain = min(3, n_targets)
        return [chain] + [1] * (n_targets - chain)
    if profile == 2:
        return [1] * n_targets
    chain = min(4, n_targets)
    return [chain] + [1] * (n_targets - chain)


def _place_target_runs(grid: list[list[int]], rng, run_lengths: list[int],
                       *, edge_mode: str | None,
                       boundary_row_required: bool) -> bool:
    height, width = len(grid), len(grid[0])
    if len(run_lengths) > height:
        return False
    rows = list(range(height))
    rng.shuffle(rows)
    if boundary_row_required:
        boundary_rows = [0, height - 1]
        rng.shuffle(boundary_rows)
        first_row = boundary_rows[0]
        rows.remove(first_row)
        rows.insert(0, first_row)
    for index, run_length in enumerate(run_lengths):
        span = 2 * run_length + 1
        if span > width:
            return False
        row = rows[index]
        if index == 0 and edge_mode == "left":
            start = 0
        elif index == 0 and edge_mode == "right":
            start = width - span
        else:
            starts = list(range(width - span + 1))
            # Non-edge profiles still vary position, but avoid accidentally
            # supplying the edge witness reserved for profiles 2/3.
            if edge_mode is None:
                interior = [value for value in starts
                            if value > 0 and value + span < width]
                if interior:
                    starts = interior
            rng.shuffle(starts)
            start = starts[0]
        for col in range(start, start + span, 2):
            grid[row][col] = 7
    return True


def _try_pattern(grid: list[list[int]], rng,
                 pattern: tuple[tuple[int, int, int], ...],
                 *, required_targets: int,
                 required_six_gaps: int | None = None,
                 require: Callable[[list[list[int]]], bool] | None = None) -> bool:
    """Place a translated pattern without changing the target grammar."""
    height, width = len(grid), len(grid[0])
    max_dr = max(dr for dr, _, _ in pattern)
    max_dc = max(dc for _, dc, _ in pattern)
    origins = [
        (row, col)
        for row in range(height - max_dr)
        for col in range(width - max_dc)
    ]
    rng.shuffle(origins)
    for row0, col0 in origins:
        cells = [(row0 + dr, col0 + dc, value) for dr, dc, value in pattern]
        if any(grid[row][col] != 0 for row, col, _ in cells):
            continue
        for row, col, value in cells:
            grid[row][col] = value
        valid = len(_target_centers(grid)) == required_targets
        if valid and required_six_gaps is not None:
            valid = len(_six_gap_centers(grid)) == required_six_gaps
        if valid and require is not None:
            valid = bool(require(grid))
        if valid:
            return True
        for row, col, _ in cells:
            grid[row][col] = 0
    return False


def _place_sixes(grid: list[list[int]], rng, n_sixes: int,
                  *, six_gap_required: bool, target_row_required: bool,
                  required_targets: int) -> bool:
    desired_gaps = 1 if six_gap_required else 0
    placed = 0
    if six_gap_required:
        if not _try_pattern(
            grid,
            rng,
            ((0, 0, 6), (0, 2, 6)),
            required_targets=required_targets,
            required_six_gaps=1,
            require=(
                (lambda candidate: _analyze(candidate)["has_target_row_with_six"])
                if target_row_required
                else None
            ),
        ):
            return False
        placed = 2
    elif target_row_required:
        if not _try_pattern(
            grid,
            rng,
            ((0, 0, 6),),
            required_targets=required_targets,
            required_six_gaps=0,
            require=lambda candidate: _analyze(candidate)["has_target_row_with_six"],
        ):
            return False
        placed = 1

    candidates = [
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] == 0
    ]
    rng.shuffle(candidates)
    for row, col in candidates:
        if placed >= n_sixes:
            break
        grid[row][col] = 6
        if (
            len(_target_centers(grid)) == required_targets
            and len(_six_gap_centers(grid)) == desired_gaps
        ):
            placed += 1
        else:
            grid[row][col] = 0
    return placed == n_sixes


def generate(seed: int, sample_index: int, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    profile = schedule_profile(seed, sample_index, difficulty)
    default_h, default_w, default_targets, default_sixes = _PROFILES[profile]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_profile_int(ctx, overrides, "grid_h", default_h, 8, 10)
    width = _draw_profile_int(ctx, overrides, "grid_w", default_w, 11, 14)
    n_targets = _draw_profile_int(ctx, overrides, "n_targets", default_targets, 4, 8)
    n_sixes = _draw_profile_int(ctx, overrides, "n_sixes", default_sixes, 3, 4)
    rng = ctx.draw_rng("layout")

    edge_mode = {0: None, 1: None, 2: "left", 3: "right"}[profile]
    run_lengths = _target_run_lengths(profile, n_targets)
    for _attempt in range(300):
        grid = full_grid(height, width, 0)
        if not _place_target_runs(
            grid,
            rng,
            run_lengths,
            edge_mode=edge_mode,
            boundary_row_required=(profile in (0, 2)),
        ):
            continue
        if len(_target_centers(grid)) != n_targets:
            continue

        # Profiles 0 and 2 carry a vertical 7-0-7 counterexample.
        if profile in (0, 2):
            if not _try_pattern(
                grid,
                rng,
                ((0, 0, 7), (2, 0, 7)),
                required_targets=n_targets,
                require=lambda g: bool(
                    set(_vertical_gap_centers(g)) - set(_target_centers(g))
                ),
            ):
                continue
            # One additional unrelated orange marker keeps target color/count
            # shortcuts from using every 7 as an endpoint.
            if not _try_pattern(
                grid,
                rng,
                ((0, 0, 7),),
                required_targets=n_targets,
            ):
                continue
        else:
            # Compound distractor: adjacent 77 plus a longer 7-0-0-7 gap,
            # using only three orange cells.
            if not _try_pattern(
                grid,
                rng,
                ((0, 0, 7), (0, 1, 7), (0, 4, 7)),
                required_targets=n_targets,
                require=lambda g: bool(_long_gap_pairs(g)),
            ):
                continue
            # Low target-count overrides otherwise leave fewer orange cells
            # than any canonical input. Add unrelated singles until the
            # canonical lower envelope is reached.
            while sum(value == 7 for row in grid for value in row) < 11:
                if not _try_pattern(
                    grid,
                    rng,
                    ((0, 0, 7),),
                    required_targets=n_targets,
                ):
                    break
            if sum(value == 7 for row in grid for value in row) < 11:
                continue

        if not _place_sixes(
            grid,
            rng,
            n_sixes,
            six_gap_required=(profile in (0, 2)),
            target_row_required=(profile in (0, 2)),
            required_targets=n_targets,
        ):
            continue

        errors = self_check(grid)
        if errors:
            continue
        # Verify the schedule-specific feature survived placement.
        info = _analyze(grid)
        if profile == 0 and not (
            info["vertical_only_gaps"]
            and info["has_boundary_row_target"]
            and info["has_target_row_with_six"]
            and info["six_gaps"]
        ):
            continue
        if profile == 1 and not (
            info["max_targets_in_row"] >= 2 and info["long_gaps"]
            and info["adjacent_pairs"]
        ):
            continue
        if profile == 2 and not (
            info["has_edge_target"] and info["has_boundary_row_target"]
            and info["has_target_row_with_six"] and info["vertical_only_gaps"]
            and info["six_gaps"]
        ):
            continue
        if profile == 3 and not (
            info["has_edge_target"] and info["max_targets_in_row"] >= 2
            and info["long_gaps"] and info["adjacent_pairs"]
        ):
            continue
        return grid
    raise ValueError("could not place a lawful shortcut-rebutting scene")


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the selected Racket authority."""
    output = [list(row) for row in grid]
    for row, col in _target_centers(grid):
        output[row][col] = 3
    return output


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    info = _analyze(grid)
    if info.get("errors"):
        return list(info["errors"])
    errors: list[str] = []
    if not (8 <= info["grid_h"] <= 10):
        errors.append(f"grid height {info['grid_h']} is outside 8..10")
    if not (11 <= info["grid_w"] <= 14):
        errors.append(f"grid width {info['grid_w']} is outside 11..14")
    if not info["palette"].issubset({0, 6, 7}):
        errors.append(f"input palette {sorted(info['palette'])} is not a subset of [0, 6, 7]")
    if not (4 <= info["n_targets"] <= 8):
        errors.append(f"expected 4..8 horizontal 7-0-7 targets, got {info['n_targets']}")
    if not (3 <= info["n_sixes"] <= 4):
        errors.append(f"expected 3..4 color-6 distractors, got {info['n_sixes']}")
    if not (11 <= info["n_sevens"] <= 19):
        errors.append(f"expected 11..19 orange cells, got {info['n_sevens']}")
    if not info["has_dangling_orange"]:
        errors.append("every orange cell is a target endpoint; missing negative orange evidence")
    if len(rule_mirror(grid)) != info["grid_h"]:
        errors.append("rule mirror changed grid height")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    info = _analyze(grid)
    if info.get("errors"):
        return {}
    return {
        "grid_h": info["grid_h"],
        "grid_w": info["grid_w"],
        "n_targets": info["n_targets"],
        "n_sixes": info["n_sixes"],
    }


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    info = _analyze(grid)
    profile = (
        info["grid_h"],
        info["grid_w"],
        info["n_targets"],
        info["n_sixes"],
    )
    if profile not in _CANONICAL_PROFILES:
        errors.append(f"profile {profile} is outside the four canonical families")
    return errors


def _safe_witness(grid, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    info = _analyze(grid)
    return not info.get("errors") and bool(predicate(info))


SEMANTIC_WITNESSES = {
    "multi_target_row": lambda grid: _safe_witness(
        grid, lambda info: info["max_targets_in_row"] >= 2
    ),
    "edge_touching_target": lambda grid: _safe_witness(
        grid, lambda info: info["has_edge_target"]
    ),
    "boundary_row_target": lambda grid: _safe_witness(
        grid, lambda info: info["has_boundary_row_target"]
    ),
    "target_row_with_six": lambda grid: _safe_witness(
        grid, lambda info: info["has_target_row_with_six"]
    ),
    "vertical_orange_gap_unchanged": lambda grid: _safe_witness(
        grid, lambda info: bool(info["vertical_only_gaps"])
    ),
    "long_horizontal_orange_gap_unchanged": lambda grid: _safe_witness(
        grid, lambda info: bool(info["long_gaps"])
    ),
    "six_gap_unchanged": lambda grid: _safe_witness(
        grid, lambda info: bool(info["six_gaps"])
    ),
    "more_than_four_targets": lambda grid: _safe_witness(
        grid, lambda info: info["n_targets"] > 4
    ),
}


def _rival_one_target_per_row(grid):
    output = [list(row) for row in grid]
    seen_rows: set[int] = set()
    for row, col in _target_centers(grid):
        if row not in seen_rows:
            output[row][col] = 3
            seen_rows.add(row)
    return output


def _rival_interior_only(grid):
    output = [list(row) for row in grid]
    width = len(grid[0])
    for row, col in _target_centers(grid):
        if col not in (1, width - 2):
            output[row][col] = 3
    return output


def _rival_interior_rows_only(grid):
    output = [list(row) for row in grid]
    last_row = len(grid) - 1
    for row, col in _target_centers(grid):
        if row not in (0, last_row):
            output[row][col] = 3
    return output


def _rival_target_rows_without_six(grid):
    output = [list(row) for row in grid]
    for row, col in _target_centers(grid):
        if 6 not in grid[row]:
            output[row][col] = 3
    return output


def _rival_horizontal_or_vertical(grid):
    output = rule_mirror(grid)
    for row, col in _vertical_gap_centers(grid):
        output[row][col] = 3
    return output


def _rival_fill_between_oranges(grid):
    output = rule_mirror(grid)
    for row, left, right in _long_gap_pairs(grid):
        for col in range(left + 1, right):
            if output[row][col] == 0:
                output[row][col] = 3
    return output


def _rival_equal_nonzero_gap(grid):
    output = [list(row) for row in grid]
    for row in range(len(grid)):
        for col in range(1, len(grid[0]) - 1):
            if (
                grid[row][col] == 0
                and grid[row][col - 1] != 0
                and grid[row][col - 1] == grid[row][col + 1]
            ):
                output[row][col] = 3
    return output


def _rival_first_four_targets(grid):
    output = [list(row) for row in grid]
    for row, col in _target_centers(grid)[:4]:
        output[row][col] = 3
    return output


SEMANTIC_RIVALS = {
    "one_target_per_row": _rival_one_target_per_row,
    "interior_only": _rival_interior_only,
    "interior_rows_only": _rival_interior_rows_only,
    "target_rows_without_six": _rival_target_rows_without_six,
    "horizontal_or_vertical": _rival_horizontal_or_vertical,
    "fill_between_oranges": _rival_fill_between_oranges,
    "equal_nonzero_gap": _rival_equal_nonzero_gap,
    "first_four_targets": _rival_first_four_targets,
}
WITNESS_RIVALS = {
    "multi_target_row": ["one_target_per_row"],
    "edge_touching_target": ["interior_only"],
    "boundary_row_target": ["interior_rows_only"],
    "target_row_with_six": ["target_rows_without_six"],
    "vertical_orange_gap_unchanged": ["horizontal_or_vertical"],
    "long_horizontal_orange_gap_unchanged": ["fill_between_oranges"],
    "six_gap_unchanged": ["equal_nonzero_gap"],
    "more_than_four_targets": ["first_four_targets"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # The public pairs contain no 6-0-6 gap, so this color-blind endpoint rule
    # is answer-equivalent there. Profile 2 supplies the generated refuter.
    "equal_nonzero_gap": _rival_equal_nonzero_gap,
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is malformed")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"pair {index} input is unlawful: {errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"pair {index} output disagrees with the horizontal-gap rule")
    if reasons:
        return reasons

    required = {
        "multi-target row": lambda info: info["max_targets_in_row"] >= 2,
        "edge-touching target": lambda info: info["has_edge_target"],
        "boundary-row target": lambda info: info["has_boundary_row_target"],
        "target row containing a 6": lambda info: info["has_target_row_with_six"],
        "vertical orange gap": lambda info: bool(info["vertical_only_gaps"]),
        "long horizontal orange gap": lambda info: bool(info["long_gaps"]),
        "6-0-6 gap": lambda info: bool(info["six_gaps"]),
        "more than four targets": lambda info: info["n_targets"] > 4,
    }
    demo_info = [_analyze(pair["input"]) for pair in demos]
    for label, predicate in required.items():
        if not any(predicate(info) for info in demo_info):
            reasons.append(f"demos omit a {label} counterexample")

    for name, competitor in LESSON_COMPETITORS.items():
        fits_demos = all(
            competitor(pair["input"]) == pair["output"] for pair in demos
        )
        if fits_demos and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"demos remain compatible with competitor {name!r}, which changes the query answer"
            )
    return reasons
