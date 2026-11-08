"""Native parametric family for chamber legend task 67a09b7f6b66.

The canonical setting maps each chamber's dot count directly to the corresponding
legend slot.  The composed setting first finds the unique chamber marked by a dot
in its upper-left interior corner, derives that chamber's dot count, then uses
that input-dependent count as the cyclic origin for all chamber-to-legend fills.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any

HOME = Path(__file__).resolve().parent
SETTINGS = ("absolute_count", "anchor_cycle")
RIVALS = (
    "position_only",
    "occupied_rows",
    "fixed_anchor_1",
    "fixed_anchor_2",
    "fixed_anchor_3",
)
DEMO_PROFILES = ((9, 13), (12, 19), (15, 22), (18, 25), (21, 28), (24, 30))
QUERY_PROFILES = ((20, 19), (24, 22), (27, 28), (30, 30))
DEMO_ANCHOR_COUNTS = (2, 3, 2, 3, 2, 3)
QUERY_ANCHOR_COUNTS = (3, 1, 2, 3)


def _read_exact(path: Path) -> str:
    value = path.read_text(encoding="utf-8")
    if not value.strip():
        raise ValueError(f"empty Racket source: {path}")
    return value


CANONICAL_PROGRAM = _read_exact(HOME / "canonical.rkt")
ANCHOR_CYCLE_PROGRAM = _read_exact(HOME / "anchor_cycle.rkt")


def _setting(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"legend_mapping"}:
        raise ValueError("settings must contain exactly legend_mapping")
    value = settings["legend_mapping"]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"legend_mapping must be one of {SETTINGS}")
    return value


def program(settings: Any) -> str:
    return CANONICAL_PROGRAM if _setting(settings) == "absolute_count" else ANCHOR_CYCLE_PROGRAM


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list:
        raise ValueError("grid must have 1..30 rows")
    width = len(grid[0])
    if not 1 <= width <= 30:
        raise ValueError("grid must have 1..30 columns")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    if len(grid) < 6 or width < 13:
        raise ValueError("chamber grids must be at least 6x13")
    return len(grid), width


def _zero_connected(rows: range, cols: range, dots: set[tuple[int, int]]) -> bool:
    cells = {(row, col) for row in rows for col in cols} - dots
    if not cells:
        return False
    remaining = set(cells)
    stack = [remaining.pop()]
    while stack:
        row, col = stack.pop()
        for point in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if point in remaining:
                remaining.remove(point)
                stack.append(point)
    if remaining:
        return False
    return all(
        any(
            point in cells
            for point in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
        )
        for row, col in dots
    )


def analyze(grid: Any) -> dict[str, Any]:
    height, width = _validate_grid(grid)
    if any(grid[0][col] != 0 for col in range(width) if col not in {1, 2, 3}):
        raise ValueError("only row-0 columns 1..3 may contain the legend")
    legend = grid[0][1:4]
    if any(value == 0 for value in legend) or len(set(legend)) != 3:
        raise ValueError("legend must contain three distinct nonzero colors")
    if any(value != 8 for value in grid[1]) or any(value != 8 for value in grid[-1]):
        raise ValueError("top and bottom chamber walls must be complete color-8 rows")
    wall_columns = [
        col
        for col in range(width)
        if all(grid[row][col] == 8 for row in range(1, height))
    ]
    if len(wall_columns) != 4 or wall_columns[0] != 0 or wall_columns[-1] != width - 1:
        raise ValueError("exactly four full-height chamber wall columns are required")
    counts: list[int] = []
    occupied_rows: list[int] = []
    chamber_widths: list[int] = []
    anchor_candidates: list[int] = []
    for chamber in range(3):
        left, right = wall_columns[chamber], wall_columns[chamber + 1]
        chamber_widths.append(right - left - 1)
        rows = range(2, height - 1)
        cols = range(left + 1, right)
        values = [grid[row][col] for row in rows for col in cols]
        if any(value not in {0, 1} for value in values):
            raise ValueError("chamber interiors may contain only zero and color-1 dots")
        dots = {(row, col) for row in rows for col in cols if grid[row][col] == 1}
        counts.append(len(dots))
        occupied_rows.append(len({row for row, _ in dots}))
        if not _zero_connected(rows, cols, dots):
            raise ValueError("each chamber must retain one connected zero region touching every dot")
        if grid[2][left + 1] == 1:
            anchor_candidates.append(chamber)
    if sorted(counts) != [1, 2, 3]:
        raise ValueError("chamber dot counts must be a permutation of 1,2,3")
    if len(anchor_candidates) != 1:
        raise ValueError("exactly one chamber must have an upper-left anchor dot")
    anchor_chamber = anchor_candidates[0]
    return {
        "height": height,
        "width": width,
        "legend": list(legend),
        "wall_columns": wall_columns,
        "chamber_widths": chamber_widths,
        "counts": sorted(counts),
        "count_order": counts,
        "occupied_rows": occupied_rows,
        "anchor_chamber": anchor_chamber,
        "anchor_count": counts[anchor_chamber],
    }


def _fill_slots(grid: Any, slots: list[int]) -> list[list[int]]:
    facts = analyze(grid)
    if len(slots) != 3 or any(type(slot) is not int or slot not in {1, 2, 3} for slot in slots):
        raise ValueError("three legend slots in 1..3 are required")
    result = deepcopy(grid)
    for chamber, slot in enumerate(slots):
        left = facts["wall_columns"][chamber]
        right = facts["wall_columns"][chamber + 1]
        color = facts["legend"][slot - 1]
        for row in range(2, facts["height"] - 1):
            for col in range(left + 1, right):
                result[row][col] = color
    return result


def transform(grid: Any, legend_mapping: str) -> list[list[int]]:
    if type(legend_mapping) is not str or legend_mapping not in SETTINGS:
        raise ValueError(f"legend_mapping must be one of {SETTINGS}")
    facts = analyze(grid)
    if legend_mapping == "absolute_count":
        slots = list(facts["count_order"])
    else:
        anchor_count = facts["anchor_count"]
        slots = [((count - anchor_count) % 3) + 1 for count in facts["count_order"]]
    return _fill_slots(grid, slots)


def rival_transform(grid: Any, name: str) -> list[list[int]]:
    if name not in RIVALS:
        raise ValueError(f"unknown rival: {name}")
    facts = analyze(grid)
    if name == "position_only":
        slots = [1, 2, 3]
    elif name == "occupied_rows":
        slots = list(facts["occupied_rows"])
    else:
        fixed = int(name[-1])
        slots = [((count - fixed) % 3) + 1 for count in facts["count_order"]]
    return _fill_slots(grid, slots)


def _racket_program_for_mode(mode: str) -> str:
    if mode == "absolute_count":
        return CANONICAL_PROGRAM
    if mode == "anchor_cycle":
        return ANCHOR_CYCLE_PROGRAM
    if mode.startswith("fixed_anchor_"):
        fixed = int(mode[-1])
        anchor_expression = str(fixed)
        slot_expression = "(+ 1 (modulo (- n anchor-count) 3))"
    elif mode == "occupied_rows":
        anchor_expression = "1"
        slot_expression = "(length (remove-duplicates (map first dots)))"
    elif mode == "position_only":
        return """(rule! (let ((dummy 0))
  (define dirs4 (list (list -1 0) (list 1 0) (list 0 -1) (list 0 1)))
  (define (e15b-region-dots grid region)
    (let* ((bb (bbox-of-cells region))
           (r1 (max 1 (- (first bb) 1))) (c1 (max 0 (- (second bb) 1)))
           (r2 (min (- (rows grid) 1) (+ (third bb) 1)))
           (c2 (min (- (cols grid) 1) (+ (fourth bb) 1))))
      (filter (lambda (p)
                (and (= (at grid (first p) (second p)) 1)
                     (any? (lambda (d)
                             (member? (list (+ (first p) (first d))
                                            (+ (second p) (second d))) region))
                           dirs4)))
              (positions-in-rect r1 c1 r2 c2))))
  (let* ((legend (filter values (for/list ((c (in-range (cols g))))
                                  (let ((v (at g 0 c))) (if (= v 0) #f (list c v))))))
         (body (subgrid g 1 0 (- (rows g) 1) (- (cols g) 1)))
         (regions (map (lambda (region)
                         (map (lambda (p) (list (+ 1 (first p)) (second p))) region))
                       (find-0-regions body 0))))
    (for/fold ((out g)) ((region (in-list regions)) (slot (in-range 1 4)))
      (let* ((dots (e15b-region-dots g region))
             (hit (filter (lambda (pair) (= (first pair) slot)) legend)))
        (if (empty? hit) out
            (paint-cells out (append region dots) (second (first hit)))))))))"""
    else:
        raise ValueError(f"unknown mode: {mode}")
    return f"""(rule! (let ((dummy 0))
  (define dirs4 (list (list -1 0) (list 1 0) (list 0 -1) (list 0 1)))
  (define (e15b-region-dots grid region)
    (let* ((bb (bbox-of-cells region))
           (r1 (max 1 (- (first bb) 1))) (c1 (max 0 (- (second bb) 1)))
           (r2 (min (- (rows grid) 1) (+ (third bb) 1)))
           (c2 (min (- (cols grid) 1) (+ (fourth bb) 1))))
      (filter (lambda (p)
                (and (= (at grid (first p) (second p)) 1)
                     (any? (lambda (d)
                             (member? (list (+ (first p) (first d))
                                            (+ (second p) (second d))) region))
                           dirs4)))
              (positions-in-rect r1 c1 r2 c2))))
  (let* ((legend (filter values (for/list ((c (in-range (cols g))))
                                  (let ((v (at g 0 c))) (if (= v 0) #f (list c v))))))
         (body (subgrid g 1 0 (- (rows g) 1) (- (cols g) 1)))
         (regions (map (lambda (region)
                         (map (lambda (p) (list (+ 1 (first p)) (second p))) region))
                       (find-0-regions body 0)))
         (anchor-count {anchor_expression}))
    (for/fold ((out g)) ((region (in-list regions)))
      (let* ((dots (e15b-region-dots g region))
             (n (length dots))
             (slot {slot_expression})
             (hit (filter (lambda (pair) (= (first pair) slot)) legend)))
        (if (empty? hit) out
            (paint-cells out (append region dots) (second (first hit)))))))))"""


def rival_program(name: str) -> str:
    if name not in RIVALS:
        raise ValueError(f"unknown rival: {name}")
    return _racket_program_for_mode(name)


def _rng(seed: int, split: str, index: int, label: str) -> random.Random:
    material = f"67a09b7f6b66|{seed}|{split}|{index}|{label}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(material).digest()[:16], "big"))


def _wall_columns(width: int) -> list[int]:
    interior = width - 4
    base, remainder = divmod(interior, 3)
    widths = [base + (1 if index >= 3 - remainder else 0) for index in range(3)]
    if min(widths) < 3:
        raise ValueError("each chamber needs at least three interior columns")
    first = widths[0] + 1
    second = first + widths[1] + 1
    return [0, first, second, width - 1]


def _legend(seed: int, split: str, index: int) -> list[int]:
    rng = _rng(seed, split, index, "legend")
    nonwall = [2, 3, 4, 5, 6, 7, 9]
    if (seed + index + (0 if split == "train" else 1)) % 2 == 0:
        colors = rng.sample(nonwall, 2) + [8]
        rng.shuffle(colors)
        return colors
    return rng.sample(nonwall, 3)


def _count_order(seed: int, split: str, index: int, anchor_chamber: int, anchor_count: int) -> list[int]:
    others = [value for value in (1, 2, 3) if value != anchor_count]
    _rng(seed, split, index, "count-order").shuffle(others)
    order: list[int | None] = [None, None, None]
    order[anchor_chamber] = anchor_count
    cursor = 0
    for chamber in range(3):
        if order[chamber] is None:
            order[chamber] = others[cursor]
            cursor += 1
    return [int(value) for value in order]


def _choose_dots(
    *,
    seed: int,
    split: str,
    index: int,
    chamber: int,
    rows: range,
    cols: range,
    count: int,
    anchor: bool,
) -> set[tuple[int, int]]:
    corner = (rows.start, cols.start)
    rng = _rng(seed, split, index, f"dots:{chamber}")
    all_cells = [(row, col) for row in rows for col in cols]
    if count == 2:
        if anchor:
            candidates = [
                {corner, (rows.start, col)}
                for col in cols
                if col != cols.start
            ]
        else:
            candidates = [
                {(row, first), (row, second)}
                for row in rows
                for first in cols
                for second in cols
                if first < second and corner not in {(row, first), (row, second)}
            ]
        rng.shuffle(candidates)
        for dots in candidates:
            if _zero_connected(rows, cols, dots):
                return dots
        raise RuntimeError("unable to place same-row two-dot witness")

    required = {corner} if anchor else set()
    candidates = [cell for cell in all_cells if cell not in required and (anchor or cell != corner)]
    for _ in range(200):
        chosen = required | set(rng.sample(candidates, count - len(required)))
        if _zero_connected(rows, cols, chosen):
            return chosen
    raise RuntimeError("unable to place authority-safe chamber dots")


def _make_input(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = DEMO_PROFILES if split == "train" else QUERY_PROFILES
    anchor_counts = DEMO_ANCHOR_COUNTS if split == "train" else QUERY_ANCHOR_COUNTS
    height, width = profiles[index]
    anchor_count = anchor_counts[index]
    anchor_chamber = (seed + index + (0 if split == "train" else 1)) % 3
    walls = _wall_columns(width)
    counts = _count_order(seed, split, index, anchor_chamber, anchor_count)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    legend = _legend(seed, split, index)
    for col, color in enumerate(legend, start=1):
        grid[0][col] = color
    for col in range(width):
        grid[1][col] = 8
        grid[-1][col] = 8
    for row in range(1, height):
        for col in walls:
            grid[row][col] = 8
    for chamber, count in enumerate(counts):
        rows = range(2, height - 1)
        cols = range(walls[chamber] + 1, walls[chamber + 1])
        dots = _choose_dots(
            seed=seed,
            split=split,
            index=index,
            chamber=chamber,
            rows=rows,
            cols=cols,
            count=count,
            anchor=chamber == anchor_chamber,
        )
        for row, col in dots:
            grid[row][col] = 1
    facts = analyze(grid)
    if facts["anchor_count"] != anchor_count or facts["anchor_chamber"] != anchor_chamber:
        raise AssertionError("constructed anchor changed")
    if facts["count_order"] != counts:
        raise AssertionError("constructed count order changed")
    return grid


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    legend_mapping = _setting(settings)
    train_inputs = [_make_input(seed, "train", index) for index in range(demos)]
    test_inputs = [_make_input(seed, "test", index) for index in range(queries)]
    all_inputs = train_inputs + test_inputs
    if len({repr(grid) for grid in all_inputs}) != len(all_inputs):
        raise AssertionError("generated inputs must be distinct")

    def pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
        return {"input": deepcopy(grid), "output": transform(grid, legend_mapping)}

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
