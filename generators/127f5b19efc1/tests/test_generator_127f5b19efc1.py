from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "127f5b19efc1"
gen = importlib.import_module(
    "puzzle_generators.per_puzzle.127f5b19efc1.generator"
)


def _canonical_pairs() -> list[dict]:
    pairs: list[dict] = []
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            for split in ("train", "test"):
                values = row.get(split, [])
                if isinstance(values, dict):
                    values = [values]
                pairs.extend(values)
    assert len(pairs) == 5
    return pairs


def _axis_values(name: str) -> list[object]:
    spec = gen.AXES[name]
    if spec["type"] == "int":
        lo, hi = map(int, spec["valid"].split(".."))
        return [lo, hi]
    return spec["valid"].split("|")


def test_rule_hash_and_all_canonical_pairs_are_pinned() -> None:
    assert gen.RULE_HASH == "692baf483e4b"
    for pair in _canonical_pairs():
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_generation_is_deterministic_fresh_rng_pure_and_structural() -> None:
    for band in ("easy", "medium", "hard"):
        for sample_index in range(24):
            state = random.getstate()
            first = gen.generate(9127, sample_index, difficulty=band)
            assert random.getstate() == state
            second = gen.generate(9127, sample_index, difficulty=band)
            assert random.getstate() == state
            assert first == second
            assert first is not second
            assert all(left is not right for left, right in zip(first, second))
            assert gen.self_check(first, difficulty=band) == []
            first[0][0] = 9 if first[0][0] != 9 else 0
            assert gen.generate(9127, sample_index, difficulty=band) == second


def test_every_declared_axis_is_exactly_observable_at_boundaries() -> None:
    for name in gen.AXES:
        for index, value in enumerate(_axis_values(name)):
            grid = gen.generate(
                44 + index,
                17 + index,
                difficulty="hard",
                **{name: value},
            )
            assert gen.observe_overrides(grid)[name] == value
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, misspelled_axis=1)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_sliding_four_demo_lesson_is_identifiable(band: str) -> None:
    for start in range(20):
        demos = []
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
            grid = gen.generate(10_000 + start, sample_index, difficulty=band)
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
        query_grid = gen.generate(
            10_000 + start,
            start + gen.EXAMPLES_NEEDED,
            difficulty=band,
        )
        query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []


def test_self_check_rejects_targeted_impostors() -> None:
    valid = gen.generate(207, 3, difficulty="medium", distractor_count=1)
    _coerced, facts, errors = gen._analysis(valid)
    assert errors == []

    full_one_color = copy.deepcopy(valid)
    for row in range(len(full_one_color) - 1):
        for col, value in enumerate(full_one_color[row]):
            if value:
                full_one_color[row][col] = 8
    assert any("two or three colors" in reason for reason in gen.self_check(full_one_color))

    missing_key = copy.deepcopy(valid)
    key_col = facts["key_positions"][0]
    missing_key[-1][key_col] = 0
    assert any("exactly four" in reason for reason in gen.self_check(missing_key))

    dirty_separator = copy.deepcopy(valid)
    dirty_separator[-2][0] = 7
    assert any("row above" in reason for reason in gen.self_check(dirty_separator))

    merged_distractor = copy.deepcopy(valid)
    distractor = facts["distractors"][0][0]
    for dr, dc in gen._DELTAS:
        row, col = distractor[0] + dr, distractor[1] + dc
        if 0 <= row < len(merged_distractor) - 2 and 0 <= col < len(merged_distractor[0]):
            if merged_distractor[row][col] == 0:
                merged_distractor[row][col] = 6
                break
    assert any("singleton" in reason for reason in gen.self_check(merged_distractor))

    bad_spacing = copy.deepcopy(valid)
    source = facts["key_positions"][1]
    target = source + 1 if source + 1 < len(bad_spacing[0]) else source - 1
    bad_spacing[-1][target] = bad_spacing[-1][source]
    bad_spacing[-1][source] = 0
    assert any("separated by one zero" in reason for reason in gen.self_check(bad_spacing))


def test_semantic_witnesses_cover_repeats_distractors_and_variable_cells() -> None:
    names = {
        "repeated_keys_repeat_panels",
        "largest_component_is_the_template",
        "panel_cell_size_follows_transformed_crops",
    }
    hits = {name: 0 for name in names}
    for sample_index in range(160):
        band = ("easy", "medium", "hard")[sample_index % 3]
        grid = gen.generate(80_000 + sample_index, sample_index, difficulty=band)
        truth = gen.rule_mirror(grid)
        for name in names:
            if not gen.SEMANTIC_WITNESSES[name](grid):
                continue
            hits[name] += 1
            for rival_name in gen.WITNESS_RIVALS[name]:
                assert gen.SEMANTIC_RIVALS[rival_name](grid) != truth
    assert all(count > 0 for count in hits.values()), hits
