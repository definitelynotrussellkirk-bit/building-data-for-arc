"""Small regression tests for the reusable review helpers."""
import importlib.util
from pathlib import Path
import sys

import pytest

WORK = Path(__file__).resolve().parents[1] / "workspace"


def load(name):
    spec = importlib.util.spec_from_file_location(name, WORK / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


probe = load("review_probe")
audit = load("audit_probe")


def test_fingerprints_are_key_order_independent():
    assert probe.fingerprint({"x": 1, "y": 2}) == probe.fingerprint({"y": 2, "x": 1})
    assert probe.fingerprint([[1, 2]]) != probe.fingerprint([[2, 1]])


def test_racket_grid_literal():
    assert probe.literal([[0, 2], [1, 9]]) == "'((0 2) (1 9))"


@pytest.mark.parametrize("value", [{"input": [[0]], "output": [[1]]}, [{"input": [[0]], "output": [[1]]}]])
def test_canonical_pairs_support_both_repository_encodings(value):
    assert probe.canonical_pairs(value) == [{"input": [[0]], "output": [[1]]}]


@pytest.mark.parametrize("value", ["bad", [{"input": [[0]]}]])
def test_bad_authoring_pair_fails_loud(value):
    with pytest.raises(ValueError):
        probe.canonical_pairs(value)


def test_four_rotations_restore_a_shape():
    points = [(0, 0), (1, 0), (1, 1)]
    rotated = points
    for _ in range(4):
        rotated = audit.rotated(rotated)
    assert rotated == sorted(points)


def test_rectangle_priority_really_changes_overlap():
    grid = [[0] * 5 for _ in range(5)]
    grid[0][0] = grid[3][3] = 2
    grid[1][1] = grid[4][4] = 1
    forward = audit.rectangle_rule(grid)
    backward = audit.rectangle_rule(grid, (1, 2))
    assert forward[1][3] == 8 and backward[1][3] == 3
