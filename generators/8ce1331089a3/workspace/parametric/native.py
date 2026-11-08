"""Native finite parametric family for ARC task 8ce1331089a3.

The canonical setting keeps only wall-adjacent endpoints.  The composed setting
first counts the four color-defined routes, then expands only the uniquely most
frequent route into complete source-to-wall traces.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any

HOME = Path(__file__).resolve().parent
ROUTES = ("top", "bottom", "left", "right")
SETTINGS = ("wall_endpoint", "dominant_trace")
DEMO_SIZES = ((12, 12), (10, 15), (14, 11), (14, 17), (18, 18), (16, 22))
QUERY_SIZES = ((20, 16), (18, 24), (24, 20), (30, 30))


def _read_exact(path: Path) -> str:
    value = path.read_text(encoding="utf-8")
    if not value.strip():
        raise ValueError(f"empty Racket source: {path}")
    return value


CANONICAL_PROGRAM = _read_exact(HOME / "canonical.rkt")


def _selector_expression(selector: str) -> str:
    if selector == "most":
        comparator = ">"
    elif selector == "least":
        comparator = "<"
    elif selector in ROUTES:
        return f"{selector}-color" if selector != "bottom" else "bot-color"
    else:
        raise ValueError(f"unknown selector: {selector}")
    names = {
        "top": "top-count",
        "bottom": "bot-count",
        "left": "left-count",
        "right": "right-count",
    }
    colors = {
        "top": "top-color",
        "bottom": "bot-color",
        "left": "left-color",
        "right": "right-color",
    }
    clauses = []
    for route in ROUTES[:-1]:
        others = [other for other in ROUTES if other != route]
        tests = " ".join(
            f"({comparator} {names[route]} {names[other]})" for other in others
        )
        clauses.append(f"((and {tests}) {colors[route]})")
    return "(cond\n                    " + "\n                    ".join(clauses) + "\n                    (else right-color))"


def _trace_program(selector: str = "most", *, trace_all: bool = False) -> str:
    selector_expr = _selector_expression(selector)
    condition = "#t" if trace_all else "(= v dominant-color)"
    return f"""(rule! (lambda (g)
  (let* ((h (rows g))
         (w (cols g))
         (top-color (at g 0 1))
         (bot-color (at g (- h 1) 1))
         (left-color (at g 1 0))
         (right-color (at g 1 (- w 1)))
         (top-count (for*/sum ((r (range 1 (- h 1))) (c (range 1 (- w 1))))
                      (if (= (at g r c) top-color) 1 0)))
         (bot-count (for*/sum ((r (range 1 (- h 1))) (c (range 1 (- w 1))))
                      (if (= (at g r c) bot-color) 1 0)))
         (left-count (for*/sum ((r (range 1 (- h 1))) (c (range 1 (- w 1))))
                       (if (= (at g r c) left-color) 1 0)))
         (right-count (for*/sum ((r (range 1 (- h 1))) (c (range 1 (- w 1))))
                        (if (= (at g r c) right-color) 1 0)))
         (dominant-color {selector_expr})
         (result (make-hash)))
    (for* ((r (range 0 h)) (c (range 0 w)))
      (hash-set! result (list r c)
        (if (or (zero? r) (= r (- h 1)) (zero? c) (= c (- w 1)))
            (at g r c)
            0)))
    (for* ((r (range 1 (- h 1))) (c (range 1 (- w 1))))
      (let ((v (at g r c)))
        (when (!= v 0)
          (cond
            ((= v top-color)
             (if {condition}
                 (for ((rr (range 1 (+ r 1)))) (hash-set! result (list rr c) v))
                 (hash-set! result (list 1 c) v)))
            ((= v bot-color)
             (if {condition}
                 (for ((rr (range r (- h 1)))) (hash-set! result (list rr c) v))
                 (hash-set! result (list (- h 2) c) v)))
            ((= v left-color)
             (if {condition}
                 (for ((cc (range 1 (+ c 1)))) (hash-set! result (list r cc) v))
                 (hash-set! result (list r 1) v)))
            ((= v right-color)
             (if {condition}
                 (for ((cc (range c (- w 1)))) (hash-set! result (list r cc) v))
                 (hash-set! result (list r (- w 2)) v)))))))
    (cellmap g (r c v) (hash-ref result (list r c) 0)))))"""


DOMINANT_TRACE_PROGRAM = _trace_program("most")


def _setting(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"path_rule"}:
        raise ValueError("settings must contain exactly path_rule")
    value = settings["path_rule"]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"path_rule must be one of {SETTINGS}")
    return value


def program(settings: Any) -> str:
    return CANONICAL_PROGRAM if _setting(settings) == "wall_endpoint" else DOMINANT_TRACE_PROGRAM


def rival_program(name: str) -> str:
    """Return bounded executable rivals used by the task-local teaching audit."""
    if name == "trace_all":
        return _trace_program("most", trace_all=True)
    if name == "least_frequent":
        return _trace_program("least")
    if name.startswith("fixed_") and name[6:] in ROUTES:
        return _trace_program(name[6:])
    raise ValueError(f"unknown rival: {name}")


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list:
        raise ValueError("grid must have 1..30 rows")
    width = len(grid[0])
    if not 1 <= width <= 30:
        raise ValueError("grid must have 1..30 columns")
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    if len(grid) < 5 or width < 5:
        raise ValueError("route grids must be at least 5x5")
    return len(grid), width


def analyze(grid: Any) -> dict[str, Any]:
    height, width = _validate_grid(grid)
    edge_colors = {
        "top": grid[0][1],
        "bottom": grid[height - 1][1],
        "left": grid[1][0],
        "right": grid[1][width - 1],
    }
    if 0 in edge_colors.values() or len(set(edge_colors.values())) != 4:
        raise ValueError("four distinct nonzero edge colors are required")
    route_by_color = {color: route for route, color in edge_colors.items()}
    counts = {route: 0 for route in ROUTES}
    distractors = []
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            value = grid[row][col]
            if value == 0:
                continue
            route = route_by_color.get(value)
            if route is None:
                distractors.append((row, col, value))
            else:
                counts[route] += 1
    maximum = max(counts.values())
    winners = [route for route in ROUTES if counts[route] == maximum]
    return {
        "height": height,
        "width": width,
        "edge_colors": edge_colors,
        "route_counts": counts,
        "unique_dominant": len(winners) == 1,
        "dominant_route": winners[0] if len(winners) == 1 else None,
        "distractors": distractors,
    }


def _endpoint(route: str, row: int, col: int, height: int, width: int) -> tuple[int, int]:
    if route == "top":
        return 1, col
    if route == "bottom":
        return height - 2, col
    if route == "left":
        return row, 1
    return row, width - 2


def _trace(route: str, row: int, col: int, height: int, width: int):
    if route == "top":
        return ((rr, col) for rr in range(1, row + 1))
    if route == "bottom":
        return ((rr, col) for rr in range(row, height - 1))
    if route == "left":
        return ((row, cc) for cc in range(1, col + 1))
    return ((row, cc) for cc in range(col, width - 1))


def transform(grid: Any, path_rule: str) -> list[list[int]]:
    if type(path_rule) is not str or path_rule not in SETTINGS:
        raise ValueError(f"path_rule must be one of {SETTINGS}")
    facts = analyze(grid)
    if path_rule == "dominant_trace" and not facts["unique_dominant"]:
        raise ValueError("dominant_trace grammar requires a unique dominant route")
    height, width = facts["height"], facts["width"]
    result = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        for col in range(width):
            if row in {0, height - 1} or col in {0, width - 1}:
                result[row][col] = grid[row][col]
    route_by_color = {color: route for route, color in facts["edge_colors"].items()}
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            value = grid[row][col]
            route = route_by_color.get(value)
            if route is None:
                continue
            if path_rule == "dominant_trace" and route == facts["dominant_route"]:
                cells = _trace(route, row, col, height, width)
            else:
                cells = (_endpoint(route, row, col, height, width),)
            for rr, cc in cells:
                result[rr][cc] = value
    return result


def _rng(seed: int, split: str, index: int, label: str) -> random.Random:
    material = f"8ce1331089a3|{seed}|{split}|{index}|{label}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(material).digest()[:16], "big"))


def _distance(route: str, position: tuple[int, int], height: int, width: int) -> int:
    row, col = position
    return {"top": row, "bottom": height - 1 - row, "left": col, "right": width - 1 - col}[route]


def _trace_cells(route: str, position: tuple[int, int], height: int, width: int) -> set[tuple[int, int]]:
    return set(_trace(route, position[0], position[1], height, width))


def _target_key(route: str, position: tuple[int, int]) -> int:
    return position[1] if route in {"top", "bottom"} else position[0]


def _route_counts(height: int, width: int, dominant: str) -> dict[str, int]:
    opposite = {"top": "bottom", "bottom": "top", "left": "right", "right": "left"}[dominant]
    shared_capacity = width - 4 if dominant in {"top", "bottom"} else height - 4
    if height == width == 30:
        dominant_count, opposite_count = 8, 6
        perpendicular_counts = (4, 2)
    elif min(height, width) >= 18:
        dominant_count, opposite_count = 7, 5
        perpendicular_counts = (3, 2)
    else:
        dominant_count = min(5, shared_capacity - 2)
        opposite_count = min(3, shared_capacity - dominant_count)
        perpendicular_counts = (2, 1)
    if dominant_count <= max(opposite_count, *perpendicular_counts) or opposite_count < 1:
        raise ValueError(f"cannot create a unique dominant route in {height}x{width}")
    others = [route for route in ROUTES if route not in {dominant, opposite}]
    return {
        dominant: dominant_count,
        opposite: opposite_count,
        others[0]: perpendicular_counts[0],
        others[1]: perpendicular_counts[1],
    }


def _choose_positions(
    *,
    seed: int,
    split: str,
    index: int,
    route: str,
    count: int,
    height: int,
    width: int,
    occupied: set[tuple[int, int]],
    blocked: set[tuple[int, int]],
    longest_first: bool,
) -> list[tuple[int, int]]:
    candidates = [
        (row, col)
        for row in range(2, height - 2)
        for col in range(2, width - 2)
        if (row, col) not in occupied and (row, col) not in blocked
    ]
    rng = _rng(seed, split, index, f"positions:{route}:{longest_first}")
    ties = {position: rng.random() for position in candidates}
    candidates.sort(
        key=lambda position: (
            -_distance(route, position, height, width) if longest_first else 0,
            ties[position],
            position,
        )
    )
    selected = []
    targets = set()
    for position in candidates:
        target = _target_key(route, position)
        if target in targets:
            continue
        selected.append(position)
        targets.add(target)
        occupied.add(position)
        if len(selected) == count:
            return selected
    raise ValueError(f"could not place {count} pixels for route {route} in {height}x{width}")


def _make_input(seed: int, split: str, index: int) -> list[list[int]]:
    sizes = DEMO_SIZES if split == "train" else QUERY_SIZES
    height, width = sizes[index]
    dominant_index = (seed + index + (0 if split == "train" else 2)) % len(ROUTES)
    dominant = ROUTES[dominant_index]
    counts = _route_counts(height, width, dominant)

    palette = list(range(1, 10))
    color_rng = _rng(seed, split, index, "colors")
    color_rng.shuffle(palette)
    route_colors = dict(zip(ROUTES, palette[:4], strict=True))
    distractor_count = 1 + ((seed + index + (0 if split == "train" else 1)) % 3)
    distractor_colors = palette[4 : 4 + distractor_count]

    grid = [[0 for _ in range(width)] for _ in range(height)]
    for col in range(1, width - 1):
        grid[0][col] = route_colors["top"]
        grid[height - 1][col] = route_colors["bottom"]
    for row in range(1, height - 1):
        grid[row][0] = route_colors["left"]
        grid[row][width - 1] = route_colors["right"]

    occupied: set[tuple[int, int]] = set()
    dominant_positions = _choose_positions(
        seed=seed,
        split=split,
        index=index,
        route=dominant,
        count=counts[dominant],
        height=height,
        width=width,
        occupied=occupied,
        blocked=set(),
        longest_first=True,
    )
    blocked = set().union(*(
        _trace_cells(dominant, position, height, width) for position in dominant_positions
    ))
    positions = {dominant: dominant_positions}
    for route in ROUTES:
        if route == dominant:
            continue
        positions[route] = _choose_positions(
            seed=seed,
            split=split,
            index=index,
            route=route,
            count=counts[route],
            height=height,
            width=width,
            occupied=occupied,
            blocked=blocked,
            longest_first=False,
        )

    for route, route_positions in positions.items():
        for row, col in route_positions:
            grid[row][col] = route_colors[route]

    free = [
        (row, col)
        for row in range(2, height - 2)
        for col in range(2, width - 2)
        if (row, col) not in occupied and (row, col) not in blocked
    ]
    distractor_rng = _rng(seed, split, index, "distractors")
    distractor_rng.shuffle(free)
    if len(free) < len(distractor_colors):
        raise ValueError("not enough distractor positions")
    for color, (row, col) in zip(distractor_colors, free, strict=False):
        grid[row][col] = color

    facts = analyze(grid)
    if not facts["unique_dominant"] or facts["dominant_route"] != dominant:
        raise AssertionError("constructed input lost its intended unique dominant route")
    if any(counts[route] != facts["route_counts"][route] for route in ROUTES):
        raise AssertionError("constructed route counts changed")
    return grid


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    path_rule = _setting(settings)
    train_inputs = [_make_input(seed, "train", index) for index in range(demos)]
    test_inputs = [_make_input(seed, "test", index) for index in range(queries)]
    all_inputs = train_inputs + test_inputs
    if len({repr(grid) for grid in all_inputs}) != len(all_inputs):
        raise AssertionError("generated inputs must be distinct")

    def pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
        return {"input": deepcopy(grid), "output": transform(grid, path_rule)}

    return {
        "train": [pair(grid) for grid in train_inputs],
        "test": [pair(grid) for grid in test_inputs],
        "program_solution": program(settings),
    }


def public_turn(episode: Any, query_index: Any) -> dict[str, Any]:
    if type(query_index) is not int or not isinstance(episode, dict):
        raise ValueError("query_index must be an exact integer")
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list or not 0 <= query_index < len(test):
        raise ValueError("query_index is outside the available queries")
    try:
        return {
            "train": [
                {"input": deepcopy(item["input"]), "output": deepcopy(item["output"])}
                for item in train
            ],
            "test": [{"input": deepcopy(test[query_index]["input"])}],
        }
    except (KeyError, TypeError) as error:
        raise ValueError("episode pairs are malformed") from error
