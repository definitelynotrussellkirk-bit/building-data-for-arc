"""Isolated episode-level tile-width prototype for ARC task 997c17fd6870.

The selected generator and canonical Racket authority remain unchanged.  This
prototype varies one nearby rule parameter exactly once per episode:

* ``tile_width=2`` (default/original): reverse adjacent two-column tiles.
* ``tile_width=3`` (alternative): reverse adjacent three-column tiles.

Both settings preserve cell order inside each tile.  Retained labels are made by
executing the exact callable returned by :func:`racket_program`; the Python
reference is only an independent test/debug mirror.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from puzzle_generators.base import stable_rng


TASK_ID = "997c17fd6870"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER_NAME = "tile_width"
DEFAULT_TILE_WIDTH = 2
ALLOWED_TILE_WIDTHS = (DEFAULT_TILE_WIDTH, 3)
PARAMETER_SPEC = {
    PARAMETER_NAME: {
        "type": "enum[int]",
        "allowed": list(ALLOWED_TILE_WIDTHS),
        "default": DEFAULT_TILE_WIDTH,
        "chosen": "once per episode from the deterministic episode seed",
        "input_constraints": (
            "12x12 two-color 2x2-motif scenes; width is divisible by both "
            "settings and every retained pair distinguishes them"
        ),
    }
}


def _validate_tile_width(value: Any) -> int:
    if type(value) is not int or value not in ALLOWED_TILE_WIDTHS:
        raise ValueError(
            f"{PARAMETER_NAME} must be one of {ALLOWED_TILE_WIDTHS}, got {value!r}"
        )
    return value


def choose_parameters(seed: int) -> dict[str, int]:
    """Choose one hidden tile width from the episode seed."""
    if type(seed) is not int:
        raise TypeError("episode seed must be a literal integer (not bool)")
    rng = stable_rng(seed, f"{TASK_ID}|parametric-rule", PROTOTYPE_VERSION)
    return {PARAMETER_NAME: ALLOWED_TILE_WIDTHS[rng.randrange(len(ALLOWED_TILE_WIDTHS))]}


def _validate_grid(grid: Any, *, tile_width: int) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must contain at least one row")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("grid rows must be nonempty")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        raise ValueError("grid cells must be literal ARC colors 0..9")
    if width % tile_width:
        raise ValueError(f"grid width {width} must be divisible by tile_width={tile_width}")
    return len(grid), width


def python_reference(
    grid: list[list[int]], *, tile_width: int = DEFAULT_TILE_WIDTH
) -> list[list[int]]:
    """Debug mirror: reverse tile order and preserve order inside each tile."""
    width_per_tile = _validate_tile_width(tile_width)
    _height, width = _validate_grid(grid, tile_width=width_per_tile)
    return [
        [
            value
            for start in range(width - width_per_tile, -1, -width_per_tile)
            for value in row[start:start + width_per_tile]
        ]
        for row in grid
    ]


def _motif(kind: str, first: int, second: int) -> list[list[int]]:
    if kind == "hook":
        return [[first, first], [second, first]]
    if kind == "corner":
        return [[first, 0], [second, second]]
    if kind == "gap":
        return [[first, second], [second, 0]]
    if kind == "checker":
        return [[first, second], [second, first]]
    raise ValueError(f"unknown motif kind: {kind!r}")


def _paint_motif(
    grid: list[list[int]], macro_row: int, macro_col: int, motif: list[list[int]]
) -> None:
    row0, col0 = 2 * macro_row, 2 * macro_col
    for dr in range(2):
        for dc in range(2):
            grid[row0 + dr][col0 + dc] = motif[dr][dc]


def build_input(episode_seed: int, pair_index: int) -> list[list[int]]:
    """Build a deterministic 12x12 production-family scene for one pair."""
    if type(episode_seed) is not int:
        raise TypeError("episode seed must be a literal integer (not bool)")
    if type(pair_index) is not int:
        raise TypeError("pair_index must be a literal integer (not bool)")
    if not 0 <= pair_index < 4:
        raise ValueError("pair_index must be in 0..3")

    rng = stable_rng(
        episode_seed,
        f"{TASK_ID}|parametric-input|pair={pair_index}",
        PROTOTYPE_VERSION,
    )
    first, second = rng.sample(range(1, 10), 2)
    # Six distinct oriented motif specifications guarantee the first and last
    # two-column tiles differ under every cyclic shift.
    specs = [
        ("hook", False),
        ("corner", False),
        ("gap", False),
        ("checker", False),
        ("hook", True),
        ("corner", True),
    ]
    shift = rng.randrange(len(specs))
    specs = specs[shift:] + specs[:shift]
    if rng.randrange(2):
        specs = list(reversed(specs))

    grid = [[0] * 12 for _ in range(12)]
    for macro_col, (kind, swap) in enumerate(specs):
        a, b = (second, first) if swap else (first, second)
        _paint_motif(grid, 0, macro_col, _motif(kind, a, b))

    columns = list(range(6))
    rng.shuffle(columns)
    kinds = ("hook", "corner", "gap", "checker")
    for macro_row, macro_col in enumerate(columns[1:], start=1):
        kind = kinds[rng.randrange(len(kinds))]
        swap = bool(rng.randrange(2))
        a, b = (second, first) if swap else (first, second)
        _paint_motif(grid, macro_row, macro_col, _motif(kind, a, b))

    if python_reference(grid, tile_width=2) == python_reference(grid, tile_width=3):
        raise AssertionError("constructed input does not distinguish tile widths")
    return grid


def racket_program(parameters: dict[str, Any]) -> str:
    """Materialize the exact Racket callable for one episode setting."""
    tile_width = _validate_tile_width(parameters.get(PARAMETER_NAME))
    return f"""(lambda (g)
  (let* ([w (cols g)])
    (cellmap g
             (r c v)
             (let* ([tile-start (- c (remainder c {tile_width}))]
                    [offset (remainder c {tile_width})]
                    [source-start (- (- w {tile_width}) tile-start)])
               (at g r (+ source-start offset))))))"""


def grid_literal(grid: list[list[int]]) -> str:
    _validate_grid(grid, tile_width=1)
    rows = " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    )
    return f"'({rows})"


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Redact the seed, setting, Racket source, and query answer."""
    demos = [
        {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
        for pair in episode["demos"]
    ]
    return {
        "schema": "arc-parametric-public-challenge-v1",
        "task_id": TASK_ID,
        "demos": demos,
        "query": {"input": deepcopy(episode["query"]["input"])},
    }
