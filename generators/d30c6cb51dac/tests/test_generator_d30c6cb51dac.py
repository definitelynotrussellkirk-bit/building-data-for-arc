from __future__ import annotations

import random

import pytest

from puzzle_generators.per_puzzle.d30c6cb51dac import generator as gen
from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


def _demo(seed: int, sample_index: int, band: str):
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs_match_selected_rule():
    assert gen.RULE_HASH == canonical_rule_hash(gen.TASK_ID) == "d70de3d5eaf9"
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_public_overrides_round_trip_and_unknown_keys_reject():
    for band in ("easy", "medium", "hard"):
        for n_panels in (3, 4, 5):
            for color_mode in ("monochrome", "panelwise"):
                grid = gen.generate(
                    311,
                    7,
                    difficulty=band,
                    n_panels=n_panels,
                    color_mode=color_mode,
                )
                assert gen.observe_overrides(grid) == {
                    "n_panels": n_panels,
                    "color_mode": color_mode,
                }
                assert gen.self_check(grid) == []
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, difficulty="easy", typo_axis=3)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    before = random.getstate()
    a = gen.generate(90210, 3, difficulty="hard")
    after = random.getstate()
    b = gen.generate(90210, 3, difficulty="hard")
    assert before == after
    assert a == b
    assert a is not b
    assert all(x is not y for x, y in zip(a, b))
    a[0][0] = 9 if a[0][0] != 9 else 8
    assert a != b


def test_every_two_demo_schedule_window_is_identifiable():
    # Check every residue-class start across two full schedule periods.
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            demos = [_demo(7000 + start, start + offset, band) for offset in range(2)]
            query = {"input": gen.generate(8000 + start, start + 2, difficulty=band)}
            assert gen.lesson_identifiable(demos, query) == []


def test_semantic_decoys_refute_broader_transform_shortcuts():
    for band in ("easy", "medium", "hard"):
        for sample_index in range(8):
            grid = gen.generate(1234, sample_index, difficulty=band)
            truth = gen.rule_mirror(grid)
            assert gen.SEMANTIC_RIVALS["full_dihedral"](grid) != truth
            assert gen.SEMANTIC_RIVALS["same_cell_count"](grid) != truth
            assert gen.SEMANTIC_WITNESSES["positive_relation_present"](grid)
        # Every two consecutive draws contain both LR and UD rule branches and
        # a larger scene that refutes the canonical fixed-position shortcut.
        for start in range(7):
            pair = [gen.generate(2222, start + i, difficulty=band) for i in range(2)]
            assert any(gen.SEMANTIC_WITNESSES["horizontal_reflection_branch"](g) for g in pair)
            assert any(gen.SEMANTIC_WITNESSES["vertical_reflection_branch"](g) for g in pair)
            assert any(gen.SEMANTIC_WITNESSES["identity_is_not_automatically_related"](g) for g in pair)
            assert any(gen.SEMANTIC_WITNESSES["fixed_position_shortcut_refuted"](g) for g in pair)


def test_task_specific_mutation_fixtures_are_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        errors = gen.self_check(grid)
        assert errors, f"fixture {name} unexpectedly passed self_check"


def test_sequential_materializer_schedule_covers_declared_output_codomains():
    # materialize_pool_sample advances seed and episode/sample_index together.
    # Guard against linear-selector aliasing that looks diverse under random
    # lint coordinates but collapses relation positions in ordinary training.
    seen = set()
    for episode in range(600):
        grid = gen.generate(3_300_000 + episode, episode, difficulty="hard")
        out = gen.rule_mirror(grid)
        seen.add(tuple(tuple(row) for row in out))
    assert len(seen) == gen.EXPECTED_OUTPUT_CODOMAIN
