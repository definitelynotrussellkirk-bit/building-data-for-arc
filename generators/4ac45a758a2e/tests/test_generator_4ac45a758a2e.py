"""Focused regressions for the rotation/reflection control generator."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import re

import pytest

from puzzle_generators.base import set_ctx_observer
from reviewer_support import (
    canonical_pairs as load_canonical_pairs,
    canonical_path,
    find_root,
)


ROOT = find_root(__file__)
TASK_ID = "4ac45a758a2e"
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.4ac45a758a2e.generator"
)
BANDS = ("easy", "medium", "hard")


def _canonical_row() -> dict:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise KeyError(TASK_ID)


def _canonical_pairs() -> list[dict]:
    return load_canonical_pairs(TASK_ID, root=ROOT)


def _normalized_source(source: str) -> str:
    return " ".join(source.split())


def _comment_stripped(source: str) -> str:
    return "\n".join(re.sub(r";.*$", "", line) for line in source.splitlines())


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def test_rule_hash_and_source_roles_are_synchronized_without_losing_comments():
    row = _canonical_row()
    expected = hashlib.sha256(
        _normalized_source(row["program_solution"]).encode()
    ).hexdigest()[:12]
    assert GEN.RULE_HASH == expected == "6259c8fd93a1"

    base = json.loads(
        (
            ROOT
            / "data/base/solutions/banks/d3d681cdb82a/H54__4ac45a758a2e.json"
        ).read_text()
    )
    racket = base["racket_target"]
    assert racket["target_code"] == row["program_solution"]
    assert ";;" in racket["raw_code"]
    assert _normalized_source(_comment_stripped(racket["raw_code"])) == _normalized_source(
        row["program_solution"]
    )


def test_all_canonical_inputs_are_accepted_and_python_mirror_matches_outputs():
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_all_exact_override_boundaries_are_observable():
    cases = (
        {"grid_h": 11, "grid_w": 11, "rot_count": 1, "ref_count": 1, "template_cells": 4},
        {"grid_h": 17, "grid_w": 17, "rot_count": 4, "ref_count": 2, "template_cells": 7},
        {"grid_h": 11, "grid_w": 17, "rot_count": 2, "ref_count": 2, "template_cells": 6},
        {"grid_h": 17, "grid_w": 11, "rot_count": 3, "ref_count": 1, "template_cells": 5},
    )
    for band in BANDS:
        for index, overrides in enumerate(cases):
            grid = GEN.generate(4000 + index, 100 + index, difficulty=band, **overrides)
            assert GEN.self_check(grid, meta={"overrides": overrides}) == []
            assert GEN.observe_overrides(grid) == overrides

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, texture="varied")


def test_default_draw_provenance_matches_every_observed_axis():
    for band_index, band in enumerate(BANDS):
        for index in range(24):
            captured = []
            set_ctx_observer(captured.append)
            try:
                grid = GEN.generate(
                    10_000 + 100 * band_index + index,
                    200 + index,
                    difficulty=band,
                )
            finally:
                set_ctx_observer(None)
            assert len(captured) == 1
            observed = GEN.observe_overrides(grid)
            assert set(observed) == set(GEN.AXES)
            for axis, value in observed.items():
                assert captured[0].axis_value(axis) == value


def test_schedule_covers_all_eight_control_pairs_in_any_consecutive_lesson():
    expected = set(GEN._PROFILE_ORDER)
    for start in range(16):
        observed = {
            (
                GEN.observe_overrides(grid)["rot_count"],
                GEN.observe_overrides(grid)["ref_count"],
            )
            for grid in (
                GEN.generate(77, start + offset, difficulty="medium")
                for offset in range(8)
            )
        }
        assert observed == expected


def test_eight_demo_lessons_are_identifiable_and_eliminate_named_rivals():
    for band in BANDS:
        for start in (0, 5, 11):
            demos = [
                _pair(GEN.generate(8800 + start, start + offset, difficulty=band))
                for offset in range(8)
            ]
            query = _pair(GEN.generate(8800 + start, start + 8, difficulty=band))
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert not all(
                    rival(pair["input"]) == pair["output"] for pair in demos
                ), name


def test_semantic_witnesses_fire_and_named_rival_claims_disagree():
    hits = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    for index in range(64):
        grid = GEN.generate(12_000 + index, index, difficulty="hard")
        truth = GEN.rule_mirror(grid)
        for witness, predicate in GEN.SEMANTIC_WITNESSES.items():
            if not predicate(grid):
                continue
            hits[witness] += 1
            assert any(
                GEN.SEMANTIC_RIVALS[name](grid) != truth
                for name in GEN.WITNESS_RIVALS[witness]
            )
    assert all(count > 0 for count in hits.values())


def test_mutation_fixtures_and_negative_recombination_are_rejected():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert GEN.self_check(grid), name

    # Negative recombination: remove the entire red control feature.  No red
    # replacement appears elsewhere, so the missing control cannot be inferred
    # from another scene part.
    recombined = GEN.generate(31337, 6, difficulty="medium")
    for row in recombined:
        for col, value in enumerate(row):
            if value == 2:
                row[col] = 0
    assert not any(value == 2 for row in recombined for value in row)
    assert GEN.self_check(recombined)


def test_determinism_fresh_returns_and_process_rng_isolation():
    random.seed(1459)
    state = random.getstate()
    first = GEN.generate(444, 19, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(444, 19, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert GEN.generate(444, 19, difficulty="hard") == second

    easy = GEN.generate(444, 19, difficulty="easy")
    medium = GEN.generate(444, 19, difficulty="medium")
    hard = GEN.generate(444, 19, difficulty="hard")
    assert len({_frozen(easy), _frozen(medium), _frozen(hard)}) == 3


def test_linked_semantic_census_and_disjoint_stability_are_count_backed():
    for cohort in range(2):
        for band_index, band in enumerate(BANDS):
            draws = 200
            strict_hits = 0
            unique = set()
            witnesses = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
            for index in range(draws):
                grid = GEN.generate(
                    100_000 * (cohort + 1) + 10_000 * band_index + index,
                    1000 + index,
                    difficulty=band,
                )
                assert GEN.self_check(grid) == []
                strict_hits += not GEN.strict_canonical_like(grid)
                unique.add(_frozen(grid))
                for name, predicate in GEN.SEMANTIC_WITNESSES.items():
                    witnesses[name] += bool(predicate(grid))
            assert strict_hits == draws
            assert len(unique) >= 195
            assert all(count >= 20 for count in witnesses.values())


def test_default_schedule_does_not_encode_rotation_in_template_size():
    """Every blue-count branch must occur with every ordinary template size."""
    for band in BANDS:
        sizes_by_rotation = {rotation: set() for rotation in range(1, 5)}
        for sample_index in range(32):
            facts = GEN.observe_overrides(
                GEN.generate(23_000, sample_index, difficulty=band)
            )
            sizes_by_rotation[facts["rot_count"]].add(facts["template_cells"])
        assert sizes_by_rotation == {
            rotation: {4, 5, 6, 7} for rotation in range(1, 5)
        }


def test_query_refutes_demo_learned_template_size_rotation_lookup():
    """An eight-demo lesson must not let template area replace blue counting."""
    for band in BANDS:
        for start in range(32):
            demos = [
                GEN.observe_overrides(
                    GEN.generate(31_000, start + offset, difficulty=band)
                )
                for offset in range(8)
            ]
            query = GEN.observe_overrides(
                GEN.generate(31_000, start + 8, difficulty=band)
            )

            size_to_rotation = {}
            contradictory_demo = False
            for facts in demos:
                size = facts["template_cells"]
                rotation = facts["rot_count"]
                prior = size_to_rotation.setdefault(size, rotation)
                contradictory_demo |= prior != rotation

            predicted = size_to_rotation.get(query["template_cells"])
            shortcut_survives = (
                not contradictory_demo and predicted == query["rot_count"]
            )
            assert not shortcut_survives, {
                "band": band,
                "start": start,
                "size_to_rotation": size_to_rotation,
                "query": query,
            }


def test_lesson_guard_rejects_template_size_as_a_rotation_proxy():
    """The lesson contract must catch a nuisance axis replacing blue counting."""
    demos = []
    for offset, (rotation, reflection) in enumerate(GEN._PROFILE_ORDER):
        grid = GEN.generate(
            41_000,
            offset,
            difficulty="medium",
            rot_count=rotation,
            ref_count=reflection,
            template_cells=3 + rotation,
        )
        demos.append(_pair(grid))

    query_grid = GEN.generate(
        41_000,
        8,
        difficulty="medium",
        rot_count=1,
        ref_count=1,
        template_cells=4,
    )
    reasons = GEN.lesson_identifiable(demos, _pair(query_grid))
    assert any("template size" in reason for reason in reasons), reasons
