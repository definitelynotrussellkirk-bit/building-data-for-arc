"""Isolated extension-direction prototype for ARC task 2d2b102b7740.

The selected generator and canonical rule stay fixed.  This prototype varies one
small rule parameter once per episode:

* ``extension_mode='forward'`` (canonical/default): continue the blue arithmetic
  line only beyond its final blue cell.
* ``extension_mode='both'``: continue the same spacing both before the first blue
  cell and after the final blue cell.

Every retained input has legal blue arithmetic-line seeds plus in-bounds room on
both ends, so demonstrations can identify the episode's hidden setting.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from puzzle_generators.base import stable_rng

TASK_ID = "2d2b102b7740"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER_NAME = "extension_mode"
DEFAULT_EXTENSION_MODE = "forward"
ALLOWED_EXTENSION_MODES = (DEFAULT_EXTENSION_MODE, "both")
PARAMETER_SPEC = {
    PARAMETER_NAME: {
        "type": "enum",
        "allowed": list(ALLOWED_EXTENSION_MODES),
        "default": DEFAULT_EXTENSION_MODE,
        "chosen": "once per episode from the deterministic episode seed",
        "input_constraints": (
            "2..5 equally spaced blue cells on a row-major arithmetic line, "
            "with at least one in-bounds continuation cell before the first "
            "blue and after the last blue"
        ),
    }
}

# Exact selected authority for the canonical/default setting.  Keeping the
# rule! wrapper makes its normalized hash equal the selected RULE_HASH.
CANONICAL_RACKET = """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g))
                (blues (sort-by (find-color g 1) (lambda (p) (fst p))))
                (p0 (first blues))
                (p1 (second blues))
                (dr (- (fst p1) (fst p0)))
                (dc (- (snd p1) (snd p0)))
                (last-blue (nth blues (- (length blues) 1)))
                (lr (fst last-blue))
                (lc (snd last-blue)))
           (reduce (lambda (grid i)
                     (let* ((nr (+ lr (* (+ i 1) dr)))
                            (nc (+ lc (* (+ i 1) dc))))
                       (if (and (>= nr 0) (< nr h) (>= nc 0) (< nc w))
                           (set-cell grid nr nc 2)
                           grid)))
                   g
                   (range 0 20)))))"""

BOTH_RACKET = """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g))
                (blues (sort-by (find-color g 1) (lambda (p) (fst p))))
                (p0 (first blues))
                (p1 (second blues))
                (dr (- (fst p1) (fst p0)))
                (dc (- (snd p1) (snd p0)))
                (last-blue (nth blues (- (length blues) 1)))
                (lr (fst last-blue))
                (lc (snd last-blue))
                (forward
                 (reduce (lambda (grid i)
                           (let* ((nr (+ lr (* (+ i 1) dr)))
                                  (nc (+ lc (* (+ i 1) dc))))
                             (if (and (>= nr 0) (< nr h) (>= nc 0) (< nc w))
                                 (set-cell grid nr nc 2)
                                 grid)))
                         g
                         (range 0 20))))
           (reduce (lambda (grid i)
                     (let* ((nr (- (fst p0) (* (+ i 1) dr)))
                            (nc (- (snd p0) (* (+ i 1) dc))))
                       (if (and (>= nr 0) (< nr h) (>= nc 0) (< nc w))
                           (set-cell grid nr nc 2)
                           grid)))
                   forward
                   (range 0 20)))))"""

# (height, width, start_row, start_col, count, row_step, col_step)
# Every scene is lawful for the canonical family and exposes both directions.
_SCENES = (
    (12, 14, 4, 4, 3, 2, 2),
    (14, 15, 6, 10, 3, 2, -2),
    (10, 16, 4, 3, 4, 0, 2),
    (16, 12, 3, 5, 3, 3, 0),
    (16, 16, 6, 9, 4, 2, -2),
    (14, 18, 3, 4, 3, 2, 3),
)


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("episode seed must be an integer (not bool)")
    if seed < 0:
        raise ValueError("episode seed must be nonnegative")
    return seed


def _validate_mode(mode: Any) -> str:
    if type(mode) is not str or mode not in ALLOWED_EXTENSION_MODES:
        raise ValueError(
            f"{PARAMETER_NAME} must be one of {ALLOWED_EXTENSION_MODES}, got {mode!r}"
        )
    return mode


def choose_parameters(seed: int) -> dict[str, str]:
    """Choose the hidden rule exactly once from an episode seed."""
    _validate_seed(seed)
    rng = stable_rng(seed, f"{TASK_ID}|parametric-rule", PROTOTYPE_VERSION)
    return {PARAMETER_NAME: ALLOWED_EXTENSION_MODES[rng.randrange(len(ALLOWED_EXTENSION_MODES))]}


def _make_grid(scene: tuple[int, int, int, int, int, int, int]) -> list[list[int]]:
    height, width, row0, col0, count, dr, dc = scene
    grid = [[0] * width for _ in range(height)]
    for index in range(count):
        grid[row0 + index * dr][col0 + index * dc] = 1
    errors = input_errors(grid)
    if errors:
        raise AssertionError("invalid prototype scene: " + "; ".join(errors))
    return grid


def episode_inputs(seed: int) -> list[list[list[int]]]:
    """Return four deterministic, distinct lawful inputs for one episode."""
    _validate_seed(seed)
    rng = stable_rng(seed, f"{TASK_ID}|parametric-inputs", PROTOTYPE_VERSION)
    scenes = rng.sample(list(_SCENES), 4)
    return [_make_grid(scene) for scene in scenes]


def _line_facts(grid: list[list[int]]) -> tuple[list[tuple[int, int]], int, int]:
    blues = sorted(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 1
    )
    dr = blues[1][0] - blues[0][0]
    dc = blues[1][1] - blues[0][1]
    return blues, dr, dc


def input_errors(grid: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be nonempty lists"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or value not in (0, 1) for row in grid for value in row):
        errors.append("input cells must be literal black (0) or blue (1) integers")
    blues = sorted(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 1
    )
    if not 2 <= len(blues) <= 5:
        errors.append("input must contain 2..5 blue cells")
        return errors
    dr = blues[1][0] - blues[0][0]
    dc = blues[1][1] - blues[0][1]
    if (dr, dc) == (0, 0):
        errors.append("blue spacing must be nonzero")
    if any(
        (row - prev_row, col - prev_col) != (dr, dc)
        for (prev_row, prev_col), (row, col) in zip(blues, blues[1:])
    ):
        errors.append("blue cells must form one row-major arithmetic line")
        return errors
    height = len(grid)
    before = (blues[0][0] - dr, blues[0][1] - dc)
    after = (blues[-1][0] + dr, blues[-1][1] + dc)
    if not (0 <= before[0] < height and 0 <= before[1] < width):
        errors.append("prototype inputs require an in-bounds backward continuation")
    if not (0 <= after[0] < height and 0 <= after[1] < width):
        errors.append("prototype inputs require an in-bounds forward continuation")
    return errors


def python_reference(
    grid: list[list[int]], *, extension_mode: str = DEFAULT_EXTENSION_MODE
) -> list[list[int]]:
    """Debug mirror; retained labels are produced by executing Racket."""
    mode = _validate_mode(extension_mode)
    errors = input_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    blues, dr, dc = _line_facts(grid)
    height, width = len(grid), len(grid[0])
    output = deepcopy(grid)

    row, col = blues[-1][0] + dr, blues[-1][1] + dc
    while 0 <= row < height and 0 <= col < width:
        output[row][col] = 2
        row += dr
        col += dc

    if mode == "both":
        row, col = blues[0][0] - dr, blues[0][1] - dc
        while 0 <= row < height and 0 <= col < width:
            output[row][col] = 2
            row -= dr
            col -= dc
    return output


def racket_program(parameters: dict[str, Any]) -> str:
    """Materialize the exact rule! program for one episode setting."""
    mode = _validate_mode(parameters.get(PARAMETER_NAME))
    return CANONICAL_RACKET if mode == DEFAULT_EXTENSION_MODE else BOTH_RACKET


def grid_literal(grid: list[list[int]]) -> str:
    errors = input_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    rows = " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    )
    return f"'({rows})"


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Redact the hidden setting, episode seed, rule source, and query answer."""
    return {
        "schema": "arc-parametric-public-challenge-v1",
        "task_id": TASK_ID,
        "demos": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["demos"]
        ],
        "query": {"input": deepcopy(episode["query"]["input"])},
    }
