"""Native admission tests for the anchor-color family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "2c1567aea733"
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1]
ADAPTER_PATH = HOME / "workspace" / "parametric" / "adapter.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    rows = [
        json.loads(line)
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    matches = [row["program_solution"] for row in rows if row.get("task_id") == TASK_ID]
    assert len(matches) == 1
    return matches[0]


def test_native_adapter_preserves_exact_canonical_program_and_rejects_bad_settings():
    assert ADAPTER_PATH.is_file()
    adapter = _load(ADAPTER_PATH, "native_2c1567aea733_adapter")
    assert adapter.program({"anchor_color": 1}) == _canonical_program()
    assert adapter.program({"anchor_color": 2}) != _canonical_program()
    assert adapter.program({"anchor_color": 4}) != _canonical_program()
    for bad in (None, {}, {"anchor_color": 3}, {"anchor_color": True}, {"anchor_color": 1, "x": 2}):
        with pytest.raises((TypeError, ValueError)):
            adapter.program(bad)


def _keys(episode):
    return [
        json.dumps(pair["input"], separators=(",", ":"))
        for split in ("train", "test")
        for pair in episode[split]
    ]


def test_native_counts_are_independent_prefix_stable_and_inputs_match_across_settings():
    adapter = _load(ADAPTER_PATH, "native_2c1567aea733_counts")
    settings = [{"anchor_color": color} for color in (1, 2, 4)]
    full = [adapter.generate(17, value, demos=6, queries=4) for value in settings]
    assert [_keys(row) for row in full][0] == [_keys(row) for row in full][1] == [_keys(row) for row in full][2]
    assert len(set(_keys(full[0]))) == 10
    for value, complete in zip(settings, full, strict=True):
        for demos in (2, 3, 5):
            short = adapter.generate(17, value, demos=demos, queries=4)
            assert short["train"] == complete["train"][:demos]
            assert short["test"] == complete["test"]
        for queries in (1, 2, 3):
            short = adapter.generate(17, value, demos=6, queries=queries)
            assert short["train"] == complete["train"]
            assert short["test"] == complete["test"][:queries]


def test_native_first_two_demonstrations_refute_other_anchors_and_rank_shortcuts():
    adapter = _load(ADAPTER_PATH, "native_2c1567aea733_teaching")
    prototype = _load(HOME / "workspace" / "parametric" / "prototype.py", "native_2c1567aea733_prototype")
    rivals = ("highest_top", "median_top", "lowest_top", "mean_top", "identity")
    for seed in (0, 17, 31):
        for color in (1, 2, 4):
            episode = adapter.generate(seed, {"anchor_color": color}, demos=2, queries=4)
            for other in ({1, 2, 4} - {color}):
                assert any(
                    prototype.apply_python(pair["input"], other) != pair["output"]
                    for pair in episode["train"]
                )
            for rival in rivals:
                assert any(
                    prototype.native_rival_output(pair["input"], rival) != pair["output"]
                    for pair in episode["train"]
                ), (seed, color, rival)
                assert any(
                    prototype.native_rival_output(pair["input"], rival) != pair["output"]
                    for pair in episode["test"]
                ), (seed, color, rival)


def test_native_fourth_query_is_substantive_boundary_spanning_30x30():
    adapter = _load(ADAPTER_PATH, "native_2c1567aea733_large")
    for color in (1, 2, 4):
        grid = adapter.generate(17, {"anchor_color": color}, demos=3, queries=4)["test"][3]["input"]
        assert (len(grid), len(grid[0])) == (30, 30)
        occupied = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
        assert len(occupied) >= 45
        assert {min(r for r, _ in occupied), max(r for r, _ in occupied)} == {0, 29}
        assert {min(c for _, c in occupied), max(c for _, c in occupied)} == {0, 29}
        assert {value for row in grid for value in row} == {0, 1, 2, 4}


def test_native_rejects_invalid_requests_and_returns_fresh_data():
    adapter = _load(ADAPTER_PATH, "native_2c1567aea733_validation")
    valid = {"seed": 17, "settings": {"anchor_color": 1}, "demos": 3, "queries": 4}
    for field, values in {
        "seed": (-1, 2**63, True, 1.5, "17"),
        "demos": (1, 7, True, 3.0, "3"),
        "queries": (0, 5, True, 1.0, "1"),
    }.items():
        for value in values:
            with pytest.raises((TypeError, ValueError)):
                adapter.generate(**{**valid, field: value})
    first = adapter.generate(**valid)
    second = adapter.generate(**valid)
    assert first == second and first is not second
    first["train"][0]["input"][0][0] = 9
    assert adapter.generate(**valid) == second
