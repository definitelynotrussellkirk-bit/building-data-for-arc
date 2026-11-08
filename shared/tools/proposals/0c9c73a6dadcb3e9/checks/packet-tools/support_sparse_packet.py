#!/usr/bin/env python3
"""Safely inspect and hydrate a full ARCpuzzles packet on inode-limited hosts.

This is an external storage helper, not a replacement for official review tools.
It never draws assignments, changes seeds/contracts/manifests, executes packet
sources, or displays task contents. Official review.py verify and package still
require all original repository paths to exist; a sparse receipt is not an
exception to either requirement. Finish the blind solve before reading task
sources, as required by the packet's duties.

Commands (all paths are explicit; destination means the directory above WORK):
  python support_sparse_packet.py verify --zip PACKET.zip --receipt verified.json.gz
  python support_sparse_packet.py plan --zip PACKET.zip --bootstrap
  python support_sparse_packet.py extract --zip PACKET.zip --dest checkout --bootstrap --receipt bootstrap.json.gz
  python support_sparse_packet.py extract --zip PACKET.zip --dest checkout --task TASK_ID --receipt task.json.gz
  python support_sparse_packet.py extract --zip PACKET.zip --dest checkout --contract checkout/WORK/ASSIGNMENT.json --receipt assignment.json.gz
  python support_sparse_packet.py extract --zip PACKET.zip --dest checkout --member WORK/path --receipt member.json.gz
  python support_sparse_packet.py extract --zip PACKET.zip --dest checkout --all --receipt full.json.gz
  python support_sparse_packet.py self-test

Task closure follows official review_replay._runtime_members and runtime.py:
include task/rule identity homes, declared common runtime mappings, bound base
solution authorities, controller/catalog/vendor and top-level bootstrap files.
Multiple --task / --contract / --member arguments are accepted. Existing regular
files are retained even if edited. Symlinks and nonregular paths are rejected.
Receipts contain all omitted archive paths and their issued hashes in one gzip
file, so no per-omitted-file inode is consumed. verify reads every member in
bounded chunks, checking ZIP CRC and canonical manifest SHA-256 bindings.

Sparse first-draw caveat: official draw_main verifies selected baseline sources
BEFORE journaling its seed. On an incomplete checkout, preserve one random seed
outside WORK before asking official main_selection_for_seed for the task, then
hydrate that exact task's closure and call official draw_main(WORK, seed=seed).
Do not call review.py start repeatedly on missing-source failures; that can draw
again. This helper intentionally has no seed selection/draw implementation.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile
import unittest
import zipfile

CHUNK = 1024 * 1024
MANIFEST = 'WORK/PACKET-MANIFEST.json'
SCHEMA = 'arcpuzzles-full-packet-v2'


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


def safe_name(name):
    if (not isinstance(name, str) or not name or '\\' in name or ':' in name or '\0' in name
            or PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts
            or str(PurePosixPath(name)) != name.rstrip('/')):
        raise ValueError(f'Unsafe archive path: {name!r}')


def digest_stream(stream):
    digest = hashlib.sha256()
    for chunk in iter(lambda: stream.read(CHUNK), b''):
        digest.update(chunk)
    return digest.hexdigest()


def file_digest(path):
    with Path(path).open('rb') as stream:
        return digest_stream(stream)


def no_symlinks(path):
    # Do not resolve first: resolve would hide a caller-provided symlink.
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError(f'Symlink path or ancestor: {part}')


class Packet:
    def __init__(self, path):
        self.path = Path(path).absolute()
        self.archive = zipfile.ZipFile(self.path)
        try:
            self.files = {}
            names = set()
            for info in self.archive.infolist():
                safe_name(info.filename)
                if info.filename in names:
                    raise ValueError(f'Duplicate archive member: {info.filename}')
                names.add(info.filename)
                mode = info.external_attr >> 16
                kind = stat.S_IFMT(mode)
                if info.is_dir():
                    if kind not in (0, stat.S_IFDIR):
                        raise ValueError(f'Non-directory archive member: {info.filename}')
                    continue
                if kind not in (0, stat.S_IFREG) or info.flag_bits & 1:
                    raise ValueError(f'Nonregular or encrypted archive member: {info.filename}')
                self.files[info.filename] = info
            raw = self.archive.read(MANIFEST)
            self.manifest = json.loads(raw)
            self.packet_id = hashlib.sha256(raw).hexdigest()
            if canonical(self.manifest) != raw or self.manifest.get('schema') != SCHEMA:
                raise ValueError('Noncanonical or unsupported packet manifest')
            layout = self.manifest.get('layout', {})
            entries = layout.get('entry_files', {})
            if layout.get('workspace') != 'WORK' or set(entries) != {'START-HERE.md', 'review.py'}:
                raise ValueError('Unsupported packet layout or entry inventory')
            self.expected = {'WORK/' + n: d for n, d in self.manifest['files'].items()}
            self.expected.update(entries)
            self.expected[MANIFEST] = self.packet_id
            for name, digest in self.expected.items():
                safe_name(name)
                if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
                    raise ValueError(f'Invalid SHA-256 binding: {name}')
            if set(self.files) != set(self.expected):
                missing = sorted(set(self.expected) - set(self.files))[:5]
                extra = sorted(set(self.files) - set(self.expected))[:5]
                raise ValueError(f'Archive inventory differs from manifest; missing={missing}, extra={extra}')
            if self.manifest.get('canonical_sha256') != self.expected.get('WORK/repo/shared/data/canonical/puzzles.jsonl'):
                raise ValueError('Canonical ledger hash binding differs from manifest files')
            for name in entries:
                self.read_checked(name)
        except BaseException:
            self.archive.close()
            raise

    def close(self):
        self.archive.close()

    def read_checked(self, name):
        raw = self.archive.read(name)
        if hashlib.sha256(raw).hexdigest() != self.expected[name]:
            raise ValueError(f'Original manifest mismatch: {name}')
        return raw

    def verify(self):
        size = 0
        for name in sorted(self.expected):
            with self.archive.open(name) as stream:
                digest = digest_stream(stream)
            if digest != self.expected[name]:
                raise ValueError(f'Original manifest mismatch: {name}')
            size += self.files[name].file_size
        return {'verified_files': len(self.expected), 'verified_uncompressed_bytes': size,
                'source_zip_sha256': file_digest(self.path)}

    def bootstrap(self):
        roots = {'WORK/repo/' + n for n in ('AGENTS.md', 'README.md', 'pyproject.toml', 'setup.py', 'requirements.txt')}
        return {name for name in self.expected
                if name in roots or not name.startswith('WORK/')
                or '/' not in name.removeprefix('WORK/')
                or name.startswith(('WORK/repo/src/arcpuzzles/', 'WORK/repo/catalog/', 'WORK/vendor/'))}

    def select(self, tasks=(), members=(), bootstrap=False, all_members=False):
        selected = set(self.expected) if all_members else (self.bootstrap() if bootstrap or tasks else set())
        mapping = authorities = None
        if tasks:
            mapping = json.loads(self.read_checked('WORK/repo/catalog/runtime_files.json'))
            authorities = json.loads(self.read_checked('WORK/repo/catalog/authority_files.json'))
        for task in tasks:
            if task not in self.manifest['generators']:
                raise ValueError(f'Unknown task id: {task}')
            row = self.manifest['generators'][task]
            identities = {task, row.get('rule_task_id') or task}
            for item in mapping:
                relative, target = item['path'], item['target']
                safe_name(relative)
                safe_name(target)
                if relative.startswith('generators/') and PurePosixPath(relative).parts[1] not in identities:
                    continue
                if target.startswith('data/base/solutions/') and authorities.get(target) not in identities:
                    continue
                selected.add('WORK/repo/' + relative)
            for identity in identities:
                selected.update(n for n in self.expected if n.startswith(f'WORK/repo/generators/{identity}/'))
        for member in members:
            safe_name(member)
            if member.endswith('/'):
                matched = {n for n in self.expected if n.startswith(member)}
                if not matched:
                    raise ValueError(f'No archive files under prefix: {member}')
                selected.update(matched)
            else:
                selected.add(member)
        if not selected:
            raise ValueError('Select --bootstrap, --task, --contract, --member, or --all')
        if missing := selected - self.expected.keys():
            raise ValueError(f'Missing declared sources: {sorted(missing)}')
        return selected

    def contract_tasks(self, path):
        value = json.loads(Path(path).read_text())
        if value.get('packet_id') != self.packet_id:
            raise ValueError('Contract belongs to a different packet')
        tasks = [value['task_id']] if 'task_id' in value else [row['task_id'] for row in value.get('targets', [])]
        if not tasks:
            raise ValueError('Contract contains no task ids')
        return tasks

    def plan(self, selected):
        return {'selected_files': len(selected), 'omitted_files': len(self.expected) - len(selected),
                'selected_uncompressed_bytes': sum(self.files[n].file_size for n in selected)}

    def extract(self, selected, destination):
        dest = Path(destination).absolute()
        no_symlinks(dest)
        if dest.exists() and not dest.is_dir():
            raise ValueError(f'Destination is not a directory: {dest}')
        existing = {}
        # Preflight every target before mutation; existing reviewer edits are retained.
        for name in sorted(selected):
            target = dest / name
            no_symlinks(target)
            if target.exists():
                if not target.is_file():
                    raise ValueError(f'Nonregular destination: {target}')
                existing[name] = file_digest(target)
            for parent in target.parents:
                if parent.exists() and not parent.is_dir():
                    raise ValueError(f'Nondirectory destination ancestor: {parent}')
        created = []
        for name in sorted(selected - existing.keys()):
            target = dest / name
            target.parent.mkdir(parents=True, exist_ok=True)
            no_symlinks(target)
            temp = None
            try:
                with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.hydrate-', delete=False) as out:
                    temp = Path(out.name)
                    digest = hashlib.sha256()
                    with self.archive.open(name) as stream:
                        for chunk in iter(lambda: stream.read(CHUNK), b''):
                            digest.update(chunk)
                            out.write(chunk)
                    out.flush()
                    os.fsync(out.fileno())
                if digest.hexdigest() != self.expected[name]:
                    raise ValueError(f'Original manifest mismatch: {name}')
                temp.chmod(0o644)
                # Atomic exclusive installation: unlike replace(), cannot overwrite edits.
                os.link(temp, target)
                created.append(name)
            finally:
                if temp is not None:
                    temp.unlink(missing_ok=True)
        return {'created_files': len(created), 'retained_original_files': sum(existing[n] == self.expected[n] for n in existing),
                'retained_edited_files': {n: d for n, d in existing.items() if d != self.expected[n]},
                'destination': str(dest)}

    def receipt(self, path, selected, action, result):
        value = {'schema': 'arcpuzzles-sparse-storage-receipt-v1', 'action': action,
                 'packet_id': self.packet_id, 'source_zip': str(self.path),
                 'official_full_workspace_validation_required': True,
                 'entire_archive_content_verified': action == 'verify',
                 'selection': self.plan(selected), 'result': result,
                 'selected_sha256': {n: self.expected[n] for n in sorted(selected)},
                 'omitted_sha256': {n: self.expected[n] for n in sorted(self.expected.keys() - selected)}}
        target = Path(path).absolute()
        no_symlinks(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise FileExistsError(f'Receipt already exists; choose a new path: {target}')
        raw = canonical(value)
        with target.open('xb') as stream:
            with gzip.GzipFile(fileobj=stream, mode='wb', filename='', mtime=0) as compressed:
                compressed.write(raw)
        return {'receipt': str(target), 'receipt_sha256': file_digest(target)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command', choices=['verify', 'plan', 'extract', 'self-test'])
    parser.add_argument('--zip', type=Path)
    parser.add_argument('--dest', type=Path)
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--bootstrap', action='store_true')
    parser.add_argument('--all', dest='all_members', action='store_true')
    parser.add_argument('--task', action='append', default=[])
    parser.add_argument('--contract', type=Path, action='append', default=[])
    parser.add_argument('--member', action='append', default=[])
    args = parser.parse_args(argv)
    if args.command == 'self-test':
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(SparseTests)
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    if args.zip is None:
        parser.error('--zip is required')
    if args.command == 'extract' and (args.dest is None or args.receipt is None):
        parser.error('--dest and --receipt are required for extract')
    if args.receipt:
        receipt_path = args.receipt.absolute()
        no_symlinks(receipt_path)
        if receipt_path.exists():
            raise FileExistsError(f'Receipt already exists; choose a new path: {receipt_path}')
        if args.dest and (args.dest.absolute() / 'WORK/repo') in receipt_path.parents:
            raise ValueError('Write storage receipts outside WORK/repo')
    packet = Packet(args.zip)
    try:
        tasks = list(args.task)
        for path in args.contract:
            tasks.extend(packet.contract_tasks(path))
        selected = packet.select(tasks, args.member, args.bootstrap, args.all_members) if args.command != 'verify' else set(packet.expected)
        if args.command == 'extract' and args.receipt:
            destination = args.dest.absolute()
            receipt_path = args.receipt.absolute()
            if receipt_path == destination or any(receipt_path == destination / name
                    or receipt_path in (destination / name).parents for name in selected):
                raise ValueError('Receipt must not replace or contain an extracted packet path')
        result = packet.plan(selected)
        if args.command == 'verify':
            result.update(packet.verify())
        elif args.command == 'extract':
            if args.dest is None:
                parser.error('--dest is required for extract')
            result.update(packet.extract(selected, args.dest))
        if args.receipt:
            # Receipts must remain outside WORK/repo: official packaging rejects
            # undeclared new shared sources and cannot treat receipts as originals.
            if args.dest and (Path(args.dest).absolute() / 'WORK/repo') in Path(args.receipt).absolute().parents:
                raise ValueError('Write storage receipts outside WORK/repo')
            result.update(packet.receipt(args.receipt, selected, args.command, result.copy()))
        print(json.dumps({'packet_id': packet.packet_id, 'action': args.command, **result}, sort_keys=True, indent=2))
        return 0
    finally:
        packet.close()


class SparseTests(unittest.TestCase):
    def fixture(self, directory, change=None, extra=None):
        payload = {'START-HERE.md': b'entry', 'review.py': b'entry2',
                   'WORK/repo/shared/data/canonical/puzzles.jsonl': b'ledger',
                   'WORK/README.md': b'docs', 'WORK/repo/src/arcpuzzles/controller.py': b'controller',
                   'WORK/repo/generators/task/generator.py': b'original',
                   'WORK/repo/generators/task/tests/test_a.py': b'test',
                   'WORK/repo/generators/other/generator.py': b'other',
                   'WORK/repo/shared/helper.py': b'helper',
                   'WORK/repo/shared/base.rkt': b'authority'}
        mapping = [{'path': 'shared/helper.py', 'target': 'scripts/helper.py'},
                   {'path': 'shared/data/canonical/puzzles.jsonl', 'target': 'data/canonical/puzzles.jsonl'},
                   {'path': 'generators/task/generator.py', 'target': 'generators/task/generator.py'},
                   {'path': 'generators/other/generator.py', 'target': 'generators/other/generator.py'},
                   {'path': 'shared/base.rkt', 'target': 'data/base/solutions/task.rkt'}]
        payload['WORK/repo/catalog/runtime_files.json'] = canonical(mapping)
        payload['WORK/repo/catalog/authority_files.json'] = canonical({'data/base/solutions/task.rkt': 'task'})
        sha = lambda b: hashlib.sha256(b).hexdigest()
        manifest = {'schema': SCHEMA, 'layout': {'workspace': 'WORK', 'entry_files': {n: sha(payload[n]) for n in ('START-HERE.md', 'review.py')}},
                    'files': {n[5:]: sha(b) for n, b in payload.items() if n.startswith('WORK/')},
                    'generators': {'task': {'rule_task_id': 'task'}, 'other': {'rule_task_id': 'other'}},
                    'canonical_sha256': sha(b'ledger')}
        payload[MANIFEST] = canonical(manifest)
        if change:
            payload[change] = b'corrupted'
        path = Path(directory) / 'packet.zip'
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as archive:
            for n, b in payload.items():
                archive.writestr(n, b)
            if extra:
                archive.writestr(extra, b'x')
        return path

    def test_full_verification_and_exact_closure(self):
        with tempfile.TemporaryDirectory() as d:
            packet = Packet(self.fixture(d))
            try:
                self.assertEqual(packet.verify()['verified_files'], len(packet.expected))
                selected = packet.select(['task'])
                self.assertIn('WORK/repo/shared/base.rkt', selected)
                self.assertIn('WORK/repo/generators/task/tests/test_a.py', selected)
                self.assertNotIn('WORK/repo/generators/other/generator.py', selected)
                dest = Path(d) / 'out'
                first = packet.extract(selected, dest)
                self.assertEqual(first['created_files'], len(selected))
                edited = dest / 'WORK/repo/generators/task/generator.py'
                edited.write_bytes(b'EDIT')
                second = packet.extract(selected, dest)
                self.assertEqual(second['created_files'], 0)
                self.assertEqual(edited.read_bytes(), b'EDIT')
                self.assertIn('WORK/repo/generators/task/generator.py', second['retained_edited_files'])
                receipt = Path(d) / 'receipt.gz'
                packet.receipt(receipt, selected, 'extract', second)
                with gzip.open(receipt, 'rt') as stream:
                    value = json.load(stream)
                self.assertEqual(set(value['selected_sha256']) | set(value['omitted_sha256']), set(packet.expected))
            finally:
                packet.close()

    def test_corrupt_content_is_detected_without_bad_installation(self):
        with tempfile.TemporaryDirectory() as d:
            packet = Packet(self.fixture(d, change='WORK/repo/shared/helper.py'))
            try:
                with self.assertRaisesRegex(ValueError, 'manifest mismatch'):
                    packet.verify()
                dest = Path(d) / 'out'
                with self.assertRaisesRegex(ValueError, 'manifest mismatch'):
                    packet.extract({'WORK/repo/shared/helper.py'}, dest)
                self.assertFalse((dest / 'WORK/repo/shared/helper.py').exists())
                self.assertEqual(list((dest / 'WORK/repo/shared').iterdir()), [])
            finally:
                packet.close()

    def test_inventory_and_path_traversal_rejected(self):
        for extra in ('unexpected', '../escape'):
            with self.subTest(extra=extra), tempfile.TemporaryDirectory() as d:
                with self.assertRaises(ValueError):
                    Packet(self.fixture(d, extra=extra))

    def test_destination_symlink_and_contract_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            packet = Packet(self.fixture(d))
            try:
                dest = Path(d) / 'out'
                dest.mkdir()
                (dest / 'WORK').symlink_to(Path(d), target_is_directory=True)
                with self.assertRaisesRegex(ValueError, 'Symlink'):
                    packet.extract(packet.bootstrap(), dest)
                contract = Path(d) / 'contract.json'
                contract.write_text(json.dumps({'packet_id': 'wrong', 'task_id': 'task'}))
                with self.assertRaisesRegex(ValueError, 'different packet'):
                    packet.contract_tasks(contract)
            finally:
                packet.close()


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, zipfile.BadZipFile) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        raise SystemExit(2)
