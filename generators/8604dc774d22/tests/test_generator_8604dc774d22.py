from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators import base as generator_base

gen = importlib.import_module("puzzle_generators.per_puzzle.8604dc774d22.generator")


def _canonical_inputs():
    for line in Path("data/canonical/puzzles.jsonl").open(encoding="utf-8"):
        row = json.loads(line)
        if row.get("task_id") != gen.TASK_ID:
            continue
        test = row.get("test") or []
        if isinstance(test, dict):
            test = [test]
        return [pair["input"] for pair in row.get("train") or []] + [
            pair["input"] for pair in test
        ]
    raise AssertionError("canonical task missing")


def _pairs(start: int, difficulty: str):
    demos = []
    for offset in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(1000 + offset, start + offset, difficulty=difficulty)
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(2000, start + gen.EXAMPLES_NEEDED, difficulty=difficulty)
    return demos, {"input": query_grid, "output": gen.rule_mirror(query_grid)}


def test_rule_hash_and_semantic_contract_are_pinned():
    assert gen.RULE_HASH == "9ef73bd801f3"
    assert gen.strict_canonical_like
    assert gen.SEMANTIC_WITNESSES
    assert gen.lesson_identifiable


def test_all_canonical_inputs_are_accepted():
    for grid in _canonical_inputs():
        assert gen.self_check(grid) == []


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_schedule_is_lawful_and_identifiable(difficulty):
    for start in range(8):
        demos, query = _pairs(start, difficulty)
        assert gen.lesson_identifiable(demos, query) == []
        for pair in demos + [query]:
            assert gen.self_check(pair["input"]) == []


def test_every_exact_override_boundary_is_observable():
    cases = [
        {"grid_h": 8, "grid_w": 10, "n_l_trominoes": 1,
         "decor_shape": "singleton", "decor_color": 1},
        {"grid_h": 14, "grid_w": 16, "n_l_trominoes": 4,
         "decor_shape": "l_tromino", "decor_color": 9},
        {"grid_h": 8, "grid_w": 10, "n_l_trominoes": 4,
         "decor_shape": "tee", "decor_color": 4},
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(700 + index, index, difficulty="easy", **overrides)
        assert gen.observe_overrides(grid) == overrides
        assert gen.self_check(grid, meta={"overrides": overrides}) == []



def test_default_keyed_axes_match_returned_scene():
    for difficulty in ("easy", "medium", "hard"):
        for index in range(24):
            captured = []
            generator_base.set_ctx_observer(captured.append)
            try:
                grid = gen.generate(50_000 + index, index, difficulty=difficulty)
            finally:
                generator_base.set_ctx_observer(None)
            assert len(captured) == 1
            assert captured[0].recorded_draws() == gen.observe_overrides(grid)
            assert set(captured[0].recorded_draws()) == set(gen.AXES)

def test_unknown_override_rejects_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 1, not_an_axis=3)


def test_determinism_fresh_returns_and_global_rng_state():
    random.seed(123456)
    before = random.getstate()
    first = gen.generate(55, 7, difficulty="hard")
    middle = random.getstate()
    second = gen.generate(55, 7, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    assert before == middle == after
    first[0][0] = 8
    assert second[0][0] != 8


def test_self_check_rejects_targeted_impostors():
    valid = gen.generate(42, 1, difficulty="medium")
    h, w = len(valid), len(valid[0])
    impostors = {
        "all_background": [[0] * w for _ in range(h)],
        "singleton": [[3] + [0] * (w - 1)] + [[0] * w for _ in range(h - 1)],
        "solid_2x2": [[3, 3] + [0] * (w - 2), [3, 3] + [0] * (w - 2)]
        + [[0] * w for _ in range(h - 2)],
        "short_line": [[3, 3] + [0] * (w - 2)] + [[0] * w for _ in range(h - 1)],
    }
    for name, grid in impostors.items():
        assert gen.self_check(grid), name


def test_negative_recombination_rejects_missing_vertical_contrast():
    grid = gen.generate(91, 0, difficulty="easy")
    mutated = copy.deepcopy(grid)
    analysis = gen._analysis(mutated)
    vertical = analysis["vertical"][0]
    for row, col in vertical["cells"]:
        mutated[row][col] = analysis["decor_color"]
    assert gen.self_check(mutated)
    # The oracle-domain mirror can still execute; malformed teaching grammar
    # and executable rule input are intentionally separate questions.
    assert gen.rule_mirror(mutated)


def test_schedule_contains_required_shortcut_counterexamples():
    grids = [gen.generate(300 + i, i, difficulty="easy") for i in range(4)]
    assert any(gen.SEMANTIC_WITNESSES["other_color_l_stays_unchanged"](g) for g in grids)
    assert any(gen.SEMANTIC_WITNESSES["more_than_two_targets"](g) for g in grids)
    assert all(gen.SEMANTIC_WITNESSES["horizontal_bar_stays_green"](g) for g in grids)
    assert all(gen.SEMANTIC_WITNESSES["vertical_bar_stays_green"](g) for g in grids)
