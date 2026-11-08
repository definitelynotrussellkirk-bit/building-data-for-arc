"""Task-local parametric prototype for ``de49e9901e3a``.

This is deliberately separate from the production generator and canonical rule.
One hidden episode-level parameter controls which objects are eligible for
row/column closure:

``all``
    Canonical/default behavior: close every monochrome 4-connected object.
``cross_only``
    Proposed alternative: close only objects that are exactly one complete
    occupied row union one complete occupied column; copy other objects.

The parameter is selected once per episode and shared by every demonstration
and query.  Every materialized episode contains non-cross objects so its
training pairs distinguish the two settings.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import random
from typing import Any


PARAMETER_NAME = "eligible_objects"
ALLOWED_SETTINGS = ("all", "cross_only")
DEFAULT_SETTING = "all"
PROTOTYPE_VERSION = "1.0.0"
_UNSET = object()

_CANONICAL_DIMS = ((9, 10), (10, 10), (8, 11), (9, 9))
_STAIR = frozenset({(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)})


def _validate_seed(seed: int) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, string, or None)")


def _validate_setting(setting: str) -> None:
    if type(setting) is not str:
        raise TypeError(f"{PARAMETER_NAME} must be a string")
    if setting not in ALLOWED_SETTINGS:
        raise ValueError(
            f"{PARAMETER_NAME} must be one of {ALLOWED_SETTINGS}, got {setting!r}"
        )


def choose_setting(seed: int) -> str:
    """Choose one hidden setting deterministically for a complete episode."""
    _validate_seed(seed)
    digest = hashlib.sha256(f"de49-parametric:{seed}".encode()).digest()
    return ALLOWED_SETTINGS[digest[0] % len(ALLOWED_SETTINGS)]


def _transform_square(cells: set[tuple[int, int]] | frozenset[tuple[int, int]], turn: int, reflect: bool) -> set[tuple[int, int]]:
    transformed = set(cells)
    if reflect:
        transformed = {(r, 2 - c) for r, c in transformed}
    for _ in range(turn % 4):
        transformed = {(c, 2 - r) for r, c in transformed}
    return transformed


def _cross_cells(bar_row: int, bar_col: int) -> set[tuple[int, int]]:
    return ({(bar_row, c) for c in range(3)} |
            {(r, bar_col) for r in range(3)})


def _input_for(seed: int, pair_index: int) -> list[list[int]]:
    """Construct one lawful same-family input with a guaranteed discriminator."""
    rng = random.Random(seed * 1_000_003 + pair_index * 9_176 + 0xD349)
    height, width = _CANONICAL_DIMS[pair_index % len(_CANONICAL_DIMS)]
    grid = [[0 for _ in range(width)] for _ in range(height)]

    colors = rng.sample(range(1, 10), 2)
    witness = _transform_square(_STAIR, rng.randrange(4), bool(rng.randrange(2)))
    witness_top = rng.randrange(0, max(1, height // 2 - 2))
    witness_left = rng.randrange(0, max(1, width // 2 - 2))
    for dr, dc in witness:
        grid[witness_top + dr][witness_left + dc] = colors[0]

    cross = _cross_cells(rng.randrange(3), rng.randrange(3))
    cross_top = rng.randrange(max(height // 2 + 1, height - 4), height - 2)
    cross_left = rng.randrange(max(width // 2 + 1, width - 4), width - 2)
    for dr, dc in cross:
        grid[cross_top + dr][cross_left + dc] = colors[1]
    return grid


def _components(grid: list[list[int]]) -> list[tuple[int, frozenset[tuple[int, int]]]]:
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, frozenset[tuple[int, int]]]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            cells: set[tuple[int, int]] = set()
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                rr, cc = stack.pop()
                cells.add((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, frozenset(cells)))
    return result


def _bbox_cells(cells: frozenset[tuple[int, int]]) -> set[tuple[int, int]]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return {
        (row, col)
        for row in range(min(rows), max(rows) + 1)
        for col in range(min(cols), max(cols) + 1)
    }


def _is_row_column_cross(cells: frozenset[tuple[int, int]]) -> bool:
    rows = sorted({row for row, _ in cells})
    cols = sorted({col for _, col in cells})
    for bar_row in rows:
        for bar_col in cols:
            candidate = ({(bar_row, col) for col in cols} |
                         {(row, bar_col) for row in rows})
            if candidate == set(cells):
                return True
    return False


def apply_python(grid: list[list[int]], setting: str) -> list[list[int]]:
    """Independent Python mirror for prototype authoring and unit tests."""
    _validate_setting(setting)
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("expected a nonempty rectangular grid")
    output = [[0 for _ in row] for row in grid]
    for color, cells in _components(grid):
        eligible = setting == "all" or _is_row_column_cross(cells)
        painted = _bbox_cells(cells) if eligible else set(cells)
        for row, col in painted:
            output[row][col] = color
    return output


_CANONICAL_PROGRAM = """(rule!
  (for/fold ([out (empty-grid (rows g) (cols g) 0)]) ([obj (in-list (objects g 0))])
    (let* ((rs (remove-duplicates (map first (obj-cells obj))))
           (cs (remove-duplicates (map second (obj-cells obj))))
           (cells (for*/list ([r (in-list rs)] [c (in-list cs)]) (list r c))))
      (paint-cells out cells (obj-color obj)))))"""

_CROSS_ONLY_PROGRAM = """(rule!
  (for/fold ([out (empty-grid (rows g) (cols g) 0)]) ([obj (in-list (objects g 0))])
    (let* ([original (obj-cells obj)]
           [rs (remove-duplicates (map first original))]
           [cs (remove-duplicates (map second original))]
           [cross?
            (for*/or ([bar-r (in-list rs)] [bar-c (in-list cs)])
              (let ([candidate
                     (remove-duplicates
                      (append
                       (for/list ([c (in-list cs)]) (list bar-r c))
                       (for/list ([r (in-list rs)]) (list r bar-c))))])
                (and (= (length candidate) (length original))
                     (andmap (lambda (cell) (member cell original)) candidate))))]
           [cells
            (if cross?
                (for*/list ([r (in-list rs)] [c (in-list cs)]) (list r c))
                original)])
      (paint-cells out cells (obj-color obj)))))"""


def program_for(setting: str) -> str:
    _validate_setting(setting)
    return _CANONICAL_PROGRAM if setting == "all" else _CROSS_ONLY_PROGRAM


def build_episode(seed: int, *, setting: object = _UNSET) -> dict[str, Any]:
    """Materialize three demonstrations and one query under one fixed setting."""
    _validate_seed(seed)
    selected = choose_setting(seed) if setting is _UNSET else setting
    _validate_setting(selected)
    inputs = [_input_for(seed, index) for index in range(4)]
    pairs = [
        {"input": grid, "output": apply_python(grid, selected)}
        for grid in inputs
    ]
    program = program_for(selected)
    return {
        "train": pairs[:3],
        "test": pairs[3:],
        "program": program,
        "meta": {
            "seed": seed,
            PARAMETER_NAME: selected,
            "allowed_settings": list(ALLOWED_SETTINGS),
            "default_setting": DEFAULT_SETTING,
            "prototype_version": PROTOTYPE_VERSION,
            "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return a challenge view with no hidden setting, program, or query answer."""
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [
            {"input": deepcopy(pair["input"])}
            for pair in episode["test"]
        ],
    }
