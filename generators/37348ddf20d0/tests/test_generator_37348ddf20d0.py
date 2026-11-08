from __future__ import annotations

import importlib
import random
from copy import deepcopy

import pytest

from scripts.canonical_profile_gate import canonical_pairs

TASK = "37348ddf20d0"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def independent_rule(grid):
    """Independent multi-source BFS reference for the canonical rule."""
    height, width = len(grid), len(grid[0])
    inf = height * width + 1

    def distances(color):
        out = [[inf] * width for _ in range(height)]
        queue = []
        for row in range(height):
            for col in range(width):
                if grid[row][col] == color:
                    out[row][col] = 0
                    queue.append((row, col))
        head = 0
        while head < len(queue):
            row, col = queue[head]
            head += 1
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = row + dr, col + dc
                if (
                    0 <= nr < height
                    and 0 <= nc < width
                    and grid[nr][nc] != 5
                    and out[nr][nc] == inf
                ):
                    out[nr][nc] = out[row][col] + 1
                    queue.append((nr, nc))
        return out

    red = distances(2)
    green = distances(3)
    answer = [row[:] for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0:
                continue
            if red[row][col] < green[row][col]:
                answer[row][col] = 2
            elif green[row][col] < red[row][col]:
                answer[row][col] = 3
    return answer


def test_rule_pin_and_independent_solver_match_every_canonical_pair():
    assert GEN.RULE_HASH == "6d8410c29906"
    pairs = canonical_pairs(TASK)
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert independent_rule(pair["input"]) == pair["output"]
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_five_profile_lesson_covers_every_semantic_witness_and_refutes_rivals(difficulty):
    grids = [GEN.generate(1701, index, difficulty=difficulty) for index in range(5)]
    profiles = [GEN.schedule_profile(1701, index, difficulty) for index in range(5)]
    assert set(profiles) == set(GEN.SCHEDULE_PROFILES)
    assert {GEN.observe_overrides(grid)["texture"] for grid in grids} == set(
        GEN.SCHEDULE_PROFILES
    )

    for grid in grids:
        assert GEN.self_check(grid, difficulty=difficulty) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN.rule_mirror(grid) == independent_rule(grid)

    for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
        witness_grid = next(grid for grid in grids if witness(grid))
        expected = GEN.rule_mirror(witness_grid)
        assert any(
            GEN.SEMANTIC_RIVALS[rival](deepcopy(witness_grid)) != expected
            for rival in GEN.WITNESS_RIVALS[witness_name]
        )

    query_grid = GEN.generate(1701, 5, difficulty=difficulty)
    demos = [{"input": grid, "output": GEN.rule_mirror(grid)} for grid in grids]
    query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
    assert GEN.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_override_boundary_is_exact_observable_and_band_safe(difficulty):
    case_index = 0
    for grid_h in (11, 13):
        for grid_w in (11, 13):
            for n_red in (1, 4):
                for n_green in (1, 4):
                    for texture in GEN.SCHEDULE_PROFILES:
                        requested = {
                            "grid_h": grid_h,
                            "grid_w": grid_w,
                            "n_red": n_red,
                            "n_green": n_green,
                            "texture": texture,
                        }
                        grid = GEN.generate(
                            9000 + case_index,
                            case_index % 17,
                            difficulty=difficulty,
                            **requested,
                        )
                        assert GEN.observe_overrides(grid) == requested
                        assert GEN.self_check(
                            grid, difficulty=difficulty, meta={"overrides": requested}
                        ) == []
                        assert GEN.rule_mirror(grid) == independent_rule(grid)
                        case_index += 1


def test_unknown_and_invalid_controls_fail_loudly():
    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty="expert")


@pytest.mark.parametrize(
    ("texture", "witness", "rival"),
    [
        ("wall_detour", "wall_aware_detour", "ignore_walls_manhattan"),
        ("tie_rooms", "finite_ties_remain_black", "break_ties_toward_red"),
        (
            "seedless_rooms",
            "seedless_chamber_remains_black",
            "ignore_walls_manhattan",
        ),
        (
            "open_voronoi",
            "nearest_of_multiple_same_color",
            "first_seed_each_color",
        ),
    ],
)
def test_named_profile_reproducers_catch_the_targeted_shortcut(texture, witness, rival):
    grid = GEN.generate(
        314159,
        7,
        difficulty="medium",
        grid_h=12,
        grid_w=12,
        n_red=3,
        n_green=3,
        texture=texture,
    )
    assert GEN.SEMANTIC_WITNESSES[witness](grid)
    assert GEN.SEMANTIC_RIVALS[rival](deepcopy(grid)) != GEN.rule_mirror(grid)


def test_replay_is_fresh_deterministic_global_rng_pure_and_input_pure():
    random.seed(0x37348)
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

    first[1][1] = 9
    assert GEN.generate(123, 19, difficulty="hard", texture="mixed_rooms") == second


def test_default_schedule_stays_inside_the_canonical_profile_envelope_and_varies():
    grids = [
        GEN.generate(seed, seed * 7 + 3, difficulty=("easy", "medium", "hard")[seed % 3])
        for seed in range(120)
    ]
    observations = [GEN.observe_overrides(grid) for grid in grids]
    assert all(11 <= item["grid_h"] <= 13 for item in observations)
    assert all(11 <= item["grid_w"] <= 13 for item in observations)
    assert {item["texture"] for item in observations} == set(GEN.SCHEDULE_PROFILES)
    assert len({frozen(grid) for grid in grids}) >= 115
    assert len({frozen(GEN.rule_mirror(grid)) for grid in grids}) >= 110


def test_self_check_rejects_rule_hiding_mutations():
    base = GEN.generate(44, 2, difficulty="medium", texture="mixed_rooms")

    ragged = deepcopy(base)
    ragged[-1].pop()

    invalid_color = deepcopy(base)
    invalid_color[1][1] = 9

    missing_red = [[0 if value == 2 else value for value in row] for row in base]

    broken_border = deepcopy(base)
    broken_border[0][1] = 0

    too_small = [row[:10] for row in base[:10]]

    for name, grid in {
        "ragged": ragged,
        "invalid_color": invalid_color,
        "missing_red": missing_red,
        "broken_border": broken_border,
        "too_small": too_small,
    }.items():
        assert GEN.self_check(grid), name
