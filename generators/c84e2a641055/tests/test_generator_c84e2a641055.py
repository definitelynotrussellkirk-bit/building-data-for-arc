"""Regression tests for the whole-object gravity generator repair."""
from __future__ import annotations

import copy
import importlib.util
import itertools
import random
import sys
from pathlib import Path

import pytest

TASK_DIR = Path(__file__).resolve().parents[1]
REPO = TASK_DIR.parents[1]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs as read_canonical_pairs, find_root

CANONICAL_ROOT = find_root(__file__)


def load_generator():
    path = TASK_DIR / "generator.py"
    spec = importlib.util.spec_from_file_location("generator_c84e2a641055", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


GEN = load_generator()


def canonical_pairs():
    return read_canonical_pairs(GEN.TASK_ID, root=CANONICAL_ROOT, labeled_only=True)


def lesson(seed: int, start: int, difficulty: str):
    pairs = []
    for offset in range(GEN.EXAMPLES_NEEDED + 1):
        grid = GEN.generate(seed, start + offset, difficulty=difficulty)
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
    return pairs


def test_rule_hash_and_every_canonical_pair_are_exact():
    assert GEN.RULE_HASH == "b08466eb063e"
    for pair in canonical_pairs():
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_every_declared_override_is_exact_observable_and_composable():
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    core_cases = itertools.product(
        range(4, 9),
        (1, 2),
        range(1, 5),
        ("flat", "uneven"),
    )
    for difficulty in ("easy", "medium", "hard"):
        for index, (n_cells, n_colors, drop_distance, bottom_profile) in enumerate(core_cases):
            requested = {
                "grid_h": 7,
                "grid_w": 7,
                "n_cells": n_cells,
                "n_colors": n_colors,
                "drop_distance": drop_distance,
                "bottom_profile": bottom_profile,
            }
            grid = GEN.generate(1000 + index, index, difficulty=difficulty, **requested)
            assert GEN.self_check(grid, difficulty=difficulty) == []
            assert GEN.observe_overrides(grid) == requested
        # itertools.product was consumed; rebuild it for the next band.
        core_cases = itertools.product(range(4, 9), (1, 2), range(1, 5), ("flat", "uneven"))

    boundary_cases = (
        {"grid_h": 7, "grid_w": 11, "n_cells": 8, "n_colors": 2,
         "drop_distance": 4, "bottom_profile": "flat"},
        {"grid_h": 11, "grid_w": 7, "n_cells": 4, "n_colors": 1,
         "drop_distance": 1, "bottom_profile": "uneven"},
        {"grid_h": 11, "grid_w": 11, "n_cells": 8, "n_colors": 2,
         "drop_distance": 1, "bottom_profile": "uneven"},
    )
    for index, requested in enumerate(boundary_cases):
        grid = GEN.generate(2000 + index, index, difficulty="hard", **requested)
        assert GEN.observe_overrides(grid) == requested

    with pytest.raises((TypeError, ValueError), match="integer"):
        GEN.generate(1, 0, grid_h=True)
    with pytest.raises((TypeError, ValueError), match="integer"):
        GEN.generate(1, 0, n_cells=4.5)
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty="impossible")


def test_default_schedule_spans_axes_and_keeps_canonical_support_in_every_band():
    expected_profiles = set(GEN.SCHEDULE_PROFILES)
    for difficulty in ("easy", "medium", "hard"):
        observed = []
        strict = 0
        for sample_index in range(16):
            grid = GEN.generate(3000, sample_index, difficulty=difficulty)
            assert GEN.self_check(grid, difficulty=difficulty) == []
            axes = GEN.observe_overrides(grid)
            observed.append(axes)
            strict += not GEN.strict_canonical_like(grid)
        assert {GEN.schedule_profile(3000, i, difficulty) for i in range(4)} == expected_profiles
        assert {row["grid_h"] for row in observed} == set(range(7, 12))
        assert {row["grid_w"] for row in observed} == set(range(7, 12))
        assert {row["n_cells"] for row in observed} == set(range(4, 9))
        assert {row["n_colors"] for row in observed} == {1, 2}
        assert {row["drop_distance"] for row in observed} == {1, 2, 3, 4}
        assert {row["bottom_profile"] for row in observed} == {"flat", "uneven"}
        assert strict >= 8


def test_all_five_pair_query_rotations_are_identifiable():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = lesson(4000 + start, start, difficulty)
            for query_index in range(len(pairs)):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                query = pairs[query_index]
                assert GEN.lesson_identifiable(demos, query) == [], (
                    difficulty, start, query_index
                )
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(
                        rival(demo["input"]) != demo["output"] for demo in demos
                    ), (difficulty, start, query_index, name)


