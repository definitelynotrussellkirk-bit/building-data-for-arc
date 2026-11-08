from __future__ import annotations

import copy
import hashlib
import json
import random
import sys
from pathlib import Path

import pytest

TASK_ID = "5e619caf1f27"
for _parent in Path(__file__).resolve().parents:
    for _runtime in (_parent / "shared/runtime", _parent):
        if (_runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(_runtime))
            break
    else:
        continue
    break
from reviewer_support import (  # noqa: E402
    canonical_pairs as load_canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
)

ROOT = find_root(__file__)
GEN, _GENERATOR_SOURCE, _GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def canonical_pairs(task_id):
    return load_canonical_pairs(task_id, root=ROOT)


def canonical_rule_hash(task_id):
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    source = next(row["program_solution"] for row in rows if row.get("task_id") == task_id)
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def _episode(seed: int, start: int, difficulty: str):
    demos = []
    for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
        grid = GEN.generate(seed, sample_index, difficulty=difficulty)
        demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
    qidx = start + GEN.EXAMPLES_NEEDED
    query_grid = GEN.generate(seed, qidx, difficulty=difficulty)
    return demos, {"input": query_grid, "output": GEN.rule_mirror(query_grid)}


def test_all_canonical_pairs_are_owned_and_mirrored_without_mutation():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 6
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_rule_hash_matches_comment_preserving_selected_authority():
    assert GEN.RULE_HASH == canonical_rule_hash(TASK_ID) == "ca7c525a09b4"


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_four_slot_curriculum_cycles_both_thickness_regimes(difficulty):
    observed = []
    for sample_index, expected in enumerate(GEN.CURRICULUM_PROFILES * 3):
        grid = GEN.generate(314159, sample_index, difficulty=difficulty)
        assert GEN.self_check(grid, difficulty=difficulty) == []
        assert GEN.strict_canonical_like(grid) == []
        obs = GEN.semantic_observables(grid)
        observed.append(obs["profile"])
        assert obs["profile"] == expected
        assert obs["thickness"] >= 1
        if expected.startswith("edge_limited"):
            assert obs["edge_limited"] is True
            assert obs["thickness"] < min(obs["inner_h"], obs["inner_w"])
            assert (
                GEN.SEMANTIC_RIVALS["uncapped_inner_minimum"](grid)
                != GEN.rule_mirror(grid)
            )
        else:
            assert obs["edge_limited"] is False
            assert obs["inner_h"] != obs["inner_w"]
    assert observed == list(GEN.CURRICULUM_PROFILES) * 3


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_sliding_schedule_phase_is_lesson_identifiable(difficulty):
    for seed in (7, 97, 997):
        for start in range(8):
            demos, query = _episode(seed, start, difficulty)
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert not all(
                    rival(pair["input"]) == pair["output"] for pair in demos
                ), name


def test_named_witnesses_fire_and_every_rival_claim_is_true():
    witness_hits = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    for sample_index in range(80):
        grid = GEN.generate(271828 + sample_index, sample_index, difficulty="medium")
        authority = GEN.rule_mirror(grid)
        for witness_name, predicate in GEN.SEMANTIC_WITNESSES.items():
            if predicate(grid):
                witness_hits[witness_name] += 1
                for rival_name in GEN.WITNESS_RIVALS.get(witness_name, []):
                    assert GEN.SEMANTIC_RIVALS[rival_name](grid) != authority
    assert all(count > 0 for count in witness_hits.values()), witness_hits


def test_mutation_and_negative_recombination_fixtures_reject():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 6
    for name, grid in fixtures:
        assert GEN.self_check(grid), name
        assert GEN.strict_canonical_like(grid), name


def test_every_exact_dimension_pair_is_constructible_in_every_profile():
    for height in range(11, 23):
        for width in range(11, 23):
            for sample_index in range(4):
                grid = GEN.generate(
                    100000 + height * 1000 + width * 10 + sample_index,
                    sample_index,
                    difficulty="medium",
                    grid_h=height,
                    grid_w=width,
                )
                requested = {"grid_h": height, "grid_w": width}
                assert GEN.observe_overrides(grid) == requested
                assert GEN.self_check(
                    grid, difficulty="medium", meta={"overrides": requested}
                ) == []
                assert GEN.semantic_observables(grid)["profile"] == GEN.CURRICULUM_PROFILES[sample_index]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown_axis": 1},
        {"grid_h": 10},
        {"grid_h": 23},
        {"grid_w": 10},
        {"grid_w": 23},
        {"grid_h": "11"},
        {"grid_w": True},
    ],
)
def test_unknown_and_out_of_range_overrides_reject(kwargs):
    with pytest.raises((TypeError, ValueError, AssertionError)):
        GEN.generate(99, 0, difficulty="easy", **kwargs)


def test_deterministic_fresh_returns_and_global_rng_safety():
    random.seed(90210)
    state = random.getstate()
    first = GEN.generate(1234, 2, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(1234, 2, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    replay = GEN.generate(1234, 2, difficulty="hard")
    assert replay[0][0] != 9
    assert random.getstate() == state


def test_seed_index_and_band_change_content_without_changing_semantics():
    grids = [
        GEN.generate(seed, index, difficulty=band)
        for seed, index, band in (
            (100, 0, "easy"),
            (101, 0, "easy"),
            (100, 1, "medium"),
            (101, 1, "medium"),
            (100, 2, "hard"),
            (101, 3, "hard"),
        )
    ]
    assert len({_digest(grid) for grid in grids}) >= 5
    assert all(GEN.self_check(grid) == [] for grid in grids)
