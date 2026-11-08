"""Focused semantic and override regressions for d2f386d0e071."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest


TASK_ID = "d2f386d0e071"
GENERATOR_HOME = Path(__file__).resolve().parents[1]
REPO = GENERATOR_HOME.parents[1]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"review_{TASK_ID}_generator", GENERATOR_HOME / "generator.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _canonical_row() -> dict:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise KeyError(TASK_ID)


def _pairs() -> list[dict]:
    row = _canonical_row()
    return row["train"] + row["test"]


def test_rule_hash_and_every_canonical_pair_are_pinned() -> None:
    assert GEN.RULE_HASH == "f48a460c6519"
    assert len(_pairs()) == 5
    for pair in _pairs():
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_declared_axes_are_exact_observable_and_cartesian_safe() -> None:
    assert set(GEN.AXES) == {
        "grid_h",
        "grid_w",
        "n_cells",
        "n_distinct_colors",
    }
    case_index = 0
    for difficulty in ("easy", "medium", "hard"):
        for grid_h in (5, 12):
            for grid_w in (7, 14):
                for n_cells in (4, 9):
                    for n_colors in (2, 4):
                        requested = {
                            "grid_h": grid_h,
                            "grid_w": grid_w,
                            "n_cells": n_cells,
                            "n_distinct_colors": n_colors,
                        }
                        grid = GEN.generate(
                            10_000 + case_index,
                            case_index,
                            difficulty=difficulty,
                            **requested,
                        )
                        assert GEN.self_check(grid) == []
                        assert GEN.observe_overrides(grid) == requested
                        assert GEN.rule_mirror(grid) != grid
                        case_index += 1

    with pytest.raises((TypeError, ValueError), match="unknown override"):
        GEN.generate(1, 2, typo_axis=3)


def test_default_schedule_covers_all_profiles_in_every_lesson_window() -> None:
    assert GEN.EXAMPLES_NEEDED == 4
    profiles = set(GEN.SCHEDULE_PROFILES)
    for difficulty in ("easy", "medium", "hard"):
        for start in range(12):
            observed = {
                GEN.schedule_profile(99, index, difficulty)
                for index in range(start, start + GEN.EXAMPLES_NEEDED)
            }
            assert observed == profiles


def test_default_draws_are_lawful_deterministic_and_semantically_strong() -> None:
    random.seed(20260928)
    process_state = random.getstate()
    pooled_witnesses = {name: 0 for name in GEN.SEMANTIC_WITNESSES}

    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(24):
            first = GEN.generate(7301, sample_index, difficulty=difficulty)
            second = GEN.generate(7301, sample_index, difficulty=difficulty)
            assert first == second
            assert first is not second
            assert all(a is not b for a, b in zip(first, second))
            assert GEN.self_check(first) == []
            assert GEN.strict_canonical_like(first) == []
            observed = GEN.observe_overrides(first)
            assert observed["grid_h"] == len(first)
            assert observed["grid_w"] == len(first[0])
            assert observed["n_cells"] in range(4, 10)
            assert observed["n_distinct_colors"] in range(2, 5)
            assert GEN.rule_mirror(first) != first
            for name, witness in GEN.SEMANTIC_WITNESSES.items():
                pooled_witnesses[name] += int(bool(witness(first)))

    assert random.getstate() == process_state
    assert all(hits > 0 for hits in pooled_witnesses.values()), pooled_witnesses


def test_each_firing_witness_really_refutes_its_claimed_rival() -> None:
    grids = [GEN.generate(42, index, difficulty="medium") for index in range(16)]
    for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
        firing = [g for g in grids if GEN.SEMANTIC_WITNESSES[witness_name](g)]
        assert firing, witness_name
        for grid in firing:
            expected = GEN.rule_mirror(grid)
            assert any(
                GEN.SEMANTIC_RIVALS[rival_name](grid) != expected
                for rival_name in rival_names
            ), (witness_name, rival_names)


def test_every_sliding_lesson_window_refutes_declared_competitors() -> None:
    for difficulty in ("easy", "medium", "hard"):
        pairs = []
        for sample_index in range(12):
            grid = GEN.generate(3109, sample_index, difficulty=difficulty)
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        for start in range(7):
            demos = pairs[start : start + GEN.EXAMPLES_NEEDED]
            query = pairs[start + GEN.EXAMPLES_NEEDED]
            assert GEN.lesson_identifiable(demos, query) == []
            for name, competitor in GEN.LESSON_COMPETITORS.items():
                assert any(
                    competitor(demo["input"]) != demo["output"]
                    for demo in demos
                ), name



def test_one_color_minimal_impostors_are_outside_the_teaching_grammar() -> None:
    short_line = [[0] * 9 for _ in range(7)]
    for col in range(4):
        short_line[3][col] = 2
    assert GEN.self_check(short_line)

    solid_2x2 = [[0] * 9 for _ in range(7)]
    for row in range(2):
        for col in range(2):
            solid_2x2[row][col] = 2
    assert GEN.self_check(solid_2x2)

    with pytest.raises(ValueError):
        GEN.generate(17, 0, n_distinct_colors=1)

def test_structural_impostors_are_rejected() -> None:
    one_mark = [[0] * 9 for _ in range(7)]
    one_mark[1][1] = 4
    assert GEN.self_check(one_mark)

    right_side_source = GEN.generate(5, 6, difficulty="easy")
    width = len(right_side_source[0])
    right_side_source[0][width - 1] = 7
    assert GEN.self_check(right_side_source)

    occupied_target = GEN.generate(8, 9, difficulty="easy")
    source = next(
        (r, c)
        for r, row in enumerate(occupied_target)
        for c, value in enumerate(row)
        if value and c != len(row) - 1 - c
    )
    r, c = source
    occupied_target[r][len(occupied_target[0]) - 1 - c] = 9
    assert GEN.self_check(occupied_target)
