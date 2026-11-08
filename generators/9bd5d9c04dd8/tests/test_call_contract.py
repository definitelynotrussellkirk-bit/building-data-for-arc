"""Call-level request contract regressions for 9bd5d9c04dd8."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest


TASK_HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", TASK_HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location("reviewed_9bd5d9c04dd8_call_contract", SOURCE)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"cannot load generator from {SOURCE}")
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1", -1])
def test_invalid_seed_scalars_fail_loudly(seed):
    with pytest.raises(ValueError):
        gen.generate(seed, 0, difficulty="easy")


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75, "1", -1])
def test_invalid_sample_index_scalars_fail_loudly(sample_index):
    with pytest.raises(ValueError):
        gen.generate(991, sample_index, difficulty="easy")


@pytest.mark.parametrize("difficulty", [True, False, 0, 1.0, "__invalid_difficulty__"])
def test_invalid_difficulty_scalars_fail_loudly(difficulty):
    with pytest.raises(ValueError):
        gen.generate(991, 0, difficulty=difficulty)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_valid_call_scalars_remain_supported(difficulty):
    grid = gen.generate(991, 0, difficulty=difficulty)
    assert gen.self_check(grid) == []
