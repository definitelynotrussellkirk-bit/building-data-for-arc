"""Prepare a clean, full packet for the unchanged stock return packager.

This is a packaging aid, not a gate override. It starts from the exact original
ZIP, verifies the frozen baseline, applies the already replayed source patch,
checks every changed file, and copies review evidence outside source scope.
Run the original review.py package in the printed snapshot afterward.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import stat
import subprocess
from pathlib import Path, PurePosixPath
import zipfile


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def safe_extract(archive, destination):
    with zipfile.ZipFile(archive) as z:
        names = set()
        for info in z.infolist():
            name = PurePosixPath(info.filename)
            if name.is_absolute() or '..' in name.parts or info.filename in names:
                raise ValueError(f'unsafe or repeated ZIP member: {info.filename}')
            if stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError(f'symlink ZIP member: {info.filename}')
            names.add(info.filename)
        z.extractall(destination)
        return len(z.infolist())


def copy_tree(source, target):
    def ignore(directory, names):
        return [n for n in names if n in {'.rsync-tmp', '__pycache__', '.pytest_cache'}]
    for p in source.rglob('*'):
        if p.is_symlink():
            raise ValueError(f'symlink evidence: {p}')
    shutil.copytree(source, target, ignore=ignore)


def prepare(args):
    reviewed = args.review_work.resolve()
    snapshot = args.snapshot.resolve()
    if snapshot.exists():
        raise FileExistsError(snapshot)
    contract = json.loads((reviewed / 'ASSIGNMENT.json').read_text())
    replay = json.loads((reviewed / 'checks/replay/replay.json').read_text())
    handoff = json.loads((reviewed / 'checks/replay/handoff.json').read_text())
    original_hash = sha(args.source_zip.read_bytes())
    if original_hash != replay['source_zip_sha256']:
        raise ValueError('original ZIP hash differs from replay receipt')
    with zipfile.ZipFile(args.return_zip) as z:
        patch = z.read('patches/source.patch')
        if z.read('ASSIGNMENT.json') != (reviewed / 'ASSIGNMENT.json').read_bytes():
            raise ValueError('candidate assignment differs')
    if sha(patch) != handoff['source_patch_sha256']:
        raise ValueError('source patch differs from tested handoff')
    snapshot.mkdir(parents=True)
    original_count = safe_extract(args.source_zip, snapshot)
    work = snapshot / 'WORK'
    for relative, expected in contract['baseline_sha256'].items():
        source = work / relative
        raw = source.read_bytes()
        if sha(raw) != expected:
            raise ValueError(f'original baseline mismatch: {relative}')
        target = work / '.review/baseline' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    patch_path = snapshot / 'tested-source.patch'
    patch_path.write_bytes(patch)
    commands = []
    def run(argv):
        p = subprocess.run(argv, cwd=work, text=True, capture_output=True)
        commands.append({'argv': argv, 'cwd': str(work), 'exit_code': p.returncode,
                         'stdout': p.stdout, 'stderr': p.stderr})
        if p.returncode:
            raise RuntimeError(p.stderr or p.stdout)
        return p.stdout.strip()
    run(['git', 'init', '-q'])
    if Path(run(['git', 'rev-parse', '--show-toplevel'])).resolve() != work:
        raise ValueError('wrong Git root')
    run(['git', 'apply', '--check', str(patch_path)])
    run(['git', 'apply', str(patch_path)])
    for row in replay['changed_files']:
        relative, expected = row['path'], row['sha256']
        if sha((work / relative).read_bytes()) != expected:
            raise ValueError(f'replayed file mismatch: {relative}')
        if sha((reviewed / relative).read_bytes()) != expected:
            raise ValueError(f'reviewed source changed: {relative}')
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
    report = {'schema': 'isolated-return-preparation-v1', 'status': 'prepared',
              'original_zip_sha256': original_hash, 'original_members_extracted': original_count,
              'full_original_packet_extracted': True, 'snapshot': str(snapshot),
              'work_root': str(work), 'assignment_id': contract['assignment_id'],
              'source_patch_sha256': sha(patch), 'changed_paths_verified': len(replay['changed_files']),
              'generator_sha256': replay['generator_sha256'], 'commands': commands,
              'scope': 'Fresh full source extraction plus exact tested patch and copied review evidence. Stock packaging and archive verification follow separately.'}
    for root in [reviewed, work]:
        target = root / 'checks/isolated-packaging/preparation.json'
        target.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-zip', type=Path, required=True)
    p.add_argument('--return-zip', type=Path, required=True)
    p.add_argument('--review-work', type=Path, required=True)
    p.add_argument('--snapshot', type=Path, required=True)
    prepare(p.parse_args())
