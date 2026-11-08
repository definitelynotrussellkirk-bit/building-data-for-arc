"""Behavioral checks for the expanded stamp-transform native family."""
from __future__ import annotations

from collections import Counter
import importlib.util
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parents[1] / "workspace" / "parametric"


@pytest.fixture(scope="module")
def native():
    spec = importlib.util.spec_from_file_location("native_stamp_family_test", HERE / "prototype.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _coordinates(grid, color):
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}


def _signature(grid):
    green = next(iter(_coordinates(grid, 3)))
    offsets = frozenset((r-green[0], c-green[1]) for r, c in _coordinates(grid, 8))
    return (len(grid), len(grid[0]), green, frozenset(_coordinates(grid, 2)), len(offsets)), offsets


def _multiplicity(grid, setting):
    green = next(iter(_coordinates(grid, 3)))
    offsets = [(r-green[0], (c-green[1]) * (-1 if setting == "mirror_horizontal" else 1))
               for r, c in _coordinates(grid, 8)]
    return Counter((r+dr, c+dc) for r, c in _coordinates(grid, 2) for dr, dc in offsets)


def test_native_api_exposes_same_count_intervention(native):
    assert callable(getattr(native, "generate", None)), "native generation API is absent"
    for seed in (0, 17, 20261024):
        for setting in native.PARAMETER_VALUES:
            episode = native.generate(seed, {"stamp_transform": setting}, demos=2, queries=1)
            a, b = episode["train"]
            a_sig, a_offsets = _signature(a["input"])
            b_sig, b_offsets = _signature(b["input"])
            assert a_sig == b_sig
            assert a_offsets != b_offsets
            assert a["output"] != b["output"]
            assert len(a_sig[3]) >= 2
            for pair in (a, b):
                grid = pair["input"]
                assert native.self_check(grid) == []
                cyans = _coordinates(grid, 8)
                green = next(iter(_coordinates(grid, 3)))
                lo = (min(r for r, c in cyans), min(c for r, c in cyans))
                hi = (max(r for r, c in cyans), max(c for r, c in cyans))
                assert green != lo
                assert (2*green[0], 2*green[1]) != (lo[0]+hi[0], lo[1]+hi[1])
                assert any(abs(r-green[0]) > 1 or abs(c-green[1]) > 1 for r, c in cyans)
                for value in native.PARAMETER_VALUES:
                    multiplicity = _multiplicity(grid, value)
                    assert any(count >= 2 and count % 2 == 0 for count in multiplicity.values())
                    assert not cyans <= set(multiplicity)


def test_request_counts_have_independent_prefixes_and_matched_inputs(native):
    assert callable(getattr(native, "generate", None)), "native generation API is absent"
    full = native.generate(31, {"stamp_transform": "identity"}, demos=6, queries=4)
    mirror = native.generate(31, {"stamp_transform": "mirror_horizontal"}, demos=6, queries=4)
    for split in ("train", "test"):
        assert [p["input"] for p in full[split]] == [p["input"] for p in mirror[split]]
        assert all(a["output"] != b["output"] for a, b in zip(full[split], mirror[split]))
    for demos, queries in ((2, 1), (2, 4), (3, 2), (6, 1)):
        short = native.generate(31, {"stamp_transform": "identity"}, demos=demos, queries=queries)
        assert short["train"] == full["train"][:demos]
        assert short["test"] == full["test"][:queries]
    inputs = [str(p["input"]) for p in full["train"] + full["test"]]
    assert len(set(inputs)) == 10
    assert native.generate(31, {"stamp_transform": "identity"}, demos=6, queries=4) == full


def test_queries_cover_minimum_single_red_and_substantive_maximum(native):
    assert callable(getattr(native, "generate", None)), "native generation API is absent"
    for seed in (0, 17, 20261024):
        episode = native.generate(seed, None)
        assert (len(episode["train"]), len(episode["test"])) == (3, 4)
        queries = episode["test"]
        assert (len(queries[0]["input"]), len(queries[0]["input"][0])) == (8, 8)
        assert any(len(_coordinates(p["input"], 2)) == 1 for p in queries)
        largest = queries[-1]["input"]
        assert (len(largest), len(largest[0])) == (30, 30)
        assert len(_coordinates(largest, 8)) >= 24
        assert len(_coordinates(largest, 2)) >= 10
        for setting in native.PARAMETER_VALUES:
            output = native.reference(largest, {"stamp_transform": setting})
            pixels = _coordinates(output, 8)
            assert len(pixels) >= 150
            assert min(r for r, c in pixels) == 0
            assert max(r for r, c in pixels) == 29
            assert max(c for r, c in pixels) - min(c for r, c in pixels) >= 24
        assert all(native.self_check(pair["input"]) == [] for pair in episode["train"] + queries)


