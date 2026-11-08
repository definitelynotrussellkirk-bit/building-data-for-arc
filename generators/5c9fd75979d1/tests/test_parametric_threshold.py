"""Behavior tests for the separate native bbox-threshold family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1]


def load_prototype():
    path = HOME / "workspace/parametric/prototype.py"
    assert path.is_file(), "The native parametric prototype must exist"
    spec = importlib.util.spec_from_file_location("threshold_test_prototype", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sparse_area_controls_partitions_not_pixel_count():
    p = load_prototype()
    grid = [[1,1,1,0,2,2,2], [1,1,1,0,2,0,0], [1,1,1,0,0,0,0]]
    assert p.analyze(grid, 4)["output"] == [[2,0,1], [0,0,1]]
    assert p.analyze(grid, 4, metric="cells")["output"] == [[1]]
    grid = [[1,1,1,0,0,2,0], [1,1,1,0,2,2,2], [1,1,1,0,0,2,0]]
    assert p.analyze(grid, 8)["output"] == [[2,0,1]]
    assert p.analyze(grid, 8, metric="cells")["output"] == [[1]]


def test_filter_before_partition_changes_dimensions():
    p = load_prototype()
    grid = [[1,1,1,0,0], [1,1,1,0,0], [1,1,1,0,0], [0,0,0,0,0], [0,0,0,0,2]]
    assert p.analyze(grid, 8)["output"] == [[1]]
    assert p.analyze(grid, 8, all_edges=True)["output"] == [[0,0,1],[0,0,0],[0,0,0]]


def test_canonical_program_is_byte_identical():
    p = load_prototype()
    from arcpuzzles import Catalog
    from reviewer_support import find_root
    record = Catalog(find_root(__file__)).get("5c9fd75979d1")
    programs = {v["program_solution"] for v in record["variants"]}
    assert programs == {p.program({"min_bbox_area": 2})}
    assert len({p.program({"min_bbox_area": t}) for t in (2,4,8)}) == 3


@pytest.mark.parametrize("cutoff", [2,4,8])
@pytest.mark.parametrize("demos,queries", [(2,1),(3,4),(6,4)])
def test_counts_labels_unique_inputs_and_teaching(cutoff, demos, queries):
    p = load_prototype()
    settings = {"min_bbox_area": cutoff}
    lesson = p.generate(17, settings, demos, queries)
    assert len(lesson["train"]) == demos
    assert len(lesson["test"]) == queries
    assert lesson["program_solution"] == p.program(settings)
    pairs = lesson["train"] + lesson["test"]
    assert len({json.dumps(x["input"]) for x in pairs}) == len(pairs)
    assert all(p.analyze(x["input"], cutoff)["output"] == x["output"] for x in pairs)
    for other in (2,4,8):
        if other != cutoff:
            assert any(p.analyze(x["input"], other)["output"] != x["output"] for x in lesson["train"])
    if cutoff in (4,8):
        assert any(p.analyze(x["input"], cutoff, metric="cells")["output"] != x["output"] for x in lesson["train"])
    assert any(p.analyze(x["input"], cutoff, all_edges=True)["output"] != x["output"] for x in lesson["train"])


def test_matched_inputs_count_prefix_stability_and_repeatability():
    p = load_prototype()
    base = p.generate(37, {"min_bbox_area": 2}, 3, 4)
    assert p.generate(37, {"min_bbox_area": 2}, 3, 4) == base
    for cutoff in (4,8):
        other = p.generate(37, {"min_bbox_area": cutoff}, 3, 4)
        assert [x["input"] for x in other["train"] + other["test"]] == [x["input"] for x in base["train"] + base["test"]]
    shorter = p.generate(37, {"min_bbox_area": 2}, 2, 1)
    assert shorter["train"] == base["train"][:2]
    assert shorter["test"] == base["test"][:1]
    longer = p.generate(37, {"min_bbox_area": 2}, 6, 4)
    assert longer["test"] == base["test"]


def test_real_large_content_and_boundary_contact():
    p = load_prototype()
    lesson = p.generate(0, {"min_bbox_area": 8}, 3, 4)
    grid = lesson["test"][2]["input"]
    assert (len(grid), len(grid[0])) == (30,30)
    assert sum(bool(c) for row in grid for c in row) > 380
    # A densely occupied pair of canvas edges survives global reflections/turns.
    edge_counts = [sum(bool(c) for c in grid[0]), sum(bool(c) for c in grid[-1]),
                   sum(bool(row[0]) for row in grid), sum(bool(row[-1]) for row in grid)]
    assert sum(n >= 16 for n in edge_counts) >= 2
    analysis = p.analyze(grid, 8)
    assert len(analysis["retained"]) >= 20
    assert len(analysis["row_breaks"]) >= 6
    assert len(analysis["col_breaks"]) >= 6


def test_input_layouts_include_both_portrait_and_landscape():
    p = load_prototype()
    shapes = {(len(p.make_input(seed,"test",0)), len(p.make_input(seed,"test",0)[0])) for seed in range(8)}
    assert shapes == {(14,17),(17,14)}


def test_teaching_fragments_remain_measured_separate_components():
    p = load_prototype()
    for seed in range(16):
        for index in (0,1):
            observed = {(o["area"],o["size"]) for o in p.components(p.make_input(seed,"train",index))}
            assert {(3,3),(4,3),(6,4),(8,5),(9,5),(12,6)} <= observed, (seed,index,observed)


@pytest.mark.parametrize("settings", [{}, {"min_bbox_area": True}, {"min_bbox_area":2.0}, {"min_bbox_area":3}, {"min_bbox_area":2,"extra":0}, None])
def test_invalid_settings_fail_closed(settings):
    p = load_prototype()
    with pytest.raises(ValueError): p.program(settings)


@pytest.mark.parametrize("seed,demos,queries", [(True,3,4),(-1,3,4),(2**63,3,4),(0,True,4),(0,1,4),(0,7,4),(0,3,False),(0,3,0),(0,3,5)])
def test_invalid_request_counts_and_seed(seed,demos,queries):
    p = load_prototype()
    with pytest.raises(ValueError): p.generate(seed,{"min_bbox_area":2},demos,queries)


@pytest.mark.parametrize("grid", [[], [[1], [1,2]], [[True]], [[10]], [[1.0]]])
def test_grid_contract_rejects_inexact_or_malformed_values(grid):
    p = load_prototype()
    with pytest.raises(ValueError): p.analyze(grid,2)


def test_all_declared_rival_programs_execute_in_protected_racket():
    p = load_prototype()
    from arcpuzzles.parametric_worker import _real_evaluator
    from reviewer_support import find_root
    root = find_root(__file__)
    # The staged runner uses execution-layout arc_repl/ at the root; a source
    # checkout imports it from shared/runtime/. Both must remain in this tree.
    import arc_repl.racket_bridge as runtime_bridge
    runtime = Path(runtime_bridge.__file__).resolve().parent.parent
    assert runtime.is_relative_to(root)
    apply, identity, bridge = _real_evaluator(runtime)
    grid = [[1,1,1,0,0,2,0], [1,1,1,0,2,2,2], [1,1,1,0,0,2,0]]
    try:
        assert identity["backend"] == "racket" and identity["protected"] is True
        for name in p.RIVAL_NAMES:
            out = apply(p.rival_program({"min_bbox_area":8},name),grid)
            assert out and all(type(x) is int for row in out for x in row)
    finally:
        bridge.close()
