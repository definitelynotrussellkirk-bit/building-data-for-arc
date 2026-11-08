"""Gate on public evidence, never on masked-query labels."""
import importlib.util
from pathlib import Path

PATH=Path(__file__).resolve().parents[1]/'workspace/lesson_ambiguity_gate.py'

def module():
    assert PATH.is_file(), 'public lesson ambiguity gate is missing'
    spec=importlib.util.spec_from_file_location('lesson_gate',PATH)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod


def example(query=3):
    return {'train':[{'input':[[1]],'output':[[2]]}],'test':[{'input':[[query]]}]}


def increment(grid):
    return [[v+1 for v in row] for row in grid]


def constant(grid):
    return [[2]]


def test_disagreeing_visible_consistent_programs_fail_gate():
    m=module()
    r=m.audit(example(),{'increment':increment,'constant':constant})
    assert r['status']=='AMBIGUOUS'
    assert r['ambiguous_queries']==[0]
    assert set(r['survivors'])=={'increment','constant'}
    assert not r['uses_query_labels']


def test_rival_already_refuted_by_visible_example_cannot_veto():
    m=module()
    r=m.audit(example(),{'increment':increment,'identity':lambda g:g})
    assert r['status']=='NO_KNOWN_QUERY_DISAGREEMENT'
    assert r['survivors']==['increment']


def test_surviving_programs_that_agree_on_query_do_not_veto():
    m=module()
    assert m.audit(example(query=1),{'increment':increment,'constant':constant})['status']=='NO_KNOWN_QUERY_DISAGREEMENT'


def test_query_labels_and_candidate_errors_never_silently_pass():
    m=module(); challenge=example(); challenge['test'][0]['output']=[[4]]
    assert m.audit(challenge,{'increment':increment})['status']=='ERROR'
    def broken(grid):
        raise ValueError('broken diagnostic')
    assert m.audit(example(),{'increment':increment,'broken':broken})['status']=='ERROR'


def test_candidate_mutation_cannot_contaminate_another_candidate_or_source():
    m=module(); challenge=example()
    def mutating(grid):
        grid[0][0]+=1
        return grid
    r=m.audit(challenge,{'mutating':mutating,'increment':increment})
    assert r['status']=='NO_KNOWN_QUERY_DISAGREEMENT'
    assert challenge==example()
