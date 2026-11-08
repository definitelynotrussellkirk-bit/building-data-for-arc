"""Prototype scope only: canonical authority/production API are unchanged.

Mutation target: swapping inverse back to forward must fail the rotation and
leave-one-pair-out assertions; emitting Python labels must lose Racket counts.
"""
import importlib.util
import hashlib
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

ROOT = find_root(__file__)
PROTOTYPE = ROOT / 'generators/c5f62271ea44/workspace/parametric/direction.py'


@pytest.fixture(scope='module')
def module():
    assert PROTOTYPE.is_file(), 'task-local mapping_direction prototype is not implemented'
    spec = importlib.util.spec_from_file_location('direction_prototype_test', PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def executor(module):
    with module.RuleExecutor(ROOT) as executor:
        yield executor


def test_default_rule_is_exact_canonical_and_uses_real_racket(module, executor):
    assert module.rule_source(ROOT, 'forward') == module.canonical_source(ROOT)
    assert module.rule_source(ROOT, 'forward') != module.rule_source(ROOT, 'inverse')
    before = executor.calls
    for pair in canonical_pairs(module.TASK_ID, root=ROOT):
        assert executor.apply(pair['input'], 'forward') == pair['output']
    assert executor.calls - before == 8


def test_inverse_changes_only_quarter_turn_execution(module, executor):
    gen, _, _ = load_selected_generator(module.TASK_ID, root=ROOT)
    before = executor.calls
    for index, name in enumerate(module.TRANSFORMS):
        grid = gen.generate(510 + index, index, symmetry=name, profile_kind='canonical_1')
        original = [row[:] for row in grid]
        forward = executor.apply(grid, 'forward')
        inverse = executor.apply(grid, 'inverse')
        assert forward == module.mirror(grid, 'forward')
        assert inverse == module.mirror(grid, 'inverse')
        assert (forward != inverse) == (name in ('rot_cw', 'rot_ccw'))
        assert grid == original
    assert executor.calls - before == 16


def test_episode_direction_is_fixed_and_all_query_rotations_discriminate(module, executor):
    for direction in module.DIRECTIONS:
        before = executor.calls
        episode = module.generate_episode(71, direction, root=ROOT, executor=executor)
        assert executor.calls - before == 10  # five pairs, both executed rivals
        assert len(episode['public']['train']) == 4
        assert list(episode['public']) == ['train', 'test']
        assert list(episode['public']['test'][0]) == ['input']
        assert all(set(pair) == {'input', 'output'} for pair in episode['public']['train'])
        private = episode['private']
        assert private['parameters'] == {'mapping_direction': direction}
        assert private['seed'] == 71
        assert private['racket_source'] == module.rule_source(ROOT, direction)
        assert private['racket_source_sha256'] == module.sha256_text(private['racket_source'])
        assert len(private['query_rotations']) == 5
        for rotation in private['query_rotations']:
            assert rotation['surviving_directions'] == [direction]
            assert rotation['unresolved_query_rivals'] == []


def test_deterministic_seed_choice_and_no_implicit_rule_resampling(module, executor):
    seen = set()
    for seed in range(8):
        seen.add(module.choose_direction(seed))
    assert seen == set(module.DIRECTIONS)
    first = module.generate_episode(19, None, root=ROOT, executor=executor)
    second = module.generate_episode(19, None, root=ROOT, executor=executor)
    assert first == second
    default = module.generate_episode(19, root=ROOT, executor=executor)
    assert default['private']['parameters']['mapping_direction'] == 'forward'
    with pytest.raises(ValueError, match='mapping_direction'):
        module.generate_episode(1, 'sideways', root=ROOT, executor=executor)
    with pytest.raises(ValueError, match='seed'):
        module.generate_episode(True, root=ROOT, executor=executor)


def test_complete_cli_suite_retains_rule_provenance_and_witness(module, tmp_path):
    report = module.write_suite(tmp_path / 'suite', seeds=[0], root=ROOT)
    assert report['status'] == 'passed'
    assert report['episodes'] == 2
    assert report['query_rotations_checked'] == 10
    assert report['canonical_parity_pairs'] == 8
    assert report['intervention_witness']['outputs_differ'] is True
    assert report['racket_calls'] == 30  # 8 canonical + 2*5*2 rivals + 2 witness
    for direction in module.DIRECTIONS:
        assert (tmp_path / 'suite' / f'{direction}-seed0' / 'challenge.json').is_file()
        assert (tmp_path / 'suite' / f'{direction}-seed0' / 'private.json').is_file()
        assert (tmp_path / 'suite' / f'{direction}.rkt').read_text() == module.rule_source(ROOT, direction)
    # Reported file hashes must bind emitted bytes, including JSON formatting.
    for row in report['episode_files']:
        folder = tmp_path / 'suite' / row['path']
        assert row['challenge_sha256'] == hashlib.sha256((folder / 'challenge.json').read_bytes()).hexdigest()
        assert row['private_sha256'] == hashlib.sha256((folder / 'private.json').read_bytes()).hexdigest()
