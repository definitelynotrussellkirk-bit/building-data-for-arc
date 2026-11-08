"""Regression contract for the palette-mask multiplication generator."""
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
    CANONICAL_PROFILES,
    MASKS,
    TASK_ID,
    canonical_pairs,
    canonical_profile,
    fixed_3x3_rival,
    load_generator,
    mask_shape,
    no_gap_rival,
    observed_axes,
    palette,
    reference_output,
    solid_bbox_rival,
    sorted_palette_rival,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def labelled(grid):
    return {"input": deepcopy(grid), "output": reference_output(grid)}


def test_rule_pin_and_every_canonical_pair_match_independent_oracle():
    assert gen.RULE_HASH == "efb1009fca26"
    pairs = canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert reference_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_every_exact_axis_round_trips_at_boundaries(difficulty):
    cases = [
        {"grid_h": 7, "grid_w": 9, "n_palette": 2, "mask_id": 0},
        {"grid_h": 10, "grid_w": 14, "n_palette": 4, "mask_id": len(MASKS) - 1},
    ]
    for index, requested in enumerate(cases):
        grid = gen.generate(1000 + index, 21 + index, difficulty=difficulty, **requested)
        assert gen.self_check(grid) == []
        assert observed_axes(grid) == requested
        assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 6),
        ("grid_h", 11),
        ("grid_w", 8),
        ("grid_w", 15),
        ("n_palette", 1),
        ("n_palette", 5),
        ("mask_id", -1),
        ("mask_id", len(MASKS)),
        ("grid_h", True),
        ("grid_w", 9.0),
        ("n_palette", "3"),
        ("mask_id", None if False else 2.5),
        ("palette_kind", "warm"),
        ("palette_size", 3),
        ("n_distinct_colors", 4),
        ("position_bias", "row0_palette_plus_mask"),
        ("density", "sparse"),
        ("texture", "default"),
    ],
)
def test_invalid_or_retired_overrides_fail_loudly(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(17, 0, **{key: value})


def test_default_schedule_has_rotation_safe_teaching_witnesses():
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "canonical_sorted",
        "broad_unsorted",
        "canonical_unsorted",
        "broad_sorted",
    )
    assert set(gen.LESSON_COMPETITORS) == {
        "fixed_3x3",
        "sorted_palette",
        "no_gap",
        "solid_bbox",
    }
    for difficulty in ("easy", "medium", "hard"):
        for start in range(12):
            grids = [gen.generate(20261005, start + offset, difficulty=difficulty) for offset in range(4)]
            assert sum(mask_shape(grid) != (3, 3) for grid in grids) >= 2
            assert sum(palette(grid) != sorted(palette(grid)) for grid in grids) >= 2
            assert all(canonical_profile(grid) in CANONICAL_PROFILES for grid in grids)
            pairs = [labelled(grid) for grid in grids]
            for query_index in range(4):
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                query = pairs[query_index]
                assert gen.lesson_identifiable(demos, query) == []
                for name, rival in gen.LESSON_COMPETITORS.items():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                        difficulty,
                        start,
                        query_index,
                        name,
                    )


def test_declared_canonical_shortcut_fits_all_public_pairs_and_is_refuted_generated():
    assert set(gen.CANONICAL_SHORTCUTS) == {"fixed_3x3"}
    for pair in canonical_pairs():
        original = deepcopy(pair["input"])
        assert fixed_3x3_rival(original) == pair["output"]
        assert original == pair["input"]

    witnesses = [gen.generate(33, index) for index in range(8)]
    broad = [grid for grid in witnesses if mask_shape(grid) != (3, 3)]
    assert len(broad) >= 4
    for grid in broad:
        assert gen.SEMANTIC_WITNESSES["non_3x3_mask"](grid)
        assert gen.SEMANTIC_RIVALS["fixed_3x3"](deepcopy(grid)) == fixed_3x3_rival(grid)
        assert fixed_3x3_rival(grid) != reference_output(grid)


def test_other_rivals_are_pure_and_have_real_counterexamples():
    unsorted = gen.generate(99, 1)
    assert palette(unsorted) != sorted(palette(unsorted))
    expected = reference_output(unsorted)
    rivals = {
        "sorted_palette": sorted_palette_rival,
        "no_gap": no_gap_rival,
        "solid_bbox": solid_bbox_rival,
    }
    for name, independent in rivals.items():
        original = deepcopy(unsorted)
        declared = gen.SEMANTIC_RIVALS[name](original)
        assert original == unsorted
        assert declared == independent(unsorted)
        assert declared != expected


def test_validator_rejects_targeted_impostors_and_bad_cell_types():
    good = gen.generate(88, 3, grid_h=9, grid_w=13, n_palette=4, mask_id=4)
    assert gen.self_check(good) == []

    mutations = {}
    mutations["duplicate_palette_color"] = deepcopy(good)
    nonzero = [c for c, value in enumerate(good[0]) if value]
    mutations["duplicate_palette_color"][0][nonzero[1]] = good[0][nonzero[0]]
    mutations["mask_on_legend_row"] = deepcopy(good)
    mutations["mask_on_legend_row"][0][next(c for c, value in enumerate(good[0]) if value == 0)] = 1
    mutations["foreign_color_below"] = deepcopy(good)
    mutations["foreign_color_below"][1][0] = 8
    mutations["disconnected_mask"] = deepcopy(good)
    mask_cells = [(r, c) for r, row in enumerate(good) for c, value in enumerate(row) if value == 1]
    r, c = mask_cells[-1]
    mutations["disconnected_mask"][r][c] = 0
    mutations["bool_cell"] = deepcopy(good)
    mutations["bool_cell"][1][0] = True
    mutations["float_cell"] = deepcopy(good)
    mutations["float_cell"][1][0] = 1.0
    mutations["ragged"] = deepcopy(good)
    mutations["ragged"][0].pop()

    for name, grid in mutations.items():
        assert gen.self_check(grid), name
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
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 1
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
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(6400, index, difficulty="hard") for index in range(12)]
    assert all(reference_output(grid) != grid for grid in grids)
    result = Catalog(find_root(__file__)).apply(TASK_ID, grids, timeout=180)
    assert result["rule_hash_matches_catalog"]
    assert [row["output"] for row in result["results"]] == [reference_output(grid) for grid in grids]


def test_difficulty_bands_change_lawful_defaults_without_changing_curriculum():
    for index in range(12):
        grids = {
            band: gen.generate(5150, index, difficulty=band)
            for band in ("easy", "medium", "hard")
        }
        assert len({repr(grid) for grid in grids.values()}) >= 2, index
        assert len({gen.schedule_profile(5150, index, band) for band in grids}) == 1
        assert all(gen.self_check(grid) == [] for grid in grids.values())
        assert all(canonical_profile(grid) in CANONICAL_PROFILES for grid in grids.values())


def test_review_probe_exhausts_joint_axes_and_cyclic_starts():
    import review_probe

    report = review_probe.run_probe(
        axis_difficulties=(None,),
        cyclic_starts=range(8),
        include_racket=False,
    )
    assert report["status"] == "pass"
    assert report["axis_matrix"]["checked"] == 4 * 6 * 3 * len(MASKS)
    assert report["axis_matrix"]["failures"] == []
    assert report["cyclic_lessons"]["starts_checked"] == 8 * 3
    assert report["cyclic_lessons"]["rotations_checked"] == 8 * 3 * 4
    assert report["cyclic_lessons"]["failures"] == []
