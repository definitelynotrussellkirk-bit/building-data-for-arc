#!/usr/bin/env python3
"""Storage-only adapter for an UNMODIFIED arcpuzzles full-return builder.

The archive and extraction inventory must be pinned independently. Archive-only
reads are allowed solely for never-extracted, non-selected repository originals.
No returned code is executed by this adapter. It does not replace replay-return.
"""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import hashlib
import io
from importlib.machinery import EXTENSION_SUFFIXES
import json
import os
from pathlib import Path, PosixPath, PurePosixPath
import stat as statmod
import sys
import tempfile
import zipfile


class IntegrityError(ValueError):
    pass


def digest_file(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def safe_name(name):
    if (not isinstance(name, str) or not name or '\\' in name or '\x00' in name
            or name.startswith('/') or any(p in ('', '.', '..') for p in name.split('/'))):
        raise IntegrityError(f'Unsafe relative path: {name!r}')
    return name


class ArchiveView:
    def __init__(self, *, archive, root, inventory, source_sha256, inventory_sha256,
                 selected_task):
        self.archive = Path(archive).resolve()
        self.root = Path(root).absolute()
        self.inventory = Path(inventory).resolve()
        self.selected = safe_name(selected_task)
        if '/' in self.selected:
            raise IntegrityError('Selected task must be one path component')
        self._check_real(self.root)
        self.baseline_paths = set()
        assignment = self.root / 'ASSIGNMENT.json'
        self._check_real(assignment)
        if assignment.is_file():
            record = json.loads(assignment.read_text())
            if record['task_id'] != self.selected:
                raise IntegrityError('Selected task differs from assignment')
            self.baseline_paths = {safe_name(k) for k in record.get('baseline_sha256', {})}
        if digest_file(self.archive) != source_sha256:
            raise IntegrityError('Source ZIP SHA-256 mismatch')
        if digest_file(self.inventory) != inventory_sha256:
            raise IntegrityError('Extraction inventory SHA-256 mismatch')
        self.zip = zipfile.ZipFile(self.archive)
        try:
            infos = self.zip.infolist()
            self.members = {}
            seen = set()
            for info in infos:
                name = safe_name(info.filename[:-1] if info.is_dir() else info.filename)
                if name in seen:
                    raise IntegrityError(f'Duplicate archive member: {name}')
                seen.add(name)
                mode = info.external_attr >> 16
                allowed_types = (0, statmod.S_IFDIR) if info.is_dir() else (0, statmod.S_IFREG)
                if statmod.S_IFMT(mode) not in allowed_types:
                    raise IntegrityError(f'Nonregular archive member: {name}')
                if info.is_dir():
                    continue
                self.members[name] = info
            self.manifest_raw = self.zip.read('WORK/PACKET-MANIFEST.json')
            self.manifest = json.loads(self.manifest_raw)
            self.hashes = {safe_name('WORK/' + safe_name(k)): v
                           for k, v in self.manifest['files'].items()}
            self.hashes.update({safe_name(k): v for k, v in
                               self.manifest['layout']['entry_files'].items()})
            self.hashes['WORK/PACKET-MANIFEST.json'] = hashlib.sha256(self.manifest_raw).hexdigest()
            if set(self.members) != set(self.hashes):
                raise IntegrityError('Archive inventory differs from manifest plus outer entries')
            for name, expected in self.hashes.items():
                h = hashlib.sha256()
                with self.zip.open(name) as f:
                    for chunk in iter(lambda: f.read(1024 * 1024), b''):
                        h.update(chunk)
                if h.hexdigest() != expected:
                    raise IntegrityError(f'Archive member hash mismatch: {name}')
            inventory_value = json.loads(self.inventory.read_text())
            self.materialized = set()
            for row in inventory_value['files']:
                name = safe_name(row['path'])
                if name in self.materialized or name not in self.members:
                    raise IntegrityError(f'Invalid extraction inventory member: {name}')
                if row['sha256'] != self.hashes[name] or row['bytes'] != self.members[name].file_size:
                    raise IntegrityError(f'Extraction inventory disagrees with archive: {name}')
                self.materialized.add(name)
            # Missing materialized files never become archive-only originals.
            for name in self.materialized:
                actual = self.root.parent / name
                self._check_real(actual)
                if not actual.is_file():
                    raise IntegrityError(f'Materialized original missing: {name}')
            # The manifest and outer entrypoints are immutable anchors, too.
            for name in ['WORK/PACKET-MANIFEST.json', *self.manifest['layout']['entry_files']]:
                actual = self.root.parent / name
                self._check_real(actual)
                if not actual.is_file() or digest_file(actual) != self.hashes[name]:
                    raise IntegrityError(f'Original anchor changed or missing: {name}')
            self.virtual = {name[5:]: info for name, info in self.members.items()
                            if name.startswith('WORK/repo/') and name not in self.materialized
                            and not self.protected(name[5:])}
            self.dirs = set()
            self.children = {}
            for name in self.virtual:
                self.dirs.update(str(p) for p in PurePosixPath(name).parents if str(p) != '.')
                parts = name.split('/')
                for j, part in enumerate(parts):
                    self.children.setdefault('/'.join(parts[:j]) or '.', set()).add(part)
            self._pinned_source = source_sha256
            self._pinned_inventory = inventory_sha256
        except BaseException:
            self.zip.close()
            raise

    def protected(self, rel):
        return (not rel.startswith('repo/')
                or rel == f'repo/generators/{self.selected}'
                or rel.startswith(f'repo/generators/{self.selected}/')
                or rel == 'repo/shared/data/canonical/puzzles.jsonl'
                or rel in self.baseline_paths)

    def _check_real(self, path):
        path = Path(path).absolute()
        for item in [path, *path.parents]:
            if item.is_symlink():
                raise IntegrityError(f'Symlink forbidden: {item}')

    def relative(self, path):
        physical = Path(str(path))
        if not physical.is_absolute():
            raise IntegrityError('Filesystem operations require absolute overlay paths')
        if '..' in physical.parts:
            raise IntegrityError('Parent traversal forbidden')
        self._check_real(physical)
        try:
            return physical.relative_to(self.root).as_posix()
        except ValueError:
            # Outputs outside WORK remain real paths; archive fallback never applies.
            return None

    def fallback(self, path):
        rel = self.relative(path)
        physical = Path(str(path))
        if physical.exists():
            return None
        if rel is not None and 'WORK/' + rel in self.materialized:
            raise IntegrityError(f'Materialized original missing: WORK/{rel}')
        return rel if rel in self.virtual else None

    def read(self, rel):
        raw = self.zip.read('WORK/' + rel)
        if hashlib.sha256(raw).hexdigest() != self.hashes['WORK/' + rel]:
            raise IntegrityError(f'Archive changed during read: {rel}')
        return raw

    def path(self):
        context = self
        class OverlayPath(PosixPath):
            _view = context

            def resolve(self, strict=False):
                self._view.relative(self)
                if strict and not self.exists():
                    raise FileNotFoundError(self)
                return type(self)(os.path.abspath(str(self)))

            def stat(self, *, follow_symlinks=True):
                rel = self._view.fallback(self)
                if rel is not None:
                    size = self._view.virtual[rel].file_size
                    return os.stat_result((statmod.S_IFREG | 0o644, 0, 0, 1, 0, 0, size, 0, 0, 0))
                physical = Path(str(self))
                own = self._view.relative(self)
                if not physical.exists() and own in self._view.dirs:
                    return os.stat_result((statmod.S_IFDIR | 0o755, 0, 0, 1, 0, 0, 0, 0, 0, 0))
                return physical.stat(follow_symlinks=follow_symlinks)

            def exists(self, *, follow_symlinks=True):
                try:
                    self.stat(follow_symlinks=follow_symlinks)
                    return True
                except FileNotFoundError:
                    return False

            def is_file(self, *, follow_symlinks=True):
                try:
                    return statmod.S_ISREG(self.stat(follow_symlinks=follow_symlinks).st_mode)
                except FileNotFoundError:
                    return False

            def is_dir(self, *, follow_symlinks=True):
                try:
                    return statmod.S_ISDIR(self.stat(follow_symlinks=follow_symlinks).st_mode)
                except FileNotFoundError:
                    return False

            def is_symlink(self):
                self._view.relative(self)
                return False  # _check_real already rejects every symlink ancestor.

            def open(self, mode='r', buffering=-1, encoding=None, errors=None, newline=None):
                rel = self._view.fallback(self)
                if rel is not None and mode in ('r', 'rt', 'rb'):
                    raw = io.BytesIO(self._view.read(rel))
                    if mode == 'rb':
                        return raw
                    return io.TextIOWrapper(raw, encoding=encoding or 'utf-8', errors=errors, newline=newline)
                # Write operations always address the real filesystem.
                return Path(str(self)).open(mode, buffering, encoding, errors, newline)

            def iterdir(self):
                self._view.relative(self)
                physical = Path(str(self))
                names = set()
                if physical.exists():
                    for child in physical.iterdir():
                        self._view.relative(child)
                        names.add(child.name)
                rel = self._view.relative(self)
                names.update(self._view.children.get(rel, ()))
                for name in sorted(names):
                    yield self / name

            def rglob(self, pattern, *, case_sensitive=None, recurse_symlinks=False):
                if pattern != '*' or case_sensitive is not None or recurse_symlinks:
                    raise NotImplementedError('This audited adapter supports only official builder rglob("*")')
                self._view.relative(self)
                stack = [self]
                while stack:
                    current = stack.pop()
                    for child in current.iterdir():
                        yield child
                        if child.is_dir():
                            stack.append(child)

        return OverlayPath(self.root)

    def close(self):
        self.zip.close()


@contextmanager
def official_import_context(source_root):
    """Import checked official sources without reusing any compiled cache.

    The CLI verifies source hashes before entering this context. A fresh cache
    namespace prevents even unchecked-hash bytecode from superseding those
    bytes. Reject already imported official modules rather than trusting them.
    All lazy official imports during build and validation must stay inside.
    """
    preloaded = sorted(name for name in sys.modules
                       if name == 'arcpuzzles' or name.startswith('arcpuzzles.'))
    if preloaded:
        raise IntegrityError(f'Official modules already preloaded: {preloaded}')
    source_root = Path(source_root).resolve()
    for source in source_root.rglob('*'):
        if source.is_symlink():
            raise IntegrityError(f'Official source symlink forbidden: {source}')
        if (source.name.endswith(tuple(EXTENSION_SUFFIXES))
                or (source.suffix == '.pyc' and source.parent.name != '__pycache__')):
            raise IntegrityError(f'Alternative executable official module forbidden: {source}')
    previous_path = list(sys.path)
    previous_prefix = sys.pycache_prefix
    previous_write_policy = sys.dont_write_bytecode
    with tempfile.TemporaryDirectory(prefix='arcpuzzles-verified-import-') as cache:
        try:
            sys.pycache_prefix = cache
            sys.dont_write_bytecode = True
            sys.path.insert(0, str(source_root))
            yield
        finally:
            sys.path[:] = previous_path
            sys.pycache_prefix = previous_prefix
            sys.dont_write_bytecode = previous_write_policy


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--work', type=Path, required=True)
    p.add_argument('--inventory', type=Path, required=True)
    p.add_argument('--source-sha256', required=True)
    p.add_argument('--inventory-sha256', required=True)
    p.add_argument('--task-id', required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--bundle-evidence', action='store_true')
    a = p.parse_args()
    view = ArchiveView(archive=a.archive, root=a.work, inventory=a.inventory,
                       source_sha256=a.source_sha256, inventory_sha256=a.inventory_sha256,
                       selected_task=a.task_id)
    try:
        contract = json.loads((a.work / 'ASSIGNMENT.json').read_text())
        if contract['task_id'] != a.task_id:
            raise IntegrityError('Selected task differs from assignment')
        # Authenticate all physical Python authoring sources before importing them.
        for real in (a.work / 'repo/src').rglob('*'):
            if not real.is_file() or real.suffix != '.py':
                continue
            view._check_real(real)
            name = 'WORK/' + real.relative_to(a.work).as_posix()
            if name not in view.hashes or digest_file(real) != view.hashes[name]:
                raise IntegrityError(f'Official Python source changed: {name}')
        # No monkeypatch: the genuine builder receives only a Path subclass.
        with official_import_context(a.work / 'repo/src'):
            from arcpuzzles.review_full_return import build_full_return, validate_full_return
            result = build_full_return(view.path(), a.out, bundle_evidence=a.bundle_evidence)
            with zipfile.ZipFile(a.out) as returned:
                validate_full_return(returned, view.manifest)
        if digest_file(a.archive) != a.source_sha256 or digest_file(a.inventory) != a.inventory_sha256:
            raise IntegrityError('Pinned archive or inventory changed during packaging')
        print(json.dumps(result, sort_keys=True))
    finally:
        view.close()


if __name__ == '__main__':
    main()
