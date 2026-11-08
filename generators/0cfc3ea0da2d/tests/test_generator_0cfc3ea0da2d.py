"""Focused regressions for global-frequency-rank generator 0cfc3ea0da2d."""
from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

TASK_ID = "0cfc3ea0da2d"
ROOT = Path(__file__).resolve().parents[1]
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _canonical_pairs():
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            return [
                pair
                for split in ("train", "test")
                for pair in row.get(split, [])
            ]
    raise AssertionError("canonical task row not found")


def test_rule_hash_and_all_canonical_pairs_are_synchronized():
    assert GEN.RULE_HASH == "d3e7de6ab51b"
    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_four_consecutive_profiles_cover_every_decisive_branch_per_band():
    expected_profiles = {
        ("canonical_desc", "single"),
        ("top_tie", "single"),
        ("all_tie", "single"),
        ("split_trap", "split_top"),
    }
    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(5000 + i, i, difficulty=band) for i in range(4)]
        observed = {
            (
                GEN.observe_overrides(grid)["frequency_pattern"],
                GEN.observe_overrides(grid)["component_pattern"],
            )
            for grid in grids
        }
        assert observed == expected_profiles
        for witness in GEN.SEMANTIC_WITNESSES.values():
            assert any(witness(grid) for grid in grids)


def test_four_demos_identify_every_query_schedule_residue():
    for band in ("easy", "medium", "hard"):
        for start in range(4):
            lesson = []
            for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
                grid = GEN.generate(8000 + start, sample_index, difficulty=band)
                lesson.append({"input": grid, "output": GEN.rule_mirror(grid)})
            assert GEN.lesson_identifiable(lesson[:-1], lesson[-1]) == []
            assert all(
                any(competitor(demo["input"]) != demo["output"] for demo in lesson[:-1])
                for competitor in GEN.LESSON_COMPETITORS.values()
            )


def test_override_boundaries_are_exact_and_observable_in_every_band():
    cases = (
        {"grid_h": 4},
        {"grid_h": 11},
        {"grid_w": 5},
        {"grid_w": 13},
        {"n_colors": 2},
        {"n_colors": 5},
        {"frequency_pattern": "canonical_desc"},
        {"frequency_pattern": "top_tie"},
        {"frequency_pattern": "all_tie"},
        {"frequency_pattern": "split_trap"},
        {"component_pattern": "single"},
        {"component_pattern": "split_top"},
        {
            "grid_h": 4,
            "grid_w": 5,
            "n_colors": 5,
            "frequency_pattern": "split_trap",
            "component_pattern": "split_top",
        },
    )
    for band in ("easy", "medium", "hard"):
        for index, case in enumerate(cases):
            grid = GEN.generate(10000 + index, 17 + index, difficulty=band, **case)
            observed = GEN.observe_overrides(grid)
            assert GEN.self_check(grid) == []
            for key, value in case.items():
                assert observed[key] == value

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=1)


def test_determinism_fresh_returns_input_purity_and_global_rng_state():
    random.seed(987654321)
    before = random.getstate()
    first = GEN.generate(77, 19, difficulty="hard")
    intervening = GEN.generate(78, 20, difficulty="easy")
    second = GEN.generate(77, 19, difficulty="hard")
    after = random.getstate()

    assert before == after
    assert first == second
    assert first is not second and first[0] is not second[0]
    assert intervening != first
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(77, 19, difficulty="hard") == second


def test_self_check_rejects_targeted_structural_impostors():
    all_zero = [[0] * 5 for _ in range(4)]

    one_color = [[0] * 5 for _ in range(4)]
    one_color[0][0] = 4
    one_color[0][1] = 4

    no_background = [[1, 1, 2, 2, 2] for _ in range(4)]

    # Frequencies 2 and 1 with source colors already equal to their ranks: the
    # official recoloring is an identity and therefore teaches nothing.
    identity = [[1, 1, 0, 0, 2]] + [[0] * 5 for _ in range(3)]

    unrecognized_counts = [[0] * 5 for _ in range(4)]
    for col in range(5):
        unrecognized_counts[0][col] = 4
    for col in range(3):
        unrecognized_counts[2][col] = 7

    impostors = {
        "all_zero": all_zero,
        "one_color": one_color,
        "no_background": no_background,
        "identity": identity,
        "unrecognized_counts": unrecognized_counts,
    }
    for name, grid in impostors.items():
        assert GEN.self_check(grid), name


def test_negative_recombination_is_rejected_but_rule_remains_executable():
    grid = GEN.generate(
        4242,
        3,
        difficulty="hard",
        frequency_pattern="split_trap",
        component_pattern="split_top",
        n_colors=3,
    )
    obs = GEN.semantic_observables(grid)
    top = obs["ranked_colors"][0]
    components = GEN._component_cells(grid, top)
    assert len(components) == 2

    replacement = next(color for color in range(1, 10) if color not in obs["colors"])
    recombined = copy.deepcopy(grid)
    for row, col in components[0]:
        recombined[row][col] = replacement

    assert GEN.self_check(recombined)
    output = GEN.rule_mirror(recombined)
    assert len(output) == len(recombined)
    assert len(output[0]) == len(recombined[0])


def test_generated_counterexamples_refute_canonical_shortcuts():
    canonical_pairs = _canonical_pairs()
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in canonical_pairs), name

    split = GEN.generate(9090, 3, difficulty="medium")
    tie = GEN.generate(9091, 1, difficulty="medium")
    assert GEN._rank_by_largest_component(split) != GEN.rule_mirror(split)
    assert GEN._rank_by_first_seen(tie) != GEN.rule_mirror(tie)
