"""Cue-selected satellite-count X-stamping family for ``d02691ffb818``.

The exact canonical default stamps a radius-one orange X at every blue marker.
The alternative first selects the blue marker nearest the red cue, measures the
number of green cardinal satellites around that marker, then uses that measured
count as the diagonal X radius for every blue marker.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable


TASK_ID = "d02691ffb818"
RADIUS_RULES = ("fixed_one", "cue_satellite_count")
DEFAULT_RULE = RADIUS_RULES[0]
_HERE = Path(__file__).resolve().parent
_PROGRAM_PATHS = {
    "fixed_one": _HERE / "canonical.rkt",
    "cue_satellite_count": _HERE / "cue_satellite_count.rkt",
}
_PROGRAMS = {name: path.read_text(encoding="utf-8") for name, path in _PROGRAM_PATHS.items()}

# height, width, marker_count, selected_radius, anchor, cue_distance,
# include_border_marker, include_close_pair
_DEMO_PROFILES = (
    (10, 12, 5, 2, "nw", 4, True, False),
    (12, 15, 6, 3, "se", 2, False, True),
    (14, 18, 7, 4, "center", 3, True, False),
    (16, 18, 8, 2, "north", 4, False, True),
    (18, 21, 9, 3, "west", 2, True, False),
    (20, 24, 10, 4, "east", 3, False, True),
)
_QUERY_PROFILES = (
    (11, 14, 6, 3, "south", 4, True, False),
    (17, 20, 8, 2, "center", 3, False, True),
    (24, 27, 11, 4, "north", 2, True, False),
    (30, 30, 14, 3, "center", 4, True, True),
)

Grid = list[list[int]]
Cell = tuple[int, int]
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIAGONAL_SIGNS = ((1, 1), (1, -1), (-1, 1), (-1, -1))


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def validate_rule(value: Any) -> str:
    if type(value) is not str:
        raise TypeError("radius_rule must be a string")
    if value not in RADIUS_RULES:
        raise ValueError(f"radius_rule must be one of {list(RADIUS_RULES)}")
    return value


def program_for(radius_rule: Any) -> str:
    return _PROGRAMS[validate_rule(radius_rule)]


def _rng(seed: int, stream: str, index: int) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}|cue-radius-v1|{seed}|{stream}|{index}".encode("utf-8")
    ).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _manhattan(a: Cell, b: Cell) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _chebyshev(a: Cell, b: Cell) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def _anchor(name: str, height: int, width: int, rng: random.Random) -> Cell:
    bases = {
        "nw": (2, 2),
        "se": (height - 3, width - 3),
        "center": (height // 2, width // 2),
        "north": (2, width // 2),
        "south": (height - 3, width // 2),
        "west": (height // 2, 2),
        "east": (height // 2, width - 3),
    }
    row, col = bases[name]
    jitter = [(0, 0), (0, 1), (1, 0), (0, -1), (-1, 0)]
    rng.shuffle(jitter)
    for dr, dc in jitter:
        rr, cc = row + dr, col + dc
        if 1 <= rr < height - 1 and 1 <= cc < width - 1:
            return rr, cc
    raise RuntimeError("could not place selected marker")


def _cue_for(selected: Cell, distance: int, height: int, width: int, rng: random.Random) -> Cell:
    candidates: list[Cell] = []
    for dr in range(-distance, distance + 1):
        remaining = distance - abs(dr)
        for dc in ({remaining, -remaining} if remaining else {0}):
            row, col = selected[0] + dr, selected[1] + dc
            if 0 <= row < height and 0 <= col < width and (row, col) != selected:
                candidates.append((row, col))
    if not candidates:
        raise RuntimeError("could not place cue")
    center = ((height - 1) / 2, (width - 1) / 2)
    best_score = max(abs(r - center[0]) + abs(c - center[1]) for r, c in candidates)
    best = [p for p in candidates if abs(p[0] - center[0]) + abs(p[1] - center[1]) == best_score]
    return rng.choice(best)


def _valid_marker_candidate(
    cell: Cell,
    markers: list[Cell],
    cue: Cell,
    selected_distance: int,
    height: int,
    width: int,
) -> bool:
    row, col = cell
    if not (1 <= row < height - 1 and 1 <= col < width - 1):
        return False
    if cell == cue or _manhattan(cell, cue) <= selected_distance:
        return False
    return all(_chebyshev(cell, other) >= 3 for other in markers)


def _add_boundary_marker(
    markers: list[Cell], cue: Cell, selected_distance: int, height: int, width: int
) -> None:
    candidates = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
        if (row, col) != cue
        if _manhattan((row, col), cue) > selected_distance
        if all(_chebyshev((row, col), other) >= 3 for other in markers)
        if sum(
            0 <= row + dr < height and 0 <= col + dc < width
            for dr, dc in _CARDINAL
        ) >= 2
    ]
    if not candidates:
        raise RuntimeError("could not place boundary marker")
    candidates.sort(
        key=lambda p: (
            min(_manhattan(p, other) for other in markers),
            _manhattan(p, cue),
            p,
        ),
        reverse=True,
    )
    markers.append(candidates[0])


def _add_close_pair(
    markers: list[Cell], cue: Cell, selected_distance: int, height: int, width: int, rng: random.Random
) -> None:
    selected = markers[0]
    deltas = [(0, 3), (0, -3), (3, 0), (-3, 0), (2, 2), (2, -2), (-2, 2), (-2, -2)]
    rng.shuffle(deltas)
    for dr, dc in deltas:
        candidate = selected[0] + dr, selected[1] + dc
        if _valid_marker_candidate(candidate, markers, cue, selected_distance, height, width):
            markers.append(candidate)
            return
    raise RuntimeError("could not place close marker pair")


def _fill_markers(
    markers: list[Cell],
    target: int,
    cue: Cell,
    selected_distance: int,
    height: int,
    width: int,
    rng: random.Random,
) -> None:
    pool = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
        if _valid_marker_candidate((row, col), markers, cue, selected_distance, height, width)
    ]
    while len(markers) < target:
        viable = [
            cell
            for cell in pool
            if cell not in markers
            and _valid_marker_candidate(cell, markers, cue, selected_distance, height, width)
        ]
        if not viable:
            raise RuntimeError(f"could not place {target} markers on {height}x{width}")
        score = max(min(_manhattan(cell, other) for other in markers) for cell in viable)
        best = [cell for cell in viable if min(_manhattan(cell, other) for other in markers) == score]
        rng.shuffle(best)
        markers.append(best[0])


def _available_directions(marker: Cell, occupied: set[Cell], height: int, width: int) -> list[tuple[int, int]]:
    result = []
    for dr, dc in _CARDINAL:
        cell = marker[0] + dr, marker[1] + dc
        if 0 <= cell[0] < height and 0 <= cell[1] < width and cell not in occupied:
            result.append((dr, dc))
    return result


def _assign_counts(
    markers: list[Cell], selected_radius: int, cue: Cell, height: int, width: int
) -> dict[Cell, int]:
    occupied = set(markers) | {cue}
    available = {
        marker: len(_available_directions(marker, occupied, height, width))
        for marker in markers
    }
    selected = markers[0]
    if available[selected] < selected_radius:
        raise RuntimeError("selected marker lacks enough satellite slots")
    counts = {selected: selected_radius}
    others = [marker for marker in markers if marker != selected]
    for index, marker in enumerate(others):
        desired = (1, 4, 2, 3)[index % 4]
        counts[marker] = min(desired, available[marker])

    row_major = min(markers)
    farthest = min(markers, key=lambda p: (-_manhattan(p, cue), p))
    for marker in (row_major, farthest):
        if marker != selected and counts[marker] == selected_radius:
            choices = [n for n in (4, 2, 3, 1) if n <= available[marker] and n != selected_radius]
            counts[marker] = choices[0]

    four_candidates = [m for m in others if available[m] >= 4 and m not in {row_major, farthest}]
    if not four_candidates:
        four_candidates = [m for m in others if available[m] >= 4]
    if not four_candidates:
        raise RuntimeError("scene lacks a four-satellite distractor")
    four_marker = four_candidates[0]
    counts[four_marker] = 4

    one_candidates = [m for m in others if m != four_marker and m not in {row_major, farthest}]
    if not one_candidates:
        one_candidates = [m for m in others if m != four_marker]
    if not one_candidates:
        raise RuntimeError("scene lacks a one-satellite distractor")
    counts[one_candidates[0]] = 1

    if marker := (farthest if farthest != selected else None):
        if counts[marker] == selected_radius:
            choices = [n for n in (4, 2, 3, 1) if n <= available[marker] and n != selected_radius]
            counts[marker] = choices[0]
    return counts


def _scene(seed: int, stream: str, index: int, profile: tuple[Any, ...]) -> Grid:
    height, width, marker_count, selected_radius, anchor_name, cue_distance, boundary, close_pair = profile
    rng = _rng(seed, stream, index)
    selected = _anchor(anchor_name, height, width, rng)
    cue = _cue_for(selected, cue_distance, height, width, rng)
    markers = [selected]
    if close_pair:
        _add_close_pair(markers, cue, cue_distance, height, width, rng)
    if boundary:
        _add_boundary_marker(markers, cue, cue_distance, height, width)
    _fill_markers(markers, marker_count, cue, cue_distance, height, width, rng)
    counts = _assign_counts(markers, selected_radius, cue, height, width)

    grid = [[0 for _ in range(width)] for _ in range(height)]
    for row, col in markers:
        grid[row][col] = 1
    grid[cue[0]][cue[1]] = 2
    occupied = set(markers) | {cue}
    for marker in markers:
        directions = _available_directions(marker, occupied, height, width)
        rng.shuffle(directions)
        selected_directions = directions[: counts[marker]]
        if len(selected_directions) != counts[marker]:
            raise RuntimeError("could not place requested satellite count")
        for dr, dc in selected_directions:
            cell = marker[0] + dr, marker[1] + dc
            if cell in occupied:
                raise RuntimeError("satellite collision")
            occupied.add(cell)
            grid[cell[0]][cell[1]] = 3

    analysis = analyze_input(grid)
    if analysis["errors"]:
        raise RuntimeError("constructed invalid scene: " + "; ".join(analysis["errors"]))
    if analysis["selected_marker"] != selected or analysis["selected_radius"] != selected_radius:
        raise RuntimeError("constructed cue dependency does not match profile")
    return grid


def episode_inputs(seed: int, demos: int = 3, queries: int = 4) -> dict[str, list[Grid]]:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 2, 6)
    queries = _integer("queries", queries, 1, 4)
    train = [_scene(seed, "demo", i, profile) for i, profile in enumerate(_DEMO_PROFILES)]
    test = [_scene(seed, "query", i, profile) for i, profile in enumerate(_QUERY_PROFILES)]
    all_inputs = train + test
    keys = [json.dumps(grid, separators=(",", ":")) for grid in all_inputs]
    if len(keys) != len(set(keys)):
        raise RuntimeError("constructed parametric inputs are not distinct")
    return {"train": copy.deepcopy(train[:demos]), "test": copy.deepcopy(test[:queries])}


def analyze_input(grid: Grid) -> dict[str, Any]:
    if (
        type(grid) is not list
        or not grid
        or type(grid[0]) is not list
        or not grid[0]
        or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)
        or any(type(cell) is not int or cell not in (0, 1, 2, 3) for row in grid for cell in row)
    ):
        return {"errors": ["grid must be a rectangular exact-integer grid using colors 0,1,2,3"]}
    height, width = len(grid), len(grid[0])
    markers = sorted(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 1
    )
    cue_cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    ]
    greens = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 3
    }
    errors: list[str] = []
    if len(markers) < 2:
        errors.append("at least two blue markers are required")
    if len(cue_cells) != 1:
        errors.append("exactly one red cue is required")
    cue = cue_cells[0] if len(cue_cells) == 1 else None
    satellite_counts: dict[Cell, int] = {}
    claimed_greens: set[Cell] = set()
    for marker in markers:
        adjacent = {
            (marker[0] + dr, marker[1] + dc)
            for dr, dc in _CARDINAL
            if 0 <= marker[0] + dr < height
            and 0 <= marker[1] + dc < width
            and grid[marker[0] + dr][marker[1] + dc] == 3
        }
        satellite_counts[marker] = len(adjacent)
        claimed_greens |= adjacent
        if not 1 <= len(adjacent) <= 4:
            errors.append(f"marker {marker} must have 1..4 cardinal satellites")
    if claimed_greens != greens:
        errors.append("every green satellite must be cardinally adjacent to a marker")
    for green in greens:
        owners = [marker for marker in markers if _manhattan(green, marker) == 1]
        if len(owners) != 1:
            errors.append(f"green satellite {green} must belong to exactly one marker")
    nearest_markers: list[Cell] = []
    selected_marker = None
    selected_radius = None
    cue_distance = None
    if cue is not None and markers:
        cue_distance = min(_manhattan(marker, cue) for marker in markers)
        nearest_markers = [marker for marker in markers if _manhattan(marker, cue) == cue_distance]
        if len(nearest_markers) != 1:
            errors.append("red cue must have a unique nearest blue marker")
        else:
            selected_marker = nearest_markers[0]
            selected_radius = satellite_counts.get(selected_marker)
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "markers": markers,
        "cue_cells": cue_cells,
        "cue": cue,
        "cue_distance": cue_distance,
        "nearest_markers": nearest_markers,
        "selected_marker": selected_marker,
        "selected_radius": selected_radius,
        "satellite_counts": satellite_counts,
        "green_cells": sorted(greens),
    }


def _stamp(output: Grid, marker: Cell, radius: int) -> None:
    height, width = len(output), len(output[0])
    cells = [marker] + [
        (marker[0] + sr * radius, marker[1] + sc * radius)
        for sr, sc in _DIAGONAL_SIGNS
    ]
    for row, col in cells:
        if 0 <= row < height and 0 <= col < width:
            output[row][col] = 7


def _solve_radius(grid: Grid, radius: int, markers: list[Cell] | None = None) -> Grid:
    analysis = analyze_input(grid)
    if analysis["errors"]:
        raise ValueError("invalid parametric input: " + "; ".join(analysis["errors"]))
    output = [[0 for _ in row] for row in grid]
    for marker in analysis["markers"] if markers is None else markers:
        _stamp(output, marker, radius)
    return output


def solve(grid: Grid, radius_rule: Any) -> Grid:
    rule = validate_rule(radius_rule)
    analysis = analyze_input(grid)
    if analysis["errors"]:
        raise ValueError("invalid parametric input: " + "; ".join(analysis["errors"]))
    radius = 1 if rule == "fixed_one" else analysis["selected_radius"]
    return _solve_radius(grid, radius)


def _farthest_marker(analysis: dict[str, Any]) -> Cell:
    cue = analysis["cue"]
    return min(analysis["markers"], key=lambda p: (-_manhattan(p, cue), p))


def _solve_candidate(grid: Grid, name: str) -> Grid:
    analysis = analyze_input(grid)
    if analysis["errors"]:
        raise ValueError("invalid parametric input: " + "; ".join(analysis["errors"]))
    counts = analysis["satellite_counts"]
    if name in ("fixed_one", "cue_satellite_count"):
        return solve(grid, name)
    if name.startswith("fixed_"):
        return _solve_radius(grid, int(name.split("_")[1]))
    if name == "global_max_count":
        return _solve_radius(grid, max(counts.values()))
    if name == "farthest_cue_count":
        return _solve_radius(grid, counts[_farthest_marker(analysis)])
    if name == "row_major_count":
        return _solve_radius(grid, counts[min(analysis["markers"])])
    if name == "cue_distance":
        return _solve_radius(grid, analysis["cue_distance"])
    if name == "selected_only":
        return _solve_radius(grid, analysis["selected_radius"], [analysis["selected_marker"]])
    if name == "per_marker_count":
        output = [[0 for _ in row] for row in grid]
        for marker in analysis["markers"]:
            _stamp(output, marker, counts[marker])
        return output
    raise ValueError(f"unknown candidate: {name}")


CANDIDATE_RULES = (
    "fixed_one",
    "cue_satellite_count",
    "fixed_2",
    "fixed_3",
    "fixed_4",
    "global_max_count",
    "farthest_cue_count",
    "row_major_count",
    "cue_distance",
    "selected_only",
    "per_marker_count",
)


def solve_candidate(grid: Grid, name: Any) -> Grid:
    if type(name) is not str:
        raise TypeError("candidate name must be a string")
    if name not in CANDIDATE_RULES:
        raise ValueError(f"unknown candidate: {name}")
    return _solve_candidate(copy.deepcopy(grid), name)


def _generic_program(name: str) -> str:
    if name == "fixed_one":
        return program_for("fixed_one")
    if name == "cue_satellite_count":
        return program_for("cue_satellite_count")
    radius_expr = {
        "fixed_2": "2",
        "fixed_3": "3",
        "fixed_4": "4",
        "global_max_count": "(max-list (map satellite-count markers))",
        "farthest_cue_count": "(satellite-count farthest-marker)",
        "row_major_count": "(satellite-count row-major-marker)",
        "cue_distance": "(distance selected-marker cue)",
        "selected_only": "selected-radius",
        "per_marker_count": "(satellite-count p)",
    }[name]
    markers_expr = "(list selected-marker)" if name == "selected_only" else "markers"
    return f"""(rule!
  (let ()
    (define markers (find-color g 1))
    (define cue (first (find-color g 2)))
    (define (distance p q)
      (+ (abs (- (first p) (first q)))
         (abs (- (second p) (second q)))))
    (define (row-key p) (+ (* 100 (first p)) (second p)))
    (define (satellite-count p)
      (length
        (filter
          (lambda (q)
            (and (in-bounds? (first q) (second q) (rows g) (cols g))
                 (= (at g (first q) (second q)) 3)))
          (list
            (list (- (first p) 1) (second p))
            (list (+ (first p) 1) (second p))
            (list (first p) (- (second p) 1))
            (list (first p) (+ (second p) 1))))))
    (define selected-marker
      (first (sort-by markers (lambda (p) (+ (* 10000 (distance p cue)) (row-key p))))))
    (define farthest-marker
      (first (sort-by markers (lambda (p) (+ (* -10000 (distance p cue)) (row-key p))))))
    (define row-major-marker (first (sort-by markers row-key)))
    (define selected-radius (satellite-count selected-marker))
    (for/fold ((out (empty-grid (rows g) (cols g) 0)))
              ((p (in-list {markers_expr})))
      (let ((radius {radius_expr}))
        (paint-cells
          out
          (filter
            (lambda (q) (in-bounds? (first q) (second q) (rows g) (cols g)))
            (list
              p
              (list (+ (first p) radius) (+ (second p) radius))
              (list (+ (first p) radius) (- (second p) radius))
              (list (- (first p) radius) (+ (second p) radius))
              (list (- (first p) radius) (- (second p) radius))))
          7)))))"""


def candidate_program(name: Any) -> str:
    if type(name) is not str:
        raise TypeError("candidate name must be a string")
    if name not in CANDIDATE_RULES:
        raise ValueError(f"unknown candidate: {name}")
    return _generic_program(name)


def generate_episode(
    seed: int,
    radius_rule: Any,
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    rule = validate_rule(radius_rule)
    selected = episode_inputs(seed, demos=demos, queries=queries)
    return {
        "train": [{"input": grid, "output": solve(grid, rule)} for grid in selected["train"]],
        "test": [{"input": grid, "output": solve(grid, rule)} for grid in selected["test"]],
        "program_solution": program_for(rule),
    }


def public_view(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    if type(episode) is not dict or not isinstance(episode.get("train"), list) or not isinstance(episode.get("test"), list):
        raise TypeError("episode must contain train and test lists")
    query_index = _integer("query_index", query_index, 0, len(episode["test"]) - 1)
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }


def public_bytes(public: dict[str, Any]) -> bytes:
    return (
        json.dumps(
            public,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def public_id(public: dict[str, Any]) -> str:
    return hashlib.sha256(public_bytes(public)).hexdigest()
