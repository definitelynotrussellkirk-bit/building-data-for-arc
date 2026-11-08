"""Prototype-only tests: direction semantics, authority, identifiability and export."""
import importlib.util
import hashlib
import subprocess
import sys
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


def test_cli_public_filenames_depend_only_on_canonical_public_bytes(tmp_path):
    p = prototype()
    completed = subprocess.run(
        [sys.executable, str(Path(p.__file__)), '--output', str(tmp_path)],
        capture_output=True, text=True, timeout=180,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    exported = sorted(tmp_path.glob('challenge-*.json'))
    assert len(exported) == 2
    receipt = json.loads((tmp_path / 'receipt.json').read_text())
    for path in exported:
        public = json.loads(path.read_text())
        canonical_bytes = (json.dumps(public, sort_keys=True, separators=(',', ':')) + '\n').encode()
        expected_name = 'challenge-' + hashlib.sha256(canonical_bytes).hexdigest() + '.json'
        # A seed, direction, private program, or noncanonical formatting must not
        # influence the exported public identifier. This catches the original
        # challenge-0.json / challenge-1.json parity disclosure through real CLI output.
        assert path.name == expected_name
        assert path.read_bytes() == canonical_bytes
        assert set(public) == {'train', 'test'}
        assert all(set(pair) == {'input', 'output'} for pair in public['train'])
        assert all(set(pair) == {'input'} for pair in public['test'])
    assert not (tmp_path / 'challenge-0.json').exists()
    assert not (tmp_path / 'challenge-1.json').exists()
    assert {item['public_challenge'] for item in receipt['episodes']} == {path.name for path in exported}


def test_cli_rejects_legacy_seed_named_public_file_without_mutating_evidence(tmp_path):
    p = prototype()
    stale = tmp_path / 'challenge-0.json'
    original = b'{"train": [], "test": []}\n'
    stale.write_bytes(original)
    completed = subprocess.run(
        [sys.executable, str(Path(p.__file__)), '--output', str(tmp_path)],
        capture_output=True, text=True, timeout=180,
    )
    assert completed.returncode != 0, 'CLI accepted a public filename that discloses seed parity'
    assert 'non-opaque public challenge filename' in completed.stderr
    assert stale.read_bytes() == original
    assert sorted(path.name for path in tmp_path.iterdir()) == ['challenge-0.json']
