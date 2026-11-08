from __future__ import annotations

import copy
import importlib.util
import random
from pathlib import Path

import pytest

from scripts.canonical_profile_gate import canonical_pairs


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "2e5c98d98eed"
GENERATOR_PATH = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"test_generator_{TASK_ID}", GENERATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def test_canonical_inputs_are_accepted_and_python_oracle_matches_outputs():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN._fill_interior(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_generation_is_deterministic_fresh_and_rng_pure(difficulty):
    random.seed(918273)
    state = random.getstate()
    first = GEN.generate(41, 17, difficulty=difficulty)
    assert random.getstate() == state
    second = GEN.generate(41, 17, difficulty=difficulty)
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert second[0][0] == 0


@pytest.mark.parametrize("profile", GEN.SCHEDULE_PROFILES)
def test_scene_profile_override_is_exact(profile):
    grid = GEN.generate(3, 5, difficulty="hard", scene_profile=profile)
    assert GEN.observe_overrides(grid)["scene_profile"] == profile


@pytest.mark.parametrize("color", [1, 2, 3, 4, 5, 6, 7, 9])
def test_seed_color_override_is_exact(color):
    grid = GEN.generate(5, 2, seed_color=color)
    assert GEN.observe_overrides(grid)["seed_color"] == color


@pytest.mark.parametrize("position", GEN._SEED_POSITIONS)
def test_seed_position_override_is_exact(position):
    grid = GEN.generate(7, 4, seed_position=position)
    assert GEN.observe_overrides(grid)["seed_position"] == position


def test_unknown_override_rejects_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, typo_axis="oops")


def test_self_check_rejects_targeted_structural_impostors():
    base = GEN.generate(11, 0, scene_profile="canonical_8x9_5x5")
    facts = GEN._analysis(base)
    r0, c0, r1, c1 = facts["bbox"]
    sr, sc, _ = facts["seed"]

    broken = copy.deepcopy(base)
    broken[r0][c0 + 1] = 0
    assert any("missing perimeter" in error for error in GEN.self_check(broken))

    second_seed = copy.deepcopy(base)
    extra_cell = next(
        cell
        for cell in ((r0 + 1, c0 + 1), (r1 - 1, c1 - 1), (r0 + 1, c1 - 1), (r1 - 1, c0 + 1))
        if cell != (sr, sc)
    )
    second_seed[extra_cell[0]][extra_cell[1]] = 6 if facts["seed_color"] != 6 else 7
    assert any("exactly one" in error for error in GEN.self_check(second_seed))

    seed_outside = copy.deepcopy(base)
    seed_outside[sr][sc] = 0
    seed_outside[0][0] = facts["seed_color"]
    assert any("strict frame interior" in error for error in GEN.self_check(seed_outside))

    extra_eight = copy.deepcopy(base)
    extra_eight[r0 + 1][c0 + 1] = 8
    assert any("outside the rectangle perimeter" in error for error in GEN.self_check(extra_eight))

    no_seed = copy.deepcopy(base)
    no_seed[sr][sc] = 0
    assert any("exactly one" in error for error in GEN.self_check(no_seed))


def test_every_three_demo_window_has_rule_discriminators():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(len(GEN.SCHEDULE_PROFILES)):
            grids = [GEN.generate(13, start + offset, difficulty=difficulty) for offset in range(3)]
            facts = [GEN._analysis(grid) for grid in grids]
            assert len({row["seed_color"] for row in facts}) >= 2
            assert len({row["seed_position"] for row in facts}) >= 2
            assert len({(row["frame_h"], row["frame_w"]) for row in facts}) >= 2
            demos = [{"input": grid, "output": GEN._fill_interior(grid)} for grid in grids]
            query_grid = GEN.generate(13, start + 3, difficulty=difficulty)
            query = {"input": query_grid, "output": GEN._fill_interior(query_grid)}
            assert GEN.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_off_diagonal_default_schedule_covers_every_axis_value(difficulty):
    observations = [
        GEN.observe_overrides(GEN.generate(seed, seed + 7919, difficulty=difficulty))
        for seed in range(64)
    ]
    assert {row["scene_profile"] for row in observations} == set(GEN.SCHEDULE_PROFILES)
    assert {row["seed_color"] for row in observations} == set(GEN._SEED_COLORS)
    assert {row["seed_position"] for row in observations} == set(GEN._SEED_POSITIONS)
