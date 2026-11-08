from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root, load_selected_generator


TASK = "7944933e200f"
ROOT = find_root(__file__)
MODULE, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)
CANONICAL = canonical_path(ROOT)
BASE = CANONICAL.parent.parent / "base/solutions/training/d9fac9be__7944933e200f.json"


def canonical_row():
    return next(
        json.loads(line)
        for line in CANONICAL.read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    )


def independent_objects(grid):
    height, width = len(grid), len(grid[0])
    visited, objects = set(), []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in visited:
                continue
            visited.add((start_row, start_col))
            cells, frontier = {(start_row, start_col)}, [(start_row, start_col)]
            while frontier:
                row, col = frontier.pop()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neighbour = row + dr, col + dc
                    if 0 <= neighbour[0] < height and 0 <= neighbour[1] < width and neighbour not in visited and grid[neighbour[0]][neighbour[1]] == color:
                        visited.add(neighbour)
                        cells.add(neighbour)
                        frontier.append(neighbour)
            objects.append((color, cells))
    return objects


def independent_oracle(grid):
    objects = independent_objects(grid)
    counts = Counter(value for row in grid for value in row if value != 0)
    color, cells = sorted(objects, key=lambda item: counts[item[0]])[0]
    row0, row1 = min(row for row, _ in cells), max(row for row, _ in cells)
    col0, col1 = min(col for _, col in cells), max(col for _, col in cells)
    return [row[col0 : col1 + 1] for row in grid[row0 : row1 + 1]]


def frozen(grid):
    return tuple(map(tuple, grid))


@pytest.mark.parametrize("index,profile", list(enumerate(MODULE.PUBLIC_PROFILES)))
def test_exact_public_replay(index, profile):
    pair = (canonical_row()["train"] + canonical_row()["test"])[index]
    grid = MODULE.generate(100 + index, index, scene_profile=profile)
    assert grid == pair["input"]
    assert MODULE.rule_mirror(grid) == pair["output"] == independent_oracle(grid)
    assert MODULE.canonical_profile_signature(grid) == profile
    assert MODULE.canonical_family_signature(grid) == profile
    assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", MODULE.GENERAL_PROFILES)
def test_every_general_profile_in_every_band(profile, difficulty):
    grid = MODULE.generate(20_000 + len(profile), 7, difficulty=difficulty, scene_profile=profile)
    analysis = MODULE._analysis(grid)
    assert analysis["errors"] == []
    assert analysis["scene_profile"] == profile
    assert analysis["facts"]["color_count"] >= 2
    assert analysis["output"] == MODULE.rule_mirror(grid) == independent_oracle(grid)
    assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


def test_ranking_uses_global_color_frequency_not_component_size():
    grid = [[0] * 8 for _ in range(8)]
    for cell in ((0, 0), (0, 1), (1, 0)):
        grid[cell[0]][cell[1]] = 2
    for cell in ((3, 3), (3, 5), (5, 3), (5, 5), (7, 1), (7, 3), (7, 5), (7, 7)):
        grid[cell[0]][cell[1]] = 4
    output = MODULE.rule_mirror(grid)
    assert output == [[2, 2], [2, 0]]


def test_global_count_tie_uses_first_row_major_object():
    grid = MODULE.generate(31, 1, scene_profile="global_tie_first_object")
    facts = MODULE._analysis(grid)["facts"]
    assert facts["minimum_tie"]
    assert facts["selected_object_index"] == 0
    assert MODULE.rule_mirror(grid) == independent_oracle(grid)


def test_crop_is_unmasked_and_preserves_intruder():
    grid = MODULE.generate(41, 2, scene_profile="crop_with_intruder")
    analysis = MODULE._analysis(grid)
    output = MODULE.rule_mirror(grid)
    selected_color = analysis["facts"]["selected"]["color"]
    assert analysis["facts"]["intruder_count"] >= 1
    assert any(value not in (0, selected_color) for row in output for value in row)
    assert output == independent_oracle(grid)


def test_diagonal_same_color_cells_are_separate_four_connected_objects():
    grid = MODULE.generate(51, 3, scene_profile="diagonal_split")
    facts = MODULE._analysis(grid)["facts"]
    assert len(facts["selected_color_objects"]) >= 2
    assert facts["selected"]["size"] == 1
    assert MODULE.rule_mirror(grid) == [[facts["selected"]["color"]]]


def test_public_family_preserves_component_semantics_under_relocation_and_palette():
    exact = MODULE.generate(1, 0, scene_profile="public_5")
    ordinary = next(
        grid
        for seed in range(500)
        for grid in [MODULE.generate(60_000 + seed, seed)]
        if MODULE._analysis(grid)["scene_profile"] == "public_5" and grid != exact
    )
    assert MODULE.canonical_profile_signature(ordinary) is None
    assert MODULE.canonical_family_signature(ordinary) == "public_5"
    assert MODULE._public_family_key(ordinary) in MODULE._PUBLIC_FAMILIES


