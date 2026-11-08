from __future__ import annotations

import copy
import importlib
import json
import random
import pytest

from reviewer_support import find_root


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.c83b29b14c16.generator"
)
ROOT = find_root(__file__)


def _grid(value):
    if value and isinstance(value[0], str):
        return [[int(cell) for cell in row] for row in value]
    return copy.deepcopy(value)


def _canonical_pairs():
    path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != gen.TASK_ID:
                continue
            tests = row.get("test") or []
            tests = [tests] if isinstance(tests, dict) else tests
            pairs = list(row.get("train") or []) + list(tests)
            return [
                {"input": _grid(pair["input"]), "output": _grid(pair["output"])}
                for pair in pairs
            ]
    raise AssertionError("canonical task row missing")


def test_rule_hash_canonical_acceptance_and_python_mirror():
    assert gen.RULE_HASH == "d264380c5850"
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert gen.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {
            "grid_h": 7,
            "grid_w": 7,
            "n_pairs": 2,
            "n_singletons": 0,
            "n_diagonal_pairs": 0,
            "n_triples": 0,
            "n_short_pairs": 0,
        },
        {
            "grid_h": 10,
            "grid_w": 10,
            "n_pairs": 3,
            "n_singletons": 1,
            "n_diagonal_pairs": 1,
            "n_triples": 1,
            "n_short_pairs": 1,
        },
    ],
)
def test_all_boundary_overrides_are_exact_in_every_band(difficulty, overrides):
    grid = gen.generate(812, 37, difficulty=difficulty, **overrides)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == overrides
    assert grid == gen.generate(812, 37, difficulty=difficulty, **overrides)


def test_unknown_and_invalid_overrides_are_rejected():
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        gen.generate(1, 2, misspelled_axis=1)
    for key, value in (
        ("grid_h", 6),
        ("grid_w", 11),
        ("n_pairs", 1),
        ("n_pairs", 4),
        ("n_singletons", 2),
        ("n_diagonal_pairs", -1),
        ("n_triples", 2),
        ("n_short_pairs", 2),
    ):
        with pytest.raises(ValueError):
            gen.generate(1, 2, **{key: value})


def test_default_schedule_has_canonical_profiles_and_branch_controls():
    for difficulty in ("easy", "medium", "hard"):
        observations = [
            gen.observe_overrides(gen.generate(900, index, difficulty=difficulty))
            for index in range(20)
        ]
        assert any(
            row["n_singletons"] == row["n_diagonal_pairs"] == row["n_triples"] == 0
            for row in observations
        )
        assert any(row["n_diagonal_pairs"] == 1 for row in observations)
        assert any(row["n_triples"] == 1 for row in observations)
        assert all(row["n_short_pairs"] == 1 for row in observations)
        assert all(
            (row["grid_h"], row["grid_w"])
            in {(7, 7), (8, 8), (9, 9), (8, 9), (9, 10)}
            for row in observations
        )


def test_five_sample_lessons_refute_every_named_competitor():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(8):
            pairs = []
            for index in range(start, start + gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(1301 + start, index, difficulty=difficulty)
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            assert gen.lesson_identifiable(pairs[:-1], pairs[-1]) == []


def test_semantic_witnesses_are_real_counterexamples():
    grids = [gen.generate(42, index, difficulty="medium") for index in range(12)]
    for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
        assert any(witness(grid) for grid in grids), witness_name
    for rival_name, rival in gen.SEMANTIC_RIVALS.items():
        assert any(rival(grid) != gen.rule_mirror(grid) for grid in grids), rival_name


def test_self_check_rejects_rule_hiding_mutations():
    grid = gen.generate(
        77,
        3,
        grid_h=10,
        grid_w=10,
        n_pairs=3,
        n_singletons=1,
        n_diagonal_pairs=1,
        n_triples=1,
        n_short_pairs=1,
    )
    blank = [[0 for _ in row] for row in grid]
    assert gen.self_check(blank)

    malformed = copy.deepcopy(grid)
    malformed[0].append(0)
    assert gen.self_check(malformed)

    too_many = copy.deepcopy(grid)
    positions = {}
    for r, row in enumerate(too_many):
        for c, value in enumerate(row):
            if value:
                positions.setdefault(value, []).append((r, c))
    pair_color = next(color for color, cells in positions.items() if len(cells) == 2)
    free = next(
        (r, c)
        for r, row in enumerate(too_many)
        for c, value in enumerate(row)
        if value == 0
    )
    too_many[free[0]][free[1]] = pair_color
    assert gen.self_check(too_many)


def test_replay_is_fresh_deterministic_and_global_rng_pure():
    random.seed(123456)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))


def _pair_geometry(grid):
    positions = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                positions.setdefault(value, []).append((r, c))
    aligned_distances = []
    diagonal_offsets = []
    for cells in positions.values():
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = cells
        if r1 == r2 or c1 == c2:
            aligned_distances.append(abs(r1 - r2) + abs(c1 - c2))
        else:
            diagonal_offsets.append((abs(r1 - r2), abs(c1 - c2)))
    return aligned_distances, diagonal_offsets


def test_four_sample_cycle_exposes_odd_spans_and_skew_nonalignment():
    grids = [gen.generate(761980, index, difficulty="easy") for index in range(4)]
    distances = []
    offsets = []
    for grid in grids:
        sample_distances, sample_offsets = _pair_geometry(grid)
        distances.extend(sample_distances)
        offsets.extend(sample_offsets)
    assert any(distance % 2 == 1 for distance in distances), distances
    assert any(dr != dc for dr, dc in offsets), offsets


def test_oblique_bbox_shortcut_is_declared_and_refuted_in_the_teaching_cycle():
    name = "skip 45-degree pairs, box-fill other exact pairs"
    assert name in gen.LESSON_COMPETITORS
    rival = gen.LESSON_COMPETITORS[name]
    pairs = []
    for index in range(4):
        grid = gen.generate(761980, index, difficulty="easy")
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
    assert any(rival(pair["input"]) != pair["output"] for pair in pairs)
