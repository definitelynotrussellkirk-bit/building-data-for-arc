"""Isolated flood-connectivity prototype for ``6c8eefa043e1``.

The selected production generator and canonical rule remain unchanged.  This
prototype varies only whether a seed propagates through orthogonal neighbours
(the original/default rule) or through all eight neighbours.  Walls, seed
roles, row-major seed processing, and preservation of unseeded components stay
fixed.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from puzzle_generators.base import stable_rng

TASK_ID = "6c8eefa043e1"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER_NAME = "connectivity"
DEFAULT_CONNECTIVITY = "four"
ALLOWED_CONNECTIVITY = (DEFAULT_CONNECTIVITY, "eight")
PARAMETER_SPEC = {
    PARAMETER_NAME: {
        "type": "enum",
        "allowed": list(ALLOWED_CONNECTIVITY),
        "default": DEFAULT_CONNECTIVITY,
        "chosen": "once per deterministic episode seed",
        "invariant_reasoning": (
            "identify non-gray seeds; remove each seed marker in row-major "
            "order; propagate its color through connected zero cells; preserve "
            "gray walls and every component without a seed"
        ),
        "input_constraints": (
            "each seed belongs to a different non-wall component under both "
            "settings; every pair includes a seedless satellite touching one "
            "seeded component only at a corner, so four and eight connectivity "
            "produce different outputs; another seed and an isolated unseeded "
            "component preserve the original object roles"
        ),
    }
}

CANONICAL_RACKET_PROGRAM = """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let ((colored (for*/list ((r (range 0 (rows g))) (c (range 0 (cols g)))
                              #:when
                              (let ((v (at g r c))) (and (!= v 0) (!= v 5))))
                            (list r c (at g r c)))))
             (let loop
                  ((grid g) (seeds colored))
                  (cond
                    ((null? seeds) grid)
                    (else (let* ((seed (car seeds))
                                 (sr (first seed))
                                 (sc (second seed))
                                 (clr (third seed))
                                 (g2 (set-cell grid sr sc 0))
                                 (g3 (flood-fill g2 sr sc clr)))
                            (loop g3 (cdr seeds))))))))))"""

_EIGHT_CALLABLE = """(lambda (g)
  (let ((colored
         (for*/list ((r (range 0 (rows g)))
                     (c (range 0 (cols g)))
                     #:when
                     (let ((v (at g r c)))
                       (and (!= v 0) (!= v 5))))
           (list r c (at g r c)))))
    (letrec ((flood-8
              (lambda (grid sr sc clr)
                (let grow ((current (set-cell grid sr sc clr)))
                  (let ((next
                         (map-grid
                          current
                          (lambda (r c v)
                            (if (and (= v 0)
                                     (member clr (neighbors-8 current r c -1)))
                                clr
                                v)))))
                    (if (equal? next current)
                        current
                        (grow next)))))))
      (let loop ((grid g) (seeds colored))
        (cond
          ((null? seeds) grid)
          (else
           (let* ((seed (car seeds))
                  (sr (first seed))
                  (sc (second seed))
                  (clr (third seed))
                  (g2 (set-cell grid sr sc 0))
                  (g3 (flood-8 g2 sr sc clr)))
             (loop g3 (cdr seeds)))))))))"""

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_ALL_EIGHT = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if dr or dc
)
_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)


def _validate_connectivity(value: Any) -> str:
    if type(value) is not str or value not in ALLOWED_CONNECTIVITY:
        raise ValueError(
            f"{PARAMETER_NAME} must be one of {ALLOWED_CONNECTIVITY}, got {value!r}"
        )
    return value


def choose_parameters(seed: int) -> dict[str, str]:
    """Choose the hidden rule exactly once for an entire episode."""
    if type(seed) is not int:
        raise TypeError("episode seed must be an integer (not bool)")
    rng = stable_rng(
        seed,
        f"{TASK_ID}|parametric-flood-connectivity",
        PROTOTYPE_VERSION,
    )
    return {
        PARAMETER_NAME: ALLOWED_CONNECTIVITY[
            rng.randrange(len(ALLOWED_CONNECTIVITY))
        ]
    }


def racket_callable(parameters: dict[str, Any]) -> str:
    setting = _validate_connectivity(parameters.get(PARAMETER_NAME))
    if setting == DEFAULT_CONNECTIVITY:
        prefix = "(rule! "
        assert CANONICAL_RACKET_PROGRAM.startswith(prefix)
        return CANONICAL_RACKET_PROGRAM[len(prefix) : -1]
    return _EIGHT_CALLABLE


def racket_program(parameters: dict[str, Any]) -> str:
    setting = _validate_connectivity(parameters.get(PARAMETER_NAME))
    if setting == DEFAULT_CONNECTIVITY:
        return CANONICAL_RACKET_PROGRAM
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
                return [f"cell ({r},{c}) must be an integer color 0..9"]
    return []


def _seeds(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5)
    ]


def _nonwall_components(
    grid: list[list[int]], *, connectivity: str
) -> list[set[tuple[int, int]]]:
    setting = _validate_connectivity(connectivity)
    directions = _CARDINAL if setting == "four" else _ALL_EIGHT
    h, w = len(grid), len(grid[0])
    unseen = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] != 5
    }
    result: list[set[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in directions:
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    stack.append(point)
        result.append(component)
    return result


def domain_errors(grid: Any, *, connectivity: str) -> list[str]:
    """Validate the bounded prototype domain for one setting."""
    setting = _validate_connectivity(connectivity)
    errors = _validate_grid(grid)
    if errors:
        return errors
    assert isinstance(grid, list)
    seeds = _seeds(grid)
    result: list[str] = []
    if len(seeds) != 2:
        result.append("prototype expects exactly two seed cells")
    if len({color for _, _, color in seeds}) != len(seeds):
        result.append("seed colors must be distinct")
    if not any(5 in row for row in grid):
        result.append("expected color-5 walls")
    unseeded = 0
    seeded = 0
    for component in _nonwall_components(grid, connectivity=setting):
        members = [seed for seed in seeds if (seed[0], seed[1]) in component]
        if len(members) > 1:
            result.append("competing seeds in one component")
        elif len(members) == 1:
            seeded += 1
            if len(component) == 1:
                result.append("seeded component has no zero cell to fill")
        else:
            unseeded += 1
    if seeded != len(seeds):
        result.append("every seed must occupy a non-wall component")
    if unseeded < 1:
        result.append("expected at least one unseeded component")
    return result


def python_reference(
    grid: list[list[int]], *, connectivity: str = DEFAULT_CONNECTIVITY
) -> list[list[int]]:
    """Debug mirror; retained evidence labels come from executed Racket."""
    setting = _validate_connectivity(connectivity)
    errors = domain_errors(grid, connectivity=setting)
    if errors:
        raise ValueError(errors[0])
    out = [list(row) for row in grid]
    h, w = len(out), len(out[0])
    directions = _CARDINAL if setting == "four" else _ALL_EIGHT
    for sr, sc, color in _seeds(grid):
        out[sr][sc] = 0
        stack = [(sr, sc)]
        while stack:
            r, c = stack.pop()
            if not (0 <= r < h and 0 <= c < w) or out[r][c] != 0:
                continue
            out[r][c] = color
            stack.extend((r + dr, c + dc) for dr, dc in directions)
    return out


def _transform(grid: list[list[int]], code: int) -> list[list[int]]:
    """Apply one of the eight square-grid dihedral transforms to a rectangle."""
    result = [list(row) for row in grid]
    if code >= 4:
        result = [list(row) for row in zip(*result)]
        code -= 4
    for _ in range(code):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def make_input(seed: int, pair_index: int) -> list[list[int]]:
    """Construct a lawful pair with an explicit diagonal-connectivity witness."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(pair_index) is not int:
        raise TypeError("pair_index must be an integer (not bool)")
    if pair_index < 0:
        raise ValueError("pair_index must be non-negative")
    rng = stable_rng(
        seed,
        f"{TASK_ID}|parametric-input|{pair_index}",
        PROTOTYPE_VERSION,
    )
    grid = [[5 for _ in range(13)] for _ in range(9)]

    # A seeded component and a seedless satellite touch only diagonally.
    primary = {(1, 1), (1, 2), (2, 1)}
    satellite_variants = (
        {(3, 2), (3, 3), (4, 3), (4, 4)},
        {(3, 2), (4, 2), (4, 3), (5, 3)},
        {(3, 2), (3, 3), (3, 4), (4, 4)},
        {(3, 2), (4, 2), (5, 2), (5, 3)},
    )
    satellite = satellite_variants[pair_index % len(satellite_variants)]
    second_seeded = {(1, 9), (1, 10), (2, 9), (2, 10), (2, 11)}
    isolated_unseeded = {(6, 8), (6, 9), (7, 9), (7, 10)}

    for r, c in primary | satellite | second_seeded | isolated_unseeded:
        grid[r][c] = 0
    first_color, second_color = rng.sample(_COLORS, 2)
    first_seed = rng.choice(sorted(primary))
    second_seed = rng.choice(sorted(second_seeded))
    grid[first_seed[0]][first_seed[1]] = first_color
    grid[second_seed[0]][second_seed[1]] = second_color

    grid = _transform(grid, (pair_index + rng.randrange(8)) % 8)
    for setting in ALLOWED_CONNECTIVITY:
        errors = domain_errors(grid, connectivity=setting)
        if errors:
            raise AssertionError(f"constructed invalid {setting} input: {errors}")
    if python_reference(grid, connectivity="four") == python_reference(
        grid, connectivity="eight"
    ):
        raise AssertionError("constructed input does not distinguish connectivity")
    return grid


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Remove hidden parameters, seed, reference code, and query answer."""
    return {
        "schema": "arc-parametric-public-challenge-v1",
        "task_id": TASK_ID,
        "demos": [
            {
                "input": deepcopy(pair["input"]),
                "output": deepcopy(pair["output"]),
            }
            for pair in episode["demos"]
        ],
        "query": {"input": deepcopy(episode["query"]["input"])},
    }
