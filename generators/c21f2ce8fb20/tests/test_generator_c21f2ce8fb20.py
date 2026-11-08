"""Focused regressions for the c21f2ce8fb20 chamber-count curriculum."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(HOME / "workspace"))

from reference_probe import (  # noqa: E402
    RIVALS,
    canonical_pairs,
    chamber_stats,
    count_above_three_witness,
    densest_room_output,
    intended_output,
    largest_room_output,
    load_generator,
    observed,
    prefer_exactly_three_output,
    size_density_witness,
    winner_quadrant,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def _lesson(seed: int, start: int, difficulty: str):
    pairs = []
    for sample_index in range(start, start + gen.EXAMPLES_NEEDED + 1):
        grid = gen.generate(seed, sample_index, difficulty=difficulty)
        pairs.append({"input": grid, "output": intended_output(grid)})
    return pairs[:-1], pairs[-1]


def _signature(grid):
    return tuple(tuple(row) for row in grid)


def test_rule_pin_public_contract_and_authority_are_exact():
    assert gen.VERSION == "3.0.0"
    assert gen.RULE_HASH == "b86be3a37a68"
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_chambers", "winner_seeds"}
    assert gen.EXAMPLES_NEEDED == 4
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "canonical_three_room",
        "canonical_four_room",
        "count_above_three",
        "size_density_decoys",
    )

    row = next(
        json.loads(line)
        for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == gen.TASK_ID
    )
    authority_path = (
        ROOT
        / "shared/data/base/solutions/banks/e00836ab832d/H129__c21f2ce8fb20.json"
    )
    selected = json.loads(authority_path.read_text())["racket_target"]["target_code"]
    assert selected == row["program_solution"]


def test_every_canonical_pair_is_owned_and_independent_oracle_matches():
    pairs = canonical_pairs()
    assert len(pairs) == 5
    assert all(prefer_exactly_three_output(pair["input"]) == pair["output"] for pair in pairs)
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert intended_output(pair["input"]) == pair["output"]
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 8, "grid_w": 11, "n_chambers": 3, "winner_seeds": 2},
        {"grid_h": 8, "grid_w": 11, "n_chambers": 4, "winner_seeds": 5},
        {"grid_h": 16, "grid_w": 20, "n_chambers": 3, "winner_seeds": 5},
        {"grid_h": 16, "grid_w": 20, "n_chambers": 4, "winner_seeds": 2},
    ],
)
def test_exact_override_cross_product_is_total_and_observable(difficulty, overrides):
    grid = gen.generate(20261003, 17, difficulty=difficulty, **overrides)
    assert gen.self_check(grid, difficulty=difficulty) == []
    assert observed(grid) == overrides
    assert gen.observe_overrides(grid) == overrides
    assert gen.generate(20261003, 17, difficulty=difficulty, **overrides) == grid


@pytest.mark.parametrize(
    "key,value",
    [
        ("mystery", 1),
        ("grid_h", 7),
        ("grid_h", 17),
        ("grid_h", True),
        ("grid_h", 8.0),
        ("grid_w", 10),
        ("grid_w", 21),
        ("n_chambers", 2),
        ("n_chambers", 5),
        ("winner_seeds", 1),
        ("winner_seeds", 6),
        ("winner_seeds", "3"),
    ],
)
def test_invalid_overrides_reject_loudly(key, value):
    with pytest.raises(ValueError):
        gen.generate(1, 0, **{key: value})


def test_invalid_difficulty_rejects_loudly():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="nightmare")


def test_every_sliding_four_example_window_refutes_all_named_rivals():
    assert set(gen.LESSON_COMPETITORS) == set(RIVALS)
    for difficulty in ("easy", "medium", "hard"):
        for start in range(12):
            demos, query = _lesson(8000 + start, start, difficulty)
            profiles = [
                gen.schedule_profile(8000 + start, index, difficulty)
                for index in range(start, start + gen.EXAMPLES_NEEDED)
            ]
            assert set(profiles) == set(gen.SCHEDULE_PROFILES)
            assert gen.lesson_identifiable(demos, query) == []
            for name, competitor in gen.LESSON_COMPETITORS.items():
                assert not all(
                    competitor(pair["input"]) == pair["output"] for pair in demos
                ), (difficulty, start, name)


def test_declared_canonical_shortcut_really_fits_canonical_and_is_generated_against():
    assert set(gen.CANONICAL_SHORTCUTS) == {"prefer_exactly_three"}
    assert all(
        gen.CANONICAL_SHORTCUTS["prefer_exactly_three"](pair["input"])
        == pair["output"]
        for pair in canonical_pairs()
    )
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in (2, 6, 10, 14):
            grid = gen.generate(99173, sample_index, difficulty=difficulty)
            assert gen.schedule_profile(99173, sample_index, difficulty) == "count_above_three"
            assert observed(grid)["winner_seeds"] in (4, 5)
            assert gen.SEMANTIC_WITNESSES["count_above_three"](grid)
            assert intended_output(grid) != prefer_exactly_three_output(grid)


def test_size_and_density_decoy_profile_is_a_real_two_rival_counterexample():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in (3, 7, 11, 15):
            grid = gen.generate(113355, sample_index, difficulty=difficulty)
            assert gen.schedule_profile(113355, sample_index, difficulty) == "size_density_decoys"
            intended = intended_output(grid)
            assert gen.SEMANTIC_WITNESSES["winner_not_largest"](grid)
            assert gen.SEMANTIC_WITNESSES["winner_not_densest"](grid)
            assert intended != largest_room_output(grid)
            assert intended != densest_room_output(grid)


def test_explicit_disagreement_inputs_are_exact_and_valid():
    count_grid = count_above_three_witness()
    assert gen.self_check(count_grid) == []
    assert intended_output(count_grid) != prefer_exactly_three_output(count_grid)
    assert [item["seeds"] for item in chamber_stats(count_grid)] == [4, 3, 1, 1]

    geometry_grid = size_density_witness()
    assert gen.self_check(geometry_grid) == []
    intended = intended_output(geometry_grid)
    assert intended != largest_room_output(geometry_grid)
    assert intended != densest_room_output(geometry_grid)


def test_generated_census_is_valid_varied_and_covers_teaching_axes():
    for band_index, difficulty in enumerate(("easy", "medium", "hard")):
        grids = [
            gen.generate(200_000 + band_index * 10_000 + index, index, difficulty=difficulty)
            for index in range(160)
        ]
        assert all(gen.self_check(grid, difficulty=difficulty) == [] for grid in grids)
        assert len({_signature(grid) for grid in grids}) >= 150
        stats = [observed(grid) for grid in grids]
        assert {item["n_chambers"] for item in stats} == {3, 4}
        assert {item["winner_seeds"] for item in stats} == {2, 3, 4, 5}
        assert {winner_quadrant(grid) for grid in grids} == {(0, 0), (0, 1), (1, 0), (1, 1)}
        assert set(gen.schedule_profile(0, index, difficulty) for index in range(4)) == set(gen.SCHEDULE_PROFILES)
        canonical_profiles = {
            (len(pair["input"]), len(pair["input"][0]), len({v for row in pair["input"] for v in row}))
            for pair in canonical_pairs()
        }
        assert any(
            (len(grid), len(grid[0]), len({v for row in grid for v in row})) in canonical_profiles
            for grid in grids
        )


def test_validator_rejects_structural_impostors_and_malformed_inputs():
    valid = gen.generate(
        314159,
        3,
        difficulty="hard",
        grid_h=12,
        grid_w=16,
        n_chambers=4,
        winner_seeds=4,
    )
    assert gen.self_check(valid) == []

    bad_color = deepcopy(valid)
    bad_color[0][0] = 9

    open_border = deepcopy(valid)
    open_border[0][1] = 0

    tied = deepcopy(valid)
    stats = chamber_stats(tied)
    winner = max(stats, key=lambda item: item["seeds"])
    runner_up = max((item for item in stats if item is not winner), key=lambda item: item["seeds"])
    needed = winner["seeds"] - runner_up["seeds"]
    for r, c in runner_up["cells"]:
        if needed == 0:
            break
        if tied[r][c] == 0:
            tied[r][c] = 2
            needed -= 1

    non_rectangular_room = deepcopy(valid)
    room = min(chamber_stats(non_rectangular_room), key=lambda item: item["area"])
    r0, c0, r1, c1 = room["bbox"]
    corner = (r0, c0)
    non_rectangular_room[corner[0]][corner[1]] = 5

    no_blank = deepcopy(valid)
    room = min(chamber_stats(no_blank), key=lambda item: item["area"])
    for r, c in room["cells"]:
        no_blank[r][c] = 2

    fixtures = {
        "bad_color": bad_color,
        "open_border": open_border,
        "tied": tied,
        "non_rectangular_room": non_rectangular_room,
        "no_blank": no_blank,
    }
    for name, grid in fixtures.items():
        assert gen.self_check(grid), name

    for malformed in (None, [], [[]], [[0], [0, 1]], [[True] * 11 for _ in range(8)]):
        assert gen.self_check(malformed), malformed


def test_replay_is_fresh_deterministic_and_global_rng_pure():
    random.seed(8675309)
    before = random.getstate()
    first = gen.generate(12345, 67, difficulty="hard")
    assert random.getstate() == before
    second = gen.generate(12345, 67, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second
