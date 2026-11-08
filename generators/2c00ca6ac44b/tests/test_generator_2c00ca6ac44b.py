from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest


TASK_ID = "2c00ca6ac44b"
MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def _canonical_pairs():
    pairs = []
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            pairs.extend(row.get("train", []))
            pairs.extend(row.get("test", []))
    return pairs


def _mutations(grid):
    facts = MODULE.analyze_scene(grid)
    assert not facts["errors"]
    lines = facts["facts"]["lines"]
    first = lines[0]
    color = first["color"]
    cells = list(first["cells"])

    short = copy.deepcopy(grid)
    for row, col in cells[2:]:
        short[row][col] = 7

    bent = copy.deepcopy(grid)
    row, col = cells[-1]
    bent[row][col] = 7
    candidates = [
        (max(1, row - 1), col),
        (row, max(1, col - 1)),
        (max(1, row - 2), max(1, col - 1)),
    ]
    for nr, nc in candidates:
        if bent[nr][nc] == 7 and (nr, nc) != (0, 0):
            bent[nr][nc] = color
            break

    detached = copy.deepcopy(grid)
    for row in range(1, len(detached) - 1):
        for col in range(1, len(detached[0]) - 1):
            if detached[row][col] == 7 and (row, col) not in cells:
                detached[row][col] = color
                break
        else:
            continue
        break

    bad_sentinel = copy.deepcopy(grid)
    bad_sentinel[0][0] = color

    duplicate_start_row = copy.deepcopy(grid)
    # Move one whole line so its top row equals another line's top row.
    if len(lines) >= 2:
        second = lines[1]
        delta = first["start"][0] - second["start"][0]
        moved = [(r + delta, c) for r, c in second["cells"]]
        if (
            all(0 <= r < len(grid) and 0 <= c < len(grid[0]) for r, c in moved)
            and all(duplicate_start_row[r][c] in (7, second["color"]) for r, c in moved)
        ):
            for r, c in second["cells"]:
                duplicate_start_row[r][c] = 7
            for r, c in moved:
                duplicate_start_row[r][c] = second["color"]
        else:
            duplicate_start_row = None

    out = [short, bent, detached, bad_sentinel]
    if duplicate_start_row is not None:
        out.append(duplicate_start_row)
    return out


def test_rule_hash_and_task_local_authorities_are_exactly_pinned():
    assert MODULE.RULE_HASH == "f361d92f41e6"
    canonical = None
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                canonical = row["program_solution"]
                break
    assert canonical is not None
    for rel in (
        "data/base/solutions/augmented/668eec9a__c695e25f01dc.json",
        "data/base/solutions/training/668eec9a__2c00ca6ac44b.json",
    ):
        record = json.loads((ROOT / rel).read_text())
        assert record["racket_target"]["raw_code"] == canonical
        assert record["racket_target"]["target_code"] == canonical


def test_all_canonical_pairs_match_the_structural_grammar_and_python_mirror():
    pairs = _canonical_pairs()
    assert len(pairs) == 8
    for pair in pairs:
        assert MODULE.self_check(pair["input"]) == []
        signature = MODULE.canonical_profile_signature(pair["input"])
        assert signature in MODULE.SCENE_PROFILES
        before = copy.deepcopy(pair["input"])
        assert MODULE.solve_python(pair["input"]) == pair["output"]
        assert pair["input"] == before


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_generated_draws_are_deterministic_fresh_valid_and_observable(difficulty):
    for seed in range(16):
        state = random.getstate()
        first = MODULE.generate(seed, 31, difficulty=difficulty)
        assert random.getstate() == state
        second = MODULE.generate(seed, 31, difficulty=difficulty)
        assert first == second
        assert first is not second
        assert all(a is not b for a, b in zip(first, second))
        assert MODULE.self_check(first, difficulty=difficulty) == []
        observed = MODULE.observe_overrides(first)
        assert observed["grid_h"] == len(first)
        assert observed["grid_w"] == len(first[0])
        assert observed["n_colors"] == len(
            {value for row in first for value in row if value != 7}
        )
        assert observed["scene_profile"] in MODULE.SCENE_PROFILES
        output = MODULE.solve_python(first)
        assert len(output) == 5 and all(len(row) == 3 for row in output)


def test_all_exact_axis_boundaries_survive_and_are_observed():
    boundary_cases = [
        {"grid_h": 12, "grid_w": 12, "n_colors": 3, "scene_profile": "diagonal_only"},
        {"grid_h": 24, "grid_w": 24, "n_colors": 5, "scene_profile": "with_horizontal"},
        {"grid_h": 12, "grid_w": 24, "n_colors": 5, "scene_profile": "diagonal_only"},
        {"grid_h": 24, "grid_w": 12, "n_colors": 3, "scene_profile": "with_horizontal"},
    ]
    for seed, case in enumerate(boundary_cases):
        grid = MODULE.generate(seed, 71, difficulty="easy", **case)
        assert MODULE.self_check(grid) == []
        observed = MODULE.observe_overrides(grid)
        assert all(observed[key] == value for key, value in case.items())


def test_self_check_rejects_targeted_structural_impostors():
    grid = MODULE.generate(
        90210,
        5,
        difficulty="medium",
        grid_h=16,
        grid_w=16,
        n_colors=5,
        scene_profile="with_horizontal",
    )
    mutations = _mutations(grid)
    assert len(mutations) >= 4
    for mutation in mutations:
        assert MODULE.self_check(mutation), mutation


def test_negative_recombination_breaks_the_linked_line_grammar():
    grid = MODULE.generate(
        8181,
        9,
        difficulty="hard",
        grid_h=18,
        grid_w=18,
        n_colors=4,
        scene_profile="diagonal_only",
    )
    facts = MODULE.analyze_scene(grid)["facts"]
    first, second = facts["lines"][:2]
    recombined = copy.deepcopy(grid)
    # Swap only the tail cell colors: all broad marginals remain, but neither
    # affected color is a single straight segment anymore.
    ar, ac = first["cells"][-1]
    br, bc = second["cells"][-1]
    recombined[ar][ac], recombined[br][bc] = (
        recombined[br][bc],
        recombined[ar][ac],
    )
    assert MODULE.self_check(recombined)
    assert MODULE.canonical_profile_signature(recombined) is None
