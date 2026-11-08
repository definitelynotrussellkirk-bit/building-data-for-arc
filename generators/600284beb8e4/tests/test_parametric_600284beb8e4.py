"""Contract and adversarial regressions for the cue-directed overlap family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
PROTO = HOME / "workspace/parametric"


def _load():
    path = PROTO / "adapter.py"
    spec = importlib.util.spec_from_file_location("parametric_600284beb8e4_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_contract_programs_and_default_source_are_exact() -> None:
    adapter = _load()
    contract = json.loads((PROTO / "promotion.json").read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/600284beb8e4/workspace/parametric/adapter.py",
        "parameters": {"edge_policy": ["full", "near_cue", "far_cue"]},
        "default": {"edge_policy": "full"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 2,
        "resources": [
            "generators/600284beb8e4/workspace/parametric/canonical.rkt",
            "generators/600284beb8e4/workspace/parametric/near_cue.rkt",
            "generators/600284beb8e4/workspace/parametric/far_cue.rkt",
        ],
    }
    canonical = (PROTO / "canonical.rkt").read_text()
    assert adapter.program({"edge_policy": "full"}) == canonical
    assert len({adapter.program({"edge_policy": value}) for value in adapter.EDGE_POLICIES}) == 3


def test_requested_counts_are_independent_and_query_bank_is_stable() -> None:
    adapter = _load()
    for setting in adapter.EDGE_POLICIES:
        full = adapter.generate(19, {"edge_policy": setting}, 6, 4)
        assert len(full["train"]) == 6 and len(full["test"]) == 4
        assert len({_frozen(p["input"]) for p in full["train"] + full["test"]}) == 10
        for demos in range(2, 7):
            for queries in range(1, 5):
                episode = adapter.generate(19, {"edge_policy": setting}, demos, queries)
                assert episode["train"] == full["train"][:demos]
                assert episode["test"] == full["test"][:queries]
                assert episode["program_solution"] == adapter.program({"edge_policy": setting})


def test_inputs_are_matched_across_settings_but_labels_change() -> None:
    adapter = _load()
    episodes = {
        setting: adapter.generate(31, {"edge_policy": setting}, 2, 4)
        for setting in adapter.EDGE_POLICIES
    }
    baseline = [p["input"] for p in episodes["full"]["train"] + episodes["full"]["test"]]
    for episode in episodes.values():
        assert [p["input"] for p in episode["train"] + episode["test"]] == baseline
    for index in range(6):
        outputs = {
            _frozen((episodes[s]["train"] + episodes[s]["test"])[index]["output"])
            for s in adapter.EDGE_POLICIES
        }
        assert len(outputs) == 3


def test_minimum_two_demos_identify_all_declared_settings() -> None:
    adapter = _load()
    for seed in range(48):
        for chosen in adapter.EDGE_POLICIES:
            episode = adapter.generate(seed, {"edge_policy": chosen}, 2, 4)
            survivors = []
            for candidate in adapter.EDGE_POLICIES:
                if all(
                    adapter.rule_mirror(pair["input"], candidate) == pair["output"]
                    for pair in episode["train"]
                ):
                    survivors.append(candidate)
            assert survivors == [chosen]


def test_crossed_controls_break_fixed_edge_and_rectangle_role_shortcuts() -> None:
    adapter = _load()
    for seed in range(40):
        episode = adapter.generate(seed, {"edge_policy": "near_cue"}, 2, 4)
        pairs = episode["train"] + episode["test"]
        sides = [adapter.inspect_scene(pair["input"])["cue_side"] for pair in pairs]
        assert len(set(sides[:2])) == 2
        assert len(set(sides)) == 4
        for fixed_side in adapter.CUE_SIDES:
            assert any(
                adapter.fixed_edge_rival(pair["input"], fixed_side) != pair["output"]
                for pair in episode["train"]
            )
        assert any(adapter.color2_near_rival(pair["input"]) != pair["output"] for pair in episode["train"])
        assert any(adapter.color2_far_rival(pair["input"]) != pair["output"] for pair in episode["train"])


def test_fourth_query_is_substantive_30_by_30() -> None:
    adapter = _load()
    episode = adapter.generate(5, {"edge_policy": "near_cue"}, 2, 4)
    grid = episode["test"][3]["input"]
    scene = adapter.inspect_scene(grid)
    assert len(grid) == 30 and len(grid[0]) == 30
    assert sum(value != 0 for row in grid for value in row) >= 100
    assert scene["overlap_height"] >= 8 and scene["overlap_width"] >= 8
    assert any(value in {4, 6} for row in grid for value in row)


def test_malformed_requests_are_rejected_without_coercion() -> None:
    adapter = _load()
    bad_programs = [
        None,
        {},
        {"edge_policy": "near"},
        {"edge_policy": "full", "extra": 1},
        {"edge_policy": 0},
    ]
    for settings in bad_programs:
        with pytest.raises((TypeError, ValueError)):
            adapter.program(settings)

    bad_generate = [
        (True, {"edge_policy": "full"}, 2, 4),
        (1, {"edge_policy": "full"}, True, 4),
        (1, {"edge_policy": "full"}, 2, False),
        (1, {"edge_policy": "full"}, 1, 4),
        (1, {"edge_policy": "full"}, 7, 4),
        (1, {"edge_policy": "full"}, 2, 0),
        (1, {"edge_policy": "full"}, 2, 5),
    ]
    for args in bad_generate:
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(*args)


def test_returns_are_fresh_and_input_mutation_does_not_leak() -> None:
    adapter = _load()
    first = adapter.generate(99, {"edge_policy": "far_cue"}, 2, 4)
    second = adapter.generate(99, {"edge_policy": "far_cue"}, 2, 4)
    assert first == second and first is not second
    original = copy.deepcopy(second)
    first["train"][0]["input"][0][0] = 9
    assert adapter.generate(99, {"edge_policy": "far_cue"}, 2, 4) == original
