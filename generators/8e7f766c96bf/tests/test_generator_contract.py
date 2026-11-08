"""Independent behavior regressions, portable between library and staged runtime."""
from __future__ import annotations

import copy
import importlib.util
import os
import random
import shutil
import sys
from collections import Counter
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "8e7f766c96bf"
ROOT = find_root(__file__)


def _load_generator():
    candidates = [
        ROOT / "generators" / TASK_ID / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / (TASK_ID + ".py"),
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    ]
    path = next((p for p in candidates if p.is_file()), None)
    assert path is not None, f"No owned generator in {ROOT}"
    spec = importlib.util.spec_from_file_location("review_generator_" + TASK_ID, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
BANDS = ("easy", "medium", "hard")
AXIS_VALUES = {
    "grid_h": range(9, 23), "grid_w": range(12, 23),
    "n_squares": range(1, 4), "texture": ("sparse", "contrast"),
}


def _components(grid):
    """Four-neighbor blue components, independently of the generator helpers."""
    remaining = {(r, c) for r, row in enumerate(grid)
                 for c, value in enumerate(row) if value == 1}
    components = []
    while remaining:
        start = remaining.pop()
        todo, component = [start], {start}
        while todo:
            r, c = todo.pop()
            for neighbor in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    todo.append(neighbor)
        components.append(component)
    return components


def _frames(grid):
    assert isinstance(grid, list) and grid and grid[0]
    assert all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
    assert all(type(cell) is int and cell in (0, 1) for row in grid for cell in row)
    frames = []
    for component in _components(grid):
        top = min(r for r, c in component)
        bottom = max(r for r, c in component)
        left = min(c for r, c in component)
        right = max(c for r, c in component)
        height, width = bottom-top+1, right-left+1
        assert height >= 3 and width >= 3
        border = {(r, c) for r in range(top, bottom+1) for c in range(left, right+1)
                  if r in (top, bottom) or c in (left, right)}
        assert component == border
        assert all(grid[r][c] == 0 for r in range(top+1, bottom)
                   for c in range(left+1, right))
        frames.append((top, left, height, width))
    assert any((h, w) == (4, 4) for r, c, h, w in frames)
    return frames


def _observe(grid):
    shapes = Counter((h, w) for r, c, h, w in _frames(grid))
    targets = shapes.pop((4, 4))
    if set(shapes) <= {(5, 5)}:
        assert shapes.get((5, 5), 0) <= 1
        texture = "sparse"
    else:
        assert shapes == Counter({(3, 3): 1, (4, 5): 1, (5, 4): 1})
        texture = "contrast"
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_squares": targets, "texture": texture}


def _label(grid):
    output = copy.deepcopy(grid)
    for top, left, height, width in _frames(grid):
        if (height, width) == (4, 4):
            for r in range(top+1, top+3):
                for c in range(left+1, left+3):
                    output[r][c] = 2
    return output


def _literal_witness():
    # Targets (4x4) and three independently drawn size/shape counterexamples.
    grid = [[0] * 17 for _ in range(11)]
    for top, left, height, width in ((1, 1, 4, 4), (1, 7, 3, 3),
                                      (6, 1, 4, 5), (5, 10, 5, 4)):
        for r in range(top, top+height):
            for c in range(left, left+width):
                if r in (top, top+height-1) or c in (left, left+width-1):
                    grid[r][c] = 1
    return grid


def test_public_contract_has_only_real_axes_and_preserved_rule_pin():
    assert gen.VERSION == "2.0.0"
    assert gen.RULE_HASH == "bb4f82892380"
    assert set(gen.AXES) == set(AXIS_VALUES)
    for name, lo, hi in (("grid_h", 9, 22), ("grid_w", 12, 22), ("n_squares", 1, 3)):
        assert gen.AXES[name]["type"] == "int"
        assert gen.AXES[name]["valid"] == f"{lo}..{hi}"
    assert set(gen.AXES["texture"]["valid"].split("|")) == {"sparse", "contrast"}


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("axis", AXIS_VALUES)
def test_all_single_axis_values_are_exact_in_every_band(band, axis):
    for value in AXIS_VALUES[axis]:
        grid = gen.generate(107, 1, difficulty=band, **{axis: value})
        observed = _observe(grid)
        assert observed[axis] == value, (band, axis, value, observed)
        assert gen.observe_overrides(grid) == observed
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("texture", ("sparse", "contrast"))
def test_feasible_joint_overrides_are_exact_and_never_drop_targets(band, texture):
    for seed in (0, 1, 31):
        requested = dict(grid_h=22, grid_w=22, n_squares=3, texture=texture)
        grid = gen.generate(seed, 6, difficulty=band, **requested)
        assert _observe(grid) == requested
        assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize("band", BANDS)
def test_optional_large_frame_cannot_reject_a_feasible_exact_request(band):
    # Three targets fit in two shelves on 9x12. An optional 5x5 does not.
    # The optional distractor must not turn this legal request into a seed lottery.
    requested = dict(grid_h=9, grid_w=12, n_squares=3, texture="sparse")
    for seed in range(20):
        grid = gen.generate(seed, 0, difficulty=band, **requested)
        assert _observe(grid) == requested


@pytest.mark.parametrize("requested", [
    dict(grid_h=9, grid_w=12, texture="contrast"),
    dict(grid_h=9, n_squares=3, texture="contrast"),
])
def test_impossible_joint_requests_raise_with_overridden_axes(requested):
    with pytest.raises(ValueError) as caught:
        gen.generate(4, 1, **requested)
    incompatible = getattr(caught.value, "incompatible_axes", None)
    assert incompatible and set(incompatible) <= set(requested)
    assert "texture" in incompatible


@pytest.mark.parametrize("axis,value", [
    (axis, value)
    for axis, legal in (("grid_h", 12), ("grid_w", 12), ("n_squares", 2))
    for value in (True, False, float(legal), str(legal))
])
def test_integer_overrides_reject_coercion(axis, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(3, 0, **{axis: value})


@pytest.mark.parametrize("requested", [
    {"grid_h": 8}, {"grid_h": 23}, {"grid_w": 11}, {"grid_w": 23},
    {"n_squares": 0}, {"n_squares": 4}, {"texture": "warm"},
    {"texture": "no_squares"}, {"palette_kind": "default"}, {"typo_axis": 7},
])
def test_out_of_range_old_and_unknown_controls_reject(requested):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(3, 0, **requested)


@pytest.mark.parametrize("band", BANDS)
def test_default_lessons_keep_contrast_in_every_single_query_holdout(band):
    for seed in (0, 19):
        for start in range(6):
            pairs = []
            for index in range(start, start+4):
                grid = gen.generate(seed, index, difficulty=band)
                observed = _observe(grid)
                assert observed["texture"] == ("contrast" if index % 2 else "sparse")
                pairs.append({"input": grid, "output": _label(grid)})
            assert sum(_observe(p["input"])["texture"] == "contrast" for p in pairs) == 2
            for held_out in range(4):
                demos = [p for i, p in enumerate(pairs) if i != held_out]
                assert any(_observe(p["input"])["texture"] == "contrast" for p in demos)
                for namespace in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
                    rivals = getattr(gen, namespace)
                    assert rivals
                    for name, rival in rivals.items():
                        predictions = [rival(p["input"]) for p in demos]
                        if predictions == [p["output"] for p in demos]:
                            assert rival(pairs[held_out]["input"]) == pairs[held_out]["output"], (namespace, name, seed, start, held_out)


def test_structural_validator_accepts_canonical_inputs_without_mutation():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert pairs
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        _frames(grid)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert _label(grid) == pair["output"]
        assert grid == pair["input"]


def _invalid_inputs():
    base = _literal_witness()
    partial = copy.deepcopy(base); partial[1][2] = 0
    solid4 = copy.deepcopy(base)
    for r in (2, 3):
        for c in (2, 3):
            solid4[r][c] = 1
    singleton = copy.deepcopy(base); singleton[0][16] = 1
    shortline = copy.deepcopy(base); shortline[0][15:17] = [1, 1]
    solid2 = copy.deepcopy(base)
    for r in (0, 1):
        for c in (15, 16):
            solid2[r][c] = 1
    boolean = copy.deepcopy(base); boolean[0][0] = False
    noninteger = copy.deepcopy(base); noninteger[0][0] = 0.0
    ragged = copy.deepcopy(base); ragged[-1].pop()
    return [singleton, shortline, solid2, solid4, partial, boolean, noninteger,
            ragged, [[0]], [[1]], [], [[]]]


@pytest.mark.parametrize("grid", _invalid_inputs(), ids=("singleton", "shortline", "solid2", "solid4", "partial", "bool", "float", "ragged", "blank", "single", "empty", "emptyrow"))
def test_validator_rejects_structural_impostors_and_meta_cannot_bypass(grid):
    assert gen.self_check(grid)
    assert gen.self_check(grid, meta={"texture": "no_squares"})
    assert gen.strict_canonical_like(grid)


def test_literal_contrast_witness_refutes_all_declared_shortcuts():
    grid = _literal_witness()
    expected = _label(grid)
    assert sum(cell == 2 for row in expected for cell in row) == 4
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    rivals = gen.CANONICAL_SHORTCUTS
    assert rivals
    for name, rival in rivals.items():
        original = copy.deepcopy(grid)
        assert rival(grid) != expected, name
        assert grid == original, name


def test_keyed_replay_varies_scenes_and_does_not_mutate_global_rng_or_returns():
    random.seed(671); before = random.getstate()
    first = gen.generate(501, 3, grid_h=22, grid_w=22, n_squares=2, texture="contrast")
    original = copy.deepcopy(first)
    assert gen.generate(501, 3, grid_h=22, grid_w=22, n_squares=2, texture="contrast") == first
    assert random.getstate() == before
    first[0][0] = 9
    assert gen.generate(501, 3, grid_h=22, grid_w=22, n_squares=2, texture="contrast") == original
    scenes = {tuple(tuple(row) for row in gen.generate(seed, 3, grid_h=22, grid_w=22,
                   n_squares=2, texture="contrast")) for seed in range(10)}
    assert len(scenes) >= 8


@pytest.mark.skipif(not (os.environ.get("RACKET_PATH") or shutil.which("racket")), reason="Racket runtime required")
def test_public_racket_labels_literal_and_generated_contrast_witnesses():
    # Catalog.apply is available in the library/packet public API, while the
    # inherited staged task runtime can omit the catalog package entirely.
    if not (ROOT / "catalog").is_dir():
        pytest.skip("Public Catalog API requires the packet/library root")
    from arcpuzzles import Catalog
    inputs = [_literal_witness(), gen.generate(818, 1, texture="contrast", grid_h=22, grid_w=22, n_squares=3)]
    result = Catalog(ROOT).apply(TASK_ID, inputs, allow_unapproved=True)
    assert result["executed_rule_hash"] == "bb4f82892380"
    assert result["rule_hash_matches_catalog"]
    assert [row["error"] for row in result["results"]] == [None, None]
    assert [row["output"] for row in result["results"]] == [_label(grid) for grid in inputs]
