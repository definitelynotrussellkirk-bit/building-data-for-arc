"""Focused typed API, shared-input and visibility checks for the three-rule union."""
from pathlib import Path
from copy import deepcopy
import importlib.util,json
import pytest
HOME=Path(__file__).resolve().parents[1]/'workspace/parametric'
s=importlib.util.spec_from_file_location('_4eb_union_contract',HOME/'adapter.py');A=importlib.util.module_from_spec(s);s.loader.exec_module(A)

def test_typed_settings_and_contract_have_exactly_three_strategies():
    c=json.loads((HOME/'promotion.json').read_text());assert c['parameters']=={'target_degree':[0,1,'anchor_area']};assert c['default']=={'target_degree':0}
    for v in (True,False,0.0,1.0,2,None,'0','1','anchor',[],{}):
        with pytest.raises((ValueError,TypeError)):A.program({'target_degree':v})
    assert A.program({'target_degree':0})==A.DEGREE.program({'target_degree':0})
    assert A.program({'target_degree':1})==A.DEGREE.program({'target_degree':1})
    assert A.program({'target_degree':'anchor_area'})==A.ANCHOR.program({'selection':'anchor_sized_twos'})


def test_shared_inputs_count_prefixes_and_first_turn_privacy():
    for seed in (0,17):
        reference=None
        for settings in A.SETTINGS:
            long=A.generate(seed,settings,6,4);short=A.generate(seed,settings,2,1)
            assert short['train']==long['train'][:2] and short['test']==long['test'][:1]
            inputs={split:[p['input'] for p in long[split]] for split in ('train','test')}
            if reference is not None:assert inputs==reference
            reference=inputs
            first={'train':long['train'][:2],'test':long['test']}
            visible=A.public_turn(first)
            assert visible==A.public_turn(short)
            hidden=deepcopy(first);hidden.update(settings={'private':1},program_solution='private',seed=999)
            for p in hidden['train']:p['private']='private'
            for p in hidden['test']:p['output']=[[9]]
            for p in hidden['test'][1:]:p['input']=[[9]]
            assert A.public_turn(hidden)==visible
        stress=reference['test'][2]
        assert len(stress)==len(stress[0])==30
        assert sum(v!=0 for row in stress for v in row)>=100
        for grid in reference['train']+reference['test']:
            assert A.ANCHOR.analyze(grid)['anchor_size']>=2
            boundary=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==2 and (r in (0,len(grid)-1) or c in (0,len(row)-1))]
            assert any(all(not(0<=r+dr<len(grid) and 0<=c+dc<len(grid[0])) or grid[r+dr][c+dc]!=2 for dr,dc in A.ANCHOR.EIGHT) for r,c in boundary)


def test_invalid_count_and_seed_types_fail_before_execution():
    for args in ((True,2,4),(-1,2,4),(0,True,4),(0,1,4),(0,7,4),(0,2,True),(0,2,0),(0,2,5)):
        with pytest.raises((ValueError,TypeError)):A.generate(args[0],{'target_degree':0},args[1],args[2])
