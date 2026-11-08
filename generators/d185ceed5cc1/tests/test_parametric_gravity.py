"""Focused owner tests for the isolated gravity prototype."""
import importlib.util
from pathlib import Path
import pytest
from reviewer_support import find_root


def prototype():
    p = find_root(__file__) / 'generators/d185ceed5cc1/workspace/parametric/gravity.py'
    assert p.is_file(), 'episode-level gravity prototype is missing'
    spec = importlib.util.spec_from_file_location('gravity_prototype', p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_segments_preserve_walls_and_pebble_order():
    mod = prototype()
    grid = [[2, 0, 1, 8, 0, 3]]
    assert mod.python_pack(grid, 'right') == [[0, 2, 1, 8, 0, 3]]
    assert mod.python_pack(grid, 'left') == [[2, 1, 0, 8, 3, 0]]
    assert grid == [[2, 0, 1, 8, 0, 3]]


def test_public_challenge_removes_private_fields_and_query_answers():
    mod = prototype()
    private = {'seed': 9, 'parameter': {'gravity': 'left'}, 'program': 'secret',
               'train': [{'input': [[0, 2]], 'output': [[2, 0]]}],
               'test': [{'input': [[0, 3]], 'output': [[3, 0]]}]}
    public = mod.public_challenge(private)
    assert set(public) == {'train', 'test'}
    assert public['test'] == [{'input': [[0, 3]]}]
    public['train'][0]['input'][0][0] = 9
    assert private['train'][0]['input'] == [[0, 2]]


def test_invalid_episode_settings_fail_before_sampling():
    mod = prototype()
    for seed in (True, -1, 1.5, '1'):
        with pytest.raises(ValueError):
            mod.choose_direction(seed)
    for setting in (True, 'up', 1, ''):
        with pytest.raises(ValueError):
            mod.choose_direction(1, setting)


def test_default_setting_is_deterministic_and_explicit_settings_override_it():
    mod = prototype()
    assert mod.choose_direction(17) == mod.choose_direction(17)
    assert {mod.choose_direction(s) for s in range(16)} == {'left', 'right'}
    assert mod.choose_direction(17, 'right') == 'right'
    assert mod.choose_direction(17, 'left') == 'left'
