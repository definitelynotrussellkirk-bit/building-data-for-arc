"""Prepare a verified full source snapshot for the unchanged stock packager.

Uses hardlinks to conserve inodes and bytes. Every manifest file is hashed;
changed files must match the separately replayed/tested patch receipt. This does
not change any gate or packager. Do not edit source after creating the snapshot.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath
import zipfile


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def relative(name):
    p = PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError(f'unsafe relative path: {name}')
    return Path(name)


def link_verified(source, target, digest):
    if source.is_symlink() or not source.is_file() or file_sha(source) != digest:
        raise ValueError(f'file hash/type mismatch: {source}')
    target.parent.mkdir(parents=True, exist_ok=True)
    os.link(source, target)


def copy_tree(source, target):
    def ignore(directory, names):
        return [n for n in names if n in {'.rsync-tmp', '__pycache__', '.pytest_cache'}]
    for p in source.rglob('*'):
        if p.is_symlink():
            raise ValueError(f'symlink evidence: {p}')
    shutil.copytree(source, target, ignore=ignore)


def prepare(args):
    reviewed, snapshot = args.review_work.resolve(), args.snapshot.resolve()
    if snapshot.exists():
        raise FileExistsError(snapshot)
    contract = json.loads((reviewed / 'ASSIGNMENT.json').read_text())
    replay = json.loads((reviewed / 'checks/replay/replay.json').read_text())
    handoff = json.loads((reviewed / 'checks/replay/handoff.json').read_text())
    original_hash = file_sha(args.source_zip)
    if original_hash != replay['source_zip_sha256']:
        raise ValueError('original ZIP hash differs from replay receipt')
    with zipfile.ZipFile(args.source_zip) as z:
        manifest_raw = z.read('WORK/PACKET-MANIFEST.json')
        original_count = len(z.infolist())
    if manifest_raw != (reviewed / 'PACKET-MANIFEST.json').read_bytes():
        raise ValueError('manifest differs from the original ZIP')
    manifest = json.loads(manifest_raw)
    with zipfile.ZipFile(args.return_zip) as z:
        patch = z.read('patches/source.patch')
        if z.read('ASSIGNMENT.json') != (reviewed / 'ASSIGNMENT.json').read_bytes():
            raise ValueError('candidate assignment differs')
    if sha(patch) != handoff['source_patch_sha256']:
        raise ValueError('source patch differs from the tested handoff')
    changed = {r['path']: r['sha256'] for r in replay['changed_files']}
    snapshot.mkdir(parents=True)
    args.created_snapshot = True
    work = snapshot / 'WORK'
    work.mkdir()
    for name, digest in manifest['layout']['entry_files'].items():
        link_verified(reviewed.parent / relative(name), snapshot / relative(name), digest)
    (work / 'PACKET-MANIFEST.json').write_bytes(manifest_raw)
    for name, digest in manifest['files'].items():
        path = relative(name)
        link_verified(reviewed / path, work / path, changed.get(name, digest))
    for name, digest in changed.items():
        path = relative(name)
        if name not in manifest['files']:
            link_verified(reviewed / path, work / path, digest)
        if file_sha(work / path) != digest:
            raise ValueError(f'changed source differs: {name}')
    for name, digest in contract['baseline_sha256'].items():
        path = relative(name)
        link_verified(reviewed / '.review/baseline' / path,
                      work / '.review/baseline' / path, digest)
    for name in ['ASSIGNMENT.json', 'AUDIT_ASSIGNMENT.json', 'BLIND_ASSIGNMENT.json',
                 'REVIEW.md', 'DECISIONS.md', 'QUESTION_ANSWER.md', 'FEEDBACK_TO_CODEX.md',
                 'AUDIT.md', 'RESULTS.json']:
        shutil.copy2(reviewed / name, work / name)
    for name in ['checks', 'solve', 'solve-blind']:
        copy_tree(reviewed / name, work / name)
    for name in ['solve-private', 'solve-private-blind']:
        target = work / '.review' / name / 'generator.py'
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(reviewed / '.review' / name / 'generator.py', target)
    report = {'schema': 'isolated-return-preparation-v2', 'status': 'prepared',
              'mode': 'verified_manifest_hardlink_snapshot',
              'original_zip_sha256': original_hash, 'original_members': original_count,
              'manifest_files_verified': len(manifest['files']),
              'full_declared_source_inventory_materialized': True,
              'second_full_archive_extraction': False, 'snapshot': str(snapshot),
              'work_root': str(work), 'assignment_id': contract['assignment_id'],
              'source_patch_sha256': sha(patch), 'changed_paths_verified': len(changed),
              'generator_sha256': replay['generator_sha256'],
              'scope': 'All original manifest source files hashed and materialized, with only the exact tested changes. Untracked live-workspace byproducts are not part of the original archive or tested patch. Stock packaging follows without modification.',
              'source_immutability_requirement': 'Do not modify linked source files. Stock packager checks all unchanged hashes; final archive patch must match tested patch SHA.'}
    for root in [reviewed, work]:
        (root / 'checks/isolated-packaging/preparation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2), flush=True)
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-zip', type=Path, required=True)
    p.add_argument('--return-zip', type=Path, required=True)
    p.add_argument('--review-work', type=Path, required=True)
    p.add_argument('--snapshot', type=Path, required=True)
    p.add_argument('--package-out', type=Path)
    p.add_argument('--cleanup', action='store_true')
    args = p.parse_args()
    args.created_snapshot = False
    if args.cleanup and not args.package_out:
        p.error('--cleanup requires --package-out')
    if args.package_out and args.package_out.resolve().is_relative_to(args.snapshot.resolve()):
        p.error('package output must be outside the disposable snapshot')
    try:
        report = prepare(args)
        if args.package_out:
            argv = [sys.executable, 'review.py', 'package', '--out', str(args.package_out.resolve())]
            result = subprocess.run(argv, cwd=args.snapshot, text=True, capture_output=True)
            print(result.stdout, end='', flush=True)
            print(result.stderr, end='', file=sys.stderr, flush=True)
            if result.returncode:
                raise RuntimeError(f'stock packager exited {result.returncode}')
            with zipfile.ZipFile(args.package_out) as z:
                if sha(z.read('patches/source.patch')) != report['source_patch_sha256']:
                    raise ValueError('final archive patch differs from tested source')
            completion = {'status': 'stock_package_created_and_tested_patch_identical',
                          'argv': argv, 'cwd': str(args.snapshot.resolve()), 'exit_code': 0,
                          'zip': str(args.package_out.resolve()),
                          'zip_sha256': file_sha(args.package_out),
                          'source_patch_sha256': report['source_patch_sha256']}
            (args.review_work / 'checks/isolated-packaging/completion.json').write_text(
                json.dumps(completion, indent=2) + '\n')
            print(json.dumps(completion, indent=2), flush=True)
    finally:
        if args.cleanup and args.created_snapshot:
            shutil.rmtree(args.snapshot)
