"""Regression and semantic coverage for generator 9000d0ea6484."""
from __future__ import annotations

import os
import sys
from itertools import permutations
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    INTENDED_ORDER,
    MANDATORY_SIGNATURES,
    apply_priority,
    canonical_pairs,
    fixed_canonical_color_priority,
    load_generator,
    observed,
    signatures,
    valid_priority_orders,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_rule_hash_is_pinned_to_current_authority():
    assert gen.RULE_HASH == "c9256d51e807"


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("seed", range(12))
def test_every_grid_is_a_complete_priority_lesson(band, seed):
    grid = gen.generate(seed, seed * 17 + 3, difficulty=band)
    assert gen.self_check(grid, difficulty=band) == []
    assert MANDATORY_SIGNATURES <= set(signatures(grid))
    output = apply_priority(grid)
    assert valid_priority_orders(grid, output) == [INTENDED_ORDER]
    assert grid == gen.generate(seed, seed * 17 + 3, difficulty=band)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_observable_in_every_band(band):
    options = {
        "sec0_color": 1,
        "sec1_color": 2,
        "sec2_color": 4,
        "sec3_color": 9,
        "extra_overlap_count": 5,
    }
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid, difficulty=band) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize("bad", [
    {"typo": 1},
    {"sec0_color": 0},
    {"sec1_color": 3},
    {"sec2_color": 10},
    {"extra_overlap_count": -1},
    {"extra_overlap_count": 6},
    {"extra_overlap_count": 2.5},
    {"sec0_color": 1, "sec1_color": 1},
])
def test_invalid_or_incompatible_overrides_are_rejected(bad):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **bad)


def test_difficulty_changes_default_overlap_curriculum():
    observed_counts = {
        band: [gen.observe_overrides(gen.generate(seed, seed, difficulty=band))["extra_overlap_count"]
               for seed in range(30)]
        for band in ("easy", "medium", "hard")
    }
    assert max(observed_counts["easy"]) <= min(observed_counts["hard"])
    assert observed_counts["easy"] != observed_counts["medium"]
    assert observed_counts["medium"] != observed_counts["hard"]


def test_fixed_canonical_color_shortcut_is_refuted():
    grid = gen.generate(
        41, 7,
        sec0_color=1,
        sec1_color=2,
        sec2_color=4,
        sec3_color=9,
        extra_overlap_count=5,
    )
    intended = apply_priority(grid)
    rival = fixed_canonical_color_priority(grid)
    assert intended != rival
    assert any(a != b for ra, rb in zip(intended, rival) for a, b in zip(ra, rb))


def test_self_check_rejects_minimal_impostors():
    assert gen.self_check([[1] * 19 for _ in range(4)])
    assert gen.self_check([[0] * 19 for _ in range(4)])
    assert gen.self_check([[0] * 18 for _ in range(4)])
    assert gen.self_check([[0] * 19 for _ in range(3)])


@pytest.mark.parametrize("pair", canonical_pairs())
def test_canonical_pairs_remain_in_domain_and_match_independent_oracle(pair):
    assert gen.strict_canonical_like(pair["input"]) == []
    assert gen.self_check(pair["input"]) == []
    assert apply_priority(pair["input"]) == pair["output"]


def test_semantic_contract_certifies_generated_lesson():
    demos = []
    for sample_index in range(3):
        grid = gen.generate(901, sample_index, difficulty="medium")
        demos.append({"input": grid, "output": apply_priority(grid)})
    query_grid = gen.generate(901, 3, difficulty="medium")
    assert gen.lesson_identifiable(demos, {"input": query_grid}) == []


def test_every_semantic_witness_has_a_causal_named_rival():
    assert set(gen.SEMANTIC_WITNESSES) == set(gen.WITNESS_RIVALS)
    fired = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    for seed in range(80):
        grid = gen.generate(seed, seed * 3 + 1, difficulty=("easy", "medium", "hard")[seed % 3])
        expected = gen.rule_mirror(grid)
        for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
            if not witness(grid):
                continue
            fired[witness_name] += 1
            rivals = gen.WITNESS_RIVALS[witness_name]
            assert rivals, witness_name
            assert any(gen.SEMANTIC_RIVALS[name](grid) != expected for name in rivals), witness_name
    assert all(count > 0 for count in fired.values()), fired


@pytest.mark.parametrize(
    ("seed", "sample_index", "difficulty"),
    [
        (True, 0, "easy"),
        (False, 0, None),
        (1.0, 0, "hard"),
        (1.75, 0, "easy"),
        ("1", 0, None),
        (991, True, "easy"),
        (991, False, None),
        (991, 1.0, "hard"),
        (991, 1.75, "easy"),
        (991, "1", None),
        (991, -1, "hard"),
        (991, 0, True),
        (991, 0, False),
        (991, 0, 0),
        (991, 0, 1.0),
        (991, 0, "__invalid_difficulty__"),
    ],
)
def test_common_call_arguments_reject_invalid_scalars(seed, sample_index, difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index, difficulty=difficulty)


def test_common_call_arguments_accept_documented_values():
    for difficulty in (None, "easy", "medium", "hard"):
        assert gen.self_check(gen.generate(991, 0, difficulty=difficulty)) == []
