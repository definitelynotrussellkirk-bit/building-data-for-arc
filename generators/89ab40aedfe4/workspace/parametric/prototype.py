"""Task-local legend-selected population-sort prototype for 89ab40aedfe4.

The exact canonical rule remains the default ``all_slots`` setting.  The
``contains_key`` extension treats the first bit column as a legend: body rows
marked in that key are required features.  The key stays fixed, candidate bit
columns containing every required row are stable-sorted by foreground
population, and nonmatching candidates stay fixed.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_path, find_root

TASK_ID = "89ab40aedfe4"
PUBLIC_PARENT_ID = "d59b0160"
PROTOTYPE_VERSION = "1.0.0"
STATUS = "proposed task-local prototype; not selected or production-approved"
ROOT = find_root(__file__)
SELECTION_MODES = ("all_slots", "contains_key")
DEFAULT_SELECTION_MODE = "all_slots"
PARAMETERS = {
    "selection_mode": {
        "allowed": SELECTION_MODES,
        "default": DEFAULT_SELECTION_MODE,
        "selected_once_per_episode": True,
    }
}
_AUTO = object()

_CONTAINS_KEY_PROGRAM = r"""(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((fg (at g 0 0))
                  (starts (filter (lambda (c)
                                    (and
                                      (< (+ c 1) w)
                                      (= (at g 0 c) fg)
                                      (= (at g 0 (+ c 1)) fg)
                                      (or (zero? c) (zero? (at g 0 (- c 1))))))
                                  (range 0 w)))
                  (key (fst starts)))
             (define (col-count c)
               (count-if (lambda (r) (= (at g r (+ c 1)) fg)) (range 0 h)))
             (define required
               (filter (lambda (r) (= (at g r (+ key 1)) fg)) (range 1 h)))
             (define (contains-key? c)
               (and
                 (not (= c key))
                 (= 0
                    (count-if
                      (lambda (r) (not (= (at g r (+ c 1)) fg)))
                      required))))
             (define selected (filter contains-key? starts))
             (define ordered
               (sort selected
                     (lambda (a b)
                       (let ((ca (col-count a))
                             (cb (col-count b)))
                         (if (= ca cb) (< a b) (< ca cb))))))
             (define (copy-col acc dst src)
               (reduce (lambda (a r) (set-cell a r (+ dst 1) (at g r (+ src 1))))
                       acc
                       (range 0 h)))
             (if (or (empty? required) (< (length selected) 2))
                 (error 'contains_key "requires a nonempty key and at least two matching candidates")
                 (let loop
                      ((acc g) (dsts selected) (srcs ordered))
                      (if (empty? dsts)
                          acc
                          (loop (copy-col acc (fst dsts) (fst srcs)) (cdr dsts) (cdr srcs)))))))))"""


def _validate_mode(value: Any) -> str:
    if not isinstance(value, str) or value not in SELECTION_MODES:
        raise ValueError(f"selection_mode must be one of {SELECTION_MODES}")
    return value


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    return seed


def _canonical_program(*, root: Path | str = ROOT) -> str:
    values: list[str] = []
    with canonical_path(root).open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                values.append(row["program_solution"])
    if not values or len(set(values)) != 1:
        raise ValueError(f"canonical program missing or ambiguous for {TASK_ID}")
    return values[0]


def program_for(selection_mode: Any = DEFAULT_SELECTION_MODE, *, root: Path | str = ROOT) -> str:
    """Return the exact canonical or proposed Racket rule for one setting."""
    mode = _validate_mode(selection_mode)
    if mode == DEFAULT_SELECTION_MODE:
        return _canonical_program(root=root)
    return _CONTAINS_KEY_PROGRAM


def choose_selection_mode(seed: Any) -> str:
    """Choose one hidden setting deterministically once per episode."""
    _validate_seed(seed)
    digest = hashlib.sha256(
        f"{TASK_ID}:{PROTOTYPE_VERSION}:{seed}:selection_mode".encode()
    ).digest()
    return SELECTION_MODES[digest[0] % len(SELECTION_MODES)]


def _parse_grid(grid: Any) -> tuple[list[list[int]], int, list[int]]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    checked: list[list[int]] = []
    for row in grid:
        if not isinstance(row, list) or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise ValueError("grid cells must be integer ARC colors 0..9")
        checked.append(list(row))
    foreground = checked[0][0]
    if not 1 <= foreground <= 9:
        raise ValueError("top-left foreground color must be in 1..9")
    if any(value not in (0, foreground) for row in checked for value in row):
        raise ValueError("prototype grid may use only background 0 and one foreground color")
    starts = [
        column
        for column in range(width - 1)
        if checked[0][column] == foreground
        and checked[0][column + 1] == foreground
        and (column == 0 or checked[0][column - 1] == 0)
    ]
    if len(starts) < 3:
        raise ValueError("prototype grid needs at least three slots")
    if starts[0] != 0 or starts[-1] + 2 != width:
        raise ValueError("slot markers must begin at column 0 and end at grid width")
    spacings = [right - left for left, right in zip(starts, starts[1:])]
    if not spacings or len(set(spacings)) != 1 or not 3 <= spacings[0] <= 5:
        raise ValueError("slot starts must use one spacing in 3..5")
    slot_columns = {column for start in starts for column in (start, start + 1)}
    for start in starts:
        if any(checked[row][start] != foreground for row in range(len(checked))):
            raise ValueError("every carrier must be full-height foreground")
        if checked[0][start + 1] != foreground:
            raise ValueError("every bit column needs its top marker")
    for column in range(width):
        if column not in slot_columns and any(checked[row][column] != 0 for row in range(len(checked))):
            raise ValueError("separator columns must be all background")
    return checked, foreground, starts


def _copy_in_order(
    grid: list[list[int]], starts: list[int], destination_indexes: list[int], source_indexes: list[int]
) -> list[list[int]]:
    output = deepcopy(grid)
    if len(destination_indexes) != len(source_indexes):
        raise ValueError("source and destination selections differ in length")
    for destination_index, source_index in zip(destination_indexes, source_indexes):
        destination_column = starts[destination_index] + 1
        source_column = starts[source_index] + 1
        for row in range(len(grid)):
            output[row][destination_column] = grid[row][source_column]
    return output


def apply_python(grid: Any, selection_mode: Any = DEFAULT_SELECTION_MODE) -> list[list[int]]:
    """Independent Python mirror of both declared Racket settings."""
    mode = _validate_mode(selection_mode)
    checked, foreground, starts = _parse_grid(grid)
    counts = [
        sum(checked[row][start + 1] == foreground for row in range(len(checked)))
        for start in starts
    ]
    if mode == "all_slots":
        destinations = list(range(len(starts)))
    else:
        required_rows = [
            row
            for row in range(1, len(checked))
            if checked[row][starts[0] + 1] == foreground
        ]
        if not required_rows:
            raise ValueError("contains_key requires at least one foreground key body row")
        destinations = [
            index
            for index in range(1, len(starts))
            if all(checked[row][starts[index] + 1] == foreground for row in required_rows)
        ]
        if len(destinations) < 2:
            raise ValueError("contains_key requires at least two matching candidate columns")
    sources = sorted(destinations, key=lambda index: (counts[index], index))
    return _copy_in_order(checked, starts, destinations, sources)


def _ordered_body_rows(seed: int, pair_index: int, height: int) -> list[int]:
    return sorted(
        range(1, height),
        key=lambda row: hashlib.sha256(
            f"{TASK_ID}:{PROTOTYPE_VERSION}:{seed}:{pair_index}:row:{row}".encode()
        ).digest(),
    )


def input_for(seed: Any, pair_index: Any) -> list[list[int]]:
    """Build one valid scene that distinguishes both selection settings."""
    seed = _validate_seed(seed)
    if type(pair_index) is not int or pair_index < 0:
        raise ValueError("pair_index must be a nonnegative integer")
    height = 12
    spacing = 3
    slot_count = 6
    width = spacing * (slot_count - 1) + 2
    rows = _ordered_body_rows(seed, pair_index, height)
    r0, r1, r2, r3, r4, r5, r6, r7, r8, r9 = rows[:10]
    active = (
        {0, r0, r1},
        {0, r0, r1, r2, r3},
        {0, r0, r4, r5, r6, r7},
        {0, r0, r1, r5, r6},
        {0, r1, r2, r8},
        {0, r0, r1, r9},
    )
    digest = hashlib.sha256(
        f"{TASK_ID}:{PROTOTYPE_VERSION}:{seed}:{pair_index}:color".encode()
    ).digest()
    foreground = 1 + digest[0] % 9
    grid = [[0] * width for _ in range(height)]
    for index, rows_active in enumerate(active):
        start = index * spacing
        for row in range(height):
            grid[row][start] = foreground
            grid[row][start + 1] = foreground if row in rows_active else 0
    if apply_python(grid, "all_slots") == apply_python(grid, "contains_key"):
        raise AssertionError("prototype input failed to distinguish selection settings")
    return grid


def build_episode(
    seed: Any,
    *,
    selection_mode: str | object = _AUTO,
    demonstration_count: int = 3,
    query_count: int = 4,
    root: Path | str = ROOT,
) -> dict[str, Any]:
    """Build one private episode with an episode-fixed hidden rule setting."""
    seed = _validate_seed(seed)
    if type(demonstration_count) is not int or demonstration_count < 1:
        raise ValueError("demonstration_count must be a positive integer")
    if type(query_count) is not int or query_count < 1:
        raise ValueError("query_count must be a positive integer")
    mode = choose_selection_mode(seed) if selection_mode is _AUTO else _validate_mode(selection_mode)
    pairs = []
    for pair_index in range(demonstration_count + query_count):
        grid = input_for(seed, pair_index)
        pairs.append({"input": grid, "output": apply_python(grid, mode)})
    return {
        "schema": "89ab40aedfe4-legend-selector-episode-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "public_parent_id": PUBLIC_PARENT_ID,
        "seed": seed,
        "parameter": {"selection_mode": mode},
        "program": program_for(mode, root=root),
        "train": pairs[:demonstration_count],
        "test": pairs[demonstration_count:],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Return a model-visible challenge with hidden setting and query labels removed."""
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }
