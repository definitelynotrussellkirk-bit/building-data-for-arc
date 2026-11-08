"""Promotion boundary and setting-neutral teaching for crossing bands."""
import importlib.util
import json
from pathlib import Path
import random
import sys
import types

import pytest

HOME=Path(__file__).resolve().parents[1]
ROOT=HOME.parents[1]
SOURCE=HOME/'workspace/parametric/adapter.py'


def adapter():
    assert SOURCE.is_file(), 'Missing guarded layer-selection promotion adapter'
    spec=importlib.util.spec_from_file_location('_layer_adapter_test',SOURCE)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def inputs(episode):return [p['input'] for p in episode['train']+episode['test']]


def test_adapter_preserves_both_exact_programs_and_canonical_default():
    module=adapter()
    canonical={row['program_solution'] for line in (ROOT/'shared/data/canonical/puzzles.jsonl').read_text().splitlines()
               if (row:=json.loads(line))['task_id']=='7b0cb3b9a618'}
    assert canonical=={module.program({'target_layer':'front'})}
    for setting in ['front','back']:
        assert module.program({'target_layer':setting})==(SOURCE.parent/(setting+'.rkt')).read_text()


def test_inputs_are_neutral_between_settings_and_global_rng_is_untouched():
    module=adapter();before=random.getstate()
    episodes=[module.generate(17,{'target_layer':setting},3,4) for setting in ['front','back']]
    assert inputs(episodes[0])==inputs(episodes[1]) and random.getstate()==before
    assert episodes[0]==module.generate(17,{'target_layer':'front'},3,4)
    assert len({json.dumps(value) for value in inputs(episodes[0])})==7
    assert all(a['output']!=b['output'] for a,b in zip(episodes[0]['train'],episodes[1]['train']))


@pytest.mark.parametrize('demos,queries',[(2,1),(2,10),(2,22),(12,32)])
def test_independent_counts_and_previous_retry_regression(demos,queries):
    module=adapter()
    first=module.generate(190807,{'target_layer':'front'},demos,queries)
    second=module.generate(190807,{'target_layer':'back'},demos,queries)
    assert len(first['train'])==demos and len(first['test'])==queries
    assert inputs(first)==inputs(second)
    assert len({json.dumps(value) for value in inputs(first)})==demos+queries


def test_shared_demonstrations_reject_each_declared_shortcut_for_both_rules():
    module=adapter();prototype=module._prototype
    for setting in ['front','back']:
        episode=module.generate(0,{'target_layer':setting},3,4)
        rivals=[prototype.rival_predictions(p['input']) for p in episode['train']]
        assert all(any(row[name]!=pair['output'] for row,pair in zip(rivals,episode['train'])) for name in rivals[0])
        for pair in episode['train']+episode['test']:
            assert pair['output']==[[prototype.visible_endpoints(pair['input'])[setting]]]


@pytest.mark.parametrize('seed,settings,demos,queries',[(True,{'target_layer':'front'},3,4),
    (0,{'target_layer':'front','other':1},3,4),(0,{'target_layer':'middle'},3,4),
    (0,{'target_layer':'front'},True,4),(0,{'target_layer':'front'},2,0)])
def test_invalid_direct_requests_fail_explicitly(seed,settings,demos,queries):
    with pytest.raises(ValueError):adapter().generate(seed,settings,demos,queries)


def test_unrelated_cached_module_cannot_supply_the_adapter(monkeypatch):
    enemy=types.ModuleType('layer_selection');enemy.program_for=lambda *_:'wrong rule'
    monkeypatch.setitem(sys.modules,'layer_selection',enemy)
    assert adapter().program({'target_layer':'back'})==(SOURCE.parent/'back.rkt').read_text()
