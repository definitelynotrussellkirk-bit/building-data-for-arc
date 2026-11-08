from __future__ import annotations

import copy
import pytest

import importlib
from scripts.canonical_profile_gate import canonical_pairs

gen = importlib.import_module("puzzle_generators.per_puzzle.59d647aebebb.generator")


def _canonical_inputs():
    return [pair["input"] for pair in canonical_pairs(gen.TASK_ID)]


def test_accepts_every_canonical_input():
    assert [gen.self_check(grid) for grid in _canonical_inputs()] == [[], [], []]


def test_default_schedule_covers_canonical_profile_and_operations():
    observed = [gen.observe_overrides(gen.generate(123, index, difficulty="medium"))
                for index in range(3)]
    assert observed[0] == {
        "grid_h": 4,
        "panel_w": 4,
        "operation": "union",
        "palette_size": 1,
    }
    assert {row["operation"] for row in observed} == set(gen.OPS)
    assert [gen.schedule_profile(123, index) for index in range(3)] == list(range(3))


@pytest.mark.parametrize("grid_h", [4, 10])
@pytest.mark.parametrize("panel_w", [3, 5])
@pytest.mark.parametrize("operation", gen.OPS)
@pytest.mark.parametrize("palette_size", [1, 4])
def test_exact_override_round_trip(grid_h, panel_w, operation, palette_size):
    requested = {
        "grid_h": grid_h,
        "panel_w": panel_w,
        "operation": operation,
        "palette_size": palette_size,
    }
    grid = gen.generate(911, 7, difficulty="hard", **requested)
    assert gen.observe_overrides(grid) == requested
    assert gen.self_check(grid, meta={"overrides": requested}) == []


def test_unknown_override_is_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, misspelled_axis=3)


def test_mutations_reject_missing_separator_and_wrong_demo():
    grid = gen.generate(55, 2)
    missing_separator = copy.deepcopy(grid)
    missing_separator[0][gen.observe_overrides(grid)["panel_w"]] = 0
    assert any("four full-height" in reason for reason in gen.self_check(missing_separator))

    wrong_demo = copy.deepcopy(grid)
    panel_w = gen.observe_overrides(grid)["panel_w"]
    demo_out_left = 2 * (panel_w + 1)
    wrong_demo[0][demo_out_left] = 0 if wrong_demo[0][demo_out_left] else 1
    assert gen.self_check(wrong_demo)


def test_fixed_operation_rivals_are_refuted_on_each_witness():
    for index, operation in enumerate(gen.OPS):
        grid = gen.generate(777, index)
        witness = gen.SEMANTIC_WITNESSES[f"operation_{operation.replace('-', '_')}"]
        assert witness(grid)
        authoritative = gen._fixed_operation_solver(operation)(grid)
        for rival_name in gen.WITNESS_RIVALS[f"operation_{operation.replace('-', '_')}"]:
            assert gen.SEMANTIC_RIVALS[rival_name](grid) != authoritative
