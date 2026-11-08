from __future__ import annotations

import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest


TASK = "7185b8225f1c"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
BASES = (
    ROOT / "data/base/solutions/training/b27ca6d3__7185b8225f1c.json",
    ROOT / "data/base/solutions/augmented/b27ca6d3__a6c6cc0409ee.json",
)


def canonical_rows():
    rows = []
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            rows.append(row)
    return rows


def unique_canonical_pairs():
    pairs, seen = [], set()
    for row in canonical_rows():
        for pair in row.get("train", []) + row.get("test", []):
            key = tuple(map(tuple, pair["input"]))
            if key not in seen:
                seen.add(key)
                pairs.append(pair)
    return pairs


def independent_components(grid):
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == 2}
    result = []
    while unseen:
        start = unseen.pop()
        cells = {start}
        frontier = [start]
        while frontier:
            row, col = frontier.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbour = row + dr, col + dc
                if neighbour in unseen:
                    unseen.remove(neighbour)
                    cells.add(neighbour)
                    frontier.append(neighbour)
        result.append(cells)
    return result


def independent_oracle(grid):
    height, width = len(grid), len(grid[0])
    output = [row[:] for row in grid]
    for cells in independent_components(grid):
        if len(cells) < 2:
            continue
        row0, row1 = min(r for r, _ in cells), max(r for r, _ in cells)
        col0, col1 = min(c for _, c in cells), max(c for _, c in cells)
        for row in range(max(0, row0 - 1), min(height, row1 + 2)):
            for col in range(max(0, col0 - 1), min(width, col1 + 2)):
                if output[row][col] == 0:
                    output[row][col] = 3
    return output


def frozen(grid):
    return tuple(map(tuple, grid))


@pytest.mark.parametrize("index,profile", list(enumerate(MODULE.PUBLIC_PROFILES)))
def test_exact_public_replay(index, profile):
    pair = unique_canonical_pairs()[index]
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
    assert analysis["facts"]["multi_count"] >= 1
    assert analysis["facts"]["singleton_count"] >= 1
    assert analysis["output"] == MODULE.rule_mirror(grid) == independent_oracle(grid)
    assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


def test_singletons_remain_red_even_inside_a_selected_rectangle():
    grid = [[0] * 9 for _ in range(9)]
    grid[4][3] = grid[4][4] = 2
    grid[3][5] = 2
    output = MODULE.rule_mirror(grid)
    assert output[3][5] == 2
    assert output[3][2] == output[5][5] == 3


def test_concave_bbox_hole_is_filled_not_left_as_background():
    grid = MODULE.generate(31, 1, scene_profile="polyomino_concave")
    facts = next(item for item in MODULE._analysis(grid)["facts"]["components"] if item["concave"])
    row0, col0, row1, col1 = facts["bbox"]
    holes = {(row, col) for row in range(row0, row1 + 1) for col in range(col0, col1 + 1)} - set(facts["cells"])
    assert holes
    output = MODULE.rule_mirror(grid)
    assert all(output[row][col] == 3 for row, col in holes)


@pytest.mark.parametrize("profile", ["domino_edge_h", "domino_edge_v"])
def test_edge_halos_clip_to_canvas(profile):
    grid = MODULE.generate(41 + len(profile), 2, scene_profile=profile)
    analysis = MODULE._analysis(grid)
    assert analysis["facts"]["edge_multis"] >= 1
    assert MODULE.rule_mirror(grid) == independent_oracle(grid)


def test_overlapping_halos_form_a_union_without_merging_red_components():
    grid = MODULE.generate(51, 3, scene_profile="domino_overlap")
    analysis = MODULE._analysis(grid)
    assert analysis["facts"]["multi_count"] == 2
    assert analysis["facts"]["overlap_pairs"] >= 1
    assert MODULE.rule_mirror(grid) == independent_oracle(grid)


def test_public_family_randomizes_only_singleton_nuisance():
    exact = MODULE.generate(1, 0, scene_profile="public_3")
    ordinary = next(
        grid
        for seed in range(1000)
        for grid in [MODULE.generate(60_000 + seed, seed)]
        if MODULE._analysis(grid)["scene_profile"] == "public_3" and grid != exact
    )
    exact_multis = {frozenset(cells) for cells in MODULE._red_components(exact) if len(cells) >= 2}
    ordinary_multis = {frozenset(cells) for cells in MODULE._red_components(ordinary) if len(cells) >= 2}
    assert exact_multis == ordinary_multis
    assert MODULE.canonical_profile_signature(ordinary) is None
    assert MODULE.canonical_family_signature(ordinary) == "public_3"


