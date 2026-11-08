"""Contract regressions for the selected canonical generator, not variants."""
from __future__ import annotations

import pytest

from reviewer_support import find_root, load_selected_generator


GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(
    "806425ca81b3", root=find_root(__file__)
)


@pytest.mark.parametrize("value", [True, 0.0, "0", None, [], {}])
def test_seed_and_sample_index_require_literal_integers(value):
    with pytest.raises((ValueError, TypeError)):
        GEN.generate(value, 0)
    with pytest.raises((ValueError, TypeError)):
        GEN.generate(0, value)


def test_negative_sample_index_is_rejected():
    with pytest.raises((ValueError, TypeError)):
        GEN.generate(0, -1)


@pytest.mark.parametrize("axis,integer", [("grid_h", 10), ("grid_w", 10), ("active_rows", 3)])
@pytest.mark.parametrize("kind", ["float", "fraction", "string", "true", "false"])
def test_integer_controls_never_coerce_nonintegers(axis, integer, kind):
    values = {"float": float(integer), "fraction": integer + 0.75,
              "string": str(integer), "true": True, "false": False}
    with pytest.raises((ValueError, TypeError)):
        GEN.generate(17, 2, difficulty="hard", **{axis: values[kind]})


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_public_schedule_profile_replays_as_the_observed_axis(band):
    for seed in (0, 17, 90210):
        for index in range(8):
            name = GEN.schedule_profile(seed, index, difficulty=band)
            assert name in GEN.SCENE_PROFILES
            original = GEN.generate(seed, index, difficulty=band)
            replay = GEN.generate(seed, index, difficulty=band, scene_profile=name)
            assert GEN.observe_overrides(original)["scene_profile"] == name
            assert replay == original


def test_public_schedule_repeats_every_four_samples():
    assert len(GEN.SCHEDULE_PROFILES) == 4
    for index in range(12):
        assert GEN.schedule_profile(0, index) == GEN.schedule_profile(0, index + 4)


@pytest.mark.parametrize("bad", [True, 2.0, "2", [2], {"color": 2}, None])
def test_validator_reports_malformed_color_without_raising(bad):
    grid = [[0] * 9 for _ in range(8)]
    grid[3][1] = grid[3][6] = bad
    errors = GEN.self_check(grid)
    assert isinstance(errors, list)
    assert errors, "malformed ARC colors must be rejected"


def test_legal_integer_controls_remain_exact():
    requested = {"grid_h": 10, "grid_w": 12, "active_rows": 3,
                 "scene_profile": "mixed_disjoint"}
    grid = GEN.generate(0, 0, difficulty="hard", **requested)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == requested
