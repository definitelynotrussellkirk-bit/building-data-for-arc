"""Native parametric swap-scope family for ARC task d2a80a6f9495.

``all_two_color`` is the exact canonical rule: swap the two colors inside every
8-connected non-background object containing exactly two colors.
``repeated_pair`` first counts unordered color pairs across all eligible objects,
then swaps only objects whose pair occurs more than once in the input.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from functools import cache
import hashlib
import random
from pathlib import Path
from typing import Any

TASK_ID = "d2a80a6f9495"
HERE = Path(__file__).resolve().parent
Grid = list[list[int]]

SCOPES = ("all_two_color", "repeated_pair")
DEFAULT_SCOPE = "all_two_color"
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4

# Every profile contains two independently repeated pair classes, at least one
# unique pair, and one-color plus three-color negative controls.  Query four is
# a dense 30x30 boundary case.
_DEMO_PROFILES = (
    {"h": 12, "w": 14, "repeat": (3, 2), "unique": 1, "negative": 2},
    {"h": 14, "w": 16, "repeat": (2, 3), "unique": 1, "negative": 2},
    {"h": 16, "w": 18, "repeat": (3, 2), "unique": 2, "negative": 2},
    {"h": 18, "w": 20, "repeat": (2, 4), "unique": 2, "negative": 2},
    {"h": 22, "w": 24, "repeat": (4, 3), "unique": 2, "negative": 3},
    {"h": 26, "w": 28, "repeat": (3, 5), "unique": 3, "negative": 3},
)
_QUERY_PROFILES = (
    {"h": 14, "w": 16, "repeat": (2, 3), "unique": 1, "negative": 2},
    {"h": 20, "w": 22, "repeat": (4, 2), "unique": 2, "negative": 3},
    {"h": 26, "w": 28, "repeat": (3, 4), "unique": 4, "negative": 3},
    {"h": 30, "w": 30, "repeat": (5, 4), "unique": 5, "negative": 4, "dense": True},
)

_REPEATED_PAIR_PROGRAM = """(rule! (lambda (g)
  (let* ((objs (objects-multicolor g 0))
         (pair-of
          (lambda (obj)
            (sort
             (unique
              (map (lambda (p) (at g (fst p) (snd p)))
                   (obj-cells obj)))
             <)))
         (pairs
          (map pair-of
               (filter (lambda (obj) (= 2 (length (pair-of obj)))) objs))))
    (reduce
     (lambda (acc obj)
       (let* ((cells (obj-cells obj))
              (colors (pair-of obj))
              (copies
               (if (= 2 (length colors))
                   (length (filter (lambda (p) (equal? p colors)) pairs))
                   0)))
         (if (not (> copies 1))
             acc
             (let* ((ka (first colors)) (kb (nth colors 1)))
               (reduce
                (lambda (g2 p)
                  (set-cell g2 (fst p) (snd p)
                            (if (= ka (at g (fst p) (snd p))) kb ka)))
                acc cells)))))
     g objs))))"""

_KING = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)
_MASKS: tuple[tuple[tuple[int, int], ...], ...] = (
    tuple((r, c) for r in range(3) for c in range(3)),
    tuple((r, c) for r in range(3) for c in range(3) if (r, c) != (1, 1)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 0), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0)),
)
_DENSE_MASKS = _MASKS[:2]


@cache
def canonical_program() -> str:
    source = (HERE / "canonical.rkt").read_text(encoding="utf-8")
    if not source.startswith("(rule!"):
        raise ValueError("canonical.rkt does not contain a rule")
    return source


def _validate_scope(scope: Any) -> str:
    if type(scope) is not str:
        raise TypeError("swap scope must be an exact string")
    if scope not in SCOPES:
        raise ValueError(f"unknown swap scope: {scope!r}")
    return scope


def program_for(scope: str) -> str:
    scope = _validate_scope(scope)
    return canonical_program() if scope == "all_two_color" else _REPEATED_PAIR_PROGRAM


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer")
    if not 0 <= seed < 2**63:
        raise ValueError("seed must be in 0..2**63-1")
    return seed


def _validate_count(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _objects(grid: Grid) -> list[list[tuple[int, int]]]:
    if (
        type(grid) is not list
        or not grid
        or type(grid[0]) is not list
        or not grid[0]
        or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)
        or any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row)
    ):
        raise ValueError("grid must be a rectangular ARC grid")
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(h):
        for col in range(w):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in _KING:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(sorted(cells))
    return result


def object_facts(grid: Grid) -> dict[str, Any]:
    objects = _objects(grid)
    rows: list[dict[str, Any]] = []
    pair_counter: Counter[tuple[int, int]] = Counter()
    for cells in objects:
        colors = sorted({grid[r][c] for r, c in cells})
        bbox = [
            min(r for r, _ in cells),
            min(c for _, c in cells),
            max(r for r, _ in cells),
            max(c for _, c in cells),
        ]
        row = {"cells": [list(p) for p in cells], "colors": colors, "bbox": bbox, "size": len(cells)}
        if len(colors) == 2:
            pair = (colors[0], colors[1])
            row["pair"] = list(pair)
            pair_counter[pair] += 1
        rows.append(row)
    repeated = sorted(pair for pair, count in pair_counter.items() if count > 1)
    two = [row for row in rows if len(row["colors"]) == 2]
    return {
        "objects": rows,
        "two_color_objects": two,
        "negative_object_count": len(rows) - len(two),
        "pair_counts": {f"{a},{b}": pair_counter[(a, b)] for a, b in sorted(pair_counter)},
        "repeated_pairs": [list(pair) for pair in repeated],
    }


def _selected_pairs(grid: Grid, scope: str) -> set[tuple[int, int]]:
    facts = object_facts(grid)
    if scope == "all_two_color":
        return {tuple(row["pair"]) for row in facts["two_color_objects"]}
    return {tuple(pair) for pair in facts["repeated_pairs"]}


def apply_scope(grid: Grid, scope: str) -> Grid:
    scope = _validate_scope(scope)
    selected = _selected_pairs(grid, scope)
    result = deepcopy(grid)
    for row in object_facts(grid)["two_color_objects"]:
        pair = tuple(row["pair"])
        if pair not in selected:
            continue
        first, second = pair
        for r, c in row["cells"]:
            result[r][c] = second if grid[r][c] == first else first
    return result


def _rng(seed: int, split: str, slot: int, purpose: str) -> random.Random:
    material = f"{TASK_ID}|swap-scope-v1|{seed}|{split}|{slot}|{purpose}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def _slots(height: int, width: int) -> list[tuple[int, int]]:
    return [(r, c) for r in range(0, height - 2, 4) for c in range(0, width - 2, 4)]


def _pair_classes(rng: random.Random, count: int) -> list[tuple[int, int]]:
    pairs = [(a, b) for a in range(1, 10) for b in range(a + 1, 10)]
    rng.shuffle(pairs)
    return pairs[:count]


def _paint_two(
    grid: Grid,
    origin: tuple[int, int],
    mask: tuple[tuple[int, int], ...],
    pair: tuple[int, int],
    pattern_index: int,
    rng: random.Random,
) -> None:
    cells = list(mask)
    a, b = pair
    values: list[int]
    mode = pattern_index % 4
    if mode == 0:
        values = [a if (r + c) % 2 == 0 else b for r, c in cells]
    elif mode == 1:
        values = [a if r <= 1 else b for r, _ in cells]
    elif mode == 2:
        values = [b if (r, c) == cells[len(cells) // 2] else a for r, c in cells]
    else:
        values = [rng.choice((a, b)) for _ in cells]
    values[0] = a
    values[-1] = b
    r0, c0 = origin
    for (dr, dc), value in zip(cells, values):
        grid[r0 + dr][c0 + dc] = value


def _paint_negative(
    grid: Grid,
    origin: tuple[int, int],
    mask: tuple[tuple[int, int], ...],
    colors: tuple[int, ...],
) -> None:
    r0, c0 = origin
    for index, (dr, dc) in enumerate(mask):
        grid[r0 + dr][c0 + dc] = colors[index % len(colors)]


def _make_input(seed: int, split: str, slot: int, profile: dict[str, Any]) -> Grid:
    height, width = profile["h"], profile["w"]
    repeated_counts = tuple(profile["repeat"])
    unique_count = profile["unique"]
    negative_count = profile["negative"]
    class_count = 2 + unique_count
    pair_rng = _rng(seed, split, slot, "pairs")
    pairs = _pair_classes(pair_rng, class_count)
    specs: list[tuple[str, Any]] = []
    specs.extend(("two", pairs[0]) for _ in range(repeated_counts[0]))
    specs.extend(("two", pairs[1]) for _ in range(repeated_counts[1]))
    specs.extend(("two", pair) for pair in pairs[2:])

    palette_rng = _rng(seed, split, slot, "negative-colors")
    colors = list(range(1, 10))
    palette_rng.shuffle(colors)
    for index in range(negative_count):
        if index % 2 == 0:
            specs.append(("one", (colors[index % len(colors)],)))
        else:
            start = (3 * index) % len(colors)
            triple = tuple(colors[(start + offset) % len(colors)] for offset in range(3))
            specs.append(("three", triple))

    positions = _slots(height, width)
    if len(specs) > len(positions):
        raise AssertionError("profile has more objects than separated slots")
    layout_rng = _rng(seed, split, slot, "layout")
    layout_rng.shuffle(positions)
    layout_rng.shuffle(specs)
    mask_pool = _DENSE_MASKS if profile.get("dense") else _MASKS
    masks = list(mask_pool)
    mask_rng = _rng(seed, split, slot, "masks")
    mask_rng.shuffle(masks)

    grid = [[0 for _ in range(width)] for _ in range(height)]
    pattern_rng = _rng(seed, split, slot, "patterns")
    for index, ((kind, payload), origin) in enumerate(zip(specs, positions)):
        mask = masks[index % len(masks)]
        if kind == "two":
            _paint_two(grid, origin, mask, payload, index + slot, pattern_rng)
        else:
            _paint_negative(grid, origin, mask, payload)

    facts = object_facts(grid)
    expected_two = sum(repeated_counts) + unique_count
    if len(facts["objects"]) != len(specs):
        raise AssertionError("objects merged despite separated slots")
    if len(facts["two_color_objects"]) != expected_two:
        raise AssertionError("two-color object count drifted")
    observed_counts = sorted(facts["pair_counts"].values(), reverse=True)
    if sorted(observed_counts, reverse=True) != sorted((*repeated_counts, *(1 for _ in range(unique_count))), reverse=True):
        raise AssertionError("pair multiplicities drifted")
    if facts["negative_object_count"] != negative_count:
        raise AssertionError("negative control count drifted")
    if apply_scope(grid, "all_two_color") == apply_scope(grid, "repeated_pair"):
        raise AssertionError("profile does not distinguish settings")
    return grid


def episode_inputs(seed: int, demos: int, queries: int) -> list[Grid]:
    seed = _validate_seed(seed)
    demos = _validate_count(demos, "demos", MIN_DEMOS, MAX_DEMOS)
    queries = _validate_count(queries, "queries", MIN_QUERIES, MAX_QUERIES)
    demo_inputs = [_make_input(seed, "demo", slot, _DEMO_PROFILES[slot]) for slot in range(demos)]
    query_inputs = [_make_input(seed, "query", slot, _QUERY_PROFILES[slot]) for slot in range(queries)]
    result = demo_inputs + query_inputs
    frozen = {tuple(tuple(row) for row in grid) for grid in result}
    if len(frozen) != len(result):
        raise AssertionError("episode inputs must be distinct")
    return result


def generate_episode(seed: int, swap_scope: str, demos: int, queries: int) -> dict[str, Any]:
    swap_scope = _validate_scope(swap_scope)
    inputs = episode_inputs(seed, demos, queries)
    return {
        "train": [
            {"input": grid, "output": apply_scope(grid, swap_scope)}
            for grid in inputs[:demos]
        ],
        "test": [
            {"input": grid, "output": apply_scope(grid, swap_scope)}
            for grid in inputs[demos:]
        ],
        "program_solution": program_for(swap_scope),
    }


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    if type(query_index) is not int:
        raise TypeError("query_index must be an exact integer")
    if type(episode) is not dict:
        raise TypeError("episode must be a dictionary")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode needs train and test lists")
    if not 0 <= query_index < len(test):
        raise IndexError("query_index is outside the private query list")
    visible_train = []
    for pair in train:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("every demonstration needs input and output")
        visible_train.append({"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])})
    query = test[query_index]
    if type(query) is not dict or "input" not in query:
        raise ValueError("query needs an input")
    return {"train": visible_train, "test": [{"input": deepcopy(query["input"])}]}
