"""Focused regression tests for generator a4f0ea66fd65."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.runner import _apply_rule, _load_bundle, _open_bridge_with_rule, run_one
from scripts.coder_synth_verify import _as_pairs, _norm_grid

ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "data/canonical/puzzles.jsonl").exists()
)
TASK_ID = "a4f0ea66fd65"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical row missing")


def _canonical_pairs():
    row = _canonical_row()
    return _as_pairs(row.get("train")) + _as_pairs(row.get("test"))


def test_rule_hash_and_task_local_authorities_match_canonical():
    row = _canonical_row()
    normalized = " ".join(row["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == GEN.RULE_HASH
    base_path = ROOT / "data/base/solutions/banks/3cb9777539c7/E146__a4f0ea66fd65.json"
    base = json.loads(base_path.read_text())
    assert base["racket_target"]["raw_code"] == row["program_solution"]
    assert base["racket_target"]["target_code"] == row["program_solution"]


def test_regression_all_canonical_inputs_accepted_and_outputs_exact():
    for pair in _canonical_pairs():
        inp = _norm_grid(pair["input"])
        out = _norm_grid(pair["output"])
        before = copy.deepcopy(inp)
        assert GEN.self_check(inp) == []
        assert GEN.rule_mirror(inp) == out
        assert inp == before


def test_regression_canonical_overwrite_branch_is_owned():
    pair = _canonical_pairs()[-1]
    inp = _norm_grid(pair["input"])
    facts = GEN.semantic_observables(inp)
    assert facts["scene_profile"] == "canonical_right_overwrite"
    assert facts["collision_count"] == 2
    out = GEN.rule_mirror(inp)
    assert out[5][5] == 1 and out[5][6] == 1
    assert GEN.self_check(inp) == []


def test_six_slot_schedule_interleaves_exact_vector_and_overwrite_evidence():
    expected = [
        "canonical_right_clear",
        "general_overwrite",
        "canonical_left_clear",
        "canonical_right_overwrite",
        "general_clear",
        "canonical_left_overwrite",
    ]
    canonical_profile_contract = {
        "canonical_right_clear": ((8, 12), 5),
        "canonical_left_clear": ((9, 12), 5),
        "canonical_right_overwrite": ((8, 11), 4),
        "canonical_left_overwrite": ((8, 10), 3),
    }
    for band in ("easy", "medium", "hard"):
        observed = [
            GEN.observe_overrides(GEN.generate(20260724, index, difficulty=band))
            for index in range(6)
        ]
        assert [item["scene_profile"] for item in observed] == expected
        assert [item["object_size"] for item in observed] == [5, 8, 5, 4, 6, 3]
        assert {item["decoy_color"] for item in observed} == {6, 7}
        for item in observed:
            if item["scene_profile"] in canonical_profile_contract:
                dims, size = canonical_profile_contract[item["scene_profile"]]
                assert (item["grid_h"], item["grid_w"]) == dims
                assert item["object_size"] == size


def test_general_profiles_break_signed_two_by_three_quantization():
    quantized = GEN.SEMANTIC_RIVALS["quantized_2x3"]
    vectors = set()
    for band in ("easy", "medium", "hard"):
        for profile in ("general_clear", "general_overwrite"):
            for seed in range(12):
                grid = GEN.generate(7000 + seed, seed, difficulty=band, scene_profile=profile)
                vector = tuple(GEN.semantic_observables(grid)["vector"] )
                vectors.add(vector)
                assert quantized(grid) != GEN.rule_mirror(grid), (band, profile, seed, vector)
    assert any(dr == 0 or dc == 0 for dr, dc in vectors)
    assert any(max(abs(dr), abs(dc)) >= 4 for dr, dc in vectors)


def test_declared_canonical_shortcuts_fit_every_canonical_pair():
    assert set(GEN.CANONICAL_SHORTCUTS) == {"quantized_2x3", "canonical_sign_only"}
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        for pair in _canonical_pairs():
            assert shortcut(_norm_grid(pair["input"])) == _norm_grid(pair["output"]), name


def test_every_four_demo_window_refutes_every_declared_competitor():
    assert set(GEN.CANONICAL_SHORTCUTS) <= set(GEN.LESSON_COMPETITORS)
    for band in ("easy", "medium", "hard"):
        for seed in (17, 501, 99173):
            for start in range(len(GEN.SCENE_PROFILES)):
                demos = [
                    GEN.generate(seed, start + offset, difficulty=band)
                    for offset in range(GEN.EXAMPLES_NEEDED)
                ]
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(
                        rival(grid) != GEN.rule_mirror(grid) for grid in demos
                    ), (band, seed, start, name)


def test_semantic_witnesses_are_explicit_rival_claims_or_branch_coverage():
    claimed = set(GEN.WITNESS_RIVALS)
    branches = set(GEN.BRANCH_WITNESSES)
    assert not (claimed & branches)
    assert claimed | branches == set(GEN.SEMANTIC_WITNESSES)
    for band in ("easy", "medium", "hard"):
        for index in range(12):
            grid = GEN.generate(2718, index, difficulty=band)
            official = GEN.rule_mirror(grid)
            for witness_name, predicate in GEN.SEMANTIC_WITNESSES.items():
                if predicate(grid) and witness_name in GEN.WITNESS_RIVALS:
                    assert any(
                        GEN.SEMANTIC_RIVALS[name](grid) != official
                        for name in GEN.WITNESS_RIVALS[witness_name]
                    ), (band, index, witness_name)


def test_every_declared_override_boundary_is_exact_and_observable():
    cases = [
        {"grid_h": 8}, {"grid_h": 18}, {"grid_w": 8}, {"grid_w": 18},
        {"object_size": 3}, {"object_size": 8},
        {"decoy_color": 6}, {"decoy_color": 7},
    ] + [{"scene_profile": profile} for profile in GEN.SCENE_PROFILES]
    cases += [
        {"grid_h": 8, "grid_w": 8, "object_size": 8, "scene_profile": profile, "decoy_color": 7}
        for profile in GEN.SCENE_PROFILES
    ]
    for band in ("easy", "medium", "hard"):
        for case in cases:
            grid = GEN.generate(73, 13, difficulty=band, **case)
            observed = GEN.observe_overrides(grid)
            assert GEN.self_check(grid) == []
            for key, value in case.items():
                assert observed[key] == value, (band, case, observed)


def test_invalid_overrides_reject_loudly():
    for case in (
        {"grid_h": 7}, {"grid_w": 19}, {"object_size": 2},
        {"scene_profile": "fixed_vector"}, {"decoy_color": 5}, {"unknown_axis": 1},
    ):
        with pytest.raises(ValueError):
            GEN.generate(3, 3, difficulty="medium", **case)


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(981723)
    before = random.getstate()
    first = GEN.generate(91, 17, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(91, 17, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    snapshot = copy.deepcopy(first)
    second[0][0] = (second[0][0] + 1) % 10
    assert first == snapshot


def test_declared_mutation_fixtures_are_rejected():
    fixtures = dict(GEN.mutation_fixtures())
    assert len(fixtures) >= 4
    for name, grid in fixtures.items():
        assert GEN.self_check(grid), name


def test_negative_recombination_rejected_but_racket_oracle_executes():
    grid = GEN.generate(99221, 0, difficulty="medium")
    recombined = copy.deepcopy(grid)
    # Remove the original green marker and replace it at a previously empty
    # corner. This feature is absent from all remaining scene parts and makes
    # at least one translated cyan destination leave the grid.
    for r, row in enumerate(recombined):
        for c, value in enumerate(row):
            if value == 3:
                recombined[r][c] = 0
    red = next((r, c) for r, row in enumerate(recombined) for c, value in enumerate(row) if value == 2)
    candidates = [(0, 0), (0, len(recombined[0]) - 1), (len(recombined) - 1, 0), (len(recombined) - 1, len(recombined[0]) - 1)]
    replacement = next(cell for cell in candidates if recombined[cell[0]][cell[1]] == 0 and cell != red)
    recombined[replacement[0]][replacement[1]] = 3
    assert GEN.self_check(recombined)

    bundle = _load_bundle(TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        before = copy.deepcopy(recombined)
        output = _apply_rule(bridge, fn_name, recombined)
    finally:
        bridge.shutdown()
    assert recombined == before
    assert len(output) == len(recombined) and len(output[0]) == len(recombined[0])


def test_four_demo_materialized_lessons_identify_the_query_rule_from_every_schedule_residue():
    bundle = _load_bundle(TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        for band in ("easy", "medium", "hard"):
            for start in range(len(GEN.SCENE_PROFILES)):
                episode = run_one(
                    TASK_ID, seed=501, sample_index=start, n_train=4, n_test=1,
                    difficulty=band, bundle=bundle, bridge=bridge, fn_name=fn_name,
                )
                assert GEN.lesson_identifiable(episode["train"], episode["test"][0]) == []
                for pair in episode["train"] + episode["test"]:
                    assert pair["output"] == GEN.rule_mirror(pair["input"])
    finally:
        bridge.shutdown()
