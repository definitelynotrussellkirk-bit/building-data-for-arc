import importlib.util
import json
from pathlib import Path
import pytest
HOME=Path(__file__).resolve().parents[1];ROOT=HOME.parents[1];BASE=HOME/'workspace/parametric'

def load():
    path=BASE/'family.py'
    assert path.is_file(), 'Keyed-template family has not been authored'
    spec=importlib.util.spec_from_file_location('abc_family_test',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

@pytest.mark.parametrize('index',range(6))
def test_every_original_label(index):
    f=load();ch=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['abc82100']
    gold=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['abc82100']
    pairs=ch['train']+[dict(input=p['input'],output=y) for p,y in zip(ch['test'],gold)]
    g=pairs[index]['input'];snapshot=json.dumps(g)
    assert f.solve(g)==pairs[index]['output']
    assert json.dumps(g)==snapshot

def test_touching_line_templates_are_partitioned_by_their_handles():
    f=load()
    # Cyan columns touch, but point in opposite directions and have distinct keys.
    g=[[6,6,0,0,0,0],[8,1,0,0,0,0],[8,8,0,0,0,0],
       [8,8,0,0,0,0],[2,8,0,0,0,0],[3,3,0,0,0,0]]
    assert f.solve(g)==[[1,0,0,0,0,0],[1,0,0,0,0,0],[1,0,0,0,0,0],
                        [0,2,0,0,0,0],[0,2,0,0,0,0],[0,2,0,0,0,0]]

def test_unmapped_markers_are_retained_and_stamps_clip():
    f=load()
    g=[[1,2,8,8,8],[0,0,0,0,1],[0,0,0,0,0],[0,0,0,0,6],[0,0,0,0,0]]
    assert f.solve(g)==[[0,0,0,0,0],[0,0,0,0,2],[0,0,0,0,0],[0,0,0,0,6],[0,0,0,0,0]]

def adapter():
    p=BASE/'adapter.py'
    assert p.exists(), 'Native keyed-template adapter missing'
    spec=importlib.util.spec_from_file_location('abc_adapter_test',p)
    a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a);return a

@pytest.mark.parametrize('seed',[0,1,17,43,104,156])
def test_native_counts_streams_labels_and_minimum_teaching(seed):
    f=load();a=adapter();original=a.generate(seed,{'finish':'stamp'},6,4);other=a.generate(seed,{'finish':'mark_overlap'},6,4)
    inputs=[p['input'] for s in ('train','test') for p in original[s]]
    assert len({json.dumps(g) for g in inputs})==10
    assert inputs==[p['input'] for s in ('train','test') for p in other[s]]
    for n in range(2,7):
        for q in range(1,5):
            ep=a.generate(seed,{'finish':'stamp'},n,q)
            assert ep['train']==original['train'][:n] and ep['test']==original['test'][:q]
    for setting,ep in [('stamp',original),('mark_overlap',other)]:
        assert ep['program_solution']==a.program({'finish':setting})
        assert any(len(p['input'])==len(p['input'][0])==30 for p in ep['test'])
        for s in ('train','test'):
            for p in ep[s]:assert f.solve(p['input'],setting)==p['output']
        for rival in f.rival_names(setting):
            assert any(f.rival(p['input'],setting,rival)!=p['output'] for p in ep['train'][:2]),(seed,setting,rival)
    for i in range(2):assert original['train'][i]['output']!=other['train'][i]['output']
    assert a.public_turn(a.generate(seed,{'finish':'stamp'},2,1))==a.public_turn(a.generate(seed,{'finish':'stamp'},2,4))

@pytest.mark.parametrize('bad',[True,1.5,'3',None,-1])
def test_counts_are_exact_integers(bad):
    with pytest.raises(ValueError):adapter().generate(0,{'finish':'stamp'},bad,4)

@pytest.mark.parametrize('bad',[{}, {'finish':'x'}, {'finish':'stamp','extra':1}])
def test_settings_are_strict(bad):
    with pytest.raises(ValueError):adapter().program(bad)

def test_canonical_exact_and_no_query_ordinal_leakage():
    a=adapter()
    assert a.program({'finish':'stamp'}).encode()==(HOME/'reference.rkt').read_bytes()==(BASE/'canonical.rkt').read_bytes()
    assert len({a.generate(seed,{'finish':'stamp'},2,4)['private']['source_indices'][0] for seed in range(24)})==4
    ep=a.generate(7,{'finish':'stamp'},2,4);ep['train'][0]['private']={'secret':19}
    view=a.public_turn(ep)
    assert set(view)=={'train','test'}
    assert all(set(p)=={'input','output'} for p in view['train'])
    assert set(view['test'][0])=={'input'}

def test_exact_overlap_not_bounding_box_overlap():
    f=load();a=adapter();ep=a.generate(17,{'finish':'mark_overlap'},2,4)
    p=ep['train'][0]
    out,count,instances=f.expand(p['input'])
    assert any(n>=2 for n in count.values())
    assert p['output']!=f.rival(p['input'],'mark_overlap','bounding_box')
    assert any(len(instance['cells'])>1 for instance in instances)

def test_public_writer_validates_before_writing_and_uses_content_names(tmp_path):
    path=BASE/'publication.py'
    assert path.exists(), 'Auditable public publication helper missing'
    spec=importlib.util.spec_from_file_location('abc_publication_test',path)
    p=importlib.util.module_from_spec(spec); spec.loader.exec_module(p)
    a=adapter();ep=a.generate(3,{'finish':'stamp'},2,4)
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
