from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

gen = importlib.import_module(
    "puzzle_generators.per_puzzle.a5d29cc3ea12.generator"
)


def _canonical_record():
    for line in Path("data/canonical/puzzles.jsonl").open(encoding="utf-8"):
        row = json.loads(line)
        if row.get("task_id") == gen.TASK_ID:
            return row
    raise AssertionError("canonical record not found")


def _clear_component(grid, component):
    for row, col in component["cells"]:
        grid[row][col] = 0


def _stamp_at(grid, norm, row0, col0, color):
    for dr, dc in norm:
        grid[row0 + dr][col0 + dc] = color


def test_canonical_pairs_are_accepted_and_racket_rule_is_mirrored():
    record = _canonical_record()
    pairs = record["train"] + record["test"]
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_canonical_examples_leave_exact_orientation_shortcut_alive():
    record = _canonical_record()
    pairs = record["train"] + record["test"]
    assert all(
        gen.SEMANTIC_RIVALS["match_exact_orientation_only"](pair["input"])
        == pair["output"]
        for pair in pairs
    )
    rotated = gen.generate(2026, 1, difficulty="medium")
    assert gen.observe_overrides(rotated)["match_rotation"] != 0
    assert (
        gen.SEMANTIC_RIVALS["match_exact_orientation_only"](rotated)
        != gen.rule_mirror(rotated)
    )


def test_override_boundaries_are_exact_observable_and_all_valid():
    boundary_values = {
        "grid_h": (10, 12),
        "grid_w": (12, 15),
        "shape_id": (0, 3),
        "legend_rotation": (0, 3),
        "match_rotation": (0, 3),
        "target_slot": (0, 2),
        "noise_color": ("3", "9"),
        "noise_size": (1, 2),
    }
    for difficulty in ("easy", "medium", "hard"):
        for axis, values in boundary_values.items():
            for value in values:
                grid = gen.generate(
                    37,
                    5,
                    difficulty=difficulty,
                    **{axis: value},
                )
                assert gen.self_check(grid) == []
                observed = gen.observe_overrides(grid)
                realized = (
                    len(grid)
                    if axis == "grid_h"
                    else len(grid[0])
                    if axis == "grid_w"
                    else observed[axis]
                )
                assert realized == value


def test_unknown_override_rejected_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=3)


def test_every_sliding_three_demo_window_identifies_the_rule():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(len(gen.SCHEDULE_PROFILES)):
            pairs = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(4815, sample_index, difficulty=difficulty)
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []
            demo_facts = [gen.observe_overrides(pair["input"]) for pair in pairs[:3]]
            assert {fact["target_slot"] for fact in demo_facts} == {0, 1, 2}
            assert any(fact["match_rotation"] == 0 for fact in demo_facts)
            assert any(fact["match_rotation"] != 0 for fact in demo_facts)


def test_generated_scenes_carry_both_hard_negative_controls():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(18):
            grid = gen.generate(991, sample_index, difficulty=difficulty)
            analysis = gen._analyze(grid)
            assert gen.self_check(grid) == []
            assert len(analysis["reflection_only"]) == 1
            legend = analysis["legend"]
            match_set = set(analysis["matches"])
            same_bbox_nonmatches = [
                candidate
                for index, candidate in enumerate(analysis["reds"])
                if index not in match_set
                and candidate["size"] == legend["size"]
                and (candidate["height"], candidate["width"])
                == (legend["height"], legend["width"])
            ]
            assert same_bbox_nonmatches


def test_self_check_rejects_targeted_impostors():
    base = gen.generate(71, 1, difficulty="hard")

    missing_legend = copy.deepcopy(base)
    for row in missing_legend:
        for col, value in enumerate(row):
            if value == 1:
                row[col] = 0
    assert any("one blue legend" in error for error in gen.self_check(missing_legend))

    no_match = copy.deepcopy(base)
    match_component = gen._analyze(no_match)["reds"][gen._analyze(no_match)["matches"][0]]
    row, col = next(iter(match_component["cells"]))
    no_match[row][col] = 0
    assert any("rotation-equivalent" in error for error in gen.self_check(no_match))

    two_matches = copy.deepcopy(base)
    analysis = gen._analyze(two_matches)
    legend = analysis["legend"]
    second = next(
        candidate
        for index, candidate in enumerate(analysis["reds"])
        if index not in analysis["matches"]
    )
    row0, col0, _, _ = second["bbox"]
    _clear_component(two_matches, second)
    _stamp_at(two_matches, legend["norm"], row0, col0, 2)
    assert any("exactly one rotation-equivalent" in error for error in gen.self_check(two_matches))

    missing_auxiliary = copy.deepcopy(base)
    auxiliary = gen._analyze(missing_auxiliary)["auxiliaries"][0]
    _clear_component(missing_auxiliary, auxiliary)
    assert any("one auxiliary-color" in error for error in gen.self_check(missing_auxiliary))

    leaked_answer_color = copy.deepcopy(base)
    auxiliary = gen._analyze(leaked_answer_color)["auxiliaries"][0]
    for row, col in auxiliary["cells"]:
        leaked_answer_color[row][col] = 8
    assert any("color 8" in error for error in gen.self_check(leaked_answer_color))


def test_determinism_fresh_returns_and_process_rng_purity():
    random.seed(4081)
    before = random.getstate()
    first = gen.generate(73, 8, difficulty="hard")
    middle = random.getstate()
    second = gen.generate(73, 8, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == middle == after
    first[0][0] = 9
    assert gen.generate(73, 8, difficulty="hard") == second


def test_difficulty_bands_are_deterministic_but_not_dead_aliases():
    draws = {
        difficulty: gen.generate(17, 4, difficulty=difficulty)
        for difficulty in ("easy", "medium", "hard")
    }
    assert len({json.dumps(grid) for grid in draws.values()}) >= 2
    for difficulty, grid in draws.items():
        assert grid == gen.generate(17, 4, difficulty=difficulty)
        assert gen.self_check(grid) == []


def test_rule_hash_matches_whitespace_normalized_canonical_authority():
    source = _canonical_record()["program_solution"]
    actual = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert actual == gen.RULE_HASH
