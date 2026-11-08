from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.18a70820b25b.generator")


ROOT = Path(__file__).resolve().parents[1]


def _canonical_pairs():
    pairs = []
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != gen.TASK_ID:
                continue
            for split in ("train", "test"):
                value = row.get(split) or []
                for pair in value if isinstance(value, list) else [value]:
                    pairs.append((copy.deepcopy(pair["input"]), copy.deepcopy(pair["output"])))
    return pairs


def test_all_canonical_pairs_are_owned_and_exact():
    pairs = _canonical_pairs()
    assert len(pairs) == 8
    for grid, expected in pairs:
        before = copy.deepcopy(grid)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen.rule_mirror(grid) == expected
        assert grid == before


def test_deterministic_fresh_returns_global_rng_and_aba():
    random.seed(81431)
    state = random.getstate()
    a = gen.generate(17, 31, difficulty="medium")
    assert random.getstate() == state
    b = gen.generate(18, 32, difficulty="hard")
    a2 = gen.generate(17, 31, difficulty="medium")
    assert random.getstate() == state
    assert a == a2
    assert a is not a2
    assert all(left is not right for left, right in zip(a, a2))
    a_before = copy.deepcopy(a)
    answer_a = gen.rule_mirror(a)
    answer_b = gen.rule_mirror(b)
    assert gen.rule_mirror(a) == answer_a
    assert gen.rule_mirror(b) == answer_b
    assert a == a_before


@pytest.mark.parametrize(
    "requested",
    [
        {
            "grid_h": 10,
            "grid_w": 10,
            "n_beams": 1,
            "n_scatter_total": 4,
            "n_source_distractors": 0,
            "shape_id": 0,
            "palette_kind": "warm",
            "position_bias": "left",
        },
        {
            "grid_h": 24,
            "grid_w": 24,
            "n_beams": 4,
            "n_scatter_total": 24,
            "n_source_distractors": 8,
            "shape_id": 5,
            "palette_kind": "primary",
            "position_bias": "right",
        },
    ],
)
def test_exact_override_boundaries_are_observable(requested):
    for band in ("easy", "medium", "hard"):
        grid = gen.generate(901, 77, difficulty=band, **requested)
        assert gen.self_check(grid, meta={"overrides": requested}) == []
        assert gen.observe_overrides(grid) == requested


def test_unknown_override_rejects_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, bogus_axis=1)


def test_targeted_impostors_are_rejected():
    base = gen.generate(
        931,
        47,
        difficulty="hard",
        grid_h=20,
        grid_w=20,
        n_beams=2,
        n_scatter_total=12,
        n_source_distractors=2,
        shape_id=0,
        palette_kind="warm",
        position_bias="center",
    )
    facts = gen._analyze(base)
    assert facts["errors"] == []
    mutations = []

    no_marker_colour = copy.deepcopy(base)
    for r, row in enumerate(no_marker_colour):
        for c, value in enumerate(row):
            if value == facts["marker_color"]:
                no_marker_colour[r][c] = 0
    mutations.append(no_marker_colour)

    joined_marker_component = copy.deepcopy(base)
    mr, mc = next(
        (r, c)
        for r, c in facts["marker_cells"]
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
        if 0 <= r + dr < len(base)
        and 0 <= c + dc < len(base[0])
        and base[r + dr][c + dc] == 0
    )
    # Re-find one available neighbor for the chosen marker.
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        rr, cc = mr + dr, mc + dc
        if 0 <= rr < len(base) and 0 <= cc < len(base[0]) and base[rr][cc] == 0:
            joined_marker_component[rr][cc] = facts["marker_color"]
            break
    mutations.append(joined_marker_component)

    illegal_shape = copy.deepcopy(base)
    sr, sc = facts["source_cells"][0]
    illegal_shape[sr][sc] = 0
    mutations.append(illegal_shape)

    all_columns_selected = copy.deepcopy(base)
    for c in set(facts["source_cols"]) - set(facts["trigger_columns"]):
        for r in range(facts["bottoms"][c] + 1, len(base)):
            if all_columns_selected[r][c] == 0:
                all_columns_selected[r][c] = facts["marker_color"]
                break
    mutations.append(all_columns_selected)

    floor_only_triggers = copy.deepcopy(base)
    for r in range(len(base)):
        for c in facts["source_cols"]:
            if r > facts["bottoms"][c] and floor_only_triggers[r][c] == facts["marker_color"]:
                floor_only_triggers[r][c] = 0
    for c in facts["trigger_columns"]:
        floor_only_triggers[-1][c] = facts["marker_color"]
    mutations.append(floor_only_triggers)

    for mutation in mutations:
        assert gen.self_check(mutation), mutation


def test_named_rivals_are_refuted_and_lesson_is_identifiable():
    pairs = []
    for index in range(5):
        grid = gen.generate(4117, index, difficulty="medium")
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
    assert gen.lesson_identifiable(pairs[:4], pairs[4]) == []
    witness = pairs[1]["input"]
    answer = gen.rule_mirror(witness)
    for name, rival in gen.SEMANTIC_RIVALS.items():
        assert rival(witness) != answer, name


def test_absent_feature_recombination_is_distribution_invalid_but_oracle_executes():
    grid = gen.generate(733, 19, difficulty="medium", n_source_distractors=0)
    facts = gen._analyze(grid)
    recombined = copy.deepcopy(grid)
    mr, mc = facts["marker_cells"][0]
    target = next(
        (mr + dr, mc + dc)
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
        if 0 <= mr + dr < len(grid)
        and 0 <= mc + dc < len(grid[0])
        and recombined[mr + dr][mc + dc] == 0
    )
    recombined[target[0]][target[1]] = facts["marker_color"]
    assert gen.self_check(recombined)
    # The authoritative rule grammar still has a defined answer for this
    # off-distribution feature recombination; the teaching distribution rejects it.
    output = copy.deepcopy(recombined)
    # Match the rule directly without invoking the stricter Python mirror.
    for c in facts["source_cols"]:
        if any(recombined[r][c] == facts["marker_color"] for r in range(facts["bottoms"][c] + 1, len(grid))):
            for r in range(facts["bottoms"][c] + 1, len(grid)):
                output[r][c] = facts["marker_color"]
    assert output != recombined
