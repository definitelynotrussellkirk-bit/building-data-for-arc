"""Native boundary, settings matching, and count-independent episodes."""
import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1] / 'workspace' / 'parametric'


@pytest.fixture(scope='module')
def adapter():
    path = HERE / 'adapter.py'
    assert path.is_file(), 'native adapter has not been implemented'
    spec = importlib.util.spec_from_file_location('skyline_adapter_tests', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('seed', [0, 17, 2**63 - 1])
def test_matched_inputs_distinct_settings_and_query_prefix(adapter, seed):
    all_ep = adapter.generate(seed, {'survivor_filter': 'all'}, 3, 4)
    modal = adapter.generate(seed, {'survivor_filter': 'modal_color'}, 3, 4)
    for split in ('train', 'test'):
        assert [p['input'] for p in all_ep[split]] == [p['input'] for p in modal[split]]
    assert any(a['output'] != b['output'] for a, b in zip(all_ep['train'], modal['train']))
    assert set(all_ep) == {'train', 'test', 'program_solution'}
    assert all_ep['program_solution'] == adapter.program({'survivor_filter': 'all'})
    short = adapter.generate(seed, {'survivor_filter': 'all'}, 3, 1)
    assert short['train'] == all_ep['train'] and short['test'] == all_ep['test'][:1]
    longer = adapter.generate(seed, {'survivor_filter': 'all'}, 6, 4)
    assert longer['train'][:3] == all_ep['train'] and longer['test'] == all_ep['test']


@pytest.mark.parametrize('settings', [{}, {'survivor_filter': 1}, {'survivor_filter': 'all', 'other': 3}, None])
def test_bad_settings_rejected(adapter, settings):
    with pytest.raises((ValueError, TypeError)):
        adapter.generate(0, settings, 3, 4)


@pytest.mark.parametrize('seed,demos,queries', [(True, 3, 4), (-1, 3, 4), (2**63, 3, 4), (0, 2, 4), (0, 7, 4), (0, 3, 0), (0, 3, 5), (0, 3.0, 4), (0, 3, True)])
def test_bad_counts_rejected(adapter, seed, demos, queries):
    with pytest.raises((ValueError, TypeError)):
        adapter.generate(seed, {'survivor_filter': 'all'}, demos, queries)


def test_returned_values_not_cached_or_aliased(adapter):
    settings = {'survivor_filter': 'modal_color'}
    first = adapter.generate(17, settings, 3, 4)
    saved = json.loads(json.dumps(first))
    first['train'][0]['input'][0][0] = 99
    first['test'][0]['output'][0][0] = 99
    assert adapter.generate(17, settings, 3, 4) == saved
    assert settings == {'survivor_filter': 'modal_color'}


def test_promotion_is_native_and_bounded(adapter):
    contract = json.loads((HERE / 'promotion.json').read_text())
    assert contract['parameters'] == {'survivor_filter': ['all', 'modal_color']}
    assert contract['limits'] == {'demos': [3, 6], 'queries': [1, 4]}
    assert contract['qualification_demos'] == 3
    assert contract['default'] == {'survivor_filter': 'all'}
