"""Original-label and behavior regressions; never import the official gold in production."""
import importlib.util
import json
from pathlib import Path
import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]

def load():
    path = HOME / 'generator.py'
    assert path.is_file(), 'The assigned general wire-tracing generator is missing'
    spec = importlib.util.spec_from_file_location('wire_family_under_test', path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def originals():
    raw = ROOT / 'shared/data/raw'
    d = json.loads((raw/'arc-agi_evaluation_challenges.json').read_text())['a47bf94d']
    s = json.loads((raw/'arc-agi_evaluation_solutions.json').read_text())['a47bf94d']
    return d['train'] + [dict(input=p['input'], output=o) for p,o in zip(d['test'], s)]

@pytest.mark.parametrize('index', range(4))
def test_general_python_rule_matches_every_original(index):
    m = load(); p = originals()[index]
    assert m.solve(p['input']) == p['output']

def test_reference_executes_all_original_gold():
    path = HOME/'reference.rkt'
    assert path.is_file(), 'Missing general Racket reference'
    from arcpuzzles.parametric_worker import _real_evaluator
    apply, _, bridge = _real_evaluator(ROOT/'shared/runtime')
    try:
        for pair in originals():
            assert apply(path.read_text(), pair['input']) == pair['output']
    finally:
        bridge.close()

def adapter():
    path = HOME/'workspace/parametric/adapter.py'
    assert path.exists(), 'Native adapter is missing'
    spec = importlib.util.spec_from_file_location('wire_adapter_under_test', path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

@pytest.mark.parametrize('seed', [0,1,17,43,104,156])
def test_episode_counts_matched_streams_prefix_and_stress(seed):
    a = adapter(); canonical = a.generate(seed, {'finish':'paired'}, 6, 4)
    alternative = a.generate(seed, {'finish':'longest_sink_orange'}, 6, 4)
    assert canonical['program_solution'] == (HOME/'reference.rkt').read_text()
    assert len(canonical['train']) == 6 and len(canonical['test']) == 4
    ins = [p['input'] for sp in ('train','test') for p in canonical[sp]]
    assert len({json.dumps(x) for x in ins}) == 10
    assert any(len(x)==len(x[0])==30 and sum(v!=0 for row in x for v in row)>100 for x in ins)
    for sp in ('train','test'):
        assert [p['input'] for p in canonical[sp]] == [p['input'] for p in alternative[sp]]
        assert all(p['output'] != q['output'] for p,q in zip(canonical[sp],alternative[sp]))
    for demos in range(2,7):
        for queries in range(1,5):
            short=a.generate(seed, {'finish':'paired'}, demos, queries)
            assert short['train'] == canonical['train'][:demos]
            assert short['test'] == canonical['test'][:queries]
    m=load()
    for pair in alternative['train'][:2]:
        assert pair['output'] != m.solve(pair['input'],'longest_sink_orange','manhattan')

@pytest.mark.parametrize('args', [(-1,{'finish':'paired'},2,4),(True,{'finish':'paired'},2,4),
    (0,{},2,4),(0,{'finish':'bad'},2,4),(0,{'finish':'paired','extra':1},2,4),
    (0,{'finish':'paired'},1,4),(0,{'finish':'paired'},7,4),(0,{'finish':'paired'},2,0),
    (0,{'finish':'paired'},2,5),(0,{'finish':'paired'},2.0,4),(0,{'finish':'paired'},True,4)])
def test_invalid_api_rejected(args):
    with pytest.raises((ValueError,TypeError)):
        adapter().generate(*args)

def publisher():
    path=HOME/'workspace/parametric/public_views.py'
    assert path.exists(), 'Sequential public publisher is missing'
    spec=importlib.util.spec_from_file_location('wire_public_under_test',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_public_first_turn_is_prefix_stable_and_private_invariant(tmp_path):
    import copy
    a=adapter();pub=publisher();e=a.generate(17,{'finish':'paired'},2,4)
    one,order=pub.project(e,19,1);four,other=pub.project(e,19,4)
    assert one==four[:1] and order==other[:1]
    changed=copy.deepcopy(e);changed['settings']={'secret':'changed'};changed['program_solution']='secret'
    for p in changed['test']:p['output']=[[9]]
    assert pub.project(changed,19,4)==(four,other)
    for v in four:
        assert set(v)=={'train','test'} and len(v['test'])==1
        assert set(v['test'][0])=={'input'}
    firsts={pub.project(e,s,1)[1][0] for s in range(16)}
    assert len(firsts)>1
    receipt=pub.export(e,tmp_path/'public',19)
    assert len(receipt['mapping'])==4
    for row in receipt['mapping']:
        raw=(tmp_path/'public'/f"{row['id']}.json").read_bytes()
        import hashlib
        assert hashlib.sha256(raw).hexdigest()==row['id']
    assert receipt['physical_creation_order']==sorted(receipt['physical_creation_order'])

def test_publisher_rejects_duplicate_or_truncated_bank_before_writing(tmp_path):
    import copy
    e=adapter().generate(43,{'finish':'paired'},2,4);pub=publisher()
    e['test'][1]=copy.deepcopy(e['test'][0])
    with pytest.raises(ValueError):pub.export(e,tmp_path/'duplicates',0)
    assert not (tmp_path/'duplicates').exists()
    e['test']=e['test'][:1]
    with pytest.raises(ValueError):pub.project(e,0,1)

def test_declared_rivals_execute_and_two_demos_reject_them():
    a=adapter()
    from arcpuzzles.parametric_worker import _real_evaluator
    apply,_,bridge=_real_evaluator(ROOT/'shared/runtime')
    try:
        for finish in a.SETTINGS:
            setting={'finish':finish};e=a.generate(17,setting,2,4)
            for name,program in a.rival_programs(setting).items():
                labels=[apply(program,p['input']) for p in e['train']]
                assert any(g!=p['output'] for g,p in zip(labels,e['train'])), name
    finally:bridge.close()

def test_reusable_structural_auditor_checks_real_episodes():
    path=HOME/'workspace/parametric/audit.py'
    assert path.is_file(), 'Reusable structural auditor is missing'
    spec=importlib.util.spec_from_file_location('wire_auditor_test',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    result=m.structural([17])
    assert result['episodes']==2 and result['pairs']==20
    assert result['public_turns']==8 and result['failures']==[]
