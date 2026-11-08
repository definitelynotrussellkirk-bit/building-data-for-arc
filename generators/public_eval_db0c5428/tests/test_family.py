"""Behavioral tests; fixtures are author-private and never used by generation."""
from pathlib import Path
import importlib.util
import json
from copy import deepcopy
import subprocess
import sys
import pytest
HOME = Path(__file__).resolve().parents[1]
BASE = HOME / 'workspace/parametric'

def load(name):
    path = BASE / (name + '.py')
    assert path.is_file(), f'missing implementation: {path.name}'
    spec = importlib.util.spec_from_file_location('_db0c_test_'+name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

@pytest.mark.parametrize('index', range(4))
def test_supplied_labels(index):
    p = json.loads((HOME/'tests/originals.json').read_text())[index]
    assert load('prototype').solve(p['input'], 'all') == p['output']

def manual():
    g = [[8]*15 for _ in range(15)]
    for r in range(3,12):
        for c in range(3,12):
            if not (6<=r<=8 and 6<=c<=8):g[r][c]=6
    tips = [(5,5),(5,7),(5,9),(7,5),(7,9),(9,5),(9,7),(9,9)]
    for r,c in tips:g[r][c]=2
    g[9][9]=1
    return g

def test_literal_rarest_tip_tie_free_and_exact_reflection():
    g=manual(); want=deepcopy(g)
    for r,row in enumerate([[2,2,2],[2,6,2],[2,2,1]]):
        want[6+r][6:9]=row
    want[12][12:15]=[6,6,6]
    want[13][12:15]=[6,6,6]
    want[14][12:15]=[6,6,1]
    assert load('prototype').solve(g,'rarest_tip')==want

def test_preserves_input_and_all_original_foreground():
    P=load('prototype');g=manual();before=deepcopy(g);out=P.solve(g,'all')
    assert g==before
    assert all(out[r][c]==v for r,row in enumerate(g) for c,v in enumerate(row) if v!=8)
    assert out[0][0]==2 and out[14][14]==1

@pytest.mark.parametrize('demos',[2,3,6])
def test_count_boundary_matched_inputs_and_query_invariance(demos):
    A=load('adapter');e=A.generate(17,{'extension_scope':'all'},demos,4)
    f=A.generate(17,{'extension_scope':'rarest_tip'},demos,4)
    assert e==A.generate(17,{'extension_scope':'all'},demos,4)
    assert len(e['train'])==demos and len(e['test'])==4
    assert [p['input'] for sp in ('train','test') for p in e[sp]]==[p['input'] for sp in ('train','test') for p in f[sp]]
    assert e['test']==A.generate(17,{'extension_scope':'all'},2,4)['test']
    assert len({json.dumps(p['input']) for sp in ('train','test') for p in e[sp]})==demos+4
    assert any(p['output']!=q['output'] for p,q in zip(e['train'],f['train']))

@pytest.mark.parametrize('args',[(True,2,4),(0,True,4),(0,1,4),(0,7,4),(0,2,True),(0,2,3),(0,2,5)])
def test_invalid_counts_fail_closed(args):
    seed,demos,queries=args
    with pytest.raises(ValueError):load('adapter').generate(seed,{'extension_scope':'all'},demos,queries)

@pytest.mark.parametrize('setting',[{}, {'extension_scope':True},{'extension_scope':'unknown'},{'extension_scope':'all','extra':0}])
def test_invalid_settings(setting):
    with pytest.raises(ValueError):load('adapter').program(setting)

def test_canonical_bytes_and_standalone_sampler(tmp_path):
    A=load('adapter')
    assert A.program({'extension_scope':'all'}).encode()==(HOME/'reference.rkt').read_bytes()
    assert (BASE/'sampler.py').read_bytes()==(HOME/'generator.py').read_bytes()
    p=tmp_path/'generator.py';p.write_bytes((HOME/'generator.py').read_bytes())
    script="import generator;g=generator.generate(17,0);assert generator.self_check(g)==[];assert len(g)>=15"
    result=subprocess.run([sys.executable,'-I','-c',f"import sys;sys.path.insert(0,{str(tmp_path)!r});"+script],capture_output=True,text=True)
    assert result.returncode==0,result.stderr

def test_30x30_is_four_distributed_rings():
    A=load('adapter');P=load('prototype');g=A.generate(43,{'extension_scope':'all'},2,4)['test'][3]['input']
    assert (len(g),len(g[0]))==(30,30)
    bg,rings=P.extract(g);assert len(rings)==4
    assert all(any(g[r][c]!=bg for r in range(y,y+15) for c in range(x,x+15)) for y in (0,15) for x in (0,15))

def test_known_finite_rivals_are_rejected_by_demonstrations():
    report=load('audit').audit(list(range(8)),[2,3,6])
    assert report['status']=='passed',report.get('failures')
