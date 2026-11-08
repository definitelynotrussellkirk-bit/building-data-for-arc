"""Focused regression tests for generator 994f16f93144."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

REPO_ROOT = find_root(__file__)
gen = importlib.import_module(
    "puzzle_generators.per_puzzle.994f16f93144.generator"
)


def _canonical_row():
    with canonical_path(REPO_ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical row missing")


def _one_target_grid():
    return gen.generate(
        771,
        5,
        difficulty="medium",
        grid_h=10,
        grid_w=10,
        n_triples=1,
        n_distractors=0,
        diag_dir="main",
        border_target=False,
    )


def _four_cell_main_chain():
    grid = [[0] * 7 for _ in range(7)]
    for index in range(1, 5):
        grid[index][index] = 4
    return grid


def test_rule_hash_and_all_canonical_pairs():
    row = _canonical_row()
    actual = hashlib.sha256(
        " ".join(row["program_solution"].split()).encode()
    ).hexdigest()[:12]
    assert gen.RULE_HASH == actual
    for pair in list(row["train"]) + list(row["test"]):
        input_grid = copy.deepcopy(pair["input"])
        assert gen.self_check(input_grid) == []
        assert gen.strict_canonical_like(input_grid) == []
        assert gen.rule_mirror(input_grid) == pair["output"]
        assert input_grid == pair["input"]


def test_exact_override_boundaries_are_observable():
    single_cases = [
        {"grid_h": 7},
        {"grid_h": 12},
        {"grid_w": 7},
        {"grid_w": 12},
        {"n_triples": 1},
        {"n_triples": 5},
        {"n_distractors": 0},
        {"n_distractors": 4},
        {"diag_dir": "main"},
        {"diag_dir": "anti"},
        {"diag_dir": "mixed"},
        {"border_target": False},
        {"border_target": True},
    ]
    for index, case in enumerate(single_cases):
        grid = gen.generate(900 + index, 17, difficulty="hard", **case)
        assert gen.self_check(grid) == []
        observed = gen.observe_overrides(grid)
        for key, value in case.items():
            assert observed[key] == value

    full = {
        "grid_h": 12,
        "grid_w": 12,
        "n_triples": 5,
        "n_distractors": 4,
        "diag_dir": "mixed",
        "border_target": True,
    }
    grid = gen.generate(999, 21, difficulty="hard", **full)
    assert gen.observe_overrides(grid) == full


def test_incompatible_and_unknown_overrides_reject_loudly():
    with pytest.raises(ValueError, match="incompatible"):
        gen.generate(1, 1, n_triples=1, diag_dir="mixed")
    with pytest.raises(ValueError, match="cannot be placed"):
        gen.generate(
            1,
            1,
            grid_h=7,
            grid_w=7,
            n_triples=5,
            n_distractors=4,
            diag_dir="mixed",
            border_target=False,
        )
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 1, unknown_axis=2)


def test_determinism_fresh_returns_and_global_rng_state():
    random.seed(99416)
    before = random.getstate()
    first = gen.generate(17, 9, difficulty="medium")
    after = random.getstate()
    second = gen.generate(17, 9, difficulty="medium")
    assert before == after
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    first[0][0] = 9
    assert first != second
    assert second != gen.generate(18, 9, difficulty="medium")
    assert second != gen.generate(17, 10, difficulty="medium")


def test_sequential_schedule_contains_rule_identifying_evidence():
    grids = [gen.generate(555, index, difficulty="medium") for index in range(4)]
    facts = [gen._analyze_scene(grid) for grid in grids]
    assert all(not item["errors"] for item in facts)
    assert gen.strict_canonical_like(grids[0]) == []
    assert {target.direction for item in facts for target in item["targets"]} == {
        "main",
        "anti",
    }
    assert any(item["n_distractors"] > 0 for item in facts[1:])
    assert any(
        "mismatched_diagonal" in item["distractor_kinds"] for item in facts[1:]
    )
    assert any(item["shared_target_distractor_colors"] for item in facts[1:])
    assert all(gen.rule_mirror(grid) != grid for grid in grids)


def test_targeted_impostors_are_rejected():
    base = _one_target_grid()
    facts = gen._analyze_scene(base)
    assert facts["errors"] == []
    target = facts["targets"][0]
    r, c = target.center
    mutations = []

    missing_center = copy.deepcopy(base)
    missing_center[r][c] = 0
    mutations.append(missing_center)

    wrong_endpoint = copy.deepcopy(base)
    er, ec = target.cells[0]
    wrong_endpoint[er][ec] = next(
        color for color in range(1, 8) if color != target.color
    )
    mutations.append(wrong_endpoint)

    reserved_output_color = copy.deepcopy(base)
    reserved_output_color[r][c] = 8
    mutations.append(reserved_output_color)

    crossing_target = copy.deepcopy(base)
    crossing_target[r - 1][c + 1] = target.color
    crossing_target[r + 1][c - 1] = target.color
    mutations.append(crossing_target)

    attached_new_color = copy.deepcopy(base)
    used = {value for row in base for value in row}
    replacement = next(color for color in range(1, 10) if color not in used and color != 8)
    attachment = next(
        (rr, cc)
        for tr, tc in target.cells
        for dr, dc in gen._DIRS8
        for rr, cc in [(tr + dr, tc + dc)]
        if 0 <= rr < len(base)
        and 0 <= cc < len(base[0])
        and attached_new_color[rr][cc] == 0
        and (rr, cc) not in set(target.cells)
    )
    attached_new_color[attachment[0]][attachment[1]] = replacement
    mutations.append(attached_new_color)

    for mutation in mutations:
        assert gen.self_check(mutation), mutation


def test_negative_recombination_is_distribution_invalid_but_oracle_executes():
    grid = _one_target_grid()
    facts = gen._analyze_scene(grid)
    target = facts["targets"][0]
    used = {value for row in grid for value in row}
    replacement = next(color for color in range(1, 10) if color not in used and color != 8)
    recombined = copy.deepcopy(grid)
    tr, tc = target.cells[0]
    location = next(
        (rr, cc)
        for dr, dc in gen._DIRS8
        for rr, cc in [(tr + dr, tc + dc)]
        if 0 <= rr < len(grid)
        and 0 <= cc < len(grid[0])
        and recombined[rr][cc] == 0
        and (rr, cc) not in set(target.cells)
    )
    recombined[location[0]][location[1]] = replacement
    assert gen.self_check(recombined)
    output = gen.rule_mirror(recombined)
    assert len(output) == len(recombined)
    assert len(output[0]) == len(recombined[0])
    assert output[target.center[0]][target.center[1]] == 8


def test_sampled_outputs_are_valid_and_diverse():
    distinct_inputs = set()
    distinct_outputs = set()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for seed in range(30):
            grid = gen.generate(
                10000 + 100 * band_index + seed,
                seed * 11 + 5,
                difficulty=band,
            )
            assert gen.self_check(grid) == []
            output = gen.rule_mirror(grid)
            assert output != grid
            distinct_inputs.add(json.dumps(grid, separators=(",", ":")))
            distinct_outputs.add(json.dumps(output, separators=(",", ":")))
    assert len(distinct_inputs) >= 85
    assert len(distinct_outputs) >= 85

def test_four_cell_diagonal_chain_is_a_lawful_local_predicate_case():
    grid = _four_cell_main_chain()
    expected = copy.deepcopy(grid)
    expected[2][2] = 8
    expected[3][3] = 8
    assert gen.self_check(grid) == []
    assert gen.rule_mirror(grid) == expected


def test_isolated_exact_triple_rival_is_declared_and_refuted():
    grid = _four_cell_main_chain()
    rival_name = "isolated_exact_triples_only"
    witness_name = "overlapping_diagonal_targets"
    assert rival_name in gen.SEMANTIC_RIVALS
    assert rival_name in gen.CANONICAL_SHORTCUTS
    assert rival_name in gen.LESSON_COMPETITORS
    assert gen.WITNESS_RIVALS[witness_name] == [rival_name]
    assert gen.SEMANTIC_WITNESSES[witness_name](grid)
    assert gen.SEMANTIC_RIVALS[rival_name](grid) == grid
    assert gen.SEMANTIC_RIVALS[rival_name](grid) != gen.rule_mirror(grid)


@pytest.mark.parametrize("seed", [10, 13])
def test_single_axis_target_count_override_jointly_backtracks(seed):
    grid = gen.generate(
        seed,
        seed * 17 + 3,
        difficulty="medium",
        n_triples=3,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid)["n_triples"] == 3



def test_four_pair_lesson_size_schedule_survives_every_query_rotation():
    seed = 1_175_019_826
    grids = [
        gen.generate(seed, sample_index, difficulty="easy")
        for sample_index in range(6, 10)
    ]
    dimensions = [(len(grid), len(grid[0])) for grid in grids]
    for query_index in range(4):
        demo_dimensions = {
            dimensions[index] for index in range(4) if index != query_index
        }
        assert len(demo_dimensions) >= 2, dimensions
