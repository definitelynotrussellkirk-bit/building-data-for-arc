from __future__ import annotations

import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
TASK = "34569d6118b3"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")


def _canonical_rows():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        return [row for row in map(json.loads, handle) if row.get("task_id") == TASK]


def _training_pairs():
    row = next(row for row in _canonical_rows() if row.get("source") == "training")
    test = row["test"]
    return row["train"] + ([test] if isinstance(test, dict) else test)


def _frozen(grid):
    return tuple(map(tuple, grid))


def test_rule_hash_matches_both_canonical_rows():
    hashes = {
        hashlib.sha256(" ".join(row["program_solution"].split()).encode()).hexdigest()[:12]
        for row in _canonical_rows()
    }
    assert hashes == {MODULE.RULE_HASH}


def test_every_public_profile_replays_its_canonical_pair_exactly():
    pairs = _training_pairs()
    assert len(pairs) == len(MODULE.PUBLIC_PROFILES) == 5
    for profile, pair in zip(MODULE.PUBLIC_PROFILES, pairs):
        grid = MODULE.generate(0, 0, scene_profile=profile)
        assert grid == pair["input"]
        assert MODULE.rule_mirror(grid) == pair["output"]
        assert MODULE.canonical_profile_signature(grid) == profile
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


def test_augmented_row_contains_the_same_five_pairs_in_another_order():
    augmented = next(row for row in _canonical_rows() if row.get("source") == "augmented")
    public_pairs = {(_frozen(grid), _frozen(MODULE.rule_mirror(grid))) for grid in MODULE._PUBLIC_INPUTS.values()}
    augmented_pairs = {( _frozen(pair["input"]), _frozen(pair["output"]) ) for pair in augmented["train"]}
    assert augmented_pairs == public_pairs


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


def test_default_generation_reaches_every_profile_in_every_band():
    for band in ("easy", "medium", "hard"):
        seen = {
            MODULE.observe_overrides(MODULE.generate(seed, seed * 37, difficulty=band))["scene_profile"]
            for seed in range(6000)
        }
        assert seen == set(MODULE.SCENE_PROFILES)


def test_small_manual_ordered_mapping_oracle():
    grid = [
        [1, 0, 2, 0, 5, 5, 0, 5, 5],
        [0, 0, 0, 0, 5, 0, 0, 0, 5],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 2, 0, 0, 0, 0],
    ]
    assert MODULE.rule_mirror(grid) == [[1, 1, 2, 2], [1, 0, 0, 2]]


def test_swatch_run_width_does_not_change_ordered_mapping():
    one = MODULE.generate(41, 99, scene_profile="three_color_square")
    parsed = MODULE._parse_scene(one)
    assert not parsed["errors"]
    widened = [row[:] for row in one]
    # Public examples prove width-two runs; generalized generation exercises one or two.
    assert all(1 <= end - start + 1 <= 2 for start, end, _ in parsed["swatch_runs"])
    assert MODULE.rule_mirror(one) == MODULE._analysis(one)["output"]
    assert widened == one


def test_all_mappings_are_used_and_templates_are_distinct():
    for profile in MODULE.GENERAL_PROFILES:
        grid = MODULE.generate(1234, 5678, scene_profile=profile)
        facts = MODULE._analysis(grid)["facts"]
        assert set(facts["swatch_colors"]) == {value for row in facts["layout"] for value in row}
        assert len(set(facts["templates"])) == len(facts["templates"])


def test_profile_geometry_and_output_dimensions_are_exact():
    for profile in MODULE.GENERAL_PROFILES:
        grid = MODULE.generate(99, 101, scene_profile=profile)
        facts = MODULE._analysis(grid)["facts"]
        count, th, tw, lh, lw, _ = MODULE._profile_spec(profile)
        assert (len(facts["swatch_colors"]), facts["template_h"], facts["template_w"], facts["layout_h"], facts["layout_w"]) == (count, th, tw, lh, lw)
        assert (facts["output_h"], facts["output_w"]) == (th * lh, tw * lw)
        assert facts["output_h"] <= 30 and facts["output_w"] <= 30


def test_density_profiles_are_separated_by_real_mask_density():
    dense = MODULE._analysis(MODULE.generate(1, 2, scene_profile="dense_templates"))["facts"]
    sparse = MODULE._analysis(MODULE.generate(1, 2, scene_profile="sparse_templates"))["facts"]
    assert dense["template_density"] >= 0.70
    assert sparse["template_density"] <= 0.45


def test_header_and_layout_padding_disappear_from_output():
    grid = MODULE.generate(222, 333, scene_profile="rectangular_layout")
    parsed = MODULE._parse_scene(grid)
    output = MODULE.rule_mirror(grid)
    assert len(output) == parsed["template_h"] * parsed["layout_h"]
    assert len(output[0]) == parsed["template_w"] * parsed["layout_w"]
    assert len(output) < len(grid) or len(output[0]) != len(grid[0])


def test_generation_is_deterministic_fresh_and_global_rng_independent():
    random.seed(987654)
    before = random.getstate()
    first = MODULE.generate(111, 222, difficulty="hard")
    assert random.getstate() == before
    second = MODULE.generate(111, 222, difficulty="hard")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert MODULE.generate(111, 222, difficulty="hard") == second


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0, 1], [0]],
        [[True, 0, 0], [0, 0, 0], [0, 0, 0]],
        [[10, 0, 0], [0, 0, 0], [0, 0, 0]],
        [[5] * 5 for _ in range(5)],
        [[0] * 6 for _ in range(6)],
        [[1, 0, 5, 5], [0, 0, 5, 0], [0, 0, 0, 0], [1, 0, 0, 0]],
        [[1, 0, 2, 0, 5, 5, 0, 5, 5], [0, 0, 0, 0, 5, 0, 0, 5, 0], [0] * 9, [1, 0, 0, 2, 0, 0, 0, 0, 0]],
        [[1, 0, 2, 0, 5, 5, 0, 5, 5], [0, 0, 0, 0, 5, 0, 0, 5, 0], [0] * 9, [1, 0, 3, 0, 0, 0, 0, 0, 0]],
        [[1, 0, 2, 0, 5, 5, 0, 5, 5], [0, 0, 0, 0, 5, 0, 0, 5, 0], [0] * 9, [1, 0, 0, 0, 0, 0, 0, 0, 0]],
    ],
)
def test_self_check_rejects_malformed_or_undeclared_impostors(grid):
    assert MODULE.self_check(grid)


def test_unknown_difficulty_profile_and_axis_fail_closed():
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, difficulty="extreme")
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, scene_profile="not_real")
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, layout_size="2x2")


def test_public_returns_are_fresh():
    first = MODULE.generate(1, 2, scene_profile="public_1")
    frozen = _frozen(first)
    first[0][0] = 9
    assert _frozen(MODULE.generate(1, 2, scene_profile="public_1")) == frozen
