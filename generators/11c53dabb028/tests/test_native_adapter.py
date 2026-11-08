"""Native eight-setting adapter and source-preserving promotion contract."""
import importlib.util
import itertools
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1] / 'workspace' / 'parametric'
SETTINGS = [{'input_frame': frame, 'vertical_repeats': v, 'horizontal_repeats': h}
            for frame, v, h in itertools.product(('input', 'largest_component'), (1, 2), (1, 2))]


@pytest.fixture(scope='module')
def adapter():
    path = HERE / 'adapter.py'
    assert path.is_file(), 'native adapter has not been implemented'
    spec = importlib.util.spec_from_file_location('component_tile_adapter_tests', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('seed', [0, 17, 2**63 - 1])
def test_all_settings_share_inputs_and_demos_identify_each(adapter, seed):
    episodes = [adapter.generate(seed, setting, 3, 4) for setting in SETTINGS]
    inputs = {split: [p['input'] for p in episodes[0][split]] for split in ('train', 'test')}
    for episode, setting in zip(episodes, SETTINGS):
        assert set(episode) == {'train', 'test', 'program_solution'}
        assert episode['program_solution'] == adapter.program(setting)
        for split in ('train', 'test'):
            assert [p['input'] for p in episode[split]] == inputs[split]
        for other in episodes:
            if other is not episode:
                assert any(a['output'] != b['output'] for a, b in zip(episode['train'], other['train']))


@pytest.mark.parametrize('setting', SETTINGS)
def test_independent_prefixes_and_no_aliases(adapter, setting):
    short = adapter.generate(17, setting, 3, 1)
    full = adapter.generate(17, setting, 6, 4)
    assert short['train'] == full['train'][:3] and short['test'] == full['test'][:1]
    saved = json.loads(json.dumps(short))
    short['train'][0]['input'][0][0] = 99
    short['test'][0]['output'][0][0] = 99
    assert adapter.generate(17, setting, 3, 1) == saved


@pytest.mark.parametrize('setting', [None, {}, {'input_frame': 'input'}, {**SETTINGS[0], 'vertical_repeats': True}, {**SETTINGS[0], 'other': 1}])
def test_bad_settings_rejected(adapter, setting):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, setting, 3, 4)


@pytest.mark.parametrize('seed,demos,queries', [(True, 3, 4), (-1, 3, 4), (2**63, 3, 4), (0, 2, 4), (0, 7, 4), (0, 3, 0), (0, 3, 5), (0, 3.0, 4), (0, 3, True)])
def test_bad_counts_rejected(adapter, seed, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(seed, SETTINGS[0], demos, queries)


def test_native_promotion_preserves_repeat_choices(adapter):
    contract = json.loads((HERE / 'promotion.json').read_text())
    assert contract['parameters'] == {'input_frame': ['input', 'largest_component'], 'vertical_repeats': [1, 2], 'horizontal_repeats': [1, 2]}
    assert contract['default'] == {'input_frame': 'input', 'vertical_repeats': 2, 'horizontal_repeats': 2}
    assert contract['qualification_demos'] == 3
    assert contract['limits'] == {'demos': [3, 6], 'queries': [1, 4]}
