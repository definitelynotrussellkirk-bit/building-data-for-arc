from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id


TASK_ID = "083ba0fc4534"
TASK_DIR = Path(__file__).resolve().parents[1]
PARAMETRIC_DIR = TASK_DIR / "workspace" / "parametric"


def _load(name: str):
    path = PARAMETRIC_DIR / f"{name}.py"
    assert path.is_file(), f"missing {path}"
    spec = importlib.util.spec_from_file_location(f"test_{TASK_ID}_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    root = find_root(__file__)
    programs = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    programs.add(row["program_solution"])
    assert len(programs) == 1
    return next(iter(programs))


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_adapter_and_contract_exist_with_exact_canonical_default():
    adapter = _load("adapter")
    contract = json.loads((PARAMETRIC_DIR / "promotion.json").read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"agreement": ["majority", "unanimous"]},
        "default": {"agreement": "majority"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
    }
    assert adapter.program({"agreement": "majority"}) == _canonical_program()
    assert adapter.program({"agreement": "unanimous"}) != _canonical_program()


def test_counts_settings_and_scalar_types_are_strict():
    adapter = _load("adapter")
    for bad in ({}, {"agreement": "majority", "extra": 1}, {"agreement": "plurality"}):
        with pytest.raises(ValueError):
            adapter.program(bad)
    for demos, queries in ((1, 4), (7, 4), (True, 4), (3, 3), (3, 5), (3, True)):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(1, {"agreement": "majority"}, demos, queries)
    with pytest.raises(TypeError):
        adapter.generate(True, {"agreement": "majority"}, 3, 4)


def test_inputs_are_setting_independent_distinct_and_labels_change():
    adapter = _load("adapter")
    majority = adapter.generate(23, {"agreement": "majority"}, 3, 4)
    unanimous = adapter.generate(23, {"agreement": "unanimous"}, 3, 4)
    assert _inputs(majority) == _inputs(unanimous)
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(majority)]
    assert len(serialized) == len(set(serialized)) == 7
    assert any(
        left["output"] != right["output"]
        for left, right in zip(
            majority["train"] + majority["test"],
            unanimous["train"] + unanimous["test"],
            strict=True,
        )
    )
    assert majority["program_solution"] == adapter.program({"agreement": "majority"})
    assert unanimous["program_solution"] == adapter.program({"agreement": "unanimous"})


def test_minimum_and_maximum_demo_counts_keep_four_queries_and_large_stress():
    adapter = _load("adapter")
    prototype = _load("prototype")
    for demos in (2, 6):
        episode = adapter.generate(41 + demos, {"agreement": "majority"}, demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
        assert shapes == [(5, 14), (12, 20), (21, 26), (30, 29)]
        largest = episode["test"][-1]["input"]
        metrics = prototype.input_metrics(largest)
        assert metrics["panel_width"] == 9
        assert metrics["active_local_positions"] >= 70
        assert metrics["active_boundary_sides"] == ["bottom", "left", "right", "top"]
        assert {"ab", "ax", "bx", "abc", "conflict", "singleton"} <= set(
            metrics["pattern_counts"]
        )


def test_every_demonstration_constructively_identifies_the_setting():
    adapter = _load("adapter")
    prototype = _load("prototype")
    for agreement in ("majority", "unanimous"):
        episode = adapter.generate(57, {"agreement": agreement}, 2, 4)
        rival = "unanimous" if agreement == "majority" else "majority"
        for pair in episode["train"]:
            metrics = prototype.input_metrics(pair["input"])
            assert metrics["pattern_counts"]["abc"] >= 1
            assert sum(metrics["pattern_counts"][name] for name in ("ab", "ax", "bx")) >= 1
            assert prototype.solve(pair["input"], agreement) == pair["output"]
            assert prototype.solve(pair["input"], rival) != pair["output"]


def test_public_projection_hides_private_data_and_first_turn_is_count_agnostic():
    adapter = _load("adapter")
    prototype = _load("prototype")
    episode = adapter.generate(71, {"agreement": "majority"}, 3, 4)
    public = {"train": episode["train"], "test": episode["test"]}
    raw = public_challenge_bytes(public)
    assert public_challenge_id(public) == hashlib.sha256(raw).hexdigest()
    parsed = json.loads(raw)
    assert all(set(pair) == {"input"} for pair in parsed["test"])
    assert b"program_solution" not in raw
    assert b"agreement" not in raw
    assert b"majority" not in raw

    changed_private = copy.deepcopy(public)
    changed_private["test"][0]["output"][0][0] = (
        changed_private["test"][0]["output"][0][0] + 1
    ) % 10
    assert public_challenge_id(changed_private) == public_challenge_id(public)

    turn = prototype.public_turn(episode, 0)
    assert public_challenge_bytes(turn) == public_challenge_bytes(
        {"train": episode["train"], "test": [episode["test"][0]]}
    )
    assert set(turn) == {"train", "test"}
    assert len(turn["test"]) == 1 and set(turn["test"][0]) == {"input"}


def test_generation_is_deterministic_fresh_and_seed_type_is_exact():
    adapter = _load("adapter")
    first = adapter.generate(89, {"agreement": "unanimous"}, 3, 4)
    second = adapter.generate(89, {"agreement": "unanimous"}, 3, 4)
    assert first == second
    assert first is not second
    first["train"][0]["input"][0][0] = 9
    assert adapter.generate(89, {"agreement": "unanimous"}, 3, 4) == second
