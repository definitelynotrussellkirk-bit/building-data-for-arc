"""Regression tests for the selected portal generator, independent of import layout."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
RUNTIME = REPO / "shared/runtime"
if RUNTIME.is_dir():
    sys.path.insert(0, str(RUNTIME))
_spec = importlib.util.spec_from_file_location("portal_generator_under_test", HOME / "generator.py")
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)


def canonical_pairs():
    ledger = REPO / "shared/data/canonical/puzzles.jsonl"
    if not ledger.exists():
        ledger = HOME.parents[2] / "data/canonical/puzzles.jsonl"
    for line in ledger.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == gen.TASK_ID:
            return row["train"] + row["test"]
    raise AssertionError("canonical task missing")


def test_unknown_override_is_rejected():
    with pytest.raises(ValueError, match="unknown"):
        gen.generate(123, 0, misspelled_axis=9)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_documented_dimensions_are_legal_in_every_band(band):
    grid = gen.generate(1, 0, difficulty=band, grid_h=14, grid_w=9)
    assert (len(grid), len(grid[0])) == (14, 9)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_draws_are_nonidentity(band):
    # This includes the recorded legacy identity at easy / seed=27 / index=0.
    for seed in range(40):
        grid = gen.generate(seed, 0, difficulty=band)
        assert not gen.self_check(grid), (band, seed)
        assert hasattr(gen, "route_diagnostics"), "missing observable path diagnostics"
        info = gen.route_diagnostics(grid)
        assert info["painted_cells"] >= 1, (band, seed, grid)
        assert info["shortest_route_count"] == 1, (band, seed)


def test_has_source_bound_rule_hash():
    assert getattr(gen, "RULE_HASH", None) == "f97ce42855bc"


def test_canonical_inputs_and_python_mirror_match_authority_examples():
    assert hasattr(gen, "rule_mirror"), "missing diagnostic mirror"
    for pair in canonical_pairs():
        assert not gen.self_check(pair["input"])
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True, 2, 3]], [[0.0, 2, 3]], [[-1, 2, 3]], [[10, 2, 3]]])
def test_malformed_inputs_are_rejected_without_crashing(grid):
    assert gen.self_check(grid)


@pytest.mark.parametrize("color", range(4, 10))
def test_color_override_is_visible_and_exact(color):
    assert "portal_color" in gen.AXES
    for sample_index in range(4):
        grid = gen.generate(871, sample_index, portal_color=color)
        observed = gen.observe_overrides(grid)
        assert observed["portal_color"] == color
        assert not gen.self_check(grid)


@pytest.mark.parametrize("overrides", [
    {"grid_h": 6}, {"grid_h": 15}, {"grid_w": 8}, {"grid_w": 19},
    {"grid_h": True}, {"grid_w": 11.5}, {"grid_h": "7"},
    {"portal_color": 3}, {"portal_color": 10}, {"portal_color": False},
    {"texture": "no_start"},
])
def test_invalid_override_rejected(overrides):
    with pytest.raises((ValueError, TypeError)):
        gen.generate(1, 0, **overrides)


def test_every_four_slot_lesson_eliminates_named_rivals():
    assert getattr(gen, "EXAMPLES_NEEDED", None) == 4
    for band in ("easy", "medium", "hard"):
        for seed in range(8):
            for offset in range(4):
                grids = [gen.generate(seed, offset + i, difficulty=band) for i in range(5)]
                demos = [{"input": grid, "output": gen.rule_mirror(grid)} for grid in grids[:4]]
                query = {"input": grids[4], "output": gen.rule_mirror(grids[4])}
                assert gen.lesson_identifiable(demos, query) == [], (band, seed, offset)


def test_each_named_witness_is_an_actual_disagreement():
    assert hasattr(gen, "SEMANTIC_WITNESSES")
    hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    for i in range(48):
        grid = gen.generate(998 + i, i, difficulty=("easy", "medium", "hard")[i % 3])
        truth = gen.rule_mirror(grid)
        for name, pred in gen.SEMANTIC_WITNESSES.items():
            if pred(grid):
                hits[name] += 1
                assert any(gen.SEMANTIC_RIVALS[rival](grid) != truth for rival in gen.WITNESS_RIVALS[name])
    assert all(hits.values()), hits


def test_reference_only_color4_rival_fits_all_canonical_examples():
    assert hasattr(gen, "CANONICAL_SHORTCUTS")
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs()), name


def test_rule_mirror_and_diagnostics_are_input_pure():
    assert hasattr(gen, "rule_mirror")
    for i in range(4):
        grid = gen.generate(991, i)
        before = copy.deepcopy(grid)
        gen.rule_mirror(grid)
        gen.route_diagnostics(grid)
        gen.self_check(grid)
        assert grid == before
        assert gen.generate(991, i) == before


def test_missing_markers_and_identity_layout_rejected():
    for old in (2, 3):
        grid = gen.generate(333, 0)
        mutated = [[0 if cell == old else cell for cell in row] for row in grid]
        assert gen.self_check(mutated)
    assert gen.self_check([[1, 1, 1, 1, 1], [1, 2, 1, 3, 1], [1, 4, 1, 4, 1], [1, 1, 1, 1, 1]])


def test_color8_is_a_portal_before_it_is_an_output_marker():
    grid = [[2, 0, 8, 1, 8, 0, 3]]
    assert gen.rule_mirror(grid) == [[2, 8, 8, 1, 8, 8, 3]]


def test_three_occurrences_are_ordinary_traversable_cells():
    grid = [[2, 0, 5, 0, 5, 0, 5, 0, 3]]
    assert gen.rule_mirror(grid) == [[2, 8, 5, 8, 5, 8, 5, 8, 3]]


def test_mandatory_entry_teleport_cannot_be_walked_through():
    grid = [list(map(int, row)) for row in ["1111111", "1240031", "1111111", "1400001", "1111111"]]
    expected = [list(map(int, row)) for row in ["1111111", "1248831", "1111111", "1480001", "1111111"]]
    assert gen.rule_mirror(grid) == expected
    assert gen.route_diagnostics(grid)["used_portal_colors"] == [4, 4]


def test_tied_external_input_uses_reference_neighbor_order():
    grid = [list(map(int, row)) for row in ["11111", "10001", "12131", "10001", "11111"]]
    expected = [list(map(int, row)) for row in ["11111", "18881", "12131", "10001", "11111"]]
    assert gen.rule_mirror(grid) == expected
    assert gen.route_diagnostics(grid)["shortest_route_count"] == 2


def test_actual_unreachable_grid_is_rejected():
    grid = [list(map(int, row)) for row in ["1111111", "1201411", "1111111", "1301411", "1111111"]]
    assert gen.route_diagnostics(grid)["distance"] is None
    assert "no start-to-goal route" in gen.self_check(grid)


def test_lesson_check_does_not_read_query_answer():
    grids = [gen.generate(471, i) for i in range(5)]
    demos = [{"input": g, "output": gen.rule_mirror(g)} for g in grids[:4]]
    assert gen.lesson_identifiable(demos, {"input": grids[4], "output": [[999]]}) == []


def test_lesson_check_detects_color4_ambiguity_in_canonical_demos():
    demos = canonical_pairs()[:3]
    counterexample = [[5 if v == 4 else v for v in row] for row in demos[0]["input"]]
    assert any("color4_only" in reason for reason in gen.lesson_identifiable(demos, {"input": counterexample}))


def test_canonical_profile_floor_has_minimum_support_in_pinned_small_census():
    import hashlib
    hits = 0
    for band in ("easy", "medium", "hard"):
        for i in range(20):
            seed = int(hashlib.sha256(f"profile-floor:v1:{gen.TASK_ID}:{band}:{i}".encode()).hexdigest()[:12], 16)
            grid = gen.generate(seed, seed % 7919 + i, difficulty=band)
            profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
            hits += profile in {(7, 10, 5), (7, 11, 5)}
    assert hits >= 15, f"canonical profile support {hits}/60 is below the 25% floor"
