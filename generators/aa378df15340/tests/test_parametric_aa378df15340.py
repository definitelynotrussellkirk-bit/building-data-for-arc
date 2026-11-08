from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAM = HOME / "workspace" / "parametric"


def load_module(name: str, filename: str):
    path = PARAM / filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


family = load_module("aa378_parametric_family", "native_family.py")
adapter = load_module("aa378_parametric_adapter", "adapter.py")


def inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_exact_canonical_bytes():
    expected = (PARAM / "canonical.rkt").read_text()
    assert family.program({"mode": "copy_only"}) == expected
    assert adapter.program({"mode": "copy_only"}) == expected


def test_rejects_malformed_settings_and_counts():
    for bad in ({}, {"mode": "unknown"}, {"mode": 1}, {"mode": "copy_only", "x": 1}):
        with pytest.raises(ValueError):
            family.program(bad)
    for kwargs in ({"demos": 1}, {"demos": 7}, {"queries": 0}, {"queries": 5}):
        with pytest.raises(ValueError):
            family.generate(0, {"mode": "copy_only"}, kwargs.get("demos", 3), kwargs.get("queries", 4))


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
def test_counts_are_independent_deterministic_and_inputs_are_distinct(demos, queries):
    episode = family.generate(17, {"mode": "copy_then_bridge"}, demos, queries)
    assert episode == family.generate(17, {"mode": "copy_then_bridge"}, demos, queries)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    keys = [tuple(map(tuple, grid)) for grid in inputs(episode)]
    assert len(keys) == len(set(keys))


def test_settings_use_matched_inputs_and_every_pair_distinguishes_them():
    canonical = family.generate(29, {"mode": "copy_only"}, 6, 4)
    sequential = family.generate(29, {"mode": "copy_then_bridge"}, 6, 4)
    assert inputs(canonical) == inputs(sequential)
    for c_pair, s_pair in zip(canonical["train"] + canonical["test"], sequential["train"] + sequential["test"]):
        assert c_pair["output"] == family.copy_only(c_pair["input"])
        assert s_pair["output"] == family.copy_then_bridge(s_pair["input"])
        assert c_pair["output"] != s_pair["output"]


def test_bridge_stage_consumes_the_transposed_intermediate():
    grid = family.input_bank(5)[0][0]
    intermediate = family.copy_only(grid)
    final = family.bridge_symmetric_pairs(intermediate)
    skip_a = family.bridge_symmetric_pairs(grid)
    assert final == family.copy_then_bridge(grid)
    assert skip_a == grid
    assert final != skip_a
    assert sum(v != 0 for row in final for v in row) > sum(v != 0 for row in intermediate for v in row)


def test_bank_contains_substantive_30_by_30_boundary_stress():
    _, queries = family.input_bank(11)
    grid = queries[-1]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert any(grid[0][c] for c in range(30))
    assert any(grid[29][c] for c in range(30))
    assert any(grid[r][0] for r in range(30))
    assert any(grid[r][29] for r in range(30))
    output = family.copy_then_bridge(grid)
    assert sum(v != 0 for row in output for v in row) >= 180


def test_every_scene_contains_a_bridge_longer_than_midpoint_only_can_explain():
    for seed in range(256):
        train, test = family.input_bank(seed)
        for grid in train + test:
            spans = [abs(c - r) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
            assert max(spans) >= 4, (seed, len(grid), spans)
