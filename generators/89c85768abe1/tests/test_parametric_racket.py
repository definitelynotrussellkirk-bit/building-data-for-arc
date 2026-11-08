"""Literal, protected-Racket checks for the fill-then-select rule family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from arcpuzzles.parametric_worker import _local_imports, _real_evaluator


ROOT = Path(__file__).resolve().parents[3]
RULES = ROOT / "generators/89c85768abe1/workspace/parametric/racket_rules.py"


def _load_rules():
    assert RULES.is_file(), "The task-local parametric Racket rules are missing"
    spec = importlib.util.spec_from_file_location("rules_89c85768abe1_literal_tests", RULES)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _grid(*rows):
    return [[int(color) for color in row] for row in rows]


@pytest.fixture(scope="module")
def execute():
    runtime = ROOT / "shared/runtime"
    with _local_imports(runtime, RULES.parent):
        apply, identity, bridge = _real_evaluator(runtime)
        assert identity["backend"] == "racket"
        assert identity["protected"] is True
        try:
            yield apply
        finally:
            bridge.close()


CONTACT_INPUT = _grid(
    "00000000000",
    "02003000000",
    "00020030000",
    "00000000000",
    "04000000000",
    "00000000000",
    "00040000000",
    "00000000000",
)


def test_completion_precedes_multicolor_component_selection(execute):
    # Two touching completed rectangles total 12 cells, exceeding a 9-cell box.
    rules = _load_rules()
    assert execute(rules.variant_program(), CONTACT_INPUT) == _grid(
        "00000000000",
        "02223330000",
        "02223330000",
        "00000000000",
        "00000000000",
        "00000000000",
        "00000000000",
        "00000000000",
    )


def test_select_before_fill_counterfactual_keeps_first_sparse_singleton(execute):
    rules = _load_rules()
    assert execute(rules.counterfactual_program("select_before_fill"), CONTACT_INPUT) == _grid(
        "00000000000",
        "02000000000",
        "00000000000",
        "00000000000",
        "00000000000",
        "00000000000",
        "00000000000",
        "00000000000",
    )


def test_largest_rectangle_counterfactual_drops_larger_multicolor_component(execute):
    rules = _load_rules()
    assert execute(rules.counterfactual_program("largest_rectangle"), CONTACT_INPUT) == _grid(
        "00000000000",
        "00000000000",
        "00000000000",
        "00000000000",
        "04440000000",
        "04440000000",
        "04440000000",
        "00000000000",
    )


@pytest.mark.parametrize("kind,want", [
    ("variant", _grid(
        "00000000000", "00000000000", "00000000000", "00000000000",
        "00000000000", "00000004440", "00000004440", "00000000000",
    )),
    ("eight_connected", _grid(
        "00000000000", "02200000000", "02200000000", "00033000000",
        "00033000000", "00000000000", "00000000000", "00000000000",
    )),
])
def test_diagonal_contact_does_not_join_four_neighbor_components(execute, kind, want):
    rules = _load_rules()
    scene = _grid(
        "00000000000", "02000000000", "00200000000", "00030000000",
        "00003000000", "00000004000", "00000000040", "00000000000",
    )
    program = rules.variant_program() if kind == "variant" else rules.counterfactual_program(kind)
    assert execute(program, scene) == want


@pytest.mark.parametrize("kind", ["variant", "largest_rectangle", "eight_connected"])
def test_equal_sizes_choose_earliest_row_major_component_not_lowest_color(execute, kind):
    rules = _load_rules()
    scene = _grid(
        "000000900", "000009000", "000000000", "000000000",
        "200000000", "020000000", "000000000",
    )
    want = _grid(
        "000009900", "000009900", "000000000", "000000000",
        "000000000", "000000000", "000000000",
    )
    program = rules.variant_program() if kind == "variant" else rules.counterfactual_program(kind)
    assert execute(program, scene) == want


@pytest.mark.parametrize("kind", ["variant", "select_before_fill", "largest_rectangle", "eight_connected"])
def test_empty_foreground_is_total(execute, kind):
    rules = _load_rules()
    scene = _grid("000", "000")
    program = rules.variant_program() if kind == "variant" else rules.counterfactual_program(kind)
    assert execute(program, scene) == scene


def test_unknown_counterfactual_is_rejected():
    rules = _load_rules()
    with pytest.raises(ValueError):
        rules.counterfactual_program("unknown")
