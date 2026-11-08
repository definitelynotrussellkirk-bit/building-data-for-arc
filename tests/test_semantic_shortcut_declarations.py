"""A declared canonical-fitting rule must actually fit the labeled population."""
import json
from types import SimpleNamespace
import sys

import pytest
from test_semantic_witness_records import gate


def canonical(gate, monkeypatch, tmp_path):
    reader = sys.modules['scripts.canonical_profile_gate']
    path = tmp_path / 'canonical.jsonl'
    rows = [
        {'task_id': 'x', 'train': [{'input': ['1'], 'output': ['1']}],
         'test': [{'input': ['2']}]},
        {'task_id': 'x', 'train': [{'input': ['3'], 'output': ['3']}],
         'test': [{'input': ['4'], 'output': ['4']}]},
    ]
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    monkeypatch.setattr(reader, 'CANONICAL', path)
    monkeypatch.setattr(gate, 'authoritative_simple_shortcut', lambda _: 'identity')
    return reader


def check(gate, shortcuts, **kwargs):
    return gate.check_canonical_ambiguity('x', declared_shortcuts=shortcuts,
        rival_claims=kwargs.get('claims', {}), witness_rivals=kwargs.get('witnesses', {}))


def test_declared_failure_checks_every_labeled_pair_and_retains_identity(gate, monkeypatch, tmp_path):
    canonical(gate, monkeypatch, tmp_path)
    seen = []
    def wrong(grid):
        seen.append(grid[0][0])
        return [[0]]
    report = check(gate, {'wrong': wrong})
    assert seen == [1, 3, 4]  # unlabeled test input is not an answer
    assert report['declared_validation']['wrong']['checked'] == 3
    assert report['declared_validation']['wrong']['mismatches'] == 3
    failures = report['declared_validation']['wrong']['examples']
    assert failures[-1]['pair_identity'] == {
        'canonical_row': 1, 'variant': 1, 'split': 'test', 'pair_index': 0}
    assert failures[-1]['expected_output'] == [[4]]
    assert failures[-1]['predicted_output'] == [[0]]
    assert report['invalid_declared'] == ['wrong']


def test_declared_exceptions_do_not_hide_later_failures(gate, monkeypatch, tmp_path):
    canonical(gate, monkeypatch, tmp_path)
    def broken(grid):
        if grid == [[1]]:
            raise ValueError('fixture error')
        return [[0]]
    report = check(gate, {'broken': broken})
    result = report['declared_validation']['broken']
    assert result['checked'] == 3 and result['errors'] == 1 and result['mismatches'] == 2
    assert result['examples'][0]['error'] == 'ValueError: fixture error'
    assert report['invalid_declared'] == ['broken']


def test_generic_nonmatches_stay_normal_and_matching_declaration_still_needs_witness(gate, monkeypatch, tmp_path):
    canonical(gate, monkeypatch, tmp_path)
    report = check(gate, {'identity_claim': lambda grid: grid})
    assert report['invalid_declared'] == []
    assert report['declared_validation']['identity_claim']['status'] == 'fits_all_labeled_pairs'
    assert report['authority_equal'] == ['identity']
    assert [row for row in report['unsatisfied'] if row['source'] == 'declared'] == [
        {'source': 'declared', 'shortcut': 'identity_claim'}]


@pytest.mark.parametrize('no_labels', [False, True])
def test_invalid_or_unverifiable_declaration_fails_audit_without_strict_flag(gate, monkeypatch, tmp_path, no_labels):
    reader = canonical(gate, monkeypatch, tmp_path)
    if no_labels:
        reader.CANONICAL.write_text(json.dumps({'task_id': 'x', 'train': [{'input': ['1']}]}) + '\n')
    gen = SimpleNamespace(generate=lambda seed, sample_index, **kw: [[1]],
                          CANONICAL_SHORTCUTS={'wrong': lambda grid: [[0]]})
    monkeypatch.setattr(gate.importlib, 'import_module', lambda _: gen)
    report = gate.audit_task('x', per_band=1, lessons=0)
    assert report['status'] == 'FAIL'
    assert any('CANONICAL_SHORTCUTS' in error for error in report['errors'])
    assert report['canonical_ambiguity']['invalid_declared'] == ['wrong']


def test_shortcut_mutation_never_changes_canonical_inputs(gate, monkeypatch, tmp_path):
    reader = canonical(gate, monkeypatch, tmp_path)
    before = reader.canonical_pairs('x')
    def mutate(grid):
        grid[0][0] = 0
        return grid
    report = check(gate, {'mutator': mutate})
    assert report['invalid_declared'] == ['mutator']
    assert reader.canonical_pairs('x') == before


def test_evidence_is_bounded_but_failure_totals_are_complete(gate, monkeypatch):
    pairs = [{'input': [[1]], 'output': [[2]]} for _ in range(gate.MAX_EXAMPLES + 4)]
    monkeypatch.setattr(gate, '_canonical_pairs_cached', lambda _: pairs)
    monkeypatch.setattr(gate, 'authoritative_simple_shortcut', lambda _: None)
    report = check(gate, {'wrong': lambda grid: grid})
    result = report['declared_validation']['wrong']
    assert result['mismatches'] == len(pairs)
    assert len(result['examples']) == gate.MAX_EXAMPLES
    assert result['examples'][0]['pair_identity'] == {'usable_pair_index': 0}


@pytest.mark.parametrize('prediction', [object(), {'not': 'a grid'}, [[11]], [[False]]])
def test_invalid_predictions_are_failures_and_json_safe(gate, monkeypatch, tmp_path, prediction):
    canonical(gate, monkeypatch, tmp_path)
    report = check(gate, {'invalid': lambda grid: prediction})
    assert report['invalid_declared'] == ['invalid']
    assert report['declared_validation']['invalid']['mismatches'] == 3
    assert report['declared_validation']['invalid']['examples'][0]['predicted_output'] is None
    json.dumps(report)


def test_read_error_marks_declared_rules_unverified(gate, monkeypatch, tmp_path):
    reader = canonical(gate, monkeypatch, tmp_path)
    reader.CANONICAL.unlink()
    report = check(gate, {'unknown': lambda grid: grid})
    assert report['invalid_declared'] == ['unknown']
    assert report['declared_validation']['unknown']['status'] == 'read_error'
    assert report['read_error']
