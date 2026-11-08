"""Generator for ARC task 97c75046 / content hash f5a58a06c0b4.

The canvas is a color-7 field containing one connected color-0 carve and one
color-5 marker.  A boundary cell is a 7-cell cardinally adjacent to zero.
Enumerate maximal straight boundary runs in the authority's order
(horizontal, vertical, down-right diagonal, down-left diagonal), retain runs of
length at least two, and select the run with minimum marker-to-run Manhattan
distance (breaking a distance tie by preferring the longer run).

The endpoint rule is deliberately orientation-sensitive: horizontal/vertical
runs receive the marker at their NEARER endpoint, while diagonal runs receive
it at their FARTHER endpoint.  The old marker cell becomes 7.  Generated
lessons schedule all four orientations in every four consecutive examples, so
"always nearest", "always farthest", and fixed-endpoint shortcuts are visibly
wrong rather than silently fitting the stream.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "f5a58a06c0b4"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "c76d55dfa72e"

SUMMARY = (
    "In a mostly-7 grid, find maximal straight runs of 7-cells that touch the "
    "connected 0-region cardinally. Select the run nearest the single gray(5) "
    "marker, breaking equal run distance by longer length. Move gray to the "
    "nearer endpoint for horizontal/vertical runs but to the farther endpoint "
    "for diagonal runs; restore the old marker cell to 7."
)

INVARIANTS = [
    "the palette is exactly {0,5,7}, with one gray marker",
    "the zero cells form one connected carved region inside a majority 7-field",
    "the marker is not itself touching zero and therefore does not erase a boundary cell",
    "the best straight boundary run is unique under (distance, longer-length) selection",
    "the two selected-run endpoints have unequal marker distances",
    "horizontal/vertical and diagonal endpoint policies are both taught",
]

RUN_KINDS = ("horizontal", "vertical", "diag_down", "diag_up")
ORTHOGONAL_KINDS = frozenset(("horizontal", "vertical"))
DIAGONAL_KINDS = frozenset(("diag_down", "diag_up"))

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile schedule plus difficulty-biased 6..24 generalization",
        "valid": "6..24",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile schedule plus difficulty-biased 6..24 generalization",
        "valid": "6..24",
    },
    "run_kind": {
        "type": "str",
        "default": "four-example schedule: horizontal/vertical/diag_down/diag_up",
        "valid": "|".join(RUN_KINDS),
    },
}

# Four consecutive sample indexes cover every orientation, which is the minimum
# lesson that separates the authority's orthogonal and diagonal endpoint rules.
EXAMPLES_NEEDED = 4
SCHEDULE_PROFILES = RUN_KINDS

# Four of every five ordinary draws use an exact official (h,w,palette) profile;
# one in five generalizes size.  Vertical is a lawful symmetric branch absent
# from the observed official rows, so the strict empirical rate is roughly
# 4/5 * 3/4 = 60%; 20% is a conservative count-backed floor.
MIN_STRICT_FRAC = 0.20

_CANONICAL_PROFILES = ((10, 6), (6, 8), (12, 8), (10, 16))
_CANONICAL_KINDS = frozenset(("horizontal", "diag_down", "diag_up"))
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIRECTIONS = (
    (0, 1, "horizontal"),
    (1, 0, "vertical"),
    (1, 1, "diag_down"),
    (1, -1, "diag_up"),
)


def _shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["every cell must be an integer ARC color from 0 through 9"]
    return []


def _is_boundary(grid: list[list[int]] | tuple, row: int, col: int) -> bool:
    height, width = len(grid), len(grid[0])
    if not (0 <= row < height and 0 <= col < width) or grid[row][col] != 7:
        return False
    return any(
        0 <= row + dr < height
        and 0 <= col + dc < width
        and grid[row + dr][col + dc] == 0
        for dr, dc in _CARDINAL
    )


def _raw_boundary_runs(grid: list[list[int]] | tuple) -> list[dict[str, Any]]:
    """Enumerate runs in exactly the canonical direction/row-major order."""
    height, width = len(grid), len(grid[0])
    runs: list[dict[str, Any]] = []
    for dr, dc, kind in _DIRECTIONS:
        for row in range(height):
            for col in range(width):
                if not _is_boundary(grid, row, col):
                    continue
                if _is_boundary(grid, row - dr, col - dc):
                    continue
                cells: list[tuple[int, int]] = []
                rr, cc = row, col
                while _is_boundary(grid, rr, cc):
                    cells.append((rr, cc))
                    rr += dr
                    cc += dc
                if len(cells) >= 2:
                    runs.append({
                        "cells": cells,
                        "dr": dr,
                        "dc": dc,
                        "kind": kind,
                    })
    return runs


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _shape_errors(grid)
    if errors:
        return {"errors": errors}
    markers = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    ]
    if len(markers) != 1:
        return {"errors": [f"expected exactly one gray marker, found {len(markers)}"]}
    marker = markers[0]

    def distance(cell: tuple[int, int]) -> int:
        return abs(cell[0] - marker[0]) + abs(cell[1] - marker[1])

    runs = _raw_boundary_runs(grid)
    if not runs:
        return {"errors": ["no straight boundary run of length at least two"]}
    for run in runs:
        run["min_distance"] = min(distance(cell) for cell in run["cells"])
        run["length"] = len(run["cells"])
        run["selection_key"] = (run["min_distance"], -run["length"])
        endpoints = (run["cells"][0], run["cells"][-1])
        run["endpoints"] = endpoints
        run["endpoint_distances"] = tuple(distance(cell) for cell in endpoints)

    best_key = min(run["selection_key"] for run in runs)
    tied = [run for run in runs if run["selection_key"] == best_key]
    selected = tied[0]  # same stable-order fallback as the canonical sort
    first, last = selected["endpoints"]
    first_distance, last_distance = selected["endpoint_distances"]
    diagonal = selected["kind"] in DIAGONAL_KINDS
    if diagonal:
        destination = first if first_distance >= last_distance else last
    else:
        destination = first if first_distance <= last_distance else last
    destination_index = "first" if destination == first else "last"
    nearest_cell = min(
        selected["cells"],
        key=lambda cell: (distance(cell), selected["cells"].index(cell)),
    )
    return {
        "errors": [],
        "marker": marker,
        "runs": runs,
        "best_key": best_key,
        "best_tie_count": len(tied),
        "selected": selected,
        "destination": destination,
        "destination_index": destination_index,
        "nearest_cell": nearest_cell,
    }


def _zero_region_connected(grid: list[list[int]] | tuple) -> bool:
    zeros = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 0
    }
    if not zeros:
        return False
    queue = deque([next(iter(zeros))])
    seen = {queue[0]}
    while queue:
        row, col = queue.popleft()
        for dr, dc in _CARDINAL:
            nxt = (row + dr, col + dc)
            if nxt in zeros and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen == zeros


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or rule-hiding boundary-run scenes."""
    errors = _shape_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if not 6 <= height <= 30 or not 6 <= width <= 30:
        errors.append(f"grid dimensions must be in 6..30, found {height}x{width}")

    values = {value for row in grid for value in row}
    if values != {0, 5, 7}:
        errors.append(f"palette must be exactly [0, 5, 7], found {sorted(values)}")
    marker_count = sum(value == 5 for row in grid for value in row)
    if marker_count != 1:
        errors.append(f"expected exactly one gray marker, found {marker_count}")
    zero_count = sum(value == 0 for row in grid for value in row)
    field_count = sum(value in (5, 7) for row in grid for value in row)
    if zero_count < 3:
        errors.append(f"zero carve is too small to define the task, found {zero_count} cells")
    if field_count <= zero_count:
        errors.append(f"field must remain majority 7/5: field={field_count}, zero={zero_count}")
    if zero_count and not _zero_region_connected(grid):
        errors.append("zero carve must be one cardinally connected region")

    markers = [
        (row, col)
        for row, values_row in enumerate(grid)
        for col, value in enumerate(values_row)
        if value == 5
    ]
    if len(markers) == 1:
        row, col = markers[0]
        if any(
            0 <= row + dr < height
            and 0 <= col + dc < width
            and grid[row + dr][col + dc] == 0
            for dr, dc in _CARDINAL
        ):
            errors.append("marker may not touch zero and erase a boundary cell")

    analysis = _analyze(grid)
    errors.extend(analysis.get("errors", []))
    if not analysis.get("errors"):
        if analysis["best_tie_count"] != 1:
            errors.append(
                "best boundary run must be unique under distance/length selection; "
                f"found {analysis['best_tie_count']} tied runs"
            )
        end_distances = analysis["selected"]["endpoint_distances"]
        if end_distances[0] == end_distances[1]:
            errors.append("selected-run endpoint distances must be unequal")
        if analysis["destination"] == analysis["marker"]:
            errors.append("marker must move to a different cell")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Linked empirical manifold: official sizes and observed run branches."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analyze(grid)
    profile = (len(grid), len(grid[0]))
    if profile not in _CANONICAL_PROFILES:
        return [f"dimensions {profile} are outside the four official profiles"]
    if analysis["selected"]["kind"] not in _CANONICAL_KINDS:
        return ["official rows show horizontal or diagonal selection, not vertical"]
    return []


