"""Observable generator contracts, portable across library and staged layouts."""
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root


TASK_ID = "646eeb47599b"
ROOT = find_root(__file__)
SOURCE = next(path for path in (
    ROOT / "generators" / TASK_ID / "generator.py",
    ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
) if path.is_file())
SPEC = importlib.util.spec_from_file_location("laser_generator_contract", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def wall_count(grid):
    return sum(cell == 8 for row in grid for cell in row)


@pytest.mark.parametrize("band,seed,count", [
    ("easy", 11, 4), ("medium", 38, 6), ("hard", 28, 9),
])
def test_requested_wall_count_survives_open_path_handling(band, seed, count):
    grid = GEN.generate(seed, 0, difficulty=band, n_walls=count)
    assert wall_count(grid) == count


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("h,w,count", [(5, 8, 4), (8, 5, 14)])
@pytest.mark.parametrize("orientation", ["horizontal", "vertical"])
def test_exact_controls_override_difficulty_preferences(band, h, w, count, orientation):
    grid = GEN.generate(41, 2, difficulty=band, grid_h=h, grid_w=w,
                        n_walls=count, orientation=orientation)
    assert len(grid) == h and len(grid[0]) == w
    assert wall_count(grid) == count
    seeds = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3]
    assert len(seeds) == 2
    assert (seeds[0][0] == seeds[1][0]) == (orientation == "horizontal")
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("value", [True, False, 1.0, "1", -1])
def test_sample_index_requires_a_nonnegative_integer(value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, value)


@pytest.mark.parametrize("axis,value", [
    ("grid_h", 5.9), ("grid_w", "6"), ("n_walls", 7.9),
    ("grid_h", True), ("n_walls", "8"),
])
def test_exact_integer_axes_reject_coercion(axis, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **{axis: value})


@pytest.mark.parametrize("axis,value", [
    ("typo_axis", 1), ("texture", "warm"), ("palette_kind", "cool"),
])
def test_unsupported_controls_are_not_silently_ignored(axis, value):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **{axis: value})


def test_an_immediately_blocked_seed_can_split_before_moving():
    # Racket independently confirms this grows vertical beams from both seeds.
    grid = [[7] * 5 for _ in range(5)]
    grid[2] = [8, 3, 3, 8, 7]
    grid[1][4] = grid[4][4] = 8
    assert GEN.self_check(grid) == []


def test_grid_color_types_are_not_coerced_by_python_equality():
    grid = GEN.generate(3, 1)
    r, c = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 7)
    grid[r][c] = 7.0
    assert GEN.self_check(grid)


def test_canonical_inputs_remain_in_the_declared_domain():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 6
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []


def test_every_exact_axis_is_observable_from_pixels():
    observer = getattr(GEN, "observe_overrides", None)
    assert callable(observer), "Exact controls require a pixel-derived observer"
    grid = GEN.generate(19, 1, grid_h=6, grid_w=7, n_walls=8, orientation="vertical")
    assert observer(grid) == {
        "grid_h": 6, "grid_w": 7, "n_walls": 8, "orientation": "vertical",
    }


def test_diagnostic_optics_match_independent_racket_cases():
    diagnostic = getattr(GEN, "_laser_output", None)
    assert callable(diagnostic), "Semantic witnesses need a checked optics model"
    fixture = json.loads((SOURCE.parent / "counterexamples/reference-cases.json").read_text())
    assert fixture["executed_rule_hash"] == GEN.RULE_HASH
    for pair in fixture["cases"]:
        assert diagnostic(pair["input"]) == pair["output"]
    for pair in canonical_pairs(TASK_ID, root=ROOT):
        assert diagnostic(pair["input"]) == pair["output"]


def test_claimed_canonical_shortcuts_really_fit_all_labeled_pairs():
    shortcuts = getattr(GEN, "CANONICAL_SHORTCUTS", {})
    assert set(shortcuts) == {"centerward_only", "axis_edge_only", "cluster_absorbs"}
    for pair in canonical_pairs(TASK_ID, root=ROOT):
        for name, rival in shortcuts.items():
            assert rival(pair["input"]) == pair["output"], name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_rich_examples_distinguish_the_declared_rivals(band):
    rivals = getattr(GEN, "LESSON_COMPETITORS", {})
    assert len(rivals) == 9, "Keep the tested optics and component rivals executable"
    for index in (0, 1, 3, 4):
        grid = GEN.generate(17, index, difficulty=band)
        target = GEN._laser_output(grid)
        assert target != grid
        for name, rival in rivals.items():
            assert rival(grid) != target, (band, index, name)


def test_first_component_rival_reproduces_the_retained_teaching_defect():
    rival = getattr(GEN, "SEMANTIC_RIVALS", {}).get("first_input_component_only")
    assert callable(rival), "Retain the additional component-selection rival"
    record = json.loads((SOURCE.parent / "counterexamples/first-component-lesson.json").read_text())
    lesson = record["instance"]
    assert all(rival(pair["input"]) == pair["output"] for pair in lesson["train"])
    assert rival(lesson["test"][0]["input"]) != lesson["test"][0]["output"]
