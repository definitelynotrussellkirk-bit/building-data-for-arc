"""Isolated connectivity-rule prototype for ``fea6a4ce763f``.

The canonical task segments monochromatic 4-connected components, chooses the
unique largest component by cell count, and crops its bounding box.  This
prototype varies only the connectivity relation once per episode:

* ``four`` (default/original): exact canonical ``(rule! extract-largest)``.
* ``eight`` (proposed): use monochromatic 8-connected components instead.

The input constructor deliberately places two equal-colour 2x2 blocks in
corner contact.  They are separate size-4 objects under four-connectivity and
one size-8 object under eight-connectivity, while a separate size-6/7 target is
largest only under the canonical setting.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from puzzle_generators.base import stable_rng

TASK_ID = "fea6a4ce763f"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER_NAME = "connectivity"
DEFAULT_CONNECTIVITY = "four"
ALLOWED_CONNECTIVITY = (DEFAULT_CONNECTIVITY, "eight")
PARAMETER_SPEC = {
    PARAMETER_NAME: {
        "type": "enum",
        "allowed": list(ALLOWED_CONNECTIVITY),
        "default": DEFAULT_CONNECTIVITY,
        "chosen": "once per episode from the deterministic episode seed",
        "input_constraints": (
            "each pair has a unique largest object under both settings; two "
            "same-colour 2x2 blocks touch only diagonally so the settings give "
            "different largest objects and different crops"
        ),
    }
}

_TARGET_TEMPLATES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 1), (3, 2)),
)
_SQUARE = ((0, 0), (0, 1), (1, 0), (1, 1))
_TRIOMINO = ((0, 0), (0, 1), (1, 0))


def _validate_connectivity(value: Any) -> str:
    if type(value) is not str or value not in ALLOWED_CONNECTIVITY:
        raise ValueError(
            f"{PARAMETER_NAME} must be one of {ALLOWED_CONNECTIVITY}, got {value!r}"
        )
    return value


def choose_parameters(seed: int) -> dict[str, str]:
    """Choose the hidden connectivity exactly once from an episode seed."""
    if type(seed) is not int:
        raise TypeError("episode seed must be an integer (not bool)")
    rng = stable_rng(seed, f"{TASK_ID}|parametric-connectivity", PROTOTYPE_VERSION)
    return {
        PARAMETER_NAME: ALLOWED_CONNECTIVITY[
            rng.randrange(len(ALLOWED_CONNECTIVITY))
        ]
    }


def racket_callable(parameters: dict[str, Any]) -> str:
    """Return the bare callable executed by the protected Racket bridge.

    The shared ``wrap_rule`` helper is intentionally not required here: review
    packets can omit its historical ``scripts`` parser dependency, while these
    two bounded programs need no shorthand or dictionary rewriting.
    """
    setting = _validate_connectivity(parameters.get(PARAMETER_NAME))
    if setting == DEFAULT_CONNECTIVITY:
        return "extract-largest"
    return """(lambda (g)
  (let ([objs (objects-8 g 0)])
    (if (empty? objs)
        g
        (crop-object g (argmax obj-size objs)))))"""


def racket_program(parameters: dict[str, Any]) -> str:
    """Materialize the exact ``rule!`` text for one episode setting."""
    return f"(rule! {racket_callable(parameters)})"


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if any(not isinstance(row, list) or not row for row in grid):
        return ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                return [f"cell ({r},{c}) must be an integer colour 0..9"]
    return []


def _components(
    grid: list[list[int]], *, connectivity: str
) -> list[tuple[int, set[tuple[int, int]]]]:
    setting = _validate_connectivity(connectivity)
    if _validate_grid(grid):
        raise ValueError(_validate_grid(grid)[0])
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if setting == "eight":
        directions.extend([(1, 1), (1, -1), (-1, 1), (-1, -1)])
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, set[tuple[int, int]]]] = []
    for sr in range(h):
        for sc in range(w):
            colour = grid[sr][sc]
            if colour == 0 or (sr, sc) in seen:
                continue
            cells = {(sr, sc)}
            stack = [(sr, sc)]
            seen.add((sr, sc))
            while stack:
                r, c = stack.pop()
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == colour
                    ):
                        seen.add((nr, nc))
                        cells.add((nr, nc))
                        stack.append((nr, nc))
            result.append((colour, cells))
    return result


def _crop(
    grid: list[list[int]], cells: set[tuple[int, int]]
) -> list[list[int]]:
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def domain_errors(grid: Any, *, connectivity: str) -> list[str]:
    """Validate the bounded prototype domain for one connectivity setting."""
    errors = _validate_grid(grid)
    if errors:
        return errors
    components = _components(grid, connectivity=connectivity)
    if len(components) < 2:
        return ["expected at least two nonzero components"]
    sizes = [len(cells) for _, cells in components]
    if sizes.count(max(sizes)) != 1:
        return ["largest component must be unique"]
    return []


def python_reference(
    grid: list[list[int]], *, connectivity: str = DEFAULT_CONNECTIVITY
) -> list[list[int]]:
    """Debug mirror; retained labels are produced by executed Racket."""
    errors = domain_errors(grid, connectivity=connectivity)
    if errors:
        raise ValueError(errors[0])
    components = _components(grid, connectivity=connectivity)
    _, cells = max(components, key=lambda item: len(item[1]))
    return _crop(grid, cells)


def _paint(
    grid: list[list[int]],
    origin: tuple[int, int],
    cells: tuple[tuple[int, int], ...],
    colour: int,
) -> None:
    top, left = origin
    for dr, dc in cells:
        grid[top + dr][left + dc] = colour


def _reflect_lr(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def _reflect_ud(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in reversed(grid)]


def make_input(seed: int, pair_index: int) -> list[list[int]]:
    """Create one pair that distinguishes four- from eight-connectivity."""
    if type(seed) is not int or type(pair_index) is not int or pair_index < 0:
        raise ValueError("seed and non-negative pair_index must be integers")
    rng = stable_rng(
        seed,
        f"{TASK_ID}|parametric-input|{pair_index}",
        PROTOTYPE_VERSION,
    )
    grid = [[0 for _ in range(13)] for _ in range(9)]
    colours = rng.sample(range(1, 10), 3)
    target_colour, diagonal_colour, extra_colour = colours

    target = rng.choice(_TARGET_TEMPLATES)
    _paint(grid, (1, 1), target, target_colour)
    _paint(grid, (1, 7), _SQUARE, diagonal_colour)
    _paint(grid, (3, 9), _SQUARE, diagonal_colour)
    _paint(grid, (6, 5), _TRIOMINO, extra_colour)

    if rng.choice((False, True)):
        grid = _reflect_lr(grid)
    if rng.choice((False, True)):
        grid = _reflect_ud(grid)

    for setting in ALLOWED_CONNECTIVITY:
        errors = domain_errors(grid, connectivity=setting)
        if errors:
            raise AssertionError(f"constructed invalid {setting} input: {errors}")
    if python_reference(grid, connectivity="four") == python_reference(
        grid, connectivity="eight"
    ):
        raise AssertionError("constructed input does not distinguish connectivity")
    return grid


def grid_literal(grid: list[list[int]]) -> str:
    errors = _validate_grid(grid)
    if errors:
        raise ValueError(errors[0])
    rows = " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    )
    return f"'({rows})"


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Remove the hidden setting, seed, Racket text, and query answer."""
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
