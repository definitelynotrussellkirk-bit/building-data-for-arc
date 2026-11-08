from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest


REPO = Path(__file__).resolve().parents[3]
HOME = REPO / "generators/2dacb90452ce/workspace/parametric"


def _load(name: str, filename: str):
    path = HOME / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_native_contract_and_default_program_are_exact(monkeypatch):
    monkeypatch.syspath_prepend(str(REPO / "shared/runtime"))
    family = _load("test_2dac_native_family", "native.py")
    adapter = _load("test_2dac_native_adapter", "adapter.py")
    from reviewer_support import canonical_path

    rows = [
        json.loads(line)
        for line in canonical_path(REPO).read_text().splitlines()
        if line.strip()
    ]
    programs = {
        row["program_solution"] for row in rows if row.get("task_id") == family.TASK_ID
    }
    assert programs == {family.program({family.PARAMETER: "fixed_two"})}
    assert adapter.program({family.PARAMETER: "fixed_two"}) == next(iter(programs))

    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/2dacb90452ce/workspace/parametric/adapter.py",
        "parameters": {"scale_policy": ["fixed_two", "modal_parity"]},
        "default": {"scale_policy": "fixed_two"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "resources": [
            "generators/2dacb90452ce/workspace/parametric/native.py",
            "generators/2dacb90452ce/workspace/parametric/canonical.rkt",
            "generators/2dacb90452ce/workspace/parametric/modal_parity.rkt",
        ],
    }


def test_counts_inputs_outputs_and_setting_independence():
    family = _load("test_2dac_native_family_counts", "native.py")
    for seed in (0, 17):
        for demos in (2, 3, 6):
            episodes = {
                setting: family.generate(
                    seed,
                    {family.PARAMETER: setting},
                    demos=demos,
                    queries=4,
                )
                for setting in family.SETTINGS
            }
            left, right = (episodes[setting] for setting in family.SETTINGS)
            assert [p["input"] for p in left["train"] + left["test"]] == [
                p["input"] for p in right["train"] + right["test"]
            ]
            for episode in episodes.values():
                assert len(episode["train"]) == demos
                assert len(episode["test"]) == 4
                serialized = [
                    json.dumps(pair["input"], separators=(",", ":"))
                    for pair in episode["train"] + episode["test"]
                ]
                assert len(serialized) == len(set(serialized))
                for pair in episode["train"] + episode["test"]:
                    assert 1 <= len(pair["input"]) <= 30
                    assert 1 <= len(pair["input"][0]) <= 30
                    assert 1 <= len(pair["output"]) <= 30
                    assert 1 <= len(pair["output"][0]) <= 30
            assert len(right["test"][-1]["input"]) == 10
            assert len(right["test"][-1]["output"]) == 30
            assert len(right["test"][-1]["output"][0]) == 30


def test_minimum_two_demos_identify_setting_and_kill_declared_rivals():
    family = _load("test_2dac_native_family_teaching", "native.py")
    for seed in range(12):
        for setting in family.SETTINGS:
            episode = family.generate(
                seed, {family.PARAMETER: setting}, demos=2, queries=4
            )
            assert family.surviving_rivals(episode["train"], setting) == []
            survivors = []
            for candidate in family.SETTINGS:
                if all(
                    family.apply_rule(pair["input"], candidate) == pair["output"]
                    for pair in episode["train"]
                ):
                    survivors.append(candidate)
            assert survivors == [setting]


def test_modal_count_is_the_real_input_dependent_intermediate():
    family = _load("test_2dac_native_family_dependency", "native.py")
    episode = family.generate(
        17, {family.PARAMETER: "modal_parity"}, demos=2, queries=4
    )
    odd_demo, even_demo = episode["train"]
    odd_info = family.modal_summary(odd_demo["input"])
    even_info = family.modal_summary(even_demo["input"])
    assert odd_info["count"] % 2 == 1
    assert even_info["count"] % 2 == 0
    assert family.scale_factor(odd_demo["input"], "modal_parity") == 3
    assert family.scale_factor(even_demo["input"], "modal_parity") == 2
    assert len(odd_demo["output"]) == 3 * len(odd_demo["input"])
    assert len(even_demo["output"]) == 2 * len(even_demo["input"])


def test_demo_prefix_and_query_bank_are_stable():
    family = _load("test_2dac_native_family_prefix", "native.py")
    for setting in family.SETTINGS:
        short = family.generate(5, {family.PARAMETER: setting}, 2, 4)
        long = family.generate(5, {family.PARAMETER: setting}, 6, 4)
        assert short["train"] == long["train"][:2]
        assert short["test"] == long["test"]


@pytest.mark.parametrize(
    "args",
    [
        (-1, {"scale_policy": "fixed_two"}, 2, 4),
        (0, {"scale_policy": "fixed_two"}, 1, 4),
        (0, {"scale_policy": "fixed_two"}, 7, 4),
        (0, {"scale_policy": "fixed_two"}, 2, 3),
        (0, {"scale_policy": "fixed_two"}, 2, 5),
        (0, {"scale_policy": "unknown"}, 2, 4),
        (0, {"extra": "fixed_two"}, 2, 4),
    ],
)
def test_invalid_requests_reject(args):
    family = _load("test_2dac_native_family_invalid_" + str(abs(hash(repr(args)))), "native.py")
    with pytest.raises((TypeError, ValueError)):
        family.generate(*args)
