"""Native sequential family for priority-quadrant overlay.

The canonical setting is the exact selected rule.  The alternative first
constructs that overlay, then selects the most frequent visible nonzero color
and recolors it to 9.  A retained counterfactual selects from raw source cells
before occlusion, which is observably different on the generated scenes.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any

TASK_ID = "a23328d45092"
PARAMETER = "postprocess"
SETTINGS = ("canonical", "highlight_visible_majority")
DEFAULT = {PARAMETER: "canonical"}
LIMITS = {"demos": [2, 6], "queries": [1, 4]}
HERE = Path(__file__).resolve().parent
CANONICAL = (HERE / "canonical.rkt").read_text(encoding="utf-8")
if not CANONICAL.startswith("(rule! ") or not CANONICAL.endswith(")"):
    raise RuntimeError("canonical program has an unexpected wrapper")
_CANONICAL_BODY = CANONICAL[len("(rule! "):-1]


def _majority_racket(cells_name: str) -> str:
    eligible = (
        f"(filter (lambda (color) (and (!= color 0) (!= color 1) (!= color 9) "
        f"(member color {cells_name}))) (range 0 10))"
    )
    return f"""(let* ((eligible {eligible}))
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


ALTERNATIVE = f"""(rule! (lambda (g)
  (let* ((overlaid ({_CANONICAL_BODY} g))
         (hh (rows overlaid))
         (ww (cols overlaid))
         (cells (for*/list ((r (range 0 hh)) (c (range 0 ww))) (at overlaid r c)))
         (winner {_majority_racket('cells')}))
    (if winner
        (build-grid hh ww (r c)
          (let ((value (at overlaid r c))) (if (= value winner) 9 value)))
        overlaid))))"""

WRONG_ORDER = f"""(rule! (lambda (g)
  (let* ((hh (rows g))
         (ww (cols g))
         (source-cells (for*/list ((r (range 0 hh)) (c (range 0 ww))) (at g r c)))
         (winner {_majority_racket('source-cells')})
         (overlaid ({_CANONICAL_BODY} g))
         (oh (rows overlaid))
         (ow (cols overlaid)))
    (if winner
        (build-grid oh ow (r c)
          (let ((value (at overlaid r c))) (if (= value winner) 9 value)))
        overlaid))))"""


def _setting(settings: Any) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {PARAMETER}
        or type(settings[PARAMETER]) is not str
        or settings[PARAMETER] not in SETTINGS
    ):
        raise ValueError("settings must contain exactly postprocess=canonical or highlight_visible_majority")
    return settings[PARAMETER]


def program(settings: Any) -> str:
    return CANONICAL if _setting(settings) == "canonical" else ALTERNATIVE


