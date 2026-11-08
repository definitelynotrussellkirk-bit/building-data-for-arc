"""Native request surface and matched settings, independent of production API."""
import importlib.util
from pathlib import Path

import pytest

HOME=Path(__file__).resolve().parents[1]/'workspace/parametric'
spec=importlib.util.spec_from_file_location('orbit_adapter_test',HOME/'adapter.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)


def test_default_program_is_exact_selected_resource():
    assert a.program({'orientation_frame':'fixed'}).encode()==(HOME/'canonical.rkt').read_bytes()


@pytest.mark.parametrize('seed',[0,17,2**63-1])
def test_native_labels_and_inputs_share_one_episode_setting(seed):
    episodes=[a.generate(seed,{'orientation_frame':mode},4,4) for mode in ('fixed','source_side')]
    for episode in episodes:
        assert set(episode)=={'train','test','program_solution'}
        assert len(episode['train'])==len(episode['test'])==4
        assert all(set(pair)=={'input','output'} for split in ('train','test') for pair in episode[split])
    for split in ('train','test'):
        assert [p['input'] for p in episodes[0][split]]==[p['input'] for p in episodes[1][split]]
    assert any(x['output']!=y['output'] for x,y in zip(episodes[0]['train'],episodes[1]['train']))
    assert a.generate(seed)==episodes[seed%2]


@pytest.mark.parametrize('seed',[True,-1,2**63,0.0,'1',None])
def test_rejects_bad_seeds(seed):
    with pytest.raises((ValueError,TypeError)):a.generate(seed)


@pytest.mark.parametrize('demos,queries',[(3,4),(7,4),(4,0),(4,5),(True,4),(4,True),(4.0,4)])
def test_rejects_unsupported_counts(demos,queries):
    with pytest.raises((ValueError,TypeError)):a.generate(0,demos=demos,queries=queries)


@pytest.mark.parametrize('settings',[{}, {'orientation_frame':'unknown'}, {'orientation_frame':'fixed','x':0}])
def test_rejects_unknown_settings(settings):
    with pytest.raises(ValueError):a.generate(0,settings)


def test_returned_grids_are_fresh():
    original=a.generate(17);changed=a.generate(17)
    changed['train'][0]['input'][0][0]=9
    changed['test'][0]['output'][0][0]=9
    assert a.generate(17)==original
