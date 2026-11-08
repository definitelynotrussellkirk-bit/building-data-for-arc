"""Isolated parametric-rule prototype for ARC task f1347e0836ec.

The selected generator and canonical Racket authority remain unchanged.  This
prototype varies exactly one hidden rule parameter once per episode:

* ``trigger_diagonal='main'`` (canonical/default): the diagonal orientation is
  used when the unique dot lies on the main diagonal.
* ``trigger_diagonal='anti'``: the same orientation is used when the unique dot
  lies on the anti-diagonal.

All retained labels are produced by executing the materialized Racket program.
Python helpers in this module are validation/export plumbing, not label
authority.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.base import stable_rng

TASK_ID = "f1347e0836ec"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER_NAME = "trigger_diagonal"
DEFAULT_TRIGGER_DIAGONAL = "main"
ALLOWED_TRIGGER_DIAGONALS = (DEFAULT_TRIGGER_DIAGONAL, "anti")
PARAMETER_SPEC = {
    PARAMETER_NAME: {
        "type": "enum",
        "allowed": list(ALLOWED_TRIGGER_DIAGONALS),
        "default": DEFAULT_TRIGGER_DIAGONAL,
        "chosen": "once per episode from a deterministic integer seed",
        "meaning": (
            "which diagonal predicate selects the existing top-right / "
            "bottom-left corner-arm orientation"
        ),
    }
}


def _validate_trigger_diagonal(value: Any) -> str:
    if type(value) is not str or value not in ALLOWED_TRIGGER_DIAGONALS:
        raise ValueError(
            f"{PARAMETER_NAME} must be one of {ALLOWED_TRIGGER_DIAGONALS}, "
            f"got {value!r}"
        )
    return value


def choose_parameters(seed: int) -> dict[str, str]:
    """Choose one hidden rule setting from an episode seed."""
    if type(seed) is not int:
        raise TypeError("episode seed must be an integer (not bool, float, or string)")
    rng = stable_rng(seed, f"{TASK_ID}|parametric-rule", PROTOTYPE_VERSION)
    return {
        PARAMETER_NAME: ALLOWED_TRIGGER_DIAGONALS[
            rng.randrange(len(ALLOWED_TRIGGER_DIAGONALS))
        ]
    }


def racket_program(parameters: dict[str, Any]) -> str:
    """Materialize an exact callable Racket program for one rule setting."""
    if not isinstance(parameters, dict):
        raise ValueError("parameters must be a mapping containing trigger_diagonal")
    trigger = _validate_trigger_diagonal(parameters.get(PARAMETER_NAME))
    predicate = "(= dr dc)" if trigger == "main" else "(= (+ dr dc) (- w 1))"
    return f"""(lambda (g)
  (let* ((h (rows g))
         (w (cols g)))
    (let* ((bg (at g 0 0))
           (dot (find-first (lambda (p) (!= (at g (fst p) (snd p)) bg))
                            (flatmap (lambda (r)
                                       (map (lambda (c) (cons r c)) (range 0 w)))
                                     (range 0 h))))
           (dr (fst dot))
           (dc (snd dot))
           (anti {predicate})
           (tc-c (if anti (- w 1) 0))
           (bc-c (if anti 0 (- w 1))))
      (cellmap g
               (r c v)
               (let ((v v))
                 (if (!= v bg)
                     v
                     (if (or
                           (and (= c dc) (< r dr))
                           (and
                             (zero? r)
                             (>= c (min dc tc-c))
                             (<= c (max dc tc-c)))
                           (and (= c dc) (> r dr))
                           (and
                             (= r (- h 1))
                             (>= c (min dc bc-c))
                             (<= c (max dc bc-c))))
                         1
                         v)))))))"""


def _validated_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a nonempty rectangle")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("grid rows must be nonempty sequences")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    result: list[list[int]] = []
    for row in grid:
        converted: list[int] = []
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                raise ValueError("grid cells must be literal ARC integers 0..9")
            converted.append(value)
        result.append(converted)
    return result


def grid_literal(grid: Any) -> str:
    """Encode a validated ARC grid as a quoted Racket list."""
    validated = _validated_grid(grid)
    rows = " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in validated
    )
    return f"'({rows})"


def _coerce_grid(result: Any) -> list[list[int]]:
    if not (
        isinstance(result, list)
        and result
        and all(isinstance(row, list) and row for row in result)
        and len({len(row) for row in result}) == 1
    ):
        raise RuntimeError(f"Racket returned a non-grid result: {result!r}")
    out: list[list[int]] = []
    for row in result:
        converted: list[int] = []
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                raise RuntimeError(f"Racket returned an invalid ARC cell: {value!r}")
            converted.append(value)
        out.append(converted)
    return out


def execute_program(
    program: str,
    grids: Iterable[Any],
    bridge: RacketBridge | None = None,
) -> list[list[list[int]]]:
    """Execute ``program`` on each grid, sharing or temporarily owning a bridge."""
    materialized = list(grids)
    if bridge is not None:
        return [
            _coerce_grid(bridge.eval_text(f"({program} {grid_literal(grid)})"))
            for grid in materialized
        ]
    with RacketBridge(timeout=20, max_calls_before_restart=48) as owned_bridge:
        return [
            _coerce_grid(
                owned_bridge.eval_text(f"({program} {grid_literal(grid)})")
            )
            for grid in materialized
        ]


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Export demonstrations and query input without hidden-rule leakage."""
    demos = [
        {
            "input": deepcopy(pair["input"]),
            "output": deepcopy(pair["output"]),
        }
        for pair in episode["demos"]
    ]
    return {
        "schema": "arc-parametric-public-challenge-v1",
        "task_id": TASK_ID,
        "demos": demos,
        "query": {"input": deepcopy(episode["query"]["input"])},
    }


