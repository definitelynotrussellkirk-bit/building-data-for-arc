from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path

import pytest


gen = importlib.import_module("puzzle_generators.per_puzzle.563e1df172df.generator")
ROOT = Path(__file__).resolve().parents[3]


def _canonical_pairs():
    pairs = []
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != gen.TASK_ID:
                continue
            pairs.extend(row.get("train", []))
            pairs.extend(row.get("test", []))
    return pairs


def test_all_canonical_pairs_match_python_mirror():
    pairs = _canonical_pairs()
    assert len(pairs) == 8
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(original) == []
        assert gen.rule_mirror(original) == pair["output"]
        assert original == pair["input"]


def test_every_declared_profile_is_exactly_observable():
    for index, profile in enumerate(gen.SCENE_PROFILES):
        grid = gen.generate(100 + index, index, difficulty="medium", scene_profile=profile)
        assert gen.self_check(grid, meta={"overrides": {"scene_profile": profile}}) == []
        assert gen.observe_overrides(grid) == {"scene_profile": profile}
        assert gen.strict_canonical_like(grid) == []


def test_unknown_overrides_and_bad_profiles_are_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis="northwest")
    with pytest.raises(ValueError, match="unknown scene_profile"):
        gen.generate(1, 0, scene_profile="not-a-profile")


@pytest.mark.parametrize(
    "mutator, message",
    [
        (lambda g: g[0].append(0), "rectangular"),
        (lambda g: g.__setitem__(0, [8] + g[0][1:]), "unexpected input colors"),
        (lambda g: g.__setitem__(1, g[1][:-1]), "rectangular"),
    ],
)
def test_structural_mutations_are_rejected(mutator, message):
    grid = gen.generate(11, 4, difficulty="medium")
    mutator(grid)
    assert any(message in error for error in gen.self_check(grid))


def test_same_row_and_same_column_are_rejected():
    row_grid = [[0] * 6 for _ in range(6)]
    row_grid[2][1] = 2
    row_grid[2][4] = 3
    assert any("different rows" in error for error in gen.self_check(row_grid))

    col_grid = [[0] * 6 for _ in range(6)]
    col_grid[1][3] = 2
    col_grid[4][3] = 3
    assert any("different columns" in error for error in gen.self_check(col_grid))


def test_four_scheduled_demos_falsify_named_rivals():
    demos = []
    for index in range(4):
        grid = gen.generate(23, index, difficulty="easy")
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(23, 4, difficulty="easy")
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
    assert gen.lesson_identifiable(demos, query) == []
    for rival in gen.LESSON_COMPETITORS.values():
        assert any(rival(pair["input"]) != pair["output"] for pair in demos)
