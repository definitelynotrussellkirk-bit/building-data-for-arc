"""Prototype-only tests; canonical generator approval remains separate.

These tests detect changing axis/copy semantics, per-pair hidden rules,
answer leakage, missing variable-bbox teaching, or losing canonical parity.
"""
from pathlib import Path
import sys
import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / 'workspace' / 'parametric'))


def prototype():
    path = HOME / 'workspace' / 'parametric' / 'prototype.py'
    assert path.is_file(), 'episode-level parametric prototype has not been implemented'
    import prototype as module
    return module


def test_exact_witness_distinguishes_all_four_executed_programs():
    p = prototype()
    grid = [[0] * 8 for _ in range(8)]
    grid[3][3] = grid[4][4] = 4
    expected = {
        ('horizontal', 2): [[4, 0, 4, 0], [0, 4, 0, 4]],
        ('horizontal', 3): [[4, 0, 4, 0, 4, 0], [0, 4, 0, 4, 0, 4]],
        ('vertical', 2): [[4, 0], [0, 4], [4, 0], [0, 4]],
        ('vertical', 3): [[4, 0], [0, 4], [4, 0], [0, 4], [4, 0], [0, 4]],
    }
    for setting, output in expected.items():
        assert p.racket_outputs(p.program(*setting), [grid]) == [output]


def test_default_program_preserves_all_labeled_canonical_pairs():
    p = prototype()
    from reviewer_support import canonical_pairs
    pairs = canonical_pairs(p.TASK_ID, root=p.ROOT, labeled_only=True)
    assert p.program('horizontal', 2) == p.canonical_program()
    assert p.racket_outputs(p.program(), [pair['input'] for pair in pairs]) == [pair['output'] for pair in pairs]


def test_seed_selection_is_once_per_episode_and_covers_bounded_domain():
    p = prototype()
    assert {p.choose_setting(seed) for seed in range(64)} == set(p.SETTINGS)
    assert [p.choose_setting(seed) for seed in range(10)] == [p.choose_setting(seed) for seed in range(10)]
    for axis, copies in [('diagonal', 2), ('horizontal', True), ('vertical', 4)]:
        with pytest.raises(ValueError):
            p.program(axis, copies)


@pytest.mark.parametrize('axis,copies', [('horizontal', 2), ('horizontal', 3), ('vertical', 2), ('vertical', 3)])
def test_complete_episode_is_deterministic_private_bounded_and_rotation_identifiable(axis, copies):
    p = prototype()
    episode = p.make_episode(17, setting=(axis, copies))
    assert episode == p.make_episode(17, setting=(axis, copies))
    assert episode['parameters'] == {'axis': axis, 'copies': copies}
    pairs = episode['pairs']
    assert len(pairs) == 4
    assert len({p.grid_hash(pair['input']) for pair in pairs}) == 4
    assert sum(p.bbox_shape(pair['input']) != (3, 3) for pair in pairs) >= 2
    for pair in pairs:
        assert 1 <= len(pair['input']) <= 30 and 1 <= len(pair['input'][0]) <= 30
        assert 1 <= len(pair['output']) <= 30 and 1 <= len(pair['output'][0]) <= 30
    assert p.racket_outputs(episode['program'], [pair['input'] for pair in pairs]) == [pair['output'] for pair in pairs]
    public = p.public_challenge(episode)
    assert set(public) == {'train', 'test'}
    assert all(set(pair) == {'input', 'output'} for pair in public['train'])
    assert all(set(pair) == {'input'} for pair in public['test'])
    rotations = p.score_rotations(episode)
    assert len(rotations) == 4
    for rotation in rotations:
        assert rotation['identifiable']
        assert all(row['status'] == 'refuted' for row in rotation['rivals'] if row['name'] != f'{axis}_{copies}')
        assert next(row for row in rotation['rivals'] if row['name'] == f'{axis}_{copies}')['status'] == 'survived_all'
