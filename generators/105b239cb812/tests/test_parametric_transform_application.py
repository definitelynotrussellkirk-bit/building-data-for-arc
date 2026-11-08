from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id


TASK_ID = "105b239cb812"
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
        "parameters": {"application": ["direct", "inverse"]},
        "default": {"application": "direct"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
    }
    assert adapter.program({"application": "direct"}) == _canonical_program()
    inverse = adapter.program({"application": "inverse"})
    assert inverse != _canonical_program()
    assert "inverse-transform-name" in inverse


def test_counts_settings_and_scalar_types_are_strict():
    adapter = _load("adapter")
    for bad in ({}, {"application": "direct", "extra": 1}, {"application": "sideways"}):
        with pytest.raises(ValueError):
            adapter.program(bad)
    for demos, queries in ((1, 4), (7, 4), (True, 4), (3, 3), (3, 5), (3, True)):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(1, {"application": "direct"}, demos, queries)
    with pytest.raises(TypeError):
        adapter.generate(True, {"application": "direct"}, 3, 4)


def test_inputs_are_setting_independent_distinct_and_labels_change():
    adapter = _load("adapter")
    direct = adapter.generate(23, {"application": "direct"}, 3, 4)
    inverse = adapter.generate(23, {"application": "inverse"}, 3, 4)
    assert _inputs(direct) == _inputs(inverse)
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(direct)]
    assert len(serialized) == len(set(serialized)) == 7
    assert any(
        left["output"] != right["output"]
        for left, right in zip(
            direct["train"] + direct["test"],
            inverse["train"] + inverse["test"],
            strict=True,
        )
    )
    assert direct["program_solution"] == adapter.program({"application": "direct"})
    assert inverse["program_solution"] == adapter.program({"application": "inverse"})


def test_minimum_and_maximum_demo_counts_keep_four_queries_and_lawful_maximum_stress():
    adapter = _load("adapter")
    prototype = _load("prototype")
    for demos in (2, 6):
        episode = adapter.generate(41 + demos, {"application": "direct"}, demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
        assert shapes == [(4, 14), (6, 20), (8, 26), (9, 29)]
        largest = episode["test"][-1]["input"]
        metrics = prototype.input_metrics(largest)
        assert metrics["panel_size"] == 9
        assert metrics["input_shape"] == [9, 29]
        assert metrics["panel_a_active"] >= 28
        assert metrics["panel_c_active"] >= 35
        assert metrics["panel_c_boundary_sides"] == ["bottom", "left", "right", "top"]
        assert metrics["all_orbits_unique"] is True


def test_every_demonstration_constructively_identifies_application_setting():
    adapter = _load("adapter")
    prototype = _load("prototype")
    for application in prototype.APPLICATIONS:
        rival = "inverse" if application == "direct" else "direct"
        for demos in range(2, 7):
            episode = adapter.generate(57 + demos, {"application": application}, demos, 4)
            assert all(prototype.infer_transform(pair["input"]) in {"cw", "ccw"} for pair in episode["train"])
            assert all(
                prototype.solve(pair["input"], application) == pair["output"]
                and prototype.solve(pair["input"], rival) != pair["output"]
                for pair in episode["train"]
            )



def _local_crop_rival(prototype, grid, application):
    _panel_a, _panel_b, panel_c = prototype.split_panels(grid)
    inferred = prototype.infer_transform(grid)
    applied = inferred if application == "direct" else prototype.INVERSE_TRANSFORM[inferred]
    occupied = [
        (row, col)
        for row in range(len(panel_c))
        for col in range(len(panel_c))
        if panel_c[row][col] != 0
    ]
    top = min(row for row, _ in occupied)
    bottom = max(row for row, _ in occupied)
    left = min(col for _, col in occupied)
    right = max(col for _, col in occupied)
    crop = [row[left : right + 1] for row in panel_c[top : bottom + 1]]
    transformed = prototype.transform_panel(crop, applied)
    out = [[0 for _ in panel_c] for _ in panel_c]
    for row, values in enumerate(transformed):
        for col, value in enumerate(values):
            if top + row < len(out) and left + col < len(out):
                out[top + row][left + col] = value
    return out


def test_demonstrations_refute_crop_local_transform_shortcut():
    adapter = _load("adapter")
    prototype = _load("prototype")
    for application in prototype.APPLICATIONS:
        episode = adapter.generate(59, {"application": application}, 2, 4)
        assert all(
            _local_crop_rival(prototype, pair["input"], application) != pair["output"]
            for pair in episode["train"]
        )

def test_public_projection_hides_private_data_and_first_turn_is_count_agnostic():
    adapter = _load("adapter")
    prototype = _load("prototype")
    episode = adapter.generate(71, {"application": "direct"}, 3, 4)
    public = {"train": episode["train"], "test": episode["test"]}
    raw = public_challenge_bytes(public)
    assert public_challenge_id(public) == hashlib.sha256(raw).hexdigest()
    parsed = json.loads(raw)
    assert all(set(pair) == {"input"} for pair in parsed["test"])
    assert b"program_solution" not in raw
    assert b"application" not in raw
    assert b"direct" not in raw

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
    first = adapter.generate(89, {"application": "inverse"}, 3, 4)
    second = adapter.generate(89, {"application": "inverse"}, 3, 4)
    assert first == second
    assert first is not second
    first["train"][0]["input"][0][0] = 9
    assert adapter.generate(89, {"application": "inverse"}, 3, 4) == second
