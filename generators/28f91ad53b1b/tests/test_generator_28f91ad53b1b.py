from __future__ import annotations

import importlib
import importlib.util
import random
from collections import deque
from copy import deepcopy
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK = "28f91ad53b1b"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def independent_rule(grid):
    """Independent per-seed BFS oracle for the selected canonical rule."""
    height, width = len(grid), len(grid[0])
    infinity = height * width + 1
    seeds = [
        (value, row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 5)
    ]

    def distances(start_row, start_col):
        result = [[infinity] * width for _ in range(height)]
        result[start_row][start_col] = 0
        queue = deque([(start_row, start_col)])
        while queue:
            row, col = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = row + dr, col + dc
                if (
                    0 <= nr < height
                    and 0 <= nc < width
                    and grid[nr][nc] != 5
                    and result[nr][nc] == infinity
                ):
                    result[nr][nc] = result[row][col] + 1
                    queue.append((nr, nc))
        return result

    maps = [(color, distances(row, col)) for color, row, col in seeds]
    answer = [row[:] for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 5:
                answer[row][col] = 5
                continue
            candidates = [
                (dist[row][col], color)
                for color, dist in maps
                if dist[row][col] < infinity
            ]
            answer[row][col] = min(candidates)[1] if candidates else 0
    return answer


def nonzero_components(grid):
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    }
    count = 0
    while unseen:
        count += 1
        queue = [unseen.pop()]
        for row, col in queue:
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (row + dr, col + dc)
                if point in unseen:
                    unseen.remove(point)
                    queue.append(point)
    return count


def test_rule_pin_and_independent_solver_match_every_canonical_pair():
    assert GEN.RULE_HASH == "443a7da44ab8"
    pairs = canonical_pairs(TASK, root=find_root(__file__))
    assert len(pairs) == 3
    shortcut = GEN.CANONICAL_SHORTCUTS["row_major_tie_break"]
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert independent_rule(pair["input"]) == pair["output"]
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        # This is the canonical ambiguity the repaired curriculum must refute.
        assert shortcut(deepcopy(pair["input"])) == pair["output"]


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(5))
def test_every_five_example_window_covers_profiles_and_refutes_every_rival(difficulty, start):
    seed = 1701
    grids = [GEN.generate(seed, start + offset, difficulty=difficulty) for offset in range(5)]
    assert {GEN.observe_overrides(grid)["texture"] for grid in grids} == set(
        GEN.SCHEDULE_PROFILES
    )

    outputs = [GEN.rule_mirror(grid) for grid in grids]
    for grid, output in zip(grids, outputs):
        assert GEN.self_check(grid, difficulty=difficulty) == []
        assert GEN.strict_canonical_like(grid) == []
        assert output == independent_rule(grid)
        # Canonical inputs form one connected non-background object: the wall
        # frame touches every seed. Keep the generated morphology anchored too.
        assert nonzero_components(grid) == 1

    for name, rival in GEN.LESSON_COMPETITORS.items():
        assert any(rival(deepcopy(grid)) != output for grid, output in zip(grids, outputs)), name

    query_grid = GEN.generate(seed, start + 5, difficulty=difficulty)
    demos = [
        {"input": grid, "output": output}
        for grid, output in zip(grids, outputs)
    ]
    query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
    assert GEN.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(5))
def test_every_six_pair_query_rotation_remains_identifiable(difficulty, start):
    seed = 1701
    pairs = []
    for offset in range(6):
        grid = GEN.generate(seed, start + offset, difficulty=difficulty)
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})

    for query_index, query in enumerate(pairs):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert GEN.lesson_identifiable(demos, query) == [], (
            difficulty,
            start,
            query_index,
            GEN.observe_overrides(query["input"])["texture"],
            GEN.lesson_identifiable(demos, query),
        )


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_override_boundary_is_exact_observable_and_band_safe(difficulty):
    case_index = 0
    for grid_h in (8, 10):
        for grid_w in (10, 12):
            for n_seeds in (2, 5):
                for texture in GEN.SCHEDULE_PROFILES:
                    requested = {
                        "grid_h": grid_h,
                        "grid_w": grid_w,
                        "n_seeds": n_seeds,
                        "texture": texture,
                    }
                    grid = GEN.generate(
                        9000 + case_index,
                        case_index % 17,
                        difficulty=difficulty,
                        **requested,
                    )
                    assert GEN.observe_overrides(grid) == requested
                    assert GEN.self_check(grid, difficulty=difficulty) == []
                    assert GEN.rule_mirror(grid) == independent_rule(grid)
                    assert nonzero_components(grid) == 1
                    case_index += 1


def test_unknown_and_invalid_controls_fail_loudly():
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        GEN.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty="expert")
    with pytest.raises(ValueError, match="grid_h"):
        GEN.generate(1, 0, grid_h="8")
    with pytest.raises(ValueError, match="texture"):
        GEN.generate(1, 0, texture=3)


def test_tie_order_is_an_exact_counterexample_to_the_canonical_shortcut():
    grid = GEN.generate(
        314159,
        7,
        difficulty="medium",
        grid_h=8,
        grid_w=10,
        n_seeds=2,
        texture="tie_order",
    )
    expected = GEN.rule_mirror(grid)
    shortcut = GEN.CANONICAL_SHORTCUTS["row_major_tie_break"](deepcopy(grid))
    assert expected != shortcut
    differences = [
        (row, col, expected[row][col], shortcut[row][col])
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if expected[row][col] != shortcut[row][col]
    ]
    assert differences
    assert all(winner < shortcut_winner for _, _, winner, shortcut_winner in differences)
    assert GEN.SEMANTIC_WITNESSES["smaller_color_wins_finite_ties"](grid)


