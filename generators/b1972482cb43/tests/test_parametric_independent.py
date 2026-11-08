"""Literal geometry checks for the opt-in reflection family.

Expected grids are authored independently of prototype.predict. Odd block
expansion and canvas flips exercise the constructive witnesses' boundary,
interior, and equal-span cases without reproducing their reflection algorithm.
These expectations are test oracles, not exported reference labels.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def prototype():
    path = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"
    spec = importlib.util.spec_from_file_location("_independent_reflection_review", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Input, canonical output, echo output. All coordinates are zero based.
LITERAL_CASES = (
    (
        [[0, 0, 0, 0, 0], [0, 3, 9, 0, 0], [3, 3, 3, 0, 0], [0, 3, 0, 0, 0]],
        [[0, 0, 3, 3, 3], [0, 3, 9, 3, 0], [3, 3, 3, 0, 0], [0, 3, 0, 0, 0]],
        [[3, 3, 3, 3, 3], [0, 3, 9, 3, 0], [3, 3, 3, 0, 0], [0, 3, 0, 0, 0]],
    ),
    (
        [[0, 0, 0, 0, 0], [0, 0, 0, 3, 3], [0, 0, 9, 0, 3], [0, 0, 0, 0, 0]],
        [[0, 0, 0, 0, 0], [0, 0, 0, 3, 3], [3, 0, 9, 0, 3], [3, 3, 0, 0, 0]],
        [[0, 0, 0, 0, 0], [3, 3, 0, 3, 3], [3, 0, 9, 0, 3], [3, 3, 0, 0, 0]],
    ),
    (
        [[0, 0, 0, 0, 0], [0, 9, 3, 0, 0], [0, 0, 3, 0, 0], [0, 0, 3, 3, 0]],
        [[3, 0, 0, 0, 0], [3, 9, 3, 0, 0], [0, 0, 3, 0, 0], [0, 0, 3, 3, 0]],
        [[3, 0, 0, 0, 0], [3, 9, 3, 0, 0], [3, 0, 3, 0, 0], [0, 0, 3, 3, 0]],
    ),
)


def _expand_literal(grid, h, w, scale, lr, ud):
    output = [[0] * (w * scale) for _ in range(h * scale)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 9:
                output[r * scale + scale // 2][c * scale + scale // 2] = 9
            elif value:
                for dr in range(scale):
                    for dc in range(scale):
                        output[r * scale + dr][c * scale + dc] = value
    if lr:
        output = [row[::-1] for row in output]
    if ud:
        output = output[::-1]
    return output


@pytest.mark.parametrize("case_index", range(3))
def test_literal_outputs_survive_odd_scaling_padding_and_all_flips(prototype, case_index):
    source, point, echo = LITERAL_CASES[case_index]
    for h, w in ((4, 5), (5, 7)):
        for scale in (1, 3):
            for lr, ud in ((False, False), (False, True), (True, False), (True, True)):
                grid = prototype._fixture(case_index, 3, scale, h, w, lr, ud)
                recipe = (case_index, h, w, scale, lr, ud)
                assert grid == _expand_literal(source, h, w, scale, lr, ud), recipe
                assert not prototype.validate_grid(grid), recipe
                for rule, expected in (("point", point), ("visible_span_echo", echo)):
                    assert prototype.predict(grid, {"rule": rule}) == _expand_literal(
                        expected, h, w, scale, lr, ud
                    ), (recipe, rule)


def test_clipped_tall_witness_rejects_restoring_invisible_stage_a_cells(prototype):
    source, _, expected = LITERAL_CASES[2]
    actual = prototype.predict(source, {"rule": "visible_span_echo"})
    unfiltered = prototype.predict(source, {"rule": "visible_span_echo"}, "unclipped_echo")
    assert actual == expected
    assert actual[2][0] == 3
    assert actual[3][0] == 0
    assert unfiltered[3][0] == 3


def test_maximum_seed_preserves_prefixes_across_all_demo_counts_and_settings(prototype):
    seed = 2**63 - 1
    reference = prototype.generate(seed, {"rule": "point"}, 6, 4)
    demo_inputs = [pair["input"] for pair in reference["train"]]
    query_inputs = [pair["input"] for pair in reference["test"]]
    for rule in ("point", "visible_span_echo"):
        for demos in (3, 4, 5, 6):
            full = prototype.generate(seed, {"rule": rule}, demos, 4)
            first = prototype.generate(seed, {"rule": rule}, demos, 1)
            assert [pair["input"] for pair in full["train"]] == demo_inputs[:demos]
            assert [pair["input"] for pair in full["test"]] == query_inputs
            assert first["train"] == full["train"]
            assert first["test"] == full["test"][:1]
