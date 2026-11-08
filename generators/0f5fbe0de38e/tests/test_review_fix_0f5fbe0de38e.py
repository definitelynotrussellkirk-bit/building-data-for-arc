from __future__ import annotations

import pytest

from reviewer_support import find_root, load_selected_generator


TASK_ID = "0f5fbe0de38e"
ROOT = find_root(__file__)
GEN, _GENERATOR_PATH, _GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, "1", -1])
def test_generate_rejects_invalid_sample_index_scalars(sample_index):
    with pytest.raises(ValueError, match="sample_index"):
        GEN.generate(910_000, sample_index, difficulty="easy")


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_integer_seed_scalars(seed):
    with pytest.raises(ValueError, match="seed"):
        GEN.generate(seed, 0, difficulty="easy")


@pytest.mark.parametrize(
    "difficulty",
    [True, False, 0, 1.0, "__invalid_difficulty__"],
)
def test_generate_rejects_invalid_difficulty_scalars(difficulty):
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(910_001, 0, difficulty=difficulty)


@pytest.mark.parametrize(
    "axis,value",
    [
        (axis, value)
        for axis in (
            "bg_color",
            "fill_color",
            "marker_a_color",
            "marker_b_color",
        )
        for value in (True, False, 1.0, "1")
    ],
)
def test_generate_rejects_non_integer_color_overrides(axis, value):
    with pytest.raises(ValueError, match=axis):
        GEN.generate(920_000, 0, difficulty="easy", **{axis: value})


def test_generate_is_constructive_without_semantic_round_trip(monkeypatch):
    def unexpected_analysis(_grid):
        raise AssertionError("generate must not re-parse its freshly constructed grid")

    monkeypatch.setattr(GEN, "_analyze", unexpected_analysis)
    grid = GEN.generate(
        930_000,
        5,
        difficulty="hard",
        grid_h=22,
        grid_w=22,
        template_profile="cross4_anti",
        lesson_profile="mixed_1_2_3",
        orientation_profile="mixed",
    )
    assert len(grid) == 22
    assert all(len(row) == 22 for row in grid)


def test_public_grid_observers_reuse_one_semantic_parse(monkeypatch):
    grid = GEN.generate(
        950_000,
        5,
        difficulty="hard",
        grid_h=22,
        grid_w=22,
        template_profile="cross4_anti",
        lesson_profile="mixed_1_2_3",
        orientation_profile="mixed",
    )
    original = GEN._components_non_bg_8
    calls = 0

    def counting_components(candidate, background):
        nonlocal calls
        calls += 1
        return original(candidate, background)

    monkeypatch.setattr(GEN, "_components_non_bg_8", counting_components)
    first = GEN.observe_overrides(grid)
    assert GEN.self_check(grid) == []
    second = GEN.observe_overrides(grid)
    assert first == second
    assert calls == 1

    mutated = [row[:] for row in grid]
    mutated[0][0] = (mutated[0][0] + 1) % 10
    GEN.self_check(mutated)
    assert calls == 2
