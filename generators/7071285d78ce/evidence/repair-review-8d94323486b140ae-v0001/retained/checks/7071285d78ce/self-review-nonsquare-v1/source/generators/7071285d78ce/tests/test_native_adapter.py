"""Native request isolation and one-query public-projection checks."""
import copy
import importlib.util
from pathlib import Path

import pytest
from reviewer_support import public_challenge_bytes

HOME=Path(__file__).resolve().parents[1]


def adapter():
    spec=importlib.util.spec_from_file_location('transpose_adapter_test',HOME/'workspace/parametric/adapter.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('seed',[0,17,2**63-1])
def test_setting_inputs_and_count_prefixes_do_not_reveal_private_choice(seed):
    a=adapter();settings=['all','largest','smallest']
    episodes=[a.generate(seed,{'selection':v},3,4) for v in settings]
    for split in ('train','test'):
        grids=[[p['input'] for p in e[split]] for e in episodes]
        assert grids[0]==grids[1]==grids[2]
    for choice,episode in zip(settings,episodes):
        single=a.generate(seed,{'selection':choice},3,1)
        visible={'train':episode['train'],'test':episode['test'][:1]}
        assert public_challenge_bytes(single)==public_challenge_bytes(visible)
        mutated=copy.deepcopy(episode)
        mutated['seed']=-1;mutated['settings']={'selection':'private'}
        mutated['program_solution']='private';mutated['test'][0]['output']=[[9]]
        mutated['test']=mutated['test'][:1]
        assert public_challenge_bytes(mutated)==public_challenge_bytes(visible)


@pytest.mark.parametrize('seed',[True,False,-1,2**63,1.0,'1',None])
def test_invalid_seed_is_rejected_before_sampling(seed):
    with pytest.raises(ValueError):adapter().generate(seed)


@pytest.mark.parametrize('settings',[{},[],{'selection':1},{'selection':False},
    {'selection':'ALL'},{'selection':'all','extra':0}])
def test_undeclared_settings_are_rejected(settings):
    with pytest.raises(ValueError):adapter().generate(0,settings)


def test_missing_setting_choice_is_deterministic():
    a=adapter()
    for seed,choice in enumerate(['all','largest','smallest']):
        assert a.generate(seed)==a.generate(seed,{'selection':choice})
