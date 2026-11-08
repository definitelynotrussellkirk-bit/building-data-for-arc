from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root

HERE = Path(__file__).resolve().parents[1] / "workspace" / "parametric"
ADAPTER = HERE / "adapter.py"


def load_adapter():
    assert ADAPTER.is_file(), "native parametric adapter has not been built"
    spec = importlib.util.spec_from_file_location("parametric_bc0816632908", ADAPTER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    root = find_root(__file__)
    path = root / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == "bc0816632908":
            return row["program_solution"]
    raise AssertionError("canonical program missing")


def test_default_program_is_byte_exact_canonical():
    adapter = load_adapter()
    setting = {"period": 3, "phase": 0}
    assert adapter.program(setting) == canonical_program()
    assert adapter.program(setting).encode() == (HERE / "racket" / "period3_phase0.rkt").read_bytes()


def test_settings_and_counts_are_strict():
    adapter = load_adapter()
    for bad in (None, {}, {"period": 3}, {"period": 3, "phase": 2},
                {"period": True, "phase": 0}, {"period": 3, "phase": 0, "x": 1}):
        with pytest.raises((TypeError, ValueError)):
            adapter.program(bad)
    for name, value in (("seed", True), ("demos", True), ("queries", True)):
        kwargs = dict(seed=0, settings={"period": 3, "phase": 0}, demos=3, queries=4)
        kwargs[name] = value
        with pytest.raises(ValueError):
            adapter.generate(**kwargs)
    for demos in (1, 7):
        with pytest.raises(ValueError):
            adapter.generate(0, {"period": 3, "phase": 0}, demos, 4)
    for queries in (0, 5):
        with pytest.raises(ValueError):
            adapter.generate(0, {"period": 3, "phase": 0}, 3, queries)


def test_counts_are_prefix_stable_and_inputs_match_across_settings():
    adapter = load_adapter()
    default = {"period": 3, "phase": 0}
    small = adapter.generate(17, default, 2, 1)
    large = adapter.generate(17, default, 6, 4)
    assert small["train"] == large["train"][:2]
    assert small["test"] == large["test"][:1]
    all_inputs = [pair["input"] for pair in large["train"] + large["test"]]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in all_inputs}) == len(all_inputs)
    for period, phase in adapter.SETTINGS:
        episode = adapter.generate(17, {"period": period, "phase": phase}, 6, 4)
        assert [p["input"] for p in episode["train"]] == [p["input"] for p in large["train"]]
        assert [p["input"] for p in episode["test"]] == [p["input"] for p in large["test"]]


def test_python_claims_match_each_setting_and_two_demos_identify_it():
    adapter = load_adapter()
    for seed in (0, 17, 97):
        for period, phase in adapter.SETTINGS:
            setting = {"period": period, "phase": phase}
            episode = adapter.generate(seed, setting, 2, 4)
            assert episode["program_solution"] == adapter.program(setting)
            for pair in episode["train"] + episode["test"]:
                assert pair["output"] == adapter.predict(pair["input"], setting)
            assert adapter.surviving_settings(episode["train"]) == [setting]


def test_query_bank_contains_substantive_30_by_30_stress():
    adapter = load_adapter()
    for seed in (0, 3, 17, 41):
        episode = adapter.generate(seed, {"period": 2, "phase": 1}, 3, 4)
        stress = [p for p in episode["test"] if (len(p["input"]), len(p["input"][0])) == (30, 30)]
        assert len(stress) == 1
        info = adapter.observe(stress[0]["input"])
        assert info["component_count"] >= 10
        assert info["foreground_cells"] >= 100
        assert info["row_order_differs"] is True
        assert set(info["touches"]) >= {"top", "bottom"}


def test_query_permutation_does_not_always_start_from_source_zero():
    adapter = load_adapter()
    first_positions = {adapter.query_source_order(seed)[0] for seed in range(12)}
    assert len(first_positions) > 1


def test_wrong_order_counterfactual_changes_output_on_dependency_case():
    adapter = load_adapter()
    case = adapter.dependency_case(seed=0, settings={"period": 3, "phase": 0})
    assert case["ablation"] == "wrong_order"
    assert case["output"] == adapter.predict(case["input"], case["settings"])
    assert case["counterfactual_output"] != case["output"]
    explanation = adapter.explain_dependency(case["input"], case["settings"])
    assert explanation["step_a"]
    assert explanation["intermediate"]
    assert explanation["step_b"]
    assert explanation["left_to_right_order"] != explanation["top_to_bottom_order"]
