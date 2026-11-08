"""Focused regression tests for the f7672a367745 rectangle-outline generator."""
from __future__ import annotations

import copy
import hashlib
import random

import pytest

from puzzle_generators import base as generator_base
from puzzle_generators.per_puzzle.f7672a367745 import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


def _episode(seed: int, start: int, band: str):
    demos = []
    for offset in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(seed, start + offset, difficulty=band)
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(seed, start + gen.EXAMPLES_NEEDED, difficulty=band)
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
    return demos, query


def test_rule_hash_and_all_canonical_pairs():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    # The normalized canonical text is pinned by the queue and defect lint.
    import json
    row = next(
        json.loads(line)
        for line in open("data/canonical/puzzles.jsonl", encoding="utf-8")
        if json.loads(line).get("task_id") == gen.TASK_ID
    )
    actual = hashlib.sha256(" ".join(row["program_solution"].split()).encode()).hexdigest()[:12]
    assert gen.RULE_HASH == actual == "f641b0a1fe42"
    for pair in pairs:
        assert gen.self_check(copy.deepcopy(pair["input"])) == []
        assert gen.strict_canonical_like(copy.deepcopy(pair["input"])) == []
        assert gen.rule_mirror(copy.deepcopy(pair["input"])) == pair["output"]


def test_every_profile_is_exact_observable_and_overrideable():
    for band in ("easy", "medium", "hard"):
        for index, profile in enumerate(gen.SCENE_PROFILES):
            grid = gen.generate(10_000 + index, 20_000 + index, difficulty=band, scene_profile=profile)
            assert gen.self_check(grid) == []
            assert gen.teaching_check(grid) == []
            assert gen.observe_overrides(grid) == {"scene_profile": profile}
    with pytest.raises(ValueError):
        gen.generate(1, 1, scene_profile="unknown")
    with pytest.raises(ValueError):
        gen.generate(1, 1, typo_profile="easy_single_10x10")


def test_default_keyed_profile_matches_returned_grid():
    captured = []
    generator_base.set_ctx_observer(captured.append)
    try:
        for band_index, band in enumerate(("easy", "medium", "hard")):
            for index in range(24):
                grid = gen.generate(30_000 + band_index * 100 + index, index * 17 + 3, difficulty=band)
                ctx = captured[-1]
                assert ctx.recorded_draws()["scene_profile"] == gen.observe_overrides(grid)["scene_profile"]
                assert ctx.overrides_used() == {}
    finally:
        generator_base.set_ctx_observer(None)


def test_determinism_fresh_returns_and_global_rng_state():
    random.seed(7672)
    state = random.getstate()
    first = gen.generate(17, 9, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(17, 9, difficulty="medium")
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0] = 9 if first[0][0] != 9 else 0
    assert first != second
    assert second != gen.generate(18, 9, difficulty="medium")
    assert second != gen.generate(17, 10, difficulty="medium")


def test_authority_check_and_teaching_check_have_separate_scopes():
    valid = gen.generate(44, 1, difficulty="medium", scene_profile="medium_pair_7x12")
    assert gen.self_check(valid) == []
    analysis = gen._analysis(valid)
    color, cells = next(iter(analysis["positions"].items()))
    (row_a, col_a), (row_b, col_b) = cells

    missing_corner = copy.deepcopy(valid)
    missing_corner[row_b][col_b] = 0

    third_corner = copy.deepcopy(valid)
    third_corner[0][0] = color

    collinear = copy.deepcopy(valid)
    collinear[row_b][col_b] = 0
    collinear[row_a][col_b] = color

    no_interior = copy.deepcopy(valid)
    no_interior[row_b][col_b] = 0
    target_row = row_a + 1 if row_a + 1 < len(valid) else row_a - 1
    target_col = col_a + 1 if col_a + 1 < len(valid[0]) else col_a - 1
    no_interior[target_row][target_col] = color

    overlap = [[0] * 8 for _ in range(8)]
    overlap[1][1] = overlap[6][5] = 2
    overlap[3][3] = overlap[7][7] = 4

    for impostor in (missing_corner, third_corner, collinear):
        assert gen.self_check(impostor)

    # Both are executable under the selected Racket rule, but are excluded
    # from generated lessons to avoid degenerate and overwrite-order shortcuts.
    for curriculum_boundary in (no_interior, overlap):
        assert gen.self_check(curriculum_boundary) == []
        assert gen.teaching_check(curriculum_boundary)
        gen.rule_mirror(curriculum_boundary)


def test_every_sliding_lesson_refutes_named_competitors():
    for band in ("easy", "medium", "hard"):
        for start in range(16):
            demos, query = _episode(91_000 + start, start, band)
            assert gen.lesson_identifiable(demos, query) == []
            for rival in gen.LESSON_COMPETITORS.values():
                assert any(rival(demo["input"]) != demo["output"] for demo in demos)


def test_semantic_witnesses_cover_each_band_schedule():
    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(400 + index, index, difficulty=band) for index in range(16)]
        for name, witness in gen.SEMANTIC_WITNESSES.items():
            assert any(witness(grid) for grid in grids), (band, name)
