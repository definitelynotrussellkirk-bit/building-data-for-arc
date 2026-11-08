from __future__ import annotations

import hashlib
import importlib
import json
import random
import pytest

from reviewer_support import canonical_pairs as read_canonical_pairs, canonical_path, find_root


TASK = "5f9a2df57599"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = find_root(__file__)
BASE = canonical_path(ROOT).parent.parent / "base/solutions/training/e73095fd__5f9a2df57599.json"


def canonical_row():
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row
    raise AssertionError("canonical row missing")


def canonical_pairs():
    return [
        {"input": pair["input"], "output": pair["output"]}
        for pair in read_canonical_pairs(TASK, root=ROOT, labeled_only=True)
    ]


def independent_oracle(grid):
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == 0}
    output = [row[:] for row in grid]
    facts = []
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
        row0, row1 = min(r for r, _ in cells), max(r for r, _ in cells)
        col0, col1 = min(c for _, c in cells), max(c for _, c in cells)
        top = row0 > 0 and all(grid[row0 - 1][c] == 5 for c in range(col0, col1 + 1))
        bottom = row1 < height - 1 and all(grid[row1 + 1][c] == 5 for c in range(col0, col1 + 1))
        left = col0 == 0 or all(grid[r][col0 - 1] == 5 for r in range(row0, row1 + 1))
        right = col1 == width - 1 or all(grid[r][col1 + 1] == 5 for r in range(row0, row1 + 1))
        special = col0 == col1 == 0 and row1 > row0
        eligible = top and bottom and left and right and not special
        if eligible:
            for row, col in cells:
                output[row][col] = 4
        facts.append((cells, (row0, col0, row1, col1), eligible, special))
    return output, facts


def frozen(grid):
    return tuple(tuple(row) for row in grid)


@pytest.mark.parametrize("index,profile", list(enumerate(MODULE.PUBLIC_PROFILES)))
def test_exact_public_replay(index, profile):
    pair = canonical_pairs()[index]
    grid = MODULE.generate(100 + index, index, scene_profile=profile)
    oracle, _ = independent_oracle(grid)
    assert grid == pair["input"]
    assert MODULE.rule_mirror(grid) == pair["output"] == oracle
    assert MODULE.canonical_profile_signature(grid) == profile
    assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", MODULE.GENERAL_PROFILES)
def test_every_general_profile_in_every_difficulty(profile, difficulty):
    grid = MODULE.generate(20_000 + len(profile), 7, difficulty=difficulty, scene_profile=profile)
    analysis = MODULE._analysis(grid)
    oracle, facts = independent_oracle(grid)
    expected_count = int(profile.rsplit("_n", 1)[1])
    assert analysis["errors"] == []
    assert analysis["scene_profile"] == profile
    assert analysis["facts"]["eligible_count"] == expected_count
    assert analysis["output"] == MODULE.rule_mirror(grid) == oracle
    assert sum(eligible for _, _, eligible, _ in facts) == expected_count
    assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
    if difficulty == "hard":
        assert analysis["facts"]["special_exclusions"] >= 1


@pytest.mark.parametrize("count", [1, 2, 3])
def test_interior_rectangular_and_irregular_profiles_are_observable(count):
    for stem in ("rect", "irregular"):
        grid = MODULE.generate(30_000 + count, count, scene_profile=f"{stem}_n{count}")
        eligible = MODULE._analysis(grid)["facts"]["eligible"]
        assert all(facts["edge"] == "interior" for facts in eligible)
        assert all(facts["rectangle"] for facts in eligible) is (stem == "rect") if stem == "rect" else any(not facts["rectangle"] for facts in eligible)


@pytest.mark.parametrize("edge", ["left", "right"])
def test_vertical_canvas_edges_count_as_walls(edge):
    count = 1
    grid = MODULE.generate(41_001, 1, scene_profile=f"{edge}_n1")
    eligible = MODULE._analysis(grid)["facts"]["eligible"]
    assert len(eligible) == count
    assert {facts["edge"] for facts in eligible} == {edge}
    assert all(facts[f"{edge}_wall"] for facts in eligible)


