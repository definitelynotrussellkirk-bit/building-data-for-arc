from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

TASK_ID = "4b1c57a69862"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]


def _canonical_rows():
    rows = []
    for line in (ROOT / "data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            rows.append(row)
    return rows


def _pairs(row):
    test = row.get("test", [])
    tests = [test] if isinstance(test, dict) else test
    return [*row.get("train", []), *tests]


def test_all_canonical_pairs_are_accepted_and_match_the_python_transcription():
    rows = _canonical_rows()
    assert len(rows) == 2
    pair_count = 0
    for row in rows:
        for pair in _pairs(row):
            pair_count += 1
            source = copy.deepcopy(pair["input"])
            assert GEN.self_check(source) == []
            assert GEN.strict_canonical_like(source) == []
            assert GEN._climb(source) == pair["output"]
            assert source == pair["input"]
    assert pair_count == 10
    assert GEN.RULE_HASH == "a731b6ee66cd"


@pytest.mark.parametrize("profile", GEN.SCENE_PROFILES)
@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_every_exact_scene_profile_override_is_observable(profile, band):
    grid = GEN.generate(7123, 19, difficulty=band, scene_profile=profile)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {"scene_profile": profile}


def test_unknown_override_rejects_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_profile="generalized_clear")


def test_self_check_rejects_targeted_structural_impostors():
    base = GEN.generate(91, 1, scene_profile="generalized_decoy")
    assert GEN.self_check(base) == []

    no_seed = copy.deepcopy(base)
    seed_r, seed_c = GEN._trace(no_seed)["seed"]
    no_seed[seed_r][seed_c] = 0
    assert any("one red seed" in reason for reason in GEN.self_check(no_seed))

    extra_seed = copy.deepcopy(base)
    extra_seed[-1][3] = 2
    assert any("one red seed" in reason for reason in GEN.self_check(extra_seed))

    raised_seed = copy.deepcopy(base)
    raised_seed[-1][seed_c] = 0
    raised_seed[-2][seed_c] = 2
    assert any("bottom row" in reason for reason in GEN.self_check(raised_seed))

    blocker_below = copy.deepcopy(base)
    blocker_below[-1][-1] = 1
    assert any("strictly above" in reason for reason in GEN.self_check(blocker_below))

    two_decoys = copy.deepcopy(base)
    two_decoys[-4][-1] = 1
    assert any("off-path" in reason for reason in GEN.self_check(two_decoys))


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(20260726)
    before = random.getstate()
    first = GEN.generate(777, 12, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(777, 12, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == after
    first[0][0] = 2
    assert GEN.generate(777, 12, difficulty="hard") == second


def test_every_four_sample_sliding_window_identifies_the_lesson():
    for band in ("easy", "medium", "hard"):
        for start in range(16):
            demos = []
            for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
                grid = GEN.generate(314159, sample_index, difficulty=band)
                demos.append({"input": grid, "output": GEN._climb(grid)})
            query_grid = GEN.generate(
                314159, start + GEN.EXAMPLES_NEEDED, difficulty=band
            )
            query = {"input": query_grid, "output": GEN._climb(query_grid)}
            assert GEN.lesson_identifiable(demos, query) == []


def test_default_distribution_covers_every_profile_and_strict_floor():
    for band in ("easy", "medium", "hard"):
        profiles = set()
        strict = 0
        for index in range(600):
            grid = GEN.generate(10_000 + index, index, difficulty=band)
            profiles.add(GEN.observe_overrides(grid)["scene_profile"])
            strict += GEN.strict_canonical_like(grid) == []
        assert profiles == set(GEN.SCENE_PROFILES)
        assert strict >= 150


def test_named_rivals_are_refuted_by_their_claimed_witnesses():
    witness_profiles = {
        "clear_baseline": "generalized_clear",
        "blocker_changes_path": "generalized_single",
        "adjacent_blockers_force_multi_shift": "generalized_double",
        "bridge_cells_are_required": "generalized_single",
        "off_path_blocker_is_irrelevant": "generalized_decoy",
    }
    for witness_name, profile in witness_profiles.items():
        grid = GEN.generate(1234, 0, scene_profile=profile)
        official = GEN._climb(grid)
        assert GEN.SEMANTIC_WITNESSES[witness_name](grid)
        for rival_name in GEN.WITNESS_RIVALS[witness_name]:
            assert GEN.SEMANTIC_RIVALS[rival_name](grid) != official


def test_negative_recombination_is_rejected_while_rule_remains_total():
    grid = GEN.generate(551, 3, scene_profile="generalized_decoy")
    changed = copy.deepcopy(grid)
    changed[-4][-1] = 1
    assert GEN.self_check(changed)
    output = GEN._climb(changed)
    assert len(output) == len(changed)
    assert len(output[0]) == len(changed[0])
