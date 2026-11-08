"""Focused regression tests for the b7d9205dd62d rectangle-fill generator."""
from __future__ import annotations

import copy
import hashlib
import json
import random

import pytest

from puzzle_generators import base as generator_base
from puzzle_generators.per_puzzle.b7d9205dd62d import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


def _episode(seed: int, start: int, band: str):
    demos = []
    for offset in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(seed, start + offset, difficulty=band)
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(seed, start + gen.EXAMPLES_NEEDED, difficulty=band)
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
    return demos, query


def _canonical_rule_hash() -> str:
    with open("data/canonical/puzzles.jsonl", encoding="utf-8") as handle:
        row = next(
            json.loads(line)
            for line in handle
            if json.loads(line).get("task_id") == gen.TASK_ID
        )
    return hashlib.sha256(" ".join(row["program_solution"].split()).encode()).hexdigest()[:12]


def test_rule_hash_and_all_canonical_pairs():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 4
    assert gen.RULE_HASH == _canonical_rule_hash() == "913178465622"
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source)
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert gen.rule_mirror(source) == pair["output"]
        assert source == before


def test_every_profile_is_exact_observable_and_overrideable_in_every_band():
    for band in ("easy", "medium", "hard"):
        for index, profile in enumerate(gen.SCENE_PROFILES):
            grid = gen.generate(
                10_000 + index,
                20_000 + index,
                difficulty=band,
                scene_profile=profile,
            )
            assert gen.self_check(grid) == []
            assert gen.teaching_check(grid) == []
            assert gen.observe_overrides(grid) == {"scene_profile": profile}
    with pytest.raises(ValueError):
        gen.generate(1, 1, scene_profile="unknown")
    with pytest.raises(ValueError):
        gen.generate(1, 1, typo_profile="canonical_10x11_pair2")
    with pytest.raises(ValueError):
        gen.generate(1, 1, difficulty="extreme")


def test_default_keyed_profile_matches_returned_grid():
    captured = []
    generator_base.set_ctx_observer(captured.append)
    try:
        for band_index, band in enumerate(("easy", "medium", "hard")):
            for index in range(24):
                grid = gen.generate(
                    30_000 + band_index * 100 + index,
                    index * 17 + 3,
                    difficulty=band,
                )
                ctx = captured[-1]
                assert ctx.recorded_draws()["scene_profile"] == gen.observe_overrides(grid)["scene_profile"]
                assert ctx.overrides_used() == {}
    finally:
        generator_base.set_ctx_observer(None)


def test_determinism_fresh_returns_and_global_rng_state():
    random.seed(9205)
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


def test_self_check_rejects_targeted_structural_impostors():
    valid = gen.generate(
        44,
        1,
        difficulty="medium",
        scene_profile="triple_collinear_11x11",
    )
    assert gen.self_check(valid) == []
    analysis = gen._analysis(valid)
    color, box = analysis["boxes"][0]
    cells = analysis["positions"][color]
    (row_a, col_a), (row_b, col_b) = cells

    missing_endpoint = copy.deepcopy(valid)
    missing_endpoint[row_b][col_b] = 0

    third_endpoint = copy.deepcopy(valid)
    empty = next(
        (r, c)
        for r, row in enumerate(third_endpoint)
        for c, value in enumerate(row)
        if value == 0 and not (box[0] <= r <= box[2] and box[1] <= c <= box[3])
    )
    third_endpoint[empty[0]][empty[1]] = color

    no_diagonal_targets = [[0] * 8 for _ in range(8)]
    no_diagonal_targets[1][1] = no_diagonal_targets[1][5] = 2
    no_diagonal_targets[4][2] = no_diagonal_targets[7][2] = 4

    overlapping = [[0] * 9 for _ in range(9)]
    overlapping[1][1] = overlapping[6][6] = 2
    overlapping[2][5] = overlapping[7][2] = 4

    distractor_inside_target = copy.deepcopy(valid)
    dcolor, (first, second) = analysis["collinear"][0]
    distractor_inside_target[first[0]][first[1]] = 0
    distractor_inside_target[second[0]][second[1]] = 0
    distractor_inside_target[box[0]][box[1] + 1] = dcolor
    distractor_inside_target[box[0]][box[1] + 3] = dcolor

    for impostor in (
        missing_endpoint,
        third_endpoint,
        no_diagonal_targets,
        overlapping,
        distractor_inside_target,
    ):
        assert gen.self_check(impostor)


def test_authority_and_teaching_checks_have_separate_scopes():
    valid = gen.generate(71, 0, scene_profile="canonical_10x11_pair2")
    off_profile = [row + [0, 0] for row in valid] + [[0] * (len(valid[0]) + 2) for _ in range(2)]
    assert gen.self_check(off_profile) == []
    assert gen.teaching_check(off_profile)


def test_every_sliding_lesson_refutes_named_competitors():
    for band in ("easy", "medium", "hard"):
        for start in range(16):
            demos, query = _episode(91_000 + start, start, band)
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(demo["input"]) != demo["output"] for demo in demos), (
                    band,
                    start,
                    name,
                )


def test_semantic_witnesses_cover_each_band_schedule():
    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(400 + index, index, difficulty=band) for index in range(16)]
        for name, witness in gen.SEMANTIC_WITNESSES.items():
            assert any(witness(grid) for grid in grids), (band, name)