def test_lawful_component_recombination_is_not_mislabeled_public_family():
    grid = MODULE.generate(71, 4, scene_profile="domino_mixed")
    assert MODULE.canonical_family_signature(grid) is None
    assert MODULE._analysis(grid)["scene_profile"] == "domino_mixed"


def test_determinism_fresh_returns_and_global_rng_independence():
    random.seed(991)
    state = random.getstate()
    first = MODULE.generate(73, 6, difficulty="hard", scene_profile="polyomino_mixed")
    assert random.getstate() == state
    second = MODULE.generate(73, 6, difficulty="hard", scene_profile="polyomino_mixed")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 2 if first[0][0] == 0 else 0
    assert MODULE.generate(73, 6, difficulty="hard", scene_profile="polyomino_mixed") == second


def test_default_prior_covers_every_profile_and_public_family():
    for difficulty in ("easy", "medium", "hard"):
        grids = [MODULE.generate(80_000 + seed, seed, difficulty=difficulty) for seed in range(1200)]
        profiles = [MODULE._analysis(grid)["scene_profile"] for grid in grids]
        assert sum(profile in MODULE.PUBLIC_PROFILES for profile in profiles) >= 300
        assert set(profiles) == set(MODULE.SCENE_PROFILES)
        assert all(not MODULE.self_check(grid) for grid in grids)
        assert all(
            MODULE.canonical_family_signature(grid) == profile
            for grid, profile in zip(grids, profiles)
            if profile in MODULE.PUBLIC_PROFILES
        )


def test_generated_pool_has_high_semantic_diversity():
    grids = [MODULE.generate(seed, seed + 3) for seed in range(240)]
    outputs = [MODULE.rule_mirror(grid) for grid in grids]
    assert len({frozen(grid) for grid in grids}) >= 225
    assert len({frozen(output) for output in outputs}) >= 225
    assert len({(len(grid), len(grid[0])) for grid in grids}) >= 60
    assert {value for output in outputs for row in output for value in row} == {0, 2, 3}


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0] * 8 for _ in range(7)],
        [[0] * 31 for _ in range(8)],
        [[0] * 8 for _ in range(31)],
        [[0] * 8 for _ in range(7)] + [[0] * 7],
        [[False] * 8 for _ in range(8)],
        [[3] * 8 for _ in range(8)],
        [[10] * 8 for _ in range(8)],
    ],
)
def test_malformed_grids_fail_closed(grid):
    assert MODULE.self_check(grid)
    with pytest.raises(ValueError):
        MODULE.rule_mirror(grid)


def test_semantic_mutations_fail_closed():
    grid = MODULE.generate(89, 9, scene_profile="domino_interior_h")
    components = MODULE._red_components(grid)

    only_singletons = [[0] * len(grid[0]) for _ in grid]
    for cells in components:
        if len(cells) == 1:
            row, col = next(iter(cells))
            only_singletons[row][col] = 2
    assert MODULE.self_check(only_singletons)

    no_singletons = [[0] * len(grid[0]) for _ in grid]
    for cells in components:
        if len(cells) >= 2:
            for row, col in cells:
                no_singletons[row][col] = 2
    assert MODULE.self_check(no_singletons)

    green_input = [row[:] for row in grid]
    green_input[0][0] = 3
    assert MODULE.self_check(green_input)

    all_red = [[2] * len(grid[0]) for _ in grid]
    assert MODULE.self_check(all_red)


@pytest.mark.parametrize("kwargs", [{"scene_profile": "unknown"}, {"texture": "all_singletons"}, {"group_count": 3}, {"difficulty": "expert"}])
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, **kwargs)


def test_axis_contract_is_literal_and_minimal():
    assert set(MODULE.AXES) == {"scene_profile"}
    assert tuple(MODULE.AXES["scene_profile"]["valid"].split("|")) == MODULE.SCENE_PROFILES
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()


def test_rule_hash_and_base_sources_are_exactly_synchronized():
    sources = {row["program_solution"] for row in canonical_rows()}
    assert len(sources) == 1
    source = sources.pop()
    digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert MODULE.RULE_HASH == digest == "df2d840acdd1"
    for path in BASES:
        base = json.loads(path.read_text())
        assert base["racket_target"]["raw_code"] == source
        assert base["racket_target"]["target_code"] == source
