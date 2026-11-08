"""A retained compression index must remain usable after transport disposal."""
import gzip
import json
from pathlib import Path
import zipfile

import pytest

from arcpuzzles.catalog import Catalog
from arcpuzzles.review_full_packet import build_full_packet
from arcpuzzles.review_full_return import build_full_return
from arcpuzzles.review_full_collect import collect_full_returns
from arcpuzzles.review_full_integrate import record_full_disposition
from arcpuzzles.review_retention import compact_reviews
from arcpuzzles.review_solve import digest
from test_review_full_collect import _return


def _compressed_return(library, tmp_path, schema, *, bundled=False, corrupt=None, audit=False):
    contract, returned = _return(library, tmp_path, audit=audit,
        feedback_text='## F1: Keep compressed evidence\n\nSee `checks/EVIDENCE_INDEX.json` and `checks/tooling/restore.py`.\n')
    packet = tmp_path / 'packet-0'
    original = b'{"task_id":"example","observations":[1,2,3]}\n'
    payload = gzip.compress(original, mtime=0)
    name = 'checks/compressed/files/observations.json.gz'
    row = dict(compressed_path=name, compressed_bytes=len(payload), compressed_sha256=digest(payload),
        original_path='checks/observations.json', original_bytes=len(original), original_sha256=digest(original))
    if schema == 'arcpuzzles-evidence-gzip-v1':
        name = 'checks/observations.json.gz'
        row['compressed_path'] = name
    if corrupt:
        corrupt(row)
    index = {'schema': schema, 'entries' if schema == 'arc-review-evidence-archive-v1' else 'files': [row]}
    if schema == 'review-large-evidence-v1':
        index.update(compression='gzip', count=1, original_bytes=row['original_bytes'],
                     compressed_bytes=row['compressed_bytes'])
    if schema == 'arcpuzzles-evidence-gzip-v1':
        # This supplied tool stores paths relative to the manifest's directory,
        # unlike the older indexes' complete checks/ transport member names.
        row = {'path': row['original_path'].removeprefix('checks/'),
               'compressed_path': row['compressed_path'].removeprefix('checks/'),
               'raw_size': row['original_bytes'], 'raw_sha256': row['original_sha256'],
               'compressed_size': row['compressed_bytes'], 'compressed_sha256': row['compressed_sha256']}
        index['files'] = [row]
    files = {'checks/EVIDENCE_INDEX.json': json.dumps(index).encode(), name: payload,
        'checks/tooling/restore.py': b'raise AssertionError("must not execute")\n',
        'checks/tooling/unreferenced.py': b'not selected\n',
        'checks/unrelated.json': b'{"not":"selected"}\n'}
    for n, raw in files.items():
        path = packet / n; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
    if audit:
        targets = json.loads((packet / 'AUDIT_ASSIGNMENT.json').read_text())['targets']
        (packet / 'AUDIT.md').write_text(''.join(f"## {t['task_id']}\nEvidence `checks/EVIDENCE_INDEX.json`.\n" for t in targets))
    Path(returned['zip']).unlink()
    build_full_return(packet, Path(returned['zip']), bundle_evidence=bundled)
    receipt = collect_full_returns(library / 'REVIEW', tmp_path)['receipts'][0]
    assert receipt['validation_status'] == 'accepted'
    record_full_disposition(library / 'REVIEW', contract['assignment_id'], 1,
                            'decision', 'deferred', 'Keep the supplied evidence index.')
    return receipt, files


@pytest.mark.parametrize('schema', ['arc-review-evidence-archive-v1', 'review-large-evidence-v1',
                                   'arcpuzzles-evidence-gzip-v1'])
@pytest.mark.parametrize('bundled', [False, True])
def test_manifest_payload_survives_disposal_and_repackaging(library, tmp_path, schema, bundled):
    receipt, files = _compressed_return(library, tmp_path, schema, bundled=bundled, audit=True)
    compact_reviews(library, apply=True)
    assert not Path(receipt['archive_path']).exists()
    request = next(i for i in json.loads((library / 'REVIEW/suggestions.json').read_text())['items']
                   if i.get('request_id', '').endswith(':F1'))
    manifest = json.loads((library / request['assets_manifest']['path']).read_text())
    payload_name = next(n for n in files if n.endswith('.gz'))
    expected = {'checks/EVIDENCE_INDEX.json', payload_name,
                'checks/tooling/restore.py'}
    assert {r['source_member'] for r in manifest['files']} == expected
    for row in manifest['files']:
        assert (library / row['path']).read_bytes() == files[row['source_member']]
    # Same closure is kept beside each task-owned audit index.
    for path in (library / 'generators').glob('*/counterexamples/*/audit_assets.json'):
        assets = json.loads(path.read_text())['files']
        assert {r['original_member'] for r in assets} == expected - {'checks/tooling/restore.py'}
        for row in assets: assert (library / row['path']).read_bytes() == files[row['original_member']]
    assert not list(library.rglob('unreferenced.py'))
    built = build_full_packet(Catalog(library), library / 'REVIEW', tmp_path / 'next.zip')
    with zipfile.ZipFile(built['zip']) as archive:
        for row in manifest['files']: assert archive.read('repo/' + row['path']) == files[row['source_member']]


