"""Executed counterfactual evidence, independent of the adapter sampler."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from arcpuzzles.parametric_worker import _real_evaluator
from reviewer_support import find_root, load_selected_generator


ROOT = find_root(__file__)
HOME = ROOT / "generators/0ee358bd9d75/workspace/parametric"


def load_helper():
    path = HOME / "verify_causal.py"
    assert path.is_file(), "Missing reusable protected-Racket causal witness helper"
    spec = importlib.util.spec_from_file_location("section_causal_verifier", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_wrong_partition_changes_colors_without_changing_output_shape():
    helper = load_helper()
    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    try:
        assert identity["backend"] == "racket" and identity["protected"]
        grid = [
            [1, 1, 0, 0, 3, 3, 0, 3],
            [1, 0, 1, 0, 4, 0, 3, 3],
            [2, 2, 1, 0, 3, 4, 3, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [5, 5, 0, 0, 7, 7, 7, 0],
            [6, 5, 5, 0, 8, 7, 0, 7],
            [0, 6, 5, 0, 7, 0, 8, 7],
            [5, 0, 5, 0, 0, 8, 7, 7],
        ]
        program = (HOME / "programs/least_frequent.rkt").read_text()
        case = helper.find_counterfactual(program, grid, {"selection": "least_frequent"}, apply)
        assert case["output"] == [[2, 4], [6, 8]]
        assert case["counterfactual_output"] != case["output"]
        assert [len(row) for row in case["counterfactual_output"]] == [2, 2]
        assert apply(case["program"], grid) == case["output"]
        assert apply(case["counterfactual_program"], grid) == case["counterfactual_output"]
        assert case["intermediate_value"]["actual_zero_rows"] == [3]
        assert case["intermediate_value"]["actual_zero_cols"] == [3]
    finally:
        bridge.close()


def test_missing_partition_binding_is_rejected():
    helper = load_helper()
    with pytest.raises(ValueError, match="binding"):
        helper.replace_binding("(rule! (lambda (g) g))", "zero-rows", "(list 2)")


def test_no_changed_output_is_not_reported_as_a_witness():
    helper = load_helper()
    grid = [[1 if r != 3 and c != 3 else 0 for c in range(8)] for r in range(8)]
    program = (HOME / "programs/most_frequent.rkt").read_text()
    apply, _, bridge = _real_evaluator(ROOT / "shared/runtime")
    try:
        with pytest.raises(ValueError, match="changed-color"):
            helper.find_counterfactual(program, grid, {"selection": "most_frequent"}, apply)
    finally:
        bridge.close()


def test_repeated_color_excludes_a_fixed_output_color_remap():
    helper = load_helper()
    assert hasattr(helper, "CAUSAL_INPUT"), "Need the strong same-shape repeated-color witness"
    generator, _, _ = load_selected_generator("0ee358bd9d75", root=ROOT)
    assert generator.self_check(helper.CAUSAL_INPUT) == []
    apply, _, bridge = _real_evaluator(ROOT / "shared/runtime")
    try:
        program = (HOME / "programs/most_frequent.rkt").read_text()
        case = helper.find_counterfactual(program, helper.CAUSAL_INPUT, {"selection": "most_frequent"}, apply)
        assert case["output"] == [[1, 5], [5, 7]]
        assert case["counterfactual_output"] == [[5, 7], [5, 7]]
        # The same original 5 maps to both 7 and 5: no per-color lookup can do this.
        assert case["counterfactual_output"][0][1] != case["counterfactual_output"][1][0]
        assert case["intermediate_value"]["counterfactual_dividers"] == [5]
    finally:
        bridge.close()
