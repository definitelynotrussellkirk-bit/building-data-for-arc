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


family = load_module("a2b78_parametric_family", "native_family.py")
adapter = load_module("a2b78_parametric_adapter", "adapter.py")


def inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_exact_canonical_bytes():
    expected = (PARAM / "canonical.rkt").read_text()
    assert family.program({"mode": "scan_only"}) == expected
    assert adapter.program({"mode": "scan_only"}) == expected


def test_rejects_malformed_settings_and_counts():
    for bad in ({}, {"mode": "unknown"}, {"mode": 1}, {"mode": "scan_only", "x": 1}):
        with pytest.raises(ValueError):
            family.program(bad)
    for demos, queries in ((1, 4), (7, 4), (3, 0), (3, 5)):
        with pytest.raises(ValueError):
            family.generate(0, {"mode": "scan_only"}, demos, queries)


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
def test_counts_are_independent_deterministic_and_inputs_are_distinct(demos, queries):
    episode = family.generate(17, {"mode": "scan_then_rle"}, demos, queries)
    assert episode == family.generate(17, {"mode": "scan_then_rle"}, demos, queries)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    keys = [tuple(map(tuple, grid)) for grid in inputs(episode)]
    assert len(keys) == len(set(keys))


def test_settings_use_matched_inputs_and_every_pair_distinguishes_them():
    canonical = family.generate(29, {"mode": "scan_only"}, 6, 4)
    sequential = family.generate(29, {"mode": "scan_then_rle"}, 6, 4)
    assert inputs(canonical) == inputs(sequential)
    for c_pair, s_pair in zip(canonical["train"] + canonical["test"], sequential["train"] + sequential["test"]):
        assert c_pair["output"] == family.scan_only(c_pair["input"])
        assert s_pair["output"] == family.scan_then_rle(s_pair["input"])
        assert c_pair["output"] != s_pair["output"]


def test_rle_stage_consumes_scan_order_intermediate_and_wrong_order_changes_it():
    grid = family.input_bank(5)[0][0]
    sequence = family.scan_only(grid)[0]
    final = family.rle_row(sequence)
    wrong_intermediate = family.rle_row(list(reversed(sequence)))
    assert final == family.scan_then_rle(grid)
    assert final != wrong_intermediate
    assert len(final) == 2
    assert len(final[0]) == len(final[1])
    assert sum(final[1]) == len(sequence)


def test_bank_contains_substantive_30_by_30_boundary_stress():
    _, queries = family.input_bank(11)
    grid = queries[-1]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert any(grid[0][c] for c in range(30))
    assert any(grid[29][c] for c in range(30))
    assert any(grid[r][0] for r in range(30))
    assert any(grid[r][29] for r in range(30))
    sequence = family.scan_only(grid)[0]
    assert 20 <= len(sequence) <= 30
    assert max(family.rle_row(sequence)[1]) <= 9


def test_demonstrations_separate_run_length_encoding_from_global_histogram():
    episode = family.generate(41, {"mode": "scan_then_rle"}, 2, 4)
    for pair in episode["train"]:
        run_colors = pair["output"][0]
        assert len(run_colors) > len(set(run_colors))
        sequence = family.scan_only(pair["input"])[0]
        first_order = []
        totals = {}
        for value in sequence:
            if value not in totals:
                first_order.append(value)
                totals[value] = 0
            totals[value] += 1
        histogram = [first_order, [totals[value] for value in first_order]]
        assert histogram != pair["output"]
