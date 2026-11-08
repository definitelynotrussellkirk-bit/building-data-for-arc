"""Native request and public-view behavior, independent of Racket qualification."""
import copy
import importlib.util
from pathlib import Path

import pytest
from reviewer_support import public_challenge_bytes

HOME = Path(__file__).resolve().parents[1]


def adapter():
    path = HOME / 'workspace/parametric/adapter.py'
    spec = importlib.util.spec_from_file_location('orbit_adapter_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('seed', [0, 17, 2**63 - 1])
def test_counts_settings_and_public_first_turn_are_independent(seed):
    a = adapter()
    episodes = [a.generate(seed, {'links': v}, 3, 4) for v in ('none', 'first_hit')]
    for split in ('train', 'test'):
        assert [p['input'] for p in episodes[0][split]] == [p['input'] for p in episodes[1][split]]
    assert episodes[0]['train'][0]['output'] != episodes[1]['train'][0]['output']
    for setting, episode in zip(('none', 'first_hit'), episodes):
        single = a.generate(seed, {'links': setting}, 3, 1)
        public = {'train': episode['train'], 'test': episode['test'][:1]}
        assert public_challenge_bytes(public) == public_challenge_bytes(single)
        changed_private = copy.deepcopy(episode)
        changed_private['seed'] = -1
        changed_private['settings'] = {'links': 'private mutation'}
        changed_private['program_solution'] = 'private mutation'
        changed_private['test'][0]['output'] = [[9]]
        changed_private['test'] = changed_private['test'][:1]
        assert public_challenge_bytes(changed_private) == public_challenge_bytes(public)


@pytest.mark.parametrize('seed', [True, False, -1, 2**63, 1.0, '1', None])
def test_adapter_rejects_invalid_seed_before_sampling(seed):
    with pytest.raises(ValueError):
        adapter().generate(seed)


@pytest.mark.parametrize('settings', [{}, [], {'links': 1}, {'links': False},
    {'links': 'NONE'}, {'links': 'none', 'extra': 0}])
def test_adapter_rejects_unknown_settings(settings):
    with pytest.raises(ValueError):
        adapter().generate(0, settings)


def test_default_choice_is_deterministic_and_separate_from_inputs():
    a = adapter()
    for seed, chosen in [(0, 'none'), (1, 'first_hit')]:
        assert a.generate(seed) == a.generate(seed, {'links': chosen})
