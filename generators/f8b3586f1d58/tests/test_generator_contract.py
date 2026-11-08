"""Focused input/API and finite-lesson regressions; Python mirror is diagnostic."""
import importlib.util
from pathlib import Path

import pytest
from reviewer_support import find_root, canonical_pairs

ROOT = find_root(__file__)
TASK = "f8b3586f1d58"
TASK_HOME = next(p for p in Path(__file__).resolve().parents if (p / "generator.py").is_file())
SPEC = importlib.util.spec_from_file_location("mirror_generator_under_test", TASK_HOME / "generator.py")
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def mirror(grid):
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                out[r][len(row)-1-c] = value
    return out


def occupied(grid):
    return [(r,c,v) for r,row in enumerate(grid) for c,v in enumerate(row) if v]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_declared_boundaries_and_aliases(band):
    for i in range(4):
        g = GEN.generate(7,i,difficulty=band,grid_h=4,grid_w=26,n_cells=20,palette_size=9,position_bias="mixed")
        obs = GEN.observe_overrides(g)
        assert (len(g),len(g[0]),len(occupied(g))) == (4,26,20)
        assert len({v for r,c,v in occupied(g)}) == 9
        assert obs["position_bias"] == "mixed"
        assert GEN.self_check(g) == []
        assert g == GEN.generate(7,i,difficulty=band,grid_h=4,grid_w=26,n_cells=20,n_distinct_colors=9,position_bias="mixed")


@pytest.mark.parametrize("override,value", [("grid_h",4),("grid_h",22),("grid_w",5),("grid_w",26),("n_cells",1),("n_cells",20),("n_distinct_colors",1),("n_distinct_colors",9),("palette_size",1),("palette_size",9)])
def test_single_axis_extremes_adapt_unpinned_defaults(override,value):
    for band in ("easy","medium","hard"):
        for i in range(4):
            g = GEN.generate(31,i,difficulty=band,**{override:value})
            assert GEN.observe_overrides(g)[override] == value
            assert GEN.self_check(g) == []


@pytest.mark.parametrize("side", ["left_half","right_half","mixed"])
def test_side_control_observable(side):
    for i in range(4):
        g=GEN.generate(18,i,grid_h=6,grid_w=8,n_cells=6,n_distinct_colors=3,position_bias=side)
        assert GEN.observe_overrides(g)["position_bias"] == side
        assert GEN.self_check(g) == []


@pytest.mark.parametrize("mode", ["default","sparse","dense","varied_palette"])
def test_texture_aliases(mode):
    for i in range(4):
        assert GEN.generate(55,i,texture=mode) == GEN.generate(55,i,palette_kind=mode)
        assert GEN.generate(55,i,texture=mode,palette_kind=mode) == GEN.generate(55,i,texture=mode)


@pytest.mark.parametrize("overrides", [
    {"grid_h":True},{"grid_h":4.0},{"grid_w":"9"},{"n_cells":"3"},
    {"n_cells":0},{"n_distinct_colors":10},{"palette_size":False},
    {"grid_h":3},{"grid_w":27},{"n_cells":21},
    {"density":"garbage"},{"position_bias":"center"},{"texture":"typo"},
    {"typo":123},{"colors":[1,2,3]},
    {"palette_size":2,"n_distinct_colors":3},
    {"texture":"dense","palette_kind":"sparse"},
    {"n_cells":1,"n_distinct_colors":9},
    {"n_cells":1,"position_bias":"mixed"},
    {"grid_h":4,"grid_w":5,"n_cells":20},
    {"texture":"all_on_centerline","grid_w":8},
    {"texture":"no_cells","n_cells":1},
])
def test_invalid_or_incompatible_requests_fail(overrides):
    with pytest.raises(ValueError):
        GEN.generate(5,0,**overrides)


def test_none_is_absent_and_invalid_difficulty_fails():
    assert GEN.generate(1,2) == GEN.generate(1,2,grid_h=None,texture=None,palette_size=None)
    with pytest.raises(ValueError):
        GEN.generate(1,2,difficulty="expert")


