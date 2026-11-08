#!/usr/bin/env python3
"""Isolated border-policy rule prototype for ARC task 196d5de2ea8c.

The selected production generator and its pinned authority remain canonical.
This prototype varies one nearby semantic choice once per episode:

* ``exclude_outer`` (canonical/default): regional modes start at row/column 1.
* ``include_outer``: adjacent regional modes also use row 0 and column 0.

All retained labels are produced by materialized Racket, not by the Python
mirror in this module.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from puzzle_generators.base import stable_rng

TASK_ID = "196d5de2ea8c"
PROTOTYPE_VERSION = "border-policy-v1"
PARAMETER_NAME = "border_policy"
DEFAULT_BORDER_POLICY = "exclude_outer"
ALLOWED_BORDER_POLICIES = (DEFAULT_BORDER_POLICY, "include_outer")
PARAMETER_SPEC = {
    PARAMETER_NAME: {
        "type": "enum",
        "allowed": list(ALLOWED_BORDER_POLICIES),
        "default": DEFAULT_BORDER_POLICY,
        "chosen": "once per episode from the deterministic episode seed",
        "input_constraints": (
            "the first uniform row/column must remain the divider; retained "
            "episodes use an outer-border color that changes at least one "
            "regional mode when the include_outer setting is selected"
        ),
    }
}

CANONICAL_RULE_HASH = "4af43de85dfe"
CANONICAL_SOURCE_SHA256 = (
    "82af978f86f5a43424151559a8c2911316aba0eab6f2a935ca018651bd5ee4b1"
)
CANONICAL_TL_CLAUSE = "(tl (region-color 1 div-row 1 div-col))"
CANONICAL_TR_CLAUSE = "(tr (region-color 1 div-row (+ div-col 1) w))"
CANONICAL_BL_CLAUSE = "(bl (region-color (+ div-row 1) h 1 div-col))"
ALTERNATIVE_TL_CLAUSE = "(tl (region-color 0 div-row 0 div-col))"
ALTERNATIVE_TR_CLAUSE = "(tr (region-color 0 div-row (+ div-col 1) w))"
ALTERNATIVE_BL_CLAUSE = "(bl (region-color (+ div-row 1) h 0 div-col))"

CANONICAL_SOURCE_FIXTURE = """(rule! (lambda (g)
  (let* ((div-row (find-first (lambda (r) (row-uniform? g r)) (range 0 h)))
         (div-col (find-first (lambda (c) (col-uniform? g c)) (range 0 w)))
         (divider (at g div-row div-col))
         (region-color (lambda (r1 r2 c1 c2) (mode-list (apply append (subgrid g r1 c1 (- r2 1) (- c2 1))))))
         (tl (region-color 1 div-row 1 div-col))
         (tr (region-color 1 div-row (+ div-col 1) w))
         (bl (region-color (+ div-row 1) h 1 div-col))
         (br (region-color (+ div-row 1) h (+ div-col 1) w)))
    (build-grid 3 3 (r c)
      (cond ((and (zero? r) (zero? c)) tl) ((and (zero? r) (= c 2)) tr)
            ((and (= r 2) (zero? c)) bl) ((and (= r 2) (= c 2)) br) (else divider))))))"""


def _sha256(value: str | bytes) -> str:
    data = value.encode() if isinstance(value, str) else value
    return hashlib.sha256(data).hexdigest()


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or seed < 0:
        raise TypeError("episode seed must be a nonnegative literal integer")
    return seed


def _validate_policy(policy: Any) -> str:
    if type(policy) is not str or policy not in ALLOWED_BORDER_POLICIES:
        raise ValueError(
            f"{PARAMETER_NAME} must be one of {ALLOWED_BORDER_POLICIES}"
        )
    return policy


def choose_parameters(seed: int) -> dict[str, str]:
    """Choose one hidden border policy for an entire episode."""
    _validate_seed(seed)
    rng = stable_rng(seed, f"{TASK_ID}|parametric-rule", PROTOTYPE_VERSION)
    return {
        PARAMETER_NAME: ALLOWED_BORDER_POLICIES[
            rng.randrange(len(ALLOWED_BORDER_POLICIES))
        ]
    }


def _check_canonical_source(source: Any) -> str:
    if not isinstance(source, str):
        raise TypeError("canonical Racket source must be text")
    if _sha256(source) != CANONICAL_SOURCE_SHA256:
        raise ValueError("canonical source SHA256 does not match the pinned rule")
    clauses = (
        CANONICAL_TL_CLAUSE,
        CANONICAL_TR_CLAUSE,
        CANONICAL_BL_CLAUSE,
    )
    if any(source.count(clause) != 1 for clause in clauses):
        raise ValueError("canonical source does not contain the expected region starts")
    return source


def canonical_source(*, root: Path | str | None = None) -> str:
    """Load and pin the canonical source from this execution tree."""
    from reviewer_support import canonical_path, find_root

    root = find_root(__file__) if root is None else Path(root).resolve()
    sources: set[str] = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(
                row.get("program_solution"), str
            ):
                sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError(f"expected one canonical Racket source, found {len(sources)}")
    return _check_canonical_source(sources.pop())


def materialize_rule(
    border_policy: str = DEFAULT_BORDER_POLICY,
    *,
    root: Path | str | None = None,
    source: str | None = None,
) -> str:
    """Return the exact Racket rule for one declared parameter setting."""
    policy = _validate_policy(border_policy)
    canonical = (
        canonical_source(root=root)
        if source is None
        else _check_canonical_source(source)
    )
    if policy == DEFAULT_BORDER_POLICY:
        return canonical
    replacements = (
        (CANONICAL_TL_CLAUSE, ALTERNATIVE_TL_CLAUSE),
        (CANONICAL_TR_CLAUSE, ALTERNATIVE_TR_CLAUSE),
        (CANONICAL_BL_CLAUSE, ALTERNATIVE_BL_CLAUSE),
    )
    alternative = canonical
    for old, new in replacements:
        alternative = alternative.replace(old, new, 1)
    if any(alternative.count(new) != 1 for _old, new in replacements):
        raise AssertionError("failed to materialize include_outer Racket source")
    return alternative


def restore_canonical(source: Any) -> str:
    """Prove that only the three declared region-start clauses changed."""
    if not isinstance(source, str):
        raise TypeError("Racket source must be text")
    restored = source
    for canonical, alternative in (
        (CANONICAL_TL_CLAUSE, ALTERNATIVE_TL_CLAUSE),
        (CANONICAL_TR_CLAUSE, ALTERNATIVE_TR_CLAUSE),
        (CANONICAL_BL_CLAUSE, ALTERNATIVE_BL_CLAUSE),
    ):
        counts = (restored.count(canonical), restored.count(alternative))
        if counts == (1, 0):
            continue
        if counts == (0, 1):
            restored = restored.replace(alternative, canonical, 1)
            continue
        raise ValueError("source contains an unsupported region-start mixture")
    return _check_canonical_source(restored)


def rule_callable(source: str) -> str:
    """Strip only the outer ``rule!`` wrapper and bind the legacy h/w names."""
    restore_canonical(source)
    if not source.startswith("(rule!") or not source.endswith(")"):
        raise ValueError("unexpected canonical rule wrapper")
    body = source[len("(rule!") : -1].strip()
    marker = "(lambda (g)"
    if body.count(marker) != 1:
        raise ValueError("expected exactly one wrapped grid lambda")
    grid_lambda = body[body.index(marker) :]
    return (
        "(lambda (g) "
        "(let* ((h (rows g)) (w (cols g))) "
        f"({grid_lambda} g)))"
    )


def _normalize_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list")
    if not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid rows must be nonempty lists")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        raise ValueError("grid cells must be literal ARC integers 0..9")
    return [list(row) for row in grid]


def grid_literal(grid: Any) -> str:
    rows = _normalize_grid(grid)
    return "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in rows
    ) + ")"


def execute_rule(source: str, grid: Any, *, bridge: Any) -> list[list[int]]:
    """Execute one materialized source through the packet Racket bridge."""
    expression = f"({rule_callable(source)} {grid_literal(grid)})"
    return _normalize_grid(bridge.eval_text(expression))


def _mode(values: list[int]) -> int:
    counts = Counter(values)
    maximum = max(counts.values())
    return min(color for color, count in counts.items() if count == maximum)


def python_reference(
    grid: list[list[int]],
    *,
    border_policy: str = DEFAULT_BORDER_POLICY,
) -> list[list[int]]:
    """Debug mirror only; retained episode labels come from executed Racket."""
    policy = _validate_policy(border_policy)
    rows = _normalize_grid(grid)
    height, width = len(rows), len(rows[0])
    uniform_rows = [r for r in range(height) if len(set(rows[r])) == 1]
    uniform_cols = [
        c for c in range(width) if len({rows[r][c] for r in range(height)}) == 1
    ]
    if not uniform_rows or not uniform_cols:
        raise ValueError("grid needs a uniform divider row and column")
    div_row, div_col = uniform_rows[0], uniform_cols[0]
    divider = rows[div_row][div_col]
    start = 1 if policy == DEFAULT_BORDER_POLICY else 0
    bounds = (
        (start, div_row, start, div_col),
        (start, div_row, div_col + 1, width),
        (div_row + 1, height, start, div_col),
        (div_row + 1, height, div_col + 1, width),
    )
    modes = [
        _mode(
            [
                rows[r][c]
                for r in range(row1, row2)
                for c in range(col1, col2)
            ]
        )
        for row1, row2, col1, col2 in bounds
    ]
    return [
        [modes[0], divider, modes[1]],
        [divider, divider, divider],
        [modes[2], divider, modes[3]],
    ]


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Omit the seed, hidden setting, source text, and masked query answer."""
    train = [
        {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
        for pair in episode["demos"]
    ]
    return {
        "schema": "arc-parametric-public-challenge-v1",
        "task_id": TASK_ID,
        "train": train,
        "test": [{"input": deepcopy(episode["query"]["input"])}],
    }
