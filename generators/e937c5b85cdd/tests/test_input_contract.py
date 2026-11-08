"""Call-level scalar validation regressions for e937c5b85cdd."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from reviewer_support import find_root

TASK_ID = "e937c5b85cdd"
ROOT = find_root(__file__)
SOURCE = next(
    path
    for path in (
        ROOT / "generators" / TASK_ID / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    )
    if path.is_file()
)


def _load_generator():
    spec = importlib.util.spec_from_file_location("strict_scalar_generator", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


@pytest.mark.parametrize("seed", [True, False, 1.5, "1", None])
def test_seed_rejects_non_integer_scalars(seed):
    with pytest.raises(ValueError, match="seed"):
        GEN.generate(seed, 0, difficulty="easy")


@pytest.mark.parametrize("sample_index", [True, False, -1, 1.5, "0", None])
def test_sample_index_rejects_invalid_scalars(sample_index):
    with pytest.raises(ValueError, match="sample_index"):
        GEN.generate(1, sample_index, difficulty="medium")


@pytest.mark.parametrize(
    "difficulty",
    [True, False, 0, 1.0, "__invalid_difficulty__", "EASY", ""],
)
def test_difficulty_rejects_unknown_or_non_string_values(difficulty):
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty=difficulty)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_valid_call_scalars_remain_supported(difficulty):
    grid = GEN.generate(17, 3, difficulty=difficulty)
    assert GEN.self_check(grid) == []
