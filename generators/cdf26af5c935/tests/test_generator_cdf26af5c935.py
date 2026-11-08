from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.base import set_ctx_observer
from puzzle_generators.per_puzzle.cdf26af5c935 import generator as gen


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "cdf26af5c935"
BANDS = ("easy", "medium", "hard")


def _canonical_row() -> dict:
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise KeyError(TASK_ID)


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *test]


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _pair(grid):
    return {"input": grid, "output": gen._filled_output(grid)}


def test_rule_hash_and_canonical_pairs_are_grounded():
    row = _canonical_row()
    digest = hashlib.sha256(row["program_solution"].encode()).hexdigest()[:12]
    assert gen.RULE_HASH == digest == "f0bf24a90ea6"

    base = json.loads(
        (
            ROOT
            / "data/base/solutions/banks/bc9ea2a8b0ce/medium_i10__cdf26af5c935.json"
        ).read_text()
    )
    assert base["racket_target"]["target_code"] == row["program_solution"]

    assert len(_canonical_pairs()) == 4
    for pair in _canonical_pairs():
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen._filled_output(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_consecutive_schedule_is_identifiable_and_palette_independent():
    for seed in range(24):
        demos = [_pair(gen.generate(seed, index, difficulty="medium")) for index in range(3)]
        query = _pair(gen.generate(seed, 3, difficulty="medium"))
        assert gen.lesson_identifiable(demos, query) == []
        facts = [gen.semantic_observables(pair["input"]) for pair in demos]
        assert [fact["n_rects"] for fact in facts] == [1, 2, 1]
        assert {fact["palette_kind"] for fact in facts} == {"low", "mid", "high"}
        assert any(fact["has_wide"] for fact in facts)
        assert any(fact["has_tall"] for fact in facts)
        assert any(fact["per_color_not_global_bbox"] for fact in facts)


def test_every_declared_override_is_exact_and_observable():
    cases = (
        {"grid_h": 6, "grid_w": 7, "n_rects": 1, "palette_kind": "low"},
        {"grid_h": 14, "grid_w": 14, "n_rects": 3, "palette_kind": "high"},
        {"grid_h": 8, "grid_w": 13, "n_rects": 2, "palette_kind": "mid"},
        {"grid_h": 6, "grid_w": 14, "n_rects": 3, "palette_kind": "low"},
    )
    for band in BANDS:
        for index, overrides in enumerate(cases):
            grid = gen.generate(9100 + index, 100 + index, difficulty=band, **overrides)
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == overrides


def test_default_keyed_provenance_matches_every_axis():
    for band_index, band in enumerate(BANDS):
        for index in range(20):
            captured = []
            set_ctx_observer(captured.append)
            try:
                grid = gen.generate(
                    20_000 + band_index * 100 + index,
                    300 + index,
                    difficulty=band,
                )
            finally:
                set_ctx_observer(None)
            assert len(captured) == 1
            observed = gen.observe_overrides(grid)
            assert set(observed) == set(gen.AXES)
            for axis, value in observed.items():
                assert captured[0].axis_value(axis) == value


def test_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(7281)
    state = random.getstate()
    first = gen.generate(444, 19, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(444, 19, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert gen.generate(444, 19, difficulty="hard") == second


def test_self_check_rejects_targeted_impostors_and_recombination():
    impostors = {
        "identity_2x2": [[1, 1, 0], [1, 1, 0], [0, 0, 0]],
        "three_corners": [[1, 0, 1], [0, 0, 0], [1, 0, 0]],
        "fifth_same_color": [[1, 0, 1], [0, 1, 0], [1, 0, 1]],
        "background_not_modal": [[1, 0, 1], [1, 0, 1]],
        "solid_output": [[1, 0, 0, 1], [0, 0, 0, 0], [1, 0, 0, 1]],
        "overlapping_bodies": [
            [1, 0, 0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 2, 0, 0, 0, 0, 2],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [1, 0, 0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 2, 0, 0, 0, 0, 2],
        ],
    }
    for name, grid in impostors.items():
        assert gen.self_check(grid), name

    recombined = gen.generate(731, 1, difficulty="hard", n_rects=2)
    absent = next(color for color in range(1, 10) if all(color not in row for row in recombined))
    changed = False
    for row in range(len(recombined)):
        for col in range(len(recombined[0])):
            if recombined[row][col] != 0:
                recombined[row][col] = absent
                changed = True
                break
        if changed:
            break
    assert gen.self_check(recombined)


def test_semantic_witnesses_fire_in_each_large_disjoint_census():
    for cohort in range(2):
        for band_index, band in enumerate(BANDS):
            unique = set()
            witness_counts = {name: 0 for name in gen.SEMANTIC_WITNESSES}
            for index in range(200):
                seed = 100_000 * (cohort + 1) + 10_000 * band_index + index
                grid = gen.generate(seed, 1000 + index, difficulty=band)
                assert gen.self_check(grid) == []
                assert gen.strict_canonical_like(grid) == []
                assert gen._filled_output(grid) != grid
                unique.add(_frozen(grid))
                for name, witness in gen.SEMANTIC_WITNESSES.items():
                    witness_counts[name] += bool(witness(grid))
            assert len(unique) >= 190
            assert all(count > 0 for count in witness_counts.values())


def test_invalid_controls_fail_loudly():
    bad_calls = (
        {"difficulty": "expert"},
        {"unknown": 1},
        {"grid_h": 5},
        {"grid_h": 15},
        {"grid_w": 6},
        {"grid_w": 15},
        {"n_rects": 0},
        {"n_rects": 4},
        {"palette_kind": "warm"},
        {"grid_h": "8"},
        {"n_rects": True},
    )
    for kwargs in bad_calls:
        with pytest.raises((TypeError, ValueError)):
            gen.generate(1, 1, **kwargs)
