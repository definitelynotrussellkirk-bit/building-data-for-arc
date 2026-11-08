"""Prototype scope only: this does not certify canonical generator approval."""
import importlib.util
from pathlib import Path
import pytest
from reviewer_support import find_root, canonical_pairs

ROOT = find_root(__file__)
SOURCE = Path(__file__).resolve().parent.parent / 'workspace/parametric/prototype.py'
spec = importlib.util.spec_from_file_location('border_color_prototype', SOURCE)
prototype = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prototype)


def test_parameter_contract_and_determinism():
    for invalid in (0, 10, True, 3.5, '8'):
        with pytest.raises(ValueError):
            prototype.inputs_for_episode(7, invalid)
    assert prototype.inputs_for_episode(19, 8) == prototype.inputs_for_episode(19, 8)
    assert prototype.inputs_for_episode(19, 8) == prototype.inputs_for_episode(19, 3)
    assert prototype.inputs_for_episode(19, 8) != prototype.inputs_for_episode(20, 8)


def test_public_projection_removes_private_data():
    private = {'border_color': 8, 'seed': 7, 'racket': 'secret',
               'pairs': [{'input': [[1]], 'output': [[1]]} for _ in range(4)]}
    public = prototype.public_challenge(private)
    assert set(public) == {'train', 'test'}
    assert len(public['train']) == 3
    assert public['test'] == [{'input': [[1]]}]


def test_actual_racket_canonical_equivalence_and_edge_cases():
    with prototype.RacketBridge(startup_timeout=120) as bridge:
        src = prototype.materialize(8, root=ROOT)
        for pair in canonical_pairs(prototype.TASK_ID, root=ROOT, labeled_only=True):
            assert prototype.execute(bridge, src, pair['input']) == pair['output']
        for color in range(1, 10):
            src = prototype.materialize(color, root=ROOT)
            # Preserve nonzero perimeter and interior source colors; fill zeros only.
            grid = [[2, 0, 4], [0, 7, 0], [5, 0, 9]]
            expected = [[2, color, 4], [color, 7, color], [5, color, 9]]
            assert prototype.execute(bridge, src, grid) == expected
            assert prototype.execute(bridge, src, [[0, 0]]) == [[0, 0]]
            assert prototype.execute(bridge, src, [[0, 2, 0, 4, 0]]) == [[0, 2, color, 4, 0]]
            assert prototype.execute(bridge, src, [[0], [2], [0], [4], [0]]) == [[0], [2], [color], [4], [0]]


def test_demonstrations_distinguish_all_parameter_rivals():
    with prototype.RacketBridge(startup_timeout=120) as bridge:
        for chosen in (8, 3, 6):
            episode = prototype.make_episode(bridge, seed=104729, border_color=chosen, root=ROOT)
            assert len(episode['pairs']) == 4
            assert all(episode['rival_refuting_demo_indices'][str(r)] for r in range(1, 10) if r != chosen)
            for pair in episode['pairs']:
                source_colors = {v for row in pair['input'] for v in row if v}
                assert not source_colors.intersection((8, 3, 6))
                assert chosen not in source_colors
                assert any(a == 0 and b == chosen for ra, rb in zip(pair['input'], pair['output']) for a, b in zip(ra, rb))
