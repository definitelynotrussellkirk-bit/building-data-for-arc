from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "85d01dd02c6d"
ROOT = find_root(__file__)
GEN, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
PROFILES = (
    "vertical_solid",
    "vertical_gap",
    "horizontal_solid",
    "horizontal_gap",
    "vertical_segment",
    "horizontal_segment",
)


def reference_output(grid, *, ignore_internal_walls=False, threshold=2):
    height, width = len(grid), len(grid[0])
    seeds = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, 9)
    ]

    def visible(seed, row, col):
        seed_row, seed_col = seed
        if seed_row == row:
            if ignore_internal_walls:
                return True
            return all(
                grid[row][scan_col] != 9
                for scan_col in range(min(seed_col, col), max(seed_col, col) + 1)
            )
        if seed_col == col:
            if ignore_internal_walls:
                return True
            return all(
                grid[scan_row][col] != 9
                for scan_row in range(min(seed_row, row), max(seed_row, row) + 1)
            )
        return False

    return [
        [
            9
            if grid[row][col] == 9
            else 8
            if sum(visible(seed, row, col) for seed in seeds) >= threshold
            else 0
            for col in range(width)
        ]
        for row in range(height)
    ]


def counterexample_grid():
    path = Path(__file__).resolve().parents[1] / "counterexamples" / "internal-wall-shortcut.json"
    return json.loads(path.read_text(encoding="utf-8"))["input"]


def full_divider_only_output(grid):
    height, width = len(grid), len(grid[0])
    blockers = set()
    for col in range(1, width - 1):
        non_walls = [(row, grid[row][col]) for row in range(height) if grid[row][col] != 9]
        if len(non_walls) <= 1 and (not non_walls or non_walls[0][1] not in (0, 8, 9)):
            blockers.update((row, col) for row in range(height) if grid[row][col] == 9)
    for row in range(1, height - 1):
        non_walls = [(col, grid[row][col]) for col in range(width) if grid[row][col] != 9]
        if len(non_walls) <= 1 and (not non_walls or non_walls[0][1] not in (0, 8, 9)):
            blockers.update((row, col) for col in range(width) if grid[row][col] == 9)

    seeds = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, 9)
    ]

    def visible(seed, row, col):
        seed_row, seed_col = seed
        if seed_row == row:
            return not any(
                (row, scan_col) in blockers
                for scan_col in range(min(seed_col, col), max(seed_col, col) + 1)
            )
        if seed_col == col:
            return not any(
                (scan_row, col) in blockers
                for scan_row in range(min(seed_row, row), max(seed_row, row) + 1)
            )
        return False

    return [
        [
            9
            if grid[row][col] == 9
            else 8
            if sum(visible(seed, row, col) for seed in seeds) >= 2
            else 0
            for col in range(width)
        ]
        for row in range(height)
    ]


def partial_counterexample():
    path = Path(__file__).resolve().parents[1] / "counterexamples" / "partial-wall-shortcut.json"
    return json.loads(path.read_text(encoding="utf-8"))


def normalized_rule_hash():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    # Read the program source from the exact ledger row used by canonical_pairs.
    ledger = ROOT / ("data/canonical/puzzles.jsonl" if (ROOT / "data/canonical/puzzles.jsonl").is_file()
                     else "shared/data/canonical/puzzles.jsonl")
    row = next(json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()
               if json.loads(line).get("task_id") == TASK_ID)
    source = row["program_solution"]
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12], pairs


def test_rule_hash_and_python_mirror_match_every_labeled_canonical_pair():
    digest, pairs = normalized_rule_hash()
    assert digest == "071ab7615984"
    assert GEN.RULE_HASH == digest
    assert len(pairs) == 5
    shortcut = GEN.CANONICAL_SHORTCUTS["full_divider_walls_only"]
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert reference_output(pair["input"]) == pair["output"]
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert full_divider_only_output(pair["input"]) == pair["output"]
        assert shortcut(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize("shape", [(9, 11), (10, 12), (11, 13)])
def test_every_exact_override_combination_is_observable_and_semantically_rich(
    difficulty, profile, shape
):
    height, width = shape
    grid = GEN.generate(
        117,
        23,
        difficulty=difficulty,
        grid_h=height,
        grid_w=width,
        scene_profile=profile,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "grid_h": height,
        "grid_w": width,
        "scene_profile": profile,
    }
    intended = reference_output(grid)
    assert GEN.rule_mirror(grid) == intended
    assert intended != reference_output(grid, ignore_internal_walls=True)
    assert any(
        grid[row][col] == 0 and intended[row][col] == 8
        for row in range(height)
        for col in range(width)
    )


def test_default_distribution_always_teaches_the_internal_wall_branch():
    seen_profiles = set()
    inputs = set()
    for band_index, difficulty in enumerate((None, "easy", "medium", "hard")):
        for index in range(64):
            draw_index = band_index * 64 + index
            grid = GEN.generate(4000 + draw_index, draw_index * 11, difficulty=difficulty)
            assert GEN.self_check(grid) == []
            observed = GEN.observe_overrides(grid)
            seen_profiles.add(observed["scene_profile"])
            inputs.add(tuple(map(tuple, grid)))
            assert GEN.SEMANTIC_WITNESSES["wall_blocks_visibility"](grid)
            assert GEN.SEMANTIC_WITNESSES["positive_overlap"](grid)
            assert GEN.SEMANTIC_RIVALS["ignore_internal_walls"](grid) != GEN.rule_mirror(grid)
            if observed["scene_profile"].endswith("_segment"):
                assert GEN.SEMANTIC_WITNESSES["partial_wall_blocks_visibility"](grid)
                assert GEN.CANONICAL_SHORTCUTS["full_divider_walls_only"](grid) != GEN.rule_mirror(grid)
    assert seen_profiles == set(PROFILES)
    assert len(inputs) >= 240


def test_retained_counterexample_refutes_ignore_walls_but_keeps_positive_overlap():
    grid = counterexample_grid()
    intended = reference_output(grid)
    rival = reference_output(grid, ignore_internal_walls=True)
    assert intended != rival
    assert intended[2][2] == 0
    assert rival[2][2] == 8
    assert intended[2][3] == 8
    assert intended[5][2] == 8
    assert GEN.self_check(grid) == []
    assert GEN.rule_mirror(grid) == intended
    assert GEN.SEMANTIC_RIVALS["ignore_internal_walls"](grid) == rival


def test_partial_wall_counterexample_refutes_the_canonical_fitting_shortcut():
    case = partial_counterexample()
    grid = case["input"]
    intended = case["intended_output"]
    rival = case["rival_output"]
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid)
    assert reference_output(grid) == intended
    assert full_divider_only_output(grid) == rival
    assert GEN.rule_mirror(grid) == intended
    assert GEN.CANONICAL_SHORTCUTS["full_divider_walls_only"](grid) == rival
    assert intended != rival


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_alternating_schedule_refutes_shortcut_in_every_three_of_four_window(difficulty):
    for start in range(20):
        lesson = []
        profiles = []
        for offset in range(4):
            index = start + offset
            grid = GEN.generate(7123, index, difficulty=difficulty)
            profiles.append(GEN.observe_overrides(grid)["scene_profile"])
            lesson.append({"input": grid, "output": GEN.rule_mirror(grid)})
        assert sum(profile.endswith("_segment") for profile in profiles) == 2
        for query_index in range(4):
            demos = [pair for index, pair in enumerate(lesson) if index != query_index]
            assert GEN.lesson_identifiable(demos, lesson[query_index]) == []


