from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest

from puzzle_generators.runner import _apply_rule, _load_bundle, _open_bridge_with_rule
from src.core.canonical_pairs import load_task_pairs

TASK_ID = "5faf9d5e3e6d"
ROOT = Path(__file__).resolve().parents[1]
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.5faf9d5e3e6d.generator"
)
AUTHORITY = ROOT / (
    "data/base/solutions/banks/ad4abc25f505/"
    "medium_65_transform_object_by_key__5faf9d5e3e6d.json"
)


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _crop_without_key(grid):
    body = copy.deepcopy(grid)
    body[0][0] = 0
    points = [
        (row, col)
        for row, values in enumerate(body)
        for col, value in enumerate(values)
        if value != 0
    ]
    top = min(row for row, _ in points)
    left = min(col for _, col in points)
    bottom = max(row for row, _ in points)
    right = max(col for _, col in points)
    return [row[left : right + 1] for row in body[top : bottom + 1]]


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _expected(grid):
    key = grid[0][0]
    body = _crop_without_key(grid)
    if key == 1:
        return body
    if key == 2:
        return _rotate_cw(body)
    if key == 3:
        return [row[::-1] for row in body[::-1]]
    if key == 4:
        return [row[::-1] for row in body]
    raise AssertionError(key)


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_metadata_and_normalized_rule_hash_are_pinned():
    assert GEN.GENERATOR_ID == TASK_ID
    assert GEN.TASK_ID == TASK_ID
    assert GEN.VERSION == "2.0.0"
    assert GEN.RULE_HASH == "abd7c563a610"
    record = json.loads(AUTHORITY.read_text())
    assert _normalized_hash(record["racket_target"]["target_code"]) == GEN.RULE_HASH
    canonical = next(
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )
    assert _normalized_hash(canonical["program_solution"]) == GEN.RULE_HASH


