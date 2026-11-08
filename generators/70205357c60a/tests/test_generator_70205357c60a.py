from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators import base
from reviewer_support import canonical_path, find_root


gen = importlib.import_module("puzzle_generators.per_puzzle.70205357c60a.generator")
ROOT = Path(find_root(__file__))


def _canonical_row() -> dict:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical row missing")


def _canonical_pairs() -> list[tuple[list[list[int]], list[list[int]]]]:
    row = _canonical_row()
    return [
        (pair["input"], pair["output"])
        for split in ("train", "test")
        for pair in row[split]
    ]


def test_rule_hash_and_all_canonical_pairs_are_exact_and_pure() -> None:
    row = _canonical_row()
    normalized = " ".join(row["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == gen.RULE_HASH

    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for source, expected in pairs:
        untouched = copy.deepcopy(source)
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert gen.rule_mirror(source) == expected
        assert source == untouched


def test_ordinary_draws_record_exact_observable_axes() -> None:
    for band in ("easy", "medium", "hard"):
        for sample_index in range(18):
            captured: list[object] = []
            base.set_ctx_observer(captured.append)
            try:
                grid = gen.generate(1000 + sample_index, sample_index, difficulty=band)
            finally:
                base.set_ctx_observer(None)
            assert len(captured) == 1
            recorded = captured[0].recorded_draws()
            observed = gen.observe_overrides(grid)
            assert {name: recorded[name] for name in gen.AXES} == observed
            assert gen.self_check(grid) == []


def test_boundary_overrides_are_exact_and_unknowns_reject() -> None:
    cases = [
        {"grid_h": 9},
        {"grid_h": 18},
        {"grid_w": 9},
        {"grid_w": 20},
        {"n_components": 2},
        {"n_components": 4},
        {"scene_profile": "solid_rectangles"},
        {"scene_profile": "single_notches"},
        {"scene_profile": "deep_notches"},
        {
            "grid_h": 9,
            "grid_w": 9,
            "n_components": 4,
            "scene_profile": "deep_notches",
        },
        {
            "grid_h": 18,
            "grid_w": 20,
            "n_components": 2,
            "scene_profile": "single_notches",
        },
    ]
    for band in ("easy", "medium", "hard"):
        for index, overrides in enumerate(cases):
            grid = gen.generate(5000 + index, 19, difficulty=band, **overrides)
            assert gen.self_check(grid, meta={"overrides": overrides}) == []
            observed = gen.observe_overrides(grid)
            for name, value in overrides.items():
                assert observed[name] == value

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, obsolete_axis="legacy")
    with pytest.raises(ValueError, match="grid_h"):
        gen.generate(0, 0, grid_h=8)
    with pytest.raises(ValueError, match="scene_profile"):
        gen.generate(0, 0, scene_profile="mixed")


def test_replay_is_fresh_deterministic_and_global_rng_neutral() -> None:
    random.seed(70205357)
    state = random.getstate()
    first = gen.generate(81, 7, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(81, 7, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert second[0][0] != 9


def test_self_check_rejects_degenerate_and_recombined_impostors() -> None:
    impostors = {
        "all_background": [[0] * 9 for _ in range(9)],
        "full_grid": [[5] * 9 for _ in range(9)],
        "singleton": [[5]],
        "short_line": [[0] * 9 for _ in range(9)],
        "single_2x2": [[0] * 9 for _ in range(9)],
        "two_2x2_recombined": [[0] * 9 for _ in range(9)],
    }
    for col in range(2, 6):
        impostors["short_line"][2][col] = 5
    for row in range(2, 4):
        for col in range(2, 4):
            impostors["single_2x2"][row][col] = 5
            impostors["two_2x2_recombined"][row][col] = 5
            impostors["two_2x2_recombined"][row + 4][col + 4] = 5

    for name, grid in impostors.items():
        errors = gen.self_check(grid)
        assert errors, name

    # The negative recombination remains executable under the local rule, but
    # distribution validation rejects it because no positive witness exists.
    recombined = impostors["two_2x2_recombined"]
    assert gen.rule_mirror(recombined) == recombined
    assert any("positive rule witness" in error or "identity lesson" in error for error in gen.self_check(recombined))


def test_deep_notches_preserve_bbox_interior_cells_and_kill_shortcuts() -> None:
    for band in ("easy", "medium", "hard"):
        grid = gen.generate(
            88_000,
            2,
            difficulty=band,
            grid_h=14,
            grid_w=16,
            n_components=3,
            scene_profile="deep_notches",
        )
        info = gen._analysis(grid)
        assert gen.self_check(grid) == []
        assert info["scene_profile"] == "deep_notches"
        assert info["protected_bbox_interior"]
        expected = gen.rule_mirror(grid)
        for row, col in info["protected_bbox_interior"]:
            assert grid[row][col] == 5
            assert expected[row][col] == 5
        assert gen._bbox_interior_rival(grid) != expected
        assert gen._solid_rectangle_only_rival(grid) != expected


def test_three_example_sliding_schedule_is_identifiable() -> None:
    assert gen.EXAMPLES_NEEDED == 3
    for band in ("easy", "medium", "hard"):
        for start in range(18):
            pairs = []
            for sample_index in range(start, start + 4):
                grid = gen.generate(91_000 + start, sample_index, difficulty=band)
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            profiles = {
                gen.observe_overrides(pair["input"])["scene_profile"]
                for pair in pairs[:3]
            }
            assert profiles == set(gen.SCENE_PROFILES)
            assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []
