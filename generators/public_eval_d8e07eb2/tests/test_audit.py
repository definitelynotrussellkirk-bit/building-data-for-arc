"""The future-agent audit executes its contract, rather than grepping code."""
import importlib.util
from pathlib import Path
import pytest

PATH=Path(__file__).resolve().parents[1]/'workspace/parametric/audit_lessons.py'

def load():
    assert PATH.is_file(), 'Ship the reusable audit'
    s=importlib.util.spec_from_file_location('_d8_audit_test',PATH);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def test_two_seed_audit_counts_real_lessons_and_rivals():
    r=load().audit(2)
    assert r['episodes']==12 and r['stress_30x30_pairs']==12
    assert r['labeled_pairs']==108 and r['harmful_survivors']==[] and r['failures']==[]
    assert r['minimum_demos']==4 and len(r['rivals'])>=10
    assert r['status']=='passed_bounded_generated_checks'

@pytest.mark.parametrize('bad',[0,-1,True,1.5,1025])
def test_bad_audit_bounds_rejected(bad):
    with pytest.raises(ValueError):load().audit(bad)