def test_all_canonical_pairs_are_accepted_exact_and_unambiguous():
    pairs = load_task_pairs(TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert _expected(pair["input"]) == pair["output"]
        body = _crop_without_key(pair["input"])
        answers = (
            body,
            _rotate_cw(body),
            [row[::-1] for row in body[::-1]],
            [row[::-1] for row in body],
        )
        assert len({_frozen(answer) for answer in answers}) == 4


def test_racket_exactness_input_purity_and_a_b_a_repeat():
    pairs = load_task_pairs(TASK_ID)
    bundle = _load_bundle(TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        for pair in pairs:
            source = copy.deepcopy(pair["input"])
            before = copy.deepcopy(source)
            assert _apply_rule(bridge, fn_name, source) == pair["output"]
            assert source == before

        grid_a = GEN.generate(901, 0, difficulty="easy")
        grid_b = GEN.generate(902, 4, difficulty="hard")
        out_a1 = _apply_rule(bridge, fn_name, grid_a)
        out_b = _apply_rule(bridge, fn_name, grid_b)
        out_a2 = _apply_rule(bridge, fn_name, grid_a)
        assert out_a1 == _expected(grid_a)
        assert out_b == _expected(grid_b)
        assert out_a2 == out_a1
    finally:
        bridge.shutdown()


def test_every_lesson_teaches_all_four_keys_and_varies_the_query():
    query_keys = Counter()
    query_color_counts = Counter()
    for seed in range(80):
        observations = [
            GEN.observe_overrides(GEN.generate(seed, index, difficulty="medium"))
            for index in range(5)
        ]
        assert {row["key_code"] for row in observations[:4]} == {1, 2, 3, 4}
        assert Counter(row["body_color_count"] for row in observations[:4]) == {
            1: 2,
            2: 2,
        }
        assert {row["position_zone"] for row in observations[:4]} == set(
            GEN.POSITION_ZONES
        )
        query_keys[observations[4]["key_code"]] += 1
        query_color_counts[observations[4]["body_color_count"]] += 1
    assert set(query_keys) == {1, 2, 3, 4}
    assert set(query_color_counts) == {1, 2}


@pytest.mark.parametrize(
    "overrides",
    [
        {
            "grid_h": 7,
            "grid_w": 8,
            "key_code": 4,
            "body_h": 2,
            "body_w": 3,
            "body_color_count": 1,
            "position_zone": "lower_right",
        },
        {
            "grid_h": 14,
            "grid_w": 14,
            "key_code": 1,
            "body_h": 5,
            "body_w": 5,
            "body_color_count": 2,
            "position_zone": "upper_left",
        },
    ],
)
def test_full_valid_boundary_overrides_are_exact(overrides):
    grid = GEN.generate(1201, 73, difficulty="hard", **overrides)
    assert GEN.observe_overrides(grid) == overrides
    assert GEN.self_check(grid) == []


def test_incompatible_and_unknown_overrides_fail_loudly():
    with pytest.raises(ValueError, match="cannot expose four distinct transforms"):
        GEN.generate(
            1,
            1,
            body_h=2,
            body_w=2,
            body_color_count=1,
        )
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 1, texture="warm")
    with pytest.raises(ValueError):
        GEN.generate(1, 1, key_code=5)


def test_determinism_fresh_returns_and_process_global_rng_isolation():
    state = random.getstate()
    first = GEN.generate(444, 19, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(444, 19, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 0
    assert GEN.generate(444, 19, difficulty="medium") == second


def test_self_check_rejects_targeted_semantic_impostors():
    no_key = GEN.generate(10, 0)
    no_key[0][0] = 0
    assert any("transform key" in error for error in GEN.self_check(no_key))

    no_body = [[0 for _ in range(8)] for _ in range(7)]
    no_body[0][0] = 2
    assert any("no body" in error for error in GEN.self_check(no_body))

    duplicate_key = GEN.generate(11, 1, body_color_count=1)
    bbox = GEN._body_bbox(duplicate_key)
    duplicate_key[bbox[0]][bbox[1]] = duplicate_key[0][0]
    assert any("key color" in error for error in GEN.self_check(duplicate_key))

    symmetric = [[0 for _ in range(8)] for _ in range(7)]
    symmetric[0][0] = 2
    for row in (2, 3):
        for col in (3, 4):
            symmetric[row][col] = 6
    assert any("fewer than four" in error for error in GEN.self_check(symmetric))

    disconnected = [[0 for _ in range(8)] for _ in range(7)]
    disconnected[0][0] = 1
    disconnected[2][2] = 6
    disconnected[2][3] = 6
    disconnected[4][5] = 6
    assert any("8-connected" in error for error in GEN.self_check(disconnected))

    third_color = GEN.generate(12, 2, body_color_count=2)
    bbox = GEN._body_bbox(third_color)
    present = {value for row in third_color for value in row}
    replacement = next(color for color in range(1, 10) if color not in present)
    changed = False
    for row in range(bbox[0], bbox[2] + 1):
        for col in range(bbox[1], bbox[3] + 1):
            if third_color[row][col] != 0:
                third_color[row][col] = replacement
                changed = True
                break
        if changed:
            break
    assert any("one or two colors" in error for error in GEN.self_check(third_color))


def test_negative_recombination_is_distribution_invalid_but_oracle_executable():
    grid = None
    for seed in range(200):
        candidate = GEN.generate(seed, 0, body_color_count=2)
        counts = Counter(
            value
            for row, values in enumerate(candidate)
            for col, value in enumerate(values)
            if value != 0 and (row, col) != (0, 0)
        )
        if max(counts.values()) >= 2:
            grid = candidate
            break
    assert grid is not None

    present_before = {value for row in grid for value in row}
    replacement = next(color for color in range(1, 10) if color not in present_before)
    assert replacement not in present_before
    counts = Counter(
        value
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0 and (row, col) != (0, 0)
    )
    repeated = next(color for color, count in counts.items() if count >= 2)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == repeated:
                grid[row][col] = replacement
                break
        else:
            continue
        break

    assert sum(value == replacement for row in grid for value in row) == 1
    assert any("one or two colors" in error for error in GEN.self_check(grid))

    bundle = _load_bundle(TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        output = _apply_rule(bridge, fn_name, grid)
    finally:
        bridge.shutdown()
    assert output == _expected(grid)
