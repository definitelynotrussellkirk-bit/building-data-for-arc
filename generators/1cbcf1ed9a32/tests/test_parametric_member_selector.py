"""Focused tests for the native common-pair member selector family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import random

import pytest

ROOT = Path(__file__).resolve().parents[3]
HOME = ROOT / "generators/1cbcf1ed9a32"
PARAMETRIC = HOME / "workspace/parametric"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
PROMOTION_PATH = PARAMETRIC / "promotion.json"


def _adapter():
    assert ADAPTER_PATH.is_file(), "parametric adapter has not been built"
    spec = importlib.util.spec_from_file_location(
        "_task_1cbcf1ed9a32_member_selector_adapter", ADAPTER_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _outputs(episode):
    return [pair["output"] for pair in episode["train"] + episode["test"]]


def test_contract_declares_exact_two_modes_and_four_queries():
    assert PROMOTION_PATH.is_file(), "promotion contract has not been built"
    assert json.loads(PROMOTION_PATH.read_text(encoding="utf-8")) == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/1cbcf1ed9a32/workspace/parametric/adapter.py",
        "parameters": {"output_mode": ["canonical_shape", "selector_member"]},
        "default": {"output_mode": "canonical_shape"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "qualification_demos": 3,
        "resources": [
            "generators/1cbcf1ed9a32/workspace/parametric/selector_member.rkt"
        ],
    }


def test_default_program_is_exact_canonical_and_alternative_is_distinct():
    adapter = _adapter()
    canonical = adapter.canonical_program()
    assert adapter.program({"output_mode": "canonical_shape"}) == canonical
    alternative = adapter.program({"output_mode": "selector_member"})
    assert alternative.strip()
    assert alternative != canonical
    with pytest.raises(ValueError):
        adapter.program({"output_mode": "unknown"})
    with pytest.raises(ValueError):
        adapter.program({"output_mode": "canonical_shape", "extra": True})


def test_generation_uses_matched_inputs_and_teaches_the_mode_from_demos_only():
    adapter = _adapter()
    canonical = adapter.generate(17, {"output_mode": "canonical_shape"}, 3, 4)
    selected = adapter.generate(17, {"output_mode": "selector_member"}, 3, 4)

    assert _inputs(canonical) == _inputs(selected)
    assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(canonical)}) == 7
    assert all(a != b for a, b in zip(_outputs(canonical), _outputs(selected)))

    for setting, episode in (
        ("canonical_shape", canonical),
        ("selector_member", selected),
    ):
        assert episode["program_solution"] == adapter.program({"output_mode": setting})
        certificate = adapter.certificate(
            episode["train"], [pair["input"] for pair in episode["test"]]
        )
        assert certificate["survivors"] == [setting]
        assert certificate["demos"] == 3
        assert certificate["queries"] == 4
        assert certificate["query_labels_used_for_inference"] is False
        assert certificate["selector_one_witness"] is True
        assert certificate["selector_two_witness"] is True
        assert certificate["panel_zero_distractor_witness"] is True
        assert certificate["noncanonical_orientation_witness"] is True


def test_supported_demo_counts_are_exact_and_queries_include_substantive_30x30():
    adapter = _adapter()
    for demos in range(2, 7):
        for setting in adapter.OUTPUT_MODES:
            episode = adapter.generate(900 + demos, {"output_mode": setting}, demos, 4)
            assert len(episode["train"]) == demos
            assert len(episode["test"]) == 4
            assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(episode)}) == demos + 4
            assert any(len(pair["input"]) == len(pair["input"][0]) == 30 for pair in episode["test"])
            for pair in episode["train"] + episode["test"]:
                observed = adapter.analyze(pair["input"])
                assert observed["errors"] == []
                assert sorted(observed["signature_counts"].values()) == [1, 2]
                assert len(set(observed["largest_sizes"])) == 1
                assert observed["selector"] in (1, 2)
                assert observed["common_orientations_distinct"] is True
                assert pair["output"] == adapter.solve(pair["input"], setting)
            large = next(pair["input"] for pair in episode["test"] if len(pair["input"]) == len(pair["input"][0]) == 30)
            large_observed = adapter.analyze(large)
            assert min(large_observed["largest_sizes"]) >= 40
            assert sum(cell not in (0, 5) for row in large for cell in row) >= 120

    for demos, queries in ((1, 4), (7, 4), (2, 3), (2, 5)):
        with pytest.raises(ValueError):
            adapter.generate(3, {"output_mode": "canonical_shape"}, demos, queries)


def test_minimum_lessons_reject_declared_shortcuts_across_seed_sweep():
    adapter = _adapter()
    expected_rivals = {
        "first_common_orientation",
        "second_common_orientation",
        "first_panel_orientation",
        "last_panel_orientation",
        "selector_absolute_panel",
        "selector_host_panel",
        "distractor_orientation",
        "repeated_size_else_first_canonical",
    }
    assert expected_rivals <= set(adapter.HYPOTHESES)
    for seed in range(32):
        for setting in adapter.OUTPUT_MODES:
            episode = adapter.generate(seed, {"output_mode": setting}, 2, 4)
            certificate = adapter.certificate(
                episode["train"], [pair["input"] for pair in episode["test"]]
            )
            assert certificate["survivors"] == [setting]
            assert expected_rivals.isdisjoint(certificate["survivors"])
            assert all(certificate["query_disagreement"][name] for name in expected_rivals)


def test_generation_is_deterministic_fresh_and_does_not_touch_global_random():
    adapter = _adapter()
    random.seed(20261024)
    state = random.getstate()
    first = adapter.generate(101, {"output_mode": "selector_member"}, 6, 4)
    assert random.getstate() == state
    second = adapter.generate(101, {"output_mode": "selector_member"}, 6, 4)
    assert first == second
    assert first is not second
    assert first["train"] is not second["train"]
    assert all(a is not b for a, b in zip(_inputs(first), _inputs(second)))
    first["train"][0]["input"][0][0] = 9
    assert adapter.generate(101, {"output_mode": "selector_member"}, 6, 4) == second


def test_causal_case_names_real_intermediate_and_wrong_pair_changes_output():
    adapter = _adapter()
    witness = adapter.causal_case()
    assert witness["step_a"] == "compare the three largest objects up to D4 and retain the ordered repeated-shape pair"
    assert witness["step_b"] == "use selector 1 or 2 to choose a member of that pair and emit its observed normalized orientation"
    assert witness["intermediate"] != witness["wrong_intermediate"]
    assert witness["output"] != witness["counterfactual_output"]
    assert witness["output"] == adapter.solve(witness["input"], "selector_member")


def test_public_projection_reveals_only_demos_and_one_query_input():
    adapter = _adapter()
    episode = adapter.generate(19, {"output_mode": "selector_member"}, 3, 4)
    before = copy.deepcopy(episode)
    for query_index in range(4):
        public = adapter.public_turn(episode, query_index)
        assert set(public) == {"train", "test"}
        assert public["train"] == episode["train"]
        assert public["test"] == [{"input": episode["test"][query_index]["input"]}]
        encoded = json.dumps(public, sort_keys=True)
        assert "output_mode" not in encoded
        assert "program_solution" not in encoded
        assert "query_outputs" not in encoded
        assert "queries" not in encoded
    assert episode == before
