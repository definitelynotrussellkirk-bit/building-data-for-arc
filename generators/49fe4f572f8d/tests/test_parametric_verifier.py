"""Protected-runtime negative cases for the focused verifier and example writer."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest
from reviewer_support import find_root

ROOT = find_root(__file__)
HOME = ROOT / 'generators/49fe4f572f8d/workspace/parametric'


def load_verifier():
    path = HOME / 'verify.py'
    assert path.is_file(), 'The focused verifier has not been implemented'
    spec = importlib.util.spec_from_file_location('_test_49fe_verifier', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def ambiguous_episode(program):
    def grid(cells):
        result = [[0] * 7 for _ in range(6)]
        for row, col, value in cells:
            result[row][col] = value
        return result
    return {
        'program_solution': program,
        'train': [
            {'input': grid([(0, 0, 1), (2, 2, 2)]),
             'output': grid([(5, 0, 1), (5, 2, 2)])},
            {'input': grid([(1, 3, 3), (3, 5, 4)]),
             'output': grid([(5, 3, 3), (5, 5, 4)])},
        ],
        'test': [{'input': grid([(0, 0, 1), (2, 0, 1), (4, 0, 1)]),
                  'output': grid([])}],
    }


def test_real_racket_audit_detects_a_query_changing_demo_survivor():
    verifier = load_verifier()
    adapter = verifier.load_adapter()
    episode = ambiguous_episode(adapter.program({'mode': 'settle_clear_once'}))
    with verifier.ProtectedExecutor(ROOT) as execute:
        verifier.check_labels(episode, execute)
        result = verifier.audit_rivals(
            episode, {'plain_down': adapter.program({'mode': 'down'})}, execute)
    assert result['passed'] is False
    assert result['demo_survivors'] == ['plain_down']
    assert result['query_changing_survivors'] == ['plain_down']
    assert result['rivals']['plain_down']['demo_mismatches'] == []
    assert result['rivals']['plain_down']['query_mismatches'] == [0]


def test_real_label_checker_rejects_a_corrupted_query_answer():
    verifier = load_verifier()
    program = verifier.load_adapter().program({'mode': 'settle_clear_once'})
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


def test_runtime_failure_cannot_be_counted_as_a_refuted_rival():
    verifier = load_verifier()
    program = verifier.load_adapter().program({'mode': 'settle_clear_once'})
    episode = ambiguous_episode(program)
    with verifier.ProtectedExecutor(ROOT) as execute:
        with pytest.raises(Exception):
            verifier.audit_rivals(episode, {'broken': '(rule! (not-a-real-function g))'}, execute)


def test_real_writer_metadata_invariance_and_corrupt_answer_rejection(tmp_path):
    verifier = load_verifier()
    prototype = verifier.load_adapter().prototype
    original = prototype.generate(0, {'mode': 'settle_clear_once'}, 2, 1)
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
