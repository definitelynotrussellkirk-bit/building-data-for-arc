"""Native symmetry/filter/rank contract, independent of production approval."""
from copy import deepcopy
import importlib.util
import itertools
import json
from pathlib import Path

import pytest

HOME=Path(__file__).resolve().parents[1]/"workspace/parametric"
spec=importlib.util.spec_from_file_location("symmetry_native_test",HOME/"native_family.py")
native=importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


def settings():
    return [{"axis":a,"keep_policy":p} for a,p in itertools.product(native.AXES,native.POLICIES)]


def test_exact_canonical_and_all_complete_programs():
    from arcpuzzles import Catalog
    from reviewer_support import find_root
    from puzzle_generators.rule_wrap import wrap_rule
    record=Catalog(find_root(__file__)).get("a86a630485ac")
    expected={v["program_solution"] for v in record["variants"]}
    assert expected == {native.program({"axis":"lr","keep_policy":"all"})}
    for s in settings():
        assert wrap_rule(native.program(s)).startswith("(lambda")


def test_component_identity_uses_color_and_four_neighbors():
    source=[[0]*8 for _ in range(6)]
    source[0][0]=source[1][1]=2
    source[0][1]=3
    objects=native.components(source)
    assert sorted((o["color"],o["size"]) for o in objects) == [(2,1),(2,1),(3,1)]
    assert native.apply_python(source,{"axis":"lr","keep_policy":"largest_eligible"}) == source


def test_literal_filter_before_rank_and_ties():
    source=[[0]*12 for _ in range(8)]
    # Two equal-size symmetric dominoes, plus an asymmetric larger L.
    for r,c in [(0,0),(1,0),(5,10),(6,10)]:
        source[r][c]=2
    for r,c in [(1,5),(2,5),(3,5),(3,6)]:
        source[r][c]=7
    expected=deepcopy(source)
    for r,c in [(1,5),(2,5),(3,5),(3,6)]:
        expected[r][c]=0
    for axis in native.AXES:
        assert native.apply_python(source,{"axis":axis,"keep_policy":"largest_eligible"}) == expected
        assert sum(v!=0 for row in expected for v in row)==4


def test_empty_eligible_and_empty_grid_are_total():
    source=[[0]*8 for _ in range(6)]
    for r,c in [(1,2),(2,2),(3,2),(3,3)]:
        source[r][c]=4
    blank=[[0]*8 for _ in range(6)]
    for s in settings():
        assert native.apply_python(source,s)==blank
        assert native.apply_python(blank,s)==blank


@pytest.mark.parametrize("index,dimensions",[(2,(6,8)),(6,(6,8)),(8,(23,29))])
def test_dense_boundary_profiles_fit_constructive_slots(index,dimensions):
    source=native._scene(0,index)
    assert (len(source),len(source[0]))==dimensions
    assert len(native.components(source))==(4 if index in (2,6) else 6)


@pytest.mark.parametrize("seed",[0,17,2**63-1])
def test_prefixes_matched_inputs_and_valid_episodes(seed):
    base=native.generate(seed,settings()[0],6,4)
    all_inputs=[p["input"] for split in ("train","test") for p in base[split]]
    assert len({json.dumps(g) for g in all_inputs})==10
    for s in settings():
        full=native.generate(seed,s,6,4)
        short=native.generate(seed,s,2,1)
        ordinary=native.generate(seed,s)
        assert len(ordinary["train"])==3 and len(ordinary["test"])==4
        assert short["train"]==full["train"][:2]
        assert short["test"]==full["test"][:1]
        assert [p["input"] for split in ("train","test") for p in full[split]]==all_inputs
        assert native.generate(seed,s,6,4)==full
        for split in ("train","test"):
            for pair in full[split]:
                native.validate_grid(pair["input"])
                assert pair["output"]==native.apply_python(pair["input"],s)
                assert all(type(v) is int for row in pair["output"] for v in row)


def test_minimum_teaching_core_distinguishes_all_settings():
    for seed in (0,1,17,2**63-1):
        for s in settings():
            e=native.generate(seed,s,2,4)
            for other in settings():
                if other!=s:
                    assert any(native.apply_python(p["input"],other)!=p["output"] for p in e["train"])


def test_first_two_teach_ties_occupied_counts_and_wrong_order():
    for axis in native.AXES:
        e=native.generate(0,{"axis":axis,"keep_policy":"largest_eligible"},2,4)
        first_objects=native.components(e["train"][0]["input"])
        eligible=[o for o in first_objects if native.is_symmetric(o["cells"],axis)]
        best=max(o["size"] for o in eligible)
        winners=[o for o in eligible if o["size"]==best]
        assert len(winners)==2
        assert max(o["size"] for o in first_objects)>best
        second_objects=native.components(e["train"][1]["input"])
        eligible=[o for o in second_objects if native.is_symmetric(o["cells"],axis)]
        best=max(o["size"] for o in eligible)
        area=lambda o:(o["bbox"][2]-o["bbox"][0]+1)*(o["bbox"][3]-o["bbox"][1]+1)
        assert {o["cells"] for o in eligible if o["size"]==best}!={o["cells"] for o in eligible if area(o)==max(map(area,eligible))}


