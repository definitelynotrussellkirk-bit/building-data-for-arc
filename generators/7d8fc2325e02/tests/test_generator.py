"""Regression and semantic-contract tests for 7d8fc2325e02."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "7d8fc2325e02"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def independent_rule(grid):
    width = len(grid[0])
    return [
        [3 if grid[row][col] != 0 or grid[row + 5][col] != 0 else 0
         for col in range(width)]
        for row in range(4)
    ]


def relation_counts(grid):
    counts = {"neither": 0, "top_only": 0, "bottom_only": 0, "both": 0}
    for row in range(4):
        for col in range(len(grid[0])):
            top = grid[row][col] != 0
            bottom = grid[row + 5][col] != 0
            key = (
                "both" if top and bottom
                else "top_only" if top
                else "bottom_only" if bottom
                else "neither"
            )
            counts[key] += 1
    return counts


def pair(grid):
    return {"input": grid, "output": independent_rule(grid)}


def test_rule_pin_and_public_contract_are_explicit():
    assert GEN.RULE_HASH == "e9653f7b4ad7"
    assert GEN.VERSION == "3.0.0"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.MIN_STRICT_FRAC == 1.0
    assert set(GEN.AXES) == {"grid_w", "top_color", "bot_color", "sep_color"}
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.HELPFUL_TEXTURES == ()
    assert GEN.DEGENERATE_TEXTURES == ()


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("width", [3, 5, 14])
@pytest.mark.parametrize(
    "colors",
    [
        (2, 1, 4),
        (3, 3, 3),
        (9, 1, 9),
    ],
)
def test_exact_overrides_are_constructive_and_observable(band, width, colors):
    top_color, bot_color, sep_color = colors
    grid = GEN.generate(
        183,
        7,
        difficulty=band,
        grid_w=width,
        top_color=top_color,
        bot_color=bot_color,
        sep_color=sep_color,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "grid_w": width,
        "top_color": top_color,
        "bot_color": bot_color,
        "sep_color": sep_color,
    }
    assert relation_counts(grid).keys() == {
        "neither", "top_only", "bottom_only", "both"
    }
    assert all(value > 0 for value in relation_counts(grid).values())
    assert GEN.rule_mirror(grid) == independent_rule(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_w": 2},
        {"grid_w": 15},
        {"grid_w": True},
        {"top_color": 0},
        {"top_color": 10},
        {"top_color": 1.0},
        {"bot_color": "1"},
        {"sep_color": False},
        {"unknown_axis": 1},
        {"difficulty": "impossible"},
    ],
)
def test_invalid_controls_are_rejected(kwargs):
    kwargs = dict(kwargs)
    difficulty = kwargs.pop("difficulty", None)
    with pytest.raises(ValueError):
        GEN.generate(0, 0, difficulty=difficulty, **kwargs)


@pytest.mark.parametrize("seed", [True, 1.5, "1"])
def test_invalid_seed_is_rejected(seed):
    with pytest.raises(ValueError):
        GEN.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, -1, 1.5, "1"])
def test_invalid_sample_index_is_rejected(sample_index):
    with pytest.raises(ValueError):
        GEN.generate(0, sample_index)


def test_canonical_inputs_are_accepted_and_python_rule_matches_authority():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 5
    for item in pairs:
        grid = item["input"]
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert independent_rule(grid) == item["output"]
        assert GEN.rule_mirror(grid) == item["output"]
        assert all(value > 0 for value in relation_counts(grid).values())


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_generated_input_contains_all_four_boolean_relations(band):
    for index in range(80):
        grid = GEN.generate(700 + index, index, difficulty=band)
        assert GEN.self_check(grid) == []
        counts = relation_counts(grid)
        assert all(value > 0 for value in counts.values()), (band, index, counts)
        output = independent_rule(grid)
        assert {value for row in output for value in row} == {0, 3}


def test_declared_witnesses_are_real_counterexamples_to_declared_rivals():
    grid = GEN.generate(991, 0, grid_w=5, top_color=2, bot_color=1, sep_color=4)
    truth = independent_rule(grid)
    assert set(GEN.SEMANTIC_WITNESSES) == {
        "top_only", "bottom_only", "overlap", "empty", "palette_generalization"
    }
    assert set(GEN.SEMANTIC_RIVALS) == {
        "copy_top", "copy_bottom", "and", "xor", "constant_filled",
        "canonical_colors_only",
    }
    for witness_name in ("top_only", "bottom_only", "overlap", "empty"):
        assert GEN.SEMANTIC_WITNESSES[witness_name](grid), witness_name
    for rival_name in ("copy_top", "copy_bottom", "and", "xor", "constant_filled"):
        rival = GEN.SEMANTIC_RIVALS[rival_name]
        prediction = rival(deepcopy(grid))
        assert prediction != truth, rival_name
        assert grid == GEN.generate(991, 0, grid_w=5, top_color=2, bot_color=1, sep_color=4)

    shortcut = GEN.SEMANTIC_RIVALS["canonical_colors_only"]
    assert shortcut(deepcopy(grid)) == truth
    palette_grid = GEN.generate(
        991, 7, grid_w=5, top_color=9, bot_color=8, sep_color=4
    )
    assert GEN.SEMANTIC_WITNESSES["palette_generalization"](palette_grid)
    assert shortcut(deepcopy(palette_grid)) != independent_rule(palette_grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_three_demo_window_and_query_rotation_is_identifiable(band):
    for start in range(12):
        episode = [pair(GEN.generate(1207 + start, start + offset, difficulty=band))
                   for offset in range(4)]
        for query_index, query in enumerate(episode):
            demos = [item for index, item in enumerate(episode) if index != query_index]
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(item["input"]) != item["output"] for item in demos), (
                    band, start, query_index, name
                )


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_hits_canonical_profile_and_broad_widths(band):
    grids = [GEN.generate(314, index, difficulty=band) for index in range(80)]
    observed = [GEN.observe_overrides(grid) for grid in grids]
    assert any(item == {
        "grid_w": 5,
        "top_color": 2,
        "bot_color": 1,
        "sep_color": 4,
    } for item in observed)
    assert len({item["grid_w"] for item in observed}) >= 10
    assert len({tuple(tuple(row) for row in grid) for grid in grids}) >= 76


def test_pinned_profile_floor_has_exact_canonical_support_in_every_band():
    for band in ("easy", "medium", "hard"):
        exact = 0
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
            profile = (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            exact += profile == (9, 5, 4)
        assert exact >= 1, (band, exact)


def test_self_check_rejects_relation_collapses_and_malformed_grids():
    good = GEN.generate(202, 0, grid_w=5, top_color=2, bot_color=1, sep_color=4)
    assert GEN.self_check(good) == []

    all_zero_panels = [[0] * 5 for _ in range(9)]
    all_zero_panels[4] = [4] * 5
    assert GEN.self_check(all_zero_panels)

    all_filled_panels = [[2] * 5 for _ in range(4)] + [[4] * 5] + [[1] * 5 for _ in range(4)]
    assert GEN.self_check(all_filled_panels)

    disjoint = [[0] * 5 for _ in range(9)]
    disjoint[4] = [4] * 5
    for row in range(4):
        for col in range(5):
            if (row + col) % 2 == 0:
                disjoint[row][col] = 2
            else:
                disjoint[row + 5][col] = 1
    assert GEN.self_check(disjoint)

    for malformed in (None, [], [[]], [[0], [0, 0]], [[True] * 5 for _ in range(9)]):
        assert GEN.self_check(malformed)


def test_generation_and_semantic_helpers_are_deterministic_fresh_and_pure():
    for band in (None, "easy", "medium", "hard"):
        for index in range(20):
            first = GEN.generate(77, index, difficulty=band)
            second = GEN.generate(77, index, difficulty=band)
            assert first == second
            assert first is not second
            assert all(a is not b for a, b in zip(first, second))
            original = deepcopy(first)
            assert GEN.rule_mirror(first) == independent_rule(first)
            for rival in GEN.SEMANTIC_RIVALS.values():
                rival(first)
                assert first == original
            for witness in GEN.SEMANTIC_WITNESSES.values():
                witness(first)
                assert first == original
