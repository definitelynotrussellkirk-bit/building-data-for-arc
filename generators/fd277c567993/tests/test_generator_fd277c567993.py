"""Task-local regression frontier for the additive-stencil transfer generator."""
from __future__ import annotations

import copy
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (analyze, canonical_pairs, independent_rule,
                             load_generator, valid_grid)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


EXPECTED_AXES = {
    "panel_h",
    "panel_w",
    "shape_size_ab",
    "shape_size_c",
    "n_diff",
    "palette_kind",
    "offset_relation",
}


def test_rule_binding_and_axis_contract_are_explicit():
    assert gen.RULE_HASH == "1890aa619f98"
    assert set(gen.AXES) == EXPECTED_AXES
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    for spec in gen.AXES.values():
        assert spec["valid"] not in {"2", "3", "various"}


def test_unknown_and_wrongly_typed_overrides_are_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, typo_axis=1)
    for key, value in (("panel_h", True), ("n_diff", "2"), ("palette_kind", 3)):
        with pytest.raises(ValueError):
            gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        dict(panel_h=5, panel_w=5, shape_size_ab=3, shape_size_c=6,
             n_diff=1, palette_kind="separator_shared", offset_relation="clear"),
        dict(panel_h=10, panel_w=9, shape_size_ab=6, shape_size_c=3,
             n_diff=4, palette_kind="distinct", offset_relation="overwrite"),
    ],
)
def test_every_exact_control_is_honored_in_every_band(band, options):
    grid = gen.generate(20261004, 7, difficulty=band, **options)
    assert gen.self_check(grid) == []
    observed = analyze(grid)
    declared = gen.observe_overrides(grid)
    assert {key: observed[key] for key in options} == options
    assert {key: declared[key] for key in options} == options


def test_clear_and_overwrite_are_real_rule_distinctions():
    base = dict(panel_h=5, panel_w=5, shape_size_ab=6, shape_size_c=3,
                n_diff=4, palette_kind="distinct")
    clear = gen.generate(91, 0, offset_relation="clear", **base)
    overwrite = gen.generate(91, 0, offset_relation="overwrite", **base)
    clear_f, overwrite_f = analyze(clear), analyze(overwrite)
    assert clear_f["offset_relation"] == "clear"
    assert overwrite_f["offset_relation"] == "overwrite"
    assert not (clear_f["targets"] & clear_f["query_points"])
    assert overwrite_f["targets"] & overwrite_f["query_points"]
    assert independent_rule(clear) != independent_rule(overwrite)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_four_consecutive_examples_cover_the_overwrite_shortcut(band):
    for seed in (0, 17, 987654321):
        grids = [gen.generate(seed, i, difficulty=band) for i in range(24)]
        for start in range(21):
            window = [analyze(grid) for grid in grids[start:start + 4]]
            assert {row["offset_relation"] for row in window} == {"clear", "overwrite"}
            assert all(row["before_top"] != row["query_top"] for row in window)
            assert all(
                row["before_shape"] != row["query_shape"]
                or row["before_colors"] != row["query_colors"]
                for row in window
            )


def test_python_mirror_matches_all_canonical_pairs():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert independent_rule(pair["input"]) == pair["output"]
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_generated_inputs_match_independent_rule_and_semantic_contract(band):
    for index in range(24):
        grid = gen.generate(8000 + index, index, difficulty=band)
        original = copy.deepcopy(grid)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen.rule_mirror(grid) == independent_rule(grid)
        assert grid == original
    assert set(gen.SEMANTIC_RIVALS) >= {
        "copy_query", "copy_after_panel", "absolute_8_positions", "skip_occupied_query"
    }
    assert set(gen.SEMANTIC_WITNESSES) >= {
        "nontrivial_stencil", "translated_bbox", "query_differs_from_after", "overwrites_query_object"
    }


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_scheduled_four_demo_lessons_are_identifiable(band):
    for start in range(0, 24, 4):
        pairs = []
        for index in range(start, start + 5):
            grid = gen.generate(12345 + start, index, difficulty=band)
            pairs.append({"input": grid, "output": independent_rule(grid)})
        assert gen.lesson_identifiable(pairs[:4], pairs[4]) == []


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], "bad", [[True]], {}])
def test_malformed_inputs_are_diagnostic_not_exceptions(bad):
    assert gen.self_check(bad)
    for predicate in gen.SEMANTIC_WITNESSES.values():
        assert predicate(bad) is False
    good_grid = gen.generate(0, 0)
    good = {"input": good_grid, "output": gen.rule_mirror(good_grid)}
    assert gen.lesson_identifiable([copy.deepcopy(good)] * 4, {"input": bad, "output": []})


def test_boolean_cells_cannot_pass_as_integer_outputs():
    pairs = []
    for index in range(5):
        grid = gen.generate(42, index)
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
    assert gen.lesson_identifiable(pairs[:4], pairs[4]) == []
    pairs[0]["output"] = [
        [False if value == 0 else value for value in row]
        for row in pairs[0]["output"]
    ]
    assert gen.lesson_identifiable(pairs[:4], pairs[4]) == [
        "pair 0 has a malformed output grid"
    ]


def test_default_distribution_hits_both_canonical_profiles_in_each_band():
    for band in ("easy", "medium", "hard"):
        profiles = set()
        for index in range(80):
            grid = gen.generate(50000 + index, index * 11, difficulty=band)
            assert valid_grid(grid)
            profiles.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
        assert (5, 17, 4) in profiles
        assert (5, 17, 5) in profiles


def test_deterministic_replay():
    kwargs = dict(difficulty="hard", panel_h=7, panel_w=8, shape_size_ab=5,
                  shape_size_c=4, n_diff=3, palette_kind="distinct",
                  offset_relation="overwrite")
    assert gen.generate(314159, 27, **kwargs) == gen.generate(314159, 27, **kwargs)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_five_pair_lessons_are_identifiable_under_every_query_rotation(band):
    """No single witness may be lost merely by choosing it as the query pair."""
    for start in range(8):
        pairs = []
        for index in range(start, start + gen.EXAMPLES_NEEDED + 1):
            grid = gen.generate(24680 + start, index, difficulty=band)
            pairs.append({"input": grid, "output": independent_rule(grid)})
        for query_index, query in enumerate(pairs):
            demos = [pair for i, pair in enumerate(pairs) if i != query_index]
            assert gen.lesson_identifiable(demos, query) == []
