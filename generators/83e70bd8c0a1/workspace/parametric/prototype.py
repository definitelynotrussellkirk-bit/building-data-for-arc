"""Matched-input anti-diagonal reflection and landing-cue relay episodes.

Python outputs are deterministic claims. Native qualification independently
executes every claimed label through the protected Racket runtime.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import random

TASK_ID = "83e70bd8c0a1"
VERSION = "probe-relay-v1"
HOME = Path(__file__).resolve().parent
RULES = ("full_reflection", "probe_relay")
CUE_COLORS = (2, 3, 4)
DEMO_SIZES = (7, 8, 9, 11, 13, 16)
QUERY_SIZES = (10, 15, 22, 30)

_PROBE_RELAY_PROGRAM = r"""(rule!
 ;; Move the unique blue probe by anti-diagonal reflection. Read the unique
 ;; nonblack landing cue, then transpose only that cue color's whole payload.
 (lambda (g)
   (define h (rows g))
   (define w (cols g))
   (define probe (first (find-color g 1)))
   (define sr (first probe))
   (define sc (second probe))
   (define dr (- h 1 sc))
   (define dc (- w 1 sr))
   (define moved
     (grid-from-fn h w
       (lambda (r c)
         (cond
           ((and (= r sr) (= c sc)) 0)
           ((and (= r dr) (= c dc)) 1)
           (else (at g r c))))))
   (define selected
     (find-first
       (lambda (v) (and (not (= v 0)) (not (= v 1))))
       (neighbors-4 moved dr dc 0)))
   (grid-from-fn h w
     (lambda (r c)
       (cond
         ((= (at moved c r) selected) selected)
         ((= (at moved r c) selected) 0)
         (else (at moved r c)))))))"""


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _rule(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {"rule"}:
        raise ValueError("settings must contain exactly 'rule'")
    value = settings["rule"]
    if type(value) is not str or value not in RULES:
        raise ValueError(f"rule must be one of {RULES}")
    return value


def program(settings: object) -> str:
    rule = _rule(settings)
    if rule == "full_reflection":
        return (HOME / "canonical.rkt").read_bytes().decode("utf-8")
    return _PROBE_RELAY_PROGRAM


def _anti(cell: tuple[int, int], n: int) -> tuple[int, int]:
    r, c = cell
    return n - 1 - c, n - 1 - r


def _cardinal(cell: tuple[int, int], n: int) -> set[tuple[int, int]]:
    r, c = cell
    return {
        (rr, cc)
        for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
        if 0 <= rr < n and 0 <= cc < n
    }


def _rng(seed: int, split: str, index: int) -> random.Random:
    payload = f"{TASK_ID}/{VERSION}/{seed}/{split}/{index}".encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _payload_shapes(n: int, variant: int) -> list[set[tuple[int, int]]]:
    """Three separated ribbons in the upper triangle; all transpose nontrivially."""
    height = max(1, min(4, (n + 3) // 8))
    length = max(2, min(8, n // 3))
    max_start = max(0, n - height - length - 2)
    starts = [0, max_start // 2, max_start]
    shapes: list[set[tuple[int, int]]] = []
    for shape_index, start_row in enumerate(starts):
        cells: set[tuple[int, int]] = set()
        for dr in range(height):
            row = start_row + dr
            start_col = row + 3
            width = max(2, length - ((variant + shape_index + dr) % 2))
            if start_col + width > n:
                start_col = row + 3
                width = min(width, n - start_col)
            for column in range(start_col, start_col + width):
                if column - row >= 3:
                    cells.add((row, column))
        if len(cells) < 2:
            raise AssertionError("payload construction lost its nontrivial shape")
        shapes.append(cells)
    if any(a & b for i, a in enumerate(shapes) for b in shapes[i + 1 :]):
        raise AssertionError("payload shapes overlap")
    return shapes


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    sizes = DEMO_SIZES if split == "train" else QUERY_SIZES
    n = sizes[index]
    ordinal = index if split == "train" else len(DEMO_SIZES) + index
    rng = _rng(seed, split, index)

    candidates = [k for k in range(1, n - 2) if n - 2 - k >= k + 2]
    if not candidates:
        raise AssertionError("scene too small for separated source and landing cues")
    k = candidates[(seed + ordinal) % len(candidates)]
    j = n - 2 - k
    above = (seed + ordinal) % 2 == 0
    source = (k, k + 1) if above else (k + 1, k)
    destination = _anti(source, n)
    expected_destination = (j, j + 1) if above else (j + 1, j)
    if destination != expected_destination:
        raise AssertionError("anti-diagonal source geometry drifted")

    excluded_diagonal = {k - 1, k, k + 1, j - 1, j, j + 1}
    decoy_candidates = [d for d in range(n) if d not in excluded_diagonal]
    if not decoy_candidates:
        raise AssertionError("no room for a third cue")
    t = decoy_candidates[(seed + 2 * ordinal) % len(decoy_candidates)]

    landing_color = CUE_COLORS[(seed + ordinal) % len(CUE_COLORS)]
    original_color = CUE_COLORS[(seed + ordinal + 1) % len(CUE_COLORS)]
    decoy_color = next(
        color for color in CUE_COLORS if color not in (landing_color, original_color)
    )

    grid = [[0 for _ in range(n)] for _ in range(n)]
    grid[k][k] = original_color
    grid[j][j] = landing_color
    grid[t][t] = decoy_color
    grid[source[0]][source[1]] = 1

    protected = (
        {source, destination, (k, k), (j, j), (t, t)}
        | _cardinal(source, n)
        | _cardinal(destination, n)
    )
    shapes = _payload_shapes(n, variant=(seed + ordinal) % 7)
    shape_colors = list(CUE_COLORS)
    rng.shuffle(shape_colors)
    payload_cells: dict[int, set[tuple[int, int]]] = {color: set() for color in CUE_COLORS}
    occupied = set(protected)
    for color, shape in zip(shape_colors, shapes, strict=True):
        for cell in sorted(shape):
            if cell in occupied:
                continue
            r, c = cell
            if c - r < 2:
                continue
            grid[r][c] = color
            payload_cells[color].add(cell)
            occupied.add(cell)
    if any(len(payload_cells[color]) < 2 for color in CUE_COLORS):
        raise AssertionError("each cue color needs a nontrivial remote payload")

    transpose_targets = {(c, r) for cells in payload_cells.values() for r, c in cells}
    blocked = occupied | transpose_targets | _cardinal(source, n) | _cardinal(destination, n)

    # Edge anchors and lower-triangle texture make the 30x30 case real rather
    # than a small puzzle centered on a padded canvas. They never use cue colors.
    edge_cells = ((0, n - 1), (n - 1, 0), (0, 0), (n - 1, n - 1))
    for color, cell in zip((5, 6, 7, 8), edge_cells, strict=True):
        if cell not in blocked and grid[cell[0]][cell[1]] == 0:
            grid[cell[0]][cell[1]] = color
            occupied.add(cell)

    lower = [
        (r, c)
        for r in range(n)
        for c in range(n)
        if r - c >= 2 and (r, c) not in blocked and grid[r][c] == 0
    ]
    rng.shuffle(lower)
    texture_count = min(len(lower), max(6, 2 * n))
    for position_index, (r, c) in enumerate(lower[:texture_count]):
        grid[r][c] = 5 + ((position_index + seed + ordinal) % 5)

    # Validate the causal carrier before emitting the scene.
    if sum(value == 1 for row in grid for value in row) != 1:
        raise AssertionError("scene must have exactly one probe")
    if grid[destination[0]][destination[1]] != 0:
        raise AssertionError("probe destination must start empty")
    if _cue_color(grid, source) != original_color:
        raise AssertionError("source cue is not unique")
    moved = _move_probe(grid)
    if _cue_color(moved, destination) != landing_color:
        raise AssertionError("landing cue is not unique")
    return grid


def _probe_position(grid: list[list[int]]) -> tuple[int, int]:
    positions = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    ]
    if len(positions) != 1:
        raise ValueError("input must contain exactly one blue probe")
    return positions[0]


def _cue_color(grid: list[list[int]], position: tuple[int, int]) -> int:
    n = len(grid)
    values = [
        grid[r][c]
        for r, c in _cardinal(position, n)
        if grid[r][c] not in (0, 1)
    ]
    if len(values) != 1:
        raise ValueError("probe position must have exactly one nonblack nonprobe cue")
    return values[0]


def _move_probe(grid: list[list[int]], *, keep_source: bool = False) -> list[list[int]]:
    n = len(grid)
    source = _probe_position(grid)
    destination = _anti(source, n)
    output = copy.deepcopy(grid)
    if not keep_source:
        output[source[0]][source[1]] = 0
    output[destination[0]][destination[1]] = 1
    return output


def _transpose_color(grid: list[list[int]], color: int) -> list[list[int]]:
    output = copy.deepcopy(grid)
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]
    for r, c in cells:
        output[r][c] = 0
    for r, c in cells:
        output[c][r] = color
    return output


def full_reflection(grid: list[list[int]]) -> list[list[int]]:
    n = len(grid)
    return [
        [grid[n - 1 - c][n - 1 - r] for c in range(n)]
        for r in range(n)
    ]


def relay_output(grid: list[list[int]]) -> list[list[int]]:
    moved = _move_probe(grid)
    selected = _cue_color(moved, _probe_position(moved))
    return _transpose_color(moved, selected)


def _label(grid: list[list[int]], rule: str) -> list[list[int]]:
    return full_reflection(grid) if rule == "full_reflection" else relay_output(grid)


def generate(seed: object, settings: object, demos: object, queries: object) -> dict:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    rule = _rule(settings)

    train_inputs = [_scene(seed, "train", index) for index in range(demos)]
    test_inputs = [_scene(seed, "test", index) for index in range(queries)]
    return {
        "schema": "anti-diagonal-probe-relay-episode-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": {"rule": rule},
        "train": [
            {"input": copy.deepcopy(grid), "output": _label(grid, rule)}
            for grid in train_inputs
        ],
        "test": [
            {"input": copy.deepcopy(grid), "output": _label(grid, rule)}
            for grid in test_inputs
        ],
        "program_solution": program({"rule": rule}),
    }


def public_view(episode: object, query_index: object) -> dict:
    if type(episode) is not dict:
        raise ValueError("episode must be a generated episode dictionary")
    tests = episode.get("test")
    trains = episode.get("train")
    if type(trains) is not list or type(tests) is not list or not trains or not tests:
        raise ValueError("episode must contain nonempty train and test lists")
    query_index = _integer(query_index, 0, len(tests) - 1, "query_index")
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in trains
        ],
        "test": [{"input": copy.deepcopy(tests[query_index]["input"])}],
    }
