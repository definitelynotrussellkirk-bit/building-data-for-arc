"""Native vertical-then-horizontal contracts; expectations are hand-derived."""
from pathlib import Path
import importlib.util
import copy
import json
import pytest

HOME = Path(__file__).resolve().parents[1] / 'workspace/parametric'

def adapter():
    path = HOME / 'adapter.py'
    assert path.is_file(), 'Native adapter is missing'
    spec = importlib.util.spec_from_file_location('vertical_composition_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_stage_b_needs_new_vertical_cells():
    a = adapter()
    g = [[2,0,3,0,0,0,0], [0,0,0,0,2,0,0], [0,0,3,0,0,0,0],
         [0,0,0,0,0,0,0], [2,0,0,0,0,0,0], [0,0,3,0,2,0,0]]
    expected = [[2,0,3,0,0,0,0], *[[2,2,2,2,2,0,0] for _ in range(4)], [0,0,3,0,2,0,0]]
    assert a.solve(g, 'vertical_then_horizontal') == expected
    assert a.solve(g, 'vertical_only') != expected
    assert a.pass_axis(a.pass_axis(g, 'horizontal'), 'vertical') != expected


def test_third_completed_bar_suppresses_horizontal_join():
    a = adapter()
    g = [[2,0,0,0,0,0,2], [0,0,0,2,0,0,0], [0]*7,
         [0,0,0,2,0,0,0], [2,0,0,0,0,0,2]]
    expected = [[2]*7, *[[2,0,0,2,0,0,2] for _ in range(3)], [2]*7]
    assert a.solve(g, 'vertical_then_horizontal') == expected


def test_pass_uses_frozen_counts_and_first_occurrence_overwrite_order():
    a = adapter()
    assert a.pass_axis([[2,3,2,3]], 'horizontal') == [[2,3,3,3]]
    assert a.pass_axis([[2],[3],[2],[3]], 'vertical') == [[2],[3],[3],[3]]


def test_episode_counts_prefixes_matched_inputs_and_no_duplicates():
    a = adapter()
    for seed in (0,17,91):
        for n in range(2,7):
            eps = [a.generate(seed, {'composition':m}, n, 4) for m in a.MODES]
            for e in eps:
                assert len(e['train']) == n and len(e['test']) == 4
                keys=[json.dumps(p['input']) for p in e['train']+e['test']]
                assert len(set(keys)) == n+4
                assert e == a.generate(seed, {'composition':a.MODES[eps.index(e)]}, n, 4)
                assert a.teaching_audit(e)['query_disagreeing_survivors'] == []
            assert [p['input'] for p in eps[0]['train']+eps[0]['test']] == [p['input'] for p in eps[1]['train']+eps[1]['test']]
            assert a.generate(seed, {'composition':a.MODES[0]}, n, 1)['test'] == eps[0]['test'][:1]
            assert a.generate(seed, {'composition':a.MODES[0]}, 2, 4)['train'] == eps[0]['train'][:2]


def test_boundary_has_real_structure_not_padding():
    a = adapter()
    for mode in a.MODES:
        e = a.generate(17, {'composition':mode}, 3, 4)
        p=e['test'][3]; g=p['input']; out=p['output']
        assert len(g) == len(g[0]) == len(out) == len(out[0]) == 30
        assert sum(v != 0 for row in g for v in row) >= 55
        assert all(any(row) for row in (g[0],g[-1]))
        assert any(r[0] for r in g) and any(r[-1] for r in g)
        assert sum(v != 0 for row in out for v in row) >= 350


@pytest.mark.parametrize('args', [(True,{'composition':'vertical_only'},3,4),
 (0,{},3,4), (0,{'composition':'bogus'},3,4),
 (0,{'composition':'vertical_only','secret':1},3,4),
 (0,{'composition':'vertical_only'},1,4), (0,{'composition':'vertical_only'},7,4),
 (0,{'composition':'vertical_only'},True,4), (0,{'composition':'vertical_only'},3,0),
 (0,{'composition':'vertical_only'},3,5), (0,{'composition':'vertical_only'},3,4.0)])
def test_requests_fail_closed(args):
    with pytest.raises(ValueError): adapter().generate(*args)


def test_public_turn_ignores_all_private_fields_and_is_independent():
    a=adapter(); e=a.generate(8, {'composition':a.MODES[1]},3,4)
    original=copy.deepcopy(e); before=a.public_turn_bytes(e,0)
    assert a.public_turn_bytes(a.generate(8, {'composition':a.MODES[1]},3,1),0)==before
    e['program_solution']='private'; e['settings']={'canary':'private'};e['seed']=888
    for pair in e['train']: pair['private']='never public'
    for pair in e['test']: pair['output']=[[9]];pair['private']='never public'
    assert before==a.public_turn_bytes(e,0)
    assert set(json.loads(before))=={'train','test'}
    assert len(json.loads(before)['test'])==1
    assert set(json.loads(before)['test'][0])=={'input'}
    assert e != original
    with pytest.raises(ValueError): a.public_turn_bytes(e,True)


def test_program_has_one_complete_expression_and_default_exact_bytes():
    from arc_repl.parser import parse_all
    a=adapter()
    assert a.program({'composition':a.MODES[0]}).encode()==(HOME/'canonical.rkt').read_bytes()
    for mode in a.MODES:
        assert len(parse_all(a.program({'composition':mode})))==1


def test_two_demos_refute_repeating_the_pipeline_seed5_regression():
    a=adapter();e=a.generate(5,{'composition':a.MODES[1]},2,4)
    assert 'repeat_vh_twice' not in a.teaching_audit(e)['survivors']


def test_two_demos_refute_horizontal_at_least_two_seed1_regression():
    a=adapter();e=a.generate(1,{'composition':a.MODES[1]},2,4)
    assert 'horizontal_at_least_two' not in a.teaching_audit(e)['survivors']


def test_reusable_audit_counts_all_supported_demo_lengths():
    path=HOME/'audit.py'
    assert path.is_file(), 'Reusable audit is missing'
    spec=importlib.util.spec_from_file_location('vertical_audit_test',path)
    audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
    report=audit.run_sweep(2)
    assert report['episodes']==20 and report['labeled_pair_checks']==160
    assert report['failures']==[] and report['demonstration_counts']==[2,3,4,5,6]