def test_core_contains_count_balanced_but_asymmetric_shape():
    source=native.generate(0,settings()[0],2,1)["train"][0]["input"]
    def balanced(obj):
        r0,c0,r1,c1=obj["bbox"]
        rows=[sum(r==rr for r,c in obj["cells"]) for rr in range(r0,r1+1)]
        cols=[sum(c==cc for r,c in obj["cells"]) for cc in range(c0,c1+1)]
        return rows==rows[::-1] and cols==cols[::-1]
    traps=[o for o in native.components(source) if balanced(o)
           and not native.is_symmetric(o["cells"],"lr")
           and not native.is_symmetric(o["cells"],"ud")]
    assert len(traps)==1 and traps[0]["size"]==8


@pytest.mark.parametrize("s",settings())
def test_two_demos_refute_eight_connectivity_even_for_ranked_winners(s):
    def rival(grid):
        unseen={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v}
        objects=[]
        while unseen:
            start=min(unseen)
            color=grid[start[0]][start[1]]
            todo=[start]
            cells=set()
            unseen.remove(start)
            while todo:
                r,c=todo.pop()
                cells.add((r,c))
                for dr in (-1,0,1):
                    for dc in (-1,0,1):
                        point=(r+dr,c+dc)
                        if point in unseen and grid[point[0]][point[1]]==color:
                            unseen.remove(point)
                            todo.append(point)
            if native.is_symmetric(cells,s["axis"]):
                objects.append((cells,color))
        if s["keep_policy"]=="largest_eligible" and objects:
            best=max(len(cells) for cells,color in objects)
            objects=[o for o in objects if len(o[0])==best]
        result=[[0]*len(grid[0]) for _ in grid]
        for cells,color in objects:
            for r,c in cells:
                result[r][c]=color
        return result
    for seed in (0,17):
        e=native.generate(seed,s,2,4)
        assert any(rival(p["input"])!=p["output"] for p in e["train"])


def test_size_stress_contains_large_shapes_dense_content_and_boundaries():
    for s in settings():
        e=native.generate(0,s,6,4)
        large=[p for split in ("train","test") for p in e[split] if len(p["input"])==len(p["input"][0])==30]
        assert len(large)==2
        for pair in large:
            assert sum(v!=0 for row in pair["input"] for v in row)>300
            assert sum(v!=0 for row in pair["output"] for v in row)>=196
            assert {(r>=15,c>=15) for r,row in enumerate(pair["output"]) for c,v in enumerate(row) if v}=={(False,False),(False,True),(True,False),(True,True)}
            assert any(pair["input"][0]) and any(pair["input"][-1])
            assert any(row[0] for row in pair["input"]) and any(row[-1] for row in pair["input"])
            assert max(o["size"] for o in native.components(pair["input"]))==80


def test_queries_shuffle_without_count_dependency():
    orders=[]
    for seed in range(8):
        e=native.generate(seed,settings()[0],2,4)
        orders.append(tuple((len(p["input"]),len(p["input"][0])) for p in e["test"]))
    assert len(set(orders))>1


@pytest.mark.parametrize("kwargs",[
    {"seed":True},{"seed":1.0},{"seed":-1},{"seed":2**63},
    {"demos":1},{"demos":7},{"demos":3.0},{"queries":0},{"queries":5},{"queries":True},
    {"settings":{}},{"settings":{"axis":"lr"}},
    {"settings":{"axis":"lr","keep_policy":"other"}},
    {"settings":{"axis":"lr","keep_policy":"all","extra":1}},
])
def test_invalid_requests_fail(kwargs):
    request={"seed":0,"settings":{"axis":"lr","keep_policy":"all"},"demos":3,"queries":4}
    request.update(kwargs)
    with pytest.raises((TypeError,ValueError)):
        native.generate(**request)


@pytest.mark.parametrize("source",[
    [], [[0]*8 for _ in range(5)],[[0]*31 for _ in range(6)],
    [[False]*8 for _ in range(6)],[[10]*8 for _ in range(6)],
    [[0]*8 for _ in range(5)]+[[0]*7],
])
def test_invalid_grids_fail(source):
    with pytest.raises((TypeError,ValueError)):
        native.apply_python(source,{"axis":"ud","keep_policy":"largest_eligible"})


def test_generation_and_application_have_no_shared_mutable_outputs():
    e=native.generate(0,settings()[0])
    before=deepcopy(e)
    native.apply_python(e["train"][0]["input"],settings()[1])
    assert e==before
    e["train"][0]["input"][0][0]=9
    assert native.generate(0,settings()[0])==before
