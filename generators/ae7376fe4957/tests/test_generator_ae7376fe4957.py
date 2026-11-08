"""Regression tests for the marker-offset translation generator repair."""
from __future__ import annotations

import copy
import importlib
import importlib.util
import random
from pathlib import Path

import pytest


from reviewer_support import canonical_pairs, find_root


ROOT = find_root(__file__)


def official_pairs():
    return canonical_pairs(GEN.TASK_ID, root=ROOT)


GEN = importlib.import_module("puzzle_generators.per_puzzle.ae7376fe4957.generator")


def test_canonical_inputs_are_accepted_and_solved_exactly():
    pairs = official_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_canonical_signature_bank_is_derived_exactly():
    signatures = {
        GEN.canonical_profile_signature(pair["input"]) for pair in official_pairs()
    }
    assert signatures == GEN._CANONICAL_SIGNATURES


def test_linked_recombination_is_lawful_but_not_canonical_like():
    pairs = official_pairs()
    base = copy.deepcopy(pairs[0]["input"])
    donor = pairs[1]["input"]
    facts = GEN.semantic_observables(base)
    source, target = facts["source"], facts["target"]
    for row in range(len(base)):
        for col in range(len(base[0])):
            if (row, col) not in (source, target):
                base[row][col] = 0
    donor_facts = GEN.semantic_observables(donor)
    dr0, dc0 = donor_facts["source"]
    for row, col, value in donor_facts["payload"]:
        rr = source[0] + row - dr0
        cc = source[1] + col - dc0
        if 0 <= rr < len(base) and 0 <= cc < len(base[0]) and (rr, cc) not in (source, target):
            base[rr][cc] = value
    # The broad oracle grammar remains valid, but the linked official profile is not.
    assert GEN.self_check(base) == []
    assert GEN.strict_canonical_like(base)


def test_default_schedule_covers_profiles_branches_and_rivals_in_each_band():
    for band in ("easy", "medium", "hard"):
        strict = 0
        clipping = set()
        quadrants = set()
        rival_hits = {name: 0 for name in GEN.SEMANTIC_RIVALS}
        for sample_index in range(200):
            grid = GEN.generate(7919, sample_index, difficulty=band)
            assert GEN.self_check(grid, difficulty=band) == []
            facts = GEN.semantic_observables(grid)
            strict += GEN.strict_canonical_like(grid) == []
            clipping.add(facts["clipping_mode"])
            quadrants.add(facts["shift_quadrant"])
            for name, rival in GEN.SEMANTIC_RIVALS.items():
                rival_hits[name] += GEN.rule_mirror(grid) != rival(grid)
        assert strict >= 40
        assert clipping == set(GEN._CLIPPING_MODES)
        assert quadrants == set(GEN._QUADRANTS)
        assert all(count > 0 for count in rival_hits.values())


def test_every_override_axis_is_exact_at_both_boundaries():
    boundary_cases = {
        "grid_h": (9, 18),
        "grid_w": (9, 18),
        "payload_cells": (6, 12),
        "palette_size": (2, 4),
        "extra_reds": (0, 2),
    }
    for name, values in boundary_cases.items():
        for value in values:
            grid = GEN.generate(33, 17, difficulty="medium", **{name: value})
            assert GEN.self_check(grid, meta={"overrides": {name: value}}) == []
            assert GEN.observe_overrides(grid)[name] == value


def test_unknown_override_is_rejected():
    with pytest.raises(TypeError):
        GEN.generate(0, 0, nonexistent_axis=1)


def test_self_check_rejects_structural_mutations():
    grid = GEN.generate(15, 9, difficulty="medium")

    no_source = copy.deepcopy(grid)
    source = GEN.semantic_observables(no_source)["source"]
    no_source[source[0]][source[1]] = 0
    assert GEN.self_check(no_source)

    duplicate_source = copy.deepcopy(grid)
    target = GEN.semantic_observables(duplicate_source)["target"]
    duplicate_source[0][0] = 1
    if target == (0, 0):
        duplicate_source[0][1] = 1
    assert GEN.self_check(duplicate_source)

    no_target = copy.deepcopy(grid)
    for row in range(len(no_target)):
        for col in range(len(no_target[0])):
            if no_target[row][col] == 2:
                no_target[row][col] = 3
    assert GEN.self_check(no_target)

    no_payload = [[0 for _ in row] for row in grid]
    no_payload[1][1] = 1
    no_payload[2][2] = 2
    assert GEN.self_check(no_payload)


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(123456)
    before = random.getstate()
    first = GEN.generate(91, 23, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(91, 23, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    first[0][0] = (first[0][0] + 1) % 10
    assert GEN.generate(91, 23, difficulty="hard") == second


def test_multi_red_scene_refutes_nearest_last_and_drop_red_shortcuts():
    for sample_index in range(1, 20):
        grid = GEN.generate(0, sample_index, difficulty="medium")
        facts = GEN.semantic_observables(grid)
        if facts["extra_reds"]:
            official = GEN.rule_mirror(grid)
            assert official != GEN.rival_drop_all_red_payload(grid)
            assert official != GEN.rival_use_last_red_target(grid)
            assert official != GEN.rival_use_nearest_red_target(grid)
            return
    raise AssertionError("scheduled multi-red witness did not appear")


def test_scheduled_lessons_refute_all_named_competitors():
    pairs = []
    for sample_index in range(4):
        grid = GEN.generate(123, sample_index, difficulty="medium")
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
    assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_every_rotated_three_demo_window_is_identifiable_across_schedule_residues():
    checked = 0
    lesson_size = GEN.EXAMPLES_NEEDED + 1
    for band in ("easy", "medium", "hard"):
        for seed in range(16):
            for start in range(48):
                pairs = []
                for sample_index in range(start, start + lesson_size):
                    grid = GEN.generate(seed, sample_index, difficulty=band)
                    pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
                for query_index in range(lesson_size):
                    demos = [
                        pair for index, pair in enumerate(pairs) if index != query_index
                    ]
                    assert GEN.lesson_identifiable(demos, pairs[query_index]) == [], (
                        band,
                        seed,
                        start,
                        query_index,
                    )
                    checked += 1
    assert checked == 9216


def test_workspace_shortcut_audit_is_declaration_driven_and_rotation_aware():
    path = ROOT / "generators" / GEN.TASK_ID / "workspace" / "shortcut_audit.py"
    spec = importlib.util.spec_from_file_location("ae7376fe4957_shortcut_audit", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    report = module.audit(seed_count=2, start_count=8)
    assert set(report["declared_shortcuts"]) == set(GEN.CANONICAL_SHORTCUTS)
    assert report["canonical_fitting_shortcuts"] == ["use_nearest_red_target"]
    assert all(report["generated_refutations"].values())
    assert report["rotation_failures"] == []
    assert report["rotations_checked"] == 3 * 2 * 8 * 4


def test_scheduled_inputs_keep_drop_red_rival_total():
    grid = GEN.generate(0, 7, difficulty="easy")
    assert GEN.semantic_observables(grid)["extra_reds"] == 2
    assert GEN.rival_drop_all_red_payload(grid)
