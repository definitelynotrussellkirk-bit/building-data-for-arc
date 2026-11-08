"""Focused semantic and regression tests for generator 746afba14f72."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest

from puzzle_generators.base import set_ctx_observer

TASK_ID = "746afba14f72"
ROOT = Path(__file__).resolve().parents[1]
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.746afba14f72.generator"
)
AUTHORITY = (
    ROOT
    / "data/base/solutions/banks/110177dcbe3a/E117__746afba14f72.json"
)


def _canonical_row() -> dict:
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    test = row["test"]
    return list(row["train"]) + (list(test) if isinstance(test, list) else [test])


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_metadata_rule_hash_and_active_authority_sync() -> None:
    row = _canonical_row()
    authority = json.loads(AUTHORITY.read_text())
    assert GEN.VERSION == "2.0.0"
    assert GEN.RULE_HASH == "7da5ba3f320f"
    assert GEN.RULE_HASH == _normalized_hash(row["program_solution"])
    assert authority["racket_target"]["target_code"] == row["program_solution"]


def test_all_canonical_pairs_are_accepted_and_mirror_exact() -> None:
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_exact_boundary_overrides_and_observer() -> None:
    cases = [
        {
            "grid_h": 8,
            "grid_w": 7,
            "cavities": 2,
            "n_colors": 2,
            "texture": "plus",
            "distractor_kind": "partial",
            "color_relation": "shared",
        },
        {
            "grid_h": 16,
            "grid_w": 16,
            "cavities": 3,
            "n_colors": 4,
            "texture": "ring",
            "distractor_kind": "mismatch",
            "color_relation": "varied",
        },
        {
            "grid_h": 11,
            "grid_w": 12,
            "cavities": 3,
            "n_colors": 3,
            "texture": "side_band",
            "distractor_kind": "diagonal",
            "color_relation": "shared",
        },
    ]
    for band in ("easy", "medium", "hard"):
        for seed, case in enumerate(cases):
            grid = GEN.generate(seed, 17, difficulty=band, **case)
            assert GEN.self_check(grid) == []
            assert GEN.observe_overrides(grid) == case


def test_unknown_or_out_of_range_overrides_reject_loudly() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 2, texture_leak="ring")
    with pytest.raises(ValueError, match="outside"):
        GEN.generate(1, 2, grid_h=7)
    with pytest.raises(ValueError, match="outside"):
        GEN.generate(1, 2, n_colors=5)


def test_ordinary_keyed_semantic_draws_equal_returned_observables() -> None:
    exact_axes = set(GEN.AXES)
    for band in ("easy", "medium", "hard"):
        for seed in range(24):
            captured = []
            set_ctx_observer(captured.append)
            try:
                grid = GEN.generate(seed, seed * 11 + 3, difficulty=band)
            finally:
                set_ctx_observer(None)
            assert len(captured) == 1
            drawn = captured[0].recorded_draws()
            observed = GEN.observe_overrides(grid)
            assert {axis: drawn[axis] for axis in exact_axes} == observed


def test_self_check_rejects_targeted_structural_impostors() -> None:
    base = GEN.generate(
        42,
        7,
        difficulty="medium",
        texture="ring",
        distractor_kind="partial",
        color_relation="shared",
    )
    facts = GEN._analyze(base)
    r, c = facts["positive_centers"][0]
    color = facts["positive_colors"][0]

    ragged = copy.deepcopy(base)
    ragged[0].pop()

    broken_arm = copy.deepcopy(base)
    broken_arm[r - 1][c] = 0

    prefilled_cavity = copy.deepcopy(base)
    prefilled_cavity[r][c] = color

    mismatched_arm = copy.deepcopy(base)
    mismatched_arm[r - 1][c] = color % 9 + 1

    foreign_diagonal = copy.deepcopy(base)
    foreign_diagonal[r - 1][c - 1] = color % 9 + 1

    for name, grid in {
        "ragged": ragged,
        "broken_arm": broken_arm,
        "prefilled_cavity": prefilled_cavity,
        "mismatched_arm": mismatched_arm,
        "foreign_diagonal": foreign_diagonal,
    }.items():
        assert GEN.self_check(grid), name


def test_negative_recombination_is_distribution_invalid_but_oracle_defined() -> None:
    # Replace one positive with a two-arm L. That feature is absent from every
    # remaining motif (positives have four arms; the explicit partial has three).
    grid = GEN.generate(
        91,
        5,
        difficulty="medium",
        texture="plus",
        distractor_kind="partial",
    )
    facts = GEN._analyze(grid)
    r, c = facts["positive_centers"][0]
    impostor = copy.deepcopy(grid)
    impostor[r + 1][c] = 0
    impostor[r][c + 1] = 0
    assert GEN.self_check(impostor)
    # The mathematical rule is total on this malformed teaching scene.
    assert GEN.rule_mirror(impostor)


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(20260726)
    state = random.getstate()
    first = GEN.generate(991, 37, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(991, 37, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    pristine = copy.deepcopy(second)
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(991, 37, difficulty="hard") == pristine


def test_three_demo_schedule_identifies_every_named_competitor() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(36):
            pairs = []
            for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
                grid = GEN.generate(30_000 + start, sample_index, difficulty=band)
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
            assert GEN.lesson_identifiable(pairs[:-1], pairs[-1]) == []


def test_linked_semantic_and_disjoint_stability_census_200_per_band() -> None:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        witness_counts = Counter()
        profiles = Counter()
        grids = []
        for offset in range(200):
            seed = 100_000 + band_index * 10_000 + offset
            sample_index = 7_000 + offset * 10
            grid = GEN.generate(seed, sample_index, difficulty=band)
            assert GEN.self_check(grid) == []
            assert GEN.rule_mirror(grid) != grid
            grids.append(grid)
            profiles[GEN.schedule_profile(seed, sample_index, band)] += 1
            witness_counts.update(
                name
                for name, predicate in GEN.SEMANTIC_WITNESSES.items()
                if predicate(grid)
            )
        assert set(witness_counts) == set(GEN.SEMANTIC_WITNESSES)
        assert set(profiles) == set(GEN.SCHEDULE_PROFILES)
        assert len({_frozen(grid) for grid in grids}) >= 198
        assert len({_frozen(GEN.rule_mirror(grid)) for grid in grids}) >= 190

        stable = [
            GEN.generate(
                800_000 + band_index * 10_000 + offset,
                90_000 + offset * 17,
                difficulty=band,
            )
            for offset in range(200)
        ]
        assert all(GEN.self_check(grid) == [] for grid in stable)
        first_set = {_frozen(grid) for grid in grids}
        stable_set = {_frozen(grid) for grid in stable}
        assert len(stable_set) >= 198
        assert first_set != stable_set
        assert len(first_set & stable_set) <= 2
