from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1]
PARAM = HOME / "workspace" / "parametric"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _modules():
    assert (PARAM / "prototype.py").is_file()
    assert (PARAM / "adapter.py").is_file()
    return (
        _load("_motion_prototype_test", PARAM / "prototype.py"),
        _load("_motion_adapter_test", PARAM / "adapter.py"),
    )


def _freeze(grid):
    return tuple(map(tuple, grid))


def test_parametric_sources_and_contract_exist():
    expected = {
        "adapter.py",
        "canonical.rkt",
        "complement_to_largest.rkt",
        "promotion.json",
        "prototype.py",
    }
    assert expected <= {path.name for path in PARAM.iterdir() if path.is_file()}
    contract = json.loads((PARAM / "promotion.json").read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/483682b75e12/workspace/parametric/adapter.py",
        "parameters": {"motion_mode": ["own_size", "complement_to_largest"]},
        "default": {"motion_mode": "own_size"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            "generators/483682b75e12/workspace/parametric/canonical.rkt",
            "generators/483682b75e12/workspace/parametric/complement_to_largest.rkt",
        ],
    }


def test_programs_are_stable_and_settings_fail_closed():
    _, adapter = _modules()
    canonical = (PARAM / "canonical.rkt").read_text()
    alternate = (PARAM / "complement_to_largest.rkt").read_text()
    assert adapter.program({"motion_mode": "own_size"}) == canonical
    assert adapter.program({"motion_mode": "complement_to_largest"}) == alternate
    assert canonical != alternate
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "1ecd0b9f4b26f707a759a230df287a997b214b82103aad8d3ba3db4a3d582e3f"
    )
    for bad in ({}, {"motion_mode": "unknown"}, {"motion_mode": "own_size", "x": 1}, None):
        with pytest.raises(ValueError):
            adapter.program(bad)


def test_hand_checked_global_intermediate_changes_each_component_shift():
    prototype, _ = _modules()
    grid = [[7] * 9 for _ in range(9)]
    grid[-1] = [8] * 9
    grid[4][1] = 1
    grid[5][4] = 2
    grid[5][5] = 3
    grid[6][4] = 2
    grid[6][5] = 3

    own = prototype.transform(grid, "own_size")
    complement = prototype.transform(grid, "complement_to_largest")

    assert own[3][1] == 1
    assert own[1][4:6] == [2, 3]
    assert own[2][4:6] == [2, 3]
    assert complement[0][1] == 1
    assert complement[4][4:6] == [2, 3]
    assert complement[5][4:6] == [2, 3]
    assert own != complement


def test_generation_is_matched_deterministic_prefix_stable_and_distinct():
    _, adapter = _modules()
    settings = [
        {"motion_mode": "own_size"},
        {"motion_mode": "complement_to_largest"},
    ]
    episodes = [adapter.generate(17, setting, 6, 4) for setting in settings]
    assert [[p["input"] for p in episodes[0][split]] for split in ("train", "test")] == [
        [p["input"] for p in episodes[1][split]] for split in ("train", "test")
    ]
    assert episodes[0] == adapter.generate(17, settings[0], 6, 4)
    short = adapter.generate(17, settings[0], 2, 1)
    assert short["train"] == episodes[0]["train"][:2]
    assert short["test"] == episodes[0]["test"][:1]
    all_inputs = [pair["input"] for split in ("train", "test") for pair in episodes[0][split]]
    assert len({_freeze(grid) for grid in all_inputs}) == 10


def test_minimum_lesson_identifies_setting_and_declared_shortcuts():
    prototype, adapter = _modules()
    for seed in range(24):
        for mode in prototype.MODES:
            episode = adapter.generate(seed, {"motion_mode": mode}, 2, 4)
            certificate = prototype.lesson_certificate(episode, mode)
            assert certificate["setting_survivors"] == [mode]
            assert certificate["rival_survivors"] == []
            assert certificate["query_disagreements"] == len(episode["test"])


def test_supported_count_boundaries_and_labels():
    prototype, adapter = _modules()
    for demos in range(2, 7):
        for queries in range(1, 5):
            for mode in prototype.MODES:
                episode = adapter.generate(31, {"motion_mode": mode}, demos, queries)
                assert len(episode["train"]) == demos
                assert len(episode["test"]) == queries
                assert episode["program_solution"] == adapter.program({"motion_mode": mode})
                for split in ("train", "test"):
                    for pair in episode[split]:
                        assert pair["output"] == prototype.transform(pair["input"], mode)
    for demos, queries in ((1, 1), (7, 1), (2, 0), (2, 5)):
        with pytest.raises(ValueError):
            adapter.generate(0, {"motion_mode": "own_size"}, demos, queries)


def test_fourth_query_is_substantive_30_by_30_boundary_stress():
    prototype, adapter = _modules()
    episode = adapter.generate(0, {"motion_mode": "complement_to_largest"}, 3, 4)
    grid = episode["test"][3]["input"]
    facts = prototype.scene_facts(grid)
    assert (len(grid), len(grid[0])) == (30, 30)
    assert len(facts["components"]) >= 10
    assert set(facts["sizes"]) >= {1, 2, 3, 4, 5, 6}
    occupied = [(r, c) for r, row in enumerate(grid[:-1]) for c, value in enumerate(row) if value not in (7, 8)]
    assert min(r for r, _ in occupied) <= 6
    assert max(r for r, _ in occupied) >= 26
    assert min(c for _, c in occupied) == 0
    assert max(c for _, c in occupied) == 29
    assert len({r for r, _ in occupied}) >= 18
    assert len({c for _, c in occupied}) >= 20


def test_transform_rejects_malformed_or_unsafe_inputs():
    prototype, _ = _modules()
    for grid in ([], [[]], [[7, 7], [8]], [[7] * 7 for _ in range(7)]):
        with pytest.raises(ValueError):
            prototype.transform(grid, "own_size")
    too_high = [[7] * 8 for _ in range(8)]
    too_high[-1] = [8] * 8
    too_high[0][1] = 1
    with pytest.raises(ValueError):
        prototype.transform(too_high, "complement_to_largest")
