"""Hand-checked fixtures for the findings-only audit's diagnostic rules."""
import importlib.util
from pathlib import Path
import pytest

PATH = Path(__file__).resolve().parents[1] / 'workspace/canonical_rival_probe.py'

def module():
    assert PATH.is_file(), 'canonical rival probe is not implemented yet'
    spec = importlib.util.spec_from_file_location('audit_probe', PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_fixed_color_plus_oracle_and_partial_rival():
    m = module()
    g = [[0,3,0], [3,0,3], [0,0,0]]
    assert m.reference('8b595f6acd93',g) == g
    assert m.predict('8b595f6acd93','at_least_three_green',g) == [[0,3,0],[3,4,3],[0,0,0]]
    full = [[0,3,0],[3,0,3],[0,3,0]]
    assert m.reference('8b595f6acd93',full)[1][1] == 4
    assert m.reference('8b595f6acd93',[[0,2,0],[2,0,2],[0,2,0]]) == [[0,2,0],[2,0,2],[0,2,0]]


def test_row_reference_preserves_multiple_sevens_and_nonseven_singleton():
    m = module()
    g = [[7,0,0],[7,0,7],[0,8,0],[0,0,0]]
    assert m.reference('c36d1678a484',g) == [[7,7,7],[7,0,7],[0,8,0],[0,0,0]]
    assert m.predict('c36d1678a484','any_seven',g) == [[7,7,7],[7,7,7],[0,8,0],[0,0,0]]
    assert m.predict('c36d1678a484','any_singleton',g) == [[7,7,7],[7,0,7],[8,8,8],[0,0,0]]


def test_diagnostic_functions_do_not_mutate_input():
    m = module()
    g = [[0,3,0],[3,0,3],[0,3,0]]
    old = [r[:] for r in g]
    for name in m.RIVALS['8b595f6acd93']:
        m.predict('8b595f6acd93',name,g)
    assert g == old


def test_gate_requires_a_generated_counterexample_for_canonical_discriminated_rival():
    m = module()
    assert hasattr(m,'coverage_gaps'), 'canonical retention gate is missing'
    stats = {'canonical':[{'rival_exact':{'bad_rule':False}}],
             'bands':{'easy':{'draws':10,'rival_exact_matches':{'bad_rule':10}}}}
    assert m.coverage_gaps(stats) == [{'band':'easy','rival':'bad_rule','draws':10}]
    stats['bands']['easy']['rival_exact_matches']['bad_rule']=9
    assert m.coverage_gaps(stats) == []


def test_gate_does_not_veto_an_unestablished_rival():
    m = module()
    assert hasattr(m,'coverage_gaps'), 'canonical retention gate is missing'
    stats = {'canonical':[{'rival_exact':{'maybe_equivalent':True}}],
             'bands':{'hard':{'draws':10,'rival_exact_matches':{'maybe_equivalent':10}}}}
    assert m.coverage_gaps(stats) == []
