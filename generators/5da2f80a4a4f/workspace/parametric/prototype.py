"""Task-local parametric prototype for the frame/key enlargement family.

This does not alter the production generator or canonical rule.  One hidden
``key_transform`` value is chosen for an entire episode:

* ``identity`` (canonical/default): enlarge the extracted key unchanged.
* ``transpose``: transpose the extracted key, then enlarge it to the same frame.

The shared input grammar is deliberately restricted to a 14x14 frame interior
and a dense 2x3 asymmetric key.  A 12x12 interior is divisible by both 2x3 and
its 3x2 transpose, so the same lawful input supports both settings.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import random
from pathlib import Path
from typing import Any, Iterable


TASK_ID = "5da2f80a4a4f"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER_NAME = "key_transform"
PARAMETER_VALUES = ("identity", "transpose")
DEFAULT_PARAMETER = "identity"
FRAME_SIZE = (14, 14)
KEY_SIZE = (2, 3)
CANVAS_SIZE = (18, 18)
HERE = Path(__file__).resolve().parent


_CANONICAL_MODULE = None


def _canonical_generator():
    """Load the adjacent production generator without relying on staging.

    ``arcpuzzles check`` installs a temporary ``per_puzzle`` import path, but
    this prototype is also meant to run directly from the review packet.  A
    file-based import keeps that standalone path honest while preserving the
    generator's ordinary ``puzzle_generators`` dependencies.
    """
    global _CANONICAL_MODULE
    if _CANONICAL_MODULE is not None:
        return _CANONICAL_MODULE
    generator_path = HERE.parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location(
        f"_task_local_{TASK_ID}_generator", generator_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load adjacent generator at {generator_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _CANONICAL_MODULE = module
    return module


def _validate_seed(seed: Any) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, or string)")


def _validate_parameter(value: Any) -> str:
    if type(value) is not str:
        raise TypeError(f"{PARAMETER_NAME} must be a string")
    if value not in PARAMETER_VALUES:
        raise ValueError(
            f"unknown {PARAMETER_NAME}={value!r}; expected one of {PARAMETER_VALUES}"
        )
    return value


def _rng(seed: int, label: str) -> random.Random:
    payload = f"{TASK_ID}|parametric|{PROTOTYPE_VERSION}|{seed}|{label}".encode()
    keyed_seed = int.from_bytes(hashlib.sha256(payload).digest()[:16], "big")
    return random.Random(keyed_seed)


def _key_pattern(seed: int, pair_index: int) -> list[list[int]]:
    rng = _rng(seed, f"key:{pair_index}")
    a, b, c = rng.sample([1, 3, 4, 5, 6, 7, 8, 9], 3)
    # Every row and column carries information, and the 2x3 matrix is not equal
    # to any accidental square/quadrant summary after enlargement.
    candidates = (
        [[a, b, c], [c, a, b]],
        [[a, c, b], [b, a, c]],
        [[b, a, c], [c, b, a]],
    )
    return deepcopy(candidates[pair_index % len(candidates)])


def build_input(seed: int, pair_index: int) -> list[list[int]]:
    """Build one input lawful under the canonical generator's validator."""
    _validate_seed(seed)
    if type(pair_index) is not int:
        raise TypeError("pair_index must be an integer")
    if pair_index < 0:
        raise ValueError("pair_index must be nonnegative")

    canvas_h, canvas_w = CANVAS_SIZE
    frame_h, frame_w = FRAME_SIZE
    key_h, key_w = KEY_SIZE
    rng = _rng(seed, f"layout:{pair_index}")
    frame_r0 = rng.randint(0, canvas_h - frame_h)
    frame_c0 = rng.randint(0, canvas_w - frame_w)
    key_offset_r = rng.randint(0, frame_h - 2 - key_h)
    key_offset_c = rng.randint(0, frame_w - 2 - key_w)

    grid = [[0] * canvas_w for _ in range(canvas_h)]
    for r in range(frame_h):
        for c in range(frame_w):
            if r in (0, frame_h - 1) or c in (0, frame_w - 1):
                grid[frame_r0 + r][frame_c0 + c] = 2

    key = _key_pattern(seed, pair_index)
    key_r0 = frame_r0 + 1 + key_offset_r
    key_c0 = frame_c0 + 1 + key_offset_c
    for r, row in enumerate(key):
        for c, value in enumerate(row):
            grid[key_r0 + r][key_c0 + c] = value

    findings = _canonical_generator().self_check(grid)
    if findings:
        raise AssertionError(f"prototype built an invalid input: {findings}")
    return grid


def _transformed_key(grid: list[list[int]], key_transform: str) -> tuple[dict[str, Any], list[list[int]]]:
    key_transform = _validate_parameter(key_transform)
    analysis = _canonical_generator()._analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid canonical-family input: " + "; ".join(analysis["errors"]))
    key = [list(row) for row in analysis["key_matrix"]]
    if key_transform == "transpose":
        key = [list(row) for row in zip(*key)]
    return analysis, key


