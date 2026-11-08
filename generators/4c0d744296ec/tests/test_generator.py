"""Task-local regression tests for the reviewed 4c0d744296ec sampler."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK = "4c0d744296ec"
HOME = Path(__file__).resolve().parents[1]
CANONICAL_PROFILES = {
    (6, 10, 3),
    (7, 9, 3),
    (7, 10, 3),
    (8, 8, 2),
    (9, 11, 3),
}


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_4c0d744296ec", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def intended_output(grid):
    """Independent Python oracle for the unchanged Racket rule."""
    top = list(grid[0])
    return [top[:] for _ in grid]


def observed(grid):
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "markers": sum(value != 0 for value in grid[0]),
    }


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(TASK, root=find_root(__file__)),
    ids=lambda pair: f"{pair['split']}{pair['pair_index']}",
)
def test_accepts_canonical_inputs_and_oracle_matches_outputs(pair):
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]
    assert pair["input"] == original


def test_contract_advertises_only_constructive_observable_controls():
    assert gen.RULE_HASH == "c508f4ec9417"
    assert gen.VERSION == "2.0.0"
    assert set(gen.AXES) == {"grid_h", "grid_w", "markers"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.EXAMPLES_NEEDED == 3
    assert set(gen.SEMANTIC_RIVALS) == {
        "top_row_only",
        "single_color_projection",
    }
    assert set(gen.LESSON_COMPETITORS) == set(gen.SEMANTIC_RIVALS)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_honored_and_observable_in_every_band(band):
    options = {"grid_h": 6, "grid_w": 14, "markers": 6}
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    colors = [value for value in grid[0] if value]
    assert len(colors) == len(set(colors)) == 6
    assert grid == gen.generate(17, 9, difficulty=band, **options)


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 5),
        ("grid_h", 13),
        ("grid_w", 7),
        ("grid_w", 15),
        ("markers", 1),
        ("markers", 7),
        ("grid_h", True),
        ("grid_w", 10.0),
        ("markers", "3"),
    ],
)
def test_rejects_unknown_out_of_range_and_wrong_type_overrides(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_band_has_canonical_profile_support_and_broad_diversity(band):
    profiles = set()
    inputs = set()
    edge_markers = 0
    for index in range(80):
        grid = gen.generate(4100 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        values = observed(grid)
        profiles.add((values["grid_h"], values["grid_w"], values["markers"]))
        inputs.add(tuple(tuple(row) for row in grid))
        edge_markers += int(grid[0][0] != 0 or grid[0][-1] != 0)
    assert profiles & CANONICAL_PROFILES
    assert len(profiles) >= 12
    assert len(inputs) >= 76
    assert edge_markers >= 8


def test_semantic_rivals_are_real_counterexamples_on_generated_witness():
    grid = gen.generate(712, 4, grid_h=9, grid_w=11, markers=3)
    expected = intended_output(grid)
    assert gen.SEMANTIC_WITNESSES["multiple_marker_colors"](grid)
    assert gen.WITNESS_RIVALS["multiple_marker_colors"] == [
        "top_row_only",
        "single_color_projection",
    ]
    for name in gen.WITNESS_RIVALS["multiple_marker_colors"]:
        rival = gen.SEMANTIC_RIVALS[name](grid)
        assert rival != expected
        assert gen.LESSON_COMPETITORS[name](grid) == rival


def test_self_check_rejects_rule_vacuity_body_noise_duplicate_colors_and_bad_values():
    base = gen.generate(91, 7, grid_h=8, grid_w=10, markers=3)
    mutations = []

    no_markers = deepcopy(base)
    no_markers[0] = [0] * len(no_markers[0])
    mutations.append(no_markers)

    body_noise = deepcopy(base)
    body_noise[2][4] = 7
    mutations.append(body_noise)

    duplicate = deepcopy(base)
    positions = [c for c, value in enumerate(duplicate[0]) if value]
    duplicate[0][positions[1]] = duplicate[0][positions[0]]
    mutations.append(duplicate)

    illegal_color = deepcopy(base)
    illegal_color[0][positions[0]] = 10
    mutations.append(illegal_color)

    ragged = deepcopy(base)
    ragged[-1] = ragged[-1][:-1]
    mutations.append(ragged)

    for grid in mutations:
        assert gen.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[False] * 8 for _ in range(6)]])
def test_self_check_reports_malformed_inputs_instead_of_raising(grid):
    assert gen.self_check(grid)
