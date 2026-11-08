"""Concrete rival semantics and the single-turn public projection boundary."""
from pathlib import Path
import importlib.util
import json
import pytest

HOME=Path(__file__).resolve().parents[1]/"workspace"/"parametric"


def audit_module():
    path=HOME/"audit.py"
    assert path.is_file(), "The native audit implementation is missing"
    spec=importlib.util.spec_from_file_location("reflection_audit_test",path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m


def example():
    return {"train":[{"input":[[0,2],[0,0]],"output":[[0,2],[2,0]]}],
            "test":[{"input":[[0,3],[0,0]],"output":[[0,3],[3,0]]},
                    {"input":[[0,7],[0,0]],"output":[[0,7],[7,0]]}],
            "settings":{"selection":"largest"},"seed":17,"program_solution":"PRIVATE"}


def test_one_turn_contains_only_visible_demos_and_current_input():
    m=audit_module();e=example()
    data=m.turn_bytes(e,0)
    assert json.loads(data)=={"train":e["train"],"test":[{"input":[[0,3],[0,0]]}]}
    e["test"][0]["output"]=[[9]];e["settings"]={"secret":1};e["seed"]=99
    e["program_solution"]="OTHER";e["test"][1]["input"]=[[8]]
    assert m.turn_bytes(e,0)==data


@pytest.mark.parametrize("index", [-1,2,True,0.0,"0"])
def test_turn_index_is_strict_and_bounded(index):
    with pytest.raises((ValueError,TypeError)):
        audit_module().turn_bytes(example(),index)


@pytest.mark.parametrize("bad", [[],[[True]],[[1.0]],[[10]],[[1],[2,3]],[[0]*31]])
def test_racket_result_grid_is_strict(bad):
    with pytest.raises(ValueError):
        audit_module().checked_grid(bad)


def test_wrong_order_is_a_real_executable_counterfactual():
    m=audit_module()
    source=[[0]*6 for _ in range(6)]
    for r,c,v in [(0,1,2),(1,1,2),(3,4,3),(3,5,3)]:source[r][c]=v
    all_expected=[[0]*6 for _ in range(6)]
    for r,c,v in [(0,1,2),(1,0,2),(1,1,2),(3,4,3),(3,5,3),(4,3,3),(5,3,3)]:all_expected[r][c]=v
    with m.Evaluator() as evaluator:
        for selection in ("largest","smallest"):
            wrong=evaluator.apply(m.rivals(selection)["select_before_reflect"],source)
            assert wrong==all_expected
            correct=evaluator.apply(m.FAMILY.program({"selection":selection}),source)
            assert correct!=wrong
        assert evaluator.identity["backend"]=="racket"
        assert evaluator.identity["protected"] is True


def test_color_insensitive_rival_preserves_cell_colors_when_merging():
    m=audit_module();programs=m.rivals("largest")
    assert "color_blind_components" in programs
    source=[[0]*6 for _ in range(6)]
    for r,c,v in [(0,1,2),(1,1,2),(0,2,3),(0,3,3)]:source[r][c]=v
    expected=[[0]*6 for _ in range(6)]
    for r,c,v in [(0,1,2),(1,0,2),(1,1,2),(0,2,3),(0,3,3),(2,0,3),(3,0,3)]:expected[r][c]=v
    with m.Evaluator() as evaluator:
        assert evaluator.apply(programs["color_blind_components"],source)==expected


def test_overlap_rival_cancels_only_initial_off_diagonal_pairs():
    m=audit_module()
    assert "cancel_initial_pairs" in m.rivals("all")
    source=[[0]*6 for _ in range(6)]
    for r,c,v in [(0,1,2),(1,0,2),(1,1,2),(3,4,3),(3,5,3)]:source[r][c]=v
    by_mode={"all":[(1,1,2),(3,4,3),(3,5,3),(4,3,3),(5,3,3)],
             "largest":[(3,4,3),(3,5,3),(4,3,3),(5,3,3)],"smallest":[(1,1,2)]}
    with m.Evaluator() as evaluator:
        for mode,cells in by_mode.items():
            expected=[[0]*6 for _ in range(6)]
            for r,c,v in cells:expected[r][c]=v
            assert evaluator.apply(m.rivals(mode)["cancel_initial_pairs"],source)==expected
