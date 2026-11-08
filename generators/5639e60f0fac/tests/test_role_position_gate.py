"""Opt-in counterfactual tool regression tests; synthetic records are not Racket evidence."""
import copy
import importlib.util
import json
from pathlib import Path
import types

import pytest

TOOL = Path(__file__).resolve().parents[1] / 'workspace/probe_role_positions.py'


def tool():
    assert TOOL.is_file(), 'role-position gate has not been implemented'
    spec = importlib.util.spec_from_file_location('role_position_gate', TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepared():
    gate = tool()
    generator, source = gate.load_generator()
    packet = gate.prepare(generator, source)
    return gate, generator, source, packet


def synthetic_record(packet):
    # Deliberately synthetic test data: exercises parsing and integrity checks only.
    gate = tool()
    return {'schema': 'arcpuzzles-apply-v1', 'task_id': packet['task_id'],
            'rule_task_id': packet['task_id'],
            'reference': 'canonical', 'generator_sha256': packet['generator_sha256'],
            'executed_rule_hash': packet['rule_hash'], 'catalog_rule_hash': packet['rule_hash'],
            'rule_text_sha256': packet['rule_text_sha256'], 'rule_hash_matches_catalog': True,
            'results': [{'index': i, 'valid_output': True, 'error': None,
                         'input': packet['inputs'][i],
                         'input_sha256': gate.digest(packet['inputs'][i]),
                         'output': c['python_expected'],
                         'output_sha256': gate.digest(c['python_expected'])}
                        for i, c in enumerate(packet['cases'])]}


def test_prepares_all_canonical_labels_and_four_role_quadrants():
    gate, generator, source, packet = prepared()
    assert packet['canonical_labeled_pairs'] == 3
    assert packet['canonical_split_counts'] == {'train': 2, 'test': 1}
    assert all(v['canonical_matches'] == 3 for v in packet['canonical_shortcuts'].values())
    assert {c['position_bias'] for c in packet['cases'] if c['kind'] == 'counterfactual'} == {
        'upper_left', 'upper_right', 'lower_left', 'lower_right'}
    assert all(not generator.self_check(g) for g in packet['inputs'])


def test_rejects_collision_and_out_of_bounds_movement():
    gate, generator, source, packet = prepared()
    grid = packet['inputs'][0]
    for target, canvas in [((1, 1), (1, 1)), ((-1, 1), (6, 8)), ((9, 12), (1, 1))]:
        with pytest.raises(ValueError, match='overlap|bounds|buffer'):
            gate.move_roles(grid, target, canvas)


def test_rejects_unsupported_domain_before_moving():
    gate, generator, source, packet = prepared()
    bad = copy.deepcopy(packet['inputs'][0]); bad[0][0] = 9
    with pytest.raises(ValueError, match='domain|color'):
        gate.move_roles(bad, (1, 1), (6, 8))
    with pytest.raises(ValueError, match='integer|grid'):
        gate.move_roles([[False]], (0, 0), (0, 0))


def test_position_semantic_mirror_cannot_be_certified_by_role_translation():
    gate, generator, source, packet = prepared()
    fake = types.SimpleNamespace(**{name: getattr(generator, name) for name in (
        'TASK_ID', 'self_check', 'CANONICAL_SHORTCUTS', 'LESSON_COMPETITORS')})
    def positional_rule(grid):
        # Same rule on canonical placements, identity when green is on the right.
        return generator.rule_mirror(grid) if gate.role_data(grid)['template']['bbox'][1] < gate.role_data(grid)['canvas']['bbox'][1] else grid
    fake.rule_mirror = positional_rule
    with pytest.raises(ValueError, match='position|applicability'):
        gate.prepare(fake, source)


def test_scores_competitors_separately_from_canonical_shortcuts():
    gate, generator, source, packet = prepared()
    report = gate.score(packet, synthetic_record(packet), generator, source)
    assert report['status'] == 'PASS'
    assert report['canonical_labeled_pairs'] == 3
    assert report['authority_label_kind'] == 'stored_public_racket_record'
    for name in ('left_to_right', 'top_to_bottom'):
        assert report['canonical_shortcuts'][name]['counterfactual_disagreements'] > 0
    assert 'identity' in report['lesson_competitors']
    assert report['python_mirror_mismatches'] == []


def test_wrong_stored_output_is_detected_without_claiming_rival_refutation():
    gate, generator, source, packet = prepared()
    record = synthetic_record(packet)
    record['results'][-1]['output'] = [[0] * len(packet['inputs'][-1][0]) for _ in packet['inputs'][-1]]
    record['results'][-1]['output_sha256'] = gate.digest(record['results'][-1]['output'])
    report = gate.score(packet, record, generator, source)
    assert report['status'] == 'FAIL'
    assert report['python_mirror_mismatches']
    assert report['position_invariance_supported'] is False


def test_rejects_source_identity_mismatch():
    gate, generator, source, packet = prepared()
    record = synthetic_record(packet); record['generator_sha256'] = '0' * 64
    with pytest.raises(ValueError, match='source identity'):
        gate.score(packet, record, generator, source)


def test_optional_ordinary_coverage_counts_each_band_and_emits_refuting_samples():
    import inspect
    gate = tool(); generator, source = gate.load_generator()
    assert 'coverage' in inspect.signature(gate.prepare).parameters, 'ordinary coverage is not implemented'
    packet = gate.prepare(generator, source, coverage=True)
    census = packet['ordinary_coverage']
    assert census['samples'] == 288
    assert census['prediction_kind'] == 'Python rule_mirror proxy; not Racket authority'
    assert all(band['samples'] == 96 for band in census['per_band'].values())
    assert set(census['quadrants']) == {'upper_left', 'upper_right', 'lower_left', 'lower_right'}
    assert all(count > 0 for count in census['quadrants'].values())
    assert all(rival['disagreements'] > 0 for rival in census['shortcuts'].values())
    assert 1 <= sum(c['kind'] == 'generated_witness' for c in packet['cases']) <= 2


def test_rejects_false_canonical_shortcut_claim_and_conflicting_declarations():
    gate, generator, source, packet = prepared()
    wrong = lambda grid: grid
    fake = types.SimpleNamespace(**{name: getattr(generator, name) for name in (
        'TASK_ID', 'self_check', 'rule_mirror', 'CANONICAL_SHORTCUTS', 'LESSON_COMPETITORS')})
    fake.CANONICAL_SHORTCUTS = {'identity_claim': wrong}
    with pytest.raises(ValueError, match='canonical shortcut.*fits only'):
        gate.prepare(fake, source)
    fake.CANONICAL_SHORTCUTS = {'left_to_right': wrong}
    with pytest.raises(ValueError, match='conflicting callable'):
        gate.prepare(fake, source)


@pytest.mark.parametrize('mutation', ['missing_input', 'wrong_input', 'missing_digest', 'wrong_digest'])
def test_rejects_mismatched_racket_input_identity(mutation):
    gate, generator, source, packet = prepared()
    record = synthetic_record(packet)
    result = record['results'][0]
    if mutation == 'missing_input':
        del result['input']
    elif mutation == 'wrong_input':
        result['input'] = [[0]]
        result['input_sha256'] = gate.digest(result['input'])
    elif mutation == 'missing_digest':
        del result['input_sha256']
    else:
        result['input_sha256'] = '0' * 64
    with pytest.raises(ValueError, match='input identity'):
        gate.score(packet, record, generator, source)


def test_rejects_wrong_output_digest_and_rule_task_identity():
    gate, generator, source, packet = prepared()
    record = synthetic_record(packet)
    record['results'][0]['output_sha256'] = '0' * 64
    with pytest.raises(ValueError, match='output integrity'):
        gate.score(packet, record, generator, source)
    record = synthetic_record(packet)
    record['rule_task_id'] = 'different-task'
    with pytest.raises(ValueError, match='rule identity'):
        gate.score(packet, record, generator, source)


def test_prepare_cli_emits_public_apply_payload_and_bound_metadata(tmp_path, monkeypatch):
    import sys
    gate = tool()
    target = tmp_path / 'inputs.json'
    monkeypatch.setattr(sys, 'argv', [str(TOOL), 'prepare', '--out', str(target)])
    assert gate.main() == 0
    payload = json.loads(target.read_text())
    assert set(payload) == {'inputs'}, 'public apply requires exactly one top-level key'
    packet = json.loads(target.with_suffix('.meta.json').read_text())
    assert payload['inputs'] == packet['inputs']
    record = tmp_path / 'racket.json'
    record.write_text(json.dumps(synthetic_record(packet)))
    result = tmp_path / 'report.json'
    monkeypatch.setattr(sys, 'argv', [str(TOOL), 'score', '--inputs', str(target),
                                    '--racket', str(record), '--out', str(result)])
    assert gate.main() == 0
    assert json.loads(result.read_text())['status'] == 'PASS'
    payload['inputs'][0] = [[0]]
    target.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match='input payload'):
        gate.main()