@pytest.mark.parametrize('mutation', [
    lambda r: r.update(compressed_path='checks/missing.json.gz'),
    lambda r: r.update(compressed_sha256='0' * 64),
    lambda r: r.update(compressed_bytes=r['compressed_bytes'] + 1),
    lambda r: r.update(original_sha256='0' * 64),
    lambda r: r.update(original_bytes=r['original_bytes'] - 1),
    lambda r: r.update(compressed_path='checks/../outside.gz'),
    lambda r: r.update(compressed_path='checks/runtime/hidden.gz'),
    lambda r: r.update(original_bytes=True),
])
@pytest.mark.parametrize('schema', ['arc-review-evidence-archive-v1', 'arcpuzzles-evidence-gzip-v1'])
def test_invalid_dependency_keeps_transport(library, tmp_path, mutation, schema):
    receipt, _ = _compressed_return(library, tmp_path, schema, corrupt=mutation)
    with pytest.raises(ValueError, match='[Cc]ompressed evidence'):
        compact_reviews(library, apply=True)
    assert Path(receipt['archive_path']).is_file()
    assert (library / 'REVIEW/assignments' / receipt['assignment_id']).is_dir()


def test_native_gzip_index_resolves_manifest_relative_members_only():
    from arcpuzzles.review_retention import _compressed_dependencies, _verify_compressed_dependencies
    raw = b'original'
    payload = gzip.compress(raw, mtime=0)
    index_name = 'checks/deep/bundle/MANIFEST.json'
    member = 'checks/deep/bundle/observations.json.gz'
    row = {'path': 'observations.json', 'compressed_path': 'observations.json.gz',
           'raw_size': len(raw), 'raw_sha256': digest(raw),
           'compressed_size': len(payload), 'compressed_sha256': digest(payload)}
    index = json.dumps({'schema': 'arcpuzzles-evidence-gzip-v1', 'files': [row]}).encode()
    files = {index_name: index, member: payload}
    selected, entries = _compressed_dependencies({index_name}, set(files), files.__getitem__)
    assert selected == set(files)
    _verify_compressed_dependencies(entries, files.__getitem__)
    # An identically named payload elsewhere is not this bundle's dependency.
    with pytest.raises(ValueError, match='missing dependency'):
        _compressed_dependencies({index_name}, {index_name, 'checks/observations.json.gz'}, files.__getitem__)


@pytest.mark.parametrize('change', [
    {'path': '../observations.json', 'compressed_path': '../observations.json.gz'},
    {'path': '/observations.json', 'compressed_path': '/observations.json.gz'},
    {'path': 'runtime/value', 'compressed_path': 'runtime/value.gz'},
    {'path': 'observations.json', 'compressed_path': 'different.gz'},
    {'raw_size': True},
    {'compressed_size': '20'},
])
def test_native_gzip_index_rejects_invalid_declared_contract(change):
    from arcpuzzles.review_retention import _compressed_dependencies
    row = {'path': 'observations.json', 'compressed_path': 'observations.json.gz',
           'raw_size': 1, 'raw_sha256': 'a' * 64,
           'compressed_size': 20, 'compressed_sha256': 'b' * 64, **change}
    files = {'checks/MANIFEST.json': json.dumps({'schema': 'arcpuzzles-evidence-gzip-v1', 'files': [row]}).encode()}
    with pytest.raises(ValueError, match='Compressed evidence'):
        _compressed_dependencies(set(files), {*files, 'checks/' + row['compressed_path']}, files.__getitem__)


@pytest.mark.parametrize('paths', [['value', 'value/child'], ['value', 'value.gz/child'],
                                 ['MANIFEST.json/child']])
def test_native_gzip_index_rejects_file_directory_collisions(paths):
    from arcpuzzles.review_retention import _compressed_dependencies
    rows = [{'path': p, 'compressed_path': p + '.gz', 'raw_size': 1,
             'raw_sha256': 'a' * 64, 'compressed_size': 20, 'compressed_sha256': 'b' * 64}
            for p in paths]
    index = 'checks/bundle/MANIFEST.json'
    files = {index: json.dumps({'schema': 'arcpuzzles-evidence-gzip-v1', 'files': rows}).encode()}
    names = {*files, *('checks/bundle/' + r['compressed_path'] for r in rows)}
    with pytest.raises(ValueError, match='collision'):
        _compressed_dependencies(set(files), names, files.__getitem__)


def test_native_gzip_index_requires_nonempty_files():
    from arcpuzzles.review_retention import _compressed_dependencies
    index = 'checks/bundle/MANIFEST.json'
    with pytest.raises(ValueError, match='files must not be empty'):
        _compressed_dependencies({index}, {index}, lambda _: b'{"schema":"arcpuzzles-evidence-gzip-v1","files":[]}')


def test_bad_gzip_and_conflicting_indexes_are_rejected():
    from arcpuzzles.review_retention import _compressed_dependencies, _verify_compressed_dependencies
    original = b'original'
    broken = b'not gzip'
    row = dict(compressed_path='checks/value.gz', original_path='checks/value.json',
               original_bytes=len(original), original_sha256=digest(original),
               compressed_bytes=len(broken), compressed_sha256=digest(broken))
    with pytest.raises(ValueError, match='cannot be decompressed'):
        _verify_compressed_dependencies([row], lambda _: broken)
    valid = gzip.compress(original, mtime=0)
    row.update(compressed_bytes=len(valid), compressed_sha256=digest(valid))
    conflicting = {**row, 'original_sha256': '0' * 64}
    with pytest.raises(ValueError, match='conflicting declarations'):
        _verify_compressed_dependencies([row, conflicting], lambda _: valid)
    index = {'schema': 'arc-review-evidence-archive-v1', 'entries': [row, row]}
    with pytest.raises(ValueError, match='duplicate'):
        _compressed_dependencies({'checks/index.json'}, {'checks/index.json', row['compressed_path']},
                                 lambda _: json.dumps(index).encode())


def test_unknown_index_stays_ordinary_evidence():
    from arcpuzzles.review_retention import _compressed_dependencies
    chosen = {'checks/index.json'}
    expanded, entries = _compressed_dependencies(chosen, chosen,
        lambda _: b'{"schema":"unknown-index","files":[{"compressed_path":"missing"}]}')
    assert expanded == chosen and entries == []
