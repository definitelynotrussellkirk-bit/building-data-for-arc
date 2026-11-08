from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.b320eba4cfd5 import generator

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "b320eba4cfd5"
CANONICAL = ROOT / "data/canonical/puzzles.jsonl"
BASE = ROOT / "data/base/solutions/training/17829a00__b320eba4cfd5.json"


def _canonical_row():
    return next(
        json.loads(line)
        for line in CANONICAL.read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )


def _pairs(row):
    pairs = []
    for split in ("train", "test"):
        value = row[split]
        pairs.extend([value] if isinstance(value, dict) else value)
    return pairs


def test_rule_hash_and_selected_authority_are_exactly_synchronized():
    source = _canonical_row()["program_solution"]
    expected = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    base = json.loads(BASE.read_text())
    assert generator.RULE_HASH == expected == "85019913700d"
    assert base["racket_target"]["target_code"] == source


def test_every_canonical_pair_is_accepted_and_matches_python_mirror():
    for pair in _pairs(_canonical_row()):
        source = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source)
        assert generator.self_check(source) == []
        assert generator.rule_mirror(source) == pair["output"]
        assert source == before


def test_three_sample_schedule_identifies_the_conjunctive_special_branch():
    demos = []
    observed = []
    for sample_index in range(3):
        grid = generator.generate(91, sample_index, difficulty="medium")
        observed.append(generator.observe_overrides(grid))
        demos.append({"input": grid, "output": generator.rule_mirror(grid)})
    query_grid = generator.generate(92, 6, difficulty="hard", edge_mode="tall_special")
    assert [item["edge_mode"] for item in observed] == [
        "tall_special", "short_control", "none"
    ]
    assert {item["shape_style"] for item in observed} == {"rectangles", "mixed"}
    assert generator.lesson_identifiable(demos, {"input": query_grid}) == []


@pytest.mark.parametrize("edge_mode", ["tall_special", "short_control", "none"])
@pytest.mark.parametrize("shape_style", ["rectangles", "mixed"])
def test_every_exact_axis_is_observable_at_boundary_values(edge_mode, shape_style):
    requested = {
        "grid_h": 14,
        "grid_w": 14,
        "n_top_objs": 4,
        "n_bot_objs": 5,
        "edge_mode": edge_mode,
        "shape_style": shape_style,
    }
    grid = generator.generate(401, 17, difficulty="hard", **requested)
    assert generator.observe_overrides(grid) == requested
    assert generator.self_check(grid, meta={"overrides": requested}) == []
    assert generator.rule_mirror(grid) != grid


def test_semantic_controls_choose_the_correct_branch():
    special = generator.generate(
        13, 8, difficulty="hard", edge_mode="tall_special", shape_style="mixed"
    )
    short = generator.generate(
        13, 8, difficulty="hard", edge_mode="short_control", shape_style="mixed"
    )
    absent = generator.generate(
        13, 8, difficulty="hard", edge_mode="none", shape_style="mixed"
    )
    assert generator.SEMANTIC_WITNESSES["bottom_tall_right_edge_extrudes"](special)
    assert generator.SEMANTIC_WITNESSES["bottom_short_right_edge_still_slides"](short)
    assert generator.SEMANTIC_WITNESSES["bottom_without_right_edge_control"](absent)
    for grid in (special, short, absent):
        assert generator.SEMANTIC_WITNESSES[
            "top_tall_right_edge_still_slides_up"
        ](grid)
        assert generator.SEMANTIC_WITNESSES[
            "bottom_tall_nonedge_still_slides_down"
        ](grid)


def test_self_check_rejects_structural_and_semantic_impostors():
    base = generator.generate(211, 4, difficulty="medium")
    facts = generator._scene_facts(base)
    background = facts["background"]
    top_color = facts["top_color"]
    bottom_color = facts["bottom_color"]
    cases = {}

    grid = copy.deepcopy(base)
    grid[0][3] = background
    cases["broken top band"] = grid

    grid = copy.deepcopy(base)
    grid[-1][3] = background
    cases["broken bottom band"] = grid

    grid = copy.deepcopy(base)
    grid[-1] = [top_color] * len(grid[-1])
    cases["aliased markers"] = grid

    grid = copy.deepcopy(base)
    for component in facts["top_objects"][1:]:
        for row, column in component:
            grid[row][column] = background
    cases["too few top objects"] = grid

    grid = copy.deepcopy(base)
    row, column = facts["bottom_objects"][0][0]
    grid[row][column] = 0 if 0 not in facts["palette"] else 9
    cases["illegal fourth color"] = grid

    grid = copy.deepcopy(base)
    first_top = facts["top_objects"][0]
    delta = 1 - min(row for row, _ in first_top)
    for row, column in first_top:
        grid[row][column] = background
    for row, column in first_top:
        grid[row + delta][column] = top_color
    cases["identity-aligned top object"] = grid

    failures = {name: generator.self_check(grid) for name, grid in cases.items()}
    assert all(errors for errors in failures.values()), failures
    for texture in generator.DEGENERATE_TEXTURES:
        assert generator.self_check(generator.generate(1, 1, texture=texture))


def test_self_check_rejects_projected_destination_overdraw():
    grid = [[7 for _ in range(16)] for _ in range(16)]
    grid[0] = [1] * 16
    grid[-1] = [4] * 16

    # These are distinct top-color source objects, but both slide to row 1 and
    # would overdraw column 4.  The remaining objects make the scene otherwise
    # valid under the task's teaching grammar.
    grid[4][3] = grid[4][4] = 1
    grid[7][4] = grid[7][5] = 1
    grid[5][8] = 4
    grid[9][11] = 4

    assert generator._scene_facts(grid)["errors"] == []
    collisions = generator.projected_destination_collisions(grid)
    assert collisions and collisions[0]["shared"] == [(1, 4)]
    assert any("overlap after projection" in error for error in generator.self_check(grid))
    # The oracle can still execute the negative fixture; rejection is a lesson
    # distribution boundary, not a claim that the Racket rule is undefined.
    assert generator.rule_mirror(grid) != grid


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_generated_destinations_are_disjoint(difficulty):
    for sample_index in range(50):
        grid = generator.generate(5000 + sample_index, sample_index, difficulty=difficulty)
        assert generator.projected_destination_collisions(grid) == []
        assert generator.self_check(grid) == []


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(20260724)
    state = random.getstate()
    first = generator.generate(77, 19, difficulty="hard")
    assert random.getstate() == state
    second = generator.generate(77, 19, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 0
    assert second[0][0] != 0


def test_unknown_or_conflicting_overrides_reject_loudly():
    with pytest.raises(ValueError, match="unsupported override"):
        generator.generate(1, 1, bogus_axis=3)
    with pytest.raises(ValueError, match="cannot be combined"):
        generator.generate(1, 1, texture="no_objects", grid_h=16)
    with pytest.raises(ValueError, match="unknown difficulty"):
        generator.generate(1, 1, difficulty="expert")
