"""Native adapter for the reviewed, episode-fixed special-period family.

The Python outputs are authoring claims. Native qualification and generation
independently execute the returned exact Racket program for every label.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent


def _load_adjacent(name: str, path: Path) -> Any:
    """Resolve this task's sources without a cached bare ``prototype`` import."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load task-local source: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROTOTYPE = _load_adjacent(
    "_443eebb271d9_native_prototype", HERE / "prototype.py"
)
GENERATOR = _load_adjacent(
    "_443eebb271d9_native_generator", HERE.parents[1] / "generator.py"
)


def program(settings: dict[str, Any]) -> str:
    period = PROTOTYPE.validate_native_settings(settings)
    if period == PROTOTYPE.DEFAULT_SPECIAL_PERIOD:
        # Exact canonical bytes, including its rule! wrapper and whitespace.
        return (HERE / "canonical.rkt").read_text(encoding="utf-8")
    # The native worker owns normalization and expects the same rule! contract
    # as canonical programs; the legacy prototype intentionally returns a lambda.
    return "(rule! " + PROTOTYPE.racket_program(settings) + ")"


def generate(
    seed: int, settings: dict[str, Any], demos: int, queries: int
) -> dict[str, Any]:
    period = PROTOTYPE.validate_native_settings(settings)
    train_inputs, test_inputs = PROTOTYPE.native_inputs(
        GENERATOR, seed, demos, queries
    )

    def labeled(grid: list[list[int]]) -> dict[str, list[list[int]]]:
        return {
            "input": grid,
            "output": PROTOTYPE.python_reference(grid, special_period=period),
        }

    return {
        "train": [labeled(grid) for grid in train_inputs],
        "test": [labeled(grid) for grid in test_inputs],
        "program_solution": program(settings),
    }
