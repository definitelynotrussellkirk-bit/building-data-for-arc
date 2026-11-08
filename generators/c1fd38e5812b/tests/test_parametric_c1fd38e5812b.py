from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest


HERE = Path(__file__).resolve().parents[1] / "workspace/parametric"
SPEC = importlib.util.spec_from_file_location("_c1fd38e5812b_family_test", HERE / "prototype.py")
family = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(family)


def test_exact_canonical_default():
    from arcpuzzles import Catalog
    root = HERE.parents[3]
    programs = {v["program_solution"] for v in Catalog(root).get(family.TASK_ID)["variants"]}
    assert programs == {family.program({"view": "compressed"})}


def test_compression_preserves_nonconsecutive_equal_rows_and_columns():
    logical = [[1, 2, 1], [3, 4, 3], [1, 2, 1]]
    expanded = family.expand(logical, [2, 4, 2], [3, 2, 4])
    assert family.compress(expanded) == logical


def test_zero_component_is_selectable_and_crop_preserves_other_colors():
    grid = [[1, 2, 1, 2, 1], [2, 0, 0, 0, 2], [1, 0, 3, 0, 1],
            [2, 0, 0, 0, 2], [1, 2, 1, 2, 1]]
    component = family.select_component(grid)
    assert len(component) == 8
    assert family.crop(grid, component) == [[0, 0, 0], [0, 3, 0], [0, 0, 0]]


def test_ties_follow_bbox_order_including_zero():
    grid = [[8, 9, 8, 9], [7, 0, 0, 4], [6, 2, 3, 4]]
    chosen = family.select_component(grid)
    assert family.bbox(chosen) == (1, 1, 1, 2)
    assert family.crop(grid, chosen) == [[0, 0]]


@pytest.mark.parametrize("settings", [{}, {"view": "bad"}, {"view": 1},
                                    {"view": "compressed", "x": 1}, None])
def test_reject_settings(settings):
    with pytest.raises(ValueError):
        family.program(settings)


@pytest.mark.parametrize("seed", [True, -1, 2**63, 1.0, "1"])
def test_reject_seeds(seed):
    with pytest.raises(ValueError):
        family.generate(seed, {"view": "compressed"})


@pytest.mark.parametrize("demos,queries", [(2, 4), (7, 4), (3, 0), (3, 5),
                                          (True, 1), (3.0, 1), (3, False)])
def test_reject_count_requests(demos, queries):
    with pytest.raises(ValueError):
        family.generate(0, {"view": "compressed"}, demos=demos, queries=queries)


def test_request_prefixes_settings_and_copy_isolation():
    full = family.generate(17, {"view": "compressed"}, demos=6, queries=4)
    short = family.generate(17, {"view": "compressed"}, demos=3, queries=1)
    alternate = family.generate(17, {"view": "largest_component_crop"}, demos=6, queries=4)
    assert short["train"] == full["train"][:3]
    assert short["test"] == full["test"][:1]
    for split in ("train", "test"):
        assert [p["input"] for p in full[split]] == [p["input"] for p in alternate[split]]
    assert full == family.generate(17, {"view": "compressed"}, demos=6, queries=4)
    short["train"][0]["input"][0][0] = 99
    assert family.generate(17, {"view": "compressed"}, demos=3, queries=1) != short


def test_core_teaches_zero_and_independent_span_axes():
    lesson = family.generate(0, {"view": "largest_component_crop"})
    axes = set()
    winners = []
    for pair in lesson["train"]:
        info = family.analyze(pair["input"])
        axes.add((len(set(info["row_spans"])) == 1, len(set(info["col_spans"])) == 1))
        logical = info["logical"]
        chosen = family.select_component(logical)
        winners.append(logical[chosen[0][0]][chosen[0][1]])
    assert (True, False) in axes and (False, True) in axes
    assert 0 in winners and any(color != 0 for color in winners)


def test_tie_colors_do_not_replace_bbox_tiebreak():
    lesson = family.generate(0, {"view": "largest_component_crop"})
    for sign in (1, -1):
        outputs = []
        for pair in lesson["train"]:
            grid = family.compress(pair["input"])
            wrong = min(family.components(grid), key=lambda o: (
                -len(o), sign*grid[o[0][0]][o[0][1]], *family.bbox(o)))
            outputs.append(family.crop(grid, wrong))
        assert outputs != [pair["output"] for pair in lesson["train"]]


def test_first_queries_vary_beyond_the_literal_minimum():
    outputs = [family.generate(seed, {"view": "largest_component_crop"})["test"][0]
               for seed in range(6)]
    assert len({(len(p["input"]),len(p["input"][0])) for p in outputs}) > 1
    assert any(len(p["output"])*len(p["output"][0]) > 1 for p in outputs)


def test_first_nontrivial_component_is_not_sufficient():
    lesson = family.generate(0, {"view": "largest_component_crop"})
    wrong_outputs=[]
    for pair in lesson["train"]:
        grid=family.compress(pair["input"])
        groups=family.components(grid)
        nontrivial=[o for o in groups if len(o)>1]
        chosen=min(nontrivial or groups,key=family.bbox)
        wrong_outputs.append(family.crop(grid,chosen))
    assert wrong_outputs != [pair["output"] for pair in lesson["train"]]


def test_small_and_dense_boundaries_and_all_inputs_unique():
    lesson = family.generate(0, {"view": "compressed"}, demos=6, queries=4)
    assert (len(lesson["test"][0]["input"]), len(lesson["test"][0]["input"][0])) == (4, 4)
    dense = lesson["test"][3]["input"]
    assert (len(dense), len(dense[0])) == (30, 30)
    assert len(family.compress(dense)) >= 8 and len(family.compress(dense)[0]) >= 8
    keys = {tuple(map(tuple, pair["input"])) for split in ("train", "test") for pair in lesson[split]}
    assert len(keys) == 10
    for split in ("train", "test"):
        for pair in lesson[split]:
            assert family.validate_grid(pair["input"])


def test_invalid_grammar_rejected():
    valid = family.generate(0, {"view": "compressed"})["test"][0]["input"]
    bad = copy.deepcopy(valid); bad[0][0] = True
    with pytest.raises(ValueError): family.validate_grid(bad)
    bad = copy.deepcopy(valid); bad[1][1] = 9 if bad[0][0] != 9 else 8
    with pytest.raises(ValueError): family.validate_grid(bad)
    with pytest.raises(ValueError): family.validate_grid([[0] * 31 for _ in range(4)])


def test_protected_racket_boundaries_and_semantics():
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
    root = HERE.parents[3]
    runtime = root / "shared/runtime"
    with _local_imports(runtime, HERE):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            assert identity["backend"] == "racket" and identity["protected"]
            for view in family.VIEWS:
                lesson = family.generate(0, {"view": view})
                for pair in [*lesson["train"], lesson["test"][0], lesson["test"][3]]:
                    assert apply(lesson["program_solution"], pair["input"]) == pair["output"]
        finally:
            bridge.close()
