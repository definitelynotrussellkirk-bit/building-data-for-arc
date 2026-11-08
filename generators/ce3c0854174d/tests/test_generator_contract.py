"""Regressions for the public input/override and transform-timeline contracts."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root


ROOT = find_root(__file__)
TASK = "ce3c0854174d"
SOURCE = next(p for p in (
    ROOT / "generators" / TASK / "generator.py",
    ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py",
) if p.is_file())
SPEC = importlib.util.spec_from_file_location("timeline_generator_under_test", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def example(script=(1, 3)):
    grid = [[0] * 10 for _ in range(7)]
    grid[0][:len(script)] = script
    grid[2][2] = 7
    grid[3][2:5] = [7, 7, 7]
    return grid


@pytest.mark.parametrize("axis,value", [
    ("height", 7), ("height", 12), ("width", 10), ("width", 16),
    ("script_len", 2), ("script_len", 5),
])
def test_advertised_boundaries_are_observable(axis, value):
    grid = GEN.generate(0, 0, **{axis: value})
    observed = {"height": len(grid), "width": len(grid[0]),
                "script_len": sum(v != 0 for v in grid[0])}
    assert observed[axis] == value
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_joint_dimension_and_script_length_fits(band):
    for height in range(7, 13):
        for width in range(10, 17):
            for length in range(2, 6):
                grid = GEN.generate(17, 1, difficulty=band, height=height,
                                    width=width, script_len=length)
                assert (len(grid), len(grid[0])) == (height, width)
                assert sum(v != 0 for v in grid[0]) == length
                assert not GEN.self_check(grid)


def test_unknown_axis_fails_instead_of_silently_changing_intent():
    with pytest.raises((ValueError, TypeError), match="unknown"):
        GEN.generate(0, 0, heigth=9)


@pytest.mark.parametrize("value", [True, 8.75, "9"])
def test_exact_integer_axis_does_not_coerce(value):
    with pytest.raises((ValueError, TypeError)):
        GEN.generate(0, 0, height=value)


@pytest.mark.parametrize("kind", [
    "empty_script", "script_hole", "unknown_code", "empty_body",
    "row_one_object", "body_code", "disconnected", "two_colors",
    "float_color", "bool_color", "string_color", "ragged", "all_background",
])
def test_validator_rejects_broken_task_structure(kind):
    grid = example()
    if kind == "empty_script":
        grid[0] = [0] * 10
    elif kind == "script_hole":
        grid[0][:3] = [1, 0, 3]
    elif kind == "unknown_code":
        grid[0][1] = 8
    elif kind == "empty_body":
        grid[2:] = [[0] * 10 for _ in grid[2:]]
    elif kind == "row_one_object":
        grid[1][8] = 7
    elif kind == "body_code":
        grid[3][3] = 2
    elif kind == "disconnected":
        grid[6][9] = 7
    elif kind == "two_colors":
        grid[3][3] = 8
    elif kind == "float_color":
        grid[3][3] = 7.0
    elif kind == "bool_color":
        grid[0][0] = True
    elif kind == "string_color":
        grid[3][3] = "7"
    elif kind == "ragged":
        grid[-1].pop()
    elif kind == "all_background":
        grid = [[0] * 10 for _ in range(7)]
    assert GEN.self_check(grid), kind


def test_validator_accepts_body_left_of_script_and_at_bottom_edge():
    grid = [[0] * 10 for _ in range(7)]
    grid[0][:2] = [4, 1]
    grid[5][0] = 8
    grid[6][:3] = [8, 8, 8]
    assert GEN.self_check(grid) == []


def test_all_canonical_inputs_stay_in_the_domain():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []


@pytest.mark.parametrize("code,expected", [
    (1, [[7, 7], [7, 0], [7, 0]]),
    (2, [[7, 7, 7], [0, 0, 7]]),
    (3, [[0, 0, 7], [7, 7, 7]]),
    (4, [[7, 7], [0, 7], [0, 7]]),
])
def test_executable_legend_matches_hand_computed_rectangular_outputs(code, expected):
    assert GEN.predict_gallery(example((code,))) == expected


def test_second_frame_uses_the_transformed_state():
    expected = [[7, 7, 0, 7, 7], [7, 0, 0, 0, 7], [7, 0, 0, 0, 7]]
    assert GEN.predict_gallery(example()) == expected


def test_python_diagnostic_agrees_with_all_canonical_labels():
    for pair in canonical_pairs(TASK, root=ROOT):
        assert GEN.predict_gallery(pair["input"]) == pair["output"]


def test_difficulty_affects_actual_draws():
    assert any(GEN.generate(seed, 1, difficulty="easy") !=
               GEN.generate(seed, 1, difficulty="hard") for seed in range(12))


def test_default_draw_provenance_matches_the_returned_pixels(monkeypatch):
    contexts = []
    real_context = GEN.gen_ctx

    def capture_context(**kwargs):
        ctx = real_context(**kwargs)
        contexts.append(ctx)
        return ctx

    monkeypatch.setattr(GEN, "gen_ctx", capture_context)
    for index in (0, 1):
        output = GEN.generate(17, index, difficulty="medium")
        recorded = contexts[-1].recorded_draws()
        observed = {"height": len(output), "width": len(output[0]),
                    "script_len": sum(value != 0 for value in output[0])}
        assert {key: recorded.get(key) for key in observed} == observed
