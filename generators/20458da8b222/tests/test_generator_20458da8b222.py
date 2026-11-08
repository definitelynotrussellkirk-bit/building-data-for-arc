from __future__ import annotations

from collections import Counter, deque
import hashlib
import importlib
import json
from pathlib import Path
import random

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE = importlib.import_module("puzzle_generators.per_puzzle.20458da8b222.generator")
BASE = ROOT / "data/base/solutions/banks/110177dcbe3a/H117__20458da8b222.json"


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == MODULE.TASK_ID:
                return row
    raise AssertionError("missing canonical row")


def canonical_pairs():
    row = canonical_row()
    train = row.get("train") or []
    test = row.get("test") or []
    if isinstance(train, dict):
        train = [train]
    if isinstance(test, dict):
        test = [test]
    return list(train) + list(test)


def independent_oracle(grid):
    height, width = len(grid), len(grid[0])
    seeds = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, 5)
    ]
    distance_maps = []
    for start_row, start_col, _ in seeds:
        distances = [[10**9] * width for _ in range(height)]
        distances[start_row][start_col] = 0
        queue = deque([(start_row, start_col)])
        while queue:
            row, col = queue.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = row + dr, col + dc
                if (
                    0 <= nr < height
                    and 0 <= nc < width
                    and grid[nr][nc] != 5
                    and distances[nr][nc] > distances[row][col] + 1
                ):
                    distances[nr][nc] = distances[row][col] + 1
                    queue.append((nr, nc))
        distance_maps.append(distances)
    output = [row[:] for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 5:
                continue
            values = [distances[row][col] for distances in distance_maps]
            best = min(values)
            winners = [index for index, value in enumerate(values) if value == best]
            output[row][col] = seeds[winners[0]][2] if len(winners) == 1 else 8
    return output


def seed_cells(grid):
    return [
        (row, col, grid[row][col])
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] not in (0, 5)
    ]


def test_all_canonical_pairs_match_the_independent_rule():
    assert len(canonical_pairs()) == 3
    expected_profiles = ("open_two", "split_two", "open_two_unique")
    for pair, expected_profile in zip(canonical_pairs(), expected_profiles):
        original = json.loads(json.dumps(pair["input"]))
        assert MODULE.rule_mirror(pair["input"]) == independent_oracle(pair["input"]) == pair["output"]
        assert MODULE.self_check(pair["input"]) == []
        assert MODULE.observe_overrides(pair["input"]) == {"scene_profile": expected_profile}
        assert pair["input"] == original


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("profile", MODULE.SCENE_PROFILES)
def test_every_profile_is_exact_observable_and_semantically_live(profile, difficulty):
    for seed in range(8):
        grid = MODULE.generate(10_000 + seed, seed * 19, difficulty=difficulty, scene_profile=profile)
        analysis = MODULE._analysis(grid)
        assert analysis["errors"] == []
        assert analysis["scene_profile"] == profile
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
        assert MODULE.rule_mirror(grid) == independent_oracle(grid)
        if profile in {"gated_two", "gated_three", "maze_four"}:
            assert analysis["manhattan_diff_cells"] > 0
        if profile in {"split_two", "split_four"}:
            assert len(analysis["components"]) == 2
        if profile not in {"split_two", "open_two_unique"}:
            assert analysis["tie_cells"] > 0
        if profile == "open_two_unique":
            assert analysis["tie_cells"] == 0


def test_default_distribution_covers_every_linked_branch_in_every_band():
    for difficulty in ("easy", "medium", "hard"):
        grids = [MODULE.generate(40_000 + seed, seed * 23, difficulty=difficulty) for seed in range(350)]
        analyses = [MODULE._analysis(grid) for grid in grids]
        profiles = Counter(item["scene_profile"] for item in analyses)
        outputs = [MODULE.rule_mirror(grid) for grid in grids]
        assert set(profiles) == set(MODULE.SCENE_PROFILES)
        assert min(profiles.values()) >= 25
        assert all(item["errors"] == [] for item in analyses)
        assert any(item["manhattan_diff_cells"] > 0 for item in analyses)
        assert any(len(item["components"]) == 2 for item in analyses)
        assert any(item["tie_cells"] == 0 for item in analyses)
        assert any(item["tie_cells"] > 0 for item in analyses)
        assert len({frozen(grid) for grid in grids}) >= 345
        assert len({frozen(grid) for grid in outputs}) >= 340
        assert all(grid != output for grid, output in zip(grids, outputs))


def test_self_check_rejects_targeted_semantic_impostors():
    valid = MODULE.generate(91, 7, difficulty="medium", scene_profile="gated_three")
    assert MODULE.self_check(valid) == []

    broken_border = [row[:] for row in valid]
    broken_border[0][1] = 0
    assert any("border" in error for error in MODULE.self_check(broken_border))

    duplicate_seed_color = [row[:] for row in valid]
    seeds = seed_cells(duplicate_seed_color)
    duplicate_seed_color[seeds[1][0]][seeds[1][1]] = seeds[0][2]
    assert any("distinct" in error for error in MODULE.self_check(duplicate_seed_color))

    unseeded_component = MODULE.generate(92, 8, difficulty="medium", scene_profile="split_two")
    split_seeds = seed_cells(unseeded_component)
    unseeded_component[split_seeds[0][0]][split_seeds[0][1]] = 0
    assert any("component" in error for error in MODULE.self_check(unseeded_component))

    single_seed = [[0] * 7 for _ in range(5)]
    MODULE._draw_border(single_seed)
    single_seed[2][3] = 2
    assert any("2-4 seeds" in error for error in MODULE.self_check(single_seed))

    reserved_tie_seed = [row[:] for row in valid]
    row, col, _ = seed_cells(reserved_tie_seed)[0]
    reserved_tie_seed[row][col] = 8
    assert any("reserved" in error for error in MODULE.self_check(reserved_tie_seed))

    useless_wall = [[0] * 9 for _ in range(7)]
    MODULE._draw_border(useless_wall)
    useless_wall[1][1] = 2
    useless_wall[1][7] = 3
    useless_wall[5][4] = 5
    errors = MODULE.self_check(useless_wall)
    assert any("change at least one winner" in error for error in errors)


def test_determinism_fresh_returns_input_purity_and_global_rng_isolation():
    random.seed(9157)
    state = random.getstate()
    first = MODULE.generate(101, 13, difficulty="hard", scene_profile="maze_four")
    assert random.getstate() == state
    second = MODULE.generate(101, 13, difficulty="hard", scene_profile="maze_four")
    assert first == second and first is not second and first[0] is not second[0]
    expected = MODULE.rule_mirror(first)
    assert first == second
    first[0][0] = 9
    assert MODULE.generate(101, 13, difficulty="hard", scene_profile="maze_four") == second
    assert MODULE.rule_mirror(second) == expected


def test_axis_contract_is_minimal_literal_and_fully_observable():
    assert set(MODULE.AXES) == {"scene_profile"}
    assert tuple(MODULE.AXES["scene_profile"]["valid"].split("|")) == MODULE.SCENE_PROFILES
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, scene_profile="unknown")
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, grid_h=9)
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, difficulty="expert")


def test_rule_hash_and_task_local_authority_are_pinned_by_normalized_content():
    canonical = canonical_row()["program_solution"]
    digest = hashlib.sha256(" ".join(canonical.split()).encode()).hexdigest()[:12]
    base = json.loads(BASE.read_text())
    assert MODULE.RULE_HASH == digest == "b4a1c41b804f"
    assert base["racket_target"]["target_code"] == canonical
