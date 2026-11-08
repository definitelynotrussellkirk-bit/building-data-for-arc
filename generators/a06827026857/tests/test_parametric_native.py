from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root

ROOT = find_root(__file__)
HERE = ROOT / "generators" / "a06827026857" / "workspace" / "parametric"
ADAPTER = HERE / "adapter.py"


def load_adapter():
    assert ADAPTER.is_file(), "native parametric adapter has not been built"
    spec = importlib.util.spec_from_file_location("parametric_a06827026857", ADAPTER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    root = find_root(__file__)
    path = root / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == "a06827026857":
            return row["program_solution"]
    raise AssertionError("canonical program missing")


def test_default_program_is_byte_exact_canonical():
    adapter = load_adapter()
    setting = {"window_scope": "all_windows"}
    assert adapter.program(setting) == canonical_program()
    assert adapter.program(setting).encode() == (HERE / "canonical.rkt").read_bytes()


def test_settings_and_counts_are_strict():
    adapter = load_adapter()
    for bad in (None, {}, {"window_scope": "unknown"}, {"window_scope": 1},
                {"window_scope": "all_windows", "x": 1}):
        with pytest.raises(ValueError):
            adapter.program(bad)
    for name, value in (("seed", True), ("demos", True), ("queries", True)):
        kwargs = dict(seed=0, settings={"window_scope": "all_windows"}, demos=3, queries=4)
        kwargs[name] = value
        with pytest.raises(ValueError):
            adapter.generate(**kwargs)
    for demos in (1, 7):
        with pytest.raises(ValueError):
            adapter.generate(0, {"window_scope": "all_windows"}, demos, 4)
    for queries in (0, 5):
        with pytest.raises(ValueError):
            adapter.generate(0, {"window_scope": "all_windows"}, 3, queries)


def test_counts_are_prefix_stable_and_inputs_match_across_settings():
    adapter = load_adapter()
    default = {"window_scope": "all_windows"}
    small = adapter.generate(17, default, 2, 1)
    large = adapter.generate(17, default, 6, 4)
    alternate = adapter.generate(17, {"window_scope": "dominant_color"}, 6, 4)
    assert small["train"] == large["train"][:2]
    assert small["test"] == large["test"][:1]
    assert [p["input"] for p in large["train"]] == [p["input"] for p in alternate["train"]]
    assert [p["input"] for p in large["test"]] == [p["input"] for p in alternate["test"]]
    keys = [json.dumps(p["input"], separators=(",", ":")) for p in large["train"] + large["test"]]
    assert len(keys) == len(set(keys))


def test_python_claims_match_both_rules_and_two_demos_identify_setting():
    adapter = load_adapter()
    for seed in (0, 17, 97):
        for scope in adapter.SETTINGS:
            setting = {"window_scope": scope}
            episode = adapter.generate(seed, setting, 2, 4)
            assert episode["program_solution"] == adapter.program(setting)
            for pair in episode["train"] + episode["test"]:
                assert pair["output"] == adapter.predict(pair["input"], setting)
                info = adapter.observe(pair["input"])
                assert info["dominant_unique"] is True
                assert len(info["window_colors"]) >= 2
            assert adapter.surviving_settings(episode["train"]) == [setting]


def test_teaching_scenes_refute_first_color_and_all_color_shortcuts():
    adapter = load_adapter()
    episode = adapter.generate(0, {"window_scope": "dominant_color"}, 2, 4)
    for pair in episode["train"]:
        info = adapter.observe(pair["input"])
        assert info["first_window_color"] != info["dominant_color"]
        assert adapter.predict_first_color(pair["input"]) != pair["output"]
        assert adapter.predict(pair["input"], {"window_scope": "all_windows"}) != pair["output"]



def test_window_support_cannot_be_replaced_by_largest_foreground_color():
    adapter = load_adapter()
    episode = adapter.generate(0, {"window_scope": "dominant_color"}, 6, 4)
    for pair in episode["train"] + episode["test"]:
        info = adapter.observe(pair["input"])
        foreground_by_color = {
            color: sum(cell == color for row in pair["input"] for cell in row)
            for color in range(1, 10)
        }
        assert max(foreground_by_color, key=foreground_by_color.get) != info["dominant_color"]

def test_query_bank_contains_substantive_30_by_30_stress():
    adapter = load_adapter()
    for seed in (0, 3, 17, 41):
        episode = adapter.generate(seed, {"window_scope": "dominant_color"}, 3, 4)
        stress = [p for p in episode["test"] if (len(p["input"]), len(p["input"][0])) == (30, 30)]
        assert len(stress) == 1
        info = adapter.observe(stress[0]["input"])
        assert info["foreground_cells"] >= 250
        assert info["window_count"] >= 140
        assert len(info["window_colors"]) >= 3
        assert set(info["touches"]) >= {"top", "bottom", "left"}


def test_query_permutation_does_not_always_start_from_source_zero():
    adapter = load_adapter()
    first_positions = {adapter.query_source_order(seed)[0] for seed in range(12)}
    assert len(first_positions) > 1


def test_wrong_intermediate_counterfactual_changes_dependency_case():
    adapter = load_adapter()
    case = adapter.dependency_case(seed=0, settings={"window_scope": "dominant_color"})
    assert case["ablation"] == "wrong_intermediate"
    assert case["output"] == adapter.predict(case["input"], case["settings"])
    assert case["counterfactual_output"] == adapter.predict_first_color(case["input"])
    assert case["counterfactual_output"] != case["output"]
    explanation = adapter.explain_dependency(case["input"], case["settings"])
    assert explanation["step_a"]
    assert explanation["intermediate"]
    assert explanation["step_b"]
    assert explanation["dominant_color"] != explanation["first_window_color"]
