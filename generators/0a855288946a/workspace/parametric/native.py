"""Native parametric family for ARC task 0a855288946a.

The default is the exact canonical whole-grid 180-degree rotation.  The
alternative first finds the uniquely least frequent nonzero color, then swaps
only the 180-degree cell orbits touching that color.  Thus counting and
selection produce an input-dependent intermediate consumed by the transform.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any

HOME = Path(__file__).resolve().parent
SETTINGS = ("all_cells", "rarest_color_orbits")
RIVAL_NAMES = (
    "all_cells",
    "rarest_color_orbits",
    "identity",
    "flip_left_right",
    "flip_up_down",
    "most_frequent_nonzero_orbits",
    "smallest_numeric_color_orbits",
    "second_smallest_numeric_color_orbits",
    "second_largest_numeric_color_orbits",
    "largest_numeric_color_orbits",
    "rarest_move_without_swap",
)
DEMO_PROFILES = (
    (4, 5, 14, 2),
    (5, 6, 20, 2),
    (6, 7, 28, 3),
    (8, 9, 44, 3),
    (10, 12, 70, 4),
    (12, 14, 96, 4),
)
QUERY_PROFILES = (
    (14, 16, 125, 4),
    (18, 20, 190, 5),
    (24, 24, 270, 5),
    (30, 30, 360, 6),
)

CANONICAL_PROGRAM = (HOME / "canonical.rkt").read_text(encoding="utf-8")
RAREST_PROGRAM = """(rule! (lambda (g)
  (let* ((h (rows g))
         (w (cols g))
         (colors (filter (lambda (v) (not (= v 0))) (grid-colors g)))
         (key-color (pick-min colors (lambda (v) (count-color g v))))
         (selected (find-color g key-color)))
    (define (selected? p)
      (any? (lambda (q) (and (= (fst p) (fst q)) (= (snd p) (snd q)))) selected))
    (grid-from-fn h w
      (lambda (r c)
        (let ((other (list (- h 1 r) (- w 1 c))))
          (if (or (selected? (list r c)) (selected? other))
              (at g (fst other) (snd other))
              (at g r c))))))))"""


def _setting(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"rotation_scope"}:
        raise ValueError("settings must contain exactly rotation_scope")
    value = settings["rotation_scope"]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"rotation_scope must be one of {SETTINGS}")
    return value


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def program(settings: Any) -> str:
    return CANONICAL_PROGRAM if _setting(settings) == "all_cells" else RAREST_PROGRAM


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not 3 <= len(grid) <= 30 or type(grid[0]) is not list:
        raise ValueError("grid must have 3..30 rows")
    width = len(grid[0])
    if not 3 <= width <= 30:
        raise ValueError("grid must have 3..30 columns")
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return len(grid), width


def analyze(grid: Any) -> dict[str, Any]:
    height, width = _validate_grid(grid)
    counts = Counter(cell for row in grid for cell in row if cell != 0)
    if len(counts) < 3:
        raise ValueError("need at least three nonzero colors")
    ranking = sorted(counts, key=lambda color: (counts[color], color))
    if len(ranking) > 1 and counts[ranking[0]] == counts[ranking[1]]:
        raise ValueError("rarest nonzero color must be unique")
    rarest = ranking[0]
    selected = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                if value == rarest]
    selected_set = set(selected)
    if not selected:
        raise ValueError("rarest color must occur")
    for row, col in selected:
        other = (height - 1 - row, width - 1 - col)
        if other in selected_set:
            raise ValueError("selected color may not occupy both ends of one 180-degree orbit")
        if grid[row][col] == grid[other[0]][other[1]]:
            raise ValueError("selected orbit must visibly change when swapped")
    return {
        "height": height,
        "width": width,
        "counts": dict(sorted(counts.items())),
        "rarest_color": rarest,
        "selected_cells": [list(cell) for cell in selected],
    }


def _rot180(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in reversed(grid)]


def _swap_orbits(grid: list[list[int]], selected: set[tuple[int, int]]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    result = deepcopy(grid)
    for row in range(height):
        for col in range(width):
            other = (height - 1 - row, width - 1 - col)
            if (row, col) in selected or other in selected:
                result[row][col] = grid[other[0]][other[1]]
    return result


def transform(grid: Any, rotation_scope: str) -> list[list[int]]:
    if type(rotation_scope) is not str or rotation_scope not in SETTINGS:
        raise ValueError(f"rotation_scope must be one of {SETTINGS}")
    facts = analyze(grid)
    if rotation_scope == "all_cells":
        return _rot180(grid)
    selected = {tuple(cell) for cell in facts["selected_cells"]}
    return _swap_orbits(grid, selected)


def _selected_color(grid: list[list[int]], mode: str) -> int:
    counts = Counter(cell for row in grid for cell in row if cell != 0)
    if mode == "most":
        return min(counts, key=lambda color: (-counts[color], color))
    ordered = sorted(counts)
    if mode == "smallest":
        return ordered[0]
    if mode == "second_smallest":
        return ordered[1]
    if mode == "second_largest":
        return ordered[-2]
    if mode == "largest":
        return ordered[-1]
    raise ValueError(mode)


def rival_output(grid: Any, name: str) -> list[list[int]]:
    analyze(grid)
    if name in SETTINGS:
        return transform(grid, name)
    if name == "identity":
        return deepcopy(grid)
    if name == "flip_left_right":
        return [list(reversed(row)) for row in grid]
    if name == "flip_up_down":
        return [list(row) for row in reversed(grid)]
    if name in {"most_frequent_nonzero_orbits", "smallest_numeric_color_orbits",
                "second_smallest_numeric_color_orbits",
                "second_largest_numeric_color_orbits",
                "largest_numeric_color_orbits"}:
        mode = {
            "most_frequent_nonzero_orbits": "most",
            "smallest_numeric_color_orbits": "smallest",
            "second_smallest_numeric_color_orbits": "second_smallest",
            "second_largest_numeric_color_orbits": "second_largest",
            "largest_numeric_color_orbits": "largest",
        }[name]
        color = _selected_color(grid, mode)
        selected = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                    if value == color}
        return _swap_orbits(grid, selected)
    if name == "rarest_move_without_swap":
        facts = analyze(grid)
        rarest = facts["rarest_color"]
        height, width = facts["height"], facts["width"]
        result = deepcopy(grid)
        selected = {tuple(cell) for cell in facts["selected_cells"]}
        for row, col in selected:
            result[row][col] = 0
        for row, col in selected:
            result[height - 1 - row][width - 1 - col] = rarest
        return result
    raise ValueError(f"unknown rival: {name}")


def _rng(seed: int, stream: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"rotation-scope-v1:{seed}:{stream}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _balanced_positions(height: int, width: int, rng: random.Random) -> list[tuple[int, int]]:
    buckets: list[list[tuple[int, int]]] = [[] for _ in range(4)]
    for row in range(height):
        for col in range(width):
            quadrant = (2 if row >= height / 2 else 0) + (1 if col >= width / 2 else 0)
            buckets[quadrant].append((row, col))
    for bucket in buckets:
        rng.shuffle(bucket)
    result: list[tuple[int, int]] = []
    while any(buckets):
        for bucket in buckets:
            if bucket:
                result.append(bucket.pop())
    return result


def _scene(seed: int, stream: str, index: int, profile: tuple[int, int, int, int]) -> list[list[int]]:
    height, width, nonzero_total, rare_count = profile
    rng = _rng(seed, stream, index)
    palette = sorted(rng.sample(range(1, 10), 4))
    # The first two demonstrations deliberately reverse the two middle numeric
    # ranks.  Thus color-value rank cannot substitute for measured frequency.
    rare_rank = (1, 2, 0, 3, 1, 2)[index % 6]
    rarest = palette[rare_rank]
    others = [color for color in palette if color != rarest]
    rng.shuffle(others)
    positions = _balanced_positions(height, width, rng)
    selected: list[tuple[int, int]] = []
    blocked: set[tuple[int, int]] = set()
    for pos in positions:
        other = (height - 1 - pos[0], width - 1 - pos[1])
        if pos == other or pos in blocked or other in blocked:
            continue
        selected.append(pos)
        blocked.add(pos)
        blocked.add(other)
        if len(selected) == rare_count:
            break
    if len(selected) != rare_count:
        raise RuntimeError("could not place rarest-color orbit witnesses")

    grid = [[0 for _ in range(width)] for _ in range(height)]
    assigned = Counter()
    for row, col in selected:
        grid[row][col] = rarest
        assigned[rarest] += 1
        rr, cc = height - 1 - row, width - 1 - col
        grid[rr][cc] = others[0]
        assigned[others[0]] += 1

    # Give every non-rarest color one private asymmetric orbit whose opposite
    # endpoint remains zero.  Selecting any fixed numeric rank therefore changes
    # at least one orbit that the measured-rarest rule leaves untouched.
    for color in others:
        witness = None
        for pos in positions:
            other = (height - 1 - pos[0], width - 1 - pos[1])
            if pos != other and pos not in blocked and other not in blocked:
                witness = pos, other
                break
        if witness is None:
            raise RuntimeError("could not place numeric-rank rival witness")
        pos, other = witness
        grid[pos[0]][pos[1]] = color
        assigned[color] += 1
        blocked.add(pos)
        blocked.add(other)

    remaining = nonzero_total - rare_count
    base, extra = divmod(remaining, len(others))
    targets = {color: base + (1 if i < extra else 0) for i, color in enumerate(others)}
    if any(target <= rare_count for target in targets.values()):
        raise RuntimeError("profile does not make the rarest color unique")
    available = [pos for pos in positions if pos not in blocked and grid[pos[0]][pos[1]] == 0]
    cursor = 0
    for color in others:
        need = targets[color] - assigned[color]
        if need < 0:
            raise RuntimeError("forced orbit mates exceed color budget")
        for row, col in available[cursor:cursor + need]:
            grid[row][col] = color
        cursor += need
    if sum(value != 0 for row in grid for value in row) != nonzero_total:
        raise RuntimeError("scene nonzero budget mismatch")
    facts = analyze(grid)
    if facts["rarest_color"] != rarest:
        raise RuntimeError("scene lost intended rarest color")
    if transform(grid, "all_cells") == transform(grid, "rarest_color_orbits"):
        raise RuntimeError("scene does not distinguish settings")
    return grid


def _inputs(seed: int, profiles: tuple[tuple[int, int, int, int], ...], stream: str) -> list[list[list[int]]]:
    return [_scene(seed, stream, index, profile) for index, profile in enumerate(profiles)]


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    scope = _setting(settings)
    demo_inputs = _inputs(seed, DEMO_PROFILES, "demo")[:demos]
    query_inputs = _inputs(seed, QUERY_PROFILES, "query")[:queries]
    def pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
        return {"input": deepcopy(grid), "output": transform(grid, scope)}
    return {
        "train": [pair(grid) for grid in demo_inputs],
        "test": [pair(grid) for grid in query_inputs],
        "program_solution": program({"rotation_scope": scope}),
    }
