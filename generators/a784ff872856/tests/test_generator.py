"""Focused source-bound regressions for a784ff872856.

The Racket program remains the label authority.  The local mirror is checked
against every canonical pair and against real Catalog applications so it can
be used safely by semantic-census tooling without replacing that authority.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

TASK_ID = "a784ff872856"
ROOT = find_root(__file__)
TASK_DIR = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

spec = importlib.util.spec_from_file_location(
    f"review_{TASK_ID}_generator", TASK_DIR / "generator.py"
)
assert spec and spec.loader
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

BANDS = (None, "easy", "medium", "hard")


def accepted(result):
    return result is True or result == []


@pytest.fixture(scope="module")
def canonical():
    return canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


@pytest.fixture(scope="module")
def width_vs_area_witness():
    # Width-4 object has five cells; width-2 object has six.  Width-first and
    # cell-count-first therefore disagree while all three objects are lawful.
    return [
        [2, 2, 2, 2, 0, 0, 0, 3, 3, 0],
        [0, 2, 0, 0, 0, 0, 0, 3, 3, 0],
        [0, 0, 0, 0, 0, 0, 0, 3, 3, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [4, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [4, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [4, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]


@pytest.fixture(scope="module")
def height_tie_witness():
    # Width-2 objects have heights 3 and 2.  The intended rule puts the taller
    # crop first; the canonical-fitting shorter-first rival reverses them.
    return [
        [2, 2, 2, 2, 0, 0, 0, 3, 3, 0],
        [0, 2, 0, 0, 0, 0, 0, 3, 3, 0],
        [0, 0, 0, 0, 0, 0, 0, 3, 3, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [4, 4, 0, 0, 0, 0, 0, 0, 0, 0],
        [4, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]


@pytest.fixture(scope="module")
def color_tie_witness():
    # The two width-4, height-2 crops differ only in color ordering.  The
    # intended rule puts color 2 before color 8; the descending-color rival does not.
    return [
        [8, 8, 8, 8, 0, 0, 0, 3, 3, 0],
        [0, 8, 0, 0, 0, 0, 0, 3, 3, 0],
        [0, 0, 0, 0, 0, 0, 0, 3, 3, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [2, 2, 2, 2, 0, 0, 0, 0, 0, 0],
        [0, 2, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]


def test_rule_pin_summary_and_canonical_pairs_are_exact(canonical):
    assert gen.RULE_HASH == "7991026f57da"
    assert "width" in gen.SUMMARY.lower()
    assert "cell count desc" not in gen.SUMMARY.lower()
    assert callable(getattr(gen, "strict_canonical_like", None))
    assert callable(getattr(gen, "rule_mirror", None))
    for pair in canonical:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert accepted(gen.strict_canonical_like(pair["input"]))
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_cell_count_first_is_a_real_canonical_fitting_rival(canonical):
    rival = gen.SEMANTIC_RIVALS["cell_count_first"]
    for pair in canonical:
        original = deepcopy(pair["input"])
        assert rival(pair["input"]) == pair["output"]
        assert pair["input"] == original


EXPECTED_SHORTCUTS = {
    "cell_count_first",
    "height_ascending_on_width_ties",
    "color_descending_on_dimension_ties",
}


def test_all_sort_key_shortcuts_are_declared_and_fit_canonical(canonical):
    assert set(gen.SEMANTIC_RIVALS) == EXPECTED_SHORTCUTS
    assert set(gen.CANONICAL_SHORTCUTS) == EXPECTED_SHORTCUTS
    assert set(gen.LESSON_COMPETITORS) == EXPECTED_SHORTCUTS
    for name, rival in sorted(gen.CANONICAL_SHORTCUTS.items()):
        for pair in canonical:
            original = deepcopy(pair["input"])
            assert rival(pair["input"]) == pair["output"], name
            assert pair["input"] == original


def test_exact_width_vs_area_counterexample(width_vs_area_witness):
    intended = [
        [2, 2, 2, 2],
        [0, 2, 0, 0],
        [0, 0, 0, 0],
        [3, 3, 0, 0],
        [3, 3, 0, 0],
        [3, 3, 0, 0],
        [0, 0, 0, 0],
        [4, 0, 0, 0],
        [4, 0, 0, 0],
        [4, 0, 0, 0],
    ]
    assert gen.self_check(width_vs_area_witness) == []
    assert gen.SEMANTIC_WITNESSES["width_over_cell_count"](
        width_vs_area_witness
    )
    assert gen.rule_mirror(width_vs_area_witness) == intended
    assert gen.SEMANTIC_RIVALS["cell_count_first"](
        width_vs_area_witness
    ) != intended


def test_exact_height_tie_counterexample(height_tie_witness):
    intended = [
        [2, 2, 2, 2],
        [0, 2, 0, 0],
        [0, 0, 0, 0],
        [3, 3, 0, 0],
        [3, 3, 0, 0],
        [3, 3, 0, 0],
        [0, 0, 0, 0],
        [4, 4, 0, 0],
        [4, 0, 0, 0],
    ]
    assert gen.self_check(height_tie_witness) == []
    assert gen.SEMANTIC_WITNESSES["height_descending_on_width_tie"](
        height_tie_witness
    )
    assert gen.rule_mirror(height_tie_witness) == intended
    assert gen.SEMANTIC_RIVALS["height_ascending_on_width_ties"](
        height_tie_witness
    ) != intended
    assert gen.SEMANTIC_RIVALS["color_descending_on_dimension_ties"](
        height_tie_witness
    ) == intended


def test_exact_color_tie_counterexample(color_tie_witness):
    intended = [
        [2, 2, 2, 2],
        [0, 2, 0, 0],
        [0, 0, 0, 0],
        [8, 8, 8, 8],
        [0, 8, 0, 0],
        [0, 0, 0, 0],
        [3, 3, 0, 0],
        [3, 3, 0, 0],
        [3, 3, 0, 0],
    ]
    assert gen.self_check(color_tie_witness) == []
    assert gen.SEMANTIC_WITNESSES["color_ascending_on_dimension_tie"](
        color_tie_witness
    )
    assert gen.rule_mirror(color_tie_witness) == intended
    assert gen.SEMANTIC_RIVALS["color_descending_on_dimension_ties"](
        color_tie_witness
    ) != intended
    assert gen.SEMANTIC_RIVALS["height_ascending_on_width_ties"](
        color_tie_witness
    ) == intended


@pytest.mark.parametrize("band", BANDS)
def test_canonical_inputs_are_not_rejected_by_difficulty(canonical, band):
    for pair in canonical:
        assert gen.self_check(pair["input"], difficulty=band) == []
        assert accepted(gen.strict_canonical_like(pair["input"]))


@pytest.mark.parametrize("band", BANDS)
def test_exact_axis_controls_are_honored_and_observable_in_every_band(band):
    for options in (
        {"grid_h": 7, "grid_w": 9, "n": 3},
        {"grid_h": 7, "grid_w": 9, "n": 4},
        {"grid_h": 14, "grid_w": 16, "n": 3},
        {"grid_h": 14, "grid_w": 16, "n": 4},
    ):
        grid = gen.generate(9182, 17, difficulty=band, **options)
        assert gen.observe_overrides(grid) == options
        assert gen.self_check(grid, difficulty=band) == []
        assert gen.SEMANTIC_WITNESSES["width_over_cell_count"](grid)


@pytest.mark.parametrize(
    "key,value",
    [
        ("grid_h", 6), ("grid_h", 15), ("grid_w", 8), ("grid_w", 17),
        ("n", 2), ("n", 5),
        ("grid_h", True), ("grid_h", 7.0), ("grid_w", "10"), ("n", False),
        ("texture", "default"), ("palette_kind", "warm"),
        ("palette_size", 3), ("n_distinct_colors", 3),
        ("position_bias", "scattered_colored_motifs"),
        ("density", "sparse"), ("unknown_axis", 1),
    ],
)
def test_invalid_or_retired_controls_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("seed,sample_index", [(True, 0), (1.5, 0), ("1", 0), (1, True), (1, -1)])
def test_seed_and_sample_index_are_strict(seed, sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index)


def test_none_override_values_keep_default_semantics():
    assert gen.generate(22, 1, grid_h=None, grid_w=None, n=None) == gen.generate(22, 1)


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 9 for _ in range(7)],
        [[0] * 9],
        [[0] * 9 for _ in range(7)],
        [[0] * 8 + [10] for _ in range(7)],
        ["000000000"] * 7,
    ],
)
def test_malformed_self_check_reports_reasons_without_exception(grid):
    result = gen.self_check(grid)
    assert isinstance(result, list) and result


@pytest.fixture(scope="module")
def default_lessons():
    lessons = {}
    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(761, i, difficulty=band) for i in range(8)]
        lessons[band] = grids
    return lessons


def test_default_lessons_are_deterministic_lawful_and_counterexample_rich(default_lessons):
    for band, grids in default_lessons.items():
        for index, grid in enumerate(grids):
            assert grid == gen.generate(761, index, difficulty=band)
            assert gen.self_check(grid, difficulty=band) == []
            assert gen.SEMANTIC_WITNESSES["width_over_cell_count"](grid)
            assert gen.rule_mirror(grid) != gen.SEMANTIC_RIVALS["cell_count_first"](grid)


@pytest.mark.parametrize(
    "sample_index,expected,unexpected",
    [
        (0, "height_descending_on_width_tie", "color_ascending_on_dimension_tie"),
        (1, "color_ascending_on_dimension_tie", "height_descending_on_width_tie"),
        (2, "height_descending_on_width_tie", "color_ascending_on_dimension_tie"),
        (3, "color_ascending_on_dimension_tie", "height_descending_on_width_tie"),
    ],
)
def test_three_object_schedule_alternates_secondary_key_lessons(
    sample_index, expected, unexpected
):
    grid = gen.generate(991, sample_index, difficulty="easy", n=3)
    assert gen.SEMANTIC_WITNESSES["width_over_cell_count"](grid)
    assert gen.SEMANTIC_WITNESSES[expected](grid)
    assert not gen.SEMANTIC_WITNESSES[unexpected](grid)


def test_four_object_minimum_canvas_combines_all_sort_key_witnesses():
    for band in BANDS:
        for sample_index in range(gen.LESSON_SCHEDULE_PERIOD):
            for seed in range(8):
                grid = gen.generate(
                    seed, sample_index, difficulty=band, grid_h=7, grid_w=9, n=4
                )
                assert gen.observe_overrides(grid) == {"grid_h": 7, "grid_w": 9, "n": 4}
                assert gen.self_check(grid, difficulty=band) == []
                assert all(witness(grid) for witness in gen.SEMANTIC_WITNESSES.values())


def test_schedule_supplies_all_canonical_profiles(default_lessons):
    wanted = {(7, 10, 3), (7, 11, 3), (8, 12, 3)}
    for band, grids in default_lessons.items():
        observed = {
            (len(grid), len(grid[0]), len(gen._object_infos(grid))) for grid in grids
        }
        assert wanted <= observed, (band, observed)


def test_every_three_demo_window_refutes_every_declared_rival(default_lessons):
    assert gen.EXAMPLES_NEEDED == 3
    for band, grids in default_lessons.items():
        outputs = [gen.rule_mirror(grid) for grid in grids]
        for rival_name, rival in sorted(gen.LESSON_COMPETITORS.items()):
            rival_outputs = [rival(grid) for grid in grids]
            for start in range(len(grids) - 3):
                window = range(start, start + 4)
                for query in window:
                    demos = [i for i in window if i != query]
                    assert any(rival_outputs[i] != outputs[i] for i in demos), (
                        band, rival_name, start, query
                    )


def test_real_racket_matches_local_mirror(canonical, width_vs_area_witness, default_lessons):
    grids = [pair["input"] for pair in canonical]
    grids += [width_vs_area_witness]
    grids += default_lessons["medium"][:4]
    applied = Catalog().apply(TASK_ID, grids, timeout=180)
    assert applied["rule_hash_matches_catalog"]
    assert all(r["valid_output"] and r["error"] is None for r in applied["results"])
    for result in applied["results"]:
        assert result["output"] == gen.rule_mirror(result["input"])


def test_declared_schedule_profiles_are_exactly_the_profiles_that_can_be_returned():
    observed = {
        gen.schedule_profile(0, index, difficulty=band)
        for band in ("easy", "medium", "hard")
        for index in range(gen.LESSON_SCHEDULE_PERIOD)
    }
    assert observed == set(gen.SCHEDULE_PROFILES)


def test_reusable_sort_lesson_probe_covers_every_declared_rival():
    probe_path = TASK_DIR / "workspace" / "verify_width_lesson.py"
    assert probe_path.exists(), "authoring probe has not been implemented"
    probe_spec = importlib.util.spec_from_file_location(
        f"review_{TASK_ID}_sort_probe", probe_path
    )
    assert probe_spec and probe_spec.loader
    probe = importlib.util.module_from_spec(probe_spec)
    probe_spec.loader.exec_module(probe)
    report = probe.build_report(run_racket=False)
    assert report["schema"] == "a784ff872856-sort-lesson-probe-v2"
    assert {item["name"] for item in report["canonical_shortcuts"]} == EXPECTED_SHORTCUTS
    assert all(item["fits_all_canonical_pairs"] for item in report["canonical_shortcuts"])
    assert set(report["rival_coverage"]) == EXPECTED_SHORTCUTS
    assert report["missing_rivals"] == []
    assert report["unsupported_rivals"] == []
    assert report["counterexample"]["intended_differs_from_every_declared_rival"]
    assert report["counterexamples"]
    for row in report["counterexamples"]:
        assert row["self_check_errors"] == []
        assert row["recorded_intended_matches_mirror"]
        assert row["recorded_rival_outputs_match"]
    for row in report["rival_coverage"].values():
        assert row["separator_paths"]
        assert row["witness_paths"]