@pytest.mark.parametrize(
    ("difficulty", "seed", "sample_index"),
    [
        ("medium", 3736177407, 16),
        ("hard", 3668402686, 7),
    ],
)
def test_seedless_profile_is_a_rotation_backup_for_wall_distance(
    difficulty, seed, sample_index
):
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    assert GEN.observe_overrides(grid)["texture"] == "seedless_rooms"
    assert GEN.SEMANTIC_WITNESSES["wall_aware_distance"](grid)


@pytest.mark.parametrize(
    ("texture", "witness", "rival"),
    [
        ("wall_detour", "wall_aware_distance", "component_manhattan"),
        ("tie_order", "smaller_color_wins_finite_ties", "row_major_tie_break"),
        ("seedless_rooms", "seedless_components_stay_zero", "global_manhattan"),
        ("mixed_rooms", "all_seed_colors_compete", "first_two_seeds_only"),
    ],
)
def test_named_profile_reproducers_catch_targeted_shortcuts(texture, witness, rival):
    grid = GEN.generate(
        271828,
        11,
        difficulty="hard",
        grid_h=10,
        grid_w=12,
        n_seeds=5,
        texture=texture,
    )
    assert GEN.SEMANTIC_WITNESSES[witness](grid)
    assert GEN.SEMANTIC_RIVALS[rival](deepcopy(grid)) != GEN.rule_mirror(grid)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_schedule_hits_a_canonical_profile_in_every_band(difficulty):
    canonical = canonical_pairs(TASK, root=find_root(__file__))
    profiles = {
        (len(pair["input"]), len(pair["input"][0]), len({v for row in pair["input"] for v in row}))
        for pair in canonical
    }
    draws = [GEN.generate(500 + i, i, difficulty=difficulty) for i in range(20)]
    generated = {
        (len(grid), len(grid[0]), len({v for row in grid for v in row}))
        for grid in draws
    }
    assert generated & profiles
    assert all(8 <= len(grid) <= 10 and 10 <= len(grid[0]) <= 12 for grid in draws)


def test_replay_is_fresh_deterministic_global_rng_pure_and_input_pure():
    random.seed(0x28F91)
    state = random.getstate()
    first = GEN.generate(123, 19, difficulty="hard", texture="mixed_rooms")
    assert random.getstate() == state
    second = GEN.generate(123, 19, difficulty="hard", texture="mixed_rooms")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))

    pristine = deepcopy(first)
    assert GEN.rule_mirror(first) == independent_rule(first)
    assert first == pristine

    first[2][2] = 9
    assert GEN.generate(123, 19, difficulty="hard", texture="mixed_rooms") == second


def test_default_distribution_varies_without_leaving_task_grammar():
    grids = [
        GEN.generate(seed, seed * 7 + 3, difficulty=("easy", "medium", "hard")[seed % 3])
        for seed in range(120)
    ]
    assert all(GEN.self_check(grid) == [] for grid in grids)
    assert len({frozen(grid) for grid in grids}) >= 105
    assert len({frozen(GEN.rule_mirror(grid)) for grid in grids}) >= 100
    assert {GEN.observe_overrides(grid)["texture"] for grid in grids} == set(
        GEN.SCHEDULE_PROFILES
    )


def test_self_check_rejects_rule_hiding_mutations():
    base = GEN.generate(44, 2, difficulty="medium", texture="mixed_rooms")

    ragged = deepcopy(base)
    ragged[-1].pop()

    invalid_color = deepcopy(base)
    invalid_color[2][2] = 10

    duplicate_seed_color = deepcopy(base)
    seed_cells = [
        (row, col)
        for row, values in enumerate(duplicate_seed_color)
        for col, value in enumerate(values)
        if value not in (0, 5)
    ]
    duplicate_seed_color[seed_cells[-1][0]][seed_cells[-1][1]] = duplicate_seed_color[seed_cells[0][0]][seed_cells[0][1]]

    broken_outer_border = deepcopy(base)
    broken_outer_border[0][1] = 5

    broken_inner_frame = deepcopy(base)
    broken_inner_frame[1][2] = 0

    too_small = [row[:9] for row in base[:7]]

    for name, grid in {
        "ragged": ragged,
        "invalid_color": invalid_color,
        "duplicate_seed_color": duplicate_seed_color,
        "broken_outer_border": broken_outer_border,
        "broken_inner_frame": broken_inner_frame,
        "too_small": too_small,
    }.items():
        assert GEN.self_check(grid), name


def test_workspace_reference_probe_replays_the_declared_contract_without_racket():
    path = (
        Path(find_root(__file__))
        / "generators"
        / TASK
        / "workspace"
        / "reference_probe.py"
    )
    spec = importlib.util.spec_from_file_location("task_reference_probe", path)
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    report = probe.audit(GEN, seeds_per_band=2, use_racket=False)
    assert report["passed"]
    assert report["canonical"]["independent_matches"] == 3
    assert report["rotation_probe"]["ambiguous"] == 0
    assert report["overrides"]["errors"] == []
