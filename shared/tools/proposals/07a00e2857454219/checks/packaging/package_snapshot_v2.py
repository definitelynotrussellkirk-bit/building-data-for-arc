"""Build an official return from an isolated, verified packaging snapshot.

Repository source is never moved or changed. Every source file is copied,
including undeclared files, so the official backend still enforces its scope.
Only verified authority-sync operational artifacts and duplicate evidence are
omitted. Hard links keep the read-only snapshot inexpensive where supported.
"""
from pathlib import Path
import argparse
import fcntl
import gzip
import hashlib
import json
import os
import shutil
import sys
import tarfile
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('--packet', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
root = args.packet.resolve()
work, checks = root / 'WORK', root / 'WORK/checks'
snapshot = Path(tempfile.mkdtemp(prefix='arc-review-final-snapshot-')) / 'WORK'
snapshot.mkdir()
ignored, inventory = set(), []
lock_stream = None


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def exclude(file, reason):
    raw = file.read_bytes()
    relative = file.relative_to(work).as_posix()
    ignored.add(relative)
    inventory.append({'path': relative, 'bytes': len(raw),
                      'sha256': digest(raw), 'reason': reason})


def copy_file(source):
    relative = source.relative_to(work)
    if relative.as_posix() in ignored:
        return
    if source.is_symlink():
        raise ValueError(f'Symlink is not accepted in packaging snapshot: {relative}')
    target = snapshot / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, target)
    except OSError:
        shutil.copy2(source, target)


def copy_tree(source):
    for file in source.rglob('*'):
        if file.is_file() or file.is_symlink():
            relative = file.relative_to(work)
            if any(part in {'__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache'}
                   for part in relative.parts) or file.suffix in {'.pyc', '.pyo'}:
                continue
            copy_file(file)


try:
    baseline = json.loads((work / 'ASSIGNMENT.json').read_text())['baseline_sha256']
    lock = work / 'repo/REVIEW/.lock'
    if lock.exists():
        assert lock.read_bytes() == b''
        lock_stream = lock.open('rb')
        fcntl.flock(lock_stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        exclude(lock, 'Inactive empty lock created by supported authority-sync; not baseline source.')
    recovery = work / 'repo/var/review/authority-sync'
    if recovery.exists():
        for file in recovery.rglob('*'):
            if not file.is_file():
                continue
            if file.name == 'receipt.json':
                assert file.read_bytes() == (checks / 'authority-sync/apply-receipt.json').read_bytes()
            else:
                suffix = str(file).split('/originals/', 1)[1]
                assert digest(file.read_bytes()) == baseline['repo/' + suffix]
            exclude(file, 'Verified authority-sync recovery artifact, retained by the original packet and apply receipt.')
    for manifest in checks.rglob('*.compression.json'):
        data = json.loads(manifest.read_text())
        if data.get('schema') != 'arcpuzzles-evidence-gzip-v1':
            continue
        for item in data['files']:
            original = manifest.parent / item['path']
            compressed = (manifest.parent / item['compressed_path']).read_bytes()
            raw = gzip.decompress(compressed)
            assert len(raw) == item['raw_size'] and digest(raw) == item['raw_sha256']
            assert len(compressed) == item['compressed_size'] and digest(compressed) == item['compressed_sha256']
            if original.exists():
                assert original.read_bytes() == raw
                exclude(original, 'Exact bytes retained in verified native gzip and neighboring restoration manifest.')
    with tarfile.open(checks / 'parametric/intermediate_eeaa1111.tar.gz', 'r:gz') as archive:
        saved = {m.name: archive.extractfile(m).read() for m in archive.getmembers() if m.isfile()}
    for name in ('final', 'intermediate_source_unpacked'):
        folder = checks / 'parametric' / name
        if folder.exists():
            for file in folder.rglob('*'):
                if file.is_file():
                    assert any(raw == file.read_bytes() for path, raw in saved.items()
                               if path.endswith('/' + str(file.relative_to(folder))))
                    exclude(file, 'Duplicate intermediate parameter evidence retained in verified archive and manifest.')
    log = checks / 'packaging'
    log.mkdir(exist_ok=True)
    (log / 'snapshot-policy.json').write_text(json.dumps({
        'schema': 'review-packaging-snapshot-v2',
        'policy': 'Separate read-only snapshot; copy all repository sources except verified authority-sync operational artifacts. Omit only verified evidence duplicates and generated caches. Original files are never moved or modified.',
        'backend': 'arcpuzzles.review_full_return.build_full_return',
        'source_work': str(work), 'snapshot_work': str(snapshot),
        'files': inventory}, indent=2) + '\n')
    (checks / 'review-ledger.json').write_bytes((work / 'RESULTS.json').read_bytes())
    for name in ('PACKET-MANIFEST.json', 'ASSIGNMENT.json', 'AUDIT_ASSIGNMENT.json',
                 'BLIND_ASSIGNMENT.json', 'REVIEW.md', 'DECISIONS.md',
                 'QUESTION_ANSWER.md', 'FEEDBACK_TO_CODEX.md', 'AUDIT.md', 'RESULTS.json'):
        source = work / name
        if source.is_file():
            copy_file(source)
    for name in ('repo', '.review/baseline', 'checks', 'solve', 'solve-blind'):
        copy_tree(work / name)
    for name in ('.review/solve-private/generator.py', '.review/solve-private-blind/generator.py'):
        source = work / name
        if source.is_file():
            copy_file(source)
    assert not (snapshot / 'repo/REVIEW/.lock').exists()
    for relative in ignored:
        assert not (snapshot / relative).exists(), relative
    sys.path.insert(0, str(work / 'repo/src'))
    from arcpuzzles.review_full_return import build_full_return
    result = build_full_return(snapshot, args.out, bundle_evidence=True)
    (log / (args.out.stem + '.json')).write_text(json.dumps({
        'cwd': 'packet_root', 'argv': sys.argv, 'exit_code': 0,
        'backend': 'arcpuzzles.review_full_return.build_full_return',
        'snapshot_work': str(snapshot), 'result': result}, indent=2) + '\n')
    print(json.dumps({'zip': result['zip'], 'zip_sha256': result['zip_sha256'],
                      'completion_state': result['completion_state'],
                      'patch_paths': result['patch_paths'], 'snapshot_work': str(snapshot)}))
finally:
    if lock_stream is not None:
        lock_stream.close()
