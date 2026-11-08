"""Regression tests for strict public scalar-call controls."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest


TASK_DIR = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(
    os.environ.get("GENERATOR_UNDER_TEST", TASK_DIR / "generator.py")
).resolve()


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "reviewed_0a9926d504f3_scalar_controls", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator at {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


@pytest.mark.parametrize(
    ("seed", "sample_index", "difficulty"),
    [
        (True, 0, None),
        (False, 0, None),
        (1.0, 0, None),
        (1.75, 0, None),
        ("1", 0, None),
        (1, True, None),
        (1, False, None),
        (1, 1.0, None),
        (1, 1.75, None),
        (1, "1", None),
        (1, -1, None),
        (1, 0, True),
        (1, 0, False),
        (1, 0, 0),
        (1, 0, 1.0),
        (1, 0, "__invalid_difficulty__"),
    ],
)
def test_generate_rejects_malformed_scalar_controls(seed, sample_index, difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index, difficulty=difficulty)
