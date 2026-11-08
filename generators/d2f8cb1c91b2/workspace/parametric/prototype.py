"""Episode-fixed conflict policies for d2f8cb1c91b2.

All settings infer the demonstrated D4 transform, apply it to panel X, and
merge with panel Y.  They differ only when both transformed-X and Y are
nonzero and unequal: emit marker 9, keep X, or keep Y.  The source generator
constructs at least one such conflict in every 3x15 input, so labels identify
the setting without changing the input distribution.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
from typing import Any, Iterable

TASK_ID = "d2f8cb1c91b2"
SETTINGS = (
    {"conflict_mode": "marker"},
    {"conflict_mode": "keep_x"},
    {"conflict_mode": "keep_y"},
)
DEFAULT = {"conflict_mode": "marker"}
MODES = tuple(setting["conflict_mode"] for setting in SETTINGS)

CANONICAL_PROGRAM = "(rule! (let ((dummy 0)) (define (split-panels-row grid count) (let* ((panel-w (quotient (- (cols grid) (- count 1)) count))) (for/list ((i (in-range count))) (let ((left (* i (+ panel-w 1)))) (subgrid grid 0 left (- (rows grid) 1) (+ left panel-w -1)))))) (define transform-names (list 'id 'rot90 'rot180 'rot270 'flip-h 'flip-v 'transpose 'anti-transpose)) (define (anti-transpose-grid grid) (rotate-180 (transpose grid))) (define (apply-transform-name name grid) (cond ((equal? name 'id) grid) ((equal? name 'rot90) (rotate-cw grid)) ((equal? name 'rot180) (rotate-180 grid)) ((equal? name 'rot270) (rotate-ccw grid)) ((equal? name 'flip-h) (flip-lr grid)) ((equal? name 'flip-v) (flip-ud grid)) ((equal? name 'transpose) (transpose grid)) (else (anti-transpose-grid grid)))) (define (infer-transform-name a b) (first (filter (lambda (name) (equal? (apply-transform-name name a) b)) transform-names))) (let* ((panels (split-panels-row g 4)) (name (infer-transform-name (first panels) (second panels))) (x (third panels)) (y (fourth panels)) (tx (apply-transform-name name x))) (grid-from-fn (rows tx) (cols tx) (lambda (r c) (let ((a (at tx r c)) (b (at y r c))) (cond ((and (= a 0) (= b 0)) 0) ((= a 0) b) ((= b 0) a) ((= a b) a) (else 9))))))))"
KEEP_X_PROGRAM = CANONICAL_PROGRAM.replace("(else 9)", "(else a)")
KEEP_Y_PROGRAM = CANONICAL_PROGRAM.replace("(else 9)", "(else b)")

_GENERATOR_PATH = Path(__file__).resolve().parents[2] / "generator.py"
_SPEC = importlib.util.spec_from_file_location("_task_d2f8cb1c91b2_generator", _GENERATOR_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load source generator from {_GENERATOR_PATH}")
GENERATOR = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(GENERATOR)


def _integer(value: Any, lo: int, hi: int, name: str) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")
    return value


def _settings(value: Any) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"conflict_mode"}:
        raise ValueError("settings must contain exactly conflict_mode")
    mode = value["conflict_mode"]
    if type(mode) is not str:
        raise TypeError("conflict_mode must be a string")
    if mode not in MODES:
        raise ValueError(f"conflict_mode must be one of {MODES}")
    return {"conflict_mode": mode}


def program(settings: Any) -> str:
    mode = _settings(settings)["conflict_mode"]
    return {
        "marker": CANONICAL_PROGRAM,
        "keep_x": KEEP_X_PROGRAM,
        "keep_y": KEEP_Y_PROGRAM,
    }[mode]


def transform(grid: Any, settings: Any) -> list[list[int]]:
    mode = _settings(settings)["conflict_mode"]
    errors, analysis = GENERATOR._analyze_grid(grid)
    if errors or analysis is None:
        raise ValueError("outside selected rule domain: " + "; ".join(errors))
    return GENERATOR._merge_layers(
        analysis["transformed_x"], analysis["panels"][3], conflict=mode
    )


def _source_grid(seed: int, role: str, index: int) -> list[list[int]]:
    if role not in {"demo", "query"}:
        raise ValueError("role must be demo or query")
    # Separate index ranges make query construction independent of demo count.
    sample_index = index if role == "demo" else 1000 + index
    source_seed = seed * 1_000_003 + (17 if role == "demo" else 53)
    difficulty = ("easy", "medium", "hard", None)[index % 4]
    grid = GENERATOR.generate(source_seed, sample_index, difficulty=difficulty)
    if GENERATOR.self_check(grid):
        raise RuntimeError("source generator emitted an invalid conflict-mode input")
    return grid


def _pair(grid: list[list[int]], settings: dict[str, str]) -> dict[str, Any]:
    return {"input": deepcopy(grid), "output": transform(grid, settings)}


def fit_settings(demos: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    pairs = list(demos)
    survivors: list[dict[str, str]] = []
    for candidate in SETTINGS:
        try:
            if all(
                isinstance(pair, dict)
                and pair.get("output") == transform(pair.get("input"), candidate)
                for pair in pairs
            ):
                survivors.append(dict(candidate))
        except (TypeError, ValueError):
            continue
    return survivors


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 8, "queries")
    chosen = _settings(settings)

    train = [_pair(_source_grid(seed, "demo", index), chosen) for index in range(demos)]
    test = [_pair(_source_grid(seed, "query", index), chosen) for index in range(queries)]
    if fit_settings(train) != [chosen]:
        raise RuntimeError("demonstrations do not uniquely identify conflict_mode")
    serial = [repr(pair["input"]) for pair in train + test]
    if len(serial) != len(set(serial)):
        raise RuntimeError("episode contains duplicate inputs")
    return {
        "train": train,
        "test": test,
        "settings": chosen,
        "seed": seed,
        "program_solution": program(chosen),
        "certificate": {
            "finite_rivals": [dict(setting) for setting in SETTINGS],
            "survivors": fit_settings(train),
            "racket_checked": False,
            "fixed_input_shape": [3, 15],
        },
    }
