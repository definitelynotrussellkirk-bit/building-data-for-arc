#!/usr/bin/env python3
"""Materialize and package an ARCpuzzles return with unchanged official tools.

Run under unshare --user --map-root-user --mount --fork. Before any mount this
wrapper additionally requires its own successful CLONE_NEWNS syscall and makes
mount propagation private. All 103k original files live only on a fresh tmpfs;
only the exact official output ZIP and a compact JSON build receipt leave it.
No shared/protected sources, assignment draws, contracts, or tools are modified.

Example (candidate and final builds must use distinct output directories):
  unshare --user --map-root-user --mount --fork python build_return_full.py \
    --zip upload/PACKET.zip --source-work arc_review/WORK \
    --mountpoint full_packet_mount --out-dir deliverables/candidate \
    --name review_response_review-58c6359b7db58ccc.zip

Use --probe with --mountpoint and --out-dir to test a tiny mount/write/unmount
without reading or extracting the packet. The namespace is transient, but the
empty mountpoint remains reusable. No output files or receipts are overwritten.
"""
from __future__ import annotations
import argparse
import ctypes
import gc
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import zipfile

sys.dont_write_bytecode = True

from support_sparse_packet import Packet, canonical, file_digest, no_symlinks, safe_name

CACHES = {'__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache'}
REQUIRED = ('ASSIGNMENT.json', 'REVIEW.md', 'DECISIONS.md', 'QUESTION_ANSWER.md',
            'FEEDBACK_TO_CODEX.md', 'RESULTS.json')
OPTIONAL = ('AUDIT_ASSIGNMENT.json', 'BLIND_ASSIGNMENT.json', 'AUDIT.md')


def clean_relative(relative):
    return not (set(relative.parts) & CACHES or relative.suffix in {'.pyc', '.pyo'})


def regular(path):
    no_symlinks(path)
    if not path.is_file() or not stat.S_ISREG(path.stat().st_mode):
        raise ValueError(f'Expected a regular file: {path}')


def iter_files(root, *, visible=False):
    if not root.exists():
        return
    no_symlinks(root)
    if not root.is_dir():
        raise ValueError(f'Expected a directory: {root}')
    for parent, dirs, files in os.walk(root, followlinks=False):
        parent = Path(parent)
        relative = parent.relative_to(root)
        for name in dirs + files:
            if (parent / name).is_symlink():
                raise ValueError(f'Symlink source: {parent / name}')
        dirs[:] = sorted(n for n in dirs if n not in CACHES and not (visible and n.startswith('.')))
        for name in sorted(files):
            path = parent / name
            relative = path.relative_to(root)
            if not clean_relative(relative) or visible and any(n.startswith('.') for n in relative.parts):
                continue
            regular(path)
            yield path


