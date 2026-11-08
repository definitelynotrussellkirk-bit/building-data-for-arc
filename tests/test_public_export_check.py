"""Saved public artifacts are a cheap boundary before reference execution."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys

import pytest

from reviewer_support import public_challenge_bytes


ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / 'src/arcpuzzles/review_full_packet_files/check_public_exports.py'


def challenge():
    return {'train': [{'input': [[1]], 'output': [[3]]},
                      {'input': [[2]], 'output': [[4]]}],
            'test': [{'input': [[n]]} for n in (5, 6, 7, 8)]}


def save(folder, value=None, raw=None, name=None):
    folder.mkdir(parents=True, exist_ok=True)
    raw = public_challenge_bytes(challenge() if value is None else value) if raw is None else raw
    path = folder / (name or hashlib.sha256(raw).hexdigest() + '.json')
    path.write_bytes(raw)
    return path


def check(*paths, arguments=(), entry=ENTRY):
    assert entry.is_file(), 'The portable public-export checker has not been implemented'
    result = subprocess.run([sys.executable, '-I', str(entry), *map(str, paths), *arguments],
                            capture_output=True, text=True)
    assert result.stdout, result.stderr
    return result.returncode, json.loads(result.stdout)


def codes(report):
    return {row['code'] for row in report['findings']}


def test_flat_directory_and_explicit_file_are_read_only(tmp_path):
    path = save(tmp_path / 'public')
    before = {str(p): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    code, report = check(path.parent, path)
    assert code == 0 and report['status'] == 'passed'
    assert report['files_checked'] == 1 and report['queries'] == 4
    assert report['files'][0]['demonstrations'] == 2
    assert before == {str(p): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    assert report['reference_labels_checked'] is False


@pytest.mark.parametrize('style', ['digest', 'challenge-prefix', 'digest-directory'])
def test_supported_exact_digest_names(tmp_path, style):
    raw = public_challenge_bytes(challenge())
    digest = hashlib.sha256(raw).hexdigest()
    folder = tmp_path / digest if style == 'digest-directory' else tmp_path
    name = 'public.json' if style == 'digest-directory' else (
        'challenge-' + digest + '.json' if style == 'challenge-prefix' else digest + '.json')
    code, report = check(save(folder, raw=raw, name=name))
    assert code == 0, report


@pytest.mark.parametrize('mutation,expected', [
    ('private-top-level', 'public_schema'),
    ('private-demo-field', 'public_schema'),
    ('query-output', 'public_schema'),
    ('boolean', 'public_grid'),
    ('float', 'public_grid'),
    ('ragged', 'public_grid'),
    ('empty-train', 'public_grid'),
    ('duplicate-input', 'duplicate_input'),
])
def test_rejects_actual_serialized_export_defects(tmp_path, mutation, expected):
    value = challenge()
    if mutation == 'private-top-level': value['seed'] = 123
    if mutation == 'private-demo-field': value['train'][0]['setting'] = 'private'
    if mutation == 'query-output': value['test'][0]['output'] = [[9]]
    if mutation == 'boolean': value['train'][0]['output'] = [[False]]
    if mutation == 'float': value['train'][0]['output'] = [[3.0]]
    if mutation == 'ragged': value['test'][0]['input'] = [[5], [5, 5]]
    if mutation == 'empty-train': value['train'] = []
    if mutation == 'duplicate-input': value['test'][0]['input'] = [[1]]
    raw = (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()
    code, report = check(save(tmp_path, raw=raw))
    assert code == 1 and expected in codes(report)


def test_requires_exact_saved_helper_bytes_not_equivalent_json(tmp_path):
    path = save(tmp_path, raw=json.dumps(challenge(), indent=2).encode())
    code, report = check(path)
    assert code == 1 and 'canonical_bytes' in codes(report)


def test_rejects_normalized_prefix_and_setting_named_ids(tmp_path):
    for name in ['challenge-deadbeef12345678.json', 'connectivity-4.json']:
        code, report = check(save(tmp_path / name[:-5], name=name))
        assert code == 1 and 'public_id' in codes(report)


def test_counts_are_independent_and_configurable(tmp_path):
    value = challenge(); value['test'].pop()
    path = save(tmp_path, value)
    code, report = check(path)
    assert code == 1 and 'query_count' in codes(report)
    code, report = check(path, arguments=['--queries', '3', '--demos', '2'])
    assert code == 0, report
    code, report = check(path, arguments=['--queries', '3', '--demos', '1'])
    assert code == 1 and 'demo_count' in codes(report)


def test_duplicate_public_payloads_across_distinct_files_fail(tmp_path):
    first = save(tmp_path / 'first'); second = save(tmp_path / 'second')
    code, report = check(first, second)
    assert code == 1 and 'duplicate_public_payload' in codes(report)


@pytest.mark.parametrize('raw', [b'{"train":[],"train":[],"test":[]}', b'{"test":NaN}', b'\xff'])
def test_invalid_json_is_a_reported_failure(tmp_path, raw):
    code, report = check(save(tmp_path, raw=raw))
    assert code == 1 and 'public_json' in codes(report)


def test_empty_missing_nested_or_nonjson_directory_is_not_a_pass(tmp_path):
    code, report = check(tmp_path)
    assert code == 1 and 'no_public_files' in codes(report)
    code, report = check(tmp_path / 'missing')
    assert code == 1 and 'missing_path' in codes(report)
    save(tmp_path)
    (tmp_path / 'private.txt').write_text('setting=private')
    (tmp_path / 'nested').mkdir()
    code, report = check(tmp_path)
    assert code == 1 and {'unexpected_member'} <= codes(report)


def test_symlink_members_are_never_read(tmp_path):
    outside = save(tmp_path / 'outside')
    public = tmp_path / 'public'; public.mkdir()
    (public / outside.name).symlink_to(outside)
    code, report = check(public)
    assert code == 1 and 'symlink' in codes(report)
    assert report['files_checked'] == 0


def test_copied_packet_uses_its_own_helper_without_owner_pythonpath(tmp_path):
    work = tmp_path / 'WORK'; work.mkdir()
    assert ENTRY.is_file(), 'The portable public-export checker has not been implemented'
    shutil.copy2(ENTRY, work / ENTRY.name)
    runtime = work / 'repo/shared/runtime'; runtime.mkdir(parents=True)
    shutil.copy2(ROOT / 'shared/runtime/reviewer_support.py', runtime / 'reviewer_support.py')
    # A different helper on the process import path must not become a dependency.
    poison = tmp_path / 'poison'; poison.mkdir()
    (poison / 'reviewer_support.py').write_text('raise RuntimeError("borrowed helper")')
    env = dict(os.environ, PYTHONPATH=str(poison))
    path = save(work / 'checks/public')
    result = subprocess.run([sys.executable, str(work / ENTRY.name), str(path)],
                            cwd=tmp_path, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['files_checked'] == 1
    assert not list(runtime.rglob('*.pyc')), 'A read-only check must not spend file slots on bytecode'


def test_packet_missing_local_helper_never_borrows_an_ancestor_tree(tmp_path):
    work = tmp_path / 'outer/one/WORK'; work.mkdir(parents=True)
    shutil.copy2(ENTRY, work / ENTRY.name)
    unrelated = tmp_path / 'shared/runtime'; unrelated.mkdir(parents=True)
    (unrelated / 'reviewer_support.py').write_text('raise RuntimeError("borrowed ancestor")')
    code, report = check(save(work / 'public'), entry=work / ENTRY.name)
    assert code == 1 and codes(report) == {'check_setup'}


def test_utf16_is_not_the_canonical_utf8_transport(tmp_path):
    code, report = check(save(tmp_path, raw=json.dumps(challenge()).encode('utf-16')))
    assert code == 1 and 'public_json' in codes(report)



def test_summary_retains_findings_and_hashes_sorted_content_multiset(tmp_path):
    first = save(tmp_path / 'first')
    other = challenge(); other['train'][0]['output'] = [[9]]
    second = save(tmp_path / 'second', other)
    code, full = check(first, second)
    summary_code, summary = check(second, first, arguments=['--summary'])
    assert code == summary_code == 0
    assert 'files' not in summary
    assert summary['files_checked'] == 2
    assert summary['files_hashed'] == 2
    hashes = sorted(row['sha256'] for row in full['files'])
    expected = hashlib.sha256(('\n'.join(hashes) + '\n').encode('ascii')).hexdigest()
    assert summary['content_multiset_sha256'] == expected
    assert summary['findings'] == full['findings']
    relocated = tmp_path / 'relocated'; relocated.mkdir()
    for path in (first, second): shutil.copy2(path, relocated / path.name)
    _, moved = check(relocated, arguments=['--summary'])
    assert moved['content_multiset_sha256'] == expected
    _, duplicated = check(first, save(tmp_path / 'duplicate'), arguments=['--summary'])
    assert duplicated['status'] == 'failed'
    assert 'duplicate_public_payload' in codes(duplicated)
    assert duplicated['content_multiset_sha256'] != expected


def test_summary_does_not_hide_failure_or_setup_error(tmp_path):
    path = save(tmp_path, raw=b'bad-json')
    code, summary = check(path, arguments=['--summary'])
    assert code == 1 and 'public_json' in codes(summary)
    assert summary['files_hashed'] == 1
    assert 'files' not in summary
    work = tmp_path / 'WORK'; work.mkdir()
    shutil.copy2(ENTRY, work / ENTRY.name)
    code, summary = check(path, entry=work / ENTRY.name, arguments=['--summary'])
    assert code == 1 and codes(summary) == {'check_setup'}
    assert summary['files_hashed'] == 0
