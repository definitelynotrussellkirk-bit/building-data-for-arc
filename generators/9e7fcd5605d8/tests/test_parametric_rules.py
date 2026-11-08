"""Literal, protected-Racket checks for the task's finite hole-count rules."""
from __future__ import annotations

from functools import lru_cache
import importlib.util
from pathlib import Path
import sys

import pytest


HOME = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "shared/runtime"))


@lru_cache(maxsize=1)
def _rules():
    path = HOME / "workspace/parametric/rules.py"
    assert path.is_file(), "The task-local hole-count rule builder is missing"
    spec = importlib.util.spec_from_file_location("task_9e7fcd5605d8_parametric_rules", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def apply_rule():
    from arcpuzzles.parametric_worker import _real_evaluator

    apply, identity, bridge = _real_evaluator(REPO / "shared/runtime")
    assert identity["backend"] == "racket"
    assert identity["protected"] is True
    try:
        yield apply
    finally:
        bridge.close()


# All seven foreground shapes are single 4-connected components.  The expected
# region counts below are literal hand checks, independent of the rule builder.
SHAPES = {
    "open_u": ("101", "101", "111"),
    "large_one_hole": ("11111", "10001", "10001", "10001", "11111"),
    "diagonal_two_holes": ("1111", "1011", "1101", "1111"),
    "three_holes": ("1111111", "1010101", "1111111"),
    "hole_and_open_bay": ("111111", "101001", "111001", "111000"),
    "corner_gap": ("011", "101", "111"),
    "single_cell_hole": ("111", "101", "111"),
}


def _grid(name, foreground=2):
    return [[foreground if cell == "1" else 0 for cell in row] for row in SHAPES[name]]


def _expected(name, color):
    return [[color if cell == "1" else 0 for cell in row] for row in SHAPES[name]]


@pytest.mark.parametrize(
    "name,threshold,want",
    [
        ("open_u", 1, 4), ("open_u", 2, 4),
        ("large_one_hole", 1, 8), ("large_one_hole", 2, 4),
        ("diagonal_two_holes", 1, 8), ("diagonal_two_holes", 2, 8),
        ("three_holes", 1, 8), ("three_holes", 2, 8),
        ("hole_and_open_bay", 1, 8), ("hole_and_open_bay", 2, 4),
        ("corner_gap", 1, 8), ("corner_gap", 2, 4),
        ("single_cell_hole", 1, 8), ("single_cell_hole", 2, 4),
    ],
)
def test_region_thresholds_on_literal_components(apply_rule, name, threshold, want):
    assert apply_rule(_rules().count_rule(threshold), _grid(name)) == _expected(name, want)


@pytest.mark.parametrize(
    "name,threshold,options,want",
    [
        ("open_u", 1, {"include_exterior": True}, 8),
        ("hole_and_open_bay", 2, {"include_exterior": True}, 8),
        ("large_one_hole", 2, {"score": "cells"}, 8),
        ("hole_and_open_bay", 2, {"score": "cells"}, 4),
        ("open_u", 2, {"score": "missing"}, 8),
        ("single_cell_hole", 2, {"score": "missing"}, 4),
        ("diagonal_two_holes", 2, {"connectivity": 8}, 4),
        ("corner_gap", 1, {"connectivity": 8}, 4),
        ("three_holes", 2, {"exact": True}, 4),
        ("diagonal_two_holes", 2, {"exact": True}, 8),
        ("three_holes", 3, {}, 8),
    ],
)
def test_options_separate_topology_and_cell_count(apply_rule, name, threshold, options, want):
    program = _rules().count_rule(threshold, **options)
    assert apply_rule(program, _grid(name)) == _expected(name, want)


def test_each_same_color_component_is_recolored_without_filling_background(apply_rule):
    grid = [[2, 2, 2, 3, 0, 0], [2, 0, 2, 3, 0, 5], [2, 2, 2, 3, 0, 5]]
    want = [[8, 8, 8, 4, 0, 0], [8, 0, 8, 4, 0, 4], [8, 8, 8, 4, 0, 4]]
    assert apply_rule(_rules().count_rule(1), grid) == want
    assert grid == [[2, 2, 2, 3, 0, 0], [2, 0, 2, 3, 0, 5], [2, 2, 2, 3, 0, 5]]


@pytest.mark.parametrize("color", [4, 8])
def test_constant_rivals_preserve_the_foreground_footprint(apply_rule, color):
    assert apply_rule(_rules().count_rule(2, constant=color), _grid("open_u")) == _expected("open_u", color)


def test_empty_foreground_and_filled_components_are_total(apply_rule):
    assert apply_rule(_rules().count_rule(1), [[0, 0], [0, 0]]) == [[0, 0], [0, 0]]
    assert apply_rule(_rules().count_rule(1), [[7]]) == [[4]]
    assert apply_rule(_rules().count_rule(1), [[7, 7], [7, 7]]) == [[4, 4], [4, 4]]


@pytest.mark.parametrize(
    "threshold,options",
    [
        (True, {}), (1.0, {}), ("1", {}), (0, {}), (-1, {}),
        (1, {"connectivity": True}), (1, {"connectivity": 4.0}),
        (1, {"connectivity": 6}), (1, {"include_exterior": 1}),
        (1, {"include_exterior": None}), (1, {"exact": 0}),
        (1, {"score": "area"}), (1, {"score": None}),
        (1, {"constant": True}), (1, {"constant": 4.0}),
        (1, {"constant": 0}), (1, {"constant": 9}),
    ],
)
def test_invalid_builder_options_are_rejected(threshold, options):
    with pytest.raises(ValueError):
        _rules().count_rule(threshold, **options)


@pytest.mark.parametrize("settings", [None, {}, {"min_holes": True}, {"min_holes": 1.0},
                                     {"min_holes": 3}, {"min_holes": 1, "other": 2}])
def test_invalid_rival_settings_are_rejected(settings):
    with pytest.raises(ValueError):
        _rules().rival_programs(settings)


# Signature order is SHAPES insertion order.  These literal colors detect
# threshold, connectivity, rim filtering, cell-vs-region, and exactness errors.
RIVAL_SIGNATURES = {
    1: {
        "wrong_threshold": (4, 4, 8, 8, 4, 4, 4),
        "bbox_nonfull": (8, 8, 8, 8, 8, 8, 8),
        "hole_cell_threshold": (4, 8, 8, 8, 8, 8, 8),
        "including_exterior": (8, 8, 8, 8, 8, 8, 8),
        "eight_connected_holes": (4, 8, 8, 8, 8, 4, 8),
        "exactly_threshold": (4, 8, 4, 4, 8, 8, 8),
        "all_foreground_4": (4, 4, 4, 4, 4, 4, 4),
        "all_foreground_8": (8, 8, 8, 8, 8, 8, 8),
    },
    2: {
        "wrong_threshold": (4, 8, 8, 8, 8, 8, 8),
        "bbox_nonfull": (8, 8, 8, 8, 8, 8, 8),
        "missing_cell_threshold": (8, 8, 8, 8, 8, 8, 4),
        "hole_cell_threshold": (4, 8, 8, 8, 4, 4, 4),
        "including_exterior": (4, 4, 8, 8, 8, 8, 4),
        "eight_connected_holes": (4, 4, 4, 8, 4, 4, 4),
        "exactly_threshold": (4, 4, 8, 4, 4, 4, 4),
        "all_foreground_4": (4, 4, 4, 4, 4, 4, 4),
        "all_foreground_8": (8, 8, 8, 8, 8, 8, 8),
    },
}


@pytest.mark.parametrize("threshold", [1, 2])
def test_rivals_have_literal_signatures_and_no_duplicate_programs(apply_rule, threshold):
    programs = _rules().rival_programs({"min_holes": threshold})
    assert set(programs) == set(RIVAL_SIGNATURES[threshold])
    assert len(set(programs.values())) == len(programs)
    assert _rules().count_rule(threshold) not in programs.values()
    for rival, program in programs.items():
        for name, want in zip(SHAPES, RIVAL_SIGNATURES[threshold][rival]):
            assert apply_rule(program, _grid(name)) == _expected(name, want), (threshold, rival, name)