def test_semantic_contract_is_executable_and_pure():
    full_grid = GEN.generate(931, 17, scene_profile="vertical_gap")
    segment_grid = GEN.generate(932, 18, scene_profile="horizontal_segment")
    originals = [copy.deepcopy(full_grid), copy.deepcopy(segment_grid)]
    assert GEN.WITNESS_RIVALS["wall_blocks_visibility"] == ["ignore_internal_walls"]
    assert GEN.WITNESS_RIVALS["partial_wall_blocks_visibility"] == ["full_divider_walls_only"]
    assert GEN.WITNESS_RIVALS["single_visibility_stays_zero"] == ["one_seed_suffices"]
    assert GEN.LESSON_COMPETITORS["full_divider_walls_only"] is GEN.CANONICAL_SHORTCUTS["full_divider_walls_only"]
    assert GEN.BRANCH_WITNESSES == ("positive_overlap",)
    for grid in (full_grid, segment_grid):
        assert GEN.SEMANTIC_WITNESSES["wall_blocks_visibility"](grid)
        assert GEN.SEMANTIC_WITNESSES["single_visibility_stays_zero"](grid)
        assert GEN.SEMANTIC_WITNESSES["positive_overlap"](grid)
    assert GEN.SEMANTIC_WITNESSES["partial_wall_blocks_visibility"](segment_grid)
    assert not GEN.SEMANTIC_WITNESSES["partial_wall_blocks_visibility"](full_grid)
    for grid, original in zip((full_grid, segment_grid), originals):
        for rival in GEN.SEMANTIC_RIVALS.values():
            rival(grid)
            assert grid == original
    demos = [
        {"input": full_grid, "output": GEN.rule_mirror(full_grid)},
        {"input": segment_grid, "output": GEN.rule_mirror(segment_grid)},
    ]
    assert GEN.lesson_identifiable(demos, demos[0]) == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"grid_h": 8},
        {"grid_h": True},
        {"grid_w": 14},
        {"grid_w": 12.0},
        {"scene_profile": "diagonal"},
        {"scene_profile": 1},
    ],
)
def test_invalid_overrides_fail_closed(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 2, **overrides)


def test_none_override_determinism_fresh_rows_and_global_rng_purity():
    random.seed(991)
    state = random.getstate()
    first = GEN.generate(17, 31, difficulty="hard")
    second = GEN.generate(17, 31, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert GEN.generate(17, 31, grid_h=None) == GEN.generate(17, 31)
    assert random.getstate() == state


@pytest.mark.parametrize("mutation", ["duplicate_color", "marker_color", "remove_two_seeds", "extra_wall"])
def test_self_check_rejects_mutations_that_destroy_the_contract(mutation):
    grid = GEN.generate(77, 8, scene_profile="vertical_solid")
    analysis = GEN._analyze(grid)
    if mutation == "duplicate_color":
        seeds = analysis["seeds"]
        grid[seeds[1][0]][seeds[1][1]] = seeds[0][2]
    elif mutation == "marker_color":
        row, col, _ = analysis["seeds"][0]
        grid[row][col] = 8
    elif mutation == "remove_two_seeds":
        for row, col, _ in analysis["seeds"][:2]:
            grid[row][col] = 0
    elif mutation == "extra_wall":
        grid[1][1] = 9
    assert GEN.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 11 for _ in range(9)]])
def test_malformed_grids_return_diagnostics(grid):
    assert GEN.self_check(grid)


def test_sample_index_must_be_nonnegative_integer():
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, -1)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, True)


def test_observer_rejects_a_broken_generated_divider_profile():
    grid = GEN.generate(77, 8, scene_profile="vertical_solid")
    analysis = GEN._analyze(grid)
    row, col = next(
        (r, c)
        for r, c in analysis["divider_cells"]
        if 0 < r < len(grid) - 1 and 0 < c < len(grid[0]) - 1
    )
    grid[row][col] = 0
    with pytest.raises(ValueError):
        GEN.observe_overrides(grid)
