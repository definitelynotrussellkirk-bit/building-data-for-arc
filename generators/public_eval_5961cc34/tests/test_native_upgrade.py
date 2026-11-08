"""Portability, branch-depth ties, and independently requested query prefixes."""
from pathlib import Path
import importlib.util
import json
import os
import random
import shutil
import subprocess
import sys

import pytest

HOME=Path(__file__).resolve().parents[1]
BASE=HOME/'workspace/parametric'


def load(name):
    path=BASE/(name+'.py')
    assert path.exists(), 'Missing implementation: '+name
    spec=importlib.util.spec_from_file_location('_upgrade596_'+name,path)
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
    return m


def test_generator_runs_without_task_workspace(tmp_path):
    from reviewer_support import find_root
    shutil.copy2(HOME/'generator.py',tmp_path/'generator.py')
    code="""import generator
for path in (0,3,6):
    g=generator.generate(17,0,grid_h=24,grid_w=30,path_id=path)
    assert (len(g),len(g[0]))==(24,30)
    assert not generator.self_check(g)
print('standalone generation passed')
"""
    env=dict(os.environ,PYTHONPATH=str(find_root(__file__)/'shared/runtime'),PYTHONDONTWRITEBYTECODE='1')
    p=subprocess.run([sys.executable,'-c',code],cwd=tmp_path,env=env,
                     capture_output=True,text=True,timeout=30)
    assert p.returncode==0,p.stderr


def test_standalone_generator_is_reproducible_from_native_sources():
    builder=load('build_generator')
    assert (HOME/'generator.py').read_text()==builder.render_generator()


@pytest.mark.parametrize('queries',[1,2,3])
def test_independently_requested_query_prefix(queries):
    a=load('adapter');f=load('family')
    for settings in a.SETTINGS:
        full=a.generate(17,settings,2,4)
        short=a.generate(17,settings,2,queries)
        assert short['test']==full['test'][:queries]
        assert short['private_query_bank']==full['test']
        assert f.public_view(short,0)==f.public_view(full,0)


def test_query_order_does_not_reveal_stress_ordinal():
    a=load('adapter');indices=set()
    for seed in range(32):
        e=a.generate(seed,{'finish':'trace_only'},2,4)
        indices.update(i for i,p in enumerate(e['test']) if len(p['input'])==len(p['input'][0])==30)
    assert indices==set(range(4)), '30x30 query is still hardwired to the final turn'


@pytest.mark.parametrize('orientation',range(8))
def test_fanout_profile_activates_two_tied_deepest_relays(orientation):
    s,m=load('sampler'),load('model')
    g=s.draw(17,0,split='production',grid_h=24,grid_w=30,
             path_id=6,band=2,transform_id=orientation)
    assert (len(g),len(g[0]))==(24,30)
    info=m.analyze(g)
    assert sorted(info['depths'].values())==[1,2,2]
    deepest=[i for i,d in info['depths'].items() if d==2]
    out=m.solve(g,'highlight_deepest')
    assert all(out[r][c]==9 for i in deepest for r,c in info['objects'][i]['cells'])
    assert len(info['depths'])<len(info['objects']), 'unreachable decoy must remain'


def test_two_demos_teach_all_deepest_not_one_deepest():
    a,m=load('adapter'),load('model')
    assert 'single_deepest' in m.RIVALS and 'single_port' in m.RIVALS
    for seed in range(24):
        e=a.generate(seed,{'finish':'highlight_deepest'},2,4)
        assert any(sum(d==max(x['depths'].values()) for d in x['depths'].values())>1
                   for x in (m.analyze(p['input']) for p in e['train']))
        for name in ('single_deepest','single_port'):
            assert any(m.rival(p['input'],'highlight_deepest',name)!=p['output'] for p in e['train'])


def test_protected_racket_on_branch_geometry():
    from reviewer_support import find_root
    from arcpuzzles.parametric_worker import _real_evaluator
    a=load('adapter');m=load('model');s=load('sampler')
    apply,identity,bridge=_real_evaluator(find_root(__file__)/'shared/runtime')
    try:
        assert identity['backend']=='racket' and identity['protected']
        for h,w in ((24,30),(30,30)):
            for orientation in range(8):
                g=s.draw(29,1,split='production',grid_h=h,grid_w=w,path_id=6,
                         band=1+orientation%2,transform_id=orientation)
                for setting in a.SETTINGS:
                    assert apply(a.program(setting),g)==m.solve(g,setting['finish'])
    finally:bridge.close()


def test_generation_preserves_global_rng_state():
    a=load('adapter');state=random.getstate()
    a.generate(71,{'finish':'highlight_deepest'},6,4)
    assert random.getstate()==state


def test_causal_selection_prefers_substantive_stress_and_propagates_errors():
    tool=load('authoring')
    assert hasattr(tool,'select_causal_pair'), 'causal selection helper missing'
    small={'input':[[1,1],[1,1]],'output':[[1,1],[1,1]]}
    big={'input':[[1]*30 for _ in range(30)],'output':[[1]*30 for _ in range(30)]}
    ep={'train':[small], 'test':[small,big]}
    def execute(text,grid):
        return grid if text=='actual' else [[0]*len(grid[0]) for _ in grid]
    assert tool.select_causal_pair(ep,'actual','counter',execute) is big
    def broken(text,grid):
        raise RuntimeError('protected execution failed')
    with pytest.raises(RuntimeError):tool.select_causal_pair(ep,'actual','counter',broken)
    assert tool.select_causal_pair(ep,'actual','actual',execute) is None


def terminal_prediction(model,g):
    info=model.analyze(g)
    lookup={p:i for i,o in enumerate(info['objects']) for p in o['cells']}
    out=[row[:] for row in info['output']]
    for i in info['depths']:
        o=info['objects'][i];dr,dc=o['direction'];hit=False
        for r,c in o['markers']:
            r+=dr;c+=dc
            while 0<=r<len(g) and 0<=c<len(g[0]):
                if (r,c) in lookup:hit=True;break
                r+=dr;c+=dc
        if not hit:
            for r,c in o['cells']:out[r][c]=9
    return out


def test_minimum_demos_reject_terminal_shortcut():
    a,m=load('adapter'),load('model')
    for seed in range(32):
        e=a.generate(seed,{'finish':'highlight_deepest'},2,4)
        assert any(terminal_prediction(m,p['input'])!=p['output'] for p in e['train']), seed


def test_terminal_racket_matches_independent_rival():
    from reviewer_support import find_root
    from arcpuzzles.parametric_worker import _real_evaluator
    path=BASE/'terminal-shortcut.rkt'
    assert path.exists(), 'missing protected semantic rival'
    a,m=load('adapter'),load('model')
    apply,_,bridge=_real_evaluator(find_root(__file__)/'shared/runtime')
    try:
        e=a.generate(0,{'finish':'highlight_deepest'},2,4)
        for p in e['train']+e['test']:
            assert apply(path.read_text(),p['input'])==terminal_prediction(m,p['input'])
    finally:bridge.close()
