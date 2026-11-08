"""Task-local regression and semantic-contract tests for 156bae9e7b79."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "156bae9e7b79"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
_SPEC = importlib.util.spec_from_file_location(f"review_generator_{TASK_ID}", GENERATOR_PATH)
assert _SPEC and _SPEC.loader
GEN = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(GEN)

CANONICAL_PROFILES = {(9, 9, 6), (11, 11, 8), (13, 13, 9)}
EXPECTED_AXES = {"grid_h", "grid_w", "n_colors", "line_position", "line_end"}


def _pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _profile(grid):
    return len(grid), len(grid[0]), len({cell for row in grid for cell in row})


def _labeled(seed: int, sample_index: int, difficulty: str = "medium"):
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_rule_pin_and_python_mirror_match_every_canonical_pair():
    assert GEN.RULE_HASH == "01a0d2007d61"
    for pair in _pairs():
        assert GEN.rule_mirror(deepcopy(pair["input"])) == pair["output"]


def test_generator_owns_every_canonical_input():
    for pair in _pairs():
        assert GEN.self_check(deepcopy(pair["input"])) == []
        assert GEN.strict_canonical_like(deepcopy(pair["input"])) == []
        observed = GEN.observe_overrides(pair["input"])
        assert set(observed) == EXPECTED_AXES
        assert (observed["grid_h"], observed["grid_w"], observed["n_colors"]) in CANONICAL_PROFILES
        assert observed["line_position"] == "center"
        assert observed["line_end"] == "bottom"


def test_declared_control_surface_is_small_exact_and_fully_observable():
    assert set(GEN.AXES) == EXPECTED_AXES
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.MIN_STRICT_FRAC == pytest.approx(0.25)
    assert tuple(GEN.SCHEDULE_PROFILES) == (
        "canonical_core",
        "left_truncated",
        "right_truncated",
    )


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_advertised_override_combination_is_constructive_and_observable(difficulty):
    dimensions = ((9, 9), (9, 15), (12, 13), (15, 9), (15, 15))
    case = 0
    for grid_h, grid_w in dimensions:
        for n_colors in range(6, 10):
            for line_position in ("center", "left", "right"):
                for line_end in ("bottom", "truncated"):
                    requested = {
                        "grid_h": grid_h,
                        "grid_w": grid_w,
                        "n_colors": n_colors,
                        "line_position": line_position,
                        "line_end": line_end,
                    }
                    grid = GEN.generate(
                        70_000 + case,
                        case,
                        difficulty=difficulty,
                        **requested,
                    )
                    assert GEN.self_check(grid) == [], (difficulty, requested, GEN.self_check(grid))
                    assert GEN.observe_overrides(grid) == requested
                    assert GEN.rule_mirror(grid) != grid
                    case += 1


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"grid_h": 8},
        {"grid_h": 16},
        {"grid_w": 8},
        {"grid_w": 16},
        {"n_colors": 5},
        {"n_colors": 10},
        {"line_position": "spread"},
        {"line_end": "middle"},
        {"grid_h": True},
        {"grid_w": 9.5},
        {"n_colors": "8"},
    ],
)
def test_unknown_or_invalid_controls_fail_loudly(overrides):
    with pytest.raises((KeyError, TypeError, ValueError)):
        GEN.generate(1, 2, **overrides)


@pytest.mark.parametrize(
    ("argument", "value"),
    [
        ("seed", True),
        ("seed", 1.0),
        ("seed", "1"),
        ("sample_index", True),
        ("sample_index", 1.0),
        ("sample_index", "1"),
        ("sample_index", -1),
        ("difficulty", True),
        ("difficulty", 0),
        ("difficulty", 1.0),
        ("difficulty", "__invalid_difficulty__"),
    ],
)
def test_generate_rejects_invalid_scalar_call_arguments(argument, value):
    arguments = {"seed": 17, "sample_index": 2, "difficulty": "medium"}
    arguments[argument] = value
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(
            arguments["seed"],
            arguments["sample_index"],
            difficulty=arguments["difficulty"],
        )


@pytest.mark.parametrize(
    ("sample_index", "difficulty"),
    [
        (True, "medium"),
        (1.0, "medium"),
        ("1", "medium"),
        (-1, "medium"),
        (1, True),
        (1, 0),
        (1, 1.0),
        (1, "__invalid_difficulty__"),
    ],
)
def test_schedule_profile_rejects_invalid_scalar_call_arguments(sample_index, difficulty):
    with pytest.raises((TypeError, ValueError)):
        GEN.schedule_profile(17, sample_index, difficulty)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_schedule_has_canonical_support_and_short_lesson_discriminators(difficulty):
    grids = [GEN.generate(8_100, index, difficulty=difficulty) for index in range(15)]
    assert any(_profile(grid) in CANONICAL_PROFILES for grid in grids)
    assert all(GEN.self_check(grid) == [] for grid in grids)
    for start in range(13):
        window = grids[start : start + 3]
        profiles = [GEN.schedule_profile(8_100, start + offset, difficulty) for offset in range(3)]
        assert set(profiles) == set(GEN.SCHEDULE_PROFILES)
        assert any(GEN.SEMANTIC_WITNESSES["off_center_line"](grid) for grid in window)
        assert any(GEN.SEMANTIC_WITNESSES["truncated_line"](grid) for grid in window)
        assert any(GEN.strict_canonical_like(grid) == [] for grid in window)


def test_canonical_shortcuts_fit_all_published_pairs():
    assert set(GEN.CANONICAL_SHORTCUTS) == {"fixed_grid_center", "extends_to_bottom"}
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(deepcopy(pair["input"])) == pair["output"] for pair in _pairs()), name


def test_explicit_counterexample_disagrees_with_each_named_rival():
    grid = GEN.generate(
        44,
        5,
        grid_h=12,
        grid_w=13,
        n_colors=9,
        line_position="left",
        line_end="truncated",
    )
    truth = GEN.rule_mirror(grid)
    assert GEN.SEMANTIC_WITNESSES["off_center_line"](grid)
    assert GEN.SEMANTIC_WITNESSES["truncated_line"](grid)
    assert GEN.SEMANTIC_RIVALS["fixed_grid_center"](deepcopy(grid)) != truth
    assert GEN.SEMANTIC_RIVALS["extends_to_bottom"](deepcopy(grid)) != truth


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_four_sample_rotation_remains_identifiable(difficulty):
    for start in range(12):
        pairs = [_labeled(23_000 + start, start + offset, difficulty) for offset in range(4)]
        for query_index in range(4):
            query = pairs[query_index]
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(deepcopy(demos), deepcopy(query)) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert not all(
                    rival(deepcopy(pair["input"])) == pair["output"] for pair in demos
                ), (difficulty, start, query_index, name)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_distribution_is_deterministic_valid_and_noncollapsed(difficulty):
    grids = [GEN.generate(90_000 + index, index, difficulty=difficulty) for index in range(60)]
    assert all(grid == GEN.generate(90_000 + index, index, difficulty=difficulty)
               for index, grid in enumerate(grids))
    assert all(GEN.self_check(grid) == [] for grid in grids)
    assert all(GEN.rule_mirror(grid) != grid for grid in grids)
    assert len({json.dumps(grid, separators=(",", ":")) for grid in grids}) >= 55
    assert sum(GEN.strict_canonical_like(grid) == [] for grid in grids) >= 15


def test_validator_rejects_structural_mutations_without_mutating_inputs():
    original = GEN.generate(711, 0, difficulty="medium")
    before = deepcopy(original)
    assert GEN.self_check(original) == []
    assert original == before

    observed = GEN.observe_overrides(original)
    line_col = {
        "left": len(original[0]) // 3,
        "center": len(original[0]) // 2,
        "right": len(original[0]) - 1 - len(original[0]) // 3,
    }[observed["line_position"]]
    line_rows = [r for r in range(1, len(original)) if original[r][line_col] == 8]

    mutations = []
    bad_key_anchor = deepcopy(original)
    bad_key_anchor[0][line_col] = 2
    mutations.append(bad_key_anchor)

    stray_color = deepcopy(original)
    stray_color[1][0] = 3
    mutations.append(stray_color)

    broken_line = deepcopy(original)
    broken_line[line_rows[len(line_rows) // 2]][line_col] = 5
    mutations.append(broken_line)

    second_line = deepcopy(original)
    second_col = 1 if line_col != 1 else len(original[0]) - 2
    second_line[line_rows[0]][second_col] = 8
    second_line[line_rows[1]][second_col] = 8
    mutations.append(second_line)

    for grid in mutations:
        assert GEN.self_check(grid), grid
