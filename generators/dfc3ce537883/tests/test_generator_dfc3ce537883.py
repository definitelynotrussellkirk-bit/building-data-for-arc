"""Task-local regressions for the vertical-divider reflection generator."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    TASK_ID,
    canonical_pairs,
    largest_component_only,
    load_generator,
    monochrome_copy,
    observed_axes,
    reference_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def pair(grid):
    return {"input": deepcopy(grid), "output": reference_output(grid)}


def test_rule_pin_and_all_canonical_pairs_match_independent_oracle():
    assert gen.RULE_HASH == "6177794736be"
    pairs = canonical_pairs()
    assert len(pairs) == 3
    for item in pairs:
        assert gen.self_check(item["input"]) == []
        assert gen.strict_canonical_like(item["input"]) == []
        assert reference_output(item["input"]) == item["output"]
        assert gen.rule_mirror(item["input"]) == item["output"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_every_exact_axis_round_trips_at_domain_boundaries(difficulty):
    cases = [
        {
            "grid_h": 5,
            "grid_w": 9,
            "n_cells": 3,
            "n_colors": 1,
            "layout": "connected",
            "axis_position": "center",
        },
        {
            "grid_h": 12,
            "grid_w": 15,
            "n_cells": 8,
            "n_colors": 3,
            "layout": "split",
            "axis_position": "off_center",
        },
    ]
    for index, requested in enumerate(cases):
        grid = gen.generate(
            5000 + index,
            17 + index,
            difficulty=difficulty,
            **requested,
        )
        assert gen.self_check(grid) == []
        assert observed_axes(grid) == requested
        assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 4),
        ("grid_h", 13),
        ("grid_w", 8),
        ("grid_w", 16),
        ("n_cells", 2),
        ("n_cells", 9),
        ("n_colors", 0),
        ("n_colors", 4),
        ("layout", "three_components"),
        ("axis_position", "left"),
        ("grid_h", True),
        ("n_cells", 3.0),
        ("n_colors", "2"),
        ("palette_kind", "warm"),
        ("blob_size", 4),
        ("texture", "default"),
    ],
)
def test_invalid_or_retired_overrides_fail_loudly(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(17, 0, **{key: value})


def test_every_five_pair_schedule_survives_any_query_rotation():
    rivals = gen.LESSON_COMPETITORS
    assert set(rivals) == {"largest_component_only", "monochrome_copy"}
    for difficulty in ("easy", "medium", "hard"):
        for start in range(12):
            grids = [
                gen.generate(20261004, start + offset, difficulty=difficulty)
                for offset in range(5)
            ]
            facts = [observed_axes(grid) for grid in grids]
            assert sum(item["layout"] == "split" for item in facts) >= 2
            assert sum(item["n_colors"] > 1 for item in facts) >= 2
            labelled = [pair(grid) for grid in grids]
            for held_out in range(5):
                demos = [item for i, item in enumerate(labelled) if i != held_out]
                query = labelled[held_out]
                for name, rival in rivals.items():
                    assert any(rival(item["input"]) != item["output"] for item in demos), (
                        difficulty,
                        start,
                        held_out,
                        name,
                    )
                assert gen.lesson_identifiable(demos, query) == []


def test_declared_witnesses_are_exact_per_grid_counterexamples():
    grids = [gen.generate(9300, index, difficulty="medium") for index in range(20)]
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        witness = gen.SEMANTIC_WITNESSES[witness_name]
        hits = [grid for grid in grids if witness(grid)]
        assert hits, witness_name
        for grid in hits:
            expected = reference_output(grid)
            assert any(
                gen.SEMANTIC_RIVALS[name](deepcopy(grid)) != expected
                for name in rival_names
            ), witness_name


def test_declared_canonical_shortcuts_really_fit_every_public_pair():
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "largest_component_only",
        "monochrome_copy",
    }
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        for item in canonical_pairs():
            original = deepcopy(item["input"])
            assert rival(original) == item["output"], name
            assert original == item["input"], name


def test_mutation_fixtures_and_targeted_impostors_are_rejected():
    fixtures = dict(gen.mutation_fixtures())
    assert {"no_divider", "multiple_dividers", "no_left_content", "right_content", "stray_divider_color", "clipped_reflection"} <= set(fixtures)
    for name, grid in fixtures.items():
        assert gen.self_check(grid), name

    good = gen.generate(
        88,
        2,
        grid_h=7,
        grid_w=11,
        n_cells=5,
        n_colors=2,
        layout="connected",
        axis_position="center",
    )
    bad_bool = deepcopy(good)
    bad_bool[0][0] = True
    bad_float = deepcopy(good)
    bad_float[0][0] = 1.5
    ragged = deepcopy(good)
    ragged[0].pop()
    assert gen.self_check(bad_bool)
    assert gen.self_check(bad_float)
    assert gen.self_check(ragged)
    assert gen.self_check(None)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(4815162342)
    before = random.getstate()
    first = gen.generate(1234, 19, difficulty="hard")
    middle = random.getstate()
    second = gen.generate(1234, 19, difficulty="hard")
    after = random.getstate()
    assert before == middle == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 8
    assert first != second


def test_generated_outputs_are_nonidentity_and_match_real_racket_when_available():
    try:
        from arc_repl.racket_bridge import racket_runtime_status
        from arcpuzzles import Catalog
        from reviewer_support import find_root
    except ImportError as exc:
        pytest.skip(str(exc))
    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [item["input"] for item in canonical_pairs()]
    grids += [gen.generate(6400, index, difficulty="hard") for index in range(12)]
    assert all(reference_output(grid) != grid for grid in grids)
    result = Catalog(find_root(__file__)).apply(TASK_ID, grids, timeout=180)
    assert result["rule_hash_matches_catalog"]
    assert [item["output"] for item in result["results"]] == [
        reference_output(grid) for grid in grids
    ]
