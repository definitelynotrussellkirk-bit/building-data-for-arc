from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "39fd645f21c6"
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.39fd645f21c6.generator"
)
ROOT = find_root(__file__)


def load_task_pairs(task_id: str):
    return canonical_pairs(task_id, root=ROOT)


def canonical_rule_hash(task_id: str) -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == task_id and row.get("program_solution"):
                source = " ".join(str(row["program_solution"]).split())
                return hashlib.sha256(source.encode()).hexdigest()[:12]
    raise FileNotFoundError(f"{task_id}: no canonical program_solution")


def _episode(seed: int, difficulty: str = "medium"):
    grids = [
        GEN.generate(seed, index, difficulty=difficulty)
        for index in range(GEN.EXAMPLES_NEEDED + 1)
    ]
    pairs = [{"input": grid, "output": GEN.rule_mirror(grid)} for grid in grids]
    return pairs[:-1], pairs[-1]


def test_metadata_and_task_local_authority_are_pinned():
    assert GEN.GENERATOR_ID == TASK_ID
    assert GEN.TASK_ID == TASK_ID
    assert GEN.VERSION == "4.0.0"
    assert GEN.RULE_HASH == "36a57f0bfc36"
    assert canonical_rule_hash(TASK_ID) == GEN.RULE_HASH


def test_all_canonical_pairs_are_owned_and_python_mirror_is_exact():
    pairs = load_task_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("profile", tuple(GEN.SCENE_PROFILES))
@pytest.mark.parametrize("family", tuple(GEN.TARGET_TRIPLES))
@pytest.mark.parametrize("match_count", (1, 2))
def test_declared_override_product_is_exact(profile, family, match_count):
    requested = {
        "scene_profile": profile,
        "target_family": family,
        "match_count": match_count,
    }
    grid = GEN.generate(9137, 41, difficulty="hard", **requested)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == requested
    assert GEN.rule_mirror(grid) != grid


def test_unknown_override_and_invalid_difficulty_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, texture="plain")
    with pytest.raises(ValueError, match="unsupported difficulty"):
        GEN.generate(1, 0, difficulty="impossible")


def test_every_generated_scene_requires_the_full_feature_triple():
    for band in ("easy", "medium", "hard"):
        for index in range(60):
            grid = GEN.generate(80_000 + index, 13 + index, difficulty=band)
            obs = GEN.semantic_observables(grid)
            assert GEN.strict_canonical_like(grid) == []
            assert obs["all_matching_shapes_differ_from_seed"] is True
            assert set(obs["single_feature_decoys"]) == {"area", "holes", "symmetry"}
            assert obs["matching_count"] in (1, 2)


def test_semantic_witnesses_fire_in_every_band_and_refute_claimed_rivals():
    for band in ("easy", "medium", "hard"):
        counts = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
        for index in range(80):
            grid = GEN.generate(100_000 + index, 17 + index, difficulty=band)
            truth = GEN.rule_mirror(grid)
            for name, witness in GEN.SEMANTIC_WITNESSES.items():
                if witness(grid):
                    counts[name] += 1
                    claimed = GEN.WITNESS_RIVALS.get(name, ())
                    if claimed:
                        assert any(
                            GEN.SEMANTIC_RIVALS[rival](grid) != truth
                            for rival in claimed
                        ), (band, name, claimed)
        assert all(count > 0 for count in counts.values()), (band, counts)


def test_lesson_schedule_refutes_documented_shortcuts():
    for band in ("easy", "medium", "hard"):
        for seed in range(20):
            demos, query = _episode(seed, band)
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(demo["input"]) != demo["output"] for demo in demos), (
                    band,
                    seed,
                    name,
                )
        scheduled = [
            GEN.observe_overrides(GEN.generate(7, index, difficulty=band))
            for index in range(GEN.EXAMPLES_NEEDED)
        ]
        assert [item["target_family"] for item in scheduled] == [
            "plain_asym",
            "hole_asym",
            "plain_row",
        ]
        assert [item["match_count"] for item in scheduled] == [1, 2, 1]


def test_all_cyclic_query_rotations_refute_every_declared_competitor():
    for band in ("easy", "medium", "hard"):
        for lesson_index in range(8):
            seed = 390_000 + lesson_index
            start = 4 * lesson_index
            pairs = [
                {"input": (grid := GEN.generate(seed, start + offset, difficulty=band)),
                 "output": GEN.rule_mirror(grid)}
                for offset in range(4)
            ]
            for query_index in range(4):
                query = pairs[query_index]
                demos = pairs[query_index + 1:] + pairs[:query_index]
                assert GEN.lesson_identifiable(demos, query) == []
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(
                        rival(demo["input"]) != demo["output"]
                        for demo in demos
                    ), (band, lesson_index, query_index, name)


def test_exact_shape_shortcut_fits_canonical_but_generated_scenes_refute_it():
    shortcut = GEN.CANONICAL_SHORTCUTS["exact_shape"]
    for pair in load_task_pairs(TASK_ID):
        assert shortcut(pair["input"]) == pair["output"]
    for index in range(12):
        grid = GEN.generate(2026, index, difficulty="medium")
        assert shortcut(grid) != GEN.rule_mirror(grid)


def test_self_check_rejects_targeted_semantic_impostors():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 5
    for name, grid in fixtures:
        assert GEN.self_check(grid), name


def test_determinism_fresh_returns_and_global_rng_isolation():
    state = random.getstate()
    first = GEN.generate(444, 19, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(444, 19, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(444, 19, difficulty="medium") == second