def _generator_module(generator_bundle: Any = None):
    if generator_bundle is None:
        from reviewer_support import find_root, load_selected_generator

        root = find_root(__file__)
        generator_bundle = load_selected_generator(TASK_ID, root=root)
    if isinstance(generator_bundle, tuple):
        if not generator_bundle:
            raise ValueError("generator_bundle tuple must contain the generator module")
        generator = generator_bundle[0]
    else:
        generator = generator_bundle
    if not callable(getattr(generator, "generate", None)):
        raise ValueError("generator_bundle must provide a callable generate function")
    return generator


def _check_identifiability_with_bridge(
    demos: list[dict[str, Any]], bridge: RacketBridge
) -> dict[str, Any]:
    if not isinstance(demos, list) or not demos:
        raise ValueError("demos must be a nonempty list of input/output pairs")
    inputs: list[list[list[int]]] = []
    expected: list[list[list[int]]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or set(pair) != {"input", "output"}:
            raise ValueError(f"demo {index} must contain exactly input and output")
        inputs.append(_validated_grid(pair["input"]))
        expected.append(_validated_grid(pair["output"]))

    matches: dict[str, list[bool]] = {}
    survivors: list[str] = []
    for setting in ALLOWED_TRIGGER_DIAGONALS:
        actual = execute_program(
            racket_program({PARAMETER_NAME: setting}), inputs, bridge=bridge
        )
        per_demo = [got == want for got, want in zip(actual, expected, strict=True)]
        matches[setting] = per_demo
        if all(per_demo):
            survivors.append(setting)
    return {
        "demonstration_count": len(demos),
        "surviving_settings": survivors,
        "unique": len(survivors) == 1,
        "matches_by_setting": matches,
    }


def check_identifiability(
    demos: list[dict[str, Any]], bridge: RacketBridge | None = None
) -> dict[str, Any]:
    """Return which declared rule settings fit the demonstrations exactly."""
    if bridge is not None:
        return _check_identifiability_with_bridge(demos, bridge)
    with RacketBridge(timeout=20, max_calls_before_restart=48) as owned_bridge:
        return _check_identifiability_with_bridge(demos, owned_bridge)


def _make_episode_with_bridge(
    seed: int,
    bridge: RacketBridge,
    generator_bundle: Any = None,
) -> dict[str, Any]:
    parameters = choose_parameters(seed)
    generator = _generator_module(generator_bundle)
    input_seed = stable_rng(
        seed, f"{TASK_ID}|parametric-inputs", PROTOTYPE_VERSION
    ).randrange(0, 2**63)
    sample_indices = list(range(4))
    inputs = [
        generator.generate(input_seed, sample_index, difficulty="medium")
        for sample_index in sample_indices
    ]
    for index, grid in enumerate(inputs):
        errors = generator.self_check(grid, difficulty="medium")
        if errors:
            raise AssertionError(
                f"selected generator produced invalid episode input {index}: {errors}"
            )

    program = racket_program(parameters)
    outputs = execute_program(program, inputs, bridge=bridge)
    pairs = [
        {"input": deepcopy(grid), "output": deepcopy(output)}
        for grid, output in zip(inputs, outputs, strict=True)
    ]
    demos = pairs[:3]
    identifiability = _check_identifiability_with_bridge(demos, bridge)
    selected = parameters[PARAMETER_NAME]
    if identifiability["surviving_settings"] != [selected]:
        raise AssertionError(
            "episode demonstrations do not uniquely identify the selected setting: "
            f"selected={selected!r}, survivors="
            f"{identifiability['surviving_settings']!r}"
        )

    return {
        "schema": "arc-parametric-private-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameters": parameters,
        "parameter_spec": deepcopy(PARAMETER_SPEC),
        "input_generation": {
            "generator_seed": input_seed,
            "sample_indices": sample_indices,
            "difficulty": "medium",
        },
        "racket_program": program,
        "demos": demos,
        "query": pairs[3],
        "identifiability": identifiability,
    }


def make_episode(
    seed: int,
    bridge: RacketBridge | None = None,
    generator_bundle: Any = None,
) -> dict[str, Any]:
    """Build a reproducible 3-demo/1-query episode using one hidden rule."""
    if type(seed) is not int:
        raise TypeError("episode seed must be an integer (not bool, float, or string)")
    if bridge is not None:
        return _make_episode_with_bridge(seed, bridge, generator_bundle)
    with RacketBridge(timeout=20, max_calls_before_restart=48) as owned_bridge:
        return _make_episode_with_bridge(seed, owned_bridge, generator_bundle)
