from __future__ import annotations

import copy
import importlib.util
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "c53c24435976"
ROOT = find_root(__file__)
GENERATOR = Path(__file__).resolve().parents[1] / "generator.py"


def _load():
    spec = importlib.util.spec_from_file_location("c53c24435976_generator_under_test", GENERATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load()


def test_code_override_is_honored_for_all_four_commands():
    for code in (1, 2, 3, 4):
        grid = gen.generate(0, 0, difficulty="medium", code=code)
        assert grid[0][0] == code
        assert gen.self_check(grid) == []


def test_unknown_override_is_rejected_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, difficulty="easy", misspelled_axis=3)


def test_canonical_inputs_remain_in_domain():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(copy.deepcopy(pair["input"])) == []


def test_generated_selected_transform_is_observable_across_bands():
    for difficulty in (None, "easy", "medium", "hard"):
        for code in (1, 2, 3, 4):
            for index in range(8):
                grid = gen.generate(1700 + code, index, difficulty=difficulty, code=code)
                cells = gen._shape_cells(grid)
                assert gen._selected_transform_changes(cells, code)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20261026)
    before = random.getstate()
    first = gen.generate(31, 7, difficulty="hard", code=2)
    middle = random.getstate()
    second = gen.generate(31, 7, difficulty="hard", code=2)
    after = random.getstate()
    assert before == middle == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
