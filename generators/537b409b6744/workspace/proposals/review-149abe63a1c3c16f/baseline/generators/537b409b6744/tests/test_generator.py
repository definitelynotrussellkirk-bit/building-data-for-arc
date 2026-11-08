"""Task-local regression suite for the 537b409b6744 repair."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest
from reviewer_support import canonical_pairs, find_root

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (
    TASK_ID,
    components,
    farthest_candidate_output,
    load_generator,
    mode_color,
    no_growth_output,
    observed,
    ranked_candidates,
    rule_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))
EXPECTED_AXES = {
    "grid_h",
    "grid_w",
    "direction",
    "mover_span",
    "mover_depth",
    "wall_extra",
    "wall_depth",
    "gap",
    "distractor_kind",
}


def test_contract_pins_authority_and_declares_only_observable_axes():
    assert gen.RULE_HASH == "7b81cecb3b71"
    assert gen.VERSION == "4.0.0"
    assert set(gen.AXES) == EXPECTED_AXES
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize(
    "pair",
    PAIRS,
    ids=lambda pair: f"v{pair['variant']}-{pair['split']}{pair['pair_index']}",
)
def test_all_canonical_pairs_are_accepted_and_match_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert rule_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("direction", ["down", "up", "right", "left"])
@pytest.mark.parametrize("distractor_kind", ["solid", "ragged"])
def test_every_exact_override_is_observable_in_every_band(
    band, direction, distractor_kind
):
    options = {
        "grid_h": 10,
        "grid_w": 10,
        "direction": direction,
        "mover_span": 2,
        "mover_depth": 2,
        "wall_extra": 2,
        "wall_depth": 3,
        "gap": 2,
        "distractor_kind": distractor_kind,
    }
    grid = gen.generate(701, 19, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 9),
        ("grid_h", 15),
        ("grid_w", 9),
        ("grid_w", 15),
        ("direction", "north"),
        ("mover_span", 0),
        ("mover_span", 3),
        ("mover_depth", 0),
        ("wall_extra", 1),
        ("wall_extra", 4),
        ("wall_depth", 1),
        ("wall_depth", 4),
        ("gap", -1),
        ("gap", 3),
        ("distractor_kind", "blob"),
        ("grid_h", True),
        ("gap", 1.5),
    ],
)
def test_invalid_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_covers_canonical_profile_and_semantic_branches(band):
    profiles = set()
    directions = set()
    backgrounds = set()
    distractors = set()
    for index in range(96):
        grid = gen.generate(2100 + index, index * 11, difficulty=band)
        assert grid == gen.generate(2100 + index, index * 11, difficulty=band)
        assert gen.self_check(grid) == []
        stats = observed(grid)
        assert gen.observe_overrides(grid) == stats
        assert len({value for row in grid for value in row}) == 4
        assert len(components(grid)) == 3
        candidates = ranked_candidates(grid)
        assert len(candidates) >= 2
        assert candidates[0]["gap"] < candidates[-1]["gap"]
        authority = rule_output(grid)
        assert authority != grid
        assert farthest_candidate_output(grid) != authority
        assert no_growth_output(grid) != authority
        profiles.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
        directions.add(stats["direction"])
        backgrounds.add(mode_color(grid))
        distractors.add(stats["distractor_kind"])
    assert (10, 10, 4) in profiles
    assert directions == {"down", "up", "right", "left"}
    assert distractors == {"solid", "ragged"}
    assert 7 in backgrounds
    assert len(backgrounds) >= 5


def test_validator_rejects_structure_destroying_mutations():
    options = dict(
        grid_h=10,
        grid_w=10,
        direction="down",
        mover_span=2,
        mover_depth=2,
        wall_extra=2,
        wall_depth=3,
        gap=1,
        distractor_kind="ragged",
    )
    grid = gen.generate(41, 7, **options)
    assert gen.self_check(grid) == []
    background = mode_color(grid)
    selected = ranked_candidates(grid)[0]
    object_list = components(grid, background)
    distractor = next(
        obj
        for obj in object_list
        if obj["index"]
        not in (selected["mover"]["index"], selected["wall"]["index"])
    )

    blank = [[background for _ in row] for row in grid]
    no_distractor = deepcopy(grid)
    for row, column in distractor["cells"]:
        no_distractor[row][column] = background
    holed_mover = deepcopy(grid)
    row, column = selected["mover"]["cells"][0]
    holed_mover[row][column] = background
    fifth_color = deepcopy(grid)
    used = {value for row_values in grid for value in row_values}
    extra = next(color for color in range(10) if color not in used)
    placed = False
    occupied = {cell for obj in object_list for cell in obj["cells"]}
    for row in range(len(grid)):
        for column in range(len(grid[0])):
            if (row, column) not in occupied:
                fifth_color[row][column] = extra
                placed = True
                break
        if placed:
            break

    for mutation in (blank, no_distractor, holed_mover, fifth_color):
        assert gen.self_check(mutation)


def test_semantic_contract_rivals_are_real_counterexamples():
    for direction in ("down", "up", "right", "left"):
        grid = gen.generate(
            901,
            len(direction),
            grid_h=10,
            grid_w=10,
            direction=direction,
            mover_span=2,
            mover_depth=1,
            wall_extra=2,
            wall_depth=3,
            gap=0,
            distractor_kind="solid",
        )
        assert gen.strict_canonical_like(grid) == []
        authority = rule_output(grid)
        assert gen.SEMANTIC_WITNESSES["nearest_pair"](grid)
        assert gen.SEMANTIC_RIVALS["farthest_pair"](grid) == farthest_candidate_output(grid)
        assert gen.SEMANTIC_RIVALS["no_wall_growth"](grid) == no_growth_output(grid)
        assert farthest_candidate_output(grid) != authority
        assert no_growth_output(grid) != authority


def test_colors_are_roles_not_fixed_labels():
    seen_role_palettes = set()
    for index in range(80):
        grid = gen.generate(3400 + index, index)
        selected = ranked_candidates(grid)[0]
        seen_role_palettes.add(
            (
                mode_color(grid),
                selected["mover"]["color"],
                selected["wall"]["color"],
            )
        )
    assert len(seen_role_palettes) >= 50


def test_independent_oracle_preserves_color_counts_expected_by_rule():
    for index in range(40):
        grid = gen.generate(5100 + index, index)
        output = rule_output(grid)
        selected = ranked_candidates(grid)[0]
        input_counts = Counter(value for row in grid for value in row)
        output_counts = Counter(value for row in output for value in row)
        mover_color = selected["mover"]["color"]
        assert output_counts[mover_color] == input_counts[mover_color]
        assert len(output) == len(grid)
        assert len(output[0]) == len(grid[0])


def test_difficulty_bands_change_default_gap_without_restricting_overrides():
    grids = {
        band: gen.generate(12345, 17, difficulty=band)
        for band in ("easy", "medium", "hard")
    }
    assert {band: observed(grid)["gap"] for band, grid in grids.items()} == {
        "easy": 0,
        "medium": 1,
        "hard": 2,
    }
    assert len({repr(grid) for grid in grids.values()}) == 3
