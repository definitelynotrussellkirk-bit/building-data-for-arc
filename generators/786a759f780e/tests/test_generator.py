"""Source-bound regressions for the repaired hole-sorted strip generator."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import canonical_pairs, components, facts, load_generator, oracle

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def _pair(grid):
    return {"input": deepcopy(grid), "output": oracle(grid)}


def test_rule_identity_and_all_canonical_pairs_are_owned_and_solved():
    assert gen.RULE_HASH == "71abd31a186f"
    assert gen.VERSION == "3.0.0"
    pairs = canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(deepcopy(pair["input"])) == []
        assert gen.strict_canonical_like(deepcopy(pair["input"])) == []
        assert oracle(pair["input"]) == pair["output"]
        assert gen.rule_mirror(deepcopy(pair["input"])) == pair["output"]


def test_every_five_demo_window_and_every_rotated_query_cover_all_profiles():
    assert gen.EXAMPLES_NEEDED == 5
    required = set(gen.SCENE_PROFILES)
    for start in range(24):
        six = [gen.schedule_profile(99, start + offset, difficulty="hard") for offset in range(6)]
        assert set(six[: gen.EXAMPLES_NEEDED]) == required
        for query_index in range(6):
            demos = six[:query_index] + six[query_index + 1 :]
            assert len(demos) == gen.EXAMPLES_NEEDED
            assert set(demos) == required


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_observable_and_mirrors_match_independent_oracle(band):
    for scene_profile in gen.SCENE_PROFILES:
        for canvas_profile in gen.CANVAS_PROFILES:
            grid = gen.generate(
                91027,
                17,
                difficulty=band,
                scene_profile=scene_profile,
                canvas_profile=canvas_profile,
            )
            assert gen.observe_overrides(grid) == {
                "scene_profile": scene_profile,
                "canvas_profile": canvas_profile,
            }
            assert gen.self_check(grid) == []
            assert gen.rule_mirror(deepcopy(grid)) == oracle(grid)
            assert facts(grid)["mixed_components"] >= 1


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_profiles_are_real_counterexamples_to_declared_shortcuts(band):
    for seed in range(8):
        canonical = gen.generate(seed, 0, difficulty=band, scene_profile="canonical_holes")
        priority = gen.generate(seed, 1, difficulty=band, scene_profile="hole_priority")
        ties = gen.generate(seed, 2, difficulty=band, scene_profile="tie_chain")

        assert gen._rival_area_only(priority) != oracle(priority)
        assert gen._rival_hole_only(ties) != oracle(ties)
        assert gen._rival_area_descending(ties) != oracle(ties)
        assert gen._rival_no_color_tiebreak(ties) != oracle(ties)

        for grid in (canonical, priority, ties):
            expected = oracle(grid)
            assert gen._rival_reading_order(grid) != expected
            assert gen._rival_color_order(grid) != expected
            assert gen._rival_same_color_components(grid) != expected


@pytest.mark.parametrize(
    "kwargs",
    [
        {"nonsense_axis": "typo"},
        {"scene_profile": "unknown"},
        {"canvas_profile": "10x20"},
    ],
)
def test_unknown_and_out_of_domain_overrides_reject(kwargs):
    with pytest.raises(ValueError):
        gen.generate(1, 0, **kwargs)
    with pytest.raises(ValueError):
        gen.generate(1, 0, difficulty="impossible")


def test_every_declared_canonical_shortcut_really_fits_canonical_pairs():
    pairs = canonical_pairs()
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(deepcopy(pair["input"])) == pair["output"] for pair in pairs), name


def test_rotated_lessons_are_identifiable_against_all_declared_competitors():
    for start in range(12):
        six = [gen.generate(7001 + start, start + offset, difficulty="hard") for offset in range(6)]
        pairs = [_pair(grid) for grid in six]
        for query_index in range(6):
            query = pairs[query_index]
            demos = pairs[:query_index] + pairs[query_index + 1 :]
            assert gen.lesson_identifiable(deepcopy(demos), deepcopy(query)) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(deepcopy(pair["input"])) != pair["output"] for pair in demos), name


def test_self_check_rejects_malformed_and_structural_impostors():
    malformed = [None, [], [[]], [[0], [0, 1]], [[True] * 20 for _ in range(11)]]
    for grid in malformed:
        assert gen.self_check(grid)

    one_object = [[0] * 20 for _ in range(11)]
    for row in range(3):
        for col in range(3):
            if row in (0, 2) or col in (0, 2):
                one_object[row][col] = 8
    assert gen.self_check(one_object)

    damaged = gen.generate(31, 2, scene_profile="tie_chain", canvas_profile="11x20")
    object_cells = components(damaged)[0]["cells"]
    row, col = object_cells[0]
    damaged[row][col] = 0
    assert gen.self_check(damaged)


def test_determinism_fresh_rows_and_global_random_state():
    random.seed(20261004)
    state = random.getstate()
    first = gen.generate(314159, 11, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(314159, 11, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second
