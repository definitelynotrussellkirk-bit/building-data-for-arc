from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs


GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.806425ca81b3.generator"
)
TASK_ID = "806425ca81b3"


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def test_canonical_pairs_are_accepted_and_python_mirror_is_exact():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"], "rule mirror mutated its input"


def test_exact_overrides_are_observable_at_boundaries_and_unknown_keys_reject():
    for band in ("easy", "medium", "hard"):
        for height in (8, 14):
            for width in (9, 14):
                for active_rows in (1, 5):
                    for profile in GEN.SCENE_PROFILES:
                        requested = {
                            "grid_h": height,
                            "grid_w": width,
                            "active_rows": active_rows,
                            "scene_profile": profile,
                        }
                        grid = GEN.generate(701, 19, difficulty=band, **requested)
                        assert GEN.observe_overrides(grid) == requested
                        assert GEN.self_check(grid) == []
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=True)


def test_four_phase_schedule_is_exact_and_every_profile_refutes_its_named_rival():
    expected = list(GEN.SCENE_PROFILES)
    observed = []
    for sample_index in range(4):
        grid = GEN.generate(90210, sample_index, difficulty="medium")
        observed.append(GEN.observe_overrides(grid)["scene_profile"])
    assert observed == expected

    for sample_index, witness_name in enumerate(
        (
            "three_plus_anchors_refute_exactly_two",
            "mixed_colors_same_row",
            "singleton_color_creates_no_span",
            "edge_touching_span_is_lawful",
        )
    ):
        grid = GEN.generate(90211, sample_index, difficulty="hard")
        assert GEN.SEMANTIC_WITNESSES[witness_name](grid)
        authoritative = GEN.rule_mirror(grid)
        for rival_name in GEN.WITNESS_RIVALS[witness_name]:
            assert GEN.SEMANTIC_RIVALS[rival_name](grid) != authoritative


def test_exactly_two_anchor_shortcut_fits_canonical_but_generated_witness_kills_it():
    shortcut = GEN.CANONICAL_SHORTCUTS["exactly_two_anchors_only"]
    for pair in canonical_pairs(TASK_ID):
        assert shortcut(pair["input"]) == pair["output"]
    witness = GEN.generate(8080, 0, difficulty="easy")
    assert shortcut(witness) != GEN.rule_mirror(witness)


def test_every_sliding_four_demo_window_identifies_the_next_query():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            demos = [
                _pair(GEN.generate(1701, start + offset, difficulty=band))
                for offset in range(GEN.EXAMPLES_NEEDED)
            ]
            query = _pair(
                GEN.generate(1701, start + GEN.EXAMPLES_NEEDED, difficulty=band)
            )
            assert GEN.lesson_identifiable(demos, query) == []


def test_structural_checker_rejects_all_named_mutation_fixtures():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert GEN.self_check(grid), f"mutation fixture {name!r} was accepted"


def test_determinism_fresh_returns_and_process_global_rng_purity():
    random.seed(4444)
    before = random.getstate()
    first = GEN.generate(123456, 7, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(123456, 7, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second
