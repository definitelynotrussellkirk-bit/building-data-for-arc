from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK = "67504673cd7c"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)


def _load():
    spec = importlib.util.spec_from_file_location("generator_675_under_test", HOME / "generator.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load()


def _anchor_count(grid):
    return sum(value not in (0, 5) for row in grid for value in row)


def _template_size(grid):
    return sum(value == 5 for row in grid for value in row)


def test_rule_hash_is_pinned_and_canonical_inputs_are_owned():
    assert gen.RULE_HASH == "35ef1014dd1e"
    for pair in canonical_pairs(TASK, root=ROOT):
        assert gen.self_check(pair["input"]) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("anchors", [2, 5])
@pytest.mark.parametrize("size", [3, 6])
def test_exact_axes_are_realized_in_every_band(band, anchors, size):
    grid = gen.generate(
        23,
        9,
        difficulty=band,
        grid_h=12,
        grid_w=14,
        num_anchors=anchors,
        template_size=size,
    )
    assert gen.self_check(grid) == []
    assert (len(grid), len(grid[0])) == (12, 14)
    assert _anchor_count(grid) == anchors
    assert _template_size(grid) == size
    assert gen.observe_overrides(grid) == {
        "grid_h": 12,
        "grid_w": 14,
        "num_anchors": anchors,
        "template_size": size,
    }


def test_num_anchor_override_changes_the_returned_scene():
    two = gen.generate(0, 0, num_anchors=2)
    five = gen.generate(0, 0, num_anchors=5)
    assert _anchor_count(two) == 2
    assert _anchor_count(five) == 5
    assert two != five


def test_each_band_has_a_deterministic_canonical_profile_anchor():
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]), len({v for row in pair["input"] for v in row}))
        for pair in canonical_pairs(TASK, root=ROOT)
    }
    for band in ("easy", "medium", "hard"):
        hits = 0
        for index in range(20):
            grid = gen.generate(997, index, difficulty=band)
            profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
            hits += profile in canonical_profiles
        assert hits >= 1


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown": 1},
        {"grid_h": 7},
        {"grid_w": 9},
        {"num_anchors": 1},
        {"num_anchors": 6},
        {"template_size": 2},
        {"template_size": 7},
        {"num_anchors": True},
        {"template_size": "3"},
    ],
)
def test_invalid_controls_fail_closed(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


def test_declared_anchor_only_rival_is_refuted_by_every_generated_example():
    for band in ("easy", "medium", "hard"):
        for index in range(8):
            grid = gen.generate(300 + index, index, difficulty=band)
            assert gen.SEMANTIC_WITNESSES["multi_cell_template"](grid)
            assert gen.SEMANTIC_RIVALS["anchors_only"](grid) != gen.rule_mirror(grid)
