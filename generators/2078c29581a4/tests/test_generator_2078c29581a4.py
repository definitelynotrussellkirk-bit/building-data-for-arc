from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.2078c29581a4.generator")


ROOT = Path(__file__).resolve().parents[1]


def _canonical_pairs():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == gen.TASK_ID:
            return [*row["train"], *row["test"]]
    raise AssertionError("canonical task missing")


def test_rule_hash_and_canonical_pairs():
    assert gen.RULE_HASH == "ed6dfa957511"
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(copy.deepcopy(pair["input"])) == []
        assert gen.strict_canonical_like(copy.deepcopy(pair["input"])) == []
        assert gen.rule_mirror(copy.deepcopy(pair["input"])) == pair["output"]


def test_every_four_sample_window_refutes_declared_shortcuts():
    for start in range(12):
        demos = []
        profiles = []
        for offset in range(gen.EXAMPLES_NEEDED):
            sample_index = start + offset
            grid = gen.generate(1000 + start, sample_index, difficulty="medium")
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            profiles.append(gen.schedule_profile(1000 + start, sample_index, "medium"))
        query_grid = gen.generate(2000 + start, start + gen.EXAMPLES_NEEDED, difficulty="medium")
        assert set(profiles) == set(gen.SCHEDULE_PROFILES)
        assert gen.lesson_identifiable(
            demos, {"input": query_grid, "output": gen.rule_mirror(query_grid)}
        ) == []
        for competitor in gen.LESSON_COMPETITORS.values():
            assert any(competitor(pair["input"]) != pair["output"] for pair in demos)


def test_exact_override_boundaries_and_unknown_key():
    cases = (
        {"grid_h": 5, "grid_w": 4, "n_nonempty_rows": 2},
        {"grid_h": 16, "grid_w": 16, "n_nonempty_rows": 4},
        {"grid_h": 5, "grid_w": 16, "n_nonempty_rows": 4},
        {"grid_h": 16, "grid_w": 4, "n_nonempty_rows": 2},
    )
    for index, overrides in enumerate(cases):
        grid = gen.generate(3000 + index, index, difficulty="easy", **overrides)
        assert gen.self_check(grid, meta={"overrides": overrides}) == []
        assert gen.observe_overrides(grid) == overrides
    with pytest.raises(TypeError, match="unknown override axis"):
        gen.generate(1, 0, __override_contract_unknown_axis__=1)


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(987654)
    before = random.getstate()
    left = gen.generate(42, 7, difficulty="hard")
    middle = random.getstate()
    right = gen.generate(42, 7, difficulty="hard")
    after = random.getstate()
    assert left == right
    assert left is not right
    assert all(a is not b for a, b in zip(left, right))
    assert before == middle == after
    left[0][0] = 9 if left[0][0] != 9 else 8
    assert left != right


def test_self_check_rejects_targeted_impostors():
    valid = gen.generate(55, 1, difficulty="medium")
    impostors = {}

    no_empty = copy.deepcopy(valid)
    for row in no_empty:
        if all(value == 0 for value in row):
            row[0] = 1
    impostors["no_empty_rows"] = no_empty

    one_row = [[0] * len(valid[0]) for _ in valid]
    one_row[1][0:2] = [2, 3]
    impostors["only_one_nonempty"] = one_row

    solid_single_color = [[0] * len(valid[0]) for _ in valid]
    solid_single_color[1][1:3] = [4, 4]
    solid_single_color[2][1:3] = [4, 4]
    impostors["solid_2x2_single_color"] = solid_single_color

    duplicate_rows = copy.deepcopy(valid)
    nonempty = [i for i, row in enumerate(duplicate_rows) if any(row)]
    duplicate_rows[nonempty[1]] = duplicate_rows[nonempty[0]][:]
    impostors["duplicate_nonempty_rows"] = duplicate_rows

    full_row = copy.deepcopy(valid)
    first = next(i for i, row in enumerate(full_row) if any(row))
    full_row[first] = [2] * len(full_row[first])
    impostors["full_foreground_row"] = full_row

    assert len(impostors) >= 4
    for name, grid in impostors.items():
        assert gen.self_check(grid), name


def test_negative_recombination_rejected_but_rule_mirror_requires_lawful_input():
    valid = gen.generate(77, 2, difficulty="hard")
    used = {value for row in valid for value in row if value != 0}
    malformed = gen.negative_recombination_fixture(valid)
    inserted = {
        malformed[r][0]
        for r, row in enumerate(valid)
        if all(value == 0 for value in row)
    }
    assert inserted and inserted.isdisjoint(used)
    assert gen.self_check(malformed)
    with pytest.raises(ValueError, match="invalid lesson"):
        gen.rule_mirror(malformed)
