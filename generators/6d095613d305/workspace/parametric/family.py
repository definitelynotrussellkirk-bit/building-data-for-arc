"""Matched-input parametric polyline family for ARC task 6d095613d305.

The canonical setting traces both row-major waypoint chains with horizontal-first
bends and marks shared cells 9.  Alternative settings first build those exact
input-derived traces, then recolor the uniquely longer or shorter trace to 8
away from intersections.  Native qualification re-executes all labels in Racket.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import random
from typing import Iterable

TASK_ID = "6d095613d305"
MODES = ("canonical", "longer", "shorter")
SETTINGS = tuple({"path_emphasis": mode} for mode in MODES)
DEMO_SIZES = ((10, 12), (12, 15), (14, 17), (16, 19), (18, 22), (21, 25))
QUERY_SIZES = ((30, 30), (24, 30), (30, 24), (27, 29))


def _settings(settings) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"path_emphasis"}
        or type(settings["path_emphasis"]) is not str
        or settings["path_emphasis"] not in MODES
    ):
        raise ValueError("settings must be exactly path_emphasis=canonical|longer|shorter")
    return settings["path_emphasis"]


def _integer(value, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _grid(value) -> list[list[int]]:
    if type(value) is not list or not 1 <= len(value) <= 30:
        raise ValueError("grid must have 1..30 list rows")
    if type(value[0]) is not list or not 1 <= len(value[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(value[0])
    result = []
    for row in value:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular list-of-lists")
        if any(type(cell) is not int or not 0 <= cell <= 9 for cell in row):
            raise ValueError("grid cells must be exact integer ARC colors 0..9")
        result.append(list(row))
    return result


def _color_points(grid: list[list[int]]) -> list[tuple[int, list[tuple[int, int]]]]:
    colors = sorted({cell for row in grid for cell in row if cell != 0})
    return [
        (color, [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color])
        for color in colors
    ]


def _axis(start: int, end: int) -> range:
    if start == end:
        return range(0)
    step = 1 if end > start else -1
    return range(start + step, end + step, step)


def trace(points: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    ordered = sorted(points)
    if not ordered:
        return ()
    cells = [ordered[0]]
    for (r1, c1), (r2, c2) in zip(ordered, ordered[1:]):
        cells.extend((r1, c) for c in _axis(c1, c2))
        cells.extend((r, c2) for r in _axis(r1, r2))
    return tuple(dict.fromkeys(cells))


def canonical_solve(grid) -> list[list[int]]:
    rows = _grid(grid)
    out = [[0 for _ in row] for row in rows]
    for color, points in _color_points(rows):
        for r, c in trace(points):
            out[r][c] = color if out[r][c] == 0 else 9
    return out


def solve_with_selected_color(grid, selected_color: int) -> list[list[int]]:
    rows = _grid(grid)
    pairs = dict(_color_points(rows))
    if type(selected_color) is not int or selected_color not in pairs:
        raise ValueError("selected_color must name an input path")
    out = canonical_solve(rows)
    for r, c in trace(pairs[selected_color]):
        if out[r][c] != 9:
            out[r][c] = 8
    return out


def analyze(grid) -> dict:
    try:
        rows = _grid(grid)
    except (TypeError, ValueError) as exc:
        return {"valid_for_all_settings": False, "errors": [str(exc)]}
    errors: list[str] = []
    colors = sorted({cell for row in rows for cell in row if cell != 0})
    if len(colors) != 2 or any(color in {8, 9} for color in colors):
        errors.append("input needs exactly two nonzero colors excluding 8 and 9")
    color_points = _color_points(rows)
    if len(color_points) != 2:
        return {"valid_for_all_settings": False, "errors": errors, "path_colors": colors}
    for color, points in color_points:
        if not 3 <= len(points) <= 6:
            errors.append(f"color {color} needs 3..6 waypoints")
        ordered = sorted(points)
        if not any(a[0] != b[0] for a, b in zip(ordered, ordered[1:])):
            errors.append(f"color {color} lacks vertical movement")
        if not any(a[1] != b[1] for a, b in zip(ordered, ordered[1:])):
            errors.append(f"color {color} lacks horizontal movement")
    traces = [trace(points) for _, points in color_points]
    lengths = [len(cells) for cells in traces]
    if lengths[0] == lengths[1]:
        errors.append("trace lengths must be unique")
    overlap = len(set(traces[0]) & set(traces[1]))
    if overlap < 1:
        errors.append("paths must intersect")
    longer_i = 0 if lengths[0] > lengths[1] else 1
    shorter_i = 1 - longer_i
    canonical = canonical_solve(rows)
    outputs = []
    if not errors:
        outputs = [
            canonical,
            solve_with_selected_color(rows, colors[longer_i]),
            solve_with_selected_color(rows, colors[shorter_i]),
        ]
        if len({repr(output) for output in outputs}) != len(SETTINGS):
            errors.append("setting outputs are not distinct")
    occupied = sum(value != 0 for row in canonical for value in row)
    return {
        "valid_for_all_settings": not errors,
        "errors": errors,
        "path_colors": colors,
        "trace_lengths": lengths,
        "longer_color": colors[longer_i],
        "shorter_color": colors[shorter_i],
        "overlap_cells": overlap,
        "canonical_occupied": occupied,
        "setting_outputs_distinct": not errors and len({repr(output) for output in outputs}) == 3,
    }


def solve(grid, settings) -> list[list[int]]:
    mode = _settings(settings)
    facts = analyze(grid)
    if not facts.get("valid_for_all_settings"):
        raise ValueError("invalid scene: " + "; ".join(facts.get("errors", [])))
    if mode == "canonical":
        return canonical_solve(grid)
    selected = facts["longer_color"] if mode == "longer" else facts["shorter_color"]
    return solve_with_selected_color(grid, selected)


def _derived_program(mode: str, *, forced: str | None = None) -> str:
    if mode not in {"longer", "shorter"}:
        raise ValueError(mode)
    comparison = ">" if mode == "longer" else "<"
    if forced == "first":
        selected = "p1"
    elif forced == "second":
        selected = "p2"
    else:
        selected = f"(if ({comparison} (length p1) (length p2)) p1 p2)"
    return f"""(rule!
  (let ((dummy 0))
    (define (step-range a b)
      (if (<= a b) (range a (+ b 1)) (reverse (range b (+ a 1)))))
    (define (trace points)
      (if (empty? points)
          (list)
          (let loop ([remaining (rest points)] [prev (first points)] [out (list (first points))])
            (if (empty? remaining)
                (reverse (foldl (lambda (p acc) (if (member p acc) acc (cons p acc))) (list) (reverse out)))
                (let* ((next (first remaining))
                       (r1 (first prev)) (c1 (second prev))
                       (r2 (first next)) (c2 (second next))
                       (hpart (map (lambda (c) (list r1 c)) (rest (step-range c1 c2))))
                       (vpart (map (lambda (r) (list r c2)) (rest (step-range r1 r2)))))
                  (loop (rest remaining) next (append out hpart vpart)))))))
    (define colors (grid-colors g 0))
    (define c1 (first colors))
    (define c2 (second colors))
    (define p1 (trace (find-color g c1)))
    (define p2 (trace (find-color g c2)))
    (define selected {selected})
    (define base
      (for/fold ([out (empty-grid (rows g) (cols g) 0)]) ([color (in-list colors)])
        (for/fold ([acc out]) ([p (in-list (trace (find-color g color)))])
          (if (= (at acc (first p) (second p)) 0)
              (set-cell acc (first p) (second p) color)
              (set-cell acc (first p) (second p) 9)))))
    (cellmap base (r c v)
      (if (and (not (= v 9)) (member (list r c) selected)) 8 v))))"""


def program(settings) -> str:
    mode = _settings(settings)
    if mode == "canonical":
        return Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")
    return _derived_program(mode)


def _rng(seed: int, split: str, index: int, label: str = "scene") -> random.Random:
    raw = hashlib.sha256(f"{TASK_ID}:{seed}:{split}:{index}:{label}".encode()).digest()
    return random.Random(int.from_bytes(raw, "big"))


def _sample_points(rng: random.Random, height: int, width: int, count: int, *, edge_mode: int):
    used: set[tuple[int, int]] = set()
    groups: list[list[tuple[int, int]]] = [[], []]
    forced = [
        [(0, rng.randrange(width)), (height - 1, rng.randrange(width))],
        [(rng.randrange(height), 0), (rng.randrange(height), width - 1)],
    ]
    if edge_mode % 2:
        forced.reverse()
    for group, points in zip(groups, forced):
        for point in points:
            if point not in used:
                group.append(point); used.add(point)
    population = [(r, c) for r in range(height) for c in range(width)]
    rng.shuffle(population)
    for group in groups:
        while len(group) < count:
            point = population.pop()
            if point not in used:
                group.append(point); used.add(point)
    return groups


def sample_input(seed: int, split: str, index: int, *, height: int, width: int) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    if split not in {"demo", "query"}:
        raise ValueError("split must be demo or query")
    _integer(index, 0, 63, "index")
    _integer(height, 8, 30, "height")
    _integer(width, 9, 30, "width")
    rng = _rng(seed, split, index)
    count = 4 + ((index + (1 if split == "query" else 0)) % 2)
    palette = [1, 2, 3, 4, 5, 6, 7]
    colors = rng.sample(palette, 2)
    colors.sort()
    desired_longer = index % 2
    minimum_occupied = 80 if height >= 24 and width >= 24 else max(20, (height + width) * 2)
    for attempt in range(8192):
        groups = _sample_points(rng, height, width, count, edge_mode=index + attempt)
        grid = [[0 for _ in range(width)] for _ in range(height)]
        for color, points in zip(colors, groups):
            for r, c in points:
                grid[r][c] = color
        facts = analyze(grid)
        if not facts.get("valid_for_all_settings"):
            continue
        longer_index = colors.index(facts["longer_color"])
        if longer_index != desired_longer:
            continue
        if facts["canonical_occupied"] < minimum_occupied:
            continue
        return grid
    raise RuntimeError(f"failed to construct polyline scene {height}x{width}")


def teaching_check(episode, settings) -> dict:
    _settings(settings)
    demos = episode["train"]
    survivors = [
        candidate
        for candidate in SETTINGS
        if all(solve(pair["input"], candidate) == pair["output"] for pair in demos)
    ]
    rivals = []
    mode = settings["path_emphasis"]
    for name, fn in {
        "always_first_path": lambda g: solve_with_selected_color(g, analyze(g)["path_colors"][0]),
        "always_second_path": lambda g: solve_with_selected_color(g, analyze(g)["path_colors"][1]),
        "paint_both_paths": lambda g: [[8 if v not in {0, 9} else v for v in row] for row in canonical_solve(g)],
    }.items():
        if mode != "canonical" and all(fn(pair["input"]) == pair["output"] for pair in demos):
            rivals.append(name)
    return {"survivors": survivors, "surviving_rivals": rivals}


def generate(seed, settings, demos=2, queries=4) -> dict:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    _settings(settings)
    query_sizes = list(QUERY_SIZES)
    _rng(seed, "query-order", 0).shuffle(query_sizes)

    def pairs(split: str, sizes):
        result = []
        for index, (height, width) in enumerate(sizes):
            grid = sample_input(seed, split, index, height=height, width=width)
            result.append({"input": grid, "output": solve(grid, settings)})
        return result

    episode = {
        "train": pairs("demo", DEMO_SIZES[:demos]),
        "test": pairs("query", query_sizes[:queries]),
        "program_solution": program(settings),
        "settings": copy.deepcopy(settings),
    }
    inputs = [repr(pair["input"]) for pair in episode["train"] + episode["test"]]
    if len(inputs) != len(set(inputs)):
        raise RuntimeError("generated inputs are not distinct")
    check = teaching_check(episode, settings)
    if check["survivors"] != [settings] or check["surviving_rivals"]:
        raise RuntimeError(f"demonstrations failed teaching check: {check}")
    return episode


def public_turn(episode, query_index=0) -> dict:
    if type(query_index) is not int:
        raise ValueError("query_index must be an exact integer")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or not 0 <= query_index < len(test):
        raise ValueError("episode needs train pairs and selected query")
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in train
        ],
        "test": [{"input": copy.deepcopy(test[query_index]["input"])}],
    }


def rival_programs(settings) -> dict[str, str]:
    mode = _settings(settings)
    result = {
        "always_first_path": _derived_program("longer", forced="first"),
        "always_second_path": _derived_program("longer", forced="second"),
        "paint_both_paths": """(rule!
  (let ((dummy 0))
    (define (step-range a b) (if (<= a b) (range a (+ b 1)) (reverse (range b (+ a 1)))))
    (define (trace points)
      (if (empty? points) (list)
          (let loop ([remaining (rest points)] [prev (first points)] [out (list (first points))])
            (if (empty? remaining)
                (reverse (foldl (lambda (p acc) (if (member p acc) acc (cons p acc))) (list) (reverse out)))
                (let* ([next (first remaining)] [r1 (first prev)] [c1 (second prev)]
                       [r2 (first next)] [c2 (second next)]
                       [hpart (map (lambda (c) (list r1 c)) (rest (step-range c1 c2)))]
                       [vpart (map (lambda (r) (list r c2)) (rest (step-range r1 r2)))])
                  (loop (rest remaining) next (append out hpart vpart)))))))
    (define base
      (for/fold ([out (empty-grid (rows g) (cols g) 0)]) ([color (in-list (grid-colors g 0))])
        (for/fold ([acc out]) ([p (in-list (trace (find-color g color)))])
          (if (= (at acc (first p) (second p)) 0)
              (set-cell acc (first p) (second p) color)
              (set-cell acc (first p) (second p) 9)))))
    (cellmap base (r c v) (if (and (not (= v 0)) (not (= v 9))) 8 v))))""",
    }
    for candidate in SETTINGS:
        if candidate != settings:
            result["other_setting_" + candidate["path_emphasis"]] = program(candidate)
    if mode == "canonical":
        result.pop("paint_both_paths", None)
    return result
