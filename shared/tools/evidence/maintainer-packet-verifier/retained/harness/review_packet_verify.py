"""Reproducible, scoped owner verification of a self-contained review ZIP."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import sys
import tempfile
import tomllib
import zipfile

from .review_full_packet import canonical_json, RACKET_ARCHIVE_NAME, RACKET_ARCHIVE_SHA256
from .review_replay import _no_symlinks, _safe_name
from .review_packet_verify_process import run_command


def _sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f, 'sha256').hexdigest()


def inspect_packet(path: Path, *, expected_sha256: str | None = None) -> dict:
    """Check every archive member without extracting or running packet code."""
    path = Path(path).absolute();_no_symlinks(path)
    digest = _sha(path)
    if expected_sha256 is not None and (not re.fullmatch('[0-9a-f]{64}', expected_sha256)
                                       or digest != expected_sha256):
        raise ValueError('Packet SHA-256 differs from the requested artifact')
    with zipfile.ZipFile(path) as archive:
        files = {};seen = set()
        for info in archive.infolist():
            _safe_name(info.filename);key = info.filename.rstrip('/')
            kind = stat.S_IFMT(info.external_attr >> 16)
            if key in seen or kind not in {0, stat.S_IFREG, stat.S_IFDIR} or info.flag_bits & 1:
                raise ValueError('Duplicate, encrypted or nonregular packet member: ' + info.filename)
            seen.add(key)
            if not info.is_dir():
                if kind == stat.S_IFDIR:raise ValueError('Nonregular packet member: ' + info.filename)
                files[info.filename] = info
        name = 'WORK/PACKET-MANIFEST.json'
        if name not in files:raise ValueError('Cold verification requires the current WORK workspace layout')
        raw = archive.read(name);manifest = json.loads(raw)
        if (not isinstance(manifest, dict) or manifest.get('schema') != 'arcpuzzles-full-packet-v2'
                or raw != canonical_json(manifest) or manifest.get('layout', {}).get('workspace') != 'WORK'
                or set(manifest.get('layout', {}).get('entry_files', {})) != {'review.py', 'START-HERE.md'}
                or not isinstance(manifest.get('files'), dict)):
            raise ValueError('Invalid canonical workspace packet manifest')
        expected = {'WORK/' + n: h for n, h in manifest['files'].items()}
        expected.update(manifest['layout']['entry_files']);expected[name] = hashlib.sha256(raw).hexdigest()
        if set(files) != set(expected):raise ValueError('Packet inventory differs from its manifest')
        for name, wanted in expected.items():
            if not isinstance(wanted, str) or not re.fullmatch('[0-9a-f]{64}', wanted):
                raise ValueError('Invalid packet member SHA-256: ' + name)
            if any(str(parent) in files for parent in Path(name).parents if str(parent) != '.'):
                raise ValueError('File/parent collision in packet: ' + name)
            with archive.open(name) as f:actual = hashlib.file_digest(f, 'sha256').hexdigest()
            if actual != wanted:raise ValueError('Packet member hash differs: ' + name)
    if _sha(path) != digest:raise ValueError('Packet changed while its inventory was checked')
    return {'manifest': manifest, 'packet_id': hashlib.sha256(raw).hexdigest(),
            'zip_sha256': digest, 'member_count': len(files), 'expected': expected}


def _compare_owner(owner, manifest):
    from .review_full_packet import _source_files
    owner = Path(owner).resolve()
    files = _source_files(owner, owner / 'REVIEW', selection=manifest.get('selection'))
    name = 'vendor/' + RACKET_ARCHIVE_NAME
    if name in manifest['files']:files[name] = owner / 'var/review' / RACKET_ARCHIVE_NAME
    from .review_nvarc import ARCHIVE_PATH
    if ARCHIVE_PATH in manifest['files']:files[ARCHIVE_PATH] = owner / 'var/review/ticket-data/NVARC-CHECK-001.zip'
    actual = {name: _sha(path) for name, path in files.items()}
    expected = manifest['files']
    changed = sorted(name for name in set(actual) | set(expected) if actual.get(name) != expected.get(name))
    if changed:raise ValueError('Owner source differs from frozen packet: ' + ', '.join(changed[:12]))
    return {'status': 'passed', 'logical_files': len(files), 'scope': 'Frozen selection only; no generator tests.'}


def _save_receipt(out, receipt):
    pending = out / '.verification.json.tmp'
    pending.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    pending.replace(out / 'verification.json')


def _finish_verification(cold, out, receipt, *, keep_checkout, cold_identity):
    """Publication follows retained evidence; any copy failure keeps scratch."""
    try:
        for name in ['probe-progress.json', 'probe-result.json']:
            if (cold / name).is_file():shutil.copy2(cold / name, out / name)
        if (cold / 'logs').is_dir():shutil.copytree(cold / 'logs', out / 'logs/probe', dirs_exist_ok=True)
        if 'cold_probe' in receipt:
            for command in receipt['cold_probe']['commands']:
                for stream in ('stdout', 'stderr'):
                    asset = command[stream];asset['original_path'] = asset['path']
                    asset['path'] = str(out / 'logs/probe' / Path(asset['path']).name)
        artifacts = cold / 'checkout/WORK/checks/packet-verification'
        if artifacts.is_dir():shutil.copytree(artifacts, out / 'artifacts', dirs_exist_ok=True)
        if receipt['status'] == 'checks_passed':
            if not keep_checkout:
                current = cold.stat()
                if cold.is_symlink() or (current.st_dev, current.st_ino) != cold_identity:
                    raise RuntimeError('Verifier cold root changed; refusing cleanup')
                shutil.rmtree(cold);receipt['cold_root_retained'] = False
            receipt['status'] = 'passed'
    except BaseException as exc:
        receipt.update(status='failed', retention_error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        _save_receipt(out, receipt)


def verify_packet(packet: Path, out: Path, *, task_id: str, seed: int = 17,
                  demos: int = 3, queries: int = 4, timeout: float = 180,
                  expected_sha256: str | None = None, owner_root: Path | None = None,
                  accepted_family: str | None = None, allow_unapproved: bool = False,
                  keep_checkout: bool = False, python: Path | None = None) -> dict:
    """Exercise one explicit task, retaining exact receipts and no admission change.

    This Linux x86_64 owner command creates its own /tmp checkout and venv,
    installs only the packet's declared runtime dependencies, and uses bundled
    Racket. The output directory must be new. Failed scratch is always retained;
    successful scratch is removed unless keep_checkout is requested.
    """
    out = Path(out).absolute();_no_symlinks(out)
    if out.exists():raise FileExistsError('Verification output must be new: ' + str(out))
    if (type(seed) is not int or type(demos) is not int or not 1 <= demos <= 16
            or type(queries) is not int or not 1 <= queries <= 16
            or type(timeout) not in {int, float} or not math.isfinite(timeout) or timeout <= 0):
        raise ValueError('Exact integer counts 1..16, integer seed and finite positive timeout are required')
    if platform.system() != 'Linux' or platform.machine() not in {'x86_64', 'AMD64'}:
        raise ValueError('Cold verification requires Linux x86_64 with Landlock ABI>=2')
    packet = Path(packet).absolute();checked = inspect_packet(packet, expected_sha256=expected_sha256)
    manifest = checked['manifest'];row = manifest.get('generators', {}).get(task_id)
    if row is None or task_id not in manifest.get('main_ids', []):
        raise ValueError('Choose a main target included in this exact packet')
    if not row.get('approved') and not allow_unapproved:
        raise ValueError('Selected target needs explicit --allow-unapproved research opt-in')
    if accepted_family is not None and accepted_family not in manifest['generators']:
        raise ValueError('Accepted-family probe target is absent from this packet')
    if manifest['files'].get('vendor/' + RACKET_ARCHIVE_NAME) != RACKET_ARCHIVE_SHA256:
        raise ValueError('Cold verification requires the pinned bundled Racket archive')
    interpreter = Path(python or sys.executable).resolve(strict=True)
    out.mkdir(parents=True, exist_ok=False);(out / 'logs').mkdir();(out / 'harness').mkdir()
    cold = Path(tempfile.mkdtemp(prefix='arcpuzzles-cold-', dir='/tmp'))
    created = cold.stat();cold_identity = (created.st_dev, created.st_ino)
    receipt = {'schema': 'arcpuzzles-review-packet-verification-v1', 'status': 'running',
        'packet_id': checked['packet_id'], 'packet': {'path': str(packet), 'sha256': checked['zip_sha256']},
        'archive_members_verified': checked['member_count'], 'cold_root': str(cold),
        'cold_root_retained': True, 'task_id': task_id, 'seed': seed, 'demos': demos, 'queries': queries,
        'commands': [], 'harness': [], 'owner_sources': None, 'training_admitted': False,
        'scope': 'One explicit task and optional accepted-family export; no corpus battery, semantic uniqueness or admission.'}
    def save():
        _save_receipt(out, receipt)
    def run(name, argv, env):
        print('Cold packet verification: ' + name, file=sys.stderr, flush=True)
        result = run_command(argv, cwd=cold, env=env, timeout=timeout if name != 'probe' else timeout * 12,
                             log_root=out / 'logs', name=name)
        receipt['commands'].append(result);save()
        if result['exit_code'] != 0 or result['failure']:
            raise RuntimeError('Verification command failed: ' + name + '; receipts: ' + str(out))
    save()
    try:
        if owner_root is not None:receipt['owner_sources'] = _compare_owner(owner_root, manifest);save()
        checkout = cold / 'checkout';checkout.mkdir()
        with zipfile.ZipFile(packet) as archive:
            for name, wanted in checked['expected'].items():
                target = checkout / name;target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(name) as source, target.open('xb') as dest:shutil.copyfileobj(source, dest)
                if _sha(target) != wanted:raise ValueError('Extracted packet member changed: ' + name)
                target.chmod(0o644 | ((archive.getinfo(name).external_attr >> 16) & 0o111))
        for name in ['review_packet_verify.py', 'review_packet_verify_probe.py',
                     'review_packet_verify_process.py', 'review_packet_verify_landlock.py']:
            raw = Path(__file__).with_name(name).read_bytes()
            (out / 'harness' / name).write_bytes(raw)
            if name != 'review_packet_verify.py':(cold / name).write_bytes(raw)
            receipt['harness'].append({'path': 'harness/' + name, 'sha256': hashlib.sha256(raw).hexdigest()})
        for name in ['.home', 'tmp', 'logs']:(cold / name).mkdir()
        probe = out / 'owner-read-probe.txt';probe.write_text('This owner-side file must not be readable by the cold process.\n')
        env = {'PATH': os.defpath, 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8', 'HOME': str(cold / '.home'),
               'TMPDIR': str(cold / 'tmp'), 'PYTHONNOUSERSITE': '1', 'PYTHONDONTWRITEBYTECODE': '1',
               'PIP_DISABLE_PIP_VERSION_CHECK': '1'}
        run('venv', [str(interpreter), '-I', '-m', 'venv', str(cold / 'venv')], env)
        binary = cold / 'venv/bin/python'
        project = tomllib.loads((checkout / 'WORK/repo/pyproject.toml').read_text())
        dependencies = project['project']['optional-dependencies']['runtime']
        if not isinstance(dependencies, list) or not dependencies or any(not isinstance(d, str) for d in dependencies):
            raise ValueError('Packet must declare its runtime dependencies')
        receipt['runtime_dependencies'] = dependencies;save()
        run('dependencies', [str(binary), '-I', '-m', 'pip', 'install', '--no-cache-dir', *dependencies], env)
        run('installed-versions', [str(binary), '-I', '-m', 'pip', 'freeze', '--all'], env)
        config = {'packet_id': checked['packet_id'], 'task_id': task_id, 'seed': seed,
                  'demos': demos, 'queries': queries, 'timeout': timeout,
                  'allow_unapproved': allow_unapproved, 'accepted_family': accepted_family}
        (cold / 'config.json').write_text(json.dumps(config))
        run('probe', [str(binary), '-I', str(cold / 'review_packet_verify_landlock.py'), str(cold), str(probe),
                      str(binary), '-I', str(cold / 'review_packet_verify_probe.py'), str(cold / 'config.json')], env)
        result = json.loads((cold / 'probe-result.json').read_text())
        if result['status'] != 'passed' or result['packet_id'] != checked['packet_id']:
            raise ValueError('Cold probe did not finish with the bound packet identity')
        if 'owner_read_denied' not in (out / 'logs/probe.stdout').read_text():
            raise ValueError('The owner read-denial proof is missing')
        if _sha(packet) != checked['zip_sha256']:raise ValueError('Packet changed during verification')
        if owner_root is not None:receipt['owner_sources'] = _compare_owner(owner_root, manifest)
        receipt.update(status='checks_passed', cold_probe=result)
        save()
    except BaseException as exc:
        receipt.update(status='failed', error=f'{type(exc).__name__}: {exc}');save();raise
    finally:
        _finish_verification(cold, out, receipt, keep_checkout=keep_checkout, cold_identity=cold_identity)
    return receipt
