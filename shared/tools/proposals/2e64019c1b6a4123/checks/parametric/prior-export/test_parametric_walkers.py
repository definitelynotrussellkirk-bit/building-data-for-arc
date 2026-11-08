"""Prototype-only tests: direction semantics, authority, identifiability and export."""
import importlib.util
import json
from pathlib import Path

import pytest

TASK = Path(__file__).resolve().parents[1]


def prototype():
    path = TASK / 'workspace/parametric/prototype.py'
    assert path.is_file(), 'Requested direction prototype is not implemented'
    spec = importlib.util.spec_from_file_location('walkers_prototype', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_program_is_exact_canonical_authority():
    p = prototype()
    assert p.materialize_rule() == p.canonical_rule()
    assert p.parameters_for_seed(0) == {'turn_direction': 'right'}
    assert p.parameters_for_seed(1) == {'turn_direction': 'left'}
    with pytest.raises(ValueError):
        p.materialize_rule('down')


def test_direction_changes_turn_without_losing_up_priority_or_stopping():
    p = prototype()
    # Gray above forces a turn; the open upward move then takes priority.
    grid = [[0]*5, [0,0,5,0,0], [0,0,0,0,0], [0,0,2,0,0]]
    right = [[0,0,0,2,0], [0,0,5,2,0], [0,0,2,2,0], [0,0,2,0,0]]
    left = [row[::-1] for row in right]
    with p.RacketBridge(startup_timeout=120.0) as bridge:
        assert p.evaluate(bridge, p.materialize_rule('right'), grid) == right
        assert p.evaluate(bridge, p.materialize_rule('left'), grid) == left
        boxed = [[0,5,0], [5,2,5]]
        for direction in p.DIRECTIONS:
            assert p.evaluate(bridge, p.materialize_rule(direction), boxed) == boxed
        top = [[0,2,0]]
        assert p.evaluate(bridge, p.materialize_rule('left'), top) == top
        edge = [[5,0], [2,0]]
        assert p.evaluate(bridge, p.materialize_rule('left'), edge) == edge


def test_default_executes_every_labeled_canonical_pair():
    p = prototype()
    pairs = p.canonical_examples()
    assert pairs
    with p.RacketBridge(startup_timeout=120.0) as bridge:
        for pair in pairs:
            assert p.evaluate(bridge, p.materialize_rule(), pair['input']) == pair['output']


def test_both_episode_directions_are_identified_by_visible_demonstrations():
    p = prototype()
    with p.RacketBridge(startup_timeout=120.0) as bridge:
        for seed in (0, 1):
            episode = p.make_episode(seed, bridge=bridge)
            direction = p.parameters_for_seed(seed)['turn_direction']
            assert episode['parameters'] == {'turn_direction': direction}
            assert episode['identifiable']
            assert episode['consistent_directions'] == [direction]
            assert len(episode['train']) == 3 and len(episode['test']) == 2
            for pair in episode['train'] + episode['test']:
                assert p.evaluate(bridge, episode['program'], pair['input']) == pair['output']
            public = p.public_challenge(episode)
            assert set(public) == {'train', 'test'}
            assert all(set(x) == {'input', 'output'} for x in public['train'])
            assert all(set(x) == {'input'} for x in public['test'])
            assert p.make_episode(seed, bridge=bridge) == episode


@pytest.mark.parametrize('layout', ['canonical', 'procedural'])
def test_scene_profiles_and_layouts_survive_direction_reflection(layout):
    p = prototype()
    generator = p.selected_generator()
    for profile in p.PUBLISHED_PROFILES:
        for direction in p.DIRECTIONS:
            grid = p.sample_input(42, 0, direction, scene_profile=profile, route_layout=layout)
            base = grid if direction == 'right' else p.reflect(grid)
            assert generator.self_check(base) == []
            observed = generator.observe_overrides(base)
            assert observed['scene_profile'] == profile
            assert observed['route_layout'] == layout
