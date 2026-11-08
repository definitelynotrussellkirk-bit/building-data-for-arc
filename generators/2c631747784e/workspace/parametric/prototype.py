"""Isolated reverse-then-shift rule prototype for ARC task 2c631747784e.

The selected production generator and canonical authority remain unchanged.  This
prototype varies one small episode-level count after the canonical path-color
reversal:

* ``reverse_shift=0`` (canonical/default): reverse the path colors.
* ``reverse_shift=1``: reverse, then cyclically shift the reversed sequence one
  path position toward the traversal start.

The path detection, endpoint traversal, object roles, background, and preserved
coordinates are identical in both settings.  Retained labels are produced by
executing the instantiated Racket source; ``python_reference`` is a parity oracle.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
from typing import Any

from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)

TASK_ID = "2c631747784e"
PROTOTYPE_VERSION = "reverse-shift-v1"
PARAMETER_NAME = "reverse_shift"
DEFAULT_REVERSE_SHIFT = 0
ALLOWED_REVERSE_SHIFTS = (DEFAULT_REVERSE_SHIFT, 1)
PARAMETER_SPEC = {
    PARAMETER_NAME: {
        "type": "int",
        "allowed": list(ALLOWED_REVERSE_SHIFTS),
        "default": DEFAULT_REVERSE_SHIFT,
        "chosen": "once per episode from the deterministic episode seed",
        "meaning": (
            "cyclic left shift applied after reversing the path-color sequence"
        ),
        "input_constraints": (
            "the path contains at least two distinct colors, so shifts 0 and 1 "
            "produce different outputs on every retained pair"
        ),
    }
}

ROOT = find_root(__file__)
GEN, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_BINDING = "(reversed-colors (reverse path-colors))"
_SHIFTED_BINDINGS = """(reversed-base (reverse path-colors))
         (reversed-colors
          (append (rest reversed-base) (list (first reversed-base))))"""


def sha256(value: str | bytes) -> str:
    raw = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(raw).hexdigest()


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("episode seed must be an integer (not bool)")
    if seed < 0:
        raise ValueError("episode seed must be nonnegative")
    return seed


def _validate_shift(reverse_shift: Any) -> int:
    if type(reverse_shift) is not int:
        raise TypeError("reverse_shift must be a literal integer")
    if reverse_shift not in ALLOWED_REVERSE_SHIFTS:
        raise ValueError(
            f"reverse_shift must be one of {ALLOWED_REVERSE_SHIFTS}, "
            f"got {reverse_shift!r}"
        )
    return reverse_shift


def choose_parameters(seed: int) -> dict[str, int]:
    """Select one hidden setting for the complete episode."""
    seed = _validate_seed(seed)
    return {PARAMETER_NAME: ALLOWED_REVERSE_SHIFTS[seed % len(ALLOWED_REVERSE_SHIFTS)]}


@lru_cache(maxsize=4)
def canonical_rule_source(*, root: str | Path | None = None) -> str:
    """Return the unique canonical Racket source across ledger variants."""
    selected_root = ROOT if root is None else Path(root).resolve()
    sources: set[str] = set()
    with canonical_path(selected_root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            source = row.get("program_solution")
            if isinstance(source, str):
                sources.add(source)
    if len(sources) != 1:
        raise ValueError(
            f"expected one unique canonical program_solution for {TASK_ID}, "
            f"found {len(sources)}"
        )
    source = sources.pop()
    if source.count(_CANONICAL_BINDING) != 1:
        raise ValueError("canonical reversal binding changed; reassess the prototype")
    return source


def instantiate_rule(
    reverse_shift: int = DEFAULT_REVERSE_SHIFT,
    *,
    root: str | Path | None = None,
    source: str | None = None,
) -> str:
    """Materialize exact Racket source for one bounded parameter setting."""
    shift = _validate_shift(reverse_shift)
    canonical = canonical_rule_source(root=root) if source is None else source
    if canonical.count(_CANONICAL_BINDING) != 1:
        raise ValueError("source must contain exactly one canonical reversal binding")
    if shift == DEFAULT_REVERSE_SHIFT:
        return canonical
    alternative = canonical.replace(_CANONICAL_BINDING, _SHIFTED_BINDINGS, 1)
    if alternative == canonical or alternative.count(_SHIFTED_BINDINGS) != 1:
        raise AssertionError("failed to instantiate reverse_shift=1")
    return alternative


def _trace_path(grid: list[list[int]]) -> list[tuple[int, int]]:
    """Mirror the canonical row-major endpoint and neighbor traversal."""
    normalized = normalize_grid(grid)
    cells = [
        (r, c)
        for r, row in enumerate(normalized)
        for c, value in enumerate(row)
        if value != 8
    ]
    if len(cells) < 2:
        raise ValueError("prototype domain requires a nontrivial non-cyan path")
    cell_set = set(cells)

    def neighbors(cell: tuple[int, int]) -> list[tuple[int, int]]:
        r, c = cell
        return [
            (r + dr, c + dc)
            for dr, dc in _DIRS
            if (r + dr, c + dc) in cell_set
        ]

    endpoints = [cell for cell in cells if len(neighbors(cell)) == 1]
    if len(endpoints) != 2 or any(len(neighbors(cell)) > 2 for cell in cells):
        raise ValueError("non-cyan cells must form one unbranched path")

    path: list[tuple[int, int]] = []
    visited: set[tuple[int, int]] = set()
    current: tuple[int, int] | None = endpoints[0]
    while current is not None:
        path.append(current)
        visited.add(current)
        unvisited = [cell for cell in neighbors(current) if cell not in visited]
        if len(unvisited) > 1:
            raise ValueError("path branches during traversal")
        current = unvisited[0] if unvisited else None
    if len(path) != len(cells):
        raise ValueError("non-cyan path is disconnected")
    return path


def python_reference(
    grid: list[list[int]], *, reverse_shift: int = DEFAULT_REVERSE_SHIFT
) -> list[list[int]]:
    """Parity oracle only; retained labels are executed by Racket."""
    shift = _validate_shift(reverse_shift)
    normalized = normalize_grid(grid)
    path = _trace_path(normalized)
    colors = [normalized[r][c] for r, c in path]
    transformed = list(reversed(colors))
    if shift:
        transformed = transformed[shift:] + transformed[:shift]
    output = deepcopy(normalized)
    for (r, c), color in zip(path, transformed):
        output[r][c] = color
    return output


def evaluate(bridge: Any, program: str, grid: list[list[int]]) -> list[list[int]]:
    """Execute one instantiated rule with the included Racket bridge."""
    function = strip_rule_wrapper(program)
    if not function.startswith("(lambda (g)"):
        raise ValueError("expected rule! to wrap a grid lambda")
    normalized = normalize_grid(grid)
    datum = "'(" + " ".join(
        "(" + " ".join(str(value) for value in row) + ")"
        for row in normalized
    ) + ")"
    return normalize_grid(bridge.eval_text(f"({function} {datum})"))


def generate_inputs(seed: int) -> list[list[list[int]]]:
    """Generate four lawful inputs independently of the hidden setting."""
    seed = _validate_seed(seed)
    bands = ("easy", "medium", "hard", "medium")
    return [
        GEN.generate(47_000 + seed * 101, index, difficulty=band)
        for index, band in enumerate(bands)
    ]


def make_episode(
    bridge: Any,
    seed: int,
    *,
    reverse_shift: int | None = None,
) -> dict[str, Any]:
    """Build one three-demo/one-query episode with Racket-derived labels."""
    seed = _validate_seed(seed)
    chosen = (
        choose_parameters(seed)[PARAMETER_NAME]
        if reverse_shift is None
        else _validate_shift(reverse_shift)
    )
    source = instantiate_rule(chosen)
    alternative = next(value for value in ALLOWED_REVERSE_SHIFTS if value != chosen)
    alternative_source = instantiate_rule(alternative)

    pairs: list[dict[str, Any]] = []
    alternative_outputs: list[list[list[int]]] = []
    for index, grid in enumerate(generate_inputs(seed)):
        output = evaluate(bridge, source, grid)
        mirror = python_reference(grid, reverse_shift=chosen)
        if output != mirror:
            raise AssertionError(f"Racket/Python mismatch for pair {index}")
        if chosen == DEFAULT_REVERSE_SHIFT and output != GEN.rule_mirror(grid):
            raise AssertionError(f"canonical default mismatch for pair {index}")
        rival_output = evaluate(bridge, alternative_source, grid)
        if rival_output == output:
            raise AssertionError(f"pair {index} does not distinguish the settings")
        pairs.append({"input": grid, "output": output})
        alternative_outputs.append(rival_output)

    demos = pairs[:3]
    query = pairs[3]
    refuting_demo_indices = [
        index
        for index, pair in enumerate(demos)
        if alternative_outputs[index] != pair["output"]
    ]
    if not refuting_demo_indices:
        raise AssertionError("demonstrations do not identify the chosen setting")

    return {
        "schema": "2c631747784e-reverse-shift-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameters": {PARAMETER_NAME: chosen},
        "parameter_chosen_once_for_episode": True,
        "racket_program": source,
        "racket_sha256": sha256(source),
        "demos": demos,
        "query": query,
        "rival": {
            "parameters": {PARAMETER_NAME: alternative},
            "racket_program": alternative_source,
            "racket_sha256": sha256(alternative_source),
            "outputs": alternative_outputs,
            "refuting_demonstration_indices": refuting_demo_indices,
            "query_differs": alternative_outputs[3] != query["output"],
        },
        "checks": {
            "three_demonstrations": len(demos) == 3,
            "one_query": bool(query.get("output")),
            "all_labels_executed_in_racket": True,
            "python_mirror_parity": True,
            "default_matches_canonical_rule": chosen != 0
            or all(pair["output"] == GEN.rule_mirror(pair["input"]) for pair in pairs),
            "demos_distinguish_alternative": bool(refuting_demo_indices),
            "every_pair_distinguishes_alternative": all(
                rival != pair["output"]
                for rival, pair in zip(alternative_outputs, pairs)
            ),
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Remove hidden semantics, source, seed, and the query answer."""
    return {
        "schema": "arc-parametric-public-challenge-v1",
        "task_id": TASK_ID,
        "demos": deepcopy(episode["demos"]),
        "query": {"input": deepcopy(episode["query"]["input"])},
    }
