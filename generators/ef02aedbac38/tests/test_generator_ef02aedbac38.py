from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

GEN = importlib.import_module("puzzle_generators.per_puzzle.ef02aedbac38.generator")


def _canonical_inputs():
    for line in Path("data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") == GEN.TASK_ID:
            return [pair["input"] for split in ("train", "test") for pair in row[split]]
    raise AssertionError("canonical task missing")


def _rule(grid):
    other = next(value for row in grid for value in row if value != 5)
    return [[other if value == 5 else 0 for value in row] for row in grid]


def test_all_canonical_inputs_are_accepted_and_strict():
    canonical = _canonical_inputs()
    assert len(canonical) == 4
    assert all(GEN.self_check(grid) == [] for grid in canonical)
    assert all(GEN.strict_canonical_like(grid) == [] for grid in canonical)


def test_exact_axes_observe_boundary_overrides_and_reject_unknown_keys():
    for height, width, color in ((3, 25, 1), (25, 3, 9), (25, 25, 4)):
        grid = GEN.generate(
            17,
            height * 100 + width,
            difficulty="easy",
            grid_h=height,
            grid_w=width,
            other_color=color,
        )
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == {
            "grid_h": height,
            "grid_w": width,
            "other_color": color,
        }
    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(0, 0, texture="cluster")
    with pytest.raises(ValueError, match="other_color"):
        GEN.generate(0, 0, other_color=5)


def test_default_draws_are_fresh_deterministic_and_global_rng_pure():
    state = random.getstate()
    first = GEN.generate(123, 456, difficulty="hard")
    second = GEN.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    mutated = copy.deepcopy(first)
    mutated[0][0] = 0
    assert GEN.generate(123, 456, difficulty="hard") == second
    assert GEN.self_check(second) == []


@pytest.mark.parametrize("seed,sample_index", [(84, 2), (105, 11)])
def test_small_general_partitions_keep_both_colors_spanning_two_axes(
    seed, sample_index
):
    grid = GEN.generate(seed, sample_index, difficulty="easy")
    assert GEN.self_check(grid) == []


def test_self_check_rejects_rule_hiding_and_malformed_impostors():
    impostors = [
        [[5, 5, 5], [5, 5, 5], [5, 5, 5]],
        [[2, 2, 2], [2, 5, 2], [2, 2, 2]],
        [[5, 5, 2], [5, 5, 2], [2, 2, 2]],
        [[5, 5, 5, 5], [2, 2, 2, 2], [2, 2, 2, 2]],
        [[5, 2, 2], [2, 5, 2]],
        [[5, 2, 2], [2, 5]],
        [[5, 2, 2], [2, 11, 2], [2, 2, 5]],
    ]
    assert all(GEN.self_check(grid) for grid in impostors)


def test_canonical_prior_is_stable_in_both_disjoint_200_draw_ranges():
    for start in (0, 10000):
        for band in ("easy", "medium", "hard"):
            grids = [
                GEN.generate(start + index, start + index, difficulty=band)
                for index in range(200)
            ]
            strict_hits = sum(not GEN.strict_canonical_like(grid) for grid in grids)
            assert strict_hits >= 50
            assert all(GEN.self_check(grid) == [] for grid in grids)


def test_every_four_sample_window_balances_sparse_and_dense_novel_five_masks():
    def role(grid):
        five_count = sum(value == 5 for row in grid for value in row)
        other_count = sum(value != 5 for row in grid for value in row)
        if five_count > other_count:
            return "dense"
        if five_count < other_count:
            return "sparse"
        return "tie"

    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            grids = [GEN.generate(seed, index, difficulty=band) for index in range(20)]
            for start in range(17):
                novel_roles = {
                    role(grid)
                    for grid in grids[start : start + 4]
                    if GEN.strict_canonical_like(grid)
                }
                assert {"sparse", "dense"} <= novel_roles, (
                    band,
                    seed,
                    start,
                    novel_roles,
                )


def test_official_signature_set_and_negative_recombination():
    official = _canonical_inputs()
    assert all(not GEN.strict_canonical_like(grid) for grid in official)
    # Recombine the official 3x3 dimensions with a 5x5 mask crop.  Palette and
    # dimensions remain superficially canonical, but linked morphology does not.
    recombined = [
        [5, 5, 2],
        [2, 5, 5],
        [2, 2, 5],
    ]
    assert GEN.self_check(recombined) == []
    assert GEN.strict_canonical_like(recombined)


def test_sparse_or_canonical_shortcut_fits_official_pairs_and_dies_in_every_window():
    rival = GEN.CANONICAL_SHORTCUTS["sparse_or_canonical_lookup"]
    assert all(rival(grid) == _rule(grid) for grid in _canonical_inputs())

    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            grids = [GEN.generate(seed, index, difficulty=band) for index in range(20)]
            for start in range(17):
                assert any(
                    rival(grid) != _rule(grid)
                    for grid in grids[start : start + 4]
                ), (band, seed, start)


def test_rivals_are_killed_and_lessons_are_identifiable():
    demos = []
    seed = 31
    for sample_index in range(4):
        grid = GEN.generate(seed, sample_index, difficulty="medium")
        demos.append({"input": grid, "output": _rule(grid)})
    query_grid = GEN.generate(seed, 4, difficulty="medium")
    assert GEN.lesson_identifiable(demos, {"input": query_grid}) == []
    for name, witness in GEN.SEMANTIC_WITNESSES.items():
        assert any(
            witness(GEN.generate(seed, sample_index, difficulty=band))
            for band in ("easy", "medium", "hard")
            for sample_index in range(20)
        ), name


def test_valid_call_replay_is_unchanged_by_call_contract_repair():
    fixture_path = Path(
        "generators/ef02aedbac38/counterexamples/valid-call-replay.json"
    )
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    assert fixture["baseline_source_sha256"] == (
        "ec1715f0dae31d63e1fa652acfa9a0505e26e9503e11c629f789c5cf3e24e651"
    )
    for case in fixture["cases"]:
        actual = GEN.generate(
            case["seed"],
            case["sample_index"],
            difficulty=case["difficulty"],
            **case["overrides"],
        )
        assert actual == case["grid"], case["name"]


@pytest.mark.parametrize("seed", [True, False, 1.0, "1", None])
def test_generate_rejects_non_integer_seed_scalars(seed):
    with pytest.raises(ValueError, match="seed must be an integer"):
        GEN.generate(seed, 0, difficulty="easy")


@pytest.mark.parametrize("sample_index", [True, False, -1, 1.0, "0", None])
def test_generate_rejects_invalid_sample_index_scalars(sample_index):
    with pytest.raises(ValueError, match="sample_index must be a non-negative integer"):
        GEN.generate(991, sample_index, difficulty="easy")


@pytest.mark.parametrize("difficulty", [0, 1, 0.0, 1.0, True, False, "medium ", "unknown"])
def test_generate_rejects_non_enum_difficulty_scalars(difficulty):
    with pytest.raises(ValueError, match="difficulty must be one of"):
        GEN.generate(991, 0, difficulty=difficulty)
