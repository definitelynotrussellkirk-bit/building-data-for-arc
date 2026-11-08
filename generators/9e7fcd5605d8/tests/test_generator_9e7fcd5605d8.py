"""Task-local regression tests for enclosed-hole recoloring generator."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import itertools
from pathlib import Path
import random
import sys

import pytest

TASK_ID = "9e7fcd5605d8"
HOME = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "shared" / "runtime"))

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load_generator():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
ROOT = find_root(__file__)


def _pairs():
    return canonical_pairs(TASK_ID, root=ROOT)


def _u_shape_grid(color: int = 2):
    grid = [[0] * 5 for _ in range(5)]
    for r, c in ((1, 1), (1, 3), (2, 1), (2, 3), (3, 1), (3, 2), (3, 3)):
        grid[r][c] = color
    return grid


def _expected_recolor(grid, color):
    return [[color if value else 0 for value in row] for row in grid]


def _profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def _pinned_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def test_open_concavity_is_not_a_hole_and_refutes_bbox_shortcut():
    grid = _u_shape_grid()
    authority = gen.rule_mirror(grid)
    assert authority == _expected_recolor(grid, 4)
    rival = gen.SEMANTIC_RIVALS["bbox_nonfull_is_hole"](grid)
    assert rival == _expected_recolor(grid, 8)
    assert gen.SEMANTIC_WITNESSES["open_concavity_not_hole"](grid)


def test_declares_source_bound_contract():
    assert gen.GENERATOR_ID == TASK_ID
    assert gen.TASK_ID == TASK_ID
    assert gen.VERSION == "2.0.0"
    assert gen.RULE_HASH == "02bf16fb38e9"
    assert gen.EXAMPLES_NEEDED == 4
    assert set(gen.AXES) == {
        "grid_h",
        "grid_w",
        "n_hollow",
        "n_hole_free",
        "n_multi_hole",
        "n_distinct_colors",
    }
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


def test_all_canonical_pairs_are_accepted_and_python_mirror_matches():
    pairs = _pairs()
    assert len(pairs) == 3
    for pair in pairs:
        before = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_observable_in_every_band(difficulty):
    requested = {
        "grid_h": 10,
        "grid_w": 10,
        "n_hollow": 2,
        "n_hole_free": 2,
        "n_multi_hole": 1,
        "n_distinct_colors": 2,
    }
    grid = gen.generate(71, 19, difficulty=difficulty, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert grid == gen.generate(71, 19, difficulty=difficulty, **requested)


@pytest.mark.parametrize(
    "values",
    itertools.product((10, 16), (10, 18), (1, 2), (1, 2), (0, 1), (1, 2)),
)
def test_every_boundary_override_combination_is_constructive(values):
    keys = (
        "grid_h",
        "grid_w",
        "n_hollow",
        "n_hole_free",
        "n_multi_hole",
        "n_distinct_colors",
    )
    requested = dict(zip(keys, values))
    grid = gen.generate(901, 37, difficulty="hard", **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 9),
        ("grid_h", 17),
        ("grid_w", 9),
        ("grid_w", 19),
        ("n_hollow", 0),
        ("n_hollow", 3),
        ("n_hole_free", 0),
        ("n_hole_free", 3),
        ("n_multi_hole", -1),
        ("n_multi_hole", 2),
        ("n_distinct_colors", 0),
        ("n_distinct_colors", 3),
        ("grid_h", True),
        ("n_hollow", 1.5),
        ("n_distinct_colors", "2"),
    ],
)
def test_rejects_unknown_out_of_range_and_wrong_type_overrides(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


def test_topology_counter_counts_open_ring_and_double_hole():
    open_u = _u_shape_grid()
    ring = [
        [0, 0, 0, 0, 0],
        [0, 2, 2, 2, 0],
        [0, 2, 0, 2, 0],
        [0, 2, 2, 2, 0],
        [0, 0, 0, 0, 0],
    ]
    double = [
        [0, 0, 0, 0, 0, 0],
        [0, 2, 2, 2, 2, 0],
        [0, 2, 0, 2, 2, 0],
        [0, 2, 2, 0, 2, 0],
        [0, 2, 2, 2, 2, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    assert gen._component_hole_counts(open_u) == [0]
    assert gen._component_hole_counts(ring) == [1]
    assert gen._component_hole_counts(double) == [2]


def test_generated_inputs_always_contain_the_semantic_counterexample():
    for band in ("easy", "medium", "hard"):
        for index in range(40):
            grid = gen.generate(5100 + index, index, difficulty=band)
            assert gen.self_check(grid) == []
            assert gen.SEMANTIC_WITNESSES["open_concavity_not_hole"](grid)
            assert (
                gen.SEMANTIC_RIVALS["bbox_nonfull_is_hole"](grid)
                != gen.rule_mirror(grid)
            )


def test_canonical_shortcut_reproduces_all_canonical_pairs():
    shortcut = gen.CANONICAL_SHORTCUTS["bbox_nonfull_is_hole"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in _pairs())


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(8))
def test_every_four_demo_window_refutes_all_declared_competitors(band, start):
    demos = []
    for offset in range(gen.EXAMPLES_NEEDED):
        index = start + offset
        grid = gen.generate(6200 + index, index, difficulty=band)
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    assert gen.lesson_identifiable(demos, demos[0]["input"]) == []
    for name, rival in gen.LESSON_COMPETITORS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_pinned_profile_floor_hits_every_band_and_strict_rate_meets_claim():
    canonical_profiles = {_profile(pair["input"]) for pair in _pairs()}
    for band in ("easy", "medium", "hard"):
        grids = []
        for index in range(20):
            seed = _pinned_seed(band, index)
            grids.append(gen.generate(seed, seed % 7919 + index, difficulty=band))
        assert any(_profile(grid) in canonical_profiles for grid in grids)
        strict = sum(not gen.strict_canonical_like(grid) for grid in grids)
        assert strict / len(grids) >= gen.MIN_STRICT_FRAC


def test_determinism_fresh_returns_and_process_rng_state():
    state = random.getstate()
    first = gen.generate(901, 17, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(901, 17, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 7
    assert gen.generate(901, 17, difficulty="hard") == second


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 0]], [[True] * 10 for _ in range(10)]])
def test_malformed_grids_are_diagnostic_not_exceptions(bad):
    assert gen.self_check(bad)


def test_rule_and_rival_do_not_mutate_inputs():
    grid = gen.generate(812, 9, difficulty="hard")
    original = deepcopy(grid)
    gen.rule_mirror(grid)
    for rival in gen.SEMANTIC_RIVALS.values():
        rival(grid)
    assert grid == original

@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(8))
def test_every_five_pair_window_is_identifiable_under_all_query_rotations(band, start):
    pairs = []
    for offset in range(gen.EXAMPLES_NEEDED + 1):
        index = start + offset
        grid = gen.generate(7300 + start, index, difficulty=band)
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})

    for query_index in range(len(pairs)):
        demos = pairs[:query_index] + pairs[query_index + 1 :]
        query = pairs[query_index]["input"]
        assert gen.lesson_identifiable(demos, query) == []
