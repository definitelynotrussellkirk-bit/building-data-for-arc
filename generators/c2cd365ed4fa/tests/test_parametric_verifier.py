"""Real-runtime negative cases for the task-local focused verifier and writer."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest
from reviewer_support import find_root

ROOT = find_root(__file__)
HOME = ROOT / 'generators/c2cd365ed4fa/workspace/parametric'


def load_verifier():
    path = HOME / 'verify.py'
    assert path.is_file(), 'The focused verifier has not been implemented'
    spec = importlib.util.spec_from_file_location('_test_c2cd_verifier', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def ambiguous_episode(program):
    def scene(fives, two):
        grid = [[7] * 10 for _ in range(10)]
        for r, c in fives:
            grid[r][c] = 5
        grid[two[0]][two[1]] = 2
        return grid
    tall = [[5, 7, 7, 7, 7], [5, 2, 7, 7, 7]]
    return {
        'program_solution': program,
        'train': [
            {'input': scene([(1, 1), (1, 4)], (5, 5)), 'output': deepcopy(tall)},
            {'input': scene([(2, 1), (2, 4)], (6, 5)), 'output': deepcopy(tall)},
        ],
        'test': [{'input': scene([(1, 1), (2, 2)], (5, 5)),
                  'output': [[5, 2, 7, 7, 7]]}],
    }


def test_real_racket_audit_detects_a_query_changing_demo_survivor():
    verifier = load_verifier()
    adapter = verifier.load_adapter()
    program = adapter.program({'column_order': 'fixed'})
    episode = ambiguous_episode(program)
    with verifier.ProtectedExecutor(ROOT) as execute:
        verifier.check_labels(episode, execute)
        result = verifier.audit_rivals(
            episode, {'four_connected': program.replace('objects-8', 'objects')}, execute)
    assert result['passed'] is False
    assert result['demo_survivors'] == ['four_connected']
    assert result['query_changing_survivors'] == ['four_connected']
    assert result['rivals']['four_connected']['demo_mismatches'] == []
    assert result['rivals']['four_connected']['query_mismatches'] == [0]


def test_real_label_checker_rejects_a_corrupted_query_answer():
    verifier = load_verifier()
    program = verifier.load_adapter().program({'column_order': 'fixed'})
    episode = ambiguous_episode(program)
    episode['test'][0]['output'][0][0] = 9
    with verifier.ProtectedExecutor(ROOT) as execute:
        with pytest.raises(ValueError, match='test/0.*label'):
            verifier.check_labels(episode, execute)


@pytest.mark.parametrize('claim', [[[True]], [[1.0]], [[1], [1, 1]]])
def test_exact_label_comparison_rejects_untyped_or_ragged_claims(claim):
    verifier = load_verifier()
    with pytest.raises(ValueError):
        verifier.require_exact_label(claim, [[1]], 'negative')


def test_real_writer_metadata_invariance_and_corrupt_answer_rejection(tmp_path):
    verifier = load_verifier()
    prototype = verifier.load_adapter().prototype
    original = prototype.generate(0, {'column_order': 'fixed'}, 2, 1)
    changed = deepcopy(original)
    changed['seed'] = 999
    changed['sampling'] = {'private_note': 'Private metadata must not rename the public file.'}
    manifests = [prototype.write_examples(tmp_path / name, [episode])
                 for name, episode in [('original', original), ('changed', changed)]]
    first = tmp_path / 'original' / 'public'
    second = tmp_path / 'changed' / 'public'
    assert {p.name: p.read_bytes() for p in first.iterdir()} == {
        p.name: p.read_bytes() for p in second.iterdir()}
    assert all(m['racket']['backend'] == 'racket' and m['racket']['protected'] is True
               for m in manifests)
    corrupt = deepcopy(original)
    corrupt['test'][0]['output'][0][0] = (corrupt['test'][0]['output'][0][0] + 1) % 10
    with pytest.raises(ValueError, match='claimed label'):
        prototype.write_examples(tmp_path / 'rejected', [corrupt])
    assert not (tmp_path / 'rejected').exists()
