from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest


TASK_ID = "4a5e76e7a1af"
GEN = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row {TASK_ID}")


def _mutations(grid):
    cases = {}

    top_separator = copy.deepcopy(grid)
    top_separator[0][3] = 9
    cases["prototype_separator"] = top_separator

    divider_row = copy.deepcopy(grid)
    divider_row[3][0] = 7
    cases["divider_row"] = divider_row

    mixed_prototype = copy.deepcopy(grid)
    for r in range(3):
        for c in range(3):
            if mixed_prototype[r][c] != 0:
                mixed_prototype[r][c] = 9 if mixed_prototype[r][c] != 9 else 8
                break
        else:
            continue
        break
    cases["mixed_prototype_color"] = mixed_prototype

    duplicate_code = copy.deepcopy(grid)
    duplicate_code[4][5] = duplicate_code[4][1]
    cases["duplicate_transform_code"] = duplicate_code

    duplicate_output_color = copy.deepcopy(grid)
    duplicate_output_color[4][6] = duplicate_output_color[4][2]
    cases["duplicate_output_color"] = duplicate_output_color

    single_index = copy.deepcopy(grid)
    for left in (0, 4, 8):
        single_index[4][left] = 1
    cases["single_prototype_index"] = single_index

    transform_equivalent = copy.deepcopy(grid)
    source_color = next(
        value for row in transform_equivalent[:3] for value in row[:3] if value
    )
    target_color = next(
        value for row in transform_equivalent[:3] for value in row[4:7] if value
    )
    for r in range(3):
        for c in range(3):
            transform_equivalent[r][4 + c] = (
                target_color if transform_equivalent[r][c] == source_color else 0
            )
    cases["transform_equivalent_prototypes"] = transform_equivalent
    return cases


def test_canonical_inputs_and_outputs_match_python_mirror():
    row = _canonical_row()
    pairs = row["train"] + row["test"]
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_exact_override_axes_are_observable_at_boundaries():
    cases = [
        {
            "n_proto": 3,
            "palette_kind": "canonical",
            "program_profile": "codes_123",
            "index_profile": "distinct",
        },
        {
            "n_proto": 5,
            "palette_kind": "one_overlap",
            "program_profile": "codes_234",
            "index_profile": "one_repeat",
        },
        {
            "n_proto": 4,
            "palette_kind": "disjoint",
            "program_profile": "codes_134",
            "index_profile": "distinct",
        },
    ]
    for seed, overrides in enumerate(cases, start=71):
        grid = GEN.generate(seed, 23, difficulty="hard", **overrides)
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == overrides


def test_unknown_override_rejects_loudly():
    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(1, 0, difficulty="easy", texture="dead_alias")


def test_self_check_rejects_targeted_structural_impostors():
    grid = GEN.generate(
        8128,
        3,
        difficulty="hard",
        n_proto=5,
        palette_kind="disjoint",
        program_profile="codes_234",
        index_profile="one_repeat",
    )
    mutations = _mutations(grid)
    assert len(mutations) >= 4
    for name, impostor in mutations.items():
        errors = GEN.self_check(impostor)
        assert errors, f"self_check accepted targeted impostor {name}"


def test_replay_freshness_and_global_rng_purity():
    random.seed(917_203)
    state_before = random.getstate()
    first = GEN.generate(44, 19, difficulty="medium")
    state_after = random.getstate()
    second = GEN.generate(44, 19, difficulty="medium")

    assert state_before == state_after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    old = second[0][0]
    first[0][0] = (old + 1) % 10
    assert second[0][0] == old


def test_sequential_lessons_rebut_competing_rules():
    for group in range(20):
        seed = 100_000 + group
        base = 5 * group
        episodes = []
        for offset in range(5):
            grid = GEN.generate(seed, base + offset, difficulty=("easy", "medium", "hard")[group % 3])
            episodes.append({"input": grid, "output": GEN.rule_mirror(grid)})
        assert GEN.lesson_identifiable(episodes[:4], episodes[4]) == []


def test_ordinary_generated_scenes_pass_stronger_teaching_gate():
    for band in ("easy", "medium", "hard"):
        for sample_index in range(30):
            grid = GEN.generate(991 + sample_index, sample_index, difficulty=band)
            assert GEN._teaching_errors(grid) == []
