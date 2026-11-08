from __future__ import annotations

import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root


ROOT = find_root(__file__)
TASK = "483682b75e12"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")


def _canonical_rows():
    with canonical_path(ROOT).open() as handle:
        return [row for row in map(json.loads, handle) if row.get("task_id") == TASK]


def _pairs(row):
    test = row["test"]
    return row["train"] + ([test] if isinstance(test, dict) else test)


def _frozen(grid):
    return tuple(map(tuple, grid))


def test_both_canonical_rows_share_one_rule_hash():
    rows = _canonical_rows()
    assert {row["source"] for row in rows} == {"training", "augmented"}
    hashes = {
        hashlib.sha256(" ".join(row["program_solution"].split()).encode()).hexdigest()[:12]
        for row in rows
    }
    assert hashes == {MODULE.RULE_HASH} == {"a2a5ebf00ff5"}


def test_public_profiles_replay_all_unique_canonical_pairs_exactly():
    rows = _canonical_rows()
    training = next(row for row in rows if row["source"] == "training")
    pairs = _pairs(training)
    assert len(pairs) == len(MODULE.PUBLIC_PROFILES) == 4
    for profile, pair in zip(MODULE.PUBLIC_PROFILES, pairs):
        grid = MODULE.generate(0, 0, scene_profile=profile)
        assert grid == pair["input"]
        assert MODULE.rule_mirror(grid) == pair["output"]
        assert MODULE.canonical_profile_signature(grid) == profile
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
    augmented = next(row for row in rows if row["source"] == "augmented")
    assert {_frozen(pair["input"]) for pair in _pairs(augmented)} == {_frozen(pair["input"]) for pair in pairs}
    assert {_frozen(pair["output"]) for pair in _pairs(augmented)} == {_frozen(pair["output"]) for pair in pairs}


def test_every_general_profile_is_valid_and_recoverable_in_every_band():
    for band_index, band in enumerate((None, "easy", "medium", "hard")):
        for profile_index, profile in enumerate(MODULE.GENERAL_PROFILES):
            for seed in range(30):
                grid = MODULE.generate(
                    100_000 * band_index + 1_000 * profile_index + seed,
                    seed * 31,
                    difficulty=band,
                    scene_profile=profile,
                )
                analysis = MODULE._analysis(grid)
                assert not analysis["errors"]
                assert analysis["scene_profile"] == profile
                assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


def test_default_generation_reaches_every_declared_profile():
    seen = {
        MODULE.observe_overrides(MODULE.generate(seed, seed * 37))["scene_profile"]
        for seed in range(4000)
    }
    assert seen == set(MODULE.SCENE_PROFILES)


def test_every_component_moves_up_by_its_total_size_and_keeps_cell_colors():
    for seed in range(500):
        grid = MODULE.generate(seed, seed * 19)
        analysis = MODULE._analysis(grid)
        assert not analysis["errors"]
        output = MODULE.rule_mirror(grid)
        for component in analysis["facts"]["components"]:
            size = component["size"]
            for row, col in component["cells"]:
                assert output[row - size][col] == grid[row][col]
                assert output[row][col] == 7


def test_floor_is_preserved_and_all_other_unpainted_cells_clear_to_orange():
    grid = MODULE.generate(51, 83, scene_profile="mixed_sizes")
    facts = MODULE._analysis(grid)["facts"]
    output = MODULE.rule_mirror(grid)
    targets = {cell for component in facts["components"] for cell in component["targets"]}
    assert output[-1] == [8] * len(output[-1])
    for row in range(len(output) - 1):
        for col in range(len(output[0])):
            if (row, col) not in targets:
                assert output[row][col] == 7


def test_multicolor_adjacent_cells_form_one_component_and_share_one_shift():
    grid = MODULE.generate(91, 17, scene_profile="multicolor_connected")
    facts = MODULE._analysis(grid)["facts"]
    assert len(facts["components"]) == 2
    assert all(component["size"] == 4 and len(component["colors"]) == 2 for component in facts["components"])
    output = MODULE.rule_mirror(grid)
    for component in facts["components"]:
        for row, col in component["cells"]:
            assert output[row - 4][col] == grid[row][col]


