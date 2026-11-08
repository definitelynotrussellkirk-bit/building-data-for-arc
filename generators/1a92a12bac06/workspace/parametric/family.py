"""Native half-fill relay family for ARC task 1a92a12bac06.

The canonical/default setting is byte-exact.  The alternative first performs
that canonical half fill, then recomputes cyan connectivity and paints the
remaining red tops adjacent to the unique largest cyan network yellow.  The
network can only be ranked after the half fill because newly cyan bar bottoms
join pre-existing cyan relay fragments.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

HERE = Path(__file__).resolve().parent
MODES = ("half_only", "largest_relay")
DEFAULT_MODE = "half_only"
DEMO_DIMS = ((13, 15), (14, 16), (15, 17), (16, 18), (17, 19), (18, 20))
QUERY_DIMS = ((19, 21), (22, 24), (26, 28), (30, 30))
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(settings: dict[str, Any]) -> str:
    if type(settings) is not dict:
        raise TypeError("settings must be an exact dictionary")
    if set(settings) != {"mode"}:
        raise ValueError("settings must name exactly mode")
    mode = settings["mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError("mode must be half_only or largest_relay")
    return mode


def _grid(value: Any) -> list[list[int]]:
    if (type(value) is not list or not 1 <= len(value) <= 30
            or type(value[0]) is not list or not 1 <= len(value[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(value[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in value):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return [row[:] for row in value]


def _adjacency_source() -> str:
    return """(define (adjacent? a b)
    (any? (lambda (p)
      (any? (lambda (d)
        (member (list (+ (first p) (first d))
                      (+ (second p) (second d)))
                (obj-cells b)))
        cardinal-deltas))
      (obj-cells a)))"""


def program(settings: dict[str, Any]) -> str:
    """Return exact complete Racket source for a declared setting."""
    mode = _mode(settings)
    canonical = (HERE / "canonical.rkt").read_text(encoding="utf-8")
    if mode == "half_only":
        return canonical
    from puzzle_generators.rule_wrap import wrap_rule

    half = wrap_rule(canonical)
    return f"""(rule! (lambda (g)
  {_adjacency_source()}
  (define half ({half} g))
  (define cyan (filter (lambda (o) (= (obj-color o) 8)) (objects half 0)))
  (if (null? cyan)
      half
      (let* ((winner (pick-max cyan obj-size))
             (reds (filter (lambda (o) (= (obj-color o) 2)) (objects half 0)))
             (targets (filter (lambda (o) (adjacent? o winner)) reds)))
        (reduce (lambda (out o) (paint-cells out (obj-cells o) 4))
                half
                targets)))))"""


def counterfactual_program() -> str:
    """Wrong intermediate: rank original cyan fragments before the half fill."""
    from puzzle_generators.rule_wrap import wrap_rule

    canonical = (HERE / "canonical.rkt").read_text(encoding="utf-8")
    half = wrap_rule(canonical)
    return f"""(rule! (lambda (g)
  {_adjacency_source()}
  (define original-cyan (filter (lambda (o) (= (obj-color o) 8)) (objects g 0)))
  (define half ({half} g))
  (define post-cyan (filter (lambda (o) (= (obj-color o) 8)) (objects half 0)))
  (if (null? original-cyan)
      half
      (let* ((chosen-original (pick-max original-cyan obj-size))
             (matches (filter
               (lambda (o)
                 (all? (lambda (p) (member p (obj-cells o)))
                       (obj-cells chosen-original)))
               post-cyan)))
        (if (null? matches)
            half
            (let* ((winner (first matches))
                   (reds (filter (lambda (o) (= (obj-color o) 2)) (objects half 0)))
                   (targets (filter (lambda (o) (adjacent? o winner)) reds)))
              (reduce (lambda (out o) (paint-cells out (obj-cells o) 4))
                      half
                      targets)))))))"""


def _components(grid: list[list[int]], color: int, *, diagonal: bool = False) -> list[set[tuple[int, int]]]:
    source = _grid(grid)
    height, width = len(source), len(source[0])
    pending = {(r, c) for r in range(height) for c in range(width) if source[r][c] == color}
    deltas = CARDINAL if not diagonal else tuple(
        (dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc
    )
    result: list[set[tuple[int, int]]] = []
    while pending:
        start = min(pending)
        pending.remove(start)
        cells = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for dr, dc in deltas:
                nxt = row + dr, col + dc
                if nxt in pending:
                    pending.remove(nxt)
                    cells.add(nxt)
                    queue.append(nxt)
        result.append(cells)
    return sorted(result, key=lambda cells: min(cells))


def _touches(first: set[tuple[int, int]], second: set[tuple[int, int]]) -> bool:
    return any((r + dr, c + dc) in second for r, c in first for dr, dc in CARDINAL)


def half_fill(grid: list[list[int]]) -> list[list[int]]:
    """Python claim mirror of the canonical per-bar bottom-half fill."""
    source = _grid(grid)
    output = [row[:] for row in source]
    for cells in _components(source, 2):
        rows = [r for r, _ in cells]
        top, bottom = min(rows), max(rows)
        fill_height = (bottom - top + 1) // 2
        cutoff = bottom - fill_height + 1
        for row, col in cells:
            if row >= cutoff:
                output[row][col] = 8
    return output


def _ranked(parts: list[set[tuple[int, int]]]) -> list[set[tuple[int, int]]]:
    return sorted(parts, key=lambda cells: (-len(cells), min(cells)))


def relay_state(grid: list[list[int]]) -> dict[str, Any]:
    """Expose private diagnostics for tests/audits; never part of public export."""
    source = _grid(grid)
    intermediate = half_fill(source)
    pre = _ranked(_components(source, 8))
    post = _ranked(_components(intermediate, 8))
    winner = post[0] if post else set()
    red = _components(intermediate, 2)
    targets = [cells for cells in red if winner and _touches(cells, winner)]
    return {
        "intermediate": intermediate,
        "pre_largest_cells": sorted(pre[0]) if pre else [],
        "pre_largest_size": len(pre[0]) if pre else 0,
        "post_largest_cells": sorted(winner),
        "post_largest_size": len(winner),
        "post_second_size": len(post[1]) if len(post) > 1 else 0,
        "unique_largest": bool(post) and (len(post) == 1 or len(post[0]) > len(post[1])),
        "target_red_components": [sorted(cells) for cells in targets],
    }


def _paint_components(grid: list[list[int]], parts: list[set[tuple[int, int]]], color: int) -> list[list[int]]:
    output = _grid(grid)
    for cells in parts:
        for row, col in cells:
            output[row][col] = color
    return output


def wrong_order_transform(grid: list[list[int]]) -> list[list[int]]:
    """Diagnostic rival: rank original cyan, then follow it through step A."""
    source = _grid(grid)
    intermediate = half_fill(source)
    original = _ranked(_components(source, 8))
    if not original:
        return intermediate
    post = _components(intermediate, 8)
    winner = next((cells for cells in post if original[0] <= cells), set())
    if not winner:
        return intermediate
    reds = _components(intermediate, 2)
    targets = [cells for cells in reds if _touches(cells, winner)]
    return _paint_components(intermediate, targets, 4)


def transform(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    mode = _mode(settings)
    intermediate = half_fill(grid)
    if mode == "half_only":
        return intermediate
    post = _ranked(_components(intermediate, 8))
    if not post:
        return intermediate
    reds = _components(intermediate, 2)
    targets = [cells for cells in reds if _touches(cells, post[0])]
    return _paint_components(intermediate, targets, 4)


def _rng(seed: int, split: str, index: int) -> random.Random:
    payload = f"1a92a12bac06/half-relay-v1/{seed}/{split}/{index}".encode("ascii")
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _place_bar(grid: list[list[int]], column: int, bottom: int, height: int) -> None:
    top = bottom - height + 1
    if top < 0:
        raise ValueError("bar does not fit")
    for row in range(top, bottom + 1):
        if grid[row][column] != 0:
            raise ValueError("bar overlap")
        grid[row][column] = 2


def _place_relay(grid: list[list[int]], first: int, second: int, row: int,
                 size: int, tail_on_right: bool) -> None:
    cells = [(row, col) for col in range(first + 1, second)]
    if len(cells) != 2 or size < 2:
        raise ValueError("relay pairs require an exact two-cell bridge")
    tail_col = cells[-1][1] if tail_on_right else cells[0][1]
    cells.extend((row - step, tail_col) for step in range(1, size - 1))
    for rr, cc in cells:
        if rr < 0 or grid[rr][cc] != 0:
            raise ValueError("relay overlap")
        grid[rr][cc] = 8


def _mirror(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def _scene(seed: int, split: str, index: int, height: int, width: int) -> list[list[int]]:
    rng = _rng(seed, split, index)
    profile = (0, 2, 1, 3, 0, 2)[index] if split == "train" else index % 4
    grid = [[0 for _ in range(width)] for _ in range(height)]
    left_cols = (1, 4)
    right_cols = (width - 5, width - 2)
    bottom = height - 2

    # Profiles 0/1 force a rank inversion between original relay fragments and
    # the post-half-fill cyan networks. Profile 2 makes connector mass beat bar
    # height; profile 3 makes equal connectors resolve by created cyan mass.
    if profile == 0:
        left = ((12, 11), 2)
        right = ((6, 5), 6)
    elif profile == 1:
        left = ((6, 5), 6)
        right = ((12, 11), 2)
    elif profile == 2:
        left = ((6, 5), 8)
        right = ((11, 10), 2)
    else:
        left = ((9, 8), 3)
        right = ((12, 11), 3)

    # Seed-dependent swaps vary local geometry without changing the profile's
    # guaranteed ranking relation.
    if rng.randrange(2):
        left = ((left[0][1], left[0][0]), left[1])
    if rng.randrange(2):
        right = ((right[0][1], right[0][0]), right[1])

    for col, bar_height in zip(left_cols, left[0]):
        _place_bar(grid, col, bottom, bar_height)
    for col, bar_height in zip(right_cols, right[0]):
        _place_bar(grid, col, bottom, bar_height)
    _place_relay(grid, *left_cols, bottom, left[1], bool(rng.randrange(2)))
    _place_relay(grid, *right_cols, bottom, right[1], bool(rng.randrange(2)))

    # A small independent cyan component prevents "there are exactly two cyan
    # objects" from being a valid teaching shortcut.
    middle = width // 2
    grid[0][middle - 1] = 8
    grid[0][middle] = 8

    # Larger canvases carry an additional unselected bar and cyan distractor so
    # the 30x30 query is substantive rather than a padded tiny scene.
    if height >= 18 and width >= 20:
        column = middle
        extra_bottom = min(height - 4, 14)
        _place_bar(grid, column, extra_bottom, 7)
        grid[height - 1][middle - 1] = 8
        grid[height - 1][middle] = 8

    should_mirror = bool(rng.randrange(2))
    if split == "train" and index == 0:
        should_mirror = False
    elif split == "train" and index == 1:
        should_mirror = True
    if should_mirror:
        grid = _mirror(grid)

    state = relay_state(grid)
    if not state["unique_largest"] or len(state["target_red_components"]) != 2:
        raise AssertionError("constructed relay scene lost its unique two-bar target")
    if profile in (0, 1) and state["pre_largest_cells"] == state["post_largest_cells"]:
        raise AssertionError("rank-inversion profile did not change the selected component")
    return grid


def sample_input(seed: int, split: str, index: int, *, height: int | None = None,
                 width: int | None = None) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    if type(split) is not str or split not in ("train", "test"):
        raise ValueError("split must be train or test")
    maximum = 5 if split == "train" else 3
    _integer(index, 0, maximum, "index")
    if (height is None) != (width is None):
        raise ValueError("height and width must be supplied together")
    if height is None:
        height, width = (DEMO_DIMS if split == "train" else QUERY_DIMS)[index]
    height = _integer(height, 13, 30, "height")
    width = _integer(width, 14, 30, "width")
    return _scene(seed, split, index, height, width)


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    mode = _mode(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    chosen = {"mode": mode}

    def pair(split: str, index: int) -> dict[str, list[list[int]]]:
        grid = sample_input(seed, split, index)
        return {"input": grid, "output": transform(grid, chosen)}

    return {
        "train": [pair("train", index) for index in range(demos)],
        "test": [pair("test", index) for index in range(queries)],
        "program_solution": program(chosen),
    }

def public_turn(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    """Return one visible query turn with no settings, answers, or count hints."""
    if type(episode) is not dict or type(episode.get("train")) is not list:
        raise TypeError("episode must contain train and test lists")
    tests = episode.get("test")
    if type(tests) is not list or not tests:
        raise ValueError("episode test list must be nonempty")
    _integer(query_index, 0, len(tests) - 1, "query_index")
    from reviewer_support import public_challenge_bytes

    visible = {"train": episode["train"], "test": [tests[query_index]]}
    return json.loads(public_challenge_bytes(visible))

