"""Source-bound regressions for the db98b701e5bb generator repair."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import random
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    CANONICAL_PROFILES,
    EXPECTED_RULE_HASH,
    canonical_pairs,
    components4,
    largest_scan_rank,
    load_generator,
    observed,
    recolor_rank,
    recolor_smallest,
    recolor_largest_bbox,
    reference_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
EXPECTED_AXES = {"grid_h", "grid_w", "component_profile", "distractor_color"}


def test_rule_pin_axes_and_all_canonical_pairs_match_independent_oracle():
    assert gen.RULE_HASH == EXPECTED_RULE_HASH
    assert set(gen.AXES) == EXPECTED_AXES
    pairs = canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert reference_output(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {"grid_h": 8, "grid_w": 10, "component_profile": "tie_small", "distractor_color": 1},
        {"grid_h": 9, "grid_w": 12, "component_profile": "three_distinct", "distractor_color": 5},
        {"grid_h": 10, "grid_w": 13, "component_profile": "two_large", "distractor_color": 9},
        {"grid_h": 8, "grid_w": 13, "component_profile": "four_varied", "distractor_color": 3},
    ],
)
def test_every_advertised_override_is_exact_observable_and_lawful_in_every_band(band, requested):
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert observed(grid) == requested
    assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("texture", "warm"),
        ("palette_kind", "warm"),
        ("anchor_corner", True),
        ("asymmetry_force", False),
        ("palette_size", 1),
        ("position_bias", "fixed"),
        ("n_distinct_colors", 1),
        ("other", 5),
        ("grid_h", 7), ("grid_h", 11), ("grid_h", True), ("grid_h", "8"),
        ("grid_w", 9), ("grid_w", 14), ("grid_w", False), ("grid_w", 10.0),
        ("component_profile", "unknown"), ("component_profile", 3),
        ("distractor_color", 0), ("distractor_color", 2), ("distractor_color", 8),
        ("distractor_color", 10), ("distractor_color", True),
    ],
)
def test_unknown_retired_and_invalid_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("difficulty", ["trivial", "expert", 0.5, True])
def test_unknown_or_non_string_difficulty_is_rejected(difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty=difficulty)


def test_default_distribution_hits_canonical_profiles_and_all_semantic_branches_per_band():
    for band in ("easy", "medium", "hard"):
        profiles = set()
        component_profiles = set()
        colors = set()
        ranks = set()
        inputs = set()
        for index in range(256):
            seed = 2_000 + index
            sample_index = index * 11 + 1
            grid = gen.generate(seed, sample_index, difficulty=band)
            assert gen.self_check(grid) == []
            assert grid == gen.generate(seed, sample_index, difficulty=band)
            stats = observed(grid)
            profiles.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
            component_profiles.add(stats["component_profile"])
            colors.add(stats["distractor_color"])
            ranks.add(largest_scan_rank(grid))
            inputs.add(repr(grid))
            assert reference_output(grid) != grid
        assert profiles & CANONICAL_PROFILES
        assert component_profiles == {"tie_small", "three_distinct"}
        assert colors == {1, 3, 4, 5, 6, 7, 9}
        assert ranks == {0, 1, 2}
        assert len(inputs) >= 245


def test_each_three_example_window_and_every_query_rotation_refutes_declared_competitors():
    competitors = gen.LESSON_COMPETITORS
    assert set(competitors) == {"first_red", "last_red", "smallest_red", "largest_bbox_area"}
    for band in ("easy", "medium", "hard"):
        for start in range(18):
            pairs = []
            for offset in range(4):
                index = start + offset
                grid = gen.generate(500 + start, index, difficulty=band)
                pairs.append({"input": grid, "output": reference_output(grid)})
            for query_index in range(4):
                query = pairs[query_index]
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                assert gen.lesson_identifiable(demos, query) == []
                for name, rival in competitors.items():
                    fits_all_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
                    disagrees_on_query = rival(query["input"]) != query["output"]
                    assert not (fits_all_demos and disagrees_on_query), (band, start, query_index, name)



def test_largest_bbox_area_shortcut_fits_every_canonical_pair_and_each_lesson_has_two_refutations():
    pairs = canonical_pairs()
    assert all(recolor_largest_bbox(pair["input"]) == pair["output"] for pair in pairs)
    assert gen.CANONICAL_SHORTCUTS["largest_bbox_area"] is gen.SEMANTIC_RIVALS["largest_bbox_area"]
    for band in ("easy", "medium", "hard"):
        for start in range(24):
            lesson = []
            for offset in range(4):
                grid = gen.generate(7300 + start, start + offset, difficulty=band)
                lesson.append((grid, reference_output(grid)))
            disagreements = [recolor_largest_bbox(grid) != output for grid, output in lesson]
            # Any one held-out query still leaves at least one bbox counterexample.
            assert sum(disagreements) >= 2, (band, start, disagreements)

def test_semantic_witnesses_fire_and_rivals_are_real_wrong_rules():
    intended_differences = {name: 0 for name in gen.SEMANTIC_RIVALS}
    witness_hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    for index in range(96):
        grid = gen.generate(1_000 + index, index, difficulty="medium")
        intended = reference_output(grid)
        for name, witness in gen.SEMANTIC_WITNESSES.items():
            witness_hits[name] += bool(witness(grid))
        for name, rival in gen.SEMANTIC_RIVALS.items():
            intended_differences[name] += rival(grid) != intended
    assert all(value > 0 for value in witness_hits.values())
    assert all(value > 0 for value in intended_differences.values())


@pytest.mark.parametrize(
    "mutation",
    ["largest_tie", "input_has_8", "missing_distractor", "two_distractor_colors", "touching_red", "ragged", "bad_cell"],
)
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(
        44,
        3,
        grid_h=9,
        grid_w=12,
        component_profile="three_distinct",
        distractor_color=5,
    )
    changed = deepcopy(grid)
    red = sorted(components4(changed, 2), key=len)
    if mutation == "largest_tie":
        # Remove one cell from the size-5 component while preserving connectivity.
        largest = red[-1]
        removable = next(
            cell for cell in largest
            if len(components4([[2 if (r, c) in set(largest) - {cell} else 0 for c in range(len(changed[0]))] for r in range(len(changed))], 2)) == 1
        )
        changed[removable[0]][removable[1]] = 0
    elif mutation == "input_has_8":
        r, c = red[0][0]
        changed[r][c] = 8
    elif mutation == "missing_distractor":
        changed = [[0 if value not in (0, 2) else value for value in row] for row in changed]
    elif mutation == "two_distractor_colors":
        r, c = next((r, c) for r, row in enumerate(changed) for c, value in enumerate(row) if value == 0)
        changed[r][c] = 6
    elif mutation == "touching_red":
        changed = [[0 for _ in range(12)] for _ in range(9)]
        for r, c in ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)):
            changed[r][c] = 2
        # This size-4 square is only diagonally adjacent to the size-5 plus.
        for r, c in ((3, 2), (3, 3), (4, 2), (4, 3)):
            changed[r][c] = 2
        for r, c in ((6, 8), (6, 9), (7, 8)):
            changed[r][c] = 2
        changed[8][11] = 5
    elif mutation == "ragged":
        changed[0].pop()
    elif mutation == "bad_cell":
        changed[0][0] = True
    assert gen.self_check(changed), mutation


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 10 for _ in range(8)]])
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_replay_is_fresh_global_rng_pure_and_hash_seed_independent():
    random.seed(1927)
    before = random.getstate()
    first = gen.generate(42, 7, difficulty="hard")
    after = random.getstate()
    second = gen.generate(42, 7, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))

    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    results = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert results[0] == results[1]
