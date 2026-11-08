"""Native parametric contract tests for the keyed-ray route family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "7d09ccad28c8"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
PARAM = HOME / "workspace" / "parametric"


def _load(name: str, filename: str):
    path = PARAM / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical task row not found")


def _inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_contract_and_default_program_are_exact():
    adapter = _load("route_adapter_contract", "adapter.py")
    contract = json.loads((PARAM / "promotion.json").read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"route_mode": ["straight", "clockwise_elbow"]},
        "default": {"route_mode": "straight"},
        "qualification_demos": 2,
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/clockwise-elbow.rkt",
            f"generators/{TASK_ID}/workspace/parametric/wrong-intermediate.rkt",
        ],
    }
    assert adapter.program({"route_mode": "straight"}) == _canonical_program()
    assert adapter.program({"route_mode": "clockwise_elbow"}) != _canonical_program()


@pytest.mark.parametrize("demos,queries", [(2, 1), (2, 4), (6, 1), (6, 4)])
def test_counts_setting_independent_inputs_and_real_divergence(demos: int, queries: int):
    adapter = _load(f"route_adapter_{demos}_{queries}", "adapter.py")
    family = _load(f"route_family_{demos}_{queries}", "family.py")
    straight = adapter.generate(314159, {"route_mode": "straight"}, demos, queries)
    elbow = adapter.generate(314159, {"route_mode": "clockwise_elbow"}, demos, queries)
    assert len(straight["train"]) == len(elbow["train"]) == demos
    assert len(straight["test"]) == len(elbow["test"]) == queries
    assert _inputs(straight) == _inputs(elbow)
    assert len({json.dumps(grid) for grid in _inputs(straight)}) == demos + queries
    for split in ("train", "test"):
        for canonical_pair, elbow_pair in zip(straight[split], elbow[split]):
            grid = canonical_pair["input"]
            assert canonical_pair["output"] == family.transform(grid, "straight")
            assert elbow_pair["output"] == family.transform(grid, "clockwise_elbow")
            assert canonical_pair["output"] != elbow_pair["output"]


def test_streams_are_prefix_stable_and_fourth_query_is_substantive_30x30():
    adapter = _load("route_adapter_prefix", "adapter.py")
    short = adapter.generate(2718, {"route_mode": "clockwise_elbow"}, 2, 1)
    long = adapter.generate(2718, {"route_mode": "clockwise_elbow"}, 6, 4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]
    large = long["test"][3]["input"]
    assert (len(large), len(large[0])) == (30, 30)
    assert sum(cell != 0 for row in large for cell in row) >= 150


def test_computed_first_endpoint_is_causally_used_by_second_leg():
    family = _load("route_family_causal", "family.py")
    grid = family.build_input(99, "test", 3)
    analysis = family.route_analysis(grid)
    assert analysis
    assert any(frame["first_leg"] and frame["second_leg"] for frame in analysis)
    correct = family.transform(grid, "clockwise_elbow")
    wrong = family.transform_wrong_intermediate(grid)
    assert correct != family.transform(grid, "straight")
    assert correct != wrong


@pytest.mark.parametrize(
    "settings,demos,queries,error",
    [
        ({}, 2, 1, ValueError),
        ({"route_mode": "invented"}, 2, 1, ValueError),
        ({"route_mode": "straight", "extra": 1}, 2, 1, ValueError),
        ({"route_mode": "straight"}, True, 1, TypeError),
        ({"route_mode": "straight"}, 1, 1, ValueError),
        ({"route_mode": "straight"}, 2, 5, ValueError),
    ],
)
def test_invalid_contract_inputs_fail_loudly(settings, demos, queries, error):
    adapter = _load("route_adapter_invalid", "adapter.py")
    with pytest.raises(error):
        adapter.generate(1, settings, demos, queries)
