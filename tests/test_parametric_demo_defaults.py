"""Default qualification counts stay inside each family's declared support."""
import json
import zipfile

import pytest

from arcpuzzles import Catalog, cli
from arcpuzzles import parametric_promotion as native
from arcpuzzles import review_parametric_admission as admission


@pytest.mark.parametrize('bounds,requested,expected', [
    ([2, 6], None, 2), ([5, 6], None, 5), ([2, 2], None, 2),
    ([3, 6], 4, 4), ([5, 6], 6, 6)])
def test_supported_default(bounds, requested, expected):
    assert admission.qualification_demo_count({'limits': {'demos': bounds}}, requested) == expected


@pytest.mark.parametrize('requested', [3, True, 7])
def test_unsupported_explicit_count_is_not_coerced(requested):
    with pytest.raises(ValueError):
        admission.qualification_demo_count({'limits': {'demos': [5, 6]}}, requested)


def test_contract_can_name_its_qualification_count():
    assert admission.qualification_demo_count(
        {'limits': {'demos': [2, 6]}, 'qualification_demos': 4}) == 4


def test_cli_uses_family_minimum_when_flag_omitted(library, tmp_path, monkeypatch, capsys):
    contract = {'limits': {'demos': [5, 6]}}
    monkeypatch.setattr(native, '_ready', lambda *a: (contract, {}))
    seen = []
    def qualify(*args, **kwargs):
        seen.append(kwargs['demos']); return {'status': 'qualified'}
    monkeypatch.setattr(native, 'qualify', qualify)
    assert cli.main(['--library', str(library), 'parametric', 'qualify', 'aaaa00000001',
                     '--out', str(tmp_path / 'q')]) == 0
    assert seen == [5]


@pytest.mark.parametrize('action', ['generate', 'export'])
@pytest.mark.parametrize('requested', [None, 6])
def test_cli_generation_uses_supported_count(action, requested, library, tmp_path, monkeypatch, capsys):
    contract = {'limits': {'demos': [5, 6]}}
    monkeypatch.setattr(native, '_ready', lambda *a: (contract, {}))
    seen = []
    def run(*args, **kwargs):
        seen.append(kwargs['demos'])
        return {} if action == 'export' else []
    monkeypatch.setattr(native, action, run)
    args = ['--library', str(library), 'parametric', action, 'aaaa00000001',
            '--out', str(tmp_path / 'output')]
    if requested is not None:
        args += ['--demos', str(requested)]
    assert cli.main(args) == 0
    assert seen == [5 if requested is None else requested]


def test_owner_main_admission_uses_supported_count(library, tmp_path, monkeypatch):
    contract = {'limits': {'demos': [2, 6]}}; binding = {'files': []}
    reported = {'source_binding': binding, 'contract': contract, 'programs': {'setting': 'hash'},
                'jobs': [{'demos': 5}, {'demos': 5}]}
    monkeypatch.setattr(native, '_ready', lambda *a: (contract, binding))
    monkeypatch.setattr(admission, 'validate_ready_evidence', lambda *a: reported)
    monkeypatch.setattr(admission, 'validate_sequential_witness', lambda *a: {})
    import arcpuzzles.review_sequential_replay as replay
    monkeypatch.setattr(replay, 'replay_witness', lambda *a: {'status': 'owner_replayed'})
    seen = []
    def qualify(*args, **kwargs):
        seen.append(kwargs['demos']); return {**reported, 'receipt': str(tmp_path / 'q.json')}
    monkeypatch.setattr(native, 'qualify', qualify)
    monkeypatch.setattr(native, 'accept', lambda *a, **k: {'status': 'accepted'})
    monkeypatch.setattr(native, 'status', lambda *a: {'status': 'accepted', 'acceptance_sha256': 'a' * 64})
    archive = tmp_path / 'return.zip'
    with zipfile.ZipFile(archive, 'w') as z:
        for name in ('checks/q/qualification.json', 'checks/q/execution.json', 'checks/witness.json'):
            z.writestr(name, '{}')
    draw = {'work_policy': {'schema': admission.ADMISSION_WORK_SCHEMA},
            'task_id': 'aaaa00000001', 'assignment_id': 'review-fixture'}
    row = {'parametric_work': {'status': 'ready', 'qualification_path': 'checks/q/qualification.json',
           'inventory_path': 'repo/generators/aaaa00000001/workspace/parametric/evidence/manifest.json',
           'sequential_dependency': {'witness_path': 'checks/witness.json'}}}
    result = admission.admit_main(Catalog(library), draw, row, archive)
    assert result['status'] == 'accepted', result
    assert seen == [5]
