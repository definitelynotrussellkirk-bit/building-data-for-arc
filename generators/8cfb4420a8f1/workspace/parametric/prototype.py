"""Isolated parametric-rule prototype for ARC task 8cfb4420a8f1.

This module is intentionally outside the selected generator path.  It varies one
small rule parameter once per episode:

* ``erase_scope='body_only'`` (canonical/default): preserve the top marker.
* ``erase_scope='all_occurrences'``: erase the marker too.

The exact Racket callable is materialized for each setting.  ``build_prototype``
executes those callables through the included Racket bridge; ``python_reference``
is only a test/debug mirror.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from puzzle_generators.base import stable_rng

TASK_ID = "8cfb4420a8f1"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER_NAME = "erase_scope"
DEFAULT_ERASE_SCOPE = "body_only"
ALLOWED_ERASE_SCOPES = (DEFAULT_ERASE_SCOPE, "all_occurrences")
PARAMETER_SPEC = {
    PARAMETER_NAME: {
        "type": "enum",
        "allowed": list(ALLOWED_ERASE_SCOPES),
        "default": DEFAULT_ERASE_SCOPE,
        "chosen": "once per episode from the deterministic episode seed",
        "input_constraints": (
            "row 0 must contain exactly one nonzero marker and the same colour "
            "must occur in the body; these make the two settings observable"
        ),
    }
}


def _validate_scope(scope: Any) -> str:
    if scope not in ALLOWED_ERASE_SCOPES:
        raise ValueError(
            f"{PARAMETER_NAME} must be one of {ALLOWED_ERASE_SCOPES}, got {scope!r}"
        )
    return str(scope)


def choose_parameters(seed: int) -> dict[str, str]:
    """Choose the hidden rule once from an episode seed."""
    if type(seed) is not int:
        raise TypeError("episode seed must be an integer (not bool)")
    rng = stable_rng(seed, f"{TASK_ID}|parametric-rule", PROTOTYPE_VERSION)
    return {PARAMETER_NAME: ALLOWED_ERASE_SCOPES[rng.randrange(len(ALLOWED_ERASE_SCOPES))]}


def _marker(grid: list[list[int]]) -> tuple[int, int]:
    if not (
        isinstance(grid, list)
        and grid
        and isinstance(grid[0], list)
        and grid[0]
        and all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
    ):
        raise ValueError("grid must be a nonempty rectangle")
    top = [(c, value) for c, value in enumerate(grid[0]) if value != 0]
    if len(top) != 1:
        raise ValueError("row 0 must contain exactly one nonzero marker")
    return top[0]


def python_reference(
    grid: list[list[int]], *, erase_scope: str = DEFAULT_ERASE_SCOPE
) -> list[list[int]]:
    """Debug mirror.  Retained evidence uses Racket, not this function, for labels."""
    scope = _validate_scope(erase_scope)
    marker_col, marker_color = _marker(grid)
    out = deepcopy(grid)
    for r, row in enumerate(out):
        for c, value in enumerate(row):
            if value != marker_color:
                continue
            if scope == "all_occurrences" or (r, c) != (0, marker_col):
                out[r][c] = 0
    return out


def racket_program(parameters: dict[str, Any]) -> str:
    """Materialize the exact callable Racket program for one episode setting."""
    scope = _validate_scope(parameters.get(PARAMETER_NAME))
    erase_guard = (
        "#t"
        if scope == "all_occurrences"
        else "(not (and (= r 0) (= c marker-col)))"
    )
    return f"""(lambda (g)
  (let* ([marker-col
          (first
           (filter (lambda (c) (not (= (at g 0 c) 0)))
                   (range 0 (cols g))))]
         [marker-color (at g 0 marker-col)])
    (grid-from-fn
     (rows g) (cols g)
     (lambda (r c)
       (let ([value (at g r c)])
         (if (and (= value marker-color) {erase_guard})
             0
             value))))))"""


def grid_literal(grid: list[list[int]]) -> str:
    _marker(grid)
    rows = " ".join(
        "(" + " ".join(str(int(value)) for value in row) + ")" for row in grid
    )
    return f"'({rows})"


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Redact the hidden setting, Racket source, seed, and query answer."""
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
