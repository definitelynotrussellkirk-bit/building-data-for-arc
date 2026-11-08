"""Task-local rotation prototype for ``49754d8fa42e``.

The selected production generator and canonical Racket authority stay fixed.
This proposed extension chooses one number of clockwise quarter-turns for an
entire episode, then rotates the glyph selected by the original nonzero-mode
classification rule.  Zero turns is the exact canonical behavior.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

PARAMETER_NAME = "quarter_turns_clockwise"
ALLOWED_SETTINGS = (0, 1, 2, 3)
DEFAULT_SETTING = 0
PROTOTYPE_VERSION = "1.0.0"
_UNSET = object()

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
GENERATOR_PATH = HERE.parents[1] / "generator.py"
CANONICAL_PATH = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
TASK_ID = "49754d8fa42e"

_BASE_GLYPHS = {
    1: [[0, 5, 0], [5, 5, 5], [0, 5, 0]],
    2: [[5, 5, 5], [0, 5, 0], [0, 5, 0]],
    3: [[0, 0, 5], [0, 0, 5], [5, 5, 5]],
}


def _load_production_generator():
    name = "generator_49754d8fa42e_parametric_source"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load production generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_PRODUCTION = _load_production_generator()


def _validate_seed(seed: int) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, string, or None)")


def _validate_setting(setting: int) -> None:
    if type(setting) is not int:
        raise TypeError(f"{PARAMETER_NAME} must be a literal integer")
    if setting not in ALLOWED_SETTINGS:
        raise ValueError(f"{PARAMETER_NAME} must be one of {ALLOWED_SETTINGS}, got {setting!r}")


def choose_setting(seed: int) -> int:
    """Choose one hidden rule value deterministically for the whole episode."""
    _validate_seed(seed)
    digest = hashlib.sha256(f"49754d8fa42e:glyph-rotation:{seed}".encode()).digest()
    return ALLOWED_SETTINGS[digest[0] % len(ALLOWED_SETTINGS)]


def _rotate_clockwise(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def rotated_glyph(color: int, turns: int) -> list[list[int]]:
    _validate_setting(turns)
    glyph = [row[:] for row in _BASE_GLYPHS.get(color, [[0] * 3 for _ in range(3)])]
    for _ in range(turns):
        glyph = _rotate_clockwise(glyph)
    return glyph


def mode_color(grid: list[list[int]]) -> int:
    """Return the unique nonzero mode on the production prototype domain."""
    errors = _PRODUCTION.self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    counts = Counter(value for row in grid for value in row if value != 0)
    return max(counts, key=counts.__getitem__)


def apply_python(grid: list[list[int]], turns: int) -> list[list[int]]:
    """Python authoring mirror; retained labels are checked with Racket."""
    return rotated_glyph(mode_color(grid), turns)


def _canonical_program() -> str:
    found = []
    for line in CANONICAL_PATH.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record.get("task_id") == TASK_ID:
            found.append(record["program_solution"])
    if len(found) != 1:
        raise RuntimeError(f"expected one canonical program for {TASK_ID}, found {len(found)}")
    return found[0]


def _racket_grid(grid: list[list[int]]) -> str:
    rows = " ".join("(list " + " ".join(map(str, row)) + ")" for row in grid)
    return f"(list {rows})"


def program_for(turns: int) -> str:
    """Return a complete exact Racket rule for one rotation setting."""
    _validate_setting(turns)
    if turns == DEFAULT_SETTING:
        return _canonical_program()
    glyphs = {color: rotated_glyph(color, turns) for color in (1, 2, 3)}
    return "\n".join(
        [
            "(rule! (lambda (g)",
            "         (let* ((h (rows g))",
            "                (w (cols g)))",
            "           (let ((color (mode g 0)))",
            "             (cond",
            f"               ((= color 1) {_racket_grid(glyphs[1])})",
            f"               ((= color 2) {_racket_grid(glyphs[2])})",
            f"               ((= color 3) {_racket_grid(glyphs[3])})",
            "               (else (list (list 0 0 0) (list 0 0 0) (list 0 0 0))))))))",
        ]
    )


def _input_for(seed: int, sample_index: int) -> list[list[int]]:
    difficulties = (None, "easy", "medium", "hard")
    return _PRODUCTION.generate(
        seed,
        sample_index,
        difficulty=difficulties[sample_index % len(difficulties)],
    )


def _episode_indices(seed: int) -> tuple[list[int], list[int]]:
    demo_indices = list(range(5))
    query_by_color: dict[int, int] = {}
    for index in range(5, 14):
        color = mode_color(_input_for(seed, index))
        if color in (2, 3) and color not in query_by_color:
            query_by_color[color] = index
        if len(query_by_color) == 2:
            break
    if set(query_by_color) != {2, 3}:
        raise RuntimeError("could not find rotation-sensitive query classes")
    return demo_indices, [query_by_color[2], query_by_color[3]]


def build_episode(seed: int, *, setting: object = _UNSET) -> dict[str, Any]:
    """Build five demonstrations and two queries under one fixed hidden rule."""
    _validate_seed(seed)
    selected = choose_setting(seed) if setting is _UNSET else setting
    _validate_setting(selected)
    demo_indices, query_indices = _episode_indices(seed)
    indices = demo_indices + query_indices
    inputs = [_input_for(seed, index) for index in indices]
    pairs = [
        {"input": grid, "output": apply_python(grid, selected)}
        for grid in inputs
    ]
    program = program_for(selected)
    return {
        "train": pairs[: len(demo_indices)],
        "test": pairs[len(demo_indices) :],
        "program": program,
        "meta": {
            "seed": seed,
            PARAMETER_NAME: selected,
            "demo_indices": demo_indices,
            "query_indices": query_indices,
            "prototype_version": PROTOTYPE_VERSION,
            "production_generator_version": _PRODUCTION.VERSION,
            "production_generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
            "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Remove the hidden rule value, program, and query answers."""
    return {
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["train"]
        ],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    }