def test_mixed_sizes_produce_three_distinct_jump_distances():
    facts = MODULE._analysis(MODULE.generate(7, 8, scene_profile="mixed_sizes"))["facts"]
    assert sorted(facts["sizes"]) == [1, 2, 4]
    for component in facts["components"]:
        assert all(source[0] - target[0] == component["size"] for source, target in zip(component["cells"], component["targets"]))


@pytest.mark.parametrize(
    ("profile", "size", "shape"),
    [
        ("singleton", 1, ((0, 0),)),
        ("horizontal_domino", 2, ((0, 0), (0, 1))),
        ("vertical_domino", 2, ((0, 0), (1, 0))),
        ("horizontal_triomino", 3, ((0, 0), (0, 1), (0, 2))),
        ("vertical_triomino", 3, ((0, 0), (1, 0), (2, 0))),
        ("ell_tetromino", 4, ((0, 0), (1, 0), (1, 1), (1, 2))),
        ("square_tetromino", 4, ((0, 0), (0, 1), (1, 0), (1, 1))),
        ("tee_pentomino", 5, ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1))),
        ("horizontal_six", 6, ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5))),
    ],
)
def test_shape_profiles_have_exact_size_and_topology(profile, size, shape):
    component = MODULE._analysis(MODULE.generate(3, 4, scene_profile=profile))["facts"]["components"][0]
    assert component["size"] == size
    assert component["normalized"] == shape


def test_generation_is_deterministic_fresh_and_global_rng_independent():
    random.seed(987654)
    before = random.getstate()
    first = MODULE.generate(111, 222, difficulty="hard")
    assert random.getstate() == before
    second = MODULE.generate(111, 222, difficulty="hard")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert MODULE.generate(111, 222, difficulty="hard") == second


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0, 1], [0]],
        [[True] + [7] * 6 for _ in range(6)] + [[8] * 7],
        [[10] + [7] * 6 for _ in range(6)] + [[8] * 7],
        [[7] * 31 for _ in range(6)] + [[8] * 31],
        [[7] * 7 for _ in range(6)],
        [[7] * 7 for _ in range(6)] + [[7] * 7],
        [[7] * 7 for _ in range(6)] + [[8] * 7],
    ],
)
def test_self_check_rejects_malformed_or_ruleless_impostors(grid):
    assert MODULE.self_check(grid)


def test_self_check_rejects_extra_cyan_clipping_and_target_collisions():
    extra_cyan = MODULE.generate(1, 2, scene_profile="singleton")
    extra_cyan[0][0] = 8
    clipped = [[7] * 8 for _ in range(8)]
    clipped[-1] = [8] * 8
    for col in range(6):
        clipped[4][1 + col] = 2
    collision = [[7] * 8 for _ in range(8)]
    collision[-1] = [8] * 8
    collision[2][2] = 1
    for row in (4, 5, 6):
        collision[row][2] = 2
    assert MODULE.self_check(extra_cyan)
    assert MODULE.self_check(clipped)
    assert MODULE.self_check(collision)


def test_unknown_difficulty_profile_and_axis_fail_closed():
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, difficulty="extreme")
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, scene_profile="not_real")
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, n_components=3)


def test_public_returns_are_fresh():
    first = MODULE.generate(1, 2, scene_profile="public_1")
    frozen = _frozen(first)
    first[0][0] = 9
    assert _frozen(MODULE.generate(1, 2, scene_profile="public_1")) == frozen


def test_axis_contract_is_literal_minimal_and_complete():
    assert set(MODULE.AXES) == {"scene_profile"}
    valid = set(MODULE.AXES["scene_profile"]["valid"].split("|"))
    assert valid == set(MODULE.SCENE_PROFILES)
    assert not MODULE.HELPFUL_TEXTURES and not MODULE.DEGENERATE_TEXTURES
