"""Independent semantic fixtures and protected-Racket rival parity.

These tests do not import the episode prototype.  Discovery supports both the
source checkout and the native staged task-test layout.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "40e85135fbf8"
ROOT = find_root(__file__)
SOURCE = next(path for path in (
    ROOT / "generators" / TASK_ID / "workspace/parametric/rivals.py",
    ROOT / "puzzle_generators/per_puzzle" / TASK_ID / "workspace/parametric/rivals.py",
) if path.is_file())
SPEC = importlib.util.spec_from_file_location("independent_header_rivals_tests", SOURCE)
assert SPEC and SPEC.loader
rivals = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rivals)


def _frozen(value):
    return json.dumps(value, separators=(",", ":"))


def test_hand_labels_establish_literal_equality_and_global_all_ties():
    fixtures = rivals.fixtures()
    for mode in rivals.MODES:
        assert rivals.intended(fixtures["minimum_match"], mode) == [[2]]
        assert rivals.intended(fixtures["minimum_no_match"], mode) == [[0]]
    fragmented = fixtures["fragmented_total_loses"]
    expected = [[3 if row >= 5 and col >= 5 else 0 for col in range(7)] for row in range(7)]
    assert rivals.intended(fragmented, "largest_blocks") == expected
    cross = fixtures["cross_run_product"]
    assert rivals.intended(cross, "largest_blocks") == [
        [0, 0, 1, 1, 1], [0, 0, 1, 1, 1], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]
    tied = rivals.feature_summary(fixtures["same_color_four_ties"])
    assert tied["largest_component_size"] == 6
    assert tied["largest_component_count"] == 4
    assert tied["retained_nonzero_cells"] == 24


def test_strict_header_grammar_rejects_types_bounds_and_malformed_frames():
    base = [[0, 2, 3], [2, 0, 0], [3, 0, 0]]
    invalid = [None, (), [], [[0, 2]], [[0], [2]], ((0, 2), (2, 0)),
               [[0, 2], (2, 0)], [[0, 2], [2]], [[0, 2], [2, 0, 0]],
               [[0, 0], [2, 0]], [[0, 2], [0, 0]], [[1, 2], [2, 0]],
               [[0, 2], [2, 1]], [[0, 10], [2, 0]], [[0, -1], [2, 0]],
               [[0, 2.0], [2, 0]], [[False, 2], [2, 0]], [[0, True], [2, 0]],
               [[0, 2], [2, False]], [[0] + [2] * 30, [2] + [0] * 30],
               [[0, 2]] + [[2, 0] for _ in range(30)]]
    for grid in invalid:
        for mode in rivals.MODES:
            with pytest.raises(ValueError):
                rivals.intended(grid, mode)
    before = copy.deepcopy(base)
    rivals.intended(base, "largest_blocks")
    assert base == before
    for mode in (None, True, 0, "largest", {}):
        with pytest.raises(ValueError):
            rivals.bank(mode)


def test_independent_first_stage_matches_all_canonical_labels():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        assert rivals.intended(pair["input"], "all_matches") == pair["output"]


def test_no_counted_connectivity_or_rectangle_aliases_and_all_rivals_are_wrong():
    grids = list(rivals.fixtures().values())
    for mode in rivals.MODES:
        predictions = {name: tuple(_frozen(fn(grid)) for grid in grids)
                       for name, fn in rivals.bank(mode).items()}
        correct = tuple(_frozen(rivals.intended(grid, mode)) for grid in grids)
        assert correct not in predictions.values()
        reverse = {}
        for name, signature in predictions.items():
            assert signature not in reverse, (mode, reverse.get(signature), name)
            reverse[signature] = name
    for grid in grids:
        matrix = rivals.intended(grid, "all_matches")
        four = {frozenset(obj) for obj in rivals.components(matrix)}
        eight = {frozenset(obj) for obj in rivals.components(matrix, diagonal=True)}
        binary_four = {frozenset(obj) for obj in rivals.components(matrix, monochromatic=False)}
        assert four == eight == binary_four
        for component in four:
            rows, cols = {r for r, _ in component}, {c for _, c in component}
            assert len(component) == (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def test_lawful_transpose_header_reversals_and_color_permutation():
    permutation = [0, 8, 3, 7, 2, 9, 4, 1, 6, 5]
    for grid in rivals.fixtures().values():
        rows, cols = rivals.headers(grid)
        transforms = [
            (rivals.from_headers(cols, rows), lambda output: [list(row) for row in zip(*output)]),
            (rivals.from_headers(rows[::-1], cols), lambda output: output[::-1]),
            (rivals.from_headers(rows, cols[::-1]), lambda output: [row[::-1] for row in output]),
            ([[permutation[value] for value in row] for row in grid],
             lambda output: [[permutation[value] for value in row] for row in output]),
        ]
        for mode in rivals.MODES:
            original = rivals.intended(grid, mode)
            for transformed, output_transform in transforms:
                assert rivals.intended(transformed, mode) == output_transform(original)
    stress = rivals.feature_summary(rivals.fixtures()["maximum_30"])
    assert stress["input_shape"] == [30, 30]
    assert stress["output_shape"] == [29, 29]
    assert stress["nonzero_header_cells"] == 58
    assert stress["input_interior_nonzero"] == 0
    assert stress["equality_nonzero_cells"] >= 100
    assert stress["equality_component_count"] >= 10


@pytest.fixture(scope="module")
def protected_evaluator():
    from arcpuzzles.parametric_worker import _local_imports as protected_local_imports, _real_evaluator
    runtime = ROOT / "shared/runtime" if (ROOT / "shared/runtime/arc_repl").is_dir() else ROOT
    with protected_local_imports(runtime, SOURCE.parent):
        apply, identity, bridge = _real_evaluator(runtime)
        assert identity["backend"] == "racket" and identity["protected"] is True
        try:
            yield apply
        finally:
            bridge.close()


def test_independent_complete_programs_match_protected_racket(protected_evaluator):
    fixtures = rivals.fixtures()
    for mode in rivals.MODES:
        source = rivals.racket(mode)
        for name, grid in fixtures.items():
            assert protected_evaluator(source, grid) == rivals.intended(grid, mode), (mode, name)
        for name, predict in rivals.bank(mode).items():
            source = rivals.racket(mode, name)
            witness = next(grid for grid in fixtures.values()
                           if predict(grid) != rivals.intended(grid, mode))
            for grid in (witness, fixtures["minimum_no_match"]):
                assert protected_evaluator(source, grid) == predict(grid), (mode, name, grid)
    canonical = SOURCE.with_name("canonical.rkt").read_bytes()
    assert hashlib.sha256(rivals.racket("all_matches").encode()).digest() == hashlib.sha256(canonical).digest()
