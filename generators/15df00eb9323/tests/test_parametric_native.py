"""Native majority-versus-unanimous normalized-overlay regressions."""
from __future__ import annotations

from collections import deque
import importlib.util
import json
import sys

import pytest

from arcpuzzles import Catalog
from reviewer_support import find_root

TASK_ID = "15df00eb9323"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
ADAPTER_PATH = HOME / "adapter.py"


def _load_adapter():
    assert ADAPTER_PATH.is_file(), "native parametric adapter has not been built"
    name = "_test_15df00eb9323_parametric"
    spec = importlib.util.spec_from_file_location(name, ADAPTER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = {row["program_solution"] for row in Catalog(ROOT).get(TASK_ID)["variants"]}
    assert len(programs) == 1
    return next(iter(programs))


def _components(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    queue.append(point)
        top = min(r for r, _ in cells)
        left = min(c for _, c in cells)
        result.append(frozenset((r - top, c - left) for r, c in cells))
    return result


def _support(grid):
    counts = {}
    for shape in _components(grid):
        for cell in shape:
            counts[cell] = counts.get(cell, 0) + 1
    return counts


def _crop(grid):
    occupied = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert occupied
    r1, r2 = min(r for r, _ in occupied), max(r for r, _ in occupied)
    c1, c2 = min(c for _, c in occupied), max(c for _, c in occupied)
    return [row[c1:c2 + 1] for row in grid[r1:r2 + 1]]


def _oracle(grid, level):
    counts = _support(grid)
    h = max(r for r, _ in counts) + 1
    w = max(c for _, c in counts) + 1
    threshold = 2 if level == "majority" else 3
    return _crop([[8 if counts.get((r, c), 0) >= threshold else 0 for c in range(w)] for r in range(h)])


def _visible_inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def _serialized(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def test_default_program_is_exact_canonical_and_unanimous_changes_only_support_test():
    adapter = _load_adapter()
    majority = adapter.program({"consensus_level": "majority"})
    unanimous = adapter.program({"consensus_level": "unanimous"})
    assert majority == _canonical_program()
    assert unanimous != majority
    assert "(>= cnt 2)" in majority
    assert "(>= cnt 3)" in unanimous
    assert "(>= cnt 2)" not in unanimous


@pytest.mark.parametrize("settings", [
    None, {}, {"consensus_level": "majority", "extra": 1},
    {"consensus_level": True}, {"consensus_level": 0},
    {"consensus_level": "union"},
])
def test_settings_validation_is_exact(settings):
    adapter = _load_adapter()
    with pytest.raises(ValueError):
        adapter.program(settings)


@pytest.mark.parametrize("seed,demos,queries", [
    (True, 2, 4), (-1, 2, 4), (2**63, 2, 4), (1.0, 2, 4),
    (0, True, 4), (0, 1, 4), (0, 7, 4),
    (0, 2, True), (0, 2, 3), (0, 2, 5),
])
def test_request_boundaries_are_strict(seed, demos, queries):
    adapter = _load_adapter()
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(seed, {"consensus_level": "majority"}, demos, queries)


@pytest.mark.parametrize("demos", [2, 6])
def test_min_and_max_counts_have_exact_four_distinct_queries(demos):
    adapter = _load_adapter()
    episode = adapter.generate(20261025, {"consensus_level": "unanimous"}, demos, 4)
    assert set(episode) == {"train", "test", "program_solution"}
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    enc = [_serialized(grid) for grid in _visible_inputs(episode)]
    assert len(enc) == len(set(enc))


def test_inputs_are_setting_independent_and_every_demo_distinguishes_levels():
    adapter = _load_adapter()
    majority = adapter.generate(44617, {"consensus_level": "majority"}, 2, 4)
    unanimous = adapter.generate(44617, {"consensus_level": "unanimous"}, 2, 4)
    assert _visible_inputs(majority) == _visible_inputs(unanimous)
    assert adapter.generate(44617, {"consensus_level": "majority"}, 2, 4) == majority
    assert all(a["output"] != b["output"] for a, b in zip(majority["train"], unanimous["train"]))


@pytest.mark.parametrize("level", ["majority", "unanimous"])
def test_every_pair_matches_independent_normalized_support_oracle(level):
    adapter = _load_adapter()
    episode = adapter.generate(7001, {"consensus_level": level}, 3, 4)
    for pair in [*episode["train"], *episode["test"]]:
        counts = _support(pair["input"])
        assert set(counts.values()) == {1, 2, 3}
        assert pair["output"] == _oracle(pair["input"], level)
        assert _oracle(pair["input"], "majority") != _oracle(pair["input"], "unanimous")


def test_query_bank_contains_lower_boundary_and_substantive_30x30_stress():
    adapter = _load_adapter()
    episode = adapter.generate(99, {"consensus_level": "majority"}, 3, 4)
    grids = [pair["input"] for pair in episode["test"]]
    assert (7, 11) in {(len(g), len(g[0])) for g in grids}
    stress = next(g for g in grids if (len(g), len(g[0])) == (30, 30))
    assert sum(value != 0 for row in stress for value in row) >= 120
    occupied = [(r, c) for r, row in enumerate(stress) for c, value in enumerate(row) if value]
    assert max(r for r, _ in occupied) - min(r for r, _ in occupied) >= 24
    assert max(c for _, c in occupied) - min(c for _, c in occupied) >= 24
    assert len(_components(stress)) == 3
    assert sum(value != 0 for row in _oracle(stress, "majority") for value in row) >= 20


def test_seed_seven_small_shelf_permutation_keeps_every_shape_in_bounds():
    """Regression: anchors must be centered after assigning shapes to shelves."""
    adapter = _load_adapter()
    episode = adapter.generate(7, {"consensus_level": "majority"}, 2, 4)
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 4
    for grid in _visible_inputs(episode):
        assert 1 <= len(grid) <= 30
        assert 1 <= len(grid[0]) <= 30
