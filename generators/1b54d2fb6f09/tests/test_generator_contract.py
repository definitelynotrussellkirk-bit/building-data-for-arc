"""Behavioral regressions for the length-two teaching repair."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "1b54d2fb6f09"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def straight_lengths(grid):
    info, errors = GEN._analyze(grid)
    assert errors == []
    return sorted(len(record["cells"]) for record in info["straights"])


LENGTH_TWO_WITNESS = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 2, 2, 0, 0, 0, 2, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 2, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 2, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 2, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 2, 0, 0, 0, 0, 3, 3, 3, 0],
    [0, 2, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 2, 2, 0, 0, 0, 0, 0, 0, 0],
]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_ordinary_draw_teaches_length_two_and_preserved_interior(band):
    for sample_index in range(16):
        grid = GEN.generate(1701 + sample_index, sample_index, difficulty=band)
        lengths = straight_lengths(grid)
        assert 2 in lengths
        assert any(length >= 3 for length in lengths)


@pytest.mark.parametrize("n_straight", [2, 3, 4])
def test_exact_count_override_keeps_boundary_witness(n_straight):
    grid = GEN.generate(
        91,
        n_straight,
        difficulty="hard",
        grid_h=17,
        grid_w=18,
        n_straight=n_straight,
        distractor_color=6,
        distractor_shape="corner",
    )
    lengths = straight_lengths(grid)
    assert len(lengths) == n_straight
    assert 2 in lengths
    assert any(length >= 3 for length in lengths)
    assert GEN.observe_overrides(grid)["n_straight"] == n_straight


def test_length_two_witness_is_lawful_and_refutes_skip_length_two_rival():
    assert GEN.self_check(LENGTH_TWO_WITNESS) == []
    expected = GEN.rule_mirror(LENGTH_TWO_WITNESS)
    rival = GEN._rival_skip_length_two_segments(LENGTH_TWO_WITNESS)
    differing = [
        (r, c)
        for r, row in enumerate(expected)
        for c, value in enumerate(row)
        if value != rival[r][c]
    ]
    assert differing == [(1, 1), (1, 2)]
    assert [expected[r][c] for r, c in differing] == [8, 8]
    assert [rival[r][c] for r, c in differing] == [2, 2]


def test_only_declared_canonical_shortcut_really_fits_every_canonical_pair():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
    assert set(GEN.CANONICAL_SHORTCUTS) == {"skip_length_two_segments"}
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name


def test_length_two_rival_is_refuted_by_every_draw_and_all_rivals_by_each_window():
    for start in range(8):
        pairs = []
        for offset in range(4):
            grid = GEN.generate(313 + start, start + offset)
            pairs.append((grid, GEN.rule_mirror(grid)))
            assert (
                GEN.LESSON_COMPETITORS["skip_length_two_segments"](grid)
                != pairs[-1][1]
            )
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert any(rival(grid) != expected for grid, expected in pairs), (start, name)


def test_four_pair_windows_and_all_query_rotations_are_identifiable():
    for band in ("easy", "medium", "hard"):
        for start in range(4):
            pairs = []
            for offset in range(5):
                grid = GEN.generate(1200 + start, start * 5 + offset, difficulty=band)
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
            for query_index in range(5):
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                assert GEN.lesson_identifiable(demos, pairs[query_index]) == []
