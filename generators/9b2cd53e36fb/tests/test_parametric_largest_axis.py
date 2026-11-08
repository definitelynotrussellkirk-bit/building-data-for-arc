"""Focused contract and sampler tests for the native largest-axis family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

from arcpuzzles.catalog import Catalog
from reviewer_support import find_root, public_challenge_bytes


TASK_ID = "9b2cd53e36fb"
REPO = find_root(__file__)
HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"
ADAPTER = HOME / "adapter.py"
PROTOTYPE = HOME / "prototype.py"
CONTRACT = HOME / "promotion.json"


def load_module(path: Path, label: str):
    assert path.is_file(), f"missing {path.relative_to(REPO)}"
    name = f"_test_{TASK_ID}_{label}_{path.stat().st_mtime_ns}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def adapter():
    return load_module(ADAPTER, "adapter")


def prototype():
    return load_module(PROTOTYPE, "prototype")


def canonical_program() -> str:
    programs = {
        row["program_solution"]
        for row in Catalog(REPO)._variants()[TASK_ID]
        if isinstance(row.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def assert_episode_shape(episode: dict, demos: int, queries: int) -> None:
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    assert all(set(pair) >= {"input", "output"} for pair in episode["train"] + episode["test"])
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in inputs(episode)]
    assert len(serialized) == len(set(serialized))


def test_contract_binds_exact_canonical_default_and_two_settings():
    contract = json.loads(CONTRACT.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/9b2cd53e36fb/workspace/parametric/adapter.py",
        "parameters": {"selection": ["all_holes", "largest_axis"]},
        "default": {"selection": "all_holes"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "qualification_demos": 3,
        "resources": [
            "generators/9b2cd53e36fb/workspace/parametric/prototype.py",
            "generators/9b2cd53e36fb/workspace/parametric/rules/all_holes.rkt",
            "generators/9b2cd53e36fb/workspace/parametric/rules/largest_axis.rkt",
        ],
    }
    module = adapter()
    assert module.program({"selection": "all_holes"}) == canonical_program()
    assert module.program({"selection": "largest_axis"}) != canonical_program()


@pytest.mark.parametrize("demos", range(2, 7))
def test_setting_neutral_inputs_are_distinct_deterministic_and_teaching_safe(demos: int):
    module = adapter()
    all_holes = module.generate(37, {"selection": "all_holes"}, demos, 4)
    largest_axis = module.generate(37, {"selection": "largest_axis"}, demos, 4)
    assert_episode_shape(all_holes, demos, 4)
    assert_episode_shape(largest_axis, demos, 4)
    assert inputs(all_holes) == inputs(largest_axis)
    assert module.generate(37, {"selection": "largest_axis"}, demos, 4) == largest_axis
    assert all(
        canonical["output"] != focused["output"]
        for canonical, focused in zip(all_holes["train"], largest_axis["train"], strict=True)
    )


@pytest.mark.parametrize("demos", range(2, 7))
def test_every_case_has_both_axes_unique_control_and_secondary_selected_hole(demos: int):
    module = adapter()
    proto = prototype()
    episode = module.generate(4, {"selection": "largest_axis"}, demos, 4)
    for pair in episode["train"] + episode["test"]:
        facts = proto.analyze_input(pair["input"])
        assert facts["errors"] == []
        edge_holes = facts["edge_holes"]
        assert {hole["axis"] for hole in edge_holes} == {"rows", "cols"}
        areas = [hole["area"] for hole in edge_holes]
        assert areas.count(max(areas)) == 1
        assert facts["control"]["area"] == max(areas)
        assert sum(hole["axis"] == facts["control"]["axis"] for hole in edge_holes) >= 2


def test_queries_cover_large_canvases_and_substantive_30_by_30_stress():
    module = adapter()
    proto = prototype()
    canonical = module.generate(9, {"selection": "all_holes"}, 3, 4)
    focused = module.generate(9, {"selection": "largest_axis"}, 3, 4)
    dimensions = [(len(pair["input"]), len(pair["input"][0])) for pair in canonical["test"]]
    assert dimensions == [(18, 14), (14, 18), (24, 30), (30, 30)]
    grid = canonical["test"][-1]["input"]
    facts = proto.analyze_input(grid)
    assert facts["errors"] == []
    assert len(facts["edge_holes"]) >= 5
    assert len(facts["floating_holes"]) == 1
    assert sum(cell == 0 for row in grid for cell in row) >= 40
    assert sum(cell in (5, 7) for row in grid for cell in row) >= 800
    assert canonical["test"][-1]["output"] != focused["test"][-1]["output"]


def test_first_turn_public_bytes_do_not_depend_on_future_queries_or_private_fields():
    episode = adapter().generate(12, {"selection": "largest_axis"}, 3, 4)
    first_turn = {"train": episode["train"], "test": [episode["test"][0]]}
    changed = copy.deepcopy(episode)
    changed["program_solution"] = "private program changed"
    changed["test"][0]["output"] = [[9]]
    changed["test"][1]["input"] = [[8]]
    assert public_challenge_bytes(first_turn) == public_challenge_bytes(
        {"train": changed["train"], "test": [changed["test"][0]]}
    )
    visible = json.loads(public_challenge_bytes(first_turn))
    assert set(visible) == {"train", "test"}
    assert visible["test"] == [{"input": episode["test"][0]["input"]}]


def test_trace_names_real_input_dependent_intermediate_and_selected_outputs():
    module = adapter()
    proto = prototype()
    episode = module.generate(2, {"selection": "largest_axis"}, 3, 4)
    for pair in episode["train"][:2]:
        trace = proto.sequential_trace(pair["input"])
        assert trace["step_a"] == "find the unique largest edge-touching zero component and derive its mirror axis"
        assert trace["step_b"] == "mirror and sweep every edge hole whose mirror axis matches that derived axis"
        assert trace["intermediate_value"]["axis"] in {"rows", "cols"}
        assert trace["intermediate_value"]["area"] > 0
        assert pair["output"] == proto.apply_rule(pair["input"], "largest_axis")


@pytest.mark.parametrize(
    "settings",
    [{}, {"selection": "unknown"}, {"selection": True}, {"selection": "all_holes", "extra": 1}],
)
def test_undeclared_settings_are_rejected(settings: dict):
    with pytest.raises(ValueError):
        adapter().generate(0, settings, 3, 4)


@pytest.mark.parametrize(
    "seed,demos,queries",
    [(-1, 3, 4), (True, 3, 4), (2**63, 3, 4), (0, 1, 4), (0, 7, 4),
     (0, 3, 3), (0, 3, 5), (0, 3, True), (0, 3.0, 4)],
)
def test_invalid_requests_fail_without_coercion(seed, demos, queries):
    with pytest.raises(ValueError):
        adapter().generate(seed, {"selection": "all_holes"}, demos, queries)


def test_generation_does_not_touch_global_random_state_and_returns_fresh_data():
    module = adapter()
    random.seed(8128)
    before = random.getstate()
    first = module.generate(55, {"selection": "largest_axis"}, 3, 4)
    assert random.getstate() == before
    second = module.generate(55, {"selection": "largest_axis"}, 3, 4)
    assert first == second
    first["train"][0]["input"][0][0] = 9
    assert module.generate(55, {"selection": "largest_axis"}, 3, 4) == second


@pytest.mark.parametrize("seed", range(8))
@pytest.mark.parametrize("selection", ["all_holes", "largest_axis"])
def test_two_demo_prefix_rejects_declared_and_plausible_shortcuts(seed: int, selection: str):
    module = adapter()
    proto = prototype()
    episode = module.generate(seed, {"selection": selection}, 2, 4)
    assert set(proto.variant_names()) == {
        "all_holes",
        "largest_axis",
        "fixed_rows",
        "fixed_cols",
        "only_largest",
    }
    for rival in proto.variant_names():
        assert isinstance(proto.variant_program(rival), str) and proto.variant_program(rival).strip()
        if rival == selection:
            continue
        assert any(
            proto.apply_variant(pair["input"], rival) != pair["output"]
            for pair in episode["train"]
        ), f"seed {seed} setting {selection} leaves rival {rival} alive"