def test_lawful_recombination_is_not_mislabeled_public_family():
    grid = MODULE.generate(71, 4, scene_profile="rare_polyomino")
    assert MODULE.canonical_family_signature(grid) is None
    assert MODULE._analysis(grid)["scene_profile"] == "rare_polyomino"


def test_determinism_fresh_returns_and_global_rng_independence():
    random.seed(991)
    state = random.getstate()
    first = MODULE.generate(73, 6, difficulty="hard", scene_profile="three_color_rank")
    assert random.getstate() == state
    second = MODULE.generate(73, 6, difficulty="hard", scene_profile="three_color_rank")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = (first[0][0] + 1) % 10
    assert MODULE.generate(73, 6, difficulty="hard", scene_profile="three_color_rank") == second


def test_default_prior_covers_every_profile_and_public_family():
    for difficulty in ("easy", "medium", "hard"):
        grids = [MODULE.generate(80_000 + seed, seed, difficulty=difficulty) for seed in range(1500)]
        profiles = [MODULE._analysis(grid)["scene_profile"] for grid in grids]
        assert sum(profile in MODULE.PUBLIC_PROFILES for profile in profiles) >= 400
        assert set(profiles) == set(MODULE.SCENE_PROFILES)
        assert all(not MODULE.self_check(grid) for grid in grids)
        assert all(
            MODULE.canonical_family_signature(grid) == profile
            for grid, profile in zip(grids, profiles)
            if profile in MODULE.PUBLIC_PROFILES
        )


def test_generated_pool_has_strong_pair_and_shape_diversity():
    grids = [MODULE.generate(seed, seed + 3) for seed in range(300)]
    outputs = [MODULE.rule_mirror(grid) for grid in grids]
    assert len({frozen(grid) for grid in grids}) >= 290
    assert len({(frozen(grid), frozen(output)) for grid, output in zip(grids, outputs)}) >= 290
    assert len({frozen(output) for output in outputs}) >= 110
    assert len({(len(output), len(output[0])) for output in outputs}) >= 12
    assert {value for output in outputs for row in output for value in row} == set(range(10))


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0] * 5 for _ in range(4)],
        [[0] * 31 for _ in range(5)],
        [[0] * 5 for _ in range(31)],
        [[0] * 5 for _ in range(4)] + [[0] * 4],
        [[False] * 5 for _ in range(5)],
        [[10] * 5 for _ in range(5)],
        [[0] * 5 for _ in range(5)],
        [[2] * 5 for _ in range(5)],
    ],
)
def test_malformed_or_one_color_grids_fail_closed(grid):
    assert MODULE.self_check(grid)
    if MODULE._valid_grid(grid):
        with pytest.raises(ValueError):
            MODULE.rule_mirror(grid)


def test_semantic_mutations_fail_closed():
    grid = MODULE.generate(89, 9, scene_profile="rare_polyomino")

    one_color = [[0 if value == 0 else 2 for value in row] for row in grid]
    assert MODULE.self_check(one_color)

    all_background = [[0] * len(grid[0]) for _ in grid]
    assert MODULE.self_check(all_background)

    singleton_only = [[0] * 8 for _ in range(8)]
    singleton_only[3][3] = 2
    assert MODULE.self_check(singleton_only)

    full_bbox = [[0] * 7 for _ in range(7)]
    for row, col in [(0, c) for c in range(7)] + [(r, 0) for r in range(1, 7)] + [(6, c) for c in range(1, 7)] + [(r, 6) for r in range(1, 6)]:
        full_bbox[row][col] = 2
    for row in range(1, 6):
        for col in range(1, 6):
            full_bbox[row][col] = 4
    assert MODULE.self_check(full_bbox)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"scene_profile": "unknown"},
        {"texture": "no_rare"},
        {"rare_color": 4},
        {"rare_object_size": 3},
        {"difficulty": "expert"},
    ],
)
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, **kwargs)


def test_axis_contract_is_literal_and_minimal():
    assert set(MODULE.AXES) == {"scene_profile"}
    assert tuple(MODULE.AXES["scene_profile"]["valid"].split("|")) == MODULE.SCENE_PROFILES
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()


def test_selected_rule_is_synchronized_and_archival_source_is_preserved():
    source = canonical_row()["program_solution"]
    digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert MODULE.RULE_HASH == digest == "9b761bca5c45"
    base = json.loads(BASE.read_text())
    assert hashlib.sha256(base["racket_target"]["raw_code"].encode()).hexdigest() == "9b761bca5c4577e1d0ec28e5747e599423b62a060f51669401ed5238cbceae0d"
    assert base["racket_target"]["target_code"] == source
