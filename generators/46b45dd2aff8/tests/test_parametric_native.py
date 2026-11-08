from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

REPO = Path(__file__).resolve().parents[3]
HOME = REPO / "generators/46b45dd2aff8/workspace/parametric"


def _load(name: str, filename: str):
    path = HOME / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_native_contract_and_canonical_default_are_exact(monkeypatch):
    monkeypatch.syspath_prepend(str(REPO / "shared/runtime"))
    family = _load("test_46b_native_contract", "native.py")
    adapter = _load("test_46b_native_adapter", "adapter.py")
    from reviewer_support import canonical_path
    rows = [json.loads(line) for line in canonical_path(REPO).read_text().splitlines() if line.strip()]
    programs = {row["program_solution"] for row in rows if row.get("task_id") == family.TASK_ID}
    assert programs == {family.program({family.PARAMETER: "same_color"})}
    assert adapter.program({family.PARAMETER: "same_color"}) == next(iter(programs))
    assert json.loads((HOME / "promotion.json").read_text()) == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/46b45dd2aff8/workspace/parametric/adapter.py",
        "parameters": {"rectangle_policy": ["same_color", "nearest_aligned"]},
        "default": {"rectangle_policy": "same_color"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "resources": [
            "generators/46b45dd2aff8/workspace/parametric/native.py",
            "generators/46b45dd2aff8/workspace/parametric/canonical.rkt",
            "generators/46b45dd2aff8/workspace/parametric/nearest_aligned.rkt",
        ],
    }


def test_counts_matched_inputs_bounds_and_large_query():
    family = _load("test_46b_native_counts", "native.py")
    for seed in (0, 17):
        for demos in (2, 3, 6):
            episodes = {s: family.generate(seed, {family.PARAMETER: s}, demos, 4) for s in family.SETTINGS}
            same, nearest = (episodes[s] for s in family.SETTINGS)
            assert [p["input"] for p in same["train"] + same["test"]] == [p["input"] for p in nearest["train"] + nearest["test"]]
            for episode in episodes.values():
                assert len(episode["train"]) == demos
                assert len(episode["test"]) == 4
                encoded = [json.dumps(p["input"], separators=(",", ":")) for p in episode["train"] + episode["test"]]
                assert len(encoded) == len(set(encoded))
                for pair in episode["train"] + episode["test"]:
                    assert 13 <= len(pair["input"]) <= 30
                    assert 13 <= len(pair["input"][0]) <= 30
                    assert len(pair["output"]) == len(pair["input"])
                    assert len(pair["output"][0]) == len(pair["input"][0])
            assert len(nearest["test"][-1]["input"]) == 30
            assert len(nearest["test"][-1]["input"][0]) == 30


def test_two_demos_identify_setting_and_refute_declared_rivals():
    family = _load("test_46b_native_teaching", "native.py")
    for seed in range(16):
        for setting in family.SETTINGS:
            episode = family.generate(seed, {family.PARAMETER: setting}, 2, 4)
            assert family.surviving_rivals(episode["train"], setting) == []
            compatible = [c for c in family.SETTINGS if all(family.apply_rule(p["input"], c) == p["output"] for p in episode["train"])]
            assert compatible == [setting]


def test_selection_mapping_is_the_input_dependent_intermediate():
    family = _load("test_46b_native_dependency", "native.py")
    episode = family.generate(3, {family.PARAMETER: "nearest_aligned"}, 2, 4)
    grid = episode["train"][0]["input"]
    same = family.selection_records(grid, "same_color")
    nearest = family.selection_records(grid, "nearest_aligned")
    assert same and nearest and len(same) == len(nearest)
    assert any(a["rectangle_color"] != b["rectangle_color"] for a, b in zip(same, nearest))
    assert family.apply_rule(grid, "nearest_aligned") == family.generator_nearest_rule(grid)
    assert family.apply_rule(grid, "same_color") != family.apply_rule(grid, "nearest_aligned")


def test_prefix_stability_and_four_query_bank():
    family = _load("test_46b_native_prefix", "native.py")
    for setting in family.SETTINGS:
        short = family.generate(9, {family.PARAMETER: setting}, 2, 4)
        long = family.generate(9, {family.PARAMETER: setting}, 6, 4)
        assert short["train"] == long["train"][:2]
        assert short["test"] == long["test"]


@pytest.mark.parametrize("args", [
    (-1, {"rectangle_policy": "same_color"}, 2, 4),
    (0, {"rectangle_policy": "same_color"}, 1, 4),
    (0, {"rectangle_policy": "same_color"}, 7, 4),
    (0, {"rectangle_policy": "same_color"}, 2, 3),
    (0, {"rectangle_policy": "same_color"}, 2, 5),
    (0, {"rectangle_policy": "unknown"}, 2, 4),
    (0, {"extra": "same_color"}, 2, 4),
    (True, {"rectangle_policy": "same_color"}, 2, 4),
])
def test_invalid_requests_reject(args):
    family = _load("test_46b_native_invalid_" + str(abs(hash(repr(args)))), "native.py")
    with pytest.raises((TypeError, ValueError)):
        family.generate(*args)
