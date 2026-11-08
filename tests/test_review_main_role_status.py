"""The outer status entry point exposes roles without bypassing blind-first work."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


POLICY = {'schema': 'arcpuzzles-parametric-main-two-checks-v1',
          'effort_percent': [70, 15, 15],
          'roles': ['parametric_main', 'robustness_check', 'robustness_check']}
IDS = ['aaaa00000001', 'aaaa00000002', 'aaaa00000003']


def workspace(tmp_path, *, policy_at=(), schema='arcpuzzles-full-assignment-v3', assigned=True):
    outer = tmp_path / 'relocated-packet'
    work = outer / 'WORK'
    work.mkdir(parents=True)
    source = Path(__file__).resolve().parents[1] / 'src/arcpuzzles/review_workspace_files/review.py'
    shutil.copyfile(source, outer / 'review.py')
    (outer / 'START-HERE.md').write_text('Start with review.py.\n')
    manifest = {'layout': {'workspace': 'WORK', 'entry_files': {
        name: hashlib.sha256((outer / name).read_bytes()).hexdigest()
        for name in ('START-HERE.md', 'review.py')}}, 'files': {}}
    contract = {'schema': schema, 'assignment_id': 'review-test', 'task_id': IDS[0]}
    if schema == 'arcpuzzles-full-assignment-v3':
        contract['repair_targets'] = [{'task_id': tid} for tid in IDS]
    if 'manifest' in policy_at:
        manifest['work_policy'] = POLICY
    if 'contract' in policy_at:
        contract['work_policy'] = POLICY
    (work / 'PACKET-MANIFEST.json').write_text(json.dumps(
        manifest, sort_keys=True, ensure_ascii=False, separators=(',', ':')))
    if assigned:
        (work / 'ASSIGNMENT.json').write_text(json.dumps(contract))
    return outer


def status(outer, cwd):
    result = subprocess.run([sys.executable, str(outer / 'review.py'), 'status'],
                            cwd=cwd, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return result.stdout


@pytest.mark.parametrize('policy_at', [('manifest',), ('contract',), ('manifest', 'contract')])
def test_new_policy_status_names_main_and_bounded_peers(tmp_path, policy_at):
    outer = workspace(tmp_path, policy_at=policy_at)
    output = status(outer, tmp_path)
    assert f'MAIN (70%): WORK/repo/generators/{IDS[0]}/' in output
    assert f'Robustness check 1 (15%): WORK/repo/generators/{IDS[1]}/' in output
    assert f'Robustness check 2 (15%): WORK/repo/generators/{IDS[2]}/' in output
    assert 'workspace/parametric/' in output
    assert 'No parametric work on the two peers.' in output
    assert 'parametric_work' in output
    assert 'Repair: WORK/repo/generators/' not in output


def test_new_policy_status_before_draw_explains_effort(tmp_path):
    outer = workspace(tmp_path, policy_at=('manifest',), assigned=False)
    output = status(outer, tmp_path)
    assert 'NEXT: python3 review.py start' in output
    assert 'MAIN parametric generator (70%)' in output
    assert 'two bounded robustness checks (15% each)' in output


def test_new_policy_status_preserves_blind_first_hiding(tmp_path):
    outer = workspace(tmp_path, policy_at=('manifest', 'contract'))
    (outer / 'WORK/BLIND_ASSIGNMENT.json').write_text('{}')
    output = status(outer, tmp_path)
    assert 'NEXT: python3 review.py blind prepare' in output
    assert 'WORK/repo/generators/' not in output
    assert 'parametric_work' not in output
    for tid in IDS:
        assert tid not in output
    finish = outer / 'WORK/solve-blind/summary.json'
    finish.parent.mkdir()
    finish.write_text(json.dumps({'stopping_reason': 'Finished visible-only attempt'}))
    assert 'MAIN (70%):' in status(outer, tmp_path)


@pytest.mark.parametrize('schema,count', [('arcpuzzles-full-assignment-v3', 3),
                                        ('arcpuzzles-full-assignment-v2', 1)])
def test_issued_legacy_status_keeps_repair_roles(tmp_path, schema, count):
    outer = workspace(tmp_path, schema=schema)
    output = status(outer, tmp_path)
    assert output.count('Repair: WORK/repo/generators/') == count
    assert 'MAIN (70%)' not in output
    assert 'parametric_work' not in output
    assert ('Legacy reports:' in output) == (count == 1)
    assert ('Two audits:' in output) == (count == 1)
