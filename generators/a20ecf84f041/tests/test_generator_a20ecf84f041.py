from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root


ROOT = find_root(__file__)
TASK_ID = "a20ecf84f041"
MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
DATA_ROOT = canonical_path(ROOT).parents[1]
BASE_PATH = DATA_ROOT / "base/solutions/banks/05283c9df3d9/H91__a20ecf84f041.json"


def _canonical_row():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        return next(json.loads(line) for line in handle if TASK_ID in line)


def _normalized_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _split(grid):
    divider_row = next(
        row for row in range(len(grid)) if all(value == 9 for value in grid[row])
    )
    divider_cols = [
        col
        for col in range(len(grid[0]))
        if all(grid[row][col] == 9 for row in range(len(grid)))
    ]
    left, right = divider_cols

    def sub(top, col0, bottom, col1):
        return [row[col0 : col1 + 1] for row in grid[top : bottom + 1]]

    return divider_row, left, right, (
        sub(0, 0, divider_row - 1, left - 1),
        sub(0, left + 1, divider_row - 1, right - 1),
        sub(0, right + 1, divider_row - 1, len(grid[0]) - 1),
        sub(divider_row + 1, 0, len(grid) - 1, left - 1),
        sub(divider_row + 1, left + 1, len(grid) - 1, right - 1),
        sub(divider_row + 1, right + 1, len(grid) - 1, len(grid[0]) - 1),
    )


def _state_counts(left, right):
    counts = [0, 0, 0, 0]
    for row in range(len(left)):
        for col in range(len(left[0])):
            counts[int(left[row][col] != 0) + 2 * int(right[row][col] != 0)] += 1
    return counts


def test_rule_hash_and_task_local_authority_are_synchronized():
    row = _canonical_row()
    base = json.loads(BASE_PATH.read_text())
    assert MODULE.RULE_HASH == _normalized_hash(row["program_solution"])
    assert MODULE.RULE_HASH == "94bd99d7c7c5"
    assert _normalized_hash(base["racket_target"]["target_code"]) == MODULE.RULE_HASH
    assert base["racket_target"]["target_code"] == row["program_solution"]


def test_all_canonical_inputs_are_structurally_valid_and_mirror_outputs():
    row = _canonical_row()
    pairs = list(row["train"]) + [row["test"]]
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert MODULE.self_check(pair["input"]) == []
        assert MODULE.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_generated_lessons_cover_every_truth_state_and_separate_color_roles():
    seen_ops = set()
    seen_relations = set()
    seen_sizes = set()
    seen_operand_red = set()
    seen_palette_sizes = set()
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(80):
            grid = MODULE.generate(seed, seed + 100, difficulty=difficulty)
            assert MODULE.self_check(grid) == []
            observed = MODULE.observe_overrides(grid)
            seen_ops.add(observed["op"])
            seen_relations.add(observed["operand_color_relation"])
            seen_sizes.add(observed["panel_size"])
            _, _, _, (a, b, c, d, e, blank) = _split(grid)
            assert all(_state_counts(a, b))
            assert all(_state_counts(d, e))
            assert all(value == 0 for row in blank for value in row)
            operand_colors = {
                value
                for panel in (a, b, d, e)
                for row in panel
                for value in row
                if value != 0
            }
            assert 9 not in operand_colors
            seen_operand_red.add(2 in operand_colors)
            seen_palette_sizes.add(len({value for row in grid for value in row}))
            assert {value for row in c for value in row} <= {0, 2}
    assert seen_ops == {"union", "intersection", "xor"}
    assert seen_relations == {"same", "different"}
    assert seen_sizes == {3, 4, 5, 6}
    assert seen_operand_red == {False, True}
    assert seen_palette_sizes == {3, 4, 5}


