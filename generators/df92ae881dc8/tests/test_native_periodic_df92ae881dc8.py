"""Independent pixel fixtures and strict native periodic-completion contracts."""
import importlib.util
import json
from pathlib import Path
import pytest
from reviewer_support import find_root

BASE=find_root(__file__)/'generators/df92ae881dc8/workspace/parametric'


def load(name):
    p=BASE/(name+'.py')
    assert p.is_file(), f'{name} must be implemented'
    s=importlib.util.spec_from_file_location('test_periodic_'+name,p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    return m


def test_measured_period_controls_full_column_spacing_literal_fixture():
    m=load('native')
    g=[[0,2,0,2,0,0] for _ in range(3)]+[[0,2,0,0,0,0] for _ in range(3)]
    assert m.predict(g,'observed') == [[5,2,5,2,5,2] for _ in range(6)]
    assert m.predict(g,'doubled') == [[5,2,5,2,5,2] for _ in range(3)]+[[5,2,5,5,5,2] for _ in range(3)]
    assert m.analyze(g,'doubled')['observed_period']==2
    assert m.analyze(g,'doubled')['effective_period']==4


def test_nested_l_area_competition_and_bottommost_tie_literal_fixture():
    m=load('native')
    g=[[0]*6 for _ in range(6)]
    g[1][:3]=g[3][:3]=[2]*3
    want=[[5,5,5,5,2,5],[2,2,2,5,2,5],[5,5,5,5,2,5],
          [2,2,2,5,2,5],[5,5,5,5,2,5],[2,2,2,2,2,5]]
    assert m.predict(g,'observed')==want
    assert m.analyze(g,'observed')['chosen_run']==[3,0,2,3]
    assert m.analyze(g,'observed')['winner']==[1,1]
    assert m.predict(g,'doubled')==[[2 if v==2 else 5 for v in row] for row in g]


def test_canonical_program_is_exact_selected_bytes():
    m=load('adapter')
    assert m.program({'spacing':'observed'}) == (BASE/'canonical.rkt').read_text()
    assert m.program({'spacing':'doubled'}) != (BASE/'canonical.rkt').read_text()


@pytest.mark.parametrize('kw', [
    {'seed':True},{'seed':-1},{'seed':2**63},{'demos':2},{'demos':3},{'demos':7},{'demos':3.0},
    {'queries':0},{'queries':5},{'queries':True},
    {'settings':{'spacing':'other'}},{'settings':{'spacing':'observed','extra':1}},
    {'settings':{'spacing':False}},
])
def test_requests_reject_coercions_unknowns_and_unsupported_counts(kw):
    m=load('adapter');args=dict(seed=0,settings={'spacing':'observed'},demos=4,queries=4)
    args.update(kw)
    with pytest.raises(ValueError):m.generate(**args)


def test_banks_are_setting_independent_distinct_count_independent_and_substantive():
    m=load('native')
    for seed in (0,1,17):
        ref=m.generate(seed,{'spacing':'observed'},6,4)
        for mode in m.MODES:
            for n in range(4,7):
                e=m.generate(seed,{'spacing':mode},n,4)
                assert len(e['train'])==n and len(e['test'])==4
                ins=[p['input'] for p in e['train']+e['test']]
                assert ins==[p['input'] for p in ref['train'][:n]+ref['test']]
                assert len(set(map(json.dumps,ins)))==n+4
                assert m.generate(seed,{'spacing':mode},n,1)['test']==e['test'][:1]
                assert len(e['test'][0]['input'])==len(e['test'][0]['input'][0])==6
                g=e['test'][3]['input']
                assert len(g)==len(g[0])==30 and sum(v!=0 for row in g for v in row)>=100
                assert all(any(edge) for edge in (g[0],g[-1],[r[0] for r in g],[r[-1] for r in g]))


def test_minimum_lesson_teaches_period_both_branches_and_tie_precedence():
    m=load('native')
    for seed in range(8):
        for mode in m.MODES:
            e=m.generate(seed,{'spacing':mode},4,4)
            assert m.teaching_check(e,mode)['ambiguous']==[]
            facts=[m.analyze(p['input'],mode) for p in e['train']]
            assert {f['observed_period'] for f in facts}=={2,3,4}
            assert {f['branch'] for f in facts}=={'full_columns','nested_l'}
            assert set(facts[0]['directions'])=={-1,1}


def test_protected_racket_matches_both_branches_and_30x30_claims():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    m=load('native')
    with RacketBridge() as b:
        assert b.runtime_identity['protected'] is True
        for mode in m.MODES:
            for seed in (0,1):
                e=m.generate(seed,{'spacing':mode},4,4)
                for pair in e['train']+e['test']:
                    datum="'("+' '.join('('+' '.join(map(str,row))+')' for row in pair['input'])+')'
                    assert b.eval_text(f'({wrap_rule(e["program_solution"])} {datum})')==pair['output']


def test_cached_input_bank_is_not_exposed_to_caller_mutation():
    m=load('adapter');settings={'spacing':'observed'}
    before=m.generate(7,settings,4,4)
    changed=m.generate(7,settings,4,4)
    changed['train'][0]['input'][0][0]=9
    changed['test'][3]['input'][1][1]=9
    assert m.generate(7,settings,4,4)==before


def test_bounded_audit_separates_claim_checks_from_executed_labels():
    m=load('audit');report=m.run(seeds=2,racket_seeds=())
    assert report['episodes']==12 and report['labeled_pair_checks']==108
    assert report['distinct_inputs']==20
    assert report['failures']==[] and report['protected_racket_evaluations']==0
    assert report['regression']['old_rival_fits_demos'] is True
    assert report['regression']['old_rival_differs_query'] is True
    assert report['regression']['new_refuting_demos']
