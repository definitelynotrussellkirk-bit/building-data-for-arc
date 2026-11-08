"""Proposed episode-level arm-color rotation for ARC task ``08f1d9bdd2ef``.

The canonical/default setting is rotation 0.  The four arm colors, read
clockwise as top, right, bottom, left, are rotated as one assignment while the
input grammar, cyan dividers, black corners, and magenta center remain fixed.
This module is task-local authoring evidence only; it is not a production API
or an approved variant.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from typing import Any

from reviewer_support import find_root, load_selected_generator


TASK_ID = "08f1d9bdd2ef"
PROTOTYPE_STATUS = "proposed_unapproved"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER_NAME = "arm_rotation"
SETTINGS = (0, 1, 2, 3)
DEFAULT_SETTING = 0
_CANONICAL_ARM_COLORS = (2, 3, 1, 4)  # top, right, bottom, left
_UNSET = object()

_ROOT = find_root(__file__)
_GENERATOR, _GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator(
    TASK_ID, root=_ROOT
)

_CANONICAL_RACKET = """(rule!
  (lambda (g)
    (let* ((h (rows g))
           (w (cols g))
           (sep-rows (filter (lambda (r) (= (row-count g r 8) w)) (range 0 h)))
           (sep-cols (filter (lambda (c) (= (col-count g c 8) h)) (range 0 w)))
           (r0 (first sep-rows))
           (r1 (second sep-rows))
           (c0 (first sep-cols))
           (c1 (second sep-cols)))
      (define (band x a b)
        (cond ((< x a) 0)
              ((< x b) 1)
              (else 2)))
      (cellmap g (r c v)
        (let ((br (band r r0 r1))
              (bc (band c c0 c1)))
          (cond ((= v 8) 8)
                ((and (= br 0) (= bc 1)) 2)
                ((and (= br 1) (= bc 0)) 4)
                ((and (= br 1) (= bc 1)) 6)
                ((and (= br 1) (= bc 2)) 3)
                ((and (= br 2) (= bc 1)) 1)
                (else 0)))))))"""


def _validate_setting(setting: int) -> None:
    if type(setting) is not int:
        raise TypeError(f"{PARAMETER_NAME} must be an integer")
    if setting not in SETTINGS:
        raise ValueError(f"{PARAMETER_NAME} must be one of {SETTINGS}, got {setting!r}")


def _validate_seed(seed: int) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer")


def choose_setting(seed: int) -> int:
    """Choose one deterministic setting for an entire episode."""
    _validate_seed(seed)
    digest = hashlib.sha256(f"08f1-arm-rotation:v1:{seed}".encode()).digest()
    return SETTINGS[digest[0] % len(SETTINGS)]


def arm_colors(setting: int) -> tuple[int, int, int, int]:
    """Return top/right/bottom/left colors for ``setting`` clockwise turns."""
    _validate_setting(setting)
    return tuple(
        _CANONICAL_ARM_COLORS[(index - setting) % len(_CANONICAL_ARM_COLORS)]
        for index in range(len(_CANONICAL_ARM_COLORS))
    )


def apply_python(grid: list[list[int]], setting: int) -> list[list[int]]:
    """Apply the proposed rule with an independent, simultaneous recoloring."""
    _validate_setting(setting)
    canonical = _GENERATOR.rule_mirror(grid)
    rotated = arm_colors(setting)
    translation = dict(zip(_CANONICAL_ARM_COLORS, rotated))
    return [
        [translation.get(value, value) for value in row]
        for row in canonical
    ]


def _program_with_colors(colors: tuple[int, int, int, int]) -> str:
    top, right, bottom, left = colors
    return f"""(rule!
  (lambda (g)
    (let* ((h (rows g))
           (w (cols g))
           (sep-rows (filter (lambda (r) (= (row-count g r 8) w)) (range 0 h)))
           (sep-cols (filter (lambda (c) (= (col-count g c 8) h)) (range 0 w)))
           (r0 (first sep-rows))
           (r1 (second sep-rows))
           (c0 (first sep-cols))
           (c1 (second sep-cols)))
      (define (band x a b)
        (cond ((< x a) 0)
              ((< x b) 1)
              (else 2)))
      (cellmap g (r c v)
        (let ((br (band r r0 r1))
              (bc (band c c0 c1)))
          (cond ((= v 8) 8)
                ((and (= br 0) (= bc 1)) {top})
                ((and (= br 1) (= bc 0)) {left})
                ((and (= br 1) (= bc 1)) 6)
                ((and (= br 1) (= bc 2)) {right})
                ((and (= br 2) (= bc 1)) {bottom})
                (else 0)))))))"""


def racket_program(setting: int) -> str:
    """Materialize exact Racket for one fixed setting."""
    _validate_setting(setting)
    if setting == DEFAULT_SETTING:
        return _CANONICAL_RACKET
    return _program_with_colors(arm_colors(setting))


def build_episode(
    seed: int,
    *,
    setting: object = _UNSET,
    difficulty: str = "medium",
) -> dict[str, Any]:
    """Materialize three demonstrations and one query under one setting."""
    _validate_seed(seed)
    selected = choose_setting(seed) if setting is _UNSET else setting
    _validate_setting(selected)
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, or hard")

    inputs = [
        _GENERATOR.generate(
            seed * 1_000_003 + index * 9_176,
            index,
            difficulty=difficulty,
        )
        for index in range(4)
    ]
    pairs = [
        {"input": grid, "output": apply_python(grid, selected)}
        for grid in inputs
    ]
    program = racket_program(selected)
    return {
        "schema": "08f1d9bdd2ef-arm-rotation-episode-v1",
        "prototype_status": PROTOTYPE_STATUS,
        "parameter": {PARAMETER_NAME: selected},
        "train": pairs[:3],
        "test": pairs[3:],
        "meta": {
            "seed": seed,
            "difficulty": difficulty,
            "allowed_settings": list(SETTINGS),
            "default_setting": DEFAULT_SETTING,
            "prototype_version": PROTOTYPE_VERSION,
            "generator_sha256": GENERATOR_SHA256,
            "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        },
    }


def episode_identifiability_errors(episode: dict[str, Any]) -> list[str]:
    """Check labels and whether demonstrations refute every other setting."""
    errors: list[str] = []
    try:
        selected = episode["parameter"][PARAMETER_NAME]
        _validate_setting(selected)
        train = list(episode["train"])
        test = list(episode["test"])
    except (KeyError, TypeError, ValueError) as exc:
        return [f"invalid episode contract: {exc}"]

    for index, pair in enumerate(train + test):
        try:
            expected = apply_python(pair["input"], selected)
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"pair {index} is invalid: {exc}")
            continue
        if pair.get("output") != expected:
            errors.append(f"pair {index} output disagrees with setting {selected}")

    for rival in SETTINGS:
        if rival == selected:
            continue
        if all(
            apply_python(pair["input"], rival) == pair.get("output")
            for pair in train
        ):
            errors.append(f"demonstrations fail to refute setting {rival}")
    return errors


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Strip the hidden setting, program metadata, and query answer."""
    return {
        "train": [
            {
                "input": deepcopy(pair["input"]),
                "output": deepcopy(pair["output"]),
            }
            for pair in episode["train"]
        ],
        "test": [
            {"input": deepcopy(pair["input"])}
            for pair in episode["test"]
        ],
    }
