from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.3f2ed19e5882.generator"
)
ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "3f2ed19e5882"


def _canonical_inputs():
    rows = []
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                rows.extend(pair["input"] for pair in record.get("train", []))
                rows.extend(pair["input"] for pair in record.get("test", []))
    return rows


def _runs(row):
    out = []
    start = 0
    while start < len(row):
        end = start + 1
        while end < len(row) and row[end] == row[start]:
            end += 1
        out.append((row[start], start, end))
        start = end
    return out


def _mirror(grid):
    source = {color: (start, end) for color, start, end in _runs(grid[0])}
    destination = _runs(grid[1])
    return [
        [
            value
            for color, _start, _end in destination
            for value in row[source[color][0] : source[color][1]]
        ]
        for row in grid[2:]
    ]


def test_canonical_inputs_are_owned_by_self_check():
    canonical = _canonical_inputs()
    assert len(canonical) == 3
    assert all(MODULE.self_check(grid) == [] for grid in canonical)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_generated_draws_are_visible_nonidentity_reorders(band):
    for seed in range(20):
        grid = MODULE.generate(seed, seed + 101, difficulty=band)
        assert MODULE.self_check(grid) == []
        observed = MODULE.observe_overrides(grid)
        assert observed["output_changes"] is True
        assert observed["distinct_body_blocks"] == observed["n_blocks"]
        assert observed["moved_positions"] >= 2
        assert _mirror(grid) != grid[2:]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"n_blocks": 2, "body_rows": 3, "block_w": 2},
        {"n_blocks": 6, "body_rows": 9, "block_w": 5},
        {"n_blocks": 2, "body_rows": 9, "block_w": 5},
        {"n_blocks": 6, "body_rows": 3, "block_w": 2},
    ],
)
def test_exact_override_boundaries_survive_every_band(band, overrides):
    grid = MODULE.generate(77, 13, difficulty=band, **overrides)
    observed = MODULE.observe_overrides(grid)
    for key, value in overrides.items():
        assert observed[key] == value


def test_self_check_rejects_targeted_semantic_impostors():
    base = MODULE.generate(
        991,
        17,
        difficulty="hard",
        n_blocks=4,
        body_rows=6,
        block_w=3,
    )
    block_w = 3

    missing_destination_color = copy.deepcopy(base)
    missing_destination_color[1][0:block_w] = [0] * block_w
    assert MODULE.self_check(missing_destination_color)

    identity_header = copy.deepcopy(base)
    identity_header[1] = identity_header[0][:]
    assert any("non-identity" in item for item in MODULE.self_check(identity_header))

    unequal_source_width = copy.deepcopy(base)
    unequal_source_width[0][block_w] = unequal_source_width[0][0]
    assert MODULE.self_check(unequal_source_width)

    duplicate_body_block = copy.deepcopy(base)
    for row in range(2, len(duplicate_body_block)):
        duplicate_body_block[row][block_w : 2 * block_w] = duplicate_body_block[row][0:block_w]
    assert any("pairwise distinct" in item for item in MODULE.self_check(duplicate_body_block))

    empty_body_block = copy.deepcopy(base)
    for row in range(2, len(empty_body_block)):
        empty_body_block[row][0:block_w] = [0] * block_w
    assert any("must contain nonzero" in item for item in MODULE.self_check(empty_body_block))


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(123456)
    state = random.getstate()
    first = MODULE.generate(55, 8, difficulty="medium")
    assert random.getstate() == state
    second = MODULE.generate(55, 8, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 0
    assert second[0][0] != 0
