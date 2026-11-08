"""Regression and semantic-contract tests for ffdc0ddb44bd."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

from puzzle_generators.helpers.selfcheck import components
from reviewer_support import canonical_pairs, find_root

TASK_ID = "ffdc0ddb44bd"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _candidate_components(grid):
    return sorted(
        components(grid, colors={2, 3, 4, 5, 6}),
        key=lambda comp: (comp["bbox"][0], comp["bbox"][1]),
    )


def _crop_component(comp):
    r1, c1, r2, c2 = comp["bbox"]
    cells = set(comp["cells"])
    return [
        [8 if (row, col) in cells else 0 for col in range(c1, c2 + 1)]
        for row in range(r1, r2 + 1)
    ]


def independent_rule(grid):
    comps = _candidate_components(grid)
    counts = {}
    for comp in comps:
        counts[comp["norm"]] = counts.get(comp["norm"], 0) + 1
    winner = sorted(counts, key=lambda shape: (-counts[shape], len(shape)))[0]
    return _crop_component(next(comp for comp in comps if comp["norm"] == winner))


def color2_shortcut(grid):
    return _crop_component(next(comp for comp in _candidate_components(grid) if comp["color"] == 2))


def first_object_shortcut(grid):
    return _crop_component(_candidate_components(grid)[0])


def _pair(grid):
    return {"input": grid, "output": independent_rule(grid)}


def test_rule_pin_and_small_exact_axis_contract():
    assert GEN.RULE_HASH == "29652af15048"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.SCHEDULE_PROFILES == (0, 1, 2, 3)
    assert set(GEN.AXES) == {"height", "width", "majority_count"}


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("height,width", [(9, 14), (10, 16), (18, 22)])
@pytest.mark.parametrize("majority_count", [2, 3, 4])
def test_exact_overrides_are_constructive_and_observable(
    band, height, width, majority_count
):
    grid = GEN.generate(
        183,
        7,
        difficulty=band,
        height=height,
        width=width,
        majority_count=majority_count,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "height": height,
        "width": width,
        "majority_count": majority_count,
    }
    assert independent_rule(grid) == GEN.rule_mirror(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"height": 8},
        {"height": 19},
        {"width": 13},
        {"width": 23},
        {"majority_count": 1},
        {"majority_count": 5},
        {"height": True},
        {"width": 16.5},
        {"majority_count": "2"},
        {"unknown_axis": 1},
        {"difficulty": "impossible"},
    ],
)
def test_invalid_controls_are_rejected(kwargs):
    difficulty = kwargs.pop("difficulty", None)
    with pytest.raises(ValueError):
        GEN.generate(0, 0, difficulty=difficulty, **kwargs)


def test_canonical_inputs_are_accepted_and_rule_mirror_matches_authority():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert independent_rule(pair["input"]) == pair["output"]
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_declared_shortcuts_really_fit_all_canonical_pairs():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    expected = {
        "color_2_object": color2_shortcut,
        "first_object": first_object_shortcut,
    }
    assert set(GEN.CANONICAL_SHORTCUTS) == set(expected)
    for name, shortcut in expected.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_four_profile_schedule_breaks_color_and_position_shortcuts(band):
    grids = [GEN.generate(911, index, difficulty=band) for index in range(8)]
    truth = [independent_rule(grid) for grid in grids]

    color_disagreements = [color2_shortcut(grid) != out for grid, out in zip(grids, truth)]
    first_disagreements = [first_object_shortcut(grid) != out for grid, out in zip(grids, truth)]
    assert any(color_disagreements) and not all(color_disagreements)
    assert any(first_disagreements) and not all(first_disagreements)
    assert any(GEN.SEMANTIC_WITNESSES["color_2_is_decoy"](grid) for grid in grids)
    assert any(GEN.SEMANTIC_WITNESSES["first_object_is_decoy"](grid) for grid in grids)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_cyclic_four_pair_window_and_query_rotation_is_identifiable(band):
    for start in range(12):
        pairs = [_pair(GEN.generate(1207 + start, start + offset, difficulty=band))
                 for offset in range(4)]
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(item["input"]) != item["output"] for item in demos), (
                    band,
                    start,
                    query_index,
                    name,
                )


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_hits_canonical_profile_and_varies_scene(band):
    grids = [GEN.generate(314, index, difficulty=band) for index in range(80)]
    observed = [GEN.observe_overrides(grid) for grid in grids]
    assert any(
        item["height"] in {9, 10}
        and item["width"] == 16
        and item["majority_count"] == 2
        for item in observed
    )
    assert len({item["height"] for item in observed}) >= 6
    assert len({item["width"] for item in observed}) >= 6
    assert {item["majority_count"] for item in observed} == {2, 3, 4}
    assert len({tuple(tuple(row) for row in grid) for grid in grids}) >= 76


def test_generation_and_helpers_are_deterministic_fresh_and_pure():
    for band in (None, "easy", "medium", "hard"):
        for index in range(12):
            first = GEN.generate(77, index, difficulty=band)
            second = GEN.generate(77, index, difficulty=band)
            assert first == second
            assert first is not second
            assert all(a is not b for a, b in zip(first, second))
            assert GEN.self_check(first) == []
            original = deepcopy(first)
            assert GEN.rule_mirror(first) == independent_rule(first)
            for rival in GEN.SEMANTIC_RIVALS.values():
                rival(first)
                assert first == original
            for witness in GEN.SEMANTIC_WITNESSES.values():
                witness(first)
                assert first == original


def test_self_check_rejects_semantic_near_misses_but_accepts_role_swaps():
    good = GEN.generate(202, 0, height=10, width=16, majority_count=2)
    assert GEN.self_check(good) == []

    # Color is not semantic: swapping two whole-object colors stays valid.
    swapped = [[6 if value == 2 else 2 if value == 6 else value for value in row]
               for row in good]
    assert GEN.self_check(swapped) == []

    invalid_color = deepcopy(good)
    r, c = _candidate_components(invalid_color)[0]["cells"][0]
    invalid_color[r][c] = 9
    assert GEN.self_check(invalid_color)

    tied = deepcopy(good)
    majority = [comp for comp in _candidate_components(tied)
                if comp["norm"] == _candidate_components(tied)[0]["norm"]]
    # Erase one complete majority object, leaving one winner and one decoy.
    # There is then no strict most-frequent shape.
    winner_norm = max(
        {comp["norm"] for comp in _candidate_components(tied)},
        key=lambda shape: sum(comp["norm"] == shape for comp in _candidate_components(tied)),
    )
    erase = next(comp for comp in _candidate_components(tied) if comp["norm"] == winner_norm)
    for row, col in erase["cells"]:
        tied[row][col] = 0
    assert GEN.self_check(tied)


def test_pinned_profile_floor_has_exact_canonical_support_in_every_band():
    """Mirror the native gate's pinned off-diagonal 20-draw census."""
    import hashlib

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
            exact += profile in {(9, 16, 4), (10, 16, 4)}
        assert exact >= 1, (band, exact)