def observe_overrides(grid) -> dict[str, object]:
    """Recover every exact axis from the returned input grid."""
    analysis = _analyze(grid)
    return {
        "grid_h": len(grid) if isinstance(grid, (list, tuple)) else None,
        "grid_w": (
            len(grid[0])
            if isinstance(grid, (list, tuple)) and grid and isinstance(grid[0], (list, tuple))
            else None
        ),
        "run_kind": (
            analysis["selected"]["kind"] if not analysis.get("errors") else None
        ),
    }


def schedule_profile(seed, sample_index, difficulty=None):
    """Every four consecutive examples cover all authority orientations."""
    return RUN_KINDS[sample_index % len(RUN_KINDS)]


def _scheduled_defaults(sample_index: int) -> dict[str, object]:
    defaults: dict[str, object] = {
        "run_kind": RUN_KINDS[sample_index % len(RUN_KINDS)],
    }
    profile_slot = sample_index % 5
    if profile_slot < len(_CANONICAL_PROFILES):
        defaults["grid_h"], defaults["grid_w"] = _CANONICAL_PROFILES[profile_slot]
    return defaults


def _choose_marker_for_run(
    grid: list[list[int]],
    run: list[tuple[int, int]],
    near_start: bool,
    rng,
) -> tuple[int, int]:
    """Choose a varied non-boundary marker position that distinguishes endpoints."""
    first, last = run[0], run[-1]
    preferred = first if near_start else last
    other = last if near_start else first
    height, width = len(grid), len(grid[0])
    candidates: list[tuple[tuple[int, int, int, int], tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 7 or _is_boundary(grid, row, col):
                continue
            preferred_distance = abs(row - preferred[0]) + abs(col - preferred[1])
            other_distance = abs(row - other[0]) + abs(col - other[1])
            if preferred_distance >= other_distance:
                continue
            run_distance = min(
                abs(row - run_row) + abs(col - run_col)
                for run_row, run_col in run
            )
            score = (run_distance, preferred_distance, row, col)
            candidates.append((score, (row, col)))
    if not candidates:
        raise ValueError("no non-boundary marker position distinguishes run endpoints")
    candidates.sort(key=lambda item: item[0])
    best_run_distance = candidates[0][0][0]
    # A small distance envelope keeps the intended run competitive while adding
    # many more lawful marker placements than a single hand-picked coordinate.
    close = [
        cell
        for score, cell in candidates
        if score[0] <= best_run_distance + 2
    ]
    return rng.choice(close)


def _paint_horizontal_carve(
    grid: list[list[int]],
    row0: int,
    col0: int,
    block_height: int,
    block_width: int,
    side: str,
    rng,
) -> list[tuple[int, int]]:
    """Paint a connected jagged carve while preserving one straight target lip."""
    width = len(grid[0])
    target_zero_row = row0 + block_height - 1 if side == "top" else row0
    for row in range(row0, row0 + block_height):
        if row == target_zero_row:
            left_extra = right_extra = 0
        else:
            left_extra = rng.randint(0, col0)
            right_extra = rng.randint(0, width - (col0 + block_width))
        for col in range(
            col0 - left_extra,
            col0 + block_width + right_extra,
        ):
            grid[row][col] = 0
    boundary_row = target_zero_row + (1 if side == "top" else -1)
    return [(boundary_row, col) for col in range(col0, col0 + block_width)]


def _paint_vertical_carve(
    grid: list[list[int]],
    row0: int,
    col0: int,
    block_height: int,
    block_width: int,
    side: str,
    rng,
) -> list[tuple[int, int]]:
    """Paint a connected jagged carve while preserving one straight target lip."""
    height = len(grid)
    target_zero_col = col0 + block_width - 1 if side == "left" else col0
    for col in range(col0, col0 + block_width):
        if col == target_zero_col:
            top_extra = bottom_extra = 0
        else:
            top_extra = rng.randint(0, row0)
            bottom_extra = rng.randint(0, height - (row0 + block_height))
        for row in range(
            row0 - top_extra,
            row0 + block_height + bottom_extra,
        ):
            grid[row][col] = 0
    boundary_col = target_zero_col + (1 if side == "left" else -1)
    return [(row, boundary_col) for row in range(row0, row0 + block_height)]


def _build_horizontal(height: int, width: int, near_start: bool, rng) -> list[list[int]]:
    grid = full_grid(height, width, 7)
    block_height = rng.randint(2, min(height - 2, max(2, height // 2)))
    block_width = rng.randint(4, min(width - 2, max(4, (2 * width) // 3)))
    col0 = rng.randint(1, width - block_width - 1)
    side = rng.choice(("top", "bottom"))
    row0 = 0 if side == "top" else height - block_height
    run = _paint_horizontal_carve(
        grid, row0, col0, block_height, block_width, side, rng
    )
    marker_row, marker_col = _choose_marker_for_run(grid, run, near_start, rng)
    grid[marker_row][marker_col] = 5
    return grid


def _build_vertical(height: int, width: int, near_start: bool, rng) -> list[list[int]]:
    grid = full_grid(height, width, 7)
    block_height = rng.randint(4, min(height - 2, max(4, (2 * height) // 3)))
    block_width = rng.randint(2, min(width - 2, max(2, width // 2)))
    row0 = rng.randint(1, height - block_height - 1)
    side = rng.choice(("left", "right"))
    col0 = 0 if side == "left" else width - block_width
    run = _paint_vertical_carve(
        grid, row0, col0, block_height, block_width, side, rng
    )
    marker_row, marker_col = _choose_marker_for_run(grid, run, near_start, rng)
    grid[marker_row][marker_col] = 5
    return grid


def _carve_triangle(
    grid: list[list[int]],
    depth: int,
    corner: str,
) -> None:
    height, width = len(grid), len(grid[0])
    for offset in range(depth):
        run = depth - offset
        for step in range(run):
            if corner == "bottom_left":
                row, col = height - 1 - offset, step
            elif corner == "bottom_right":
                row, col = height - 1 - offset, width - 1 - step
            elif corner == "top_left":
                row, col = offset, step
            else:
                row, col = offset, width - 1 - step
            grid[row][col] = 0


def _choose_diagonal_marker(
    grid: list[list[int]],
    kind: str,
    near_start: bool,
    rng,
) -> tuple[int, int]:
    matching = [run for run in _raw_boundary_runs(grid) if run["kind"] == kind]
    if len(matching) != 1:
        raise ValueError(f"triangle produced {len(matching)} {kind} runs instead of one")
    return _choose_marker_for_run(grid, matching[0]["cells"], near_start, rng)


def _build_diagonal(
    height: int,
    width: int,
    kind: str,
    near_start: bool,
    rng,
) -> list[list[int]]:
    grid = full_grid(height, width, 7)
    depth = rng.randint(3, min(height, width) - 3)
    if kind == "diag_down":
        corner = rng.choice(("bottom_left", "top_right"))
    else:
        corner = rng.choice(("bottom_right", "top_left"))
    _carve_triangle(grid, depth, corner)
    marker_row, marker_col = _choose_diagonal_marker(
        grid, kind, near_start, rng
    )
    grid[marker_row][marker_col] = 5
    return grid


def _build_scene(
    height: int,
    width: int,
    kind: str,
    near_start: bool,
    rng,
) -> list[list[int]]:
    for _attempt in range(60):
        if kind == "horizontal":
            grid = _build_horizontal(height, width, near_start, rng)
        elif kind == "vertical":
            grid = _build_vertical(height, width, near_start, rng)
        else:
            grid = _build_diagonal(height, width, kind, near_start, rng)
        analysis = _analyze(grid)
        if (
            not self_check(grid)
            and not analysis.get("errors")
            and analysis["selected"]["kind"] == kind
        ):
            return [row[:] for row in grid]
    raise ValueError(
        f"could not realize unique {kind} boundary selection in {height}x{width}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic lawful input; Racket remains output authority."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    effective_overrides = _scheduled_defaults(sample_index)
    for name, value in overrides.items():
        if value is not None:
            effective_overrides[name] = value
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    height = ctx.draw_int_diff("grid_h", 6, 24)
    width = ctx.draw_int_diff("grid_w", 6, 24)
    kind = ctx.draw_choice("run_kind", RUN_KINDS)
    # Fix endpoint-role coverage independently of random geometry: every four
    # consecutive examples contain two first-endpoint and two last-endpoint
    # answers.  Diagonal runs invert marker-nearness because their answer is the
    # farther endpoint.
    destination_is_first = sample_index % 2 == 0
    near_start = (
        destination_is_first
        if kind in ORTHOGONAL_KINDS
        else not destination_is_first
    )
    grid = _build_scene(height, width, kind, near_start, ctx.draw_rng("layout"))
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError("constructed invalid boundary-run scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    if observed != {"grid_h": height, "grid_w": width, "run_kind": kind}:
        raise ValueError(
            f"constructed scene does not expose requested axes: requested="
            f"{(height, width, kind)!r}, observed={observed!r}"
        )
    return [row[:] for row in grid]


# ---------------------------------------------------------------------------
# Task-linked semantic contract and explicit rival rules
# ---------------------------------------------------------------------------

def _move_marker(grid, destination: tuple[int, int]) -> list[list[int]]:
    output = [list(row) for row in grid]
    marker = next(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    )
    output[marker[0]][marker[1]] = 7
    output[destination[0]][destination[1]] = 5
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Diagnostic Python mirror only; generation never uses it as authority."""
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return [list(row) for row in grid]
    return _move_marker(grid, analysis["destination"])


def _nearest_endpoint_for_all(grid) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return [list(row) for row in grid]
    endpoints = analysis["selected"]["endpoints"]
    distances = analysis["selected"]["endpoint_distances"]
    destination = endpoints[0] if distances[0] <= distances[1] else endpoints[1]
    return _move_marker(grid, destination)


def _farthest_endpoint_for_all(grid) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return [list(row) for row in grid]
    endpoints = analysis["selected"]["endpoints"]
    distances = analysis["selected"]["endpoint_distances"]
    destination = endpoints[0] if distances[0] >= distances[1] else endpoints[1]
    return _move_marker(grid, destination)


def _first_endpoint_always(grid) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return [list(row) for row in grid]
    return _move_marker(grid, analysis["selected"]["endpoints"][0])


def _last_endpoint_always(grid) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return [list(row) for row in grid]
    return _move_marker(grid, analysis["selected"]["endpoints"][1])


def _nearest_boundary_cell(grid) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return [list(row) for row in grid]
    return _move_marker(grid, analysis["nearest_cell"])


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "nearest_endpoint_for_all": _nearest_endpoint_for_all,
    "farthest_endpoint_for_all": _farthest_endpoint_for_all,
    "first_endpoint_always": _first_endpoint_always,
    "last_endpoint_always": _last_endpoint_always,
    "nearest_boundary_cell": _nearest_boundary_cell,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _witness_kind(grid, kind: str) -> bool:
    analysis = _analyze(grid)
    return (
        not analysis.get("errors")
        and analysis["selected"]["kind"] == kind
        and analysis["selected"]["endpoint_distances"][0]
        != analysis["selected"]["endpoint_distances"][1]
    )


def _witness_destination(grid, endpoint: str) -> bool:
    analysis = _analyze(grid)
    return not analysis.get("errors") and analysis["destination_index"] == endpoint


def _witness_nearest_cell_differs(grid) -> bool:
    analysis = _analyze(grid)
    return (
        not analysis.get("errors")
        and analysis["nearest_cell"] != analysis["destination"]
    )


SEMANTIC_WITNESSES = {
    "horizontal_nearer_endpoint": lambda grid: _witness_kind(grid, "horizontal"),
    "vertical_nearer_endpoint": lambda grid: _witness_kind(grid, "vertical"),
    "diag_down_farther_endpoint": lambda grid: _witness_kind(grid, "diag_down"),
    "diag_up_farther_endpoint": lambda grid: _witness_kind(grid, "diag_up"),
    "destination_is_first_endpoint": lambda grid: _witness_destination(grid, "first"),
    "destination_is_last_endpoint": lambda grid: _witness_destination(grid, "last"),
    "endpoint_not_nearest_boundary_cell": _witness_nearest_cell_differs,
}

WITNESS_RIVALS = {
    "horizontal_nearer_endpoint": ["farthest_endpoint_for_all"],
    "vertical_nearer_endpoint": ["farthest_endpoint_for_all"],
    "diag_down_farther_endpoint": ["nearest_endpoint_for_all"],
    "diag_up_farther_endpoint": ["nearest_endpoint_for_all"],
    "destination_is_first_endpoint": ["last_endpoint_always"],
    "destination_is_last_endpoint": ["first_endpoint_always"],
    "endpoint_not_nearest_boundary_cell": ["nearest_boundary_cell"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations that eliminate every named plausible shortcut."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    analyses: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} is outside the teaching grammar: {errors[:2]}")
            continue
        expected = rule_mirror(demo["input"])
        if expected != demo["output"]:
            reasons.append(f"demo {index} output disagrees with the authority mirror")
        analyses.append(_analyze(demo["input"]))

    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query must contain input and output")
        return reasons
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query is outside the teaching grammar: {query_errors[:2]}")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output disagrees with the authority mirror")

    if analyses:
        observed_kinds = {analysis["selected"]["kind"] for analysis in analyses}
        missing = sorted(set(RUN_KINDS) - observed_kinds)
        if missing:
            reasons.append(f"demonstrations miss scheduled run branches: {missing}")
        observed_destinations = {
            analysis["destination_index"] for analysis in analyses
        }
        if observed_destinations != {"first", "last"}:
            reasons.append(
                "demonstrations do not show both first- and last-endpoint destinations"
            )
        dimensions = {
            (len(demo["input"]), len(demo["input"][0]))
            for demo in demos
            if isinstance(demo, dict) and demo.get("input")
        }
        if len(dimensions) < 2:
            reasons.append("demonstrations do not vary grid dimensions")

    if not query_errors:
        for name, competitor in LESSON_COMPETITORS.items():
            survives = all(
                competitor(demo["input"]) == demo["output"]
                for demo in demos
                if isinstance(demo, dict) and "input" in demo and "output" in demo
            )
            if survives:
                rival_query = competitor(query["input"])
                relation = (
                    "answers the query differently"
                    if rival_query != query["output"]
                    else "also matches this query"
                )
                reasons.append(
                    f"named competitor survives every demonstration and {relation}: {name}"
                )
    return reasons
