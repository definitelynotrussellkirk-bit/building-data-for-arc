"""Focused serialization/verifier checks; fixture labels are not Racket evidence."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


@pytest.fixture
def tool():
    path = Path(__file__).resolve().parents[1] / 'workspace/authoring_preview.py'
    assert path.is_file(), 'The requested generic authoring projection helper is missing'
    spec = importlib.util.spec_from_file_location('_test_authoring_preview', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def evidence(tmp_path, tool, monkeypatch):
    root = tmp_path / 'repo'
    root.mkdir()
    source = tmp_path / 'checks/preflight'
    source.mkdir(parents=True)
    episode = {
        'seed': 17, 'settings': {'mode': 'a'}, 'program_solution': '(lambda (g) g)',
        'train': [{'input': [[1]], 'output': [[2]]},
                  {'input': [[3]], 'output': [[4]]}],
        'test': [{'input': [[n]], 'output': [[(n + 1) % 10]]} for n in (5, 6, 7, 8)],
    }
    q = {'task_id': 'public_eval_12345678',
         'source_binding': {'task_id': 'public_eval_12345678', 'files': [
             {'path': 'fixture.py', 'sha256': 'a' * 64}]}}
    execution = {'episodes': [episode]}
    originals = {'pairs': [{'input': [[1]], 'output': [[2]]}]}
    values = {'preflight.json': q, 'execution.json': execution,
              'original-pairs.json': originals}
    for name, value in values.items():
        (source / name).write_bytes(tool._raw(value))

    # The protected preflight boundary is intentionally replaced in unit tests;
    # projection, publication, file inventory and mutation checks remain real.
    def fixture_loader(selected_root, path):
        assert Path(selected_root) == root
        source_bytes = {name: (Path(path).parent / name).read_bytes() for name in values}
        return (json.loads(source_bytes['preflight.json']),
                json.loads(source_bytes['execution.json']), source_bytes)
    monkeypatch.setattr(tool, '_load_preflight', fixture_loader)
    return root, source / 'preflight.json', tmp_path / 'bundle'


def test_export_projects_only_one_query_and_pairs_private_order(tool, evidence):
    root, preflight, bundle = evidence
    report = tool.export(root, preflight, bundle, presentation_seed=23)
    assert report['status'] == 'authoring_projection'
    assert report['owner_acceptance'] == 'not_performed'
    assert report['training_admitted'] is False
    manifest = json.loads((bundle / 'private/manifest.json').read_bytes())
    assert manifest['schema'] == tool.SCHEMA
    assert manifest['episodes'][0]['source_indices'] == tool.query_order(4, 17 + 23)
    for position, identifier in enumerate(manifest['episodes'][0]['view_ids']):
        raw = (bundle / 'public' / f'{identifier}.json').read_bytes()
        value = json.loads(raw)
        assert hashlib.sha256(raw).hexdigest() == identifier
        assert set(value) == {'train', 'test'}
        assert len(value['test']) == 1
        assert set(value['test'][0]) == {'input'}
        index = manifest['episodes'][0]['source_indices'][position]
        assert value['test'][0]['input'] == [[(5, 6, 7, 8)[index]]]
    assert tool.verify(root, bundle)['views'] == 4


@pytest.mark.parametrize('mutation', [
    'answer_leakage', 'altered_bytes', 'wrong_filename_hash', 'missing_file',
    'metadata_tamper', 'permutation_tamper', 'extra_member', 'source_receipt_drift',
])
def test_verifier_rejects_saved_mutations(tool, evidence, mutation):
    root, preflight, bundle = evidence
    tool.export(root, preflight, bundle)
    public = next((bundle / 'public').iterdir())
    manifest_path = bundle / 'private/manifest.json'
    if mutation == 'answer_leakage':
        value = json.loads(public.read_bytes())
        value['test'][0]['output'] = [[9]]
        public.write_bytes(tool._raw(value))
    elif mutation == 'altered_bytes':
        public.write_bytes(public.read_bytes() + b' ')
    elif mutation == 'wrong_filename_hash':
        public.rename(public.with_name('0' * 64 + '.json'))
    elif mutation == 'missing_file':
        public.unlink()
    elif mutation in {'metadata_tamper', 'permutation_tamper'}:
        value = json.loads(manifest_path.read_bytes())
        if mutation == 'metadata_tamper':
            value['source_binding']['files'][0]['sha256'] = 'b' * 64
        else:
            value['episodes'][0]['source_indices'].reverse()
        manifest_path.write_bytes(tool._raw(value))
    elif mutation == 'extra_member':
        (bundle / 'public/order.json').write_text('{}')
    else:
        preflight.write_bytes(preflight.read_bytes() + b' ')
    with pytest.raises((ValueError, OSError)):
        tool.verify(root, bundle)


def test_export_refuses_existing_destination_and_duplicate_views(tool, evidence):
    root, preflight, bundle = evidence
    bundle.mkdir()
    with pytest.raises(FileExistsError):
        tool.export(root, preflight, bundle)
    bundle.rmdir()
    execution_path = preflight.with_name('execution.json')
    execution = json.loads(execution_path.read_bytes())
    execution['episodes'].append(deepcopy(execution['episodes'][0]))
    execution_path.write_bytes(tool._raw(execution))
    with pytest.raises(ValueError, match='Duplicate visible'):
        tool.export(root, preflight, bundle)
    assert not bundle.exists()


def test_self_check_exercises_private_invariance_and_negative_controls(tool, evidence):
    root, preflight, bundle = evidence
    tool.export(root, preflight, bundle, presentation_seed=23)
    before = {p.relative_to(bundle): p.read_bytes() for p in bundle.rglob('*') if p.is_file()}
    report_path = bundle.parent / 'self-check.json'
    report = tool.self_check(root, bundle, report_path)
    assert report['status'] == 'passed'
    assert report['first_turns_checked'] == 1
    assert report['invariance_checks'] >= 6
    assert report['positive_controls'] == 1
    assert {r['name'] for r in report['negative_verifier_checks']} >= {
        'answer_leakage', 'altered_bytes', 'wrong_filename_hash', 'missing_file',
        'metadata_tamper', 'permutation_tamper'}
    assert all(row['status'] == 'rejected' for row in report['negative_verifier_checks'])
    leakage = next(row for row in report['negative_verifier_checks'] if row['name'] == 'answer_leakage')
    assert leakage['content_hash_recomputed'] is True
    assert json.loads(report_path.read_bytes()) == report
    assert before == {p.relative_to(bundle): p.read_bytes() for p in bundle.rglob('*') if p.is_file()}
    with pytest.raises(FileExistsError):
        tool.self_check(root, bundle, report_path)


def test_verifier_rejects_symlink_and_self_check_cannot_pollute_bundle(tool, evidence):
    root, preflight, bundle = evidence
    tool.export(root, preflight, bundle)
    with pytest.raises(ValueError, match='outside'):
        tool.self_check(root, bundle, bundle / 'private/check.json')
    public = next((bundle / 'public').iterdir())
    saved = public.read_bytes()
    public.unlink()
    target = bundle.parent / 'linked.json'
    target.write_bytes(saved)
    public.symlink_to(target)
    with pytest.raises(ValueError, match='symlink'):
        tool.verify(root, bundle)
