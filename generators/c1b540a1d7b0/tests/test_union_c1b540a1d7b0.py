"""Candidate-local disjoint-rule contract checks."""
from pathlib import Path
import importlib.util
import pytest

def family():
    path=Path(__file__).resolve().parents[1]/"workspace/parametric/union_family.py"
    spec=importlib.util.spec_from_file_location("union_contract_c1b540a1d7b0",path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

@pytest.mark.parametrize("seed",[0,17])
def test_shared_two_demo_lesson_and_prefixes(seed):
    m=family();key="component_scope"
    es=[m.generate(seed,{key:s},6,4) for s in m.SETTINGS]
    assert len({repr([p["input"] for p in e["train"]+e["test"]]) for e in es})==1
    assert len({repr([p["output"] for p in e["train"][:2]]) for e in es})==4
    for s,e in zip(m.SETTINGS,es):
        small=m.generate(seed,{key:s},2,1)
        assert small["train"]==e["train"][:2]
        assert small["test"]==e["test"][:1]
        assert len({repr(p["input"]) for p in e["train"]+e["test"]})==10
        assert all(len(p["output"])<=30 and len(p["output"][0])<=30 for p in e["train"]+e["test"])
    assert any(len(p["input"])==len(p["input"][0])==30 for p in es[0]["test"])

def test_prior_programs_and_default_are_exact():
    m=family();key="component_scope"
    for mode in m.retained.SETTINGS:
        assert m.program({key:mode})==m.retained.program({key:mode})
    assert m.program()==m.old.program({key:m.SETTINGS[0]})


def test_minimum_lesson_preserves_all_declared_teaching_contrasts():
    m=family()
    for seed in (0,17):
        episode=m.generate(seed,{"component_scope":"armiest_component"},2,4)
        names,first=m.teaching_rejections(episode["train"][0]["input"])
        same_names,second=m.teaching_rejections(episode["train"][1]["input"])
        assert names==same_names and len(names)==31
        assert first|second==names

def test_legacy_aliases_and_exact_incoming_program():
    m=family()
    assert m.program({"room_policy":"largest_room"})==m.program({"component_scope":"largest_residual_room"})
    assert m.program({"finish_rule":"classify_only"})==m.program()
    assert m.program({"finish_rule":"classify_then_highlight_armiest"})==m.program({"component_scope":"armiest_component"})
    assert m.program({"component_scope":"armiest_component"})==m.armiest.program({"finish_rule":"classify_then_highlight_armiest"})


def test_residual_maximum_varies_and_fixed_size_shortcuts_fail():
    m=family()
    observed=set()
    for seed in (0,4,17,49):
        episode=m.generate(seed,{"component_scope":"largest_residual_room"},2,4)
        demos=[m.residual_maximum(p["input"]) for p in episode["train"]]
        queries=[m.residual_maximum(p["input"]) for p in episode["test"]]
        assert len(set(demos))==2
        assert len(set(queries))>=2
        observed.update(demos+queries)
        expected=[p["output"] for p in episode["train"]]
        for size in (3,4,6):
            assert [m.fixed_residual_size(p["input"],size) for p in episode["train"]]!=expected
    assert observed=={3,4,6}
