"""Task-local regressions for bb41378fe3c8's teaching distribution."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
sys.path.insert(0, str(ROOT / "shared/runtime"))

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def load_generator():
    source = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("bb41378fe3c8_under_test", source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = load_generator()
BANDS = (None, "easy", "medium", "hard")
MARKER_PROFILES = ("plain", "blocked", "boundary", "mixed")


def intended_output(grid):
    """Independent mirror of the selected rule, used only by tests."""
    output = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 2:
                continue
            target = (row + 1, col + 1)
            if target[0] < height and target[1] < width and grid[target[0]][target[1]] == 0:
                output[target[0]][target[1]] = 5
    return output


def labelled(grid):
    return {"input": deepcopy(grid), "output": intended_output(grid)}


def marker_cells(grid):
    return [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    ]


def independent_observation(grid):
    height, width = len(grid), len(grid[0])
    markers = marker_cells(grid)
    boundary = [
        cell for cell in markers
        if cell[0] == height - 1 or cell[1] == width - 1
    ]
    blocked = [
        (row, col) for row, col in markers
        if row + 1 < height and col + 1 < width and grid[row + 1][col + 1] != 0
    ]
    if boundary and blocked:
        profile = "mixed"
    elif boundary:
        profile = "boundary"
    elif blocked:
        profile = "blocked"
    else:
        profile = "plain"
    blocked_targets = {(row + 1, col + 1) for row, col in blocked}
    free_decoys = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 2) and (row, col) not in blocked_targets
    ]
    return {
        "grid_h": height,
        "grid_w": width,
        "n_markers": len(markers),
        "marker_profile": profile,
        "n_decoys": len(free_decoys),
    }


@pytest.mark.parametrize(
    "pair",
    canonical_pairs("bb41378fe3c8", root=find_root(__file__)),
    ids=lambda pair: f"{pair['split']}{pair['pair_index']}",
)
def test_canonical_pairs_match_independent_rule_and_validator(pair):
    assert intended_output(pair["input"]) == pair["output"]
    assert gen.self_check(pair["input"]) == []


def test_contract_metadata_is_narrow_exact_and_rule_pinned():
    assert gen.RULE_HASH == "d655d37ca499"
    assert tuple(gen.AXES) == (
        "grid_h",
        "grid_w",
        "n_markers",
        "marker_profile",
        "n_decoys",
    )
    assert tuple(gen.AXES["marker_profile"]["valid"]) == MARKER_PROFILES
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == ()
    assert gen.DEGENERATE_TEXTURES == ()
    assert gen.HELPFUL_TEXTURES == ()


def test_reported_underfill_seed_now_honors_exact_marker_override():
    grid = gen.generate(1, 0, grid_h=6, grid_w=6, n_markers=7)
    assert len(marker_cells(grid)) == 7
    assert gen.observe_overrides(grid)["n_markers"] == 7
    assert gen.self_check(grid) == []


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("profile", MARKER_PROFILES)
def test_hardest_cartesian_override_is_exact_in_every_band(band, profile):
    grid = gen.generate(
        73,
        11,
        difficulty=band,
        grid_h=6,
        grid_w=6,
        n_markers=7,
        marker_profile=profile,
        n_decoys=3,
    )
    expected = {
        "grid_h": 6,
        "grid_w": 6,
        "n_markers": 7,
        "marker_profile": profile,
        "n_decoys": 3,
    }
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == expected
    assert independent_observation(grid) == expected
    assert grid == gen.generate(
        73,
        11,
        difficulty=band,
        grid_h=6,
        grid_w=6,
        n_markers=7,
        marker_profile=profile,
        n_decoys=3,
    )


@pytest.mark.parametrize("kwargs", [
    {"typo": 1},
    {"grid_h": 5},
    {"grid_w": 12},
    {"n_markers": 2},
    {"n_markers": True},
    {"marker_profile": "unknown"},
    {"marker_profile": 4},
    {"n_decoys": 4},
    {"n_decoys": 1.0},
])
def test_invalid_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize("band", BANDS)
def test_schedule_is_complete_deterministic_and_rotation_safe(band):
    period = len(gen.SCHEDULE_PROFILES)
    assert period == 8
    for seed in range(4):
        observed_names = {
            gen.schedule_profile(seed, index, band)
            for index in range(period)
        }
        assert observed_names == set(gen.SCHEDULE_PROFILES)
        for start in range(period):
            pairs = [
                labelled(gen.generate(seed, start + offset, difficulty=band))
                for offset in range(4)
            ]
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert gen.lesson_identifiable(demos, pairs[query_index]) == []
                for rival in gen.LESSON_COMPETITORS.values():
                    assert not all(
                        rival(pair["input"]) == pair["output"]
                        for pair in demos
                    )



def test_difficulty_bands_feed_the_keyed_layout_draw():
    # Axis defaults stay curriculum-controlled, but the optional difficulty
    # label must not be a dead input to generation.
    for seed in range(12):
        grids = {
            repr(gen.generate(seed, seed * 17 + 3, difficulty=band))
            for band in ("easy", "medium", "hard")
        }
        assert len(grids) > 1


def test_canonical_shortcuts_fit_public_pairs_and_generated_witnesses_refute_them():
    pairs = canonical_pairs("bb41378fe3c8", root=find_root(__file__))
    for pair in pairs:
        for rival in gen.CANONICAL_SHORTCUTS.values():
            assert rival(pair["input"]) == pair["output"]

    blocked = gen.generate(19, 0, marker_profile="blocked", n_decoys=0)
    decoy = gen.generate(19, 1, marker_profile="plain", n_decoys=1)
    assert gen.SEMANTIC_WITNESSES["blocked_destination"](blocked)
    assert gen.SEMANTIC_WITNESSES["non2_decoy_with_empty_shadow"](decoy)
    assert gen.SEMANTIC_RIVALS["overwrite_blockers"](blocked) != intended_output(blocked)
    assert gen.SEMANTIC_RIVALS["all_nonzero_casts"](decoy) != intended_output(decoy)


def test_rule_mirror_and_rivals_are_pure_and_independent():
    grid = gen.generate(91, 3, marker_profile="mixed", n_decoys=3)
    original = deepcopy(grid)
    output = gen.rule_mirror(grid)
    assert grid == original
    assert output == intended_output(grid)
    assert output is not grid
    assert all(left is not right for left, right in zip(output, grid))
    for rival in gen.SEMANTIC_RIVALS.values():
        before = deepcopy(grid)
        rival(grid)
        assert grid == before


def test_distribution_is_valid_deterministic_diverse_and_exact_at_upper_bound():
    serialized = set()
    profiles = set()
    shapes = set()
    for index in range(200):
        grid = gen.generate(1000 + index, index * 13 + 5, n_markers=7)
        assert grid == gen.generate(1000 + index, index * 13 + 5, n_markers=7)
        assert len(marker_cells(grid)) == 7
        assert gen.self_check(grid) == []
        assert gen.rule_mirror(grid) == intended_output(grid)
        serialized.add(repr(grid))
        profiles.add(gen.observe_overrides(grid)["marker_profile"])
        shapes.add((len(grid), len(grid[0])))
    # The schedule intentionally revisits canonical-sized anchors; require
    # strong within-band diversity without pretending the finite 6x6 anchor
    # has an effectively unbounded layout space.
    assert len(serialized) >= 180
    assert profiles == set(MARKER_PROFILES)
    assert {(6, 6), (7, 7), (8, 8)}.issubset(shapes)


@pytest.mark.parametrize("grid", [
    None,
    [],
    [[]],
    [[0], [0, 2]],
    [[True] * 6 for _ in range(6)],
    [[0] * 6 for _ in range(6)],
])
def test_validator_rejects_malformed_or_content_free_inputs_without_throwing(grid):
    assert gen.self_check(grid)


def test_validator_rejects_structure_destroying_mutations():
    base = gen.generate(311, 3, marker_profile="mixed", n_decoys=2)
    mutations = []

    output_color_in_input = deepcopy(base)
    output_color_in_input[0][1] = 5
    mutations.append(output_color_in_input)

    adjacent_markers = deepcopy(base)
    marker = marker_cells(adjacent_markers)[0]
    adjacent_markers[marker[0]][marker[1] + 1 if marker[1] + 1 < len(base[0]) else marker[1] - 1] = 2
    mutations.append(adjacent_markers)

    no_background = [[2 for _ in row] for row in base]
    mutations.append(no_background)

    too_many_decoys = deepcopy(base)
    added = 0
    for row in range(len(too_many_decoys) - 1):
        for col in range(len(too_many_decoys[0]) - 1):
            if too_many_decoys[row][col] == 0 and too_many_decoys[row + 1][col + 1] == 0:
                too_many_decoys[row][col] = 1
                added += 1
                if added == 5:
                    break
        if added == 5:
            break
    mutations.append(too_many_decoys)

    for changed in mutations:
        assert gen.self_check(changed)


def test_declared_mutation_fixtures_are_all_rejected():
    fixtures = gen.mutation_fixtures()
    assert fixtures
    for name, grid in fixtures:
        assert gen.self_check(grid), name
