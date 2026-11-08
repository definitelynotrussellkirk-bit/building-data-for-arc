"""Regressions for underdetermined transform-key lessons, using literal labels."""
import importlib.util

import pytest
from reviewer_support import canonical_pairs, find_root


@pytest.fixture(scope="module")
def generator():
    root = find_root(__file__)
    candidates = (
        root / "generators/2f58238f8bb6/generator.py",
        root / "puzzle_generators/per_puzzle/2f58238f8bb6/generator.py",
    )
    path = next(path for path in candidates if path.is_file())
    spec = importlib.util.spec_from_file_location("key_strip_teaching", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _input(keys, shape):
    grid = [[0] * 8 for _ in range(6)]
    grid[0][:len(keys)] = keys
    for r, row in enumerate(shape, 2):
        grid[r][2:2+len(row)] = row
    return grid


def _hook(generator):
    hook = getattr(generator, "lesson_identifiable", None)
    assert callable(hook), "Missing executable test for transform-key ambiguity"
    return hook


def test_symmetric_demo_does_not_teach_asymmetric_query(generator):
    # A vertical bar cannot distinguish 180 degrees from a vertical flip.
    demo = {"input": _input([3], [[7], [7], [7]]), "output": [[7], [7], [7]]}
    query = {"input": _input([3], [[7, 7], [7, 0], [7, 0]])}
    assert _hook(generator)([demo, demo, demo], query)


def test_unseen_key_is_reported_when_its_query_transform_matters(generator):
    demo = {"input": _input([1], [[7, 7], [7, 0], [7, 0]]),
            "output": [[7, 7], [7, 0], [7, 0]]}
    query = {"input": _input([2], [[7, 7], [7, 0], [7, 0]])}
    assert _hook(generator)([demo], query)


def test_equivalent_surviving_maps_are_not_false_ambiguity(generator):
    # An unseen key on a square has the same answer under all eight D4 maps.
    demo = {"input": _input([1], [[7, 7], [7, 0], [7, 0]]),
            "output": [[7, 7], [7, 0], [7, 0]]}
    query = {"input": _input([2], [[7, 7], [7, 7]])}
    assert _hook(generator)([demo], query) == []


def test_canonical_demonstrations_determine_query_maps(generator):
    pairs = canonical_pairs("2f58238f8bb6", root=find_root(__file__))
    assert _hook(generator)(pairs[:2], {"input": pairs[2]["input"]}) == []


def test_inconsistent_demo_label_is_reported(generator):
    demo = {"input": _input([3], [[7], [7], [7]]), "output": [[8]]}
    query = {"input": _input([3], [[7, 7], [7, 0], [7, 0]])}
    assert _hook(generator)([demo], query)


def test_query_label_is_not_read_by_identifiability_check(generator):
    pairs = canonical_pairs("2f58238f8bb6", root=find_root(__file__))
    query = {"input": pairs[2]["input"], "output": [[9]]}
    assert _hook(generator)(pairs[:2], query) == []
