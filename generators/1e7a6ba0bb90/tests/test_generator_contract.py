"""Portable regressions for canonical support, honest controls and teaching."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root
from puzzle_generators.helpers.selfcheck import components


TASK = "1e7a6ba0bb90"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"
SPEC = importlib.util.spec_from_file_location("reviewed_generator", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
PAIRS = canonical_pairs(TASK, root=ROOT)


def parts(grid):
    tkey = next(v for v in grid[0] if v in (1, 2, 3))
    okey = next(v for v in grid[0] if v in (4, 5, 6))
    objs = sorted(components(grid[2:]), key=lambda obj: (obj["bbox"][1], obj["bbox"][0], obj["color"]))
    return tkey, okey, objs


def transform(cells, key):
    cells = set(cells)
    h = max(r for r, c in cells) + 1
    w = max(c for r, c in cells) + 1
    if key == 1:
        return {(c, h - 1 - r) for r, c in cells}
    if key == 2:
        return {(r, w - 1 - c) for r, c in cells}
    return {(h - 1 - r, c) for r, c in cells}


def independent_output(grid):
    """Coordinate-set oracle, separate from the generator's bit-mask helpers."""
    tkey, okey, objs = parts(grid)
    a = transform(objs[0]["norm"], tkey)
    b = set(objs[1]["norm"])
    cells = a | b if okey == 4 else a & b if okey == 5 else a ^ b
    if not cells:
        return [[0]]
    r0, c0 = min(r for r, c in cells), min(c for r, c in cells)
    return [[8 if (r, c) in cells else 0
             for c in range(c0, max(c for r, c in cells) + 1)]
            for r in range(r0, max(r for r, c in cells) + 1)]


@pytest.mark.parametrize("pair", PAIRS, ids=lambda p: f'{p["split"]}-{p["pair_index"]}')
def test_accepts_canonical_inputs(pair):
    assert GEN.self_check(pair["input"]) == []


@pytest.mark.parametrize("bad", [[], [[]], [[0, 1], [0]], [[True]], [[1.2]], [[11]], [None]])
def test_validator_returns_reasons_for_malformed_grids(bad):
    assert GEN.self_check(bad)


def test_rejects_uninterpreted_header_cells():
    grid = GEN.generate(17, 0)
    c = next(c for c, v in enumerate(grid[0]) if not v)
    grid[0][c] = 9
    assert GEN.self_check(grid)


def test_rejects_third_body_object_even_in_key_colors():
    grid = GEN.generate(17, 0)
    grid[-1] = [0] * len(grid[0])
    grid[-2] = [0] * len(grid[0])
    grid[-1][-1] = 1
    assert GEN.self_check(grid)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("height,width", [(8, 10), (14, 16)])
def test_dimension_boundaries_are_usable_in_every_band(difficulty, height, width):
    grid = GEN.generate(31, 7, difficulty=difficulty, grid_h=height, grid_w=width)
    assert (len(grid), len(grid[0])) == (height, width)
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("tkey", [1, 2, 3])
@pytest.mark.parametrize("okey", [4, 5, 6])
def test_transform_and_operation_overrides_are_visible(tkey, okey):
    grid = GEN.generate(29, 4, transform_key=tkey, operation_key=okey)
    assert parts(grid)[:2] == (tkey, okey)


@pytest.mark.parametrize("kind,want", [("canonical", (2, 3)), ("reversed", (3, 2))])
def test_palette_roles_are_observable(kind, want):
    grid = GEN.generate(9, 2, palette_kind=kind)
    assert tuple(obj["color"] for obj in parts(grid)[2]) == want


@pytest.mark.parametrize("relation", ["equal", "disjoint", "overlap"])
def test_relation_control_describes_transformed_operands(relation):
    grid = GEN.generate(13, 5, relation=relation)
    tkey, _, objs = parts(grid)
    a, b = transform(objs[0]["norm"], tkey), set(objs[1]["norm"])
    observed = "equal" if a == b else "disjoint" if not a & b else "overlap"
    assert observed == relation
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("kwargs", [{"typo_axis": 1}, {"grid_h": True}, {"grid_w": 12.5},
                                    {"grid_h": "10"}, {"transform_key": 4}, {"operation_key": 3},
                                    {"palette_kind": "unknown"}, {"relation": "unknown"}])
def test_invalid_overrides_raise(kwargs):
    with pytest.raises((ValueError, TypeError)):
        GEN.generate(19, 3, **kwargs)


def test_default_schedule_covers_all_key_pairs_in_every_nine_window():
    wanted = {(t, o) for t in (1, 2, 3) for o in (4, 5, 6)}
    for band in ("easy", "medium", "hard"):
        for seed in (0, 17):
            grids = [GEN.generate(seed, i, difficulty=band) for i in range(18)]
            for start in range(9):
                assert {parts(g)[:2] for g in grids[start:start + 9]} == wanted


def test_authoring_output_helpers_agree_with_independent_oracle():
    for pair in PAIRS:
        assert independent_output(pair["input"]) == pair["output"]
        assert GEN.predict_for_authoring(pair["input"]) == pair["output"]
    for band in ("easy", "medium", "hard"):
        for index in range(18):
            grid = GEN.generate(731, index, difficulty=band)
            assert GEN.predict_for_authoring(grid) == independent_output(grid)


def test_declared_shortcuts_really_fit_all_labeled_canonical_pairs():
    assert GEN.CANONICAL_SHORTCUTS
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in PAIRS), name


def test_every_rotation_refutes_query_changing_declared_rivals():
    for band in ("easy", "medium", "hard"):
        for seed in (0, 17):
            examples = [GEN.generate(seed, index, difficulty=band) for index in range(18)]
            outputs = [independent_output(grid) for grid in examples]
            for start in range(9):
                grids = examples[start:start + 10]
                labels = outputs[start:start + 10]
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    matches = [rival(grid) == label for grid, label in zip(grids, labels)]
                    assert sum(not match for match in matches) != 1, (band, seed, start, name)


def test_generation_and_rivals_do_not_mutate_inputs_or_depend_on_call_order():
    first = GEN.generate(77, 5, difficulty="hard")
    baseline = copy.deepcopy(first)
    for rival in GEN.LESSON_COMPETITORS.values():
        rival(first)
    assert first == baseline
    GEN.generate(2, 71, difficulty="easy")
    assert GEN.generate(77, 5, difficulty="hard") == baseline


def test_racket_verified_clockwise_counterexample_is_not_counterclockwise():
    grid = [[0] * 12 for _ in range(8)]
    grid[0][1], grid[0][3] = 1, 4
    for r, c in ((0, 0), (1, 0), (2, 0), (2, 1)):
        grid[2+r][c] = 2
    for r, c in ((0, 0), (0, 1), (1, 1)):
        grid[2+r][5+c] = 3
    # Fixed expectations verified by the unchanged public Racket authority.
    assert GEN.self_check(grid) == []
    assert GEN.predict_for_authoring(grid) == [[8, 8, 8], [8, 8, 0]]
    assert GEN.CANONICAL_SHORTCUTS["key_1_means_ccw"](grid) == [[8, 8, 8], [8, 8, 8]]


def test_teaching_positions_refute_vertical_alignment_after_crop():
    # Independent review found that merely offsetting the two input objects
    # does not guarantee different answers after intersection and cropping.
    grid = GEN.generate(92, 2, difficulty="hard")
    assert GEN.CANONICAL_SHORTCUTS["retain_relative_vertical_offset"](grid) != independent_output(grid)
