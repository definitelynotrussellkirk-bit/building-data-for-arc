"""Behavioral contract for the opt-in command-source family."""
from __future__ import annotations

import importlib.util
import json
import random
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
ADAPTER_PATH = HOME / "workspace/parametric/adapter.py"
SPEC = importlib.util.spec_from_file_location("dcc5f8961845_parametric_tests", ADAPTER_PATH)
ADAPTER = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(ADAPTER)
HEADER = {"second_source": "header"}
MARKER = {"second_source": "post_first_marker"}


def _input_bytes(episode):
    return [json.dumps(pair["input"], separators=(",", ":"))
            for pair in episode["train"] + episode["test"]]


def test_default_program_preserves_exact_canonical_bytes():
    from reviewer_support import canonical_pairs, find_root
    del canonical_pairs  # the import also proves the portable helper is available
    root = find_root(__file__)
    rows = (json.loads(line) for line in (root / "shared/data/canonical/puzzles.jsonl").open())
    canonical = next(row["program_solution"] for row in rows if row["task_id"] == HOME.name)
    assert ADAPTER.program(HEADER) == canonical
    assert ADAPTER.program(MARKER) != canonical


def test_post_first_marker_is_a_real_sequential_dependency():
    witness = ADAPTER.sequential_witness()
    assert witness["setting"] == MARKER
    assert witness["step_a"] == "apply the first header transform to the cropped motif"
    assert witness["intermediate"]["marker_corner"] != witness["skip_a_intermediate"]["marker_corner"]
    assert witness["correct_output"] != witness["skip_a_output"]
    assert ADAPTER.solve(witness["input"], MARKER) == witness["correct_output"]


@pytest.mark.parametrize("demos", [2, 3, 4, 5, 6])
def test_supported_demo_counts_identify_both_settings_and_refute_rivals(demos):
    matched = []
    for settings in (HEADER, MARKER):
        episode = ADAPTER.generate(17, settings, demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        assert len(_input_bytes(episode)) == len(set(_input_bytes(episode)))
        other = MARKER if settings == HEADER else HEADER
        assert any(ADAPTER.solve(pair["input"], other) != pair["output"]
                   for pair in episode["train"])
        report = ADAPTER.lesson_report(episode, settings)
        assert report["demonstration_survivors"] == []
        assert report["surviving_query_disagreements"] == []
        matched.append(_input_bytes(episode))
    assert matched[0] == matched[1]


@pytest.mark.parametrize("queries", [1, 2, 3, 4])
def test_query_counts_are_prefix_stable_and_first_turn_matches_single_query(queries):
    from reviewer_support import public_challenge_bytes
    one = ADAPTER.generate(33, MARKER, 3, 1)
    many = ADAPTER.generate(33, MARKER, 3, queries)
    assert one["train"] == many["train"]
    assert one["test"][0] == many["test"][0]
    first_turn = {"train": many["train"], "test": many["test"][:1]}
    assert public_challenge_bytes(one) == public_challenge_bytes(first_turn)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    state = random.getstate()
    first = ADAPTER.generate(9, MARKER, 3, 4)
    assert random.getstate() == state
    second = ADAPTER.generate(9, MARKER, 3, 4)
    assert first == second and first is not second
    first["train"][0]["input"][0][0] = 9
    assert ADAPTER.generate(9, MARKER, 3, 4) == second


def test_30x30_query_has_real_content_spread_and_boundary_contacts():
    grid = ADAPTER.generate(7, MARKER, 3, 4)["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    motif = ADAPTER.analyze(grid)["motif"]
    assert (len(motif), len(motif[0])) == (28, 30)
    occupied = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                if value and r >= 2]
    assert len(occupied) >= 400
    assert {r // 15 for r, _ in occupied} == {0, 1}
    assert {c // 15 for _, c in occupied} == {0, 1}
    assert min(c for _, c in occupied) == 0
    assert max(c for _, c in occupied) == 29
    assert max(r for r, _ in occupied) == 29
    assert sum(value == 9 for row in grid for value in row) == 1


def test_python_labels_follow_each_declared_program_semantics():
    for seed in (0, 17, 81):
        for settings in (HEADER, MARKER):
            episode = ADAPTER.generate(seed, settings, 2, 4)
            assert episode["program_solution"] == ADAPTER.program(settings)
            for pair in episode["train"] + episode["test"]:
                assert pair["output"] == ADAPTER.solve(pair["input"], settings)


@pytest.mark.parametrize("settings", [
    {},
    {"second_source": True},
    {"second_source": "other"},
    {"second_source": "header", "extra": 1},
])
def test_invalid_settings_are_rejected(settings):
    with pytest.raises(ValueError):
        ADAPTER.generate(0, settings, 3, 4)


@pytest.mark.parametrize("demos,queries", [
    (1, 4), (7, 4), (True, 4), (3, 0), (3, 5), (3, True),
])
def test_count_boundaries_reject_invalid_requests(demos, queries):
    with pytest.raises(ValueError):
        ADAPTER.generate(0, MARKER, demos, queries)


def test_seed_and_grid_types_are_strict():
    with pytest.raises(ValueError):
        ADAPTER.generate(True, MARKER, 3, 4)
    with pytest.raises(ValueError):
        ADAPTER.solve([[True]], MARKER)


def test_lesson_audit_retains_rivals_that_match_an_individual_demo():
    template = [list(row) for row in ADAPTER._MODULE._TEACHING[0]["template"]]
    grid = ADAPTER._MODULE._paint_scene(9, 12, template, 2, 0, 1, 5)
    expected = ADAPTER.solve(grid, MARKER)
    rivals = ADAPTER.rival_outputs(grid, MARKER)
    assert "header_then_marker" in rivals
    assert rivals["header_then_marker"] == expected
