#!/usr/bin/env python3
"""Pack, verify, and restore explicitly selected checks/ evidence with stdlib gzip.

Manifest schema review-large-evidence-v1 is recognized by ARCpuzzles retention.
No originals are deleted. Run --help; paths in manifests are WORK-relative.
Use a private, non-concurrently-edited workspace; this is not a sandbox for
another process racing directory replacements. Requires Python 3.12+.
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
import zlib

SCHEMA = 'review-large-evidence-v1'
DEFAULT_LIMIT = 128 * 1024 * 1024
CHUNK = 1024 * 1024
MAX_ENTRIES = 4096
MAX_MANIFEST = 4 * 1024 * 1024


def checked_path(value: str) -> str:
    """Only canonical relative paths beneath checks/ are transportable."""
    if (not isinstance(value, str) or not value.startswith('checks/')
            or any(ord(c) < 32 or ord(c) == 127 for c in value)
            or '\\' in value or ':' in value
            or any(part in ('', '.', '..') for part in value.split('/'))
            or str(PurePosixPath(value)) != value):
        raise ValueError(f'unsafe checks/ path: {value!r}')
    return value


def no_symlinks(path: Path) -> None:
    for item in (path, *path.parents):
        if item.is_symlink():
            raise ValueError(f'symlink is not allowed: {item}')


def regular(path: Path) -> None:
    no_symlinks(path)
    if not stat.S_ISREG(path.stat().st_mode):
        raise ValueError(f'not a regular file: {path}')


def digest(path: Path) -> tuple[int, str]:
    regular(path)
    size, checksum = 0, hashlib.sha256()
    with path.open('rb') as source:
        while chunk := source.read(CHUNK):
            size += len(chunk)
            checksum.update(chunk)
    return size, checksum.hexdigest()


def json_bytes(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode()


def unique_keys(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f'duplicate JSON key: {key}')
        value[key] = item
    return value


def no_collisions(paths) -> None:
    paths = set(paths)
    for path in paths:
        if any(parent.as_posix() in paths for parent in PurePosixPath(path).parents):
            raise ValueError(f'file/directory path collision: {path}')


def load_manifest(work: Path, manifest_path: str, limit: int) -> dict:
    manifest_path = checked_path(manifest_path)
    path = work / manifest_path
    regular(path)
    if path.stat().st_size > MAX_MANIFEST:
        raise ValueError('manifest exceeds 4 MiB')
    manifest = json.loads(path.read_bytes(), object_pairs_hook=unique_keys)
    if (not isinstance(manifest, dict) or manifest.get('schema') != SCHEMA
            or manifest.get('compression') != 'gzip'):
        raise ValueError('unsupported evidence manifest')
    rows = manifest.get('files')
    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_ENTRIES:
        raise ValueError('manifest requires 1..4096 files')
    originals, compressed = set(), set()
    original_bytes = compressed_bytes = 0
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('manifest row must be an object')
        original = checked_path(row.get('original_path'))
        payload = checked_path(row.get('compressed_path'))
        if (original in originals or payload in compressed or not payload.endswith('.gz')
                or original == payload):
            raise ValueError('duplicate original/payload path or invalid gzip name')
        originals.add(original)
        compressed.add(payload)
        for prefix in ('original', 'compressed'):
            size, sha = row.get(prefix + '_bytes'), row.get(prefix + '_sha256')
            if type(size) is not int or size < 0:
                raise ValueError(f'invalid {prefix} byte count')
            if not isinstance(sha, str) or not re.fullmatch('[0-9a-f]{64}', sha):
                raise ValueError(f'invalid {prefix} SHA-256')
        original_bytes += row['original_bytes']
        compressed_bytes += row['compressed_bytes']
    if manifest_path in compressed:
        raise ValueError('manifest cannot name itself as a gzip payload')
    if originals & (compressed | {manifest_path}):
        raise ValueError('original paths overlap archive members')
    no_collisions(originals)
    no_collisions(compressed | {manifest_path})
    totals = dict(count=len(rows), original_bytes=original_bytes, compressed_bytes=compressed_bytes)
    if any(type(manifest.get(key)) is not int or manifest[key] != value for key, value in totals.items()):
        raise ValueError('manifest totals differ from file entries')
    if original_bytes > limit or compressed_bytes > limit + MAX_ENTRIES * 1024:
        raise ValueError('manifest exceeds configured aggregate byte limit')
    return manifest


def expand(work: Path, row: dict, destination=None) -> None:
    """Consume no more than the declared expansion plus one detecting byte."""
    payload = work / row['compressed_path']
    if digest(payload) != (row['compressed_bytes'], row['compressed_sha256']):
        raise ValueError(f'compressed size/hash mismatch: {row["compressed_path"]}')
    count, checksum = 0, hashlib.sha256()
    with gzip.open(payload, 'rb') as source:
        while chunk := source.read(min(CHUNK, row['original_bytes'] - count + 1)):
            count += len(chunk)
            if count > row['original_bytes']:
                raise ValueError(f'expansion exceeds declared bytes: {row["original_path"]}')
            checksum.update(chunk)
            if destination is not None:
                destination.write(chunk)
    if (count, checksum.hexdigest()) != (row['original_bytes'], row['original_sha256']):
        raise ValueError(f'expanded size/hash mismatch: {row["original_path"]}')


def publish(temporary: Path, target: Path) -> None:
    """Exclusive publication; an equal existing file is preserved unchanged."""
    no_symlinks(target)
    try:
        os.link(temporary, target)
    except FileExistsError:
        if digest(target) != digest(temporary):
            raise ValueError(f'existing different content is preserved: {target}')


def temporary_file(parent: Path):
    no_symlinks(parent)
    parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix='.evidence-', dir=parent)
    return descriptor, Path(name)


def pack(work: Path, manifest_path: str, paths: list[str], limit: int) -> dict:
    manifest_path = checked_path(manifest_path)
    paths = sorted(checked_path(path) for path in paths)
    if not 1 <= len(paths) <= MAX_ENTRIES or len(set(paths)) != len(paths):
        raise ValueError('select 1..4096 distinct explicit checks/ files')
    output = PurePosixPath(manifest_path).parent
    if any(PurePosixPath(path).is_relative_to(output) for path in paths):
        raise ValueError('input evidence must be outside the archive manifest directory')
    source_info = {path: digest(work / path) for path in paths}
    if sum(size for size, sha in source_info.values()) > limit:
        raise ValueError('selected evidence exceeds aggregate byte limit')
    manifest_target = work / manifest_path
    no_symlinks(manifest_target)
    if manifest_target.exists():
        prior = verify(work, manifest_path, limit)
        if ({row['original_path']: (row['original_bytes'], row['original_sha256'])
             for row in prior['files']} != source_info):
            raise ValueError('existing manifest differs; choose a new manifest path')
        return prior
    rows = []
    for path in paths:
        compressed_path = (output / 'payloads' / (path.removeprefix('checks/') + '.gz')).as_posix()
        target = work / checked_path(compressed_path)
        descriptor, temporary = temporary_file(target.parent)
        try:
            raw_size, raw_sha = 0, hashlib.sha256()
            with os.fdopen(descriptor, 'wb') as sink:
                with gzip.GzipFile(filename='', fileobj=sink, mode='wb', compresslevel=9, mtime=0) as compressed:
                    with (work / path).open('rb') as source:
                        while chunk := source.read(CHUNK):
                            raw_size += len(chunk)
                            if raw_size > source_info[path][0]:
                                raise ValueError(f'source changed during packing: {path}')
                            raw_sha.update(chunk)
                            compressed.write(chunk)
                sink.flush()
                os.fsync(sink.fileno())
            if (raw_size, raw_sha.hexdigest()) != source_info[path]:
                raise ValueError(f'source changed during packing: {path}')
            compressed_size, compressed_sha = digest(temporary)
            row = dict(original_path=path, original_bytes=raw_size, original_sha256=raw_sha.hexdigest(),
                       compressed_path=compressed_path, compressed_bytes=compressed_size,
                       compressed_sha256=compressed_sha)
            # Verify actual compressed bytes and full CRC before making them visible.
            expand_temporary = dict(row, compressed_path=temporary.relative_to(work).as_posix())
            expand(work, expand_temporary)
            publish(temporary, target)
            rows.append(row)
        finally:
            temporary.unlink(missing_ok=True)
    manifest = dict(schema=SCHEMA, compression='gzip', count=len(rows),
                    original_bytes=sum(row['original_bytes'] for row in rows),
                    compressed_bytes=sum(row['compressed_bytes'] for row in rows), files=rows,
                    restoration='Run evidence_archive.py verify --work WORK --manifest THIS_WORK_RELATIVE_PATH, then restore with the same options and --destination NEW_WORK_ROOT. Original checks/ paths are recreated. Existing different files are never overwritten. Originals were not deleted by pack.')
    if len(json_bytes(manifest)) > MAX_MANIFEST:
        raise ValueError('generated manifest exceeds 4 MiB')
    descriptor, temporary = temporary_file(manifest_target.parent)
    try:
        with os.fdopen(descriptor, 'wb') as sink:
            sink.write(json_bytes(manifest))
            sink.flush()
            os.fsync(sink.fileno())
        publish(temporary, manifest_target)
    finally:
        temporary.unlink(missing_ok=True)
    return verify(work, manifest_path, limit)


def verify(work: Path, manifest_path: str, limit: int) -> dict:
    manifest = load_manifest(work, manifest_path, limit)
    for row in manifest['files']:
        expand(work, row)
    return manifest


def restore(work: Path, manifest_path: str, destination: Path, limit: int) -> dict:
    manifest = verify(work, manifest_path, limit)
    no_symlinks(destination)
    # Detect every existing conflict before creating the first restored file.
    for row in manifest['files']:
        target = destination / row['original_path']
        no_symlinks(target)
        if target.exists() and digest(target) != (row['original_bytes'], row['original_sha256']):
            raise ValueError(f'existing different content is preserved: {target}')
    for row in manifest['files']:
        target = destination / row['original_path']
        if target.exists():
            continue
        descriptor, temporary = temporary_file(target.parent)
        try:
            with os.fdopen(descriptor, 'wb') as sink:
                expand(work, row, sink)
                sink.flush()
                os.fsync(sink.fileno())
            publish(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
    return manifest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('pack', 'verify', 'restore'):
        command = commands.add_parser(name)
        command.add_argument('--work', type=Path, required=True, help='WORK root containing checks/')
        command.add_argument('--manifest', default='checks/compressed/MANIFEST.json', help='WORK-relative checks/ manifest path')
        command.add_argument('--max-bytes', type=int, default=DEFAULT_LIMIT, help='aggregate expanded limit; default 134217728 (128 MiB)')
        if name == 'pack':
            command.add_argument('--path', action='append', required=True, help='explicit WORK-relative checks/ file; repeat')
        if name == 'restore':
            command.add_argument('--destination', type=Path, required=True, help='destination WORK root; restores original checks/ paths')
    args = parser.parse_args(argv)
    try:
        if args.max_bytes < 1:
            raise ValueError('--max-bytes must be positive')
        work = args.work.absolute()
        no_symlinks(work)
        if not work.is_dir():
            raise ValueError('--work must be an existing directory')
        if args.command == 'pack':
            result = pack(work, args.manifest, args.path, args.max_bytes)
        elif args.command == 'verify':
            result = verify(work, args.manifest, args.max_bytes)
        else:
            result = restore(work, args.manifest, args.destination.absolute(), args.max_bytes)
        print(json.dumps(dict(status=args.command + '_verified', manifest=args.manifest,
                              count=result['count'], original_bytes=result['original_bytes'],
                              compressed_bytes=result['compressed_bytes']), sort_keys=True))
        return 0
    except (OSError, EOFError, ValueError, TypeError, KeyError, zlib.error) as exc:
        print(f'evidence archive rejected: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
