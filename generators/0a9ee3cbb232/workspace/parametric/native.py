"""Native matched-input run-axis family for ARC task 0a9ee3cbb232.

The canonical setting counts maximal horizontal runs of colors 3 then 2.
The nearby setting counts maximal vertical runs.  In both cases Step A derives
an input-dependent pair ``(n3, n2)`` and Step B packs that intermediate into
the same 2x3 row-major tally, naturally truncating after six cells.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

TASK_ID = "0a9ee3cbb232"
PARAMETER = "run_axis"
CANONICAL = "horizontal"
ALTERNATIVE = "vertical"
SETTINGS = (CANONICAL, ALTERNATIVE)
HOME = Path(__file__).resolve().parent
BACKGROUNDS = (0, 1, 4, 5, 6, 7, 8, 9)

# Each rectangle is (color, top, left, height, width).  Same-row and
# same-column split objects are intentional teaching witnesses: they separate
# maximal-run counts from occupied-row/column and component counts.
DEMO_SPECS = (
    (10, 12, ((3, 1, 1, 1, 4), (3, 3, 1, 2, 1),
              (2, 7, 1, 1, 2), (2, 7, 5, 1, 2))),             # H 3,2 / V 5,4
    (11, 13, ((3, 1, 1, 1, 2), (3, 4, 1, 1, 2),
              (2, 1, 9, 4, 1))),                              # H 2,4 / V 4,1
    (12, 14, ((3, 1, 1, 4, 2),
              (2, 8, 1, 1, 3), (2, 8, 7, 1, 2))),             # H 4,2 / V 2,5
    (14, 15, ((3, 1, 1, 1, 5),
              (2, 4, 10, 3, 1), (2, 9, 10, 2, 1))),           # H 1,5 / V 5,2
    (16, 17, ((3, 1, 1, 2, 1), (3, 6, 4, 3, 2),
              (2, 13, 8, 1, 4))),                             # H 5,1 / V 3,4
    (18, 19, ((3, 1, 2, 1, 3), (3, 5, 2, 1, 3),
              (2, 10, 12, 3, 2))),                            # H 2,3 / V 6,2
)
QUERY_SPECS = (
    (20, 22, ((3, 1, 1, 1, 3), (3, 4, 1, 1, 2), (3, 7, 1, 1, 2),
              (2, 12, 14, 4, 2))),                            # H 3,4 / V 7,2
    (22, 24, ((3, 1, 1, 4, 2), (2, 18, 8, 1, 6))),            # H 4,1 / V 2,6
    (24, 26, ((3, 1, 1, 1, 2), (3, 1, 7, 1, 3),
              (2, 10, 18, 2, 1), (2, 15, 16, 3, 2))),         # H 2,5 / V 5,3
    (30, 30, (                                                   # H 3,3 / V 78,73
        (3, 0, 0, 1, 26), (3, 10, 2, 1, 26), (3, 20, 4, 1, 26),
        (2, 5, 0, 1, 24), (2, 15, 3, 1, 25), (2, 29, 6, 1, 24),
    )),
)


def _exact_int(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _setting(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER}")
    value = settings[PARAMETER]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"{PARAMETER} must be one of {SETTINGS}")
    return value


def program(settings: dict[str, Any]) -> str:
    axis = _setting(settings)
    return (HOME / ("canonical.rkt" if axis == CANONICAL else "vertical.rkt")).read_text(
        encoding="utf-8"
    )


def counterfactual_program(n3: int, n2: int) -> str:
    """Materialize Step B with a caller-forced run-count intermediate."""
    n3 = _exact_int(n3, 0, 900, "n3")
    n2 = _exact_int(n2, 0, 900, "n2")
    return f"""(rule! (lambda (g)
  (let* ((n3 {n3}) (n2 {n2}))
    (build-grid 2 3 (r c)
      (let ((i (+ (* r 3) c)))
        (cond ((< i n3) 3) ((< i (+ n3 n2)) 2) (else 0)))))))"""


def _validate_arc_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    height, width = len(grid), len(grid[0])
    if not 1 <= height <= 30 or not 1 <= width <= 30:
        raise ValueError("grid dimensions must be 1..30")
    for row in grid:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(cell) is not int or not 0 <= cell <= 9 for cell in row):
            raise ValueError("grid cells must be exact integer ARC colors")
    return height, width


def _validate_grid(grid: Any) -> tuple[int, int]:
    height, width = _validate_arc_grid(grid)
    if not all(any(cell == color for row in grid for cell in row) for color in (3, 2)):
        raise ValueError("both colors 3 and 2 must occur")
    return height, width


def _run_count(lines: list[list[int]], color: int) -> int:
    total = 0
    for line in lines:
        active = False
        for value in line:
            if value == color:
                if not active:
                    total += 1
                active = True
            else:
                active = False
    return total


def _components(grid: list[list[int]], color: int) -> int:
    height, width = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == color}
    count = 0
    while remaining:
        count += 1
        queue = [remaining.pop()]
        for r, c in queue:
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (r + dr, c + dc)
                if q in remaining:
                    remaining.remove(q)
                    queue.append(q)
    return count


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    height, width = _validate_grid(grid)
    columns = [list(column) for column in zip(*grid)]
    horizontal = [_run_count(grid, color) for color in (3, 2)]
    vertical = [_run_count(columns, color) for color in (3, 2)]
    return {
        "shape": [height, width],
        "horizontal_counts": horizontal,
        "vertical_counts": vertical,
        "component_counts": [_components(grid, color) for color in (3, 2)],
        "occupied_rows": [sum(any(v == color for v in row) for row in grid) for color in (3, 2)],
        "occupied_columns": [sum(any(v == color for v in col) for col in columns) for color in (3, 2)],
        "cell_counts": [sum(v == color for row in grid for v in row) for color in (3, 2)],
    }


def tally(n3: int, n2: int) -> list[list[int]]:
    if type(n3) is not int or type(n2) is not int or n3 < 0 or n2 < 0:
        raise ValueError("tally counts must be nonnegative exact integers")
    output = [[0] * 3 for _ in range(2)]
    for index in range(6):
        output[index // 3][index % 3] = 3 if index < n3 else (2 if index < n3 + n2 else 0)
    return output


def transform(grid: list[list[int]], axis: str) -> list[list[int]]:
    if axis not in SETTINGS:
        raise ValueError(f"unknown run axis: {axis!r}")
    facts = analyze(grid)
    counts = facts[f"{axis}_counts"]
    return tally(*counts)


def _rng(seed: int, *parts: Any) -> random.Random:
    payload = json.dumps([TASK_ID, "run-axis-native-v1", seed, *parts], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _render_spec(seed: int, index: int, spec: tuple[int, int, tuple[tuple[int, int, int, int, int], ...]]) -> tuple[list[list[int]], dict[str, Any]]:
    height, width, rectangles = spec
    background = BACKGROUNDS[_rng(seed, index, "background").randrange(len(BACKGROUNDS))]
    grid = [[background] * width for _ in range(height)]
    for color, top, left, rh, rw in rectangles:
        for r in range(top, top + rh):
            for c in range(left, left + rw):
                if not (0 <= r < height and 0 <= c < width):
                    raise ValueError("rectangle leaves the declared canvas")
                if grid[r][c] != background:
                    raise ValueError("rectangles overlap")
                grid[r][c] = color
    # Reflections broaden positions while preserving both run-count pairs.
    flip_rows = bool(_rng(seed, index, "flip-rows").randrange(2))
    flip_cols = bool(_rng(seed, index, "flip-cols").randrange(2))
    if flip_rows:
        grid = list(reversed(grid))
    if flip_cols:
        grid = [list(reversed(row)) for row in grid]
    facts = analyze(grid)
    if facts["horizontal_counts"] == facts["vertical_counts"]:
        raise AssertionError("spec must distinguish horizontal and vertical settings")
    return grid, {
        "source_index": index,
        "shape": [height, width],
        "background": background,
        "flip_rows": flip_rows,
        "flip_cols": flip_cols,
        "horizontal_counts": facts["horizontal_counts"],
        "vertical_counts": facts["vertical_counts"],
    }


def _from_fact(name: str) -> Callable[[list[list[int]]], list[list[int]]]:
    return lambda grid: tally(*analyze(grid)[name])


def _denser_axis(grid: list[list[int]]) -> list[list[int]]:
    facts = analyze(grid)
    h, v = facts["horizontal_counts"], facts["vertical_counts"]
    return tally(*(v if sum(v) > sum(h) else h))


def _sparser_axis(grid: list[list[int]]) -> list[list[int]]:
    facts = analyze(grid)
    h, v = facts["horizontal_counts"], facts["vertical_counts"]
    return tally(*(v if sum(v) < sum(h) else h))


def _swapped(axis: str) -> Callable[[list[list[int]]], list[list[int]]]:
    return lambda grid: tally(*reversed(analyze(grid)[f"{axis}_counts"]))


RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "component_counts": _from_fact("component_counts"),
    "occupied_rows": _from_fact("occupied_rows"),
    "occupied_columns": _from_fact("occupied_columns"),
    "cell_counts": _from_fact("cell_counts"),
    "denser_axis": _denser_axis,
    "sparser_axis": _sparser_axis,
    "swapped_horizontal": _swapped("horizontal"),
    "swapped_vertical": _swapped("vertical"),
    "one_run_each": lambda grid: tally(1, 1),
}


def lesson_certificate(demos: list[dict[str, Any]], query_inputs: list[list[list[int]]]) -> dict[str, Any]:
    if type(demos) is not list or not demos or type(query_inputs) is not list or not query_inputs:
        raise ValueError("nonempty demonstrations and query inputs are required")
    for pair in demos:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("each demonstration needs input and output")
        analyze(pair["input"])
        _validate_arc_grid(pair["output"])
    for grid in query_inputs:
        analyze(grid)
    surviving_values = [
        axis for axis in SETTINGS
        if all(transform(pair["input"], axis) == pair["output"] for pair in demos)
    ]
    surviving_settings = [{PARAMETER: axis} for axis in surviving_values]
    intended_queries = (
        [transform(grid, surviving_values[0]) for grid in query_inputs]
        if len(surviving_values) == 1 else []
    )
    surviving_rivals: list[str] = []
    ambiguous_rivals: list[dict[str, Any]] = []
    for name, rival in RIVALS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            surviving_rivals.append(name)
            if intended_queries:
                disagreements = [
                    index for index, (grid, expected) in enumerate(zip(query_inputs, intended_queries))
                    if rival(grid) != expected
                ]
                if disagreements:
                    ambiguous_rivals.append({"name": name, "query_indices": disagreements})
    return {
        "surviving_settings": surviving_settings,
        "surviving_rivals": surviving_rivals,
        "ambiguous_rivals": ambiguous_rivals,
        "query_count": len(query_inputs),
        "scope": "two declared axes and nine finite component/occupancy/count/order/axis shortcuts; demonstrations fitted before query comparisons",
    }


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    seed = _exact_int(seed, 0, 2**63 - 1, "seed")
    axis = _setting(settings)
    demos = _exact_int(demos, 2, 6, "demos")
    queries = _exact_int(queries, 1, 4, "queries")

    train: list[dict[str, Any]] = []
    train_sampling: list[dict[str, Any]] = []
    for index, spec in enumerate(DEMO_SPECS[:demos]):
        grid, receipt = _render_spec(seed, index, spec)
        train.append({"input": grid, "output": transform(grid, axis)})
        train_sampling.append(receipt)

    bank: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for source_index, spec in enumerate(QUERY_SPECS):
        grid, receipt = _render_spec(seed, 1000 + source_index, spec)
        bank.append(({"input": grid, "output": transform(grid, axis)}, receipt))
    order = list(range(len(bank)))
    _rng(seed, "query-order").shuffle(order)
    selected = order[:queries]
    test = [bank[index][0] for index in selected]
    test_sampling = [dict(bank[index][1], source_query_index=index, presentation_index=position)
                     for position, index in enumerate(selected)]

    encoded = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(encoded) != len(set(encoded)):
        raise ValueError("episode contains duplicate inputs")
    certificate = lesson_certificate(train, [pair["input"] for pair in test])
    if certificate["surviving_settings"] != [copy.deepcopy(settings)]:
        raise ValueError("visible demonstrations do not uniquely teach the declared setting")
    if certificate["ambiguous_rivals"]:
        raise ValueError(f"finite shortcut ambiguity: {certificate['ambiguous_rivals']}")
    return {
        "train": train,
        "test": test,
        "program_solution": program(settings),
        "settings": copy.deepcopy(settings),
        "seed": seed,
        "certificate": certificate,
        "sampling": {"train": train_sampling, "test": test_sampling, "query_order": order},
        "status": "proposed",
        "training_admitted": False,
    }


def public_turn(episode: dict[str, Any], index: int) -> dict[str, Any]:
    from reviewer_support import public_challenge_bytes

    index = _exact_int(index, 0, len(episode["test"]) - 1, "query index")
    return json.loads(public_challenge_bytes({"train": episode["train"], "test": [episode["test"][index]]}))
