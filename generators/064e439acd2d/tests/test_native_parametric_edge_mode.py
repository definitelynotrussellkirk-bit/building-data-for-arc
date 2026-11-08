from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK_ID = "064e439acd2d"
ROOT = find_root(__file__)
HERE = ROOT / f"generators/{TASK_ID}/workspace/parametric"


def load_module(filename: str = "prototype.py"):
    path = HERE / filename
    assert path.is_file(), f"missing native source: {path}"
    spec = importlib.util.spec_from_file_location(f"edge_mode_{filename}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical program missing")


def inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_native_program_adapter_and_promotion_contract_are_exact():
    p = load_module()
    adapter = load_module("adapter.py")
    promotion = json.loads((HERE / "promotion.json").read_text(encoding="utf-8"))

    assert p.program({"edge_mode": "near"}) == canonical_program()
    assert adapter.program({"edge_mode": "near"}) == canonical_program()
    assert p.program({"edge_mode": "far"}) != canonical_program()
    assert promotion == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"edge_mode": ["near", "far"]},
        "default": {"edge_mode": "near"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
        ],
    }


def test_generation_is_prefix_stable_matched_and_has_four_real_queries():
    p = load_module()
    near2 = p.generate(29, {"edge_mode": "near"}, demos=2, queries=4)
    near6 = p.generate(29, {"edge_mode": "near"}, demos=6, queries=4)
    far6 = p.generate(29, {"edge_mode": "far"}, demos=6, queries=4)
    one_query = p.generate(29, {"edge_mode": "near"}, demos=6, queries=1)

    assert near2["train"] == near6["train"][:2]
    assert one_query["train"] == near6["train"]
    assert one_query["test"] == near6["test"][:1]
    assert inputs(near6) == inputs(far6)
    assert [pair["output"] for pair in near6["train"]] != [
        pair["output"] for pair in far6["train"]
    ]

    query_shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in near6["test"]]
    assert query_shapes == [(12, 15), (18, 20), (24, 27), (30, 30)]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs(near6)}) == 10

    stress = near6["test"][3]
    changed = sum(
        before != after
        for in_row, out_row in zip(stress["input"], stress["output"])
        for before, after in zip(in_row, out_row)
    )
    nonzero = sum(cell != 0 for row in stress["input"] for cell in row)
    assert changed >= 16
    assert nonzero >= 250


def test_two_demos_identify_setting_and_refute_declared_shortcuts():
    p = load_module()
    for setting in p.SETTINGS:
        episode = p.generate(17, setting, demos=2, queries=4)
        certificate = episode["certificate"]
        assert certificate["survivors"] == [setting]
        assert certificate["all_declared_rivals_refuted"] is True
        assert all(index in (0, 1) for index in certificate["rival_first_refutation"].values())
        assert all(query["selected_rule_matches"] for query in certificate["queries"])


def test_strict_validation_rejects_malformed_settings_counts_and_cells():
    p = load_module()
    for settings in ({}, {"edge_mode": "middle"}, {"edge_mode": True}, {"edge_mode": "near", "x": 1}):
        with pytest.raises(ValueError):
            p.program(settings)
    for kwargs in (
        {"seed": True, "settings": p.DEFAULT, "demos": 3, "queries": 4},
        {"seed": 0, "settings": p.DEFAULT, "demos": 1, "queries": 4},
        {"seed": 0, "settings": p.DEFAULT, "demos": 7, "queries": 4},
        {"seed": 0, "settings": p.DEFAULT, "demos": 3, "queries": 0},
        {"seed": 0, "settings": p.DEFAULT, "demos": 3, "queries": 5},
    ):
        with pytest.raises(ValueError):
            p.generate(**kwargs)
    for grid in ([], [[]], [[True]], [[0], [0, 1]], [[10]]):
        with pytest.raises(ValueError):
            p.transform(grid, p.DEFAULT)


def test_first_public_turn_has_no_private_or_future_query_dependence():
    p = load_module()
    episode = p.generate(73, {"edge_mode": "far"}, demos=3, queries=4)
    first = p.public_turn_bytes(episode, 0)
    visible = json.loads(first)
    assert set(visible) == {"train", "test"}
    assert len(visible["test"]) == 1
    assert visible["test"][0] == {"input": episode["test"][0]["input"]}
    assert first == public_challenge_bytes({"train": episode["train"], "test": episode["test"][:1]})

    changed = copy.deepcopy(episode)
    changed["settings"] = {"private": "changed"}
    changed["program_solution"] = "changed"
    changed["test"][0]["output"] = [[9]]
    changed["test"][3]["input"] = [[9]]
    assert p.public_turn_bytes(changed, 0) == first
    with pytest.raises(ValueError):
        p.public_turn_bytes(episode, -1)
    with pytest.raises(ValueError):
        p.public_turn_bytes(episode, 4)
