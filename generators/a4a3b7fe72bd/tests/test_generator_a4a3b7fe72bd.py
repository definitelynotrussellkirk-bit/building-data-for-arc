"""Regression and semantic-contract tests for generator a4a3b7fe72bd."""
from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.a4a3b7fe72bd import generator as gen

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PATHS = (
    ROOT / "data/base/solutions/training/3ee1011a__a4a3b7fe72bd.json",
    ROOT / "data/base/solutions/augmented/3ee1011a__fe54eca8ca63.json",
)


def _canonical_rows():
    rows = []
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                rows.append(row)
    return rows


def _canonical_pairs():
    for row in _canonical_rows():
        for split in ("train", "test"):
            for index, pair in enumerate(row.get(split) or []):
                yield row["content_hash"], split, index, pair


def test_rule_pin_and_selected_authorities_match_canonical_program():
    rows = _canonical_rows()
    assert len(rows) == 2
    programs = {row["program_solution"] for row in rows}
    assert len(programs) == 1
    canonical = programs.pop()
    assert gen.RULE_HASH == "7db7ae0bc165"

    for path in AUTHORITY_PATHS:
        target = json.loads(path.read_text(encoding="utf-8"))["racket_target"]
        assert target["target_code"] == canonical
        assert target["raw_code"] != canonical
        assert target["canonicalization_status"] == (
            "selected_matches_canonical_archival_preserved"
        )


def test_every_canonical_pair_is_accepted_and_reproduced():
    reviewed = 0
    unique_inputs = set()
    signatures = set()
    for content_hash, split, index, pair in _canonical_pairs():
        reviewed += 1
        grid = pair["input"]
        assert gen.self_check(grid) == [], (content_hash, split, index)
        assert gen.strict_canonical_like(grid) == []
        assert gen.rule_mirror(grid) == pair["output"]
        signatures.add(gen.canonical_profile_signature(grid))
        unique_inputs.add(json.dumps(grid, separators=(",", ":")))
    assert reviewed == 8
    assert len(unique_inputs) == 4
    assert signatures == {(21, 22, 3), (23, 29, 3), (24, 20, 4), (21, 23, 4)}


def test_scheduled_four_pair_lesson_is_identifiable_and_branch_complete():
    pairs = []
    for sample_index in range(4):
        grid = gen.generate(1000 + sample_index, sample_index, difficulty="medium")
        assert gen.self_check(grid) == []
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
    assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []

    facts = [gen.observe_overrides(pair["input"]) for pair in pairs]
    assert {fact["n_colors"] for fact in facts} == {3, 4}
    assert {fact["max_length"] for fact in facts} == {5, 6, 7, 8}
    assert {fact["line_orientation"] for fact in facts} == {
        "horizontal_only",
        "vertical_only",
        "mixed",
    }
    assert {fact["length_profile"] for fact in facts} == {"step2", "irregular"}


def test_determinism_fresh_returns_and_global_rng_isolation():
    state = random.getstate()
    first = gen.generate(90210, 17, difficulty="hard")
    second = gen.generate(90210, 17, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert gen.generate(90210, 17, difficulty="hard") == second


def test_every_individual_override_boundary_is_exact_in_every_band():
    cases = (
        {"grid_h": 14},
        {"grid_h": 29},
        {"grid_w": 14},
        {"grid_w": 29},
        {"n_colors": 2},
        {"n_colors": 4},
        {"max_length": 3},
        {"max_length": 8},
        {"length_profile": "step2"},
        {"length_profile": "consecutive"},
        {"length_profile": "irregular"},
        {"line_orientation": "horizontal_only"},
        {"line_orientation": "vertical_only"},
        {"line_orientation": "mixed"},
    )
    for difficulty in ("easy", "medium", "hard"):
        for case in cases:
            grid = gen.generate(31, 3, difficulty=difficulty, **case)
            observed = gen.observe_overrides(grid)
            assert gen.self_check(grid, meta={"overrides": case}) == []
            assert all(observed[key] == value for key, value in case.items())


def test_compatible_multi_axis_overrides_are_exact_and_conflicts_are_loud():
    cases = (
        {
            "grid_h": 14,
            "grid_w": 29,
            "n_colors": 2,
            "max_length": 4,
            "length_profile": "irregular",
            "line_orientation": "horizontal_only",
        },
        {
            "grid_h": 29,
            "grid_w": 14,
            "n_colors": 4,
            "max_length": 8,
            "length_profile": "consecutive",
            "line_orientation": "vertical_only",
        },
    )
    for case in cases:
        grid = gen.generate(77, 8, difficulty="hard", **case)
        assert gen.observe_overrides(grid) == case

    with pytest.raises(ValueError, match="incompatible semantic overrides"):
        gen.generate(1, 1, n_colors=2, max_length=8)
    with pytest.raises(ValueError, match="incompatible semantic overrides"):
        gen.generate(1, 1, max_length=3, length_profile="irregular")
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 1, bogus_axis=7)
    with pytest.raises(ValueError, match="unknown difficulty"):
        gen.generate(1, 1, difficulty="impossible")


def test_declared_semantic_witnesses_fire_in_each_band():
    for difficulty in ("easy", "medium", "hard"):
        hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
        for sample_index in range(32):
            grid = gen.generate(4000 + sample_index, sample_index, difficulty=difficulty)
            assert gen.strict_canonical_like(grid) == []
            for name, predicate in gen.SEMANTIC_WITNESSES.items():
                hits[name] += bool(predicate(grid))
        assert all(count > 0 for count in hits.values()), (difficulty, hits)


def test_mutation_fixtures_reject_task_semantic_impostors():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 6
    assert "absent_l_shape_recombination" in {name for name, _ in fixtures}
    for name, grid in fixtures:
        assert gen.self_check(copy.deepcopy(grid)), name
