from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root, public_challenge_bytes
from arcpuzzles import Catalog


TASK_ID = "89a9a629c544"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def load_prototype():
    path = PARAMETRIC / "prototype.py"
    assert path.is_file(), "native prototype is missing"
    spec = importlib.util.spec_from_file_location("_test_89_parametric", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_program():
    record = Catalog(ROOT).get(TASK_ID)
    programs = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_contract_and_exact_canonical_default():
    prototype = load_prototype()
    contract = json.loads((PARAMETRIC / "promotion.json").read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"axis_policy": ["vertical", "anchor_bbox"]},
        "default": {"axis_policy": "vertical"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/vertical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/anchor_bbox.rkt",
        ],
    }
    assert prototype.program({"axis_policy": "vertical"}) == canonical_program()
    assert (PARAMETRIC / "vertical.rkt").read_bytes() == canonical_program().encode()
    assert prototype.program({"axis_policy": "anchor_bbox"}) != canonical_program()
    alternate = prototype.program({"axis_policy": "anchor_bbox"})
    assert "(shape-w box)" in alternate and "(shape-h box)" in alternate
    assert "(third box)" not in alternate and "(fourth box)" not in alternate


@pytest.mark.parametrize("setting", ["vertical", "anchor_bbox"])
@pytest.mark.parametrize("demos", range(2, 7))
def test_every_supported_count_is_deterministic_distinct_and_teachable(setting, demos):
    prototype = load_prototype()
    settings = {"axis_policy": setting}
    episode = prototype.generate(17, settings, demos, 4)
    replay = prototype.generate(17, settings, demos, 4)
    assert episode == replay
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    assert episode["program_solution"] == prototype.program(settings)
    all_inputs = [pair["input"] for split in ("train", "test") for pair in episode[split]]
    assert len({frozen(grid) for grid in all_inputs}) == demos + 4
    assert prototype.teaching_failures(episode["train"], episode["test"], settings) == []
    for pair in episode["train"] + episode["test"]:
        assert prototype.validate_input(pair["input"]) == []
        assert pair["output"] == prototype.transform(pair["input"], settings)


@pytest.mark.parametrize("setting", ["vertical", "anchor_bbox"])
def test_inputs_are_setting_independent_and_count_prefix_stable(setting):
    prototype = load_prototype()
    one = prototype.generate(91, {"axis_policy": setting}, 2, 1)
    four = prototype.generate(91, {"axis_policy": setting}, 2, 4)
    other = prototype.generate(
        91,
        {"axis_policy": "anchor_bbox" if setting == "vertical" else "vertical"},
        2,
        4,
    )
    assert [p["input"] for p in one["train"]] == [p["input"] for p in four["train"]]
    assert one["test"][0]["input"] == four["test"][0]["input"]
    assert [p["input"] for p in four["train"] + four["test"]] == [
        p["input"] for p in other["train"] + other["test"]
    ]
    projected = {"train": four["train"], "test": [{"input": four["test"][0]["input"]}]}
    assert public_challenge_bytes(one) == public_challenge_bytes(projected)


def test_constructed_dependency_and_size_stress_are_real():
    prototype = load_prototype()
    episode = prototype.generate(0, {"axis_policy": "anchor_bbox"}, 2, 4)
    demo_axes = [prototype.scene_facts(pair["input"])["anchor_axis"] for pair in episode["train"]]
    assert demo_axes == ["lr", "ud"]
    assert prototype.transform(episode["train"][0]["input"], {"axis_policy": "vertical"}) != episode["train"][0]["output"]
    stress = episode["test"][-1]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    assert sum(value != 0 for row in stress for value in row) >= 80
    facts = prototype.scene_facts(stress)
    assert facts["unique_anchor"] is True
    assert facts["all_layers_ud_safe"] and facts["all_layers_lr_safe"]


def test_invalid_requests_reject_without_coercion():
    prototype = load_prototype()
    bad_settings = [None, {}, {"axis_policy": "lr"}, {"axis_policy": True}, {"axis_policy": "vertical", "x": 1}]
    for settings in bad_settings:
        with pytest.raises(ValueError):
            prototype.generate(0, settings, 2, 4)
    for seed, demos, queries in [(True, 2, 4), (0, 1, 4), (0, 7, 4), (0, 2, 0), (0, 2, 5)]:
        with pytest.raises(ValueError):
            prototype.generate(seed, {"axis_policy": "vertical"}, demos, queries)