@pytest.mark.parametrize("mode", ["no_cells","all_on_centerline","full_right_half"])
def test_lawful_explicit_edges_honor_shape(mode):
    opts={"grid_h":10,"grid_w":11,"texture":mode}
    if mode != "no_cells":
        opts.update(n_cells=6,n_distinct_colors=2)
    g=GEN.generate(6,2,**opts)
    assert (len(g),len(g[0])) == (10,11)
    assert GEN.self_check(g) == []
    assert len(occupied(g)) == (0 if mode=="no_cells" else 6)
    if mode=="all_on_centerline":
        assert all(c==5 for r,c,v in occupied(g))
        assert mirror(g)==g
    if mode=="full_right_half":
        assert all(c>5 for r,c,v in occupied(g))


@pytest.mark.parametrize("bad", [[],[[]],[[0],[0,1]],[[True]],[[1.5]],[[10]],[[2,0,0,0,3]]])
def test_validation_rejects_malformed_or_colliding_inputs(bad):
    assert GEN.self_check(bad)


def test_validation_accepts_lawful_rule_endpoints_and_existing_pairs():
    for g in ([[0]*5 for _ in range(4)], [[2,0,3,0,2]], [[0,0,0,0,4]]):
        assert GEN.self_check(g) == []
    assert mirror([[2,0,0,0,3]]) == [[3,0,0,0,2]]


def test_canonical_support_and_rule_pin():
    assert GEN.RULE_HASH == "26d859cbdb3e"
    for pair in canonical_pairs(TASK, root=ROOT):
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) in ([],True)
        assert mirror(pair["input"]) == pair["output"]
    for band in ("easy","medium","hard"):
        assert GEN.strict_canonical_like(GEN.generate(19,0,difficulty=band)) in ([],True)


def test_rich_profiles_and_every_query_rotation():
    assert GEN.LESSON_SCHEDULE_PERIOD == 4
    for band in ("easy","medium","hard"):
        for seed in range(8):
            for start in range(4):
                pairs=[]
                for i in range(start,start+4):
                    g=GEN.generate(seed,i,difficulty=band)
                    assert GEN.self_check(g) == []
                    cells=occupied(g)
                    if i%4:
                        off=[(r,c,v) for r,c,v in cells if 2*c != len(g[0])-1]
                        assert len(off)>=4
                        assert len({v for r,c,v in off}) < len(off)
                    if i%4 in (2,3):
                        assert len(g[0])%2==1
                        assert GEN.observe_overrides(g)["position_bias"]=="mixed"
                        assert any(2*c==len(g[0])-1 for r,c,v in cells)
                    pairs.append({"input":g,"output":mirror(g)})
                for held in range(4):
                    assert GEN.lesson_identifiable([p for j,p in enumerate(pairs) if j!=held],pairs[held]) == []


def test_lesson_hook_detects_a_real_query_ambiguity():
    demo=[[1,0,0,0,0],[0,2,0,0,0]]
    query=[[1,1,0,0,0],[0,0,0,0,0]]
    pair=lambda g:{"input":g,"output":mirror(g)}
    reasons=GEN.lesson_identifiable([pair(demo)]*3,pair(query))
    assert any("first_color" in reason for reason in reasons)
    assert GEN.lesson_identifiable([pair(query)]*3,pair(query)) == []


@pytest.mark.parametrize("index", [2,3])
def test_center_seed_counts_separately_from_off_axis_capacity(index):
    g=GEN.generate(0,index,difficulty="easy",grid_h=4,grid_w=5,n_cells=9)
    assert (len(g),len(g[0]),len(occupied(g))) == (4,5,9)
    assert sum(2*c==4 for r,c,v in occupied(g)) == 1
    assert GEN.observe_overrides(g)["position_bias"] == "mixed"
    assert GEN.self_check(g) == []
