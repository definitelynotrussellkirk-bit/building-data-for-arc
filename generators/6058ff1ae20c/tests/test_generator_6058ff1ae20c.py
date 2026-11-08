from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
from pathlib import Path

import pytest


TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATOR_PATH = TASK_ROOT / "generator.py"
CANONICAL_PATH = REPO_ROOT / "shared/data/canonical/puzzles.jsonl"


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_6058ff1ae20c_under_test", GENERATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _canonical_row() -> dict:
    for line in CANONICAL_PATH.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == gen.TASK_ID:
            return row
    raise AssertionError("canonical row missing")


def _canonical_pairs() -> list[tuple[list[list[int]], list[list[int]]]]:
    row = _canonical_row()
    raw_test = row["test"]
    tests = [raw_test] if isinstance(raw_test, dict) else list(raw_test)
    records = list(row["train"]) + tests
    return [(copy.deepcopy(item["input"]), copy.deepcopy(item["output"])) for item in records]


def _marks(grid):
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]


def test_rule_hash_and_canonical_authority_are_pinned():
    source = _canonical_row()["program_solution"]
    digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert digest == gen.RULE_HASH == "95d2eeca4e5d"


def test_all_canonical_pairs_are_accepted_and_mirrored_exactly():
    assert len(_canonical_pairs()) == 4
    for source, expected in _canonical_pairs():
        before = copy.deepcopy(source)
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert gen.rule_mirror(source) == expected
        assert source == before


def test_row_major_fold_order_matches_racket_for_distinct_seeds():
    source = [[0] * 5 for _ in range(5)]
    source[1][3] = 2
    source[3][1] = 7
    expected = [
        [0, 7, 0, 2, 0],
        [2, 7, 2, 2, 2],
        [0, 7, 0, 2, 0],
        [7, 7, 7, 7, 7],
        [0, 7, 0, 2, 0],
    ]
    assert gen.self_check(source) == []
    assert gen.rule_mirror(source) == expected


def test_schedule_covers_all_profiles_in_every_three_demo_window():
    assert gen.EXAMPLES_NEEDED == 3
    assert tuple(gen.SCHEDULE_PROFILES) == tuple(gen.SCENE_PROFILES)
    expected = set(gen.SCENE_PROFILES)
    for band in (None, "easy", "medium", "hard"):
        for start in range(12):
            observed = {
                gen.schedule_profile(111, start + offset, band)
                for offset in range(gen.EXAMPLES_NEEDED)
            }
            assert observed == expected


def test_default_profiles_are_truthful_and_observable():
    expected_shapes = {
        "single": (1, 1),
        "same_color_pair": (2, 1),
        "ordered_distinct_pair": (2, 2),
    }
    for band in ("easy", "medium", "hard"):
        for sample_index, profile in enumerate(gen.SCENE_PROFILES):
            grid = gen.generate(700, sample_index, difficulty=band)
            marks = _marks(grid)
            assert (len(marks), len({value for _, _, value in marks})) == expected_shapes[profile]
            assert len({row for row, _, _ in marks}) == len(marks)
            assert len({col for _, col, _ in marks}) == len(marks)
            assert gen.observe_overrides(grid) == {
                "grid_h": len(grid),
                "grid_w": len(grid[0]),
                "scene_profile": profile,
            }
            assert gen.self_check(grid) == []


def test_every_exact_override_round_trips_at_boundaries_in_every_band():
    dimensions = ((5, 5), (8, 9), (12, 12))
    for band in ("easy", "medium", "hard"):
        for profile in gen.SCENE_PROFILES:
            for sample_index, (height, width) in enumerate(dimensions):
                expected = {
                    "grid_h": height,
                    "grid_w": width,
                    "scene_profile": profile,
                }
                grid = gen.generate(
                    900 + sample_index,
                    sample_index,
                    difficulty=band,
                    **expected,
                )
                assert gen.observe_overrides(grid) == expected
                assert gen.self_check(grid) == []


def test_single_profile_supplies_exact_canonical_shape_support_in_every_band():
    canonical_profiles = {
        (len(source), len(source[0]), len({value for row in source for value in row}))
        for source, _ in _canonical_pairs()
    }
    for band in ("easy", "medium", "hard"):
        for sample_index in (0, 3, 6, 9):
            grid = gen.generate(1234 + sample_index, sample_index, difficulty=band)
            profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
            assert profile in canonical_profiles


def test_declared_canonical_shortcuts_fit_canonical_and_generated_curriculum_refutes_them():
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(source) == expected for source, expected in _canonical_pairs()), name

    same_pair = gen.generate(77, 1, scene_profile="same_color_pair")
    distinct_pair = gen.generate(78, 2, scene_profile="ordered_distinct_pair")
    assert gen.CANONICAL_SHORTCUTS["first_seed_only"](same_pair) != gen.rule_mirror(same_pair)
    assert gen.CANONICAL_SHORTCUTS["reverse_seed_order"](distinct_pair) != gen.rule_mirror(distinct_pair)
    assert gen.CANONICAL_SHORTCUTS["reuse_first_seed_color"](distinct_pair) != gen.rule_mirror(distinct_pair)


def test_every_three_demo_lesson_is_identifiable_against_named_competitors():
    for band in ("easy", "medium", "hard"):
        for start in range(9):
            episode = []
            for offset in range(4):
                source = gen.generate(5000 + start, start + offset, difficulty=band)
                episode.append({"input": source, "output": gen.rule_mirror(source)})
            demos, query = episode[: gen.EXAMPLES_NEEDED], episode[-1]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(item["input"]) != item["output"] for item in demos), name


def test_self_check_rejects_malformed_and_out_of_curriculum_inputs():
    fixtures = []
    fixtures.append([])
    fixtures.append([[0, 0], [0]])
    fixtures.append([[0] * 5 for _ in range(4)])

    boolean = [[0] * 5 for _ in range(5)]
    boolean[2][2] = True
    fixtures.append(boolean)

    shared_row = [[0] * 5 for _ in range(5)]
    shared_row[2][1] = 2
    shared_row[2][3] = 2
    fixtures.append(shared_row)

    shared_col = [[0] * 5 for _ in range(5)]
    shared_col[1][2] = 2
    shared_col[3][2] = 4
    fixtures.append(shared_col)

    three_seeds = [[0] * 5 for _ in range(5)]
    three_seeds[0][0] = 2
    three_seeds[2][2] = 3
    three_seeds[4][4] = 4
    fixtures.append(three_seeds)

    for fixture in fixtures:
        assert gen.self_check(fixture), fixture


def test_unknown_invalid_and_wrong_typed_overrides_fail_closed():
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        gen.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="expert")
    with pytest.raises(ValueError, match="grid_h"):
        gen.generate(1, 0, grid_h=4)
    with pytest.raises(ValueError, match="grid_w"):
        gen.generate(1, 0, grid_w=True)
    with pytest.raises(ValueError, match="scene_profile"):
        gen.generate(1, 0, scene_profile="unknown")


def test_generation_is_deterministic_fresh_and_global_rng_isolated():
    random.seed(314159)
    before = random.getstate()
    first = gen.generate(9876, 11, difficulty="hard")
    after = random.getstate()
    second = gen.generate(9876, 11, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert second != first
