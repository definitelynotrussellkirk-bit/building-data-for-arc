"""Candidate-local disjoint-rule contract checks."""
from pathlib import Path
import importlib.util
import pytest

def family():
    path=Path(__file__).resolve().parents[1]/"workspace/parametric/union_family.py"
    spec=importlib.util.spec_from_file_location("union_contract_b37eb391ddc0",path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

@pytest.mark.parametrize("seed",[0,17])
def test_shared_two_demo_lesson_and_prefixes(seed):
    m=family();key="completion_scope"
    es=[m.generate(seed,{key:s},6,4) for s in m.SETTINGS]
    assert len({repr([p["input"] for p in e["train"]+e["test"]]) for e in es})==1
    assert len({repr([p["output"] for p in e["train"][:2]]) for e in es})==3
    for s,e in zip(m.SETTINGS,es):
        small=m.generate(seed,{key:s},2,1)
        assert small["train"]==e["train"][:2]
        assert small["test"]==e["test"][:1]
        assert len({repr(p["input"]) for p in e["train"]+e["test"]})==10
        assert all(len(p["output"])<=30 and len(p["output"][0])<=30 for p in e["train"]+e["test"])
    assert any(len(p["input"])==len(p["input"][0])==30 for p in es[0]["test"])

def test_prior_programs_and_default_are_exact():
    m=family();key="completion_scope"
    for mode in m.SETTINGS[:2]:
        assert m.program({key:mode})==m.old.program({key:mode})
    assert m.program()==m.old.program({key:m.SETTINGS[0]})
