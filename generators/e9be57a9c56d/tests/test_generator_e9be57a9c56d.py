"""Source-bound regression and teaching tests for e9be57a9c56d."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (
    canonical_pairs,
    canonical_record,
    endpoint_only_anchor,
    facts,
    fixed_color_two_anchor,
    load_generator,
    oracle,
    profile,
    racket_outputs,
)

gen = load_generator()
CANONICAL_PROFILES = {(23, 17, 4), (16, 22, 4), (23, 14, 4), (13, 24, 5)}
EXPECTED_AXES = {"orientation", "n_markers", "template_size", "anchor_pos"}


@pytest.mark.parametrize("pair", canonical_pairs(), ids=("train0", "train1", "train2", "test0"))
def test_canonical_inputs_are_owned_and_independent_oracle_is_exact(pair):
    assert gen.RULE_HASH == "f8100feef807"
    assert gen.self_check(pair["input"]) == []
    assert hasattr(gen, "strict_canonical_like")
    assert gen.strict_canonical_like(pair["input"]) == []
    assert oracle(pair["input"]) == pair["output"]
    assert hasattr(gen, "rule_mirror")
    assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_active_racket_authorities_are_exactly_synced_to_canonical_source():
    root = HOME.parents[1]
    canonical = canonical_record()["program_solution"]
    for relative in (
        "shared/data/base/solutions/training/9b2a60aa__e9be57a9c56d.json",
        "shared/data/base/solutions/augmented/9b2a60aa__22a0e99ad7cd.json",
    ):
        target = json.loads((root / relative).read_text(encoding="utf-8"))["racket_target"]
        assert target["target_code"] == canonical


def test_declared_axis_surface_is_small_exact_and_observable():
    assert set(gen.AXES) == EXPECTED_AXES
    assert hasattr(gen, "observe_overrides")
    for orientation in ("horizontal", "vertical"):
        for n_markers in range(2, 6):
            for template_size in range(3, 8):
                for anchor_pos in range(n_markers):
                    grid = gen.generate(
                        9102,
                        n_markers * 100 + template_size * 10 + anchor_pos,
                        orientation=orientation,
                        n_markers=n_markers,
                        template_size=template_size,
                        anchor_pos=anchor_pos,
                    )
                    expected = {
                        "orientation": orientation,
                        "n_markers": n_markers,
                        "template_size": template_size,
                        "anchor_pos": anchor_pos,
                    }
                    assert gen.self_check(grid) == []
                    assert gen.observe_overrides(grid) == expected
                    assert {name: facts(grid)[name] for name in expected} == expected
                    assert gen.rule_mirror(grid) == oracle(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": 1},
        {"orientation": "diagonal"}, {"orientation": 1},
        {"n_markers": 1}, {"n_markers": 6}, {"n_markers": True}, {"n_markers": "3"},
        {"template_size": 2}, {"template_size": 8}, {"template_size": False}, {"template_size": 4.0},
        {"anchor_pos": -1}, {"anchor_pos": 5}, {"anchor_pos": True}, {"anchor_pos": "1"},
        {"n_markers": 2, "anchor_pos": 2},
    ],
)
def test_invalid_or_unknown_overrides_fail_fast(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(7, 0, **kwargs)


def test_unknown_difficulty_fails_fast():
    with pytest.raises(ValueError):
        gen.generate(7, 0, difficulty="expert")


def test_public_schedule_profiles_are_exact_canonical_profile_triples():
    assert set(gen.SCHEDULE_PROFILES) == CANONICAL_PROFILES


def test_incompatible_anchor_marker_pairs_are_declared_for_strict_override_audit():
    declaration = getattr(gen, "INCOMPATIBLE_OVERRIDE_COMBINATIONS", ())
    assert any(
        isinstance(item, dict) and set(item) == {"n_markers", "anchor_pos"}
        for item in declaration
    )


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_every_valid_single_axis_override_is_constructive_across_bands(band):
    cases = [
        *({"orientation": value} for value in ("horizontal", "vertical")),
        *({"n_markers": value} for value in range(2, 6)),
        *({"template_size": value} for value in range(3, 8)),
        *({"anchor_pos": value} for value in range(5)),
    ]
    for seed in range(32):
        for case in cases:
            grid = gen.generate(seed, seed * 17 + 3, difficulty=band, **case)
            assert gen.self_check(grid) == []
            observed = gen.observe_overrides(grid)
            assert all(observed[name] == value for name, value in case.items())


@pytest.mark.parametrize("band", (None, "easy", "medium", "hard"))
def test_each_twenty_draw_band_hits_every_canonical_profile(band):
    grids = [gen.generate(3181, index, difficulty=band) for index in range(20)]
    profiles = {profile(grid) for grid in grids}
    assert CANONICAL_PROFILES <= profiles
    assert all(gen.self_check(grid) == [] for grid in grids)
    assert all(gen.strict_canonical_like(grid) == [] for grid in grids)


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_every_four_consecutive_draws_survive_all_query_rotations(band):
    assert getattr(gen, "EXAMPLES_NEEDED", None) == 3
    assert set(gen.CANONICAL_SHORTCUTS) == {"fixed_color_two_anchor", "endpoint_only_anchor"}
    for start in range(16):
        pairs = []
        for offset in range(4):
            grid = gen.generate(4401, start + offset, difficulty=band)
            pairs.append({"input": grid, "output": oracle(grid)})
        for query_index in range(4):
            query = pairs[query_index]
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(deepcopy(demos), deepcopy(query)) == []
            for rival in gen.LESSON_COMPETITORS.values():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos)


def test_canonical_shortcuts_fit_all_canonical_pairs_and_generated_witnesses_refute_them():
    pairs = canonical_pairs()
    for rival in (fixed_color_two_anchor, endpoint_only_anchor):
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs)
    for rival in gen.CANONICAL_SHORTCUTS.values():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs)

    grids = [gen.generate(992, index, difficulty="medium") for index in range(12)]
    assert any(facts(grid)["template_color"] != 2 and fixed_color_two_anchor(grid) != oracle(grid)
               for grid in grids)
    assert any(0 < facts(grid)["anchor_pos"] < facts(grid)["n_markers"] - 1
               and endpoint_only_anchor(grid) != oracle(grid) for grid in grids)
    assert any(gen.SEMANTIC_WITNESSES["non_two_template_anchor"](grid) for grid in grids)
    assert any(gen.SEMANTIC_WITNESSES["interior_anchor"](grid) for grid in grids)


@pytest.mark.parametrize("band", (None, "easy", "medium", "hard"))
def test_default_distribution_is_deterministic_lawful_and_diverse(band):
    grids = [gen.generate(7000 + index, index, difficulty=band) for index in range(96)]
    assert grids == [gen.generate(7000 + index, index, difficulty=band) for index in range(96)]
    assert all(gen.self_check(grid) == [] for grid in grids)
    assert all(gen.rule_mirror(grid) == oracle(grid) for grid in grids)
    assert len({tuple(map(tuple, grid)) for grid in grids}) >= 90
    rows = [facts(grid) for grid in grids]
    assert {row["orientation"] for row in rows} == {"horizontal", "vertical"}
    assert {row["n_markers"] for row in rows} >= {4, 5}
    assert {row["template_size"] for row in rows} >= {6, 7}
    assert any(row["template_color"] != 2 for row in rows)
    assert any(0 < row["anchor_pos"] < row["n_markers"] - 1 for row in rows)


def test_all_targeted_mutation_fixtures_are_rejected():
    assert hasattr(gen, "mutation_fixtures")
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 6
    for name, grid in fixtures:
        assert gen.self_check(grid), name
        assert gen.strict_canonical_like(grid), name


@pytest.mark.parametrize("grid", (None, [], [[]], [[0], [0, 1]], [[True] * 8 for _ in range(8)]))
def test_malformed_values_are_diagnostic_not_exceptions(grid):
    assert gen.self_check(grid)


def test_real_racket_authority_matches_independent_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status
    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(556, index, difficulty="hard") for index in range(16)]
    original = deepcopy(grids)
    assert racket_outputs(grids) == [oracle(grid) for grid in grids]
    assert grids == original


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_declared_rivals_are_total_rectangular_grid_rules_on_generated_domain(band):
    declarations = (
        gen.CANONICAL_SHORTCUTS,
        gen.LESSON_COMPETITORS,
        gen.SEMANTIC_RIVALS,
    )
    for sample_index in range(64):
        grid = gen.generate(271828, sample_index, difficulty=band)
        for declaration in declarations:
            for name, rival in declaration.items():
                prediction = rival(deepcopy(grid))
                assert isinstance(prediction, list), (band, sample_index, name)
                assert len(prediction) == len(grid), (band, sample_index, name)
                assert all(isinstance(row, list) and len(row) == len(grid[0])
                           for row in prediction), (band, sample_index, name)
                assert all(type(value) is int and 0 <= value <= 9
                           for row in prediction for value in row), (band, sample_index, name)


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_reference_probe_rivals_match_declared_total_predictions(band):
    named = {
        "fixed_color_two_anchor": fixed_color_two_anchor,
        "endpoint_only_anchor": endpoint_only_anchor,
    }
    for sample_index in range(32):
        grid = gen.generate(314159, sample_index, difficulty=band)
        for name, independent in named.items():
            expected = gen.CANONICAL_SHORTCUTS[name](deepcopy(grid))
            prediction = independent(deepcopy(grid))
            assert isinstance(prediction, list), (band, sample_index, name)
            assert prediction == expected, (band, sample_index, name)
