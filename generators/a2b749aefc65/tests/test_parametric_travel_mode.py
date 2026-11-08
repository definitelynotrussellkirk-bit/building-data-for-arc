"""Behavior tests for the proposed one-step/two-step travel family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from reviewer_support import find_root

ROOT = find_root(__file__)
HOME = ROOT / "generators/a2b749aefc65/workspace/parametric"
PROTOTYPE_PATH = HOME / "prototype.py"
ADAPTER_PATH = HOME / "adapter.py"
CONTRACT_PATH = HOME / "promotion.json"
PROBE_PATH = HOME / "adversarial_probe.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_task_local_parametric_artifacts_are_present() -> None:
    assert PROTOTYPE_PATH.is_file()
    assert ADAPTER_PATH.is_file()
    assert CONTRACT_PATH.is_file()
    assert PROBE_PATH.is_file()


@pytest.fixture(scope="module")
def prototype():
    return _load("parametric_a2b749aefc65", PROTOTYPE_PATH)


@pytest.fixture(scope="module")
def adapter():
    sys.path.insert(0, str(HOME))
    try:
        return _load("parametric_a2b749aefc65_adapter", ADAPTER_PATH)
    finally:
        sys.path.remove(str(HOME))


@pytest.fixture(scope="module")
def bridge(prototype):
    with prototype.RacketBridge(max_calls_before_restart=192) as active:
        yield active


def test_default_program_is_exact_and_two_step_patch_is_guarded(prototype) -> None:
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "4126da9b82909ec2ed3442a85c7bd8b43f0c5397ab595e705da49b86f76b54bb"
    )
    assert prototype.program_for("one_step", root=ROOT) == canonical
    two = prototype.program_for("two_steps", root=ROOT)
    assert two != canonical
    assert "(+ r (* 2 dr))" in two
    assert "(+ c (* 2 dc))" in two
    for bad in ("three_steps", "", 1, True, None):
        with pytest.raises(ValueError, match="travel_mode"):
            prototype.program_for(bad, root=ROOT)


def test_real_racket_and_python_mirror_distinguish_both_modes(prototype, bridge) -> None:
    grid = prototype.build_input(7, 0, 7, "medium")
    before = copy.deepcopy(grid)
    outputs = {}
    for mode in prototype.ALLOWED_MODES:
        expected = prototype.python_mirror(grid, travel_mode=mode)
        actual = prototype.execute_rule(
            prototype.program_for(mode, root=ROOT), grid, bridge=bridge
        )
        assert actual == expected
        outputs[mode] = actual
    assert outputs["one_step"] != outputs["two_steps"]
    assert grid == before


def test_sampler_reserves_sources_and_both_destination_sets(prototype) -> None:
    for seed in (0, 11, 97):
        for sample_index in range(6):
            grid = prototype.build_input(seed, sample_index, 7, "hard")
            facts = prototype.analyze_motion(grid)
            markers = facts["markers"]
            assert {marker["side"] for marker in markers} == {"top", "bottom", "left", "right"}
            occupied = []
            for marker in markers:
                occupied.extend({
                    marker["source"], marker["destination_one"], marker["destination_two"]
                })
            assert len(occupied) == len(set(occupied))
            assert set(facts["distractors"]).isdisjoint(occupied)


def test_sampler_preserves_blocked_and_partially_blocked_boundary_branches(prototype) -> None:
    grid = prototype.build_input(43, 0, 6, "medium")
    markers = prototype.analyze_motion(grid)["markers"]
    for side in ("top", "bottom", "left", "right"):
        side_markers = [marker for marker in markers if marker["side"] == side]
        assert any(
            marker["destination_one"] == marker["source"]
            and marker["destination_two"] == marker["source"]
            for marker in side_markers
        ), side
        assert any(
            marker["destination_one"] != marker["source"]
            and marker["destination_two"] == marker["source"]
            for marker in side_markers
        ), side


def test_adapter_outputs_matched_identifiable_episodes_with_four_queries(
    prototype, adapter, bridge
) -> None:
    families = {
        mode: adapter.generate(17, {"travel_mode": mode}, 2, 4)
        for mode in prototype.ALLOWED_MODES
    }
    inputs = [
        pair["input"]
        for pair in families["one_step"]["train"] + families["one_step"]["test"]
    ]
    assert len({prototype.grid_sha256(grid) for grid in inputs}) == 6
    for mode, claims in families.items():
        assert claims["program_solution"] == prototype.program_for(mode, root=ROOT)
        assert len(claims["train"]) == 2 and len(claims["test"]) == 4
        assert [pair["input"] for pair in claims["train"] + claims["test"]] == inputs
        rival = next(value for value in prototype.ALLOWED_MODES if value != mode)
        assert all(
            pair["output"] == prototype.python_mirror(pair["input"], travel_mode=mode)
            and pair["output"] != prototype.python_mirror(pair["input"], travel_mode=rival)
            for pair in claims["train"]
        )
        for pair in claims["train"] + claims["test"]:
            assert prototype.execute_rule(
                claims["program_solution"], pair["input"], bridge=bridge
            ) == pair["output"]


def test_counts_validation_and_contract_are_strict(prototype, adapter) -> None:
    for demos in (2, 6):
        claims = adapter.generate(29, {"travel_mode": "one_step"}, demos, 4)
        assert len(claims["train"]) == demos and len(claims["test"]) == 4
    for demos in (1, 7, True):
        with pytest.raises(ValueError, match="demos"):
            adapter.generate(1, {"travel_mode": "one_step"}, demos, 4)
    for queries in (0, 3, 5, True):
        with pytest.raises(ValueError, match="queries"):
            adapter.generate(1, {"travel_mode": "one_step"}, 2, queries)
    for settings in ({}, {"travel_mode": "bad"}, {"extra": "one_step"}):
        with pytest.raises(ValueError):
            adapter.program(settings)

    assert json.loads(CONTRACT_PATH.read_text()) == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/a2b749aefc65/workspace/parametric/adapter.py",
        "parameters": {"travel_mode": ["one_step", "two_steps"]},
        "default": {"travel_mode": "one_step"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
    }


def test_final_query_is_substantive_30_by_30_not_padding(prototype, adapter) -> None:
    claims = adapter.generate(31, {"travel_mode": "two_steps"}, 2, 4)
    grid = claims["test"][-1]["input"]
    assert [len(grid), len(grid[0])] == [30, 30]
    facts = prototype.analyze_motion(grid)
    assert len(facts["markers"]) >= 24
    assert len(facts["distractors"]) >= 12
    assert {marker["side"] for marker in facts["markers"]} == {
        "top", "bottom", "left", "right"
    }
    one = prototype.python_mirror(grid, travel_mode="one_step")
    two = prototype.python_mirror(grid, travel_mode="two_steps")
    assert one != two
    assert sum(value != facts["background"] for row in two[1:-1] for value in row[1:-1]) >= 36