def counterfactual_program() -> str:
    return WRONG_ORDER


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _rng(seed: int, stream: str) -> random.Random:
    _integer(seed, 0, 2**63 - 1, "seed")
    digest = hashlib.sha256(f"{TASK_ID}:native-v1:{seed}:{stream}".encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _separators(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    h, w = len(grid), len(grid[0])
    if not 5 <= h <= 30 or not 5 <= w <= 30:
        raise ValueError("grid dimensions must be in 5..30")
    if any(type(row) is not list or len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be exact integer ARC colors")
    rows = [r for r, row in enumerate(grid) if all(value == 1 for value in row)]
    cols = [c for c in range(w) if all(grid[r][c] == 1 for r in range(h))]
    if len(rows) != 1 or len(cols) != 1:
        raise ValueError("need exactly one full row and one full column of 1s")
    sr, sc = rows[0], cols[0]
    if sr < 2 or sc < 2 or sr + 1 + sr > h or sc + 1 + sc > w:
        raise ValueError("separator must leave four aligned output-sized quadrants")
    if any(value == 9 for r, row in enumerate(grid) for c, value in enumerate(row) if r != sr and c != sc):
        raise ValueError("parametric inputs reserve color 9 for the second stage")
    return sr, sc


def overlay(grid: list[list[int]]) -> list[list[int]]:
    sr, sc = _separators(grid)
    output = [[0 for _ in range(sc)] for _ in range(sr)]
    for r in range(sr):
        for c in range(sc):
            values = (
                grid[r][c],
                grid[r][sc + 1 + c],
                grid[sr + 1 + r][c],
                grid[sr + 1 + r][sc + 1 + c],
            )
            output[r][c] = next((value for value in values if value != 0), 0)
    return output


def _majority(values: list[int]) -> int:
    eligible = [value for value in values if value not in (0, 1, 9)]
    if not eligible:
        raise ValueError("no eligible majority color")
    colors = sorted(set(eligible))
    return min(colors, key=lambda color: (-eligible.count(color), color))


def visible_majority(overlaid: list[list[int]]) -> int:
    return _majority([value for row in overlaid for value in row])


def source_majority(grid: list[list[int]]) -> int:
    sr, sc = _separators(grid)
    cells: list[int] = []
    for r in range(sr):
        for c in range(sc):
            cells.extend(
                (
                    grid[r][c],
                    grid[r][sc + 1 + c],
                    grid[sr + 1 + r][c],
                    grid[sr + 1 + r][sc + 1 + c],
                )
            )
    return _majority(cells)


def _mark(overlaid: list[list[int]], winner: int) -> list[list[int]]:
    return [[9 if value == winner else value for value in row] for row in overlaid]


def solve(grid: list[list[int]], setting: str = "canonical") -> list[list[int]]:
    if setting not in SETTINGS:
        raise ValueError("unknown postprocess setting")
    intermediate = overlay(grid)
    if setting == "canonical":
        return intermediate
    return _mark(intermediate, visible_majority(intermediate))


def solve_wrong_order(grid: list[list[int]]) -> list[list[int]]:
    return _mark(overlay(grid), source_majority(grid))


# h, w, separator row, separator column, visible-majority quadrant
_DEMO_SPECS = (
    (9, 9, 4, 4, 0),
    (11, 11, 5, 5, 1),
    (13, 15, 6, 6, 2),
    (15, 13, 6, 6, 0),
    (17, 19, 8, 8, 1),
    (21, 21, 10, 10, 2),
)
_QUERY_SPECS = (
    (10, 12, 4, 5, 2),
    (16, 18, 7, 8, 0),
    (23, 25, 11, 11, 1),
    (30, 30, 14, 14, 2),
)


def _put(grid: list[list[int]], sr: int, sc: int, q: int, r: int, c: int, value: int) -> None:
    offsets = ((0, 0), (0, sc + 1), (sr + 1, 0), (sr + 1, sc + 1))
    ro, co = offsets[q]
    grid[ro + r][co + c] = value


def _scene(seed: int, spec: tuple[int, int, int, int, int], stream: str) -> list[list[int]]:
    h, w, sr, sc, focus_q = spec
    if sr + 1 + sr > h or sc + 1 + sc > w:
        raise RuntimeError("invalid native scene dimensions")
    rng = _rng(seed, stream)
    colors = rng.sample([2, 3, 4, 5, 6, 7, 8], 4)
    grid = [[0 for _ in range(w)] for _ in range(h)]
    for c in range(w):
        grid[sr][c] = 1
    for r in range(h):
        grid[r][sc] = 1

    coords = [(r, c) for r in range(sr) for c in range(sc)]
    rng.shuffle(coords)
    n = len(coords)
    # BR covers every aligned coordinate, making it the source-cell majority.
    for r, c in coords:
        _put(grid, sr, sc, 3, r, c, colors[3])

    # Install disjoint visible regions. Earlier quadrants are deliberately
    # sparse unless they own the majority, so the requested focus survives the
    # canonical priority overlay. The focus receives about 55% of all cells.
    focus_n = max(2, int(n * 0.56))
    early_counts = [max(1, int(n * 0.06)), max(1, int(n * 0.08)), max(1, int(n * 0.10))]
    cursor = 0
    for q in range(3):
        count = focus_n if q == focus_q else early_counts[q]
        # For a later focus, keep earlier occupied positions disjoint so they do
        # not occlude it; for an earlier focus disjointness still makes the
        # visible count transparent and auditable.
        chosen = coords[cursor : min(n, cursor + count)]
        cursor += len(chosen)
        for r, c in chosen:
            _put(grid, sr, sc, q, r, c, colors[q])

    # Guarantee each source quadrant has a witness even on the smallest spec.
    for q in range(3):
        r, c = coords[(q * 7 + seed) % n]
        _put(grid, sr, sc, q, r, c, colors[q])

    overlaid = overlay(grid)
    if visible_majority(overlaid) != colors[focus_q]:
        # Deterministic repair: assign still-visible coordinates to the focus.
        for r, c in coords:
            for earlier in range(focus_q):
                _put(grid, sr, sc, earlier, r, c, 0)
            _put(grid, sr, sc, focus_q, r, c, colors[focus_q])
            overlaid = overlay(grid)
            if visible_majority(overlaid) == colors[focus_q]:
                break
    if visible_majority(overlay(grid)) != colors[focus_q]:
        raise RuntimeError(f"could not establish visible majority for {stream}")
    if source_majority(grid) == visible_majority(overlay(grid)):
        raise RuntimeError(f"source and visible majorities unexpectedly agree for {stream}")
    return grid


def input_bank(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    train = [_scene(seed, spec, f"demo:{index}") for index, spec in enumerate(_DEMO_SPECS)]
    test = [_scene(seed, spec, f"query:{index}") for index, spec in enumerate(_QUERY_SPECS)]
    frozen = [tuple(map(tuple, grid)) for grid in train + test]
    if len(frozen) != len(set(frozen)):
        raise RuntimeError("constructed inputs must be distinct")
    return train, test


def generate(
    seed: int,
    settings: dict[str, str] | None = None,
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
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
