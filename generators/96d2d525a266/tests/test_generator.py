"""Focused regressions for the rectangle-outline generator."""
from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (
    aligned_pair_rival,
    canonical_pairs,
    features,
    load_generator,
    observed,
    racket_outputs,
    reference_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs())
def test_accepts_canonical_domain_and_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert reference_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_observable_in_every_band(band):
    options = dict(grid_h=20, grid_w=19, n_pair_colors=4, n_decoy_colors=4)
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 9),
        ("grid_h", 21),
        ("grid_w", True),
        ("n_pair_colors", 0),
        ("n_pair_colors", 5),
        ("n_decoy_colors", -1),
        ("n_decoy_colors", 5),
        ("n_decoy_colors", 2.0),
        ("n_pair_colors", "2"),
    ],
)
def test_rejects_unknown_or_invalid_overrides(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


def test_zero_decoy_override_remains_exact_even_though_ordinary_lessons_use_decoys():
    options = dict(grid_h=10, grid_w=10, n_pair_colors=1, n_decoy_colors=0)
    grid = gen.generate(31, 1, difficulty="hard", **options)
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert gen.self_check(grid) == []


@pytest.mark.parametrize("value", [True, False, 1.0, "1", -1])
def test_rejects_invalid_sample_index(value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, value)


def test_distribution_covers_rule_distinguishing_branches():
    totals = {name: 0 for name in (
        "aligned_decoy",
        "multi_cell_decoy",
        "overlapping_pair_boxes",
        "outline_overwrite",
        "order_sensitive_overlap",
    )}
    shapes = set()
    pair_counts = set()
    decoy_counts = set()
    for band in (None, "easy", "medium", "hard"):
        for i in range(192):
            grid = gen.generate(2100 + i, i * 11, difficulty=band)
            assert gen.self_check(grid) == []
            assert grid == gen.generate(2100 + i, i * 11, difficulty=band)
            obs = observed(grid)
            shapes.add((obs["grid_h"], obs["grid_w"]))
            pair_counts.add(obs["n_pair_colors"])
            decoy_counts.add(obs["n_decoy_colors"])
            for name, present in features(grid).items():
                totals[name] += bool(present)
    assert len(shapes) >= 20
    assert pair_counts == {1, 2, 3, 4}
    # Ordinary lessons keep at least one decoy so the three-demo teaching
    # contract is always supported; zero remains an exact override boundary.
    assert decoy_counts == {1, 2, 3, 4}
    assert all(count >= 20 for count in totals.values()), totals


def test_canonical_aligned_pair_shortcut_gets_generated_counterexamples():
    assert all(aligned_pair_rival(pair["input"]) == pair["output"] for pair in canonical_pairs())
    witnesses = []
    for i in range(160):
        grid = gen.generate(7300 + i, i)
        if features(grid)["aligned_decoy"]:
            witnesses.append(grid)
    assert witnesses
    assert all(reference_output(grid) != aligned_pair_rival(grid) for grid in witnesses)
    assert gen.CANONICAL_SHORTCUTS["aligned_pairs_also_expand"] is not None


def test_generated_inputs_match_independent_oracle_and_do_not_mutate():
    for i in range(96):
        grid = gen.generate(5000 + i, i * 3, difficulty=("easy", "medium", "hard")[i % 3])
        original = deepcopy(grid)
        output = reference_output(grid)
        assert grid == original
        assert output != grid


def test_real_racket_reference_matches_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(8100 + i, i, difficulty=("easy", "medium", "hard")[i % 3]) for i in range(24)]
    assert racket_outputs(grids) == [reference_output(grid) for grid in grids]


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 10 for _ in range(10)], [[0] * 10 for _ in range(10)]],
)
def test_malformed_or_semantically_empty_inputs_are_diagnostic(grid):
    assert gen.self_check(grid)


def test_every_four_sample_lesson_refutes_declared_rivals_under_query_rotation():
    """Three demos plus one query must teach every declared competitor."""
    for band in ("easy", "medium", "hard"):
        for start in range(24):
            grids = [
                gen.generate(12000 + start, start + offset, difficulty=band)
                for offset in range(4)
            ]
            expected = [reference_output(grid) for grid in grids]
            for query_index in range(4):
                demo_indices = [index for index in range(4) if index != query_index]
                for name, rival in gen.LESSON_COMPETITORS.items():
                    fits_demos = all(
                        rival(grids[index]) == expected[index]
                        for index in demo_indices
                    )
                    changes_query = rival(grids[query_index]) != expected[query_index]
                    assert not (fits_demos and changes_query), (
                        band,
                        start,
                        query_index,
                        name,
                    )


@pytest.mark.parametrize(
    "band,seed,start,rival_name",
    [
        ("easy", 8117972535090, 0, "numeric_color_order"),
        ("easy", 89756791814456, 22, "aligned_pairs_also_expand"),
        ("medium", 128699225020830, 22, "aligned_pairs_also_expand"),
    ],
)
def test_historical_ambiguous_lessons_are_now_refuted(band, seed, start, rival_name):
    """Regression for the three ambiguous lessons found in the first repair."""
    grids = [gen.generate(seed, start + offset, difficulty=band) for offset in range(4)]
    expected = [reference_output(grid) for grid in grids]
    rival = gen.LESSON_COMPETITORS[rival_name]
    fits_all_demos = all(rival(grids[index]) == expected[index] for index in range(3))
    changes_query = rival(grids[3]) != expected[3]
    assert not (fits_all_demos and changes_query)
