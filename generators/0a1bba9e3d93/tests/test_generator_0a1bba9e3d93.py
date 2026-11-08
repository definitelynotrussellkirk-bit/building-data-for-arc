"""Task-local regression and semantic-teaching tests for 0a1bba9e3d93."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import canonical_pairs, facts, load_generator, oracle

gen = load_generator()


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "test0"])
def test_canonical_inputs_are_owned_and_rule_mirror_matches(pair):
    assert gen.RULE_HASH == "386c52a84df2"
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert oracle(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_declared_exact_override_combination_is_constructive_and_observable(band):
    for height in range(3, 13):
        for panel_w in range(3, 9):
            for texture in ("plain", "diff_query", "clip"):
                grid = gen.generate(
                    991, height * 100 + panel_w,
                    difficulty=band,
                    grid_h=height,
                    panel_w=panel_w,
                    texture=texture,
                )
                expected = {"grid_h": height, "panel_w": panel_w, "texture": texture}
                assert gen.self_check(grid) == []
                assert gen.observe_overrides(grid) == expected
                assert facts(grid)["texture"] == texture
                assert gen.rule_mirror(grid) == oracle(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": 1},
        {"grid_h": 2}, {"grid_h": 13}, {"grid_h": True}, {"grid_h": 3.5},
        {"panel_w": 2}, {"panel_w": 9}, {"panel_w": False}, {"panel_w": "3"},
        {"texture": "no_growth"}, {"texture": 1},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(kwargs):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **kwargs)


def test_unknown_difficulty_is_rejected():
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty="expert")


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_four_consecutive_default_draws_cover_teaching_profiles(band):
    for start in range(12):
        profiles = [gen.schedule_profile(17, start + offset, band) for offset in range(4)]
        assert set(profiles) == set(gen.SCHEDULE_PROFILES)
        pairs = []
        for offset in range(5):
            grid = gen.generate(17, start + offset, difficulty=band)
            pairs.append({"input": grid, "output": oracle(grid)})
        assert gen.lesson_identifiable(pairs[:4], pairs[4]) == []


def test_declared_shortcuts_fit_all_canonical_pairs_but_have_generated_counterexamples():
    pairs = canonical_pairs()
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "copy_after_shape",
        "reject_partial_clip",
    }
    for rival in gen.CANONICAL_SHORTCUTS.values():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs)

    diff_grid = gen.generate(41, 1, texture="diff_query", grid_h=5, panel_w=5)
    clip_grid = gen.generate(41, 2, texture="clip", grid_h=5, panel_w=5)
    expected_diff = oracle(diff_grid)
    expected_clip = oracle(clip_grid)
    assert gen.SEMANTIC_WITNESSES["different_query_shape"](diff_grid)
    assert gen.SEMANTIC_RIVALS["copy_after_shape"](diff_grid) != expected_diff
    assert gen.SEMANTIC_WITNESSES["partial_clip"](clip_grid)
    assert gen.SEMANTIC_RIVALS["reject_partial_clip"](clip_grid) != expected_clip


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_is_deterministic_valid_and_diverse(band):
    grids = [gen.generate(2000 + index, index, difficulty=band) for index in range(96)]
    assert all(gen.self_check(grid) == [] for grid in grids)
    assert all(gen.strict_canonical_like(grid) == [] for grid in grids)
    assert all(grid == gen.generate(2000 + index, index, difficulty=band)
               for index, grid in enumerate(grids))
    signatures = {
        (tuple(tuple(row) for row in grid), tuple(tuple(row) for row in oracle(grid)))
        for grid in grids
    }
    assert len(signatures) >= 90
    assert {facts(grid)["texture"] for grid in grids} == {"plain", "diff_query", "clip"}
    exact_profiles = {
        (len(grid), len(grid[0]), len({value for row in grid for value in row}))
        for grid in grids
    }
    assert (3, 11, 4) in exact_profiles
    assert (4, 14, 4) in exact_profiles


@pytest.mark.parametrize(
    "mutation",
    [
        "blank",
        "bad_separator",
        "extra_panel_color",
        "erase_query",
        "disconnect_after",
        "remove_growth",
        "ragged",
        "bool_cell",
    ],
)
def test_self_check_rejects_targeted_destructive_mutations(mutation):
    grid = gen.generate(73, 1, grid_h=6, panel_w=6, texture="diff_query")
    changed = deepcopy(grid)
    panel_w = (len(changed[0]) - 2) // 3
    if mutation == "blank":
        changed = [[0 for _ in row] for row in changed]
    elif mutation == "bad_separator":
        changed[0][panel_w] = 0
    elif mutation == "extra_panel_color":
        changed[-1][0] = 9 if changed[-1][0] != 9 else 7
    elif mutation == "erase_query":
        left = 2 * (panel_w + 1)
        for row in changed:
            row[left:left + panel_w] = [0] * panel_w
    elif mutation == "disconnect_after":
        left = panel_w + 1
        support = {
            (row, col)
            for row in range(len(changed))
            for col in range(panel_w)
            if changed[row][left + col] != 0
        }
        color = changed[next(iter(support))[0]][left + next(iter(support))[1]]
        candidate = next(
            (row, col)
            for row in range(len(changed))
            for col in range(panel_w)
            if (row, col) not in support
            and all(abs(row - rr) + abs(col - cc) > 1 for rr, cc in support)
        )
        changed[candidate[0]][left + candidate[1]] = color
    elif mutation == "remove_growth":
        before = [row[:panel_w] for row in changed]
        for row_index, row in enumerate(before):
            changed[row_index][panel_w + 1:2 * panel_w + 1] = row[:]
    elif mutation == "ragged":
        changed[0] = changed[0][:-1]
    elif mutation == "bool_cell":
        changed[0][0] = True
    assert gen.self_check(changed)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 11 for _ in range(3)]])
def test_self_check_is_diagnostic_on_malformed_values(grid):
    assert gen.self_check(grid)