@pytest.mark.parametrize("panel_size", [3, 6])
@pytest.mark.parametrize("op", ["union", "intersection", "xor"])
@pytest.mark.parametrize("relation", ["same", "different"])
def test_exact_override_boundaries(panel_size, op, relation):
    overrides = {
        "panel_size": panel_size,
        "op": op,
        "operand_color_relation": relation,
    }
    grid = MODULE.generate(991, 7, difficulty="easy", **overrides)
    assert MODULE.observe_overrides(grid) == overrides
    assert MODULE.self_check(grid, meta={"overrides": overrides}) == []


def test_invalid_overrides_and_difficulty_reject_loudly():
    with pytest.raises(ValueError):
        MODULE.generate(1, 1, panel_size=2)
    with pytest.raises(ValueError):
        MODULE.generate(1, 1, op="nand")
    with pytest.raises(ValueError):
        MODULE.generate(1, 1, unsupported_axis=True)
    with pytest.raises(ValueError):
        MODULE.generate(1, 1, difficulty="extreme")


def test_self_check_rejects_targeted_structural_impostors():
    grid = MODULE.generate(17001, 23, difficulty="medium")
    divider_row, left_divider, right_divider, panels = _split(grid)
    a, _, _, d, _, _ = panels

    impostors = {}
    bad = copy.deepcopy(grid)
    bad[divider_row + 1][right_divider + 1] = 2
    impostors["prefilled query"] = bad

    bad = copy.deepcopy(grid)
    demo_cell = next(
        (row, col)
        for row in range(len(a))
        for col in range(len(a[0]))
        if a[row][col] != 0
    )
    bad[demo_cell[0]][demo_cell[1]] = 8 if a[demo_cell[0]][demo_cell[1]] != 8 else 7
    impostors["mixed top operand palette"] = bad

    bad = copy.deepcopy(grid)
    for row in range(divider_row):
        for col in range(right_divider + 1, len(grid[0])):
            bad[row][col] = 0
    impostors["corrupt demonstration result"] = bad

    bad = copy.deepcopy(grid)
    for row in range(len(bad)):
        bad[row][1] = 9
    impostors["extra divider"] = bad

    bad = copy.deepcopy(grid)
    bad[divider_row][0] = 0
    impostors["broken divider"] = bad

    bad = copy.deepcopy(grid)
    query_cell = next(
        (row, col)
        for row in range(len(d))
        for col in range(len(d[0]))
        if d[row][col] != 0
    )
    rr, cc = divider_row + 1 + query_cell[0], query_cell[1]
    bad[rr][cc] = 8 if d[query_cell[0]][query_cell[1]] != 8 else 7
    impostors["mixed bottom operand palette"] = bad

    # Negative recombination: splice one query operand from a different
    # calibrated lesson.  Its nuisance color disagrees with the retained mate,
    # so this plausible-looking cross-scene hybrid must fail closed.
    base_query_color = next(value for row in d for value in row if value != 0)
    donor_query_right = None
    for donor_seed in range(17002, 17102):
        donor = MODULE.generate(
            donor_seed,
            24,
            difficulty="medium",
            panel_size=divider_row,
            operand_color_relation="different",
        )
        donor_panel = _split(donor)[3][4]
        donor_color = next(value for row in donor_panel for value in row if value != 0)
        if donor_color != base_query_color:
            donor_query_right = donor_panel
            break
    assert donor_query_right is not None
    recombined = copy.deepcopy(grid)
    for row in range(len(donor_query_right)):
        for col in range(len(donor_query_right[0])):
            recombined[divider_row + 1 + row][left_divider + 1 + col] = donor_query_right[row][col]
    impostors["negative cross-scene query recombination"] = recombined

    for name, impostor in impostors.items():
        assert MODULE.self_check(impostor), name


def test_replay_freshness_and_process_global_rng_discipline():
    random.seed(20260723)
    before = random.getstate()
    first = MODULE.generate(12345, 17, difficulty="hard", op="xor")
    after = random.getstate()
    second = MODULE.generate(12345, 17, difficulty="hard", op="xor")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == after
    first[0][0] = 9 if first[0][0] != 9 else 0
    assert second == MODULE.generate(12345, 17, difficulty="hard", op="xor")