def test_top_and_bottom_canvas_edges_do_not_count_as_walls():
    top = [[5] * 8 for _ in range(8)]
    for row in range(0, 2):
        for col in range(2, 5):
            top[row][col] = 0
    facts = next(facts for facts in (MODULE._region_facts(top, cells) for cells in MODULE._zero_components(top)) if facts["bbox"] == (0, 2, 1, 4))
    assert not facts["top_wall"] and not facts["eligible"]

    bottom = [[5] * 8 for _ in range(8)]
    for row in range(6, 8):
        for col in range(2, 5):
            bottom[row][col] = 0
    facts = next(facts for facts in (MODULE._region_facts(bottom, cells) for cells in MODULE._zero_components(bottom)) if facts["bbox"] == (6, 2, 7, 4))
    assert not facts["bottom_wall"] and not facts["eligible"]


def test_column_zero_vertical_special_case_remains_black():
    grid = [[5] * 8 for _ in range(8)]
    for row in range(2, 5):
        grid[row][0] = 0
    facts = MODULE._region_facts(grid, MODULE._zero_components(grid)[0])
    assert facts["top_wall"] and facts["bottom_wall"] and facts["left_wall"] and facts["right_wall"]
    assert facts["excluded_left_vertical"] and not facts["eligible"]
    assert MODULE.rule_mirror(grid) == grid


def test_irregular_region_paints_object_cells_not_its_whole_bbox():
    grid = MODULE.generate(51, 3, scene_profile="irregular_n1")
    analysis = MODULE._analysis(grid)
    region = analysis["facts"]["eligible"][0]
    row0, col0, row1, col1 = region["bbox"]
    assert not region["rectangle"]
    output = MODULE.rule_mirror(grid)
    assert all(output[row][col] == 4 for row, col in region["cells"])
    missing = {(row, col) for row in range(row0, row1 + 1) for col in range(col0, col1 + 1)} - set(region["cells"])
    assert missing and all(output[row][col] == 5 for row, col in missing)


def test_determinism_fresh_returns_and_global_rng_independence():
    random.seed(991)
    state = random.getstate()
    first = MODULE.generate(73, 6, difficulty="hard", scene_profile="mixed_n3")
    assert random.getstate() == state
    second = MODULE.generate(73, 6, difficulty="hard", scene_profile="mixed_n3")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 4
    assert MODULE.generate(73, 6, difficulty="hard", scene_profile="mixed_n3") == second


def test_generated_pool_has_high_input_and_output_diversity():
    grids = [MODULE.generate(seed, seed + 3) for seed in range(200)]
    outputs = [MODULE.rule_mirror(grid) for grid in grids]
    assert len({frozen(grid) for grid in grids}) >= 180
    assert len({frozen(output) for output in outputs}) >= 180
    assert len({(len(grid), len(grid[0])) for grid in grids}) >= 40
    assert {value for output in outputs for row in output for value in row} == {0, 4, 5}


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
        [[4] * 8 for _ in range(8)],
        [[10] * 8 for _ in range(8)],
    ],
)
def test_malformed_grids_fail_closed(grid):
    assert MODULE.self_check(grid)
    with pytest.raises(ValueError):
        MODULE.rule_mirror(grid)


def test_semantic_mutations_fail_closed():
    grid = MODULE.generate(89, 9, scene_profile="rect_n2")
    facts = MODULE._analysis(grid)["facts"]

    broken_wall = [row[:] for row in grid]
    for region in facts["eligible"]:
        row0, col0, _, _ = region["bbox"]
        broken_wall[row0 - 1][col0] = 0
    assert MODULE.self_check(broken_wall)

    yellow_input = [row[:] for row in grid]
    yellow_input[0][0] = 4
    assert MODULE.self_check(yellow_input)

    no_gray = [[0] * len(grid[0]) for _ in grid]
    assert MODULE.self_check(no_gray)


@pytest.mark.parametrize("kwargs", [{"scene_profile": "unknown"}, {"texture": "all_rooms"}, {"difficulty": "expert"}])
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, **kwargs)


def test_axis_contract_is_literal_and_minimal():
    assert set(MODULE.AXES) == {"scene_profile"}
    assert tuple(MODULE.AXES["scene_profile"]["valid"].split("|")) == MODULE.SCENE_PROFILES
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()


def test_rule_hash_and_base_sources_are_exactly_synchronized():
    source = canonical_row()["program_solution"]
    digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert MODULE.RULE_HASH == digest == "5b73d3931a5c"
    base = json.loads(BASE.read_text())
    normalized = " ".join(source.split())
    assert " ".join(base["racket_target"]["raw_code"].split()) == normalized
    assert " ".join(base["racket_target"]["target_code"].split()) == normalized