def test_queries_preserve_separated_multiple_destinations(native):
    for seed in (0, 17, 31, 20261024):
        queries = native.generate(seed, None)["test"]
        assert any(len(_coordinates(pair["input"], 2)) >= 2
                   and all(max(_multiplicity(pair["input"], setting).values()) == 1
                           for setting in native.PARAMETER_VALUES)
                   for pair in queries), "queries must include fully separated multiple copies under both settings"


def test_reference_preserves_thin_hole_geometry_and_even_overlaps(native):
    assert callable(getattr(native, "reference", None)), "native reference API is absent"
    grid = [[0]*12 for _ in range(12)]
    grid[2][2] = 3
    for r, c in ((1,1), (1,2), (1,3), (2,1), (2,3), (3,1), (3,2), (3,3), (3,4)):
        grid[r][c] = 8
    grid[7][4] = grid[7][5] = 2
    expected_identity = {
        (6,3), (6,4), (6,5), (6,6), (7,3), (7,4), (7,5), (7,6),
        (8,3), (8,4), (8,5), (8,6), (8,7),
    }
    expected_mirror = {
        (6,3), (6,4), (6,5), (6,6), (7,3), (7,4), (7,5), (7,6),
        (8,2), (8,3), (8,4), (8,5), (8,6),
    }
    assert _coordinates(native.reference(grid, {"stamp_transform":"identity"}), 8) == expected_identity
    assert _coordinates(native.reference(grid, {"stamp_transform":"mirror_horizontal"}), 8) == expected_mirror
    grid[7][5] = 0
    output = native.reference(grid, {"stamp_transform":"identity"})
    assert output[7][4] == 0
    assert output[2][2] == 0 and output[1][1] == 0


def test_settings_and_scalar_types_are_strict(native):
    assert callable(getattr(native, "normalize_settings", None)), "native settings API is absent"
    assert native.normalize_settings(None) == {"stamp_transform":"identity"}
    assert native.normalize_settings({}) == {"stamp_transform":"identity"}
    for invalid in (True, 1, "identity", [], {"stamp_transform": True}, {"stamp_transform":"rotate"}, {"x":"identity"}):
        with pytest.raises((TypeError, ValueError)):
            native.normalize_settings(invalid)
    for seed in (True, -1, 0.5, "0", None):
        with pytest.raises((TypeError, ValueError)):
            native.generate(seed, None)
    for key, invalids in (("demos", (True, 1, 7, 2.0, "2")), ("queries", (True, 0, 5, 1.0, "1"))):
        for value in invalids:
            with pytest.raises((TypeError, ValueError)):
                native.generate(0, None, **{key:value})


def test_program_is_exact_canonical_and_adapter_uses_native_contract(native):
    assert callable(getattr(native, "program", None)), "native program API is absent"
    canonical = (HERE / "canonical.rkt").read_text(encoding="utf-8")
    assert native.program(None) == canonical
    assert native.program({"stamp_transform":"mirror_horizontal"}) != canonical
    spec = importlib.util.spec_from_file_location("native_stamp_adapter_test", HERE / "adapter.py")
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    episode = adapter.generate(17, {"stamp_transform":"mirror_horizontal"}, 2, 4)
    assert episode == native.generate(17, {"stamp_transform":"mirror_horizontal"}, 2, 4)
    assert episode["program_solution"] == adapter.program({"stamp_transform":"mirror_horizontal"})


def test_native_self_check_rejects_malformed_and_out_of_bounds_inputs(native):
    assert callable(getattr(native, "self_check", None)), "native grammar validator is absent"
    for malformed in ([], [[0], [0, 1]], [[False]*8 for _ in range(8)], [[0]*7 for _ in range(8)]):
        assert native.self_check(malformed)
    grid = [[0]*8 for _ in range(8)]
    grid[3][3], grid[3][4], grid[0][0] = 3, 8, 2
    assert native.self_check(grid), "horizontal mirror at top-left destination must be rejected"
    grid[0][0], grid[4][4] = 0, 2
    assert native.self_check(grid) == []
    grid[7][7] = 8
    assert native.self_check(grid), "disconnected cyan source must be rejected"
