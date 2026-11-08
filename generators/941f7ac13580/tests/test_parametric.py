from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random

import pytest
from arcpuzzles.catalog import Catalog
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

ROOT = find_root(__file__)
TASK_ID = "941f7ac13580"
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
SETTINGS = ({"sequence_origin": "top_left"}, {"sequence_origin": "border_size"})


def _load(name: str = "prototype.py"):
    path = HOME / name
    assert path.is_file(), f"missing parametric source: {path}"
    spec = importlib.util.spec_from_file_location(
        "_parametric_941_" + hashlib.sha256(str(path).encode()).hexdigest(), path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical() -> str:
    return Catalog(ROOT).get(TASK_ID)["variants"][0]["program_solution"]


def test_exact_canonical_default_and_strict_settings() -> None:
    p = _load()
    assert (HOME / "canonical.rkt").read_text(encoding="utf-8") == _canonical()
    assert p.program({"sequence_origin": "top_left"}) == _canonical()
    assert p.DEFAULT == {"sequence_origin": "top_left"}
    with pytest.raises(ValueError):
        p.program({})
    with pytest.raises(ValueError):
        p.program({"sequence_origin": "unknown"})
    with pytest.raises(ValueError):
        p.program({"sequence_origin": "top_left", "extra": 1})


def test_matched_inputs_real_dependency_and_required_query_bank() -> None:
    p = _load()
    state = random.getstate()
    base = p.generate(17, SETTINGS[0], demos=2, queries=4)
    assert random.getstate() == state
    alt = p.generate(17, SETTINGS[1], demos=2, queries=4)
    assert base == p.generate(17, SETTINGS[0], demos=2, queries=4)

    base_inputs = [pair["input"] for pair in base["train"] + base["test"]]
    alt_inputs = [pair["input"] for pair in alt["train"] + alt["test"]]
    assert base_inputs == alt_inputs
    assert len(base["train"]) == 2 and len(base["test"]) == 4
    assert len({json.dumps(grid, separators=(",", ":")) for grid in base_inputs}) == 6
    assert (len(base["test"][-1]["input"]), len(base["test"][-1]["input"][0])) == (30, 30)
    assert sum(cell != 0 for row in base["test"][-1]["input"] for cell in row) >= 20

    for index, grid in enumerate(base_inputs):
        facts = p.scene_facts(grid)
        assert facts["border_object_count"] == 1, index
        assert facts["rotation"] != 0, index
        assert facts["object_count"] >= 3
        expected_base = p.transform(grid, SETTINGS[0])
        expected_alt = p.transform(grid, SETTINGS[1])
        assert expected_base != expected_alt
        assert base["train"] + base["test"]
        split = "train" if index < 2 else "test"
        pair = base[split][index if split == "train" else index - 2]
        alt_pair = alt[split][index if split == "train" else index - 2]
        assert pair["output"] == expected_base
        assert alt_pair["output"] == expected_alt


def test_count_independence_minimum_identification_and_boundaries() -> None:
    p = _load()
    for seed in range(20):
        for setting in SETTINGS:
            episode = p.generate(seed, setting, demos=2, queries=4)
            assert episode["certificate"]["survivors"] == [setting]
            assert all(row["object_count"] >= 3 for row in episode["certificate"]["scenes"])
    maximum = p.generate(99, SETTINGS[1], demos=6, queries=4)
    assert len(maximum["train"]) == 6
    assert len(maximum["test"]) == 4
    with pytest.raises(ValueError):
        p.generate(1, SETTINGS[0], demos=1, queries=4)
    with pytest.raises(ValueError):
        p.generate(1, SETTINGS[0], demos=7, queries=4)
    with pytest.raises(ValueError):
        p.generate(1, SETTINGS[0], demos=2, queries=3)
    with pytest.raises(ValueError):
        p.generate(True, SETTINGS[0], demos=2, queries=4)


def test_thin_adapter_and_private_projection_boundary() -> None:
    p = _load()
    adapter = _load("adapter.py")
    episode = adapter.generate(73, SETTINGS[1], 3, 4)
    assert len(episode["train"]) == 3 and len(episode["test"]) == 4
    assert episode["program_solution"] == p.program(SETTINGS[1])

    visible = public_challenge_bytes(episode)
    decoded = json.loads(visible)
    assert set(decoded) == {"train", "test"}
    assert all(set(pair) == {"input"} for pair in decoded["test"])
    changed = copy.deepcopy(episode)
    changed["settings"] = {"private": "changed"}
    changed["program_solution"] = "changed"
    changed["test"][0]["output"] = [[9]]
    assert public_challenge_bytes(changed) == visible
    assert public_challenge_id(changed) == public_challenge_id(episode)


def test_regression_minimum_lesson_kills_border_rank_and_largest_size_shortcuts() -> None:
    p = _load()
    for seed in range(32):
        for setting in SETTINGS:
            episode = p.generate(seed, setting, demos=2, queries=4)
            shortcuts = episode["certificate"]["shortcut_refutations"]
            assert shortcuts["border_rank"] is True, (seed, setting, shortcuts)
            assert shortcuts["largest_size"] is True, (seed, setting, shortcuts)
            assert shortcuts["sort_by_size"] is True, (seed, setting, shortcuts)
            assert shortcuts["wrong_offset_plus_one"] is True, (seed, setting, shortcuts)
            if setting["sequence_origin"] == "border_size":
                assert shortcuts["fixed_first"] is True, (seed, shortcuts)


def test_certificate_recomputes_and_rejects_malformed_private_payloads() -> None:
    p = _load()
    episode = p.generate(123, SETTINGS[1], demos=2, queries=4)
    forged = copy.deepcopy(episode)
    forged["certificate"] = {"survivors": [SETTINGS[0]], "racket_checked": True}
    assert p.certify(forged)["survivors"] == [SETTINGS[1]]

    duplicate = copy.deepcopy(episode)
    duplicate["test"][0]["input"] = copy.deepcopy(duplicate["train"][0]["input"])
    with pytest.raises(ValueError, match="distinct"):
        p.certify(duplicate)

    wrong = copy.deepcopy(episode)
    wrong["test"][0]["output"] = [[9]]
    with pytest.raises(ValueError, match="label"):
        p.certify(wrong)

    with pytest.raises(ValueError):
        p.transform([[True]], SETTINGS[0])
    with pytest.raises(ValueError):
        p.transform([[0, 1], [0]], SETTINGS[0])
