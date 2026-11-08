#!/usr/bin/env python3
"""Explicit archive-backed source adapter for an unchanged official return builder.

Only never-materialized, immutable manifest repo sources may fall back to ZIP.
All selected sources, baselines, assignments, documents and evidence stay physical.
No official module is modified or monkeypatched. Output is built and then parsed
by the official APIs. This integration shim is deliberately recorded in a receipt.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PosixPath
import stat
import sys
import zipfile


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


def safe(name, directory=False):
    if directory and name.endswith('/'):
        name = name[:-1]
    return bool(name) and '\\' not in name and ':' not in name and all(ord(c) >= 32 and ord(c) != 127 for c in name) and all(p not in ('', '.', '..') for p in name.split('/'))


class SourceView:
    def __init__(self, work, archive, inventory):
        self.work = Path(work).resolve()
        self.archive = Path(archive).resolve()
        self.inventory = inventory
        self.reads = {}
        self.archive_identity = self.archive.stat()
        if inventory.get('schema') != 'arcpuzzles-materialized-sources-v1':
            raise ValueError('unsupported materialized inventory')
        if not isinstance(inventory.get('paths'), list) or any(not safe(p) for p in inventory['paths']):
            raise ValueError('invalid materialized inventory paths')
        if len(set(inventory['paths'])) != len(inventory['paths']):
            raise ValueError('duplicate materialized inventory paths')
        self.materialized = set(inventory['paths'])
        with self.archive.open('rb') as f:
            self.archive_sha256 = hashlib.file_digest(f, 'sha256').hexdigest()
        if self.archive_sha256 != inventory['archive_sha256']:
            raise ValueError('archive hash differs from materialized inventory')
        raw = (self.work/'PACKET-MANIFEST.json').read_bytes()
        self.manifest_sha256 = sha(raw)
        if self.manifest_sha256 != inventory['manifest_sha256']:
            raise ValueError('manifest hash differs from materialized inventory')
        self.manifest = json.loads(raw)
        self.contract = json.loads((self.work/'ASSIGNMENT.json').read_bytes())
        self.selected = 'repo/generators/' + self.contract['task_id'] + '/'
        self.protected = set(self.contract['baseline_sha256']) | self.materialized
        self.files = self.manifest['files']
        if any(not safe(p) for p in self.files):
            raise ValueError('unsafe manifest path')
        if not self.materialized <= set(self.files):
            raise ValueError('materialized inventory contains nonmanifest paths')
        for rel in self.materialized:
            if not os.path.lexists(self.work/rel):
                raise ValueError('deleted materialized source: ' + rel)
        # Fail closed even if an incomplete snapshot omitted selected originals.
        for rel in self.files:
            if rel.startswith(self.selected) and not os.path.lexists(self.work/rel):
                raise ValueError('missing selected source: ' + rel)
        self.z = zipfile.ZipFile(self.archive)
        try:
            self.members = {}
            for info in self.z.infolist():
                if info.filename in self.members:
                    raise ValueError('duplicate archive path: ' + info.filename)
                if not safe(info.filename, info.is_dir()) or info.orig_filename != info.filename:
                    raise ValueError('unsafe archive path: ' + repr(info.orig_filename))
                kind = stat.S_IFMT(info.external_attr >> 16)
                if kind not in (0, stat.S_IFREG, stat.S_IFDIR) or (kind == stat.S_IFDIR and not info.is_dir()) or (kind == stat.S_IFREG and info.is_dir()):
                    raise ValueError('unsafe nonregular archive member: ' + info.filename)
                self.members[info.filename] = info
            if self.z.read('WORK/PACKET-MANIFEST.json') != raw:
                raise ValueError('archive manifest differs from physical manifest')
            self.fallback = {p for p in self.files if p.startswith('repo/') and p not in self.protected and not p.startswith(self.selected)}
            for rel in self.fallback:
                info = self.members.get('WORK/' + rel)
                if info is None or info.is_dir():
                    raise ValueError('missing regular archive source: ' + rel)
            self.zip_dirs = set()
            for rel in self.files:
                parts = rel.split('/')
                self.zip_dirs.update('/'.join(parts[:i]) for i in range(1, len(parts)))
            view = self

            class ArchivePath(PosixPath):
                def _relative(self):
                    try:
                        return Path(str(self)).relative_to(view.work).as_posix()
                    except ValueError:
                        return None

                def _fallback(self):
                    rel = self._relative()
                    # Never mask any physical symlink, special file or directory.
                    if rel not in view.fallback or os.path.lexists(str(self)):
                        return None
                    view.check_parents(Path(str(self)))
                    return rel

                def is_file(self):
                    return Path(str(self)).is_file() or self._fallback() is not None

                def is_dir(self):
                    if os.path.lexists(str(self)):
                        return Path(str(self)).is_dir()
                    return self._relative() in view.zip_dirs

                def is_symlink(self):
                    return Path(str(self)).is_symlink()

                def exists(self, *, follow_symlinks=True):
                    return Path(str(self)).exists(follow_symlinks=follow_symlinks) or self._fallback() is not None or self.is_dir()

                def read_bytes(self):
                    rel = self._fallback()
                    if rel is None:
                        view.check_parents(Path(str(self)))
                        return Path(str(self)).read_bytes()
                    raw = view.z.read(view.members['WORK/' + rel])
                    digest = sha(raw)
                    if digest != view.files[rel]:
                        raise ValueError('archive source hash mismatch: ' + rel)
                    view.reads[rel] = {'path': rel, 'sha256': digest, 'bytes': len(raw)}
                    return raw

                def open(self, mode='r', buffering=-1, encoding=None, errors=None, newline=None):
                    if self._fallback() is None:
                        return Path(str(self)).open(mode, buffering, encoding, errors, newline)
                    if mode not in ('r', 'rb', 'rt'):
                        raise ValueError('archive sources are read-only')
                    stream = io.BytesIO(self.read_bytes())
                    return stream if mode == 'rb' else io.TextIOWrapper(stream, encoding=encoding or 'utf-8', errors=errors, newline=newline)

                def stat(self, *, follow_symlinks=True):
                    rel = self._fallback()
                    if rel is None:
                        return Path(str(self)).stat(follow_symlinks=follow_symlinks)
                    info = view.members['WORK/' + rel]
                    return os.stat_result((stat.S_IFREG | 0o444, 0, 0, 1, 0, 0, info.file_size, 0, 0, 0))

                def rglob(self, pattern, *, case_sensitive=None):
                    if pattern != '*':
                        raise ValueError('archive view supports only the official rglob("*") traversal')
                    physical = {str(p) for p in Path(str(self)).rglob('*', case_sensitive=case_sensitive)}
                    rel = self._relative()
                    prefix = '' if rel == '.' else rel + '/' if rel is not None else None
                    if prefix is not None:
                        for item in set(view.files) | view.zip_dirs:
                            if item.startswith(prefix) and item != rel:
                                physical.add(str(view.work/item))
                    for item in sorted(physical):
                        yield type(self)(item)

            self.root = ArchivePath(str(self.work))
        except BaseException:
            self.z.close()
            raise

    def check_parents(self, path):
        for parent in (path, *path.parents):
            if parent == self.work.parent:
                break
            if parent.is_symlink():
                raise ValueError('physical symlink in source view: ' + str(parent))

    def receipt(self):
        now = self.archive.stat()
        before = self.archive_identity
        if (now.st_dev, now.st_ino, now.st_size, now.st_mtime_ns, now.st_ctime_ns) != (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns):
            raise ValueError('archive changed while source view was active')
        rows = sorted(self.reads.values(), key=lambda r: r['path'])
        return {'schema': 'arcpuzzles-sparse-source-view-v1',
                'integration_shim': True, 'archive_sha256': self.archive_sha256,
                'manifest_sha256': self.manifest_sha256,
                'materialized_inventory_sha256': sha(canonical(self.inventory)),
                'materialized_files': len(self.materialized),
                'fallback_files': len(rows), 'fallback_bytes': sum(r['bytes'] for r in rows),
                'fallback_inventory_sha256': sha(canonical(rows)),
                'fallback_inventory_encoding': 'canonical JSON sorted list of {path,sha256,bytes}; UTF-8; no newline'}

    def __enter__(self): return self
    def __exit__(self, *exc): self.z.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work', required=True, type=Path)
    p.add_argument('--archive', required=True, type=Path)
    p.add_argument('--inventory', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--receipt', required=True, type=Path)
    p.add_argument('--bundle-evidence', action='store_true')
    args = p.parse_args()
    # Imports come from the physically materialized official package, untouched.
    sys.path.insert(0, str(args.work.resolve()/'repo/src'))
    from arcpuzzles.review_full_return import build_full_return, validate_full_return
    inventory = json.loads(args.inventory.read_bytes())
    with SourceView(args.work, args.archive, inventory) as view:
        result = build_full_return(view.root, args.out.resolve(), bundle_evidence=args.bundle_evidence)
        with zipfile.ZipFile(result['zip']) as returned:
            parsed = validate_full_return(returned, view.manifest)
        receipt = view.receipt()
        receipt.update(official_builder_result=result, official_parser_result=parsed)
        with args.receipt.open('x', encoding='utf-8') as target:
            target.write(canonical(receipt).decode() + '\n')
    print(json.dumps({'zip': result['zip'], 'zip_sha256': result['zip_sha256'],
                      'receipt': str(args.receipt), 'fallback_files': receipt['fallback_files'],
                      'fallback_bytes': receipt['fallback_bytes']}, sort_keys=True))


if __name__ == '__main__': main()
