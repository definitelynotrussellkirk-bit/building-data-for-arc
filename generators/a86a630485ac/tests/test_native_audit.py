"""Independent geometry, mathematical rival semantics, and hole detector tests."""
import importlib.util
from pathlib import Path
import pytest

HOME=Path(__file__).resolve().parents[1]/"workspace/parametric"

def load(name):
    path=HOME/(name+".py")
    assert path.exists(), "Independent teaching audit has not been implemented"
    spec=importlib.util.spec_from_file_location("symmetry_audit_test_"+name,path)
    result=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

def scene(objects,h=9,w=19):
    g=[[0]*w for _ in range(h)]
    for color,cells in objects:
        for r,c in cells:
            g[r][c]=color
    return g

T={(0,0),(0,1),(0,2),(1,1),(2,1)}
U={(r+4,c+7) for c,r in T}
A={(r+4,c) for r in range(3) for c in range(3)}-{(6,2)}
S={(7,13),(8,13)}

def test_literal_symmetry_filter_then_rank_and_blank():
    audit=load("audit_native")
    g=scene([(2,T),(3,U),(4,A),(5,S)])
    assert audit.expected(g,{"axis":"lr","keep_policy":"all"})==scene([(2,T),(5,S)])
    assert audit.expected(g,{"axis":"ud","keep_policy":"largest_eligible"})==scene([(3,U)])
    assert audit.expected(scene([(4,A)]),{"axis":"lr","keep_policy":"largest_eligible"})==scene([])

def test_all_largest_ties_are_kept_and_global_ranking_is_wrong():
    audit=load("audit_native")
    other={(r,c+10) for r,c in T}
    g=scene([(2,T),(3,other),(4,A),(5,S)])
    s={"axis":"lr","keep_policy":"largest_eligible"}
    intended=scene([(2,T),(3,other)])
    assert audit.expected(g,s)==intended
    assert audit.expected(g,s,"global_rank_before_filter")==scene([])
    assert audit.expected(g,s,"first_winner")==scene([(2,T)])
    assert audit.expected(g,s,"last_winner")==scene([(3,other)])

def test_connectivity_and_color_aggregation_are_distinct():
    audit=load("audit_native")
    g=scene([(2,{(0,0),(1,1),(5,5)}),(3,{(0,1)})])
    assert sorted(map(len,audit.components(g)))==[1,1,1,1]
    assert sorted(map(len,audit.components(g,"eight_connectivity")))==[1,1,2]
    assert sorted(map(len,audit.components(g,"color_aggregate")))==[1,3]
    assert sorted(map(len,audit.components(g,"multicolor_eight")))==[1,3]

def test_detector_negative_and_strict_missing_predictions():
    audit=load("audit_native")
    episode={"train":[{"output":[[2]]}],"test":[{"output":[[4]]}]}
    assert audit.classify(episode,[[[2]]],[[[9]]])=={"status":"teaching_hole","demo_mismatches":[],"query_mismatches":[0]}
    assert audit.classify(episode,[[[8]]],None)["status"]=="refuted_by_demos"
    assert audit.classify(episode,[[[2]]],[[[4]]])["status"]=="survivor_agrees_all_queries"
    with pytest.raises(ValueError):
        audit.classify(episode,[[[2]]],None)
    with pytest.raises(ValueError):
        audit.classify(episode,[],[])

def test_minimum_demos_refute_mathematical_rivals_or_agree_queries():
    audit=load("audit_native")
    native=load("native_family")
    for settings in audit.SETTINGS:
        for seed in (0,17):
            episode=native.generate(seed,settings,2,4)
            for split in ("train","test"):
                for pair in episode[split]:
                    assert audit.expected(pair["input"],settings)==pair["output"]
            for rival in audit.rivals(settings):
                demos=[audit.expected(p["input"],settings,rival) for p in episode["train"]]
                queries=[audit.expected(p["input"],settings,rival) for p in episode["test"]]
                result=audit.classify(episode,demos,queries)
                assert result["status"]!="teaching_hole",(settings,seed,rival,result)
                assert audit.rival_program(settings,rival).startswith("(rule!")


def test_histogram_palindrome_does_not_imply_bitmap_symmetry():
    audit=load("audit_native")
    cells={(r,c) for r,row in enumerate(("1100","0110","0110","0011")) for c,v in enumerate(row) if v=="1"}
    g=scene([(7,cells)])
    for axis in ("lr","ud"):
        settings={"axis":axis,"keep_policy":"largest_eligible"}
        assert not audit.symmetric(cells,axis)
        assert audit.expected(g,settings)==scene([])
        assert audit.expected(g,settings,"mirrored_counts")==g


def test_occupied_count_ranking_differs_from_box_and_peak_rank():
    audit=load("audit_native")
    sparse={(0,c) for c in range(7)}|{(r,3) for r in range(7)}
    dense={(r,c) for r in range(4) for c in range(10,14)}
    g=scene([(2,sparse),(3,dense)])
    settings={"axis":"lr","keep_policy":"largest_eligible"}
    assert audit.expected(g,settings)==scene([(3,dense)])
    for rival in ("bbox_area_rank","bbox_longest_rank","row_peak_rank","column_peak_rank"):
        assert audit.expected(g,settings,rival)==scene([(2,sparse)])


def test_selected_component_preserves_shape_and_not_all_matching_color():
    audit=load("audit_native")
    g=scene([(2,T|A)])
    settings={"axis":"lr","keep_policy":"all"}
    assert audit.expected(g,settings)==scene([(2,T)])
    assert audit.expected(g,settings,"selected_colors")==g
    assert audit.expected(g,settings,"fill_bbox")==scene([(2,{(r,c) for r in range(3) for c in range(3)})])
    assert audit.expected(g,settings,"fixed_color_1")==scene([(1,T)])