def run_record(argv, cwd, receipt, *, env=None):
    started = time.monotonic()
    process = subprocess.run([str(x) for x in argv], cwd=cwd, env=env,
                             text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    record = {'argv': [str(x) for x in argv], 'cwd': str(cwd),
              'exit_code': process.returncode, 'stdout': process.stdout,
              'stderr': process.stderr, 'elapsed_seconds': round(time.monotonic()-started, 3)}
    receipt['commands'].append(record)
    if process.returncode:
        raise RuntimeError(f'Command failed ({process.returncode}): {argv}\n{process.stderr}')
    return record


def prepare_source(packet, work):
    no_symlinks(work)
    regular(work / 'PACKET-MANIFEST.json')
    if file_digest(work / 'PACKET-MANIFEST.json') != packet.packet_id:
        raise ValueError('Working manifest differs from original ZIP')
    contract = json.loads((work / 'ASSIGNMENT.json').read_text())
    if contract.get('packet_id') != packet.packet_id:
        raise ValueError('Working assignment belongs to a different packet')
    task = contract['task_id']
    if task not in packet.manifest['generators']:
        raise ValueError('Unknown selected task')
    home = 'repo/generators/' + task + '/'
    baseline = contract['baseline_sha256']
    for relative, digest in baseline.items():
        safe_name(relative)
        if packet.manifest['files'].get(relative) != digest:
            raise ValueError(f'Baseline contract hash differs from original packet: {relative}')
        frozen = work / '.review/baseline' / relative
        regular(frozen)
        if file_digest(frozen) != digest:
            raise ValueError(f'Frozen baseline changed: {relative}')
    for name in REQUIRED:
        regular(work / name)
    # Refuse to hide edits to protected sources merely because this is sparse.
    checked = 0
    for path in iter_files(work / 'repo'):
        relative = path.relative_to(work).as_posix()
        if relative.startswith(home) or relative in baseline:
            continue
        expected = packet.manifest['files'].get(relative)
        if expected is None or file_digest(path) != expected:
            raise ValueError(f'Changed/undeclared protected working source: {relative}')
        checked += 1
    # Top-level scripts and issued documents must also remain original. Authored
    # reports are separate known inputs, not replacements for official tooling.
    for relative, digest in packet.manifest['files'].items():
        if '/' not in relative and (work / relative).exists():
            regular(work / relative)
            if file_digest(work / relative) != digest:
                raise ValueError(f'Changed official bootstrap file: {relative}')
    outer = work.parent
    for name in ('review.py', 'START-HERE.md'):
        regular(outer / name)
        if file_digest(outer / name) != packet.expected[name]:
            raise ValueError(f'Changed official outer entry file: {name}')
    return contract, checked


def overlay_sources(work, staged_work, contract):
    task = contract['task_id']
    sources = {}
    home = work / 'repo/generators' / task
    for path in iter_files(home):
        sources[path.relative_to(work).as_posix()] = path
    # Canonical/authority changes are copied only where the immutable baseline
    # binds them. The unchanged official builder enforces the permitted scope.
    for relative in contract['baseline_sha256']:
        path = work / relative
        regular(path)
        sources[relative] = path
        sources['.review/baseline/' + relative] = work / '.review/baseline' / relative
    for name in REQUIRED + OPTIONAL:
        if (work / name).exists():
            regular(work / name)
            sources[name] = work / name
    for directory, visible in (('checks', False), ('solve', True), ('solve-blind', True)):
        for path in iter_files(work / directory, visible=visible):
            sources[path.relative_to(work).as_posix()] = path
    for directory in ('solve-private', 'solve-private-blind'):
        path = work / '.review' / directory / 'generator.py'
        if path.exists():
            regular(path)
            sources[path.relative_to(work).as_posix()] = path
    # .review/test-venv, racket-runtime and private execution trees are never
    # traversed/copied. Only exact baseline files and generator snapshots above.
    inventory_hash = hashlib.sha256()
    copied_bytes = 0
    for relative, source in sorted(sources.items()):
        safe_name(relative)
        regular(source)
        if relative.startswith('repo/') and source.stat().st_mode & 0o111:
            raise ValueError(f'Executable selected source is forbidden: {relative}')
        before = (source.stat().st_size, source.stat().st_mtime_ns, file_digest(source))
        target = staged_work / relative
        no_symlinks(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(0o444 if relative.startswith('.review/baseline/') else 0o644)
        after = (source.stat().st_size, source.stat().st_mtime_ns, file_digest(source))
        actual = file_digest(target)
        if before != after or actual != before[2]:
            raise ValueError(f'Working source changed during copy: {relative}')
        inventory_hash.update(canonical({'path': relative, 'sha256': actual, 'bytes': before[0]}) + b'\n')
        copied_bytes += before[0]
    return {'copied_files': len(sources), 'copied_bytes': copied_bytes,
            'overlay_inventory_sha256': inventory_hash.hexdigest(),
            'excluded_private_trees': ['.review/test-venv', '.review/racket-runtime',
                                       '.review/solve-private/* except generator.py',
                                       '.review/solve-private-blind/* except generator.py']}


def exclusive_copy(source, destination):
    regular(source)
    no_symlinks(destination)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, prefix='.export-', delete=False) as outgoing:
            temporary = Path(outgoing.name)
            with source.open('rb') as incoming:
                shutil.copyfileobj(incoming, outgoing, 1024*1024)
            outgoing.flush()
            os.fsync(outgoing.fileno())
        if file_digest(source) != file_digest(temporary):
            raise ValueError('Exported output hash differs from official package')
        os.link(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--zip', type=Path)
    parser.add_argument('--source-work', type=Path)
    parser.add_argument('--mountpoint', type=Path, required=True)
    parser.add_argument('--out-dir', type=Path, required=True)
    parser.add_argument('--name', default='review_response_review-58c6359b7db58ccc.zip')
    parser.add_argument('--probe', action='store_true')
    parser.add_argument('--replay', action='store_true', help='official fresh runtime-closure replay inside tmpfs')
    parser.add_argument('--tests-json', type=Path, help='JSON list of Python-argument arrays; run in fresh replay via review.py run')
    parser.add_argument('--python', type=Path, default=Path(sys.executable), help='base interpreter for a fresh tmpfs venv')
    parser.add_argument('--pytest-spec', default='pytest>=8', help='pytest requirement installed only in private fresh venv')
    args = parser.parse_args(argv)
    test_commands = []
    if args.tests_json:
        regular(args.tests_json.absolute())
        test_commands = json.loads(args.tests_json.read_text())
        if (not isinstance(test_commands, list) or not test_commands or
                any(not isinstance(command, list) or not command or
                    any(not isinstance(arg, str) or not arg or '\0' in arg for arg in command)
                    for command in test_commands)):
            raise ValueError('--tests-json must contain a nonempty list of nonempty string argument arrays')
        args.replay = True
    if not args.probe and (args.zip is None or args.source_work is None):
        parser.error('--zip and --source-work are required except for --probe')
    safe_name(args.name)
    if '/' in args.name or not args.name.endswith('.zip'):
        parser.error('--name must be a single .zip filename')
    mountpoint, outdir = args.mountpoint.absolute(), args.out_dir.absolute()
    work = args.source_work.absolute() if args.source_work else None
    for path in (mountpoint, outdir):
        no_symlinks(path)
    if mountpoint == outdir or mountpoint in outdir.parents or outdir in mountpoint.parents:
        raise ValueError('Mountpoint and output directory must be disjoint')
    if work and (mountpoint == work or mountpoint in work.parents or work in mountpoint.parents):
        raise ValueError('Mountpoint must be separate from working review')
    if mountpoint.exists() and (not mountpoint.is_dir() or any(mountpoint.iterdir())):
        raise ValueError('Mountpoint must be a new or empty directory')
    outdir.mkdir(parents=True, exist_ok=True)
    receipt_path = outdir / (args.name + ('.probe.json' if args.probe else '.build.json'))
    final_zip = outdir / args.name
    # Reserve receipt exclusively BEFORE expensive work. A failure leaves a
    # reviewable failed receipt and cannot accidentally overwrite prior evidence.
    with receipt_path.open('x', encoding='utf-8') as receipt_stream:
        receipt = {'schema': 'arcpuzzles-private-full-build-v1', 'status': 'running',
                   'probe': args.probe, 'mountpoint': str(mountpoint), 'commands': [],
                   'official_tools_modified': False, 'full_verification_before_overlay': False,
                   'final_output': str(final_zip)}
        # Reserve physical receipt space before costly work so a later full
        # overlay cannot prevent recording a typical failure/verification log.
        initial = json.dumps(receipt, sort_keys=True, indent=2) + '\n'
        receipt_reservation = 4096 if args.probe else 262144
        receipt_stream.write(initial + ' ' * max(0, receipt_reservation - len(initial)))
        receipt_stream.flush()
        os.fsync(receipt_stream.fileno())
        mounted = False
        packet = None
        try:
            if final_zip.exists():
                raise FileExistsError(final_zip)
            if not args.probe:
                packet = Packet(args.zip)
                contract, checked = prepare_source(packet, work)
                receipt.update(packet_id=packet.packet_id, assignment_id=contract['assignment_id'],
                               task_id=contract['task_id'], protected_working_files_verified=checked,
                               source_zip_sha256=file_digest(args.zip))
            mountpoint.mkdir(parents=True, exist_ok=True)
            # Linux syscall success is authoritative. Some sandboxes expose a
            # synthetic /proc namespace view, so namespace inode comparison is
            # deliberately not used to decide whether mounts are isolated.
            libc = ctypes.CDLL(None, use_errno=True)
            if libc.unshare(0x00020000) != 0:  # CLONE_NEWNS
                error = ctypes.get_errno()
                raise OSError(error, 'Creating private mount namespace failed: ' + os.strerror(error))
            receipt['private_mount_namespace_created'] = True
            run_record(['mount', '--make-rprivate', '/'], Path.cwd(), receipt)
            options = 'size=1M,nr_inodes=32,mode=0700,nodev,nosuid' if args.probe else 'size=3G,nr_inodes=200000,mode=0700,nodev,nosuid'
            run_record(['mount', '-t', 'tmpfs', '-o', options, 'arc-review-private', mountpoint], Path.cwd(), receipt)
            mounted = True
            capacity = os.statvfs(mountpoint)
            receipt['tmpfs_capacity'] = {'available_bytes': capacity.f_bavail*capacity.f_frsize,
                                         'available_inodes': capacity.f_favail}
            if args.probe:
                probe = mountpoint / 'probe.txt'
                probe.write_text('private full-packet build probe\n')
                if probe.read_text() != 'private full-packet build probe\n':
                    raise ValueError('Probe write/read failed')
                receipt['probe_result'] = 'pass'
            else:
                selected = set(packet.expected)
                extraction = packet.extract(selected, mountpoint)
                receipt['full_extraction'] = {**packet.plan(selected), **extraction}
                packet.receipt(mountpoint / 'full-extraction.json.gz', selected, 'extract', extraction)
                packet.close()
                packet = None
                gc.collect()
                env = {key: value for key, value in os.environ.items() if key not in {'PYTHONPATH', 'PYTHONHOME'}}
                env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1')
                # This unchanged outer entrypoint hashes every original member
                # and both entry files before ANY authored overlay is installed.
                verify = run_record([sys.executable, mountpoint/'review.py', 'verify'], mountpoint, receipt, env=env)
                receipt['full_verification_before_overlay'] = verify['exit_code'] == 0
                receipt['overlay'] = overlay_sources(work, mountpoint/'WORK', contract)
                packaged = mountpoint / 'WORK' / args.name
                run_record([sys.executable, mountpoint/'review.py', 'package', '--bundle-evidence',
                            '--out', packaged], mountpoint, receipt, env=env)
                regular(packaged)
                receipt['official_zip_sha256'] = file_digest(packaged)
                receipt['official_zip_bytes'] = packaged.stat().st_size
                # Official package already calls validate_full_return. Check
                # ZIP CRC here as an independent transport-integrity gate.
                with zipfile.ZipFile(packaged) as archive:
                    bad = archive.testzip()
                    if bad:
                        raise ValueError(f'Official output ZIP CRC failure: {bad}')
                    receipt['official_zip_members'] = len(archive.infolist())
                if args.replay:
                    replay_root = mountpoint / 'fresh-replay'
                    # The installed controller is loaded from the unchanged
                    # full original tree; the source delta is applied by the
                    # official replay-return command, not by this wrapper.
                    replay_command = [sys.executable, '-m', 'arcpuzzles', '--library', mountpoint/'WORK/repo',
                        'review', 'replay-return', '--source-zip', args.zip.absolute(),
                        '--return-zip', packaged, '--compare-work', work, '--out', replay_root, '--runtime-closure']
                    replay_env = dict(env, PYTHONPATH=os.pathsep.join((str(mountpoint/'WORK/repo/src'),
                        str(mountpoint/'WORK/repo/shared/runtime'))), ARCPUZZLES_HOME=str(mountpoint/'WORK/repo'))
                    run_record(replay_command, mountpoint/'WORK/repo', receipt, env=replay_env)
                    replay_receipt = json.loads((replay_root/'replay.json').read_text())
                    if replay_receipt.get('status') != 'patch_replay_passed_tests_pending':
                        raise ValueError('Official replay did not reach a successful hash-comparison state')
                    receipt['fresh_replay'] = {'status': replay_receipt['status'],
                        'generator_sha256': replay_receipt['generator_sha256'],
                        'patch_sha256': replay_receipt['patch_sha256'],
                        'changed_files': replay_receipt['changed_files'],
                        'full_original_packet_extracted': replay_receipt['full_original_packet_extracted']}
                    fresh_root = replay_root / 'checkout'
                    if test_commands:
                        venv = mountpoint / 'fresh-test-venv'
                        temp = mountpoint / 'temporary'
                        temp.mkdir()
                        test_env = {key: value for key, value in env.items()
                                    if key not in {'PYTHONPATH', 'PYTHONHOME', 'VIRTUAL_ENV'}}
                        test_env.update(TMPDIR=str(temp), PIP_CACHE_DIR=str(mountpoint/'pip-cache'))
                        run_record([args.python.absolute(), '-m', 'venv', '--system-site-packages', venv],
                                   mountpoint, receipt, env=test_env)
                        fresh_python = venv / 'bin/python'
                        run_record([fresh_python, '-m', 'pip', 'install', '--no-cache-dir', args.pytest_spec],
                                   mountpoint, receipt, env=test_env)
                        package_probe = ['-c', 'import sys,pytest,numpy,PIL; print(sys.executable); '
                            'print("pytest",pytest.__version__,pytest.__file__); '
                            'print("numpy",numpy.__version__,numpy.__file__); '
                            'print("Pillow",PIL.__version__,PIL.__file__)']
                        run_record([fresh_python, *package_probe], mountpoint, receipt, env=test_env)
                        for index, command in enumerate(test_commands, 1):
                            record = run_record([fresh_python, fresh_root/'review.py', 'run',
                                fresh_python, *command], fresh_root, receipt, env=test_env)
                            log = outdir / f'{args.name}.fresh-test-{index:02d}.log'
                            with log.open('x', encoding='utf-8') as stream:
                                stream.write(record['stdout'])
                                stream.write('\nSTDERR:\n' + record['stderr'])
                            receipt.setdefault('fresh_test_logs', []).append(
                                {'path': str(log), 'sha256': file_digest(log), 'argv': command,
                                 'exit_code': record['exit_code']})
                        receipt['fresh_tests_passed'] = True
                    for source, suffix in ((replay_root/'replay.json', '.replay.json'),
                            (replay_root/'extraction-manifest.json.gz', '.replay-extraction.json.gz')):
                        exported = outdir / (args.name + suffix)
                        exclusive_copy(source, exported)
                        receipt.setdefault('replay_exports', []).append(
                            {'path': str(exported), 'sha256': file_digest(exported)})
                # Export exact official bytes only after requested replay/tests
                # have passed. Candidate and final builds use distinct outdirs.
                exclusive_copy(packaged, final_zip)
                receipt['exported_zip_sha256'] = file_digest(final_zip)
            receipt['status'] = 'passed'
        except BaseException as error:
            receipt['status'] = 'failed'
            receipt['error'] = f'{type(error).__name__}: {error}'
            raise
        finally:
            if packet:
                packet.close()
            if mounted:
                try:
                    run_record(['umount', mountpoint], Path.cwd(), receipt)
                    receipt['tmpfs_unmounted'] = True
                except BaseException as error:
                    receipt['status'] = 'failed'
                    receipt['unmount_error'] = f'{type(error).__name__}: {error}'
                    # Exiting this private namespace releases its mounts even
                    # if explicit cleanup failed; never force unmount a host path.
            receipt['mountpoint_empty_after_unmount'] = not any(mountpoint.iterdir()) if mountpoint.exists() and receipt.get('tmpfs_unmounted') else None
            receipt_stream.seek(0)
            receipt_stream.write(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
            receipt_stream.truncate()
            receipt_stream.flush()
            os.fsync(receipt_stream.fileno())
        if receipt['status'] != 'passed':
            raise RuntimeError('Private build cleanup failed; inspect receipt')
    print(json.dumps({'status': 'passed', 'receipt': str(receipt_path),
                      'zip': str(final_zip) if not args.probe else None}, sort_keys=True))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f'ERROR: {type(error).__name__}: {error}', file=sys.stderr)
        raise SystemExit(2)
