"""Episode-fixed completion rule with an input-derived dominant-target route.

The default returns the selected canonical program byte-for-byte.  The alternate
first discovers and applies every canonical local 2x2 completion, counts those
new cells by colour, selects the unique most-completed colour, then connects its
new cells along shared rows and columns.  Inputs are sampled independently of the
private setting; Python labels are claims replayed by native protected Racket.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
from pathlib import Path
import random
from typing import Any

_CANONICAL = Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")
_RULES = ("complete_only", "route_dominant")
_TRAIN_DIMS = ((8, 10), (10, 12), (12, 14), (14, 18), (18, 22), (22, 26))
_TEST_DIMS = ((11, 15), (16, 20), (24, 27), (30, 30))


def _integer(value: Any, minimum: int, maximum: int, name: str) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an exact integer in {minimum}..{maximum}")
    return value


def _finish_rule(settings: Any) -> str:
    if (type(settings) is not dict or set(settings) != {"finish_rule"}
            or type(settings["finish_rule"]) is not str
            or settings["finish_rule"] not in _RULES):
        raise ValueError(
            "settings must be exactly {'finish_rule': 'complete_only'|'route_dominant'}"
        )
    return settings["finish_rule"]


def _grid(grid: Any) -> list[list[int]]:
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(value) is not int or not 0 <= value <= 9 for value in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact integer ARC colours")
    return [row[:] for row in grid]


def _fills(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    height, width = len(grid), len(grid[0])
    result: list[tuple[int, int, int]] = []
    for row in range(height - 1):
        for col in range(width - 1):
            cells = ((row, col), (row, col + 1), (row + 1, col), (row + 1, col + 1))
            values = [grid[r][c] for r, c in cells]
            nonzero = [value for value in values if value]
            if len(nonzero) == 3 and len(set(nonzero)) == 1 and values.count(0) == 1:
                r, c = cells[values.index(0)]
                result.append((r, c, nonzero[0]))
    return result


def completion_analysis(grid: Any) -> dict[str, Any]:
    """Return the canonical completion intermediate used by the alternate rule."""
    source = _grid(grid)
    fills = _fills(source)
    counts = Counter(color for _row, _col, color in fills)
    targets: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for row, col, color in fills:
        if (row, col) not in targets[color]:
            targets[color].append((row, col))
    dominant = None
    if counts:
        dominant = min(counts, key=lambda color: (-counts[color], color))
    return {
        "fills": fills,
        "counts": dict(counts),
        "targets_by_color": {color: cells[:] for color, cells in targets.items()},
        "dominant_color": dominant,
    }


def _complete(source: list[list[int]], fills: list[tuple[int, int, int]]) -> list[list[int]]:
    result = [row[:] for row in source]
    for row, col, color in fills:
        result[row][col] = color
    return result


def _paint_segment(grid: list[list[int]], a: tuple[int, int], b: tuple[int, int], color: int) -> None:
    r1, c1 = a
    r2, c2 = b
    if r1 == r2:
        for col in range(min(c1, c2), max(c1, c2) + 1):
            if grid[r1][col] == 0:
                grid[r1][col] = color
    elif c1 == c2:
        for row in range(min(r1, r2), max(r1, r2) + 1):
            if grid[row][c1] == 0:
                grid[row][c1] = color


def transform(grid: Any, settings: Any) -> list[list[int]]:
    """Return a deterministic Python claim for the selected episode rule."""
    finish_rule = _finish_rule(settings)
    source = _grid(grid)
    analysis = completion_analysis(source)
    result = _complete(source, analysis["fills"])
    if finish_rule == "complete_only" or analysis["dominant_color"] is None:
        return result
    color = analysis["dominant_color"]
    targets = analysis["targets_by_color"][color]
    for index, first in enumerate(targets):
        for second in targets[index + 1 :]:
            _paint_segment(result, first, second, color)
    return result


_ALTERNATE = r'''(rule! (let* ((fills (filter values (for*/list ((r (in-range (- (rows g) 1))) (c (in-range (- (cols g) 1)))) (let* ((pts (list (list r c) (list r (+ c 1)) (list (+ r 1) c) (list (+ r 1) (+ c 1)))) (vals (map (lambda (p) (at g (first p) (second p))) pts)) (nz (filter (lambda (v) (not (= v 0))) vals))) (if (and (= (length nz) 3) (= (length (remove-duplicates nz)) 1) (= (length (filter (lambda (v) (= v 0)) vals)) 1)) (let ((p (first (filter (lambda (p) (= (at g (first p) (second p)) 0)) pts)))) (list (first p) (second p) (first nz))) #f))))) (intermediate (for/fold ((out g)) ((item (in-list fills))) (set-cell out (first item) (second item) (third item)))) (colors (remove-duplicates (map third fills))) (winner (pick-max colors (lambda (color) (count-if (lambda (item) (= (third item) color)) fills)))) (targets (filter (lambda (item) (= (third item) winner)) fills)) (pairs (filter values (for*/list ((a (in-list targets)) (b (in-list targets))) (if (and (or (< (first a) (first b)) (and (= (first a) (first b)) (< (second a) (second b)))) (or (= (first a) (first b)) (= (second a) (second b)))) (list a b) #f))))) (for/fold ((out intermediate)) ((pair (in-list pairs))) (let* ((a (first pair)) (b (second pair)) (r1 (first a)) (c1 (second a)) (r2 (first b)) (c2 (second b))) (if (= r1 r2) (for/fold ((line out)) ((c (in-range (min c1 c2) (+ (max c1 c2) 1)))) (if (= (at line r1 c) 0) (set-cell line r1 c winner) line)) (for/fold ((line out)) ((r (in-range (min r1 r2) (+ (max r1 r2) 1)))) (if (= (at line r c1) 0) (set-cell line r c1 winner) line)))))))'''


def program(settings: Any) -> str:
    """Return one complete Racket rule; the default is byte-exact canonical."""
    return _CANONICAL if _finish_rule(settings) == "complete_only" else _ALTERNATE


def _rng(seed: int, purpose: str) -> random.Random:
    raw = f"6d678fbbe87e/dominant-route-v1/{seed}/{purpose}".encode("ascii")
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _stamp_missing(grid: list[list[int]], target: tuple[int, int], color: int, corner: str) -> None:
    row, col = target
    if corner == "br":
        block = ((row - 1, col - 1), (row - 1, col), (row, col - 1), (row, col))
        missing = 3
    elif corner == "bl":
        block = ((row - 1, col), (row - 1, col + 1), (row, col), (row, col + 1))
        missing = 2
    elif corner == "tr":
        block = ((row, col - 1), (row, col), (row + 1, col - 1), (row + 1, col))
        missing = 1
    else:
        raise ValueError(f"unknown missing corner {corner!r}")
    height, width = len(grid), len(grid[0])
    if any(not (0 <= r < height and 0 <= c < width) for r, c in block):
        raise ValueError("completion motif does not fit")
    for index, (r, c) in enumerate(block):
        expected = 0
        if grid[r][c] != expected:
            raise ValueError(f"completion motif collision at {(r, c)}")
        if index != missing:
            grid[r][c] = color


def _palette(seed: int, split: str, index: int) -> tuple[int, int, int]:
    colors = sorted(_rng(seed, f"{split}/{index}/palette").sample(range(1, 10), 3))
    pattern = index % 3
    if pattern == 0:
        return colors[2], colors[0], colors[1]
    if pattern == 1:
        return colors[1], colors[2], colors[0]
    return colors[0], colors[1], colors[2]


def _dimensions(split: str, index: int) -> tuple[int, int]:
    return (_TRAIN_DIMS if split == "train" else _TEST_DIMS)[index]


def sample_input(
    seed: Any,
    split: str,
    index: Any,
    *,
    height: int | None = None,
    width: int | None = None,
) -> list[list[int]]:
    """Construct a matched scene with a 3/2/1 completion-count curriculum."""
    _integer(seed, 0, 2**63 - 1, "seed")
    if type(split) is not str or split not in ("train", "test"):
        raise ValueError("split must be 'train' or 'test'")
    _integer(index, 0, 5 if split == "train" else 3, "index")
    if height is None and width is None:
        height, width = _dimensions(split, index)
    elif height is None or width is None:
        raise ValueError("height and width must be supplied together")
    else:
        _integer(height, 8, 30, "height")
        _integer(width, 10, 30, "width")

    dominant, runner, singleton = _palette(seed, split, index)
    grid = [[0] * width for _ in range(height)]

    # Three dominant targets form an L route whose input motifs touch top, left,
    # right and bottom boundaries.  Their missing cells are the route endpoints.
    _stamp_missing(grid, (1, 1), dominant, "br")
    _stamp_missing(grid, (1, width - 2), dominant, "bl")
    _stamp_missing(grid, (height - 2, 1), dominant, "tr")

    # Two aligned runner-up targets deliberately remain unbridged under the
    # alternate rule, distinguishing winner selection from bridge-everything.
    runner_row = max(4, height // 2)
    runner_left = max(4, width // 3)
    _stamp_missing(grid, (runner_row, runner_left), runner, "br")
    _stamp_missing(grid, (runner_row, width - 2), runner, "bl")

    # One additional completion creates the 3/2/1 count ladder.
    singleton_col = max(4, width // 2)
    _stamp_missing(grid, (height - 1, singleton_col), singleton, "br")

    # A large solid runner-up rectangle makes raw input-frequency and largest-
    # object selectors choose the wrong colour without creating new completions.
    rect_row = runner_row + 2
    rect_col = singleton_col + 2
    for row in range(rect_row, height):
        for col in range(rect_col, width):
            if grid[row][col] != 0:
                raise ValueError("solid distractor collision")
            grid[row][col] = runner

    # Whole-scene reflections add geometry variation while retaining exact roles.
    rng = _rng(seed, f"{split}/{index}/{height}x{width}/reflection")
    if rng.randrange(2):
        grid = [list(reversed(row)) for row in grid]
    if rng.randrange(2):
        grid = list(reversed(grid))

    analysis = completion_analysis(grid)
    if sorted(analysis["counts"].values()) != [1, 2, 3]:
        raise AssertionError(f"constructed scene has wrong completion counts: {analysis['counts']}")
    winner = analysis["dominant_color"]
    input_counts = {color: sum(value == color for row in grid for value in row)
                    for color in analysis["counts"]}
    if max(input_counts, key=input_counts.get) == winner:
        raise AssertionError("raw input frequency accidentally identifies the winner")
    return grid


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    """Generate prefix-stable demonstrations and private query labels."""
    _integer(seed, 0, 2**63 - 1, "seed")
    _finish_rule(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    episode: dict[str, Any] = {"program_solution": program(settings)}
    for split, count in (("train", demos), ("test", queries)):
        pairs = []
        for index in range(count):
            source = sample_input(seed, split, index)
            pairs.append({"input": source, "output": transform(source, settings)})
        episode[split] = pairs
    return episode
