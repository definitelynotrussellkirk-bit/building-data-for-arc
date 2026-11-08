"""Task-local proposed rule-parameter prototype for ``9ce2dcf587b8``.

The hidden episode parameter ``diagonal_axes`` is selected once and shared by
all demonstrations and queries:

``both``
    Canonical/default behavior: each marker emits along both diagonal axes
    (all four diagonal directions).
``main_only``
    Proposed nearby behavior: each marker emits only along the NW-SE axis.

Marker roles, source preservation, same-color painting, ray extent, collision
handling, and the input family remain unchanged.  This module is authoring
support only; it does not change the selected production Racket authority.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
from typing import Any, Sequence

HERE = Path(__file__).resolve().parent
TASK_ROOT = HERE.parents[1]

PARAMETER_NAME = "diagonal_axes"
ALLOWED_SETTINGS = ("both", "main_only")
DEFAULT_SETTING = "both"
PROTOTYPE_VERSION = "1.0.0"
CANONICAL_RULE_HASH = "e635bf3ddbe0"
_UNSET = object()
_DIRECTIONS = {
    "both": ((-1, -1), (-1, 1), (1, -1), (1, 1)),
    "main_only": ((-1, -1), (1, 1)),
}
_MAIN_ONLY_RACKET_DIRECTIONS = "'((-1 -1) (1 1))"
_EPISODE_RECIPES = (
    {"grid_h": 7, "grid_w": 7, "fgc": 1, "n_dots": 1},
    {"grid_h": 11, "grid_w": 13, "fgc": 4, "n_dots": 1},
    {"grid_h": 15, "grid_w": 15, "fgc": 7, "n_dots": 1},
    {"grid_h": 17, "grid_w": 9, "fgc": 9, "n_dots": 1},
)


def _validate_seed(seed: int) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, string, or None)")


def _validate_setting(setting: Any) -> None:
    if type(setting) is not str:
        raise TypeError(f"{PARAMETER_NAME} must be a string")
    if setting not in ALLOWED_SETTINGS:
        raise ValueError(
            f"{PARAMETER_NAME} must be one of {ALLOWED_SETTINGS}, got {setting!r}"
        )


def choose_setting(seed: int) -> str:
    """Choose one deterministic hidden setting for the complete episode."""
    _validate_seed(seed)
    digest = hashlib.sha256(f"9ce2dcf587b8|{PARAMETER_NAME}|{seed}".encode()).digest()
    return ALLOWED_SETTINGS[digest[0] % len(ALLOWED_SETTINGS)]


def _canonical_program() -> str:
    # Exact selected source copied through Catalog; native qualification binds it.
    return (HERE / "canonical.rkt").read_text()


def program_for(setting: str) -> str:
    """Materialize exact Racket for one bounded parameter setting."""
    _validate_setting(setting)
    canonical = _canonical_program()
    if setting == "both":
        return canonical
    if canonical.count("diagonal-deltas") != 1:
        raise ValueError("canonical program no longer has one direction-list site")
    return canonical.replace(
        "diagonal-deltas",
        _MAIN_ONLY_RACKET_DIRECTIONS,
        1,
    )


def apply_python(grid: Sequence[Sequence[int]], setting: str) -> list[list[int]]:
    """Independent Python mirror used only for authoring checks."""
    _validate_setting(setting)
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty rectangular grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected nonempty rows")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")

    source = [list(row) for row in grid]
    output = [list(row) for row in grid]
    height = len(source)
    markers = [
        (row, col, value)
        for row, values in enumerate(source)
        for col, value in enumerate(values)
        if value != 0
    ]
    for row, col, color in markers:
        for dr, dc in _DIRECTIONS[setting]:
            for distance in range(1, max(height, width)):
                rr = row + dr * distance
                cc = col + dc * distance
                if (
                    0 <= rr < height
                    and 0 <= cc < width
                    and source[rr][cc] == 0
                    and output[rr][cc] == 0
                ):
                    output[rr][cc] = color
    return output


def _load_generator():
    path = TASK_ROOT / "generator.py"
    spec = importlib.util.spec_from_file_location("generator_9ce2dcf587b8_parametric", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _episode_input(generator, seed: int, pair_index: int) -> list[list[int]]:
    overrides = dict(_EPISODE_RECIPES[pair_index])
    return generator.generate(
        seed=seed * 1009 + pair_index * 37 + 11,
        sample_index=seed % 97 + pair_index * 11,
        difficulty=("easy", "medium", "hard", "medium")[pair_index],
        **overrides,
    )


def build_episode(seed: int, *, setting: object = _UNSET) -> dict[str, Any]:
    """Materialize three demonstrations and one query under one fixed rule."""
    _validate_seed(seed)
    selected = choose_setting(seed) if setting is _UNSET else setting
    _validate_setting(selected)
    generator = _load_generator()
    inputs = [_episode_input(generator, seed, index) for index in range(4)]
    pairs = [
        {"input": grid, "output": apply_python(grid, selected)}
        for grid in inputs
    ]
    program = program_for(selected)
    return {
        "train": pairs[:3],
        "test": pairs[3:],
        "program": program,
        "meta": {
            "seed": seed,
            PARAMETER_NAME: selected,
            "allowed_settings": list(ALLOWED_SETTINGS),
            "default_setting": DEFAULT_SETTING,
            "prototype_version": PROTOTYPE_VERSION,
            "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return an opaque challenge with no hidden rule metadata or query label."""
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [
            {"input": deepcopy(pair["input"])}
            for pair in episode["test"]
        ],
    }
