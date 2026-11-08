from __future__ import annotations

import copy
import importlib.util
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

ROOT = find_root(__file__)
_SOURCE = ROOT / "generators/c690e739e0ce/generator.py"
_SPEC = importlib.util.spec_from_file_location("_c690e739_generator", _SOURCE)
assert _SPEC and _SPEC.loader
gen = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(gen)

TASK_ID = "c690e739e0ce"


def _canonical_pairs():
    pairs = []
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        for split in ("train", "test"):
            pairs.extend(row.get(split, []))
    return pairs


def test_canonical_inputs_and_outputs_match_horizontal_reflection():
    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_boundary_overrides_and_all_textures_are_deterministic_and_valid():
    cases = [
        dict(grid_h=3, grid_w=3, palette_size=2),
        dict(grid_h=20, grid_w=20, palette_size=6),
    ]
    for texture in gen.TEXTURES:
        for index, overrides in enumerate(cases):
            kwargs = dict(overrides, texture=texture)
            first = gen.generate(991, index, difficulty="hard", **kwargs)
            second = gen.generate(991, index, difficulty="hard", **kwargs)
            assert first == second
            assert first is not second
            assert gen.self_check(first, meta=kwargs) == []
            assert gen.observe_overrides(first) == {
                "grid_h": overrides["grid_h"],
                "grid_w": overrides["grid_w"],
                "palette_size": overrides["palette_size"],
            }


def test_generation_preserves_global_rng_and_returns_fresh_rows():
    random.seed(481516)
    before = random.getstate()
    first = gen.generate(77, 2, difficulty="medium")
    assert random.getstate() == before
    second = gen.generate(77, 2, difficulty="medium")
    assert first == second and first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert gen.generate(77, 2, difficulty="medium") == second


def test_validator_rejects_string_rows_boolean_cells_and_ragged_rows():
    valid = gen.generate(812, 0, difficulty="medium", grid_h=5, grid_w=7, palette_size=3)
    string_rows = ["".join(map(str, row)) for row in valid]
    assert gen.self_check(valid) == []
    assert any("literal row lists" in error for error in gen.self_check(string_rows))
    assert gen.self_check([[0, 1, 2], [3, True, 4], [5, 6, 7]])
    assert gen.self_check([[0, 1, 2], [3, 4], [5, 6, 7]])
    with pytest.raises(ValueError, match="literal row lists"):
        gen.rule_mirror(string_rows)


def test_lesson_identifiability_rejects_vertical_and_identity_rivals():
    demos = []
    for index in range(2):
        grid = gen.generate(330, index, difficulty="medium")
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(330, 9, difficulty="hard")
    assert gen.lesson_identifiable(demos, {"input": query_grid}) == []

    identity = copy.deepcopy(demos)
    identity[0]["output"] = copy.deepcopy(identity[0]["input"])
    assert gen.lesson_identifiable(identity, {"input": query_grid})
