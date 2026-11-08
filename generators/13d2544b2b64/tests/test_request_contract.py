"""Regressions for request identity, sparse support, and declared schedule."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "13d2544b2b64"


@pytest.fixture(scope="module")
def generator():
    return load_selected_generator(TASK_ID, root=find_root(__file__))[0]


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
@pytest.mark.parametrize("entrypoint", ("generate", "schedule_profile"))
@pytest.mark.parametrize(
    "axis,value",
    [("seed", x) for x in (True, False, 1.0, 1.75, "1")]
    + [("sample_index", x) for x in (True, False, 1.0, 1.75, "1", -1)],
)
def test_request_identity_never_coerces_invalid_scalars(generator, band, entrypoint, axis, value):
    seed = value if axis == "seed" else 991
    index = value if axis == "sample_index" else 0
    with pytest.raises((TypeError, ValueError), match=axis):
        getattr(generator, entrypoint)(seed, index, difficulty=band)


def test_profile_override_does_not_bypass_request_validation(generator):
    for profile in generator.SCENE_PROFILES:
        for seed, index, name in ((True, 0, "seed"), (17, 1.75, "sample_index"),
                                  (17, -1, "sample_index")):
            with pytest.raises((TypeError, ValueError), match=name):
                generator.generate(seed, index, scene_profile=profile)


@pytest.mark.parametrize("seed", (0, -17, 2**100))
def test_literal_integer_seeds_remain_deterministic(generator, seed):
    first = generator.generate(seed, 0, difficulty="medium")
    assert first == generator.generate(seed, 0, difficulty="medium")
    assert generator.self_check(first) == []


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_ordinary_controls_include_canonical_training_marker_density(generator, band):
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
    marker_count = lambda grid: sum(value not in (0, 1) for row in grid for value in row)
    canonical_counts = {marker_count(pair["input"]) for pair in pairs if pair["split"] == "train"}
    grids = [generator.generate(seed, 0, difficulty=band, scene_profile="canonical_controls")
             for seed in range(20)]
    observed = {marker_count(grid) for grid in grids}
    assert canonical_counts & observed, (canonical_counts, observed)


def test_sparse_controls_keep_both_branches_and_all_outer_target_sides(generator):
    outer_sides = set()
    for seed in range(80):
        grid = generator.generate(seed, 0, scene_profile="canonical_controls")
        facts = generator.analyze_grid(grid)
        assert facts["horizontal_change_count"] >= 1
        assert facts["vertical_change_count"] >= 1
        assert facts["outer_change_count"] >= 1
        assert facts["one_sided_counterexample_count"] >= 1
        for r, row in enumerate(facts["output"]):
            for c, value in enumerate(row):
                if value != grid[r][c]:
                    if r < 2:
                        outer_sides.add("top")
                    elif r > 5:
                        outer_sides.add("bottom")
                    elif c < 2:
                        outer_sides.add("left")
                    elif c > 5:
                        outer_sides.add("right")
    assert outer_sides == {"top", "bottom", "left", "right"}


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_controls_include_canonical_shared_source_topology(generator, band):
    # Canonical examples reuse a corner source for two perpendicular outer
    # fills. Independent pairs alone lose that reasoning structure.
    facts = [generator.analyze_grid(generator.generate(
        seed, 0, difficulty=band, scene_profile="canonical_controls"))
        for seed in range(40)]
    assert any(f["outer_change_count"] >= 2 and f["center_change_count"] >= 1
               and f["marker_count"] == 5 for f in facts)
    assert {2, 3} <= {f["changed_count"] for f in facts}


def test_declared_period_matches_all_four_profile_windows(generator):
    period = getattr(generator, "LESSON_SCHEDULE_PERIOD", None)
    assert type(period) is int and period > 0, "explicit positive schedule period required"
    assert period == len(generator.SCENE_PROFILES)
    for band in ("easy", "medium", "hard"):
        for seed in (0, 17, -3):
            for start in range(4 * period):
                window = [generator.schedule_profile(seed, start + offset, band)
                          for offset in range(period)]
                assert set(window) == set(generator.SCENE_PROFILES)
                assert generator.schedule_profile(seed, start + period, band) == window[0]


def test_teaching_count_is_readable_without_executing_generator_source(generator):
    # Solve preparation reads this declaration with ast.literal_eval so it can
    # enforce the teaching minimum before importing any reviewer source.
    declaration = next(node for node in ast.parse(Path(generator.__file__).read_text()).body
                       if isinstance(node, ast.Assign)
                       and any(isinstance(target, ast.Name) and target.id == "EXAMPLES_NEEDED"
                               for target in node.targets))
    try:
        count = ast.literal_eval(declaration.value)
    except (TypeError, ValueError) as exc:
        raise AssertionError("EXAMPLES_NEEDED must be a literal for solve preparation") from exc
    assert type(count) is int and 1 <= count <= 32
    assert count == len(generator.SCENE_PROFILES)
