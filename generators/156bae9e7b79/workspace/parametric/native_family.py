"""Native sequential family for keyed triangular projection.

The canonical setting is byte-for-byte the selected rule.  The alternative first
constructs that canonical projection, then finds the most frequent projected
non-background/non-cyan color and recolors it to 9.  The winner is therefore a
property of the input-dependent intermediate, not merely of the key row.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any

TASK_ID = "156bae9e7b79"
PARAMETER = "postprocess"
SETTINGS = ("canonical", "highlight_projected_majority")
DEFAULT = {PARAMETER: "canonical"}
LIMITS = {"demos": [2, 6], "queries": [1, 4]}
HERE = Path(__file__).resolve().parent
CANONICAL = (HERE / "canonical.rkt").read_text(encoding="utf-8")
if not CANONICAL.startswith("(rule! ") or not CANONICAL.endswith(")"):
    raise RuntimeError("canonical program has an unexpected wrapper")
_CANONICAL_BODY = CANONICAL[len("(rule! "):-1]


def _majority_racket(cells_name: str, eligible_expression: str) -> str:
    return f"""(let* ((eligible {eligible_expression}))
      (if (empty? eligible)
          #f
          (let loop ((remaining (rest eligible))
                     (best (first eligible))
                     (best-count (count-where (lambda (value) (= value (first eligible))) {cells_name})))
            (if (empty? remaining)
                best
                (let* ((candidate (first remaining))
                       (candidate-count (count-where (lambda (value) (= value candidate)) {cells_name})))
                  (if (> candidate-count best-count)
                      (loop (rest remaining) candidate candidate-count)
                      (loop (rest remaining) best best-count)))))))"""


_PROJECTED_ELIGIBLE = (
    "(filter (lambda (color) (and (!= color 5) (!= color 8) (!= color 9) "
    "(member color cells))) (range 0 10))"
)
_KEY_ELIGIBLE = (
    "(filter (lambda (color) (and (!= color 5) (!= color 8) (!= color 9) "
    "(member color key))) (range 0 10))"
)

ALTERNATIVE = f"""(rule! (lambda (g)
  (let* ((projected ({_CANONICAL_BODY} g))
         (hh (rows projected))
         (ww (cols projected))
         (cells (for*/list ((r (range 0 hh)) (c (range 0 ww))) (at projected r c)))
         (winner {_majority_racket('cells', _PROJECTED_ELIGIBLE)}))
    (if winner
        (build-grid hh ww (r c)
          (let ((value (at projected r c))) (if (= value winner) 9 value)))
        projected))))"""

WRONG_ORDER = f"""(rule! (lambda (g)
  (let* ((ww (cols g))
         (key (for/list ((c (range 0 ww))) (at g 0 c)))
         (winner {_majority_racket('key', _KEY_ELIGIBLE)})
         (projected ({_CANONICAL_BODY} g))
         (hh (rows projected)))
    (if winner
        (build-grid hh ww (r c)
          (let ((value (at projected r c))) (if (= value winner) 9 value)))
        projected))))"""


def _setting(settings: Any) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {PARAMETER}
        or type(settings[PARAMETER]) is not str
        or settings[PARAMETER] not in SETTINGS
    ):
        raise ValueError("settings must contain exactly postprocess=canonical or highlight_projected_majority")
    return settings[PARAMETER]


def program(settings: Any) -> str:
    return CANONICAL if _setting(settings) == "canonical" else ALTERNATIVE


def counterfactual_program() -> str:
    return WRONG_ORDER


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def validate_input(grid: Any) -> tuple[int, int, int, int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    h, w = len(grid), len(grid[0])
    if not 2 <= h <= 30 or not 3 <= w <= 30:
        raise ValueError("grid size must be within 2..30 by 3..30")
    if any(type(row) is not list or len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("cells must be exact integer ARC colors")
    line_cells = [(r, c) for r in range(1, h) for c in range(w) if grid[r][c] == 8]
    if not line_cells or len({c for _, c in line_cells}) != 1:
        raise ValueError("need exactly one cyan line column below the key row")
    line_col = line_cells[0][1]
    rows = sorted(r for r, _ in line_cells)
    if rows != list(range(rows[0], rows[-1] + 1)):
        raise ValueError("cyan line must be contiguous")
    if grid[0][line_col] != 5 or any(grid[0][c] == 5 for c in range(w) if c != line_col):
        raise ValueError("key row must use gray only at the line column")
    if any(grid[r][c] not in (5, 8) for r in range(1, h) for c in range(w)):
        raise ValueError("below the key row only gray and the cyan line are allowed")
    if any(value == 9 for value in grid[0]):
        raise ValueError("parametric inputs reserve color 9 for the second stage")
    return h, w, line_col, rows[0], rows[-1]


def project(grid: list[list[int]]) -> list[list[int]]:
    h, w, line_col, line_top, line_bottom = validate_input(grid)
    key = grid[0]
    out = [[5] * w for _ in range(h)]
    max_radius = (w - 1) // 2
    for r in range(line_top, line_bottom + 1):
        radius = min(max_radius, r - line_top)
        for c in range(w):
            if c == line_col:
                out[r][c] = 8
            elif line_col - radius <= c <= line_col + radius:
                out[r][c] = key[c]
    return out


def _majority(values: list[int], excluded: set[int]) -> int:
    counts = {color: values.count(color) for color in range(10) if color not in excluded and color in values}
    if not counts:
        raise ValueError("no eligible color")
    return min(counts, key=lambda color: (-counts[color], color))


def projected_majority(projected: list[list[int]]) -> int:
    return _majority([value for row in projected for value in row], {5, 8, 9})


def key_row_majority(grid: list[list[int]]) -> int:
    validate_input(grid)
    return _majority(list(grid[0]), {5, 8, 9})


def solve(grid: list[list[int]], setting: str = "canonical") -> list[list[int]]:
    if setting not in SETTINGS:
        raise ValueError("unknown postprocess setting")
    intermediate = project(grid)
    if setting == "canonical":
        return intermediate
    winner = projected_majority(intermediate)
    return [[9 if value == winner else value for value in row] for row in intermediate]


def solve_wrong_order(grid: list[list[int]]) -> list[list[int]]:
    winner = key_row_majority(grid)
    return [[9 if value == winner else value for value in row] for row in project(grid)]


def _rng(seed: int, stream: str) -> random.Random:
    _integer(seed, 0, 2**63 - 1, "seed")
    digest = hashlib.sha256(f"{TASK_ID}:native-v2:{seed}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


# height, width, line column, line top, line bottom
_DEMO_SPECS = (
    (9, 9, 4, 2, 8),
    (11, 13, 4, 3, 10),
    (13, 11, 7, 4, 11),
    (15, 17, 5, 3, 14),
    (19, 21, 14, 5, 18),
    (24, 25, 8, 6, 22),
)
_QUERY_SPECS = (
    (10, 12, 6, 2, 9),
    (16, 18, 11, 4, 15),
    (23, 27, 9, 5, 21),
    (30, 30, 14, 4, 29),
)


def _scene(seed: int, spec: tuple[int, int, int, int, int], stream: str) -> list[list[int]]:
    h, w, line_col, line_top, line_bottom = spec
    rng = _rng(seed, stream)
    palette = rng.sample([0, 1, 2, 3, 4, 6, 7], 7)
    focus, decoy = palette[:2]
    others = palette[2:]
    active_rows = line_bottom - line_top + 1
    weighted = []
    for c in range(w):
        if c == line_col:
            continue
        distance = abs(c - line_col)
        weight = max(0, active_rows - distance) if distance <= (w - 1) // 2 else 0
        weighted.append((weight, c))
    weighted.sort(key=lambda item: (-item[0], item[1]))

    key = [others[(c + seed) % len(others)] for c in range(w)]
    key[line_col] = 5
    # High-weight columns make the projected winner; low-weight columns make a
    # different key-row majority, which supplies the retained wrong-order case.
    for _, c in weighted[: max(2, min(4, len(weighted) // 4))]:
        key[c] = focus
    low = sorted(weighted, key=lambda item: (item[0], -item[1]))
    for _, c in low[: max(4, len(weighted) // 3)]:
        key[c] = decoy
    # Deterministically repair either majority without an unbounded sampler.
    for _ in range(w * 2):
        grid = [[5] * w for _ in range(h)]
        grid[0] = key[:]
        for r in range(line_top, line_bottom + 1):
            grid[r][line_col] = 8
        projected = project(grid)
        if projected_majority(projected) == focus and key_row_majority(grid) == decoy:
            return grid
        # Strengthen the projected winner at the highest remaining weight.
        candidate = next((c for _, c in weighted if key[c] not in (focus, 5)), None)
        if candidate is None:
            break
        key[candidate] = focus
        # Preserve an unweighted decoy majority using the least influential slot.
        counts = {color: key.count(color) for color in set(key) - {5}}
        if counts.get(decoy, 0) <= counts.get(focus, 0):
            spare = next((c for _, c in low if key[c] not in (decoy, 5) and c != candidate), None)
            if spare is not None:
                key[spare] = decoy
    raise RuntimeError(f"could not construct a causal scene for {stream}")


def input_bank(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    train = [_scene(seed, spec, f"demo:{i}") for i, spec in enumerate(_DEMO_SPECS)]
    test = [_scene(seed, spec, f"query:{i}") for i, spec in enumerate(_QUERY_SPECS)]
    keys = [tuple(map(tuple, grid)) for grid in train + test]
    if len(keys) != len(set(keys)):
        raise RuntimeError("constructed inputs must be distinct")
    return train, test


def generate(seed: int, settings: dict[str, str] | None = None, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    if settings is None:
        settings = {PARAMETER: SETTINGS[_rng(seed, "setting").randrange(len(SETTINGS))]}
    setting = _setting(settings)
    train, test = input_bank(seed)

    def pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
        return {"input": deepcopy(grid), "output": solve(grid, setting)}

    return {
        "train": [pair(grid) for grid in train[:demos]],
        "test": [pair(grid) for grid in test[:queries]],
        "program_solution": program(settings),
        "settings": dict(settings),
    }


def public_turn(episode: dict[str, Any], index: int = 0) -> dict[str, Any]:
    tests = episode.get("test")
    if type(index) is not int or not isinstance(tests, list) or not 0 <= index < len(tests):
        raise ValueError("query index out of range")
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(tests[index]["input"])}],
    }
