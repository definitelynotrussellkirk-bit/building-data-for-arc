from __future__ import annotations

import importlib.util
import json

import pytest

from arcpuzzles import Catalog
from reviewer_support import find_root, public_challenge_bytes


TASK_ID = "e777125624ca"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def load_prototype():
    path = PARAMETRIC / "prototype.py"
    assert path.is_file(), "native prototype is missing"
    spec = importlib.util.spec_from_file_location("_test_e777_parametric", path)
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
    contract = json.loads((PARAMETRIC / "promotion.json").read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"rule_mode": ["nor", "sparser_difference"]},
        "default": {"rule_mode": "nor"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/nor.rkt",
            f"generators/{TASK_ID}/workspace/parametric/sparser_difference.rkt",
        ],
    }
    assert prototype.program({"rule_mode": "nor"}) == canonical_program()
    assert (PARAMETRIC / "nor.rkt").read_bytes() == canonical_program().encode()
    alternate = prototype.program({"rule_mode": "sparser_difference"})
    assert alternate != canonical_program()
    assert "left-count" in alternate
    assert "right-count" in alternate
    assert "sparser" in alternate


@pytest.mark.parametrize("setting", ["nor", "sparser_difference"])
@pytest.mark.parametrize("demos", range(2, 7))
def test_every_supported_count_is_deterministic_distinct_and_teachable(setting, demos):
    prototype = load_prototype()
    settings = {"rule_mode": setting}
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


@pytest.mark.parametrize("setting", ["nor", "sparser_difference"])
def test_inputs_are_setting_independent_and_count_prefix_stable(setting):
    prototype = load_prototype()
    one = prototype.generate(91, {"rule_mode": setting}, 2, 1)
    four = prototype.generate(91, {"rule_mode": setting}, 2, 4)
    other = prototype.generate(
        91,
        {"rule_mode": "sparser_difference" if setting == "nor" else "nor"},
        2,
        4,
    )
    assert [pair["input"] for pair in one["train"]] == [
        pair["input"] for pair in four["train"]
    ]
    assert one["test"][0]["input"] == four["test"][0]["input"]
    assert [pair["input"] for pair in four["train"] + four["test"]] == [
        pair["input"] for pair in other["train"] + other["test"]
    ]
    projected = {"train": four["train"], "test": [{"input": four["test"][0]["input"]}]}
    assert public_challenge_bytes(one) == public_challenge_bytes(projected)


def test_constructed_dependency_and_domain_maximum_are_real():
    prototype = load_prototype()
    episode = prototype.generate(0, {"rule_mode": "sparser_difference"}, 2, 4)
    demo_sides = [prototype.scene_facts(pair["input"])["sparser"] for pair in episode["train"]]
    assert demo_sides == ["left", "right"]
    assert all(
        prototype.transform(pair["input"], {"rule_mode": "nor"}) != pair["output"]
        for pair in episode["train"]
    )
    stress = episode["test"][-1]["input"]
    assert (len(stress), len(stress[0])) == (30, 7)
    assert sum(value != 0 for row in stress for value in row) >= 100
    facts = prototype.scene_facts(stress)
    assert all(facts["state_counts"][state] > 0 for state in ("00", "10", "01", "11"))
    assert facts["left_count"] != facts["right_count"]


def test_invalid_requests_reject_without_coercion():
    prototype = load_prototype()
    bad_settings = [
        None,
        {},
        {"rule_mode": "xor"},
        {"rule_mode": True},
        {"rule_mode": "nor", "x": 1},
    ]
    for settings in bad_settings:
        with pytest.raises(ValueError):
            prototype.generate(0, settings, 2, 4)
    for seed, demos, queries in [
        (True, 2, 4),
        (0, 1, 4),
        (0, 7, 4),
        (0, 2, 0),
        (0, 2, 5),
    ]:
        with pytest.raises(ValueError):
            prototype.generate(seed, {"rule_mode": "nor"}, demos, queries)
