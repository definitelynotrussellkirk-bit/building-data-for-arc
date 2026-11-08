"""Environment-specific checkpoint orchestration for one official replay.

Normal machines should use the supplied public replay-return --runtime-closure
command. This script accommodates the measured 64 MiB tmpfs and inode limit.
It deletes only its own exact temporary roots after verifying a full checkpoint.
It never changes the shipped builder, validator, replay implementation or patch.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tarfile
import time
import traceback
import zipfile

ROOT = Path('/dev/arc_review_122421_b4a2803c2341')
WORK = ROOT / 'WORK'
SCRATCH = Path('/workspace/scratch/b4a2803c2341')
SOURCE = SCRATCH / 'upload/SEND-THIS-ARCpuzzles-review(20261023-122421).zip'
RETURNED = SCRATCH / 'outputs/candidate-review-8bbc1d0a8ab0ba4b.zip'
FRESH = Path('/dev/arc_replay_122421_b4a2803c2341')
CHECKPOINT = SCRATCH / 'outputs/checkpoint-122421.tar.gz'
SAVED = SCRATCH / 'outputs/replay-122421'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, obj):
    Path(path).write_text(json.dumps(obj, sort_keys=True, indent=2) + '\n')


def inventory(root):
    result = {}
    for path in sorted(root.rglob('*')):
        mode = path.lstat().st_mode
        name = path.relative_to(root).as_posix()
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise RuntimeError(f'Unexpected checkpoint source type: {path}')
        result[name] = {'sha256': sha(path), 'bytes': path.stat().st_size,
                        'mode': stat.S_IMODE(mode)}
    return result


def safe_remove_owned(root):
    if root not in {ROOT, FRESH} or root.is_symlink() or root.parent != Path('/dev'):
        raise RuntimeError(f'Refusing unexpected removal root: {root}')
    if root.exists():
        shutil.rmtree(root)


def restore_checkpoint(prefix=None):
    with tarfile.open(CHECKPOINT, 'r:gz') as archive:
        for member in archive:
            if member.isdir():
                if prefix is None or member.name == prefix or member.name.startswith(prefix + '/'):
                    target = ROOT / member.name
                    target.mkdir(parents=True, exist_ok=True)
                    target.chmod(member.mode)
                continue
            if not member.isfile():
                raise RuntimeError('Checkpoint must contain only regular files and directories')
            name = Path(member.name)
            if name.is_absolute() or '..' in name.parts:
                raise RuntimeError('Unsafe checkpoint member')
            if prefix is not None and not member.name.startswith(prefix + '/'):
                continue
            target = ROOT / member.name
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(member) as source, target.open('xb') as dest:
                shutil.copyfileobj(source, dest)
            target.chmod(member.mode)


def main():
    started = time.monotonic()
    os.chdir(SCRATCH)
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    if CHECKPOINT.exists() or SAVED.exists() or FRESH.exists():
        raise RuntimeError('Checkpoint, saved results and fresh checkout must all be new')
    if not ROOT.is_dir() or ROOT.is_symlink():
        raise RuntimeError('Expected owned source workspace is missing or unsafe')
    SAVED.mkdir()
    sys.path.insert(0, str(WORK / 'repo/src'))
    from arcpuzzles.review_full_return import validate_full_return
    from arcpuzzles.review_replay import replay_return

    with zipfile.ZipFile(SOURCE) as source, zipfile.ZipFile(RETURNED) as returned:
        manifest = json.loads(source.read('WORK/PACKET-MANIFEST.json'))
        checked = validate_full_return(returned, manifest)
        changed_bytes = {name: (WORK / name).read_bytes() for name in checked['patch_paths']}
        patch_hash = hashlib.sha256(returned.read('patches/source.patch')).hexdigest()
    replay_source = WORK / 'repo/src/arcpuzzles/review_replay.py'
    validator_source = WORK / 'repo/src/arcpuzzles/review_full_return.py'
    for path in (replay_source, validator_source):
        relative = path.relative_to(WORK).as_posix()
        assert sha(path) == manifest['files'][relative], relative
    receipt = {
        'schema': 'one-review-low-space-replay-orchestration-v1',
        'command': [sys.executable, '-B', str(Path(__file__).absolute())],
        'cwd': str(SCRATCH), 'script_sha256': sha(__file__),
        'source_zip_sha256': sha(SOURCE), 'candidate_zip_sha256': sha(RETURNED),
        'candidate_patch_sha256': patch_hash,
        'official_replay_source_sha256': sha(replay_source),
        'official_validator_source_sha256': sha(validator_source),
        'original_compare_work': str(WORK),
        'scope': 'Unmodified public replay_return API with runtime_closure=True; only declared closure extracted; separate real tests from applied checkout.',
        'status': 'running',
    }
    save(SAVED / 'orchestration.json', receipt)
    before = inventory(ROOT)
    with tarfile.open(CHECKPOINT, 'w:gz', compresslevel=1) as archive:
        for child in sorted(ROOT.iterdir()):
            archive.add(child, arcname=child.name, recursive=True)
    verified = {}
    with tarfile.open(CHECKPOINT, 'r:gz') as archive:
        for member in archive:
            if member.isdir():
                continue
            if not member.isfile() or member.name in verified:
                raise RuntimeError('Unexpected or duplicate checkpoint member')
            with archive.extractfile(member) as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            verified[member.name] = {'sha256': digest, 'bytes': member.size, 'mode': member.mode}
    if verified != before or inventory(ROOT) != before:
        raise RuntimeError('Checkpoint bytes or live workspace changed before removal')
    receipt['checkpoint'] = {'sha256': sha(CHECKPOINT), 'files': len(verified),
                             'bytes': CHECKPOINT.stat().st_size,
                             'all_member_bytes_and_modes_verified': True}
    save(SAVED / 'orchestration.json', receipt)
    print('Verified checkpoint:', len(verified), 'files;', CHECKPOINT.stat().st_size, 'compressed bytes', flush=True)

    removed = False
    tests_returncode = None
    try:
        safe_remove_owned(ROOT)
        removed = True
        for name, raw in changed_bytes.items():
            path = WORK / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        replay_start = time.monotonic()
        replay = replay_return(SOURCE, RETURNED, WORK, FRESH, runtime_closure=True)
        receipt['replay_elapsed_seconds'] = time.monotonic() - replay_start
        receipt['public_api_call'] = {
            'call': 'arcpuzzles.review_replay.replay_return',
            'source_zip': str(SOURCE), 'return_zip': str(RETURNED),
            'compare_work': str(WORK), 'out': str(FRESH), 'runtime_closure': True,
            'result_status': replay['status'],
        }
        for name in ('replay.json', 'extraction-manifest.json.gz'):
            shutil.copyfile(FRESH / name, SAVED / name)
        save(SAVED / 'orchestration.json', receipt)
        print('Official replay:', replay['status'], 'extracted', replay['extracted_files'], 'of', replay['original_files'], flush=True)

        # The official replay and its extraction inventory are complete. Release
        # only the disposable copy of the vendor archive to fit the verified
        # private runtime used for tests. This does not alter any source file.
        fresh_work = FRESH / 'checkout/WORK'
        archives = list((fresh_work / 'vendor').rglob('*.tar.gz'))
        if len(archives) != 1:
            raise RuntimeError(f'Expected exactly one disposable vendor archive, found {archives}')
        archive = archives[0]
        receipt['post_replay_space_release'] = {
            'path': str(archive), 'bytes': archive.stat().st_size, 'sha256': sha(archive),
            'timing': 'Only after official extraction, git application and changed-byte comparison succeeded',
        }
        archive.unlink()
        restore_checkpoint(prefix='private-runtime')
        runtime_expected = {k: v for k, v in before.items() if k.startswith('private-runtime/')}
        runtime_actual = {'private-runtime/' + k: v for k, v in inventory(ROOT / 'private-runtime').items()}
        assert runtime_actual == runtime_expected
        env = os.environ.copy()
        binary_root = SCRATCH / 'private-runtime-bin'
        env.update(PYTHONDONTWRITEBYTECODE='1',
                   PYTHONPATH=str(fresh_work / 'repo/src') + ':' + str(fresh_work / 'repo/shared/runtime'),
                   RACKET_PATH=str(binary_root / 'racket'),
                   PATH=str(binary_root) + os.pathsep + env['PATH'])
        argv = [sys.executable, '-B', '-m', 'unittest', 'discover', '-s',
                'generators/c4f6a0585dbf/tests', '-p', 'test_*.py', '-v']
        test_start = time.monotonic()
        process = subprocess.run(argv, cwd=fresh_work / 'repo', env=env,
                                 capture_output=True, text=True, timeout=120)
        tests_returncode = process.returncode
        (SAVED / 'unittest.stdout.txt').write_text(process.stdout)
        (SAVED / 'unittest.stderr.txt').write_text(process.stderr)
        test_receipt = {
            'command': argv, 'cwd': str(fresh_work / 'repo'),
            'exit_code': process.returncode, 'elapsed_seconds': time.monotonic() - test_start,
            'environment': {k: env[k] for k in ('PYTHONDONTWRITEBYTECODE','PYTHONPATH','RACKET_PATH')},
            'PATH_prefix': str(binary_root), 'patch_sha256': patch_hash,
            'source_sha256': {name: sha(fresh_work / name) for name in checked['patch_paths']},
            'stdout_path': 'checks/replay/unittest.stdout.txt',
            'stderr_path': 'checks/replay/unittest.stderr.txt',
            'scope': 'All three authored unittest files in the freshly patched runtime-closure checkout; real Racket; no full production battery.',
            'source_imports': 'Only fresh checkout src/shared/runtime added to PYTHONPATH; comparison tree contains changed files only.',
        }
        save(SAVED / 'unittest.json', test_receipt)
        receipt['status'] = 'passed' if process.returncode == 0 else 'fresh_tests_failed'
        receipt['fresh_tests_exit_code'] = process.returncode
        print('Fresh tests exit:', process.returncode, 'seconds:', test_receipt['elapsed_seconds'], flush=True)
        print(process.stderr[-500:], flush=True)
    except BaseException as exc:
        receipt['status'] = 'failed'
        receipt['error'] = f'{type(exc).__name__}: {exc}'
        (SAVED / 'failure.txt').write_text(traceback.format_exc())
        if (FRESH / 'replay.json').is_file():
            shutil.copyfile(FRESH / 'replay.json', SAVED / 'replay.json')
        raise
    finally:
        if removed:
            safe_remove_owned(FRESH)
            safe_remove_owned(ROOT)
            ROOT.mkdir()
            restore_checkpoint()
            if inventory(ROOT) != before:
                raise RuntimeError('Restored checkpoint differs from original verified workspace')
            receipt['workspace_restored_and_verified'] = True
        receipt['elapsed_seconds'] = time.monotonic() - started
        save(SAVED / 'orchestration.json', receipt)
        dest = WORK / 'checks/replay'
        dest.mkdir(exist_ok=True)
        for path in SAVED.iterdir():
            if path.is_file():
                shutil.copyfile(path, dest / path.name)
        shutil.copyfile(__file__, dest / 'checkpoint_replay.py')
        print('Workspace restored; evidence copied to', dest, flush=True)
    if tests_returncode:
        raise SystemExit(tests_returncode)


if __name__ == '__main__':
    main()
