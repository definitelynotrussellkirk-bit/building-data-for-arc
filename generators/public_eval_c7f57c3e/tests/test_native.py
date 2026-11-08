"""Native closure, settings, count independence and shuffled presentation."""
import importlib.util
import json
from pathlib import Path
import shutil

import pytest

HOME = Path(__file__).resolve().parents[1]
BASE = HOME / 'workspace' / 'parametric'


def load(path):
    spec = importlib.util.spec_from_file_location('_c7_adapter_test_' + str(path).encode().hex(), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def adapter():
    return load(BASE / 'adapter.py')


def test_local_canonical_resource_and_isolation(tmp_path, adapter):
    canonical = (BASE / 'canonical.rkt').read_bytes()
    assert canonical == (HOME / 'reference.rkt').read_bytes()
    assert adapter.program(adapter.SETTINGS[0]).encode() == canonical
    assert adapter.program(adapter.SETTINGS[1]) != adapter.program(adapter.SETTINGS[0])
    contract = json.loads((BASE / 'promotion.json').read_text())
    assert 'generators/public_eval_c7f57c3e/workspace/parametric/canonical.rkt' in contract['resources']
    isolated = tmp_path / 'generators' / HOME.name / 'workspace' / 'parametric'
    shutil.copytree(BASE, isolated, ignore=shutil.ignore_patterns('__pycache__', 'evidence'))
    relocated = load(isolated / 'adapter.py')
    assert relocated.program(relocated.SETTINGS[0]).encode() == canonical
    assert relocated.generate(17, relocated.SETTINGS[0], 2, 4) == adapter.generate(17, adapter.SETTINGS[0], 2, 4)


@pytest.mark.parametrize('demos', range(2, 7))
@pytest.mark.parametrize('queries', range(1, 5))
def test_counts_are_independent_stable_prefixes(adapter, demos, queries):
    for settings in adapter.SETTINGS:
        full = adapter.generate(17, settings, 6, 4)
        requested = adapter.generate(17, settings, demos, queries)
        assert requested['train'] == full['train'][:demos]
        assert requested['test'] == full['test'][:queries]


@pytest.mark.parametrize('seed', [0, 17, 43, 2**63-1])
def test_matched_streams_distinct_inputs_and_taught_parameter(adapter, seed):
    episodes = [adapter.generate(seed, settings, 2, 4) for settings in adapter.SETTINGS]
    banks = [[pair['input'] for pair in episode['train'] + episode['test']] for episode in episodes]
    assert banks[0] == banks[1]
    assert len({json.dumps(grid) for grid in banks[0]}) == 6
    assert any(left['output'] != right['output'] for left, right in zip(episodes[0]['train'], episodes[1]['train']))
    assert any(len(pair['input']) == len(pair['input'][0]) == 30 for pair in episodes[0]['test'])


def test_complete_query_bank_is_shuffled_before_prefix(adapter):
    first_indices = set()
    for seed in range(8):
        episode = adapter.generate(seed, adapter.SETTINGS[0], 2, 4)
        bank = [x[0] for x in adapter.inputs(seed)[1]]
        first_indices.add(bank.index(episode['test'][0]['input']))
        assert sorted(map(json.dumps, bank)) == sorted(json.dumps(p['input']) for p in episode['test'])
    assert len(first_indices) > 1


@pytest.mark.parametrize('field,bad', [(key, value) for key in ('seed', 'demos', 'queries')
                                    for value in (True, False, '2', 2.5, None, -1, 2**63)])
def test_integer_contract(adapter, field, bad):
    values = {'seed': 0, 'demos': 2, 'queries': 4, field: bad}
    with pytest.raises(ValueError):
        adapter.generate(settings=adapter.SETTINGS[0], **values)


@pytest.mark.parametrize('settings', [None, [], {}, {'replacement': True}, {'replacement': 'first'},
                                    {'replacement': ['swap']}, {'replacement': 'swap', 'extra': 1}])
def test_invalid_settings(adapter, settings):
    with pytest.raises(ValueError):
        adapter.program(settings)
    with pytest.raises(ValueError):
        adapter.generate(0, settings)
