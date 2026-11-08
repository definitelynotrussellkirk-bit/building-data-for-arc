"""Literal public-parent regression labels are author-private fixtures only."""
import importlib.util
import json
from pathlib import Path
import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = next(p for p in HOME.parents if (p / 'shared/data/raw/arc-agi_evaluation_challenges.json').is_file())

def module():
    path = HOME / 'workspace/parametric/prototype.py'
    assert path.is_file(), 'native prototype is not implemented'
    spec = importlib.util.spec_from_file_location('jigsaw_test_prototype', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def pairs():
    source = ROOT / 'shared/data/raw'
    task = json.loads((source / 'arc-agi_evaluation_challenges.json').read_text())['4e34c42c']
    gold = json.loads((source / 'arc-agi_evaluation_solutions.json').read_text())['4e34c42c']
    return task['train'] + [{'input': p['input'], 'output': y} for p, y in zip(task['test'], gold)]

@pytest.mark.parametrize('pair', pairs(), ids=['train0','train1','test0','test1'])
def test_all_original_labels(pair):
    assert module().solve(pair['input']) == pair['output']

def test_reference_is_authored():
    assert (HOME/'reference.rkt').is_file(), 'general Racket rule is missing'

def adapter():
    path=HOME/'workspace/parametric/adapter.py'
    assert path.is_file(), 'native adapter is not implemented'
    spec=importlib.util.spec_from_file_location('jigsaw_test_adapter',path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod

@pytest.mark.parametrize('seed', range(8))
def test_constructed_mosaics_are_recovered(seed):
    mod=module()
    assert hasattr(mod,'scene'), 'constructive sampler is missing'
    for index in range(4):
        x, expected = mod.scene(seed,index,stress=index==3)
        assert mod.solve(x)==expected
        assert mod.solve(x,bridge=True)!=expected
        if index==3:
            assert (len(x),len(x[0]))==(30,30)
            bg=mod.background(x)
            assert all(any(v!=bg for v in edge) for edge in [x[0],x[-1],[r[0] for r in x],[r[-1] for r in x]])
            assert sum(v!=bg for row in x for v in row)>=70

@pytest.mark.parametrize('demos',[2,3,6])
def test_counts_settings_and_independent_query_stream(demos):
    mod=adapter(); canonical={'finish_rule':'assemble'}; alt={'finish_rule':'assemble_then_bridge'}
    a=mod.generate(17,canonical,demos,4);b=mod.generate(17,alt,demos,4)
    assert len(a['train'])==demos and len(a['test'])==4
    assert [p['input'] for sp in ['train','test'] for p in a[sp]] == [p['input'] for sp in ['train','test'] for p in b[sp]]
    assert mod.program(canonical)==(HOME/'reference.rkt').read_text()
    assert all(x['output']!=y['output'] for x,y in zip(a['train'],b['train']))
    assert mod.generate(17,canonical,2,1)['test']==a['test'][:1]
    assert len({json.dumps(p['input']) for sp in ['train','test'] for p in a[sp]})==demos+4

@pytest.mark.parametrize('args',[(True,{'finish_rule':'assemble'},2,4),(0,{},2,4),(0,{'finish_rule':'bogus'},2,4),(0,{'finish_rule':'assemble','extra':1},2,4),(0,{'finish_rule':'assemble'},True,4),(0,{'finish_rule':'assemble'},7,4),(0,{'finish_rule':'assemble'},2,0)])
def test_strict_request_validation(args):
    with pytest.raises(ValueError): adapter().generate(*args)

def test_public_single_query_views():
    import copy
    mod=adapter();ep=mod.generate(43,{'finish_rule':'assemble'},2,4)
    assert hasattr(mod,'public_views'), 'safe controller projection is missing'
    views=mod.public_views(ep,17,4)
    assert mod.public_views(ep,17,1)==views[:1]
    assert all(set(v)=={'train','test'} and len(v['test'])==1 and set(v['test'][0])=={'input'} for v in views)
    changed=copy.deepcopy(ep);changed['program_solution']='PRIVATE';changed['settings']={'secret':999}
    for p in changed['test']: p['output']=[[9]]
    assert mod.public_views(changed,17,4)==views
    assert len({json.dumps(mod.public_views(ep,s,1)) for s in range(16)})>1
    views[0]['train'][0]['input'][0][0]=99
    assert ep['train'][0]['input'][0][0]!=99

@pytest.mark.parametrize('seed', range(16))
def test_partial_glyph_overlaps_are_reconstructed(seed):
    mod=module()
    x,y=mod.scene(seed,21,partial=True)
    assert mod.solve(x)==y

def test_generator_contract():
    path=HOME/'generator.py'
    assert path.is_file(), 'canonical generator is missing'
    spec=importlib.util.spec_from_file_location('jigsaw_production',path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    x=mod.generate(17,3)
    assert x==mod.generate(17,3)
    assert mod.self_check(x)==[]
    assert mod.self_check([[True]])
    with pytest.raises(ValueError): mod.generate(0,0,unknown=True)

@pytest.mark.parametrize('seed',[0,17,43,101])
def test_two_demos_teach_both_relay_orientations(seed):
    mod=adapter();a=mod.generate(seed,{'finish_rule':'assemble'},2,4);b=mod.generate(seed,{'finish_rule':'assemble_then_bridge'},2,4)
    axes=set()
    for p,q in zip(a['train'],b['train']):
        changed=[(r,c) for r,row in enumerate(p['output']) for c,v in enumerate(row) if v!=q['output'][r][c]]
        assert changed
        axes.add('horizontal' if len({r for r,c in changed})==1 else 'vertical')
    assert axes=={'horizontal','vertical'}
