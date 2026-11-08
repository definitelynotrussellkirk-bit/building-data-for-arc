"""Small regressions first reproduced against the packet's 2.1.0 source."""
import importlib.util
from pathlib import Path

import pytest


def _load():
    spec = importlib.util.spec_from_file_location("stamp_smoke", Path(__file__).parents[1] / "generator.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_unknown_axis_is_rejected():
    with pytest.raises(ValueError):
        _load().generate(0, 0, misspelled_region_count=2)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_advertised_minimum_height_is_usable_in_every_band(band):
    generator = _load()
    grid = generator.generate(0, 0, difficulty=band, grid_h=9)
    assert len(grid) == 9
    assert not generator.self_check(grid, difficulty=band)


def test_source_authority_is_pinned():
    assert getattr(_load(), "RULE_HASH", None) == "c86839f15a5d"


@pytest.mark.parametrize("surplus_pin", [{}, {"extra_rows": 0}, {"extra_cols": 0}])
def test_feasible_tight_layout_can_disable_unpinned_surplus(surplus_pin):
    generator = _load()
    seed = next(s for s in range(20) if generator.schedule_profile(s, 0) == "extension")
    grid = generator.generate(seed, 0, grid_h=9, grid_w=9,
                              template_h=4, template_w=4, region_count=3,
                              **surplus_pin)
    observed = generator.observe_overrides(grid)
    assert observed["extra_rows"] == observed["extra_cols"] == 0
    assert observed["region_count"] == 3
    assert not generator.self_check(grid)
