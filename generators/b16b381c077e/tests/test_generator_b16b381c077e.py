from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest


TASK_ID = "b16b381c077e"
MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.b16b381c077e.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical task row missing")


def _put_panel(grid, panel_index, panel):
    n = len(grid)
    left = panel_index * (n + 1)
    for row in range(n):
        for col in range(n):
            grid[row][left + col] = panel[row][col]


def _inverse_kind(kind):
    return {
        "rot90": "rot270",
        "rot180": "rot180",
        "rot270": "rot90",
        "flip_h": "flip_h",
        "flip_v": "flip_v",
        "transpose": "transpose",
        "anti_transpose": "anti_transpose",
    }[kind]


def test_rule_hash_pins_whitespace_normalized_canonical_rule():
    rule = _canonical_row()["program_solution"]
    expected = hashlib.sha256(" ".join(rule.split()).encode()).hexdigest()[:12]
    assert MODULE.RULE_HASH == expected == "c828867c1661"


def test_all_canonical_inputs_are_accepted():
    row = _canonical_row()
    pairs = list(row["train"]) + [row["test"]]
    assert len(pairs) == 3
    for pair in pairs:
        assert MODULE.self_check(pair["input"]) == []


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    for band in ("easy", "medium", "hard"):
        for seed in range(20):
            random.seed(99173 + seed)
            before = random.getstate()
            first = MODULE.generate(seed, seed * 11 + 3, difficulty=band)
            assert random.getstate() == before
            second = MODULE.generate(seed, seed * 11 + 3, difficulty=band)
            assert first == second
            assert first is not second
            assert all(left is not right for left, right in zip(first, second))
            first[0][0] = (first[0][0] + 1) % 10
            assert first != second


def test_exact_axis_boundaries_are_observable_in_every_band():
    for band in ("easy", "medium", "hard"):
        for panel in (3, 6):
            for kind in MODULE._TRANSFORM_KINDS:
                for divider_color in (1, 9):
                    grid = MODULE.generate(
                        712,
                        19,
                        difficulty=band,
                        panel=panel,
                        kind=kind,
                        divider_color=divider_color,
                    )
                    assert MODULE.self_check(grid) == []
                    assert MODULE.observe_overrides(grid) == {
                        "panel": panel,
                        "kind": kind,
                        "divider_color": divider_color,
                    }
    with pytest.raises(ValueError, match="unknown|override|kind"):
        MODULE.generate(1, 1, difficulty="easy", kind="id")
    with pytest.raises(ValueError, match="unsupported override"):
        MODULE.generate(1, 1, difficulty="easy", texture="empty_panel3")


def test_every_seven_consecutive_samples_cover_all_nonidentity_transforms():
    expected = set(MODULE._TRANSFORM_KINDS)
    for band in ("easy", "medium", "hard"):
        for seed in range(30):
            for start in (0, 7, 91):
                kinds = {
                    MODULE.observe_overrides(
                        MODULE.generate(seed, start + index, difficulty=band)
                    )["kind"]
                    for index in range(7)
                }
                assert kinds == expected


def test_ordinary_draws_have_unique_visible_nonembedded_answers():
    for band in ("easy", "medium", "hard"):
        seen_sizes = set()
        seen_kinds = set()
        seen_palette_sizes = set()
        for sample_index in range(100):
            grid = MODULE.generate(8000 + sample_index, sample_index, difficulty=band)
            assert MODULE.self_check(grid) == []
            analysis = MODULE._analyze(grid)
            facts = analysis["facts"]
            assert facts is not None
            assert facts["matching_kinds"] == [facts["kind"]]
            assert facts["kind"] in MODULE._TRANSFORM_KINDS
            assert facts["answer"] != facts["panel_c"]
            assert facts["answer"] not in (facts["panel_a"], facts["panel_b"])
            assert facts["divider_color"] not in {
                value
                for panel in (facts["panel_a"], facts["panel_b"], facts["panel_c"])
                for row in panel
                for value in row
            }
            seen_palette_sizes.add(len({value for row in grid for value in row}))
            seen_sizes.add(facts["panel"])
            seen_kinds.add(facts["kind"])
        assert len(seen_sizes) >= 2
        assert seen_palette_sizes == {3, 4}
        assert seen_kinds == set(MODULE._TRANSFORM_KINDS)


def test_self_check_rejects_targeted_impostors():
    base = MODULE.generate(4242, 17, difficulty="medium")
    n = len(base)
    facts = MODULE._analyze(base)["facts"]
    assert facts is not None

    zero_dividers = copy.deepcopy(base)
    for row in range(n):
        zero_dividers[row][n] = 0
        zero_dividers[row][2 * n + 1] = 0
    assert any("non-background" in msg for msg in MODULE.self_check(zero_dividers))

    broken_relation = copy.deepcopy(base)
    used = {value for row in base for value in row}
    new_color = next(color for color in range(1, 10) if color not in used)
    replacement = [[0] * n for _ in range(n)]
    replacement[0][0] = new_color
    replacement[0][1] = new_color
    replacement[1][0] = new_color
    _put_panel(broken_relation, 1, replacement)
    assert new_color not in {
        value
        for panel in (facts["panel_a"], facts["panel_c"])
        for row in panel
        for value in row
    }
    assert any("transform must be unique" in msg for msg in MODULE.self_check(broken_relation))

    ambiguous_relation = copy.deepcopy(base)
    symmetric = [[0] * n for _ in range(n)]
    symmetric[n // 2][n // 2] = facts["panel_a"][0][0] or 1
    _put_panel(ambiguous_relation, 0, symmetric)
    _put_panel(ambiguous_relation, 1, symmetric)
    assert any("transform must be unique" in msg for msg in MODULE.self_check(ambiguous_relation))

    identity_relation = copy.deepcopy(base)
    _put_panel(identity_relation, 1, facts["panel_a"])
    assert any("identity" in msg for msg in MODULE.self_check(identity_relation))

    empty_query = copy.deepcopy(base)
    _put_panel(empty_query, 2, [[0] * n for _ in range(n)])
    assert any("nonempty" in msg for msg in MODULE.self_check(empty_query))

    embedded_answer = copy.deepcopy(base)
    inverse = _inverse_kind(facts["kind"])
    query = MODULE._apply(facts["panel_a"], inverse)
    _put_panel(embedded_answer, 2, query)
    assert any("already embedded" in msg for msg in MODULE.self_check(embedded_answer))