def test_canonical_shortcuts_fit_public_pairs_and_generated_lessons_refute_them():
    public = canonical_pairs()
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in public), name
        generated = [GEN.generate(5000, index, difficulty="medium") for index in range(4)]
        assert any(shortcut(grid) != GEN.rule_mirror(grid) for grid in generated), name


def test_multicolor_counterexample_separates_whole_object_from_per_color_gravity():
    grid = GEN.generate(
        6000,
        2,
        difficulty="medium",
        grid_h=7,
        grid_w=7,
        n_cells=6,
        n_colors=2,
        drop_distance=4,
        bottom_profile="flat",
    )
    assert GEN.observe_overrides(grid)["n_colors"] == 2
    assert GEN.CANONICAL_SHORTCUTS["per_color_gravity"](grid) != GEN.rule_mirror(grid)


def test_self_check_rejects_minimal_impostors_and_malformed_grids():
    singleton = [[0] * 7 for _ in range(7)]
    singleton[2][2] = 4
    assert GEN.self_check(singleton)

    short_line = [[0] * 7 for _ in range(7)]
    for column in range(2, 5):
        short_line[2][column] = 4
    assert GEN.self_check(short_line)

    solid_2x2 = [[0] * 7 for _ in range(7)]
    for row in (1, 2):
        for column in (2, 3):
            solid_2x2[row][column] = 4
    assert GEN.self_check(solid_2x2)

    disconnected = [[0] * 7 for _ in range(7)]
    disconnected[1][1] = 3
    disconnected[3][3] = 3
    assert GEN.self_check(disconnected)

    assert GEN.self_check([])
    assert GEN.self_check([[0] * 7, [0] * 6])
    boolean_cell = [[0] * 7 for _ in range(7)]
    boolean_cell[0][0] = True
    assert GEN.self_check(boolean_cell)


def test_rule_mirror_is_fresh_and_generator_is_replay_pure():
    random.seed(24680)
    before = random.getstate()
    first = GEN.generate(44, 7, difficulty="hard")
    other = GEN.generate(45, 8, difficulty="easy")
    second = GEN.generate(44, 7, difficulty="hard")
    after = random.getstate()
    assert before == after
    assert first == second
    assert first is not second and first[0] is not second[0]
    mirrored = GEN.rule_mirror(first)
    assert mirrored is not first and mirrored[0] is not first[0]
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second
    assert second != other


def test_difficulty_band_changes_keyed_nuisance_geometry():
    """The public difficulty knob must not be a dead, byte-identical argument."""
    for sample_index in range(16):
        grids = [
            GEN.generate(7100, sample_index, difficulty=band)
            for band in ("easy", "medium", "hard")
        ]
        frozen = {
            tuple(tuple(row) for row in grid)
            for grid in grids
        }
        assert len(frozen) == 3, sample_index
        assert len({tuple(GEN.observe_overrides(grid).items()) for grid in grids}) == 1


def test_workspace_review_probe_finds_exact_shortcut_witnesses():
    path = TASK_DIR / "workspace" / "review_probe.py"
    assert path.is_file(), "review_probe.py should be retained for future reviewers"
    spec = importlib.util.spec_from_file_location("review_probe_c84e2a641055", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    report = module.build_report(seed=7300, starts=8)
    assert report["canonical_pair_count"] == 5
    assert report["rotation_failures"] == []
    for name, result in report["canonical_shortcuts"].items():
        assert result["fits_all_canonical"], name
        assert result["counterexample"] is not None, name
        assert result["counterexample"]["intended_output"] != result["counterexample"]["rival_output"]


def test_scheduled_multicolor_profiles_do_not_encode_pure_vertical_color_layers():
    """The floor color must also occur above the floor-facing row."""
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in (2, 3, 6, 7):
            grid = GEN.generate(7400, sample_index, difficulty=difficulty)
            observed = GEN.observe_overrides(grid)
            if observed["n_colors"] != 2:
                continue
            cells = [
                (row, column, value)
                for row, values in enumerate(grid)
                for column, value in enumerate(values)
                if value != 0
            ]
            bottom = max(row for row, _column, _value in cells)
            bottom_colors = {value for row, _column, value in cells if row == bottom}
            assert len(bottom_colors) == 1
            floor_color = next(iter(bottom_colors))
            assert any(row < bottom and value == floor_color for row, _column, value in cells)
            assert any(row < bottom and value != floor_color for row, _column, value in cells)
