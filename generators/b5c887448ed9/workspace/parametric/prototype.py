"""Episode-fixed overwrite-policy family for ARC task b5c887448ed9.

``reading_order`` is the exact canonical rule. ``longest_path_last`` first
constructs every ordered elbow, measures its input-dependent route length, then
paints routes from shortest to longest so the longest route wins crossings.
Inputs are setting-independent and include two demonstrations that separate the
finite family and the retained shortcut set.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Callable

TASK_ID = "b5c887448ed9"
HERE = Path(__file__).resolve().parent
CANONICAL_PATH = HERE / "canonical.rkt"
SETTINGS = ("reading_order", "longest_path_last")
DEFAULT = "reading_order"

# Six teaching surfaces followed by four controller-side query surfaces.
# Each item is (height, width, endpoint pairs). Horizontal mirroring and a
# deterministic palette rotation provide seed variation without changing the
# teaching guarantees.
DEMO_PROFILES = (
    (12, 14, (
        ((0, 6), (1, 2)),
        ((2, 3), (10, 5)),
        ((4, 12), (7, 2)),
        ((0, 13), (11, 9)),
        ((3, 6), (9, 13)),
    )),
    (14, 16, (
        ((10, 7), (12, 3)),
        ((2, 7), (13, 6)),
        ((2, 10), (13, 15)),
        ((1, 4), (9, 12)),
        ((6, 8), (7, 14)),
        ((5, 0), (8, 13)),
    )),
    (16, 18, (
        ((0, 13), (3, 3)),
        ((7, 17), (14, 1)),
        ((3, 11), (15, 5)),
        ((3, 16), (6, 13)),
        ((13, 8), (15, 3)),
        ((6, 0), (10, 7)),
    )),
    (18, 20, (
        ((15, 16), (16, 7)),
        ((8, 0), (16, 19)),
        ((2, 0), (16, 13)),
        ((3, 3), (16, 5)),
        ((4, 0), (17, 2)),
        ((6, 17), (10, 4)),
        ((9, 11), (14, 16)),
    )),
    (20, 22, (
        ((3, 5), (19, 13)),
        ((0, 9), (9, 7)),
        ((6, 1), (16, 5)),
        ((1, 21), (15, 12)),
        ((14, 18), (16, 16)),
        ((7, 6), (19, 19)),
        ((12, 10), (18, 21)),
    )),
    (22, 24, (
        ((13, 4), (15, 7)),
        ((8, 23), (13, 3)),
        ((10, 0), (11, 23)),
        ((0, 16), (17, 19)),
        ((9, 16), (20, 9)),
        ((3, 15), (14, 20)),
        ((2, 12), (18, 6)),
        ((16, 1), (19, 20)),
    )),
)
QUERY_PROFILES = (
    (14, 16, (
        ((10, 9), (13, 6)),
        ((3, 1), (9, 12)),
        ((0, 10), (9, 11)),
        ((8, 14), (13, 10)),
        ((4, 14), (7, 2)),
        ((8, 1), (11, 4)),
    )),
    (18, 20, (
        ((15, 8), (16, 5)),
        ((0, 6), (12, 4)),
        ((5, 7), (15, 12)),
        ((4, 3), (16, 9)),
        ((3, 1), (8, 15)),
        ((1, 3), (10, 19)),
        ((0, 17), (7, 10)),
    )),
    (24, 27, (
        ((2, 24), (6, 6)),
        ((17, 8), (18, 26)),
        ((15, 11), (18, 15)),
        ((14, 10), (16, 12)),
        ((6, 7), (15, 19)),
        ((5, 25), (19, 13)),
        ((10, 0), (19, 20)),
        ((0, 9), (21, 16)),
    )),
    (30, 30, (
        ((1, 19), (8, 3)),
        ((12, 28), (26, 12)),
        ((2, 6), (21, 16)),
        ((10, 14), (23, 20)),
        ((14, 18), (29, 5)),
        ((2, 23), (8, 18)),
        ((5, 21), (10, 9)),
        ((9, 20), (22, 13)),
        ((19, 18), (28, 19)),
    )),
)


def _exact_int(value: object, low: int, high: int, label: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label} must be an exact integer in {low}..{high}")
    return value


def _policy(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {"overwrite_policy"}:
        raise ValueError("settings must contain exactly overwrite_policy")
    value = settings["overwrite_policy"]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError("overwrite_policy must be reading_order|longest_path_last")
    return value


def _canonical() -> str:
    source = CANONICAL_PATH.read_text(encoding="utf-8")
    if not source.strip():
        raise RuntimeError("canonical.rkt is empty")
    return source


_LONGEST_PROGRAM = r'''(rule! (let ((dummy 0))
  (define (e8b-list< a b)
    (cond ((empty? a) #f)
          ((< (first a) (first b)) #t)
          ((> (first a) (first b)) #f)
          (else (e8b-list< (rest a) (rest b)))))
  (define (e8b-colors-reading grid)
    (remove-duplicates
      (filter (lambda (v) (not (= v 0)))
              (map (lambda (p) (at grid (first p) (second p)))
                   (grid-positions grid)))))
  (define (s16b-elbow-cells p0 p1)
    (let* ((r0 (first p0)) (c0 (second p0))
           (r1 (first p1)) (c1 (second p1))
           (cstep (if (>= c1 c0) 1 -1))
           (rstep (if (>= r1 r0) 1 -1)))
      (append
        (map (lambda (c) (list r0 c)) (range c0 (+ c1 cstep) cstep))
        (map (lambda (r) (list r c1)) (range r0 (+ r1 rstep) rstep)))))
  (define records
    (map (lambda (color)
           (let* ((cells (sort (find-color g color) e8b-list<))
                  (path (if (= (length cells) 2)
                            (s16b-elbow-cells (first cells) (second cells))
                            (list))))
             (list color cells path)))
         (e8b-colors-reading g)))
  (define ordered
    (sort records
          (lambda (a b)
            (let ((la (length (third a))) (lb (length (third b))))
              (if (= la lb)
                  (e8b-list< (first (second a)) (first (second b)))
                  (< la lb))))))
  (for/fold ((out (empty-grid (rows g) (cols g) 0)))
            ((record (in-list ordered)))
    (if (= (length (second record)) 2)
        (paint-cells out (third record) (first record))
        out))))'''


def program(settings: object) -> str:
    return _canonical() if _policy(settings) == DEFAULT else _LONGEST_PROGRAM


def counterfactual_program(settings: object) -> str:
    if _policy(settings) != "longest_path_last":
        raise ValueError("counterfactual is defined for longest_path_last")
    return _canonical()


def _path(first: tuple[int, int], second: tuple[int, int], *, vertical_first: bool = False) -> list[tuple[int, int]]:
    (r0, c0), (r1, c1) = sorted((first, second))
    cstep = 1 if c1 >= c0 else -1
    rstep = 1 if r1 >= r0 else -1
    horizontal_top = [(r0, c) for c in range(c0, c1 + cstep, cstep)]
    vertical_right = [(r, c1) for r in range(r0, r1 + rstep, rstep)]
    if not vertical_first:
        return horizontal_top + vertical_right
    vertical_left = [(r, c0) for r in range(r0, r1 + rstep, rstep)]
    horizontal_bottom = [(r1, c) for c in range(c0, c1 + cstep, cstep)]
    return vertical_left + horizontal_bottom


def _records(grid: list[list[int]], *, vertical_first: bool = False) -> list[dict[str, Any]]:
    cells: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                cells.setdefault(value, []).append((r, c))
    if not cells or any(len(points) != 2 for points in cells.values()):
        raise ValueError("every nonzero color must occur exactly twice")
    records = []
    for color, points in cells.items():
        pair = tuple(sorted(points))
        records.append({
            "color": color,
            "pair": pair,
            "path": _path(*pair, vertical_first=vertical_first),
        })
    return records


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    records = _records(grid)
    reading = sorted(records, key=lambda row: row["pair"][0])
    longest = sorted(records, key=lambda row: (len(row["path"]), row["pair"][0]))
    sets = [set(row["path"]) for row in records]
    crossings = set()
    for left in range(len(sets)):
        for right in range(left + 1, len(sets)):
            crossings.update(sets[left] & sets[right])
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "route_count": len(records),
        "path_lengths": [len(row["path"]) for row in reading],
        "reading_order": [row["color"] for row in reading],
        "longest_path_order": [row["color"] for row in longest],
        "crossing_cells": len(crossings),
        "painted_cells": len(set().union(*(set(row["path"]) for row in records))),
    }


def _render(grid: list[list[int]], policy: str, *, vertical_first: bool = False,
            fixed_color: int | None = None, limit: int | None = None,
            order_override: str | None = None) -> list[list[int]]:
    records = _records(grid, vertical_first=vertical_first)
    chosen = order_override or policy
    if chosen == "reading_order":
        records.sort(key=lambda row: row["pair"][0])
    elif chosen == "longest_path_last":
        records.sort(key=lambda row: (len(row["path"]), row["pair"][0]))
    elif chosen == "reverse_reading":
        records.sort(key=lambda row: row["pair"][0], reverse=True)
    elif chosen == "second_endpoint":
        records.sort(key=lambda row: row["pair"][1])
    elif chosen == "numeric_color":
        records.sort(key=lambda row: row["color"])
    elif chosen == "shortest_path_last":
        records.sort(key=lambda row: (-len(row["path"]), row["pair"][0]))
    elif chosen == "bbox_area_last":
        records.sort(key=lambda row: (
            (row["pair"][1][0] - row["pair"][0][0] + 1)
            * (abs(row["pair"][1][1] - row["pair"][0][1]) + 1),
            row["pair"][0],
        ))
    else:
        raise ValueError(f"unknown render policy {chosen!r}")
    if limit is not None:
        records = records[:limit]
    out = [[0 for _ in row] for row in grid]
    for record in records:
        color = fixed_color if fixed_color is not None else record["color"]
        for r, c in record["path"]:
            out[r][c] = color
    return out


def transform(grid: list[list[int]], settings: object) -> list[list[int]]:
    return _render(grid, _policy(settings))


def _profile_grid(seed: int, profile_index: int, profile: tuple[Any, ...]) -> list[list[int]]:
    height, width, raw_pairs = profile
    mirror = ((seed * 1315423911 + profile_index * 2654435761) & 1) == 1
    pairs = []
    for raw in raw_pairs:
        points = []
        for r, c in raw:
            points.append((r, width - 1 - c if mirror else c))
        pairs.append(tuple(sorted(points)))
    n = len(pairs)
    colors = list(range(1, n + 1))
    offset = (seed * 3 + profile_index * 2) % n
    colors = colors[offset:] + colors[:offset]
    grid = [[0] * width for _ in range(height)]
    for color, pair in zip(colors, pairs):
        for r, c in pair:
            if grid[r][c] != 0:
                raise AssertionError("duplicate endpoint in profile")
            grid[r][c] = color
    facts = analyze(grid)
    if facts["reading_order"] == facts["longest_path_order"]:
        raise AssertionError("profile does not separate overwrite policies")
    return grid


def _identity(grid):
    return deepcopy(grid)


def _vertical_first(grid):
    return _render(grid, "reading_order", vertical_first=True)


def _reverse_reading(grid):
    return _render(grid, "reading_order", order_override="reverse_reading")


def _second_endpoint(grid):
    return _render(grid, "reading_order", order_override="second_endpoint")


def _numeric_color(grid):
    return _render(grid, "reading_order", order_override="numeric_color")


def _shortest_path_last(grid):
    return _render(grid, "reading_order", order_override="shortest_path_last")


def _first_route_only(grid):
    return _render(grid, "reading_order", limit=1)


def _color_blind(grid):
    return _render(grid, "reading_order", fixed_color=1)


def _bbox_area_last(grid):
    return _render(grid, "reading_order", order_override="bbox_area_last")


RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _identity,
    "vertical_first": _vertical_first,
    "reverse_reading": _reverse_reading,
    "second_endpoint": _second_endpoint,
    "numeric_color": _numeric_color,
    "shortest_path_last": _shortest_path_last,
    "first_route_only": _first_route_only,
    "color_blind": _color_blind,
    "bbox_area_last": _bbox_area_last,
}


def teaching_check(episode: dict[str, Any]) -> dict[str, Any]:
    demos = episode["train"]
    queries = episode["test"]
    declared = [
        {"overwrite_policy": "reading_order"},
        {"overwrite_policy": "longest_path_last"},
    ]
    survivors = [
        setting for setting in declared
        if all(transform(pair["input"], setting) == pair["output"] for pair in demos)
    ]
    rival_rows = {}
    harmful = []
    for name, rival in RIVALS.items():
        fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
        disagreements = [rival(pair["input"]) != pair["output"] for pair in queries]
        rival_rows[name] = {
            "fits_all_demos": fits,
            "query_disagreements": disagreements,
        }
        if fits and any(disagreements):
            harmful.append(name)
    return {
        "declared_survivors": survivors,
        "harmful_survivors": harmful,
        "rivals": rival_rows,
        "query_identifiable": [
            transform(pair["input"], declared[0]) != transform(pair["input"], declared[1])
            for pair in queries
        ],
        "query_answers_used_for_fitting": False,
        "scope": "finite two-setting family plus nine executable shortcuts; not universal uniqueness",
    }


def _pair(grid: list[list[int]], settings: object) -> dict[str, Any]:
    return {"input": grid, "output": transform(grid, settings)}


def generate(seed: int, settings: object, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _exact_int(seed, 0, 2**63 - 1, "seed")
    _exact_int(demos, 2, 6, "demos")
    _exact_int(queries, 1, 4, "queries")
    _policy(settings)
    demo_bank = [
        _pair(_profile_grid(seed, index, profile), settings)
        for index, profile in enumerate(DEMO_PROFILES)
    ]
    query_bank = [
        _pair(_profile_grid(seed, len(DEMO_PROFILES) + index, profile), settings)
        for index, profile in enumerate(QUERY_PROFILES)
    ]
    return {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": deepcopy(settings),
        "train": demo_bank[:demos],
        "test": query_bank[:queries],
        "program_solution": program(settings),
    }


def model_view(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    _exact_int(query_index, 0, len(episode["test"]) - 1, "query_index")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


visible_turn = model_view
