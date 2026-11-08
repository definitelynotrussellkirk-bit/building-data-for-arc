import importlib.util
import json
from pathlib import Path
import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
BASE = HOME / 'workspace/parametric'

def load():
    path = BASE / 'family.py'
    assert path.is_file(), 'The native family implementation has not been authored'
    spec = importlib.util.spec_from_file_location('fc7_family_test', path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

@pytest.mark.parametrize('index', range(4))
def test_original_labels(index):
    m = load()
    ch = json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['fc7cae8d']
    gold = json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['fc7cae8d']
    pairs = ch['train'] + [dict(input=ch['test'][0]['input'], output=gold[0])]
    before = pairs[index]['input']
    snapshot = json.dumps(before)
    assert m.solve(before) == pairs[index]['output']
    assert json.dumps(before) == snapshot

def test_hand_checked_orientation_convention():
    m = load(); g = [[1,2,3],[4,5,6]]
    assert m.transform(g, 1) == [[4,1],[5,2],[6,3]]
    assert m.transform(g, 4) == [[3,2,1],[6,5,4]]
    assert m.transform(g, 7) == [[1,4],[2,5],[3,6]]

def test_seal_only_four_connected_top_regions():
    m = load()
    # The central zero is only diagonally connected to the upper opening.
    g = [[1,0,1,1],[1,1,0,1],[0,1,1,1],[1,1,1,1]]
    assert m.seal_top(g) == [[1,1,1,1],[1,1,0,1],[0,1,1,1],[1,1,1,1]]

def adapter():
    path = BASE / 'adapter.py'
    assert path.is_file(), 'Native adapter is missing'
    spec = importlib.util.spec_from_file_location('fc7_adapter_test', path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

@pytest.mark.parametrize('seed', [0,1,17,43,104,156])
def test_counts_prefixes_matched_inputs_and_stress(seed):
    a = adapter(); m = load()
    full = a.generate(seed, {'finish':'orient'}, 6, 4)
    alternate = a.generate(seed, {'finish':'seal_top'}, 6, 4)
    inputs = [p['input'] for split in ('train','test') for p in full[split]]
    assert len({json.dumps(g) for g in inputs}) == 10
    assert inputs == [p['input'] for split in ('train','test') for p in alternate[split]]
    assert any(len(p['input']) == len(p['input'][0]) == 30 for p in full['test'])
    for n in range(2,7):
        for q in range(1,5):
            ep = a.generate(seed, {'finish':'orient'}, n, q)
            assert ep['train'] == full['train'][:n]
            assert ep['test'] == full['test'][:q]
    for setting,ep in [('orient', full),('seal_top',alternate)]:
        assert ep['program_solution'] == a.program({'finish':setting})
        for split in ('train','test'):
            for pair in ep[split]:
                assert m.solve(pair['input'],setting) == pair['output']
    for d in range(2):
        assert full['train'][d]['output'] != alternate['train'][d]['output']
    # The actual public turn cannot depend on how many answers the controller requests.
    assert a.public_turn(a.generate(seed,{'finish':'orient'},2,1),0) == a.public_turn(a.generate(seed,{'finish':'orient'},2,4),0)

@pytest.mark.parametrize('bad', [True, 1.5, '3', None, -1])
def test_exact_integer_counts(bad):
    with pytest.raises(ValueError): adapter().generate(0, {'finish':'orient'},bad,4)

@pytest.mark.parametrize('bad', [{}, {'finish':'bad'}, {'finish':'orient','extra':0}])
def test_setting_schema_is_strict(bad):
    with pytest.raises(ValueError): adapter().program(bad)

def test_canonical_source_exact_and_first_query_is_shuffled():
    a=adapter()
    assert a.program({'finish':'orient'}).encode() == (HOME/'reference.rkt').read_bytes()
    observed={a.generate(s, {'finish':'orient'},2,4)['private']['source_indices'][0] for s in range(24)}
    assert len(observed) == 4
    assert (BASE/'canonical.rkt').read_bytes() == (HOME/'reference.rkt').read_bytes()

def test_minimum_curriculum_refutes_declared_rivals():
    a=adapter(); m=load()
    for seed in range(24):
        for finish in ('orient','seal_top'):
            ep=a.generate(seed,{'finish':finish},2,4)
            for name in m.rival_names(finish):
                assert any(m.rival(p['input'],finish,name)!=p['output'] for p in ep['train']), (seed,finish,name)

def test_public_projection_is_an_allowlist():
    a=adapter(); ep=a.generate(7, {'finish':'orient'}, 2,4)
    ep['train'][0]['private']={'secret':19}
    view=a.public_turn(ep)
    assert set(view)=={'train','test'}
    assert all(set(p)=={'input','output'} for p in view['train'])
    assert set(view['test'][0])=={'input'}

def test_public_writer_validates_before_writing_and_uses_content_names(tmp_path):
    path=BASE/'publication.py'
    assert path.exists(), 'Auditable public publication helper missing'
    spec=importlib.util.spec_from_file_location('fc7_publication_test',path)
    p=importlib.util.module_from_spec(spec); spec.loader.exec_module(p)
    a=adapter();ep=a.generate(3,{'finish':'orient'},2,4)
    views=[a.public_turn(ep,i) for i in range(4)]
    invalid=views+[{'train':views[0]['train'], 'test':ep['test']}]
    with pytest.raises(ValueError):p.publish(invalid,tmp_path/'bad')
    assert not (tmp_path/'bad').exists()
    with pytest.raises(ValueError):p.publish([views[0],views[0]],tmp_path/'dup')
    assert not (tmp_path/'dup').exists()
    ids=p.publish(views,tmp_path/'public')
    assert ids==sorted(ids)
    assert p.verify(tmp_path/'public')==4
    first=tmp_path/'public'/ids[0]
    first.write_text('{}')
    with pytest.raises(ValueError):p.verify(tmp_path/'public')
