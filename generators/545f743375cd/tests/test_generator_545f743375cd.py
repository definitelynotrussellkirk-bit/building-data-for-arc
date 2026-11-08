"""Focused regression tests for generator 545f743375cd."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.runner import _apply_rule, _load_bundle, _open_bridge_with_rule, run_one
from scripts.check_task_authority_sync import strip_racket_comments
from scripts.coder_synth_verify import _as_pairs, _norm_grid

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "545f743375cd"
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


def test_rule_hash_and_selected_authority_match_canonical_without_losing_comments():
    row = _canonical_row()
    normalized = " ".join(row["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == GEN.RULE_HASH
    base_path = ROOT / "data/base/solutions/banks/3b7f019624a4/M43__545f743375cd.json"
    base = json.loads(base_path.read_text())
    target = base["racket_target"]
    assert target["target_code"] == row["program_solution"]
    assert ";;" in target["raw_code"]
    assert " ".join(strip_racket_comments(target["raw_code"]).split()) == normalized


def test_all_canonical_inputs_are_accepted_and_outputs_are_exact():
    clipped_counts = []
    for pair in _canonical_pairs():
        inp = _norm_grid(pair["input"])
        out = _norm_grid(pair["output"])
        before = copy.deepcopy(inp)
        assert GEN.self_check(inp) == []
        assert GEN.strict_canonical_like(inp) == []
        assert GEN.rule_mirror(inp) == out
        assert inp == before
        clipped_counts.append(GEN.semantic_observables(inp)["in_bounds_target_count"])
    assert clipped_counts == [4, 3, 2, 4, 0]


def test_eight_slot_schedule_covers_vectors_clipping_and_anchors_in_every_band():
    expected_vectors = list(GEN.VECTOR_PROFILES)
    expected_clip = ["full", "partial", "partial", "full", "partial", "full", "partial", "full"]
    for band in ("easy", "medium", "hard"):
        observed = [
            GEN.observe_overrides(GEN.generate(20260725, index, difficulty=band))
            for index in range(8)
        ]
        assert [item["vector_profile"] for item in observed] == expected_vectors
        assert [item["clip_profile"] for item in observed] == expected_clip
        assert {item["marker_anchor"] for item in observed} == {"edge", "interior"}
        assert {item["decoration_anchor"] for item in observed} == {"corner", "edge", "interior"}
        assert [(item["grid_h"], item["grid_w"]) for item in observed[:5]] == [
            (10, 12), (11, 12), (10, 13), (11, 12), (10, 13)
        ]


def test_every_declared_override_boundary_is_exact_and_observable():
    cases = [
        {"grid_h": 10}, {"grid_h": 16}, {"grid_w": 11}, {"grid_w": 16},
        {"marker_anchor": "edge"}, {"marker_anchor": "interior"},
        {"decoration_anchor": "corner"}, {"decoration_anchor": "edge"},
        {"decoration_anchor": "interior"}, {"clip_profile": "full"},
        {"clip_profile": "partial"},
    ]
    cases += [{"vector_profile": name} for name in GEN.VECTOR_PROFILES]
    cases += [{"blob_shape": name} for name in GEN.BLOB_SHAPES]
    cases += [
        {
            "grid_h": 10,
            "grid_w": 11,
            "vector_profile": vector,
            "blob_shape": shape,
            "clip_profile": clip,
            "marker_anchor": marker,
            "decoration_anchor": decoration,
        }
        for vector in GEN.VECTOR_PROFILES
        for shape in ("hook_top", "tee_top")
        for clip in ("full", "partial")
        for marker in GEN.MARKER_ANCHORS
        for decoration in GEN.DECORATION_ANCHORS
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
        {"grid_h": 9}, {"grid_w": 10}, {"grid_w": 17}, {"vector_profile": "fixed"},
        {"blob_shape": "square"}, {"clip_profile": "all_out"},
        {"marker_anchor": "corner"}, {"decoration_anchor": "random"},
        {"unknown_axis": 1},
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


def test_negative_recombination_is_rejected_but_racket_oracle_executes_purely():
    fixtures = dict(GEN.mutation_fixtures())
    recombined = fixtures["decoration_recombined_into_target"]
    assert GEN.self_check(recombined)
    assert sum(value == 5 for row in recombined for value in row) == 1

    bundle = _load_bundle(TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        before = copy.deepcopy(recombined)
        output = _apply_rule(bridge, fn_name, recombined)
    finally:
        bridge.shutdown()
    assert recombined == before
    assert len(output) == len(recombined) and len(output[0]) == len(recombined[0])


def test_four_demo_lessons_refute_every_named_competitor():
    for band in ("easy", "medium", "hard"):
        for start in (0, 17, 34):
            episode = run_one(
                TASK_ID,
                seed=501 + start,
                sample_index=start,
                n_train=4,
                n_test=1,
                difficulty=band,
            )
            assert GEN.lesson_identifiable(episode["train"], episode["test"][0]) == []
            survivors = set(GEN.LESSON_COMPETITORS)
            for pair in episode["train"]:
                official = tuple(map(tuple, pair["output"]))
                survivors &= {
                    name
                    for name, competitor in GEN.LESSON_COMPETITORS.items()
                    if tuple(map(tuple, competitor(pair["input"]))) == official
                }
            assert not survivors
            for pair in episode["train"] + episode["test"]:
                assert pair["output"] == GEN.rule_mirror(pair["input"])
