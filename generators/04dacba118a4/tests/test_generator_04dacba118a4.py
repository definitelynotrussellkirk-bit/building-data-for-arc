from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.04dacba118a4.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def _canonical_pairs():
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != GEN.TASK_ID:
                continue
            yield from row["train"]
            yield from row["test"]


def _manual_grid(key, first_shape, second_shape):
    grid = [[0 for _ in range(12)] for _ in range(8)]
    grid[0][0] = key
    for r, c in first_shape:
        grid[2 + r][1 + c] = 4
    for r, c in second_shape:
        grid[4 + r][8 + c] = 7
    return grid


def test_canonical_pairs_are_owned_and_python_mirror_matches():
    pairs = list(_canonical_pairs())
    assert len(pairs) == 4
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.expected_output(source) == pair["output"]
        assert source == pair["input"]


def test_four_consecutive_samples_identify_the_lesson_from_any_offset():
    for start in range(12):
        pairs = []
        for sample_index in range(start, start + 5):
            source = GEN.generate(8001, sample_index, difficulty="medium")
            pairs.append({"input": source, "output": GEN.expected_output(source)})
        assert GEN.lesson_identifiable(pairs[:4], pairs[4]) == []
        for rival in GEN.LESSON_COMPETITORS.values():
            assert any(rival(pair["input"]) != pair["output"] for pair in pairs[:4])


def test_declared_axes_are_exact_observable_and_unknown_axes_fail():
    cases = (
        {"grid_h": 8, "grid_w": 10, "key": 1, "shape_pair": 0, "layout": "first_left"},
        {"grid_h": 13, "grid_w": 15, "key": 2, "shape_pair": 7, "layout": "first_right"},
    )
    for overrides in cases:
        source = GEN.generate(17, 3, difficulty="hard", **overrides)
        assert GEN.observe_overrides(source) == overrides
        assert GEN.self_check(source) == []
    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(17, 3, typo_axis=1)


def test_self_check_rejects_targeted_structural_impostors():
    valid = GEN.generate(41, 2)

    no_key = copy.deepcopy(valid)
    no_key[0][0] = 0
    assert any("expected key" in reason for reason in GEN.self_check(no_key))

    missing_object = copy.deepcopy(valid)
    _, _, second = GEN._scene(missing_object)
    for r, c in second.cells:
        missing_object[r][c] = 0
    assert any("exactly two objects" in reason for reason in GEN.self_check(missing_object))

    third_object = copy.deepcopy(valid)
    for r in range(len(third_object) - 1, 0, -1):
        for c in range(len(third_object[0]) - 1, -1, -1):
            if third_object[r][c] != 0:
                continue
            if all(
                not (0 <= r + dr < len(third_object) and 0 <= c + dc < len(third_object[0]))
                or third_object[r + dr][c + dc] == 0
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
            ):
                third_object[r][c] = 9
                break
        else:
            continue
        break
    assert any("exactly two objects" in reason for reason in GEN.self_check(third_object))

    identical = _manual_grid(1, {(0, 0), (1, 0), (1, 1)}, {(0, 0), (1, 0), (1, 1)})
    assert any("must differ" in reason for reason in GEN.self_check(identical))

    no_normalized_overlap = _manual_grid(2, {(0, 0)}, {(0, 1), (1, 0), (1, 1)})
    assert any("must overlap" in reason for reason in GEN.self_check(no_normalized_overlap))


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    state = random.getstate()
    first = GEN.generate(123, 9, difficulty="easy")
    second = GEN.generate(123, 9, difficulty="easy")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert GEN.generate(123, 9, difficulty="easy") == second
    assert random.getstate() == state


def test_every_semantic_witness_fires_in_each_band():
    for band in ("easy", "medium", "hard"):
        hits = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
        for sample_index in range(96):
            source = GEN.generate(5000 + sample_index, sample_index, difficulty=band)
            assert GEN.strict_canonical_like(source) == []
            for name, witness in GEN.SEMANTIC_WITNESSES.items():
                hits[name] += int(witness(source))
        assert all(count > 0 for count in hits.values()), (band, hits)