def apply_rule(grid: list[list[int]], key_transform: str) -> list[list[int]]:
    """Python mirror for the bounded prototype; Racket remains probe authority."""
    analysis, key = _transformed_key(grid, key_transform)
    out_h, out_w = analysis["frame_h"], analysis["frame_w"]
    interior_h, interior_w = out_h - 2, out_w - 2
    key_h, key_w = len(key), len(key[0])
    if interior_h % key_h or interior_w % key_w:
        raise ValueError(
            f"transformed key {key_h}x{key_w} does not tile "
            f"interior {interior_h}x{interior_w}"
        )
    row_scale = interior_h // key_h
    col_scale = interior_w // key_w
    return [
        [
            2
            if r in (0, out_h - 1) or c in (0, out_w - 1)
            else key[(r - 1) // row_scale][(c - 1) // col_scale]
            for c in range(out_w)
        ]
        for r in range(out_h)
    ]


def racket_program(key_transform: str) -> str:
    """Materialize the exact Racket rule for one episode parameter value."""
    key_transform = _validate_parameter(key_transform)
    if key_transform == "identity":
        out_key_h = "kh"
        out_key_w = "kw"
        source_row = "(+ kr0 (quotient (- r 1) rscale))"
        source_col = "(+ kc0 (quotient (- c 1) cscale))"
    else:
        out_key_h = "kw"
        out_key_w = "kh"
        source_row = "(+ kr0 (quotient (- c 1) cscale))"
        source_col = "(+ kc0 (quotient (- r 1) rscale))"

    return f"""(rule! (lambda (g)
  (define bb (bbox-of-cells (find-color g 2)))
  (define r0 (first bb))
  (define c0 (second bb))
  (define r1 (third bb))
  (define c1 (fourth bb))
  (define oh (+ 1 (- r1 r0)))
  (define ow (+ 1 (- c1 c0)))
  (define interior
    (for*/list ([r (in-range (+ r0 1) r1)]
                [c (in-range (+ c0 1) c1)])
      (list r c)))
  (define key-cells
    (filter (lambda (p)
      (let ((v (at g (first p) (second p))))
        (and (not (= v 0)) (not (= v 2)))))
      interior))
  (define kbb (bbox-of-cells key-cells))
  (define kr0 (first kbb))
  (define kc0 (second kbb))
  (define kr1 (third kbb))
  (define kc1 (fourth kbb))
  (define kh (+ 1 (- kr1 kr0)))
  (define kw (+ 1 (- kc1 kc0)))
  (define out-kh {out_key_h})
  (define out-kw {out_key_w})
  (define rscale (quotient (- oh 2) out-kh))
  (define cscale (quotient (- ow 2) out-kw))
  (grid-from-fn oh ow
    (lambda (r c)
      (if (or (= r 0) (= c 0) (= r (- oh 1)) (= c (- ow 1)))
          2
          (at g {source_row} {source_col}))))))"""


def surviving_parameter_values(demos: Iterable[dict[str, Any]]) -> list[str]:
    """Return settings whose Python mirrors fit every labelled demonstration."""
    materialized = list(demos)
    survivors: list[str] = []
    for value in PARAMETER_VALUES:
        if all(
            isinstance(pair, dict)
            and "input" in pair
            and "output" in pair
            and apply_rule(pair["input"], value) == pair["output"]
            for pair in materialized
        ):
            survivors.append(value)
    return survivors


def generate_episode(
    seed: int,
    *,
    key_transform: str | None = None,
    n_train: int = 3,
    n_test: int = 1,
) -> dict[str, Any]:
    """Generate one complete, internally labelled prototype episode."""
    _validate_seed(seed)
    if key_transform is None:
        key_transform = _rng(seed, "episode-parameter").choice(PARAMETER_VALUES)
    key_transform = _validate_parameter(key_transform)
    if type(n_train) is not int or type(n_test) is not int:
        raise TypeError("n_train and n_test must be integers")
    if n_train < 1 or n_test < 1:
        raise ValueError("episodes require at least one train and one test pair")

    pairs = []
    for pair_index in range(n_train + n_test):
        grid = build_input(seed, pair_index)
        pairs.append({"input": grid, "output": apply_rule(grid, key_transform)})

    episode = {
        "schema": "arcpuzzles-task-parametric-prototype-v1",
        "task_id": TASK_ID,
        "version": PROTOTYPE_VERSION,
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": racket_program(key_transform),
        "meta": {
            "seed": seed,
            PARAMETER_NAME: key_transform,
            "parameter_values": list(PARAMETER_VALUES),
            "canonical_default": key_transform == DEFAULT_PARAMETER,
            "input_constraints": {
                "frame_size": list(FRAME_SIZE),
                "key_size": list(KEY_SIZE),
                "canvas_size": list(CANVAS_SIZE),
                "reason": "12x12 interior is divisible by 2x3 and its 3x2 transpose",
            },
        },
    }
    survivors = surviving_parameter_values(episode["train"])
    if survivors != [key_transform]:
        raise AssertionError(
            f"demonstrations do not identify {key_transform!r}: survivors={survivors}"
        )
    return episode


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Remove the hidden parameter, Racket source, and query answers."""
    return {
        "schema": "arcpuzzles-public-parametric-prototype-v1",
        "task_id": TASK_ID,
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
        "meta": {
            "version": episode["version"],
            "parameter_name_hidden": True,
        },
    }
