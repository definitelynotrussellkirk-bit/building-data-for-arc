#!/usr/bin/env python3
"""Stream-check a full review ZIP without extracting or importing packet code.

The manifest contract is canonical UTF-8 JSON, with `files` relative to WORK
and two outer entry files. SHA-256 confirms internal consistency, not provenance.
Only --out writes a file. Memory: ZIP index, digest inventory, and manifest JSON;
payloads stream in 1 MiB chunks. No puzzle content is interpreted or emitted.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import stat
import sys
import zipfile
import zlib

MANIFEST = 'WORK/PACKET-MANIFEST.json'
CHUNK = 1024 * 1024
MAX_MANIFEST = 64 * 1024 * 1024
HEX = re.compile(r'[0-9a-f]{64}\Z')


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def safe_path(name, directory=False):
    if not isinstance(name, str) or not name or '\\' in name or ':' in name:
        return False
    if any(ord(c) < 32 or ord(c) == 127 for c in name):
        return False
    if directory and name.endswith('/'):
        name = name[:-1]
    return all(part not in ('', '.', '..') for part in name.split('/'))


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON object key')
        result[key] = value
    return result


def stream_digest(stream, capture=False):
    digest = hashlib.sha256()
    count = 0
    content = bytearray() if capture else None
    while True:
        chunk = stream.read(CHUNK)
        if not chunk:
            break
        digest.update(chunk)
        count += len(chunk)
        if capture:
            if count > MAX_MANIFEST:
                raise ValueError('manifest exceeds 64 MiB limit')
            content.extend(chunk)
    return digest.hexdigest(), count, bytes(content) if capture else None


def verify(archive):
    receipt = dict(ok=False, archive=str(archive), archive_sha256=None,
                   manifest_sha256=None, archive_members=0, archive_files=0,
                   declared_uncompressed_bytes=0, actual_uncompressed_bytes=0,
                   streamed_files=0, verified_workspace_files=0,
                   verified_entry_files=0, duplicate_paths=[], unsafe_paths=[],
                   malformed_members=[], missing_paths=[], extra_paths=[],
                   hash_mismatches=[], errors=[])
    try:
        with archive.open('rb') as source:
            before = source_stat(source)
            receipt['archive_sha256'], receipt['archive_bytes'], _ = stream_digest(source)
            source.seek(0)
            with zipfile.ZipFile(source) as z:
                infos = z.infolist()
                counts = Counter(i.filename for i in infos)
                receipt['archive_members'] = len(infos)
                receipt['duplicate_paths'] = sorted(n for n, c in counts.items() if c > 1)
                hashes = {}
                directories = set()
                raw = None
                for info in infos:
                    name = info.filename
                    isdir = info.is_dir()
                    receipt['declared_uncompressed_bytes'] += info.file_size
                    if not safe_path(name, isdir) or info.orig_filename != name:
                        receipt['unsafe_paths'].append(info.orig_filename)
                    mode = info.external_attr >> 16
                    kind = stat.S_IFMT(mode)
                    if kind not in (0, stat.S_IFREG, stat.S_IFDIR) or (kind == stat.S_IFDIR and not isdir) or (kind == stat.S_IFREG and isdir):
                        receipt['malformed_members'].append(name)
                    if isdir:
                        directories.add(name)
                        if info.file_size:
                            receipt['malformed_members'].append(name)
                        continue
                    receipt['archive_files'] += 1
                    try:
                        with z.open(info, 'r') as payload:
                            digest, size, content = stream_digest(payload, name == MANIFEST)
                        receipt['actual_uncompressed_bytes'] += size
                        receipt['streamed_files'] += 1
                        if size != info.file_size:
                            receipt['malformed_members'].append(name)
                        hashes[name] = digest
                        if name == MANIFEST:
                            raw = content
                            receipt['manifest_sha256'] = digest
                    except (OSError, ValueError, RuntimeError, NotImplementedError, EOFError, zipfile.BadZipFile, zlib.error) as exc:
                        receipt['errors'].append('cannot stream member %r: %s' % (name, exc))
                if raw is None:
                    receipt['missing_paths'].append(MANIFEST)
                    receipt['errors'].append('manifest unavailable')
                else:
                    check_manifest(raw, hashes, directories, receipt)
            if source_stat(source) != before:
                receipt['errors'].append('archive changed during verification')
    except (OSError, ValueError, RuntimeError, NotImplementedError, EOFError, zipfile.BadZipFile) as exc:
        receipt['errors'].append('archive verification failed: %s' % exc)
    for key in ('duplicate_paths', 'unsafe_paths', 'malformed_members', 'missing_paths', 'extra_paths', 'hash_mismatches'):
        receipt[key] = sorted(set(receipt[key]))
    receipt['ok'] = not any(receipt[k] for k in ('duplicate_paths', 'unsafe_paths', 'malformed_members', 'missing_paths', 'extra_paths', 'hash_mismatches', 'errors'))
    return receipt


def source_stat(source):
    import os
    s = os.fstat(source.fileno())
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)


def check_manifest(raw, hashes, directories, receipt):
    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON number')))
        if raw != canonical(value):
            receipt['errors'].append('manifest is not canonical JSON')
        if not isinstance(value, dict) or value.get('schema') != 'arcpuzzles-full-packet-v2':
            raise ValueError('unsupported manifest schema')
        layout = value.get('layout')
        if not isinstance(layout, dict) or layout.get('workspace') != 'WORK':
            raise ValueError('invalid workspace layout')
        entries = layout.get('entry_files')
        files = value.get('files')
        if not isinstance(entries, dict) or set(entries) != {'START-HERE.md', 'review.py'}:
            raise ValueError('invalid entry file inventory')
        if not isinstance(files, dict):
            raise ValueError('invalid workspace file inventory')
        expected = {MANIFEST}
        for inventory, prefix, counter in ((files, 'WORK/', 'verified_workspace_files'), (entries, '', 'verified_entry_files')):
            for name, digest in inventory.items():
                if not safe_path(name) or not isinstance(digest, str) or not HEX.fullmatch(digest):
                    raise ValueError('invalid inventory path or SHA-256')
                path = prefix + name
                if path in expected:
                    raise ValueError('overlapping manifest inventory')
                expected.add(path)
                if path not in hashes:
                    receipt['missing_paths'].append(path)
                elif hashes[path] != digest:
                    receipt['hash_mismatches'].append(path)
                elif path not in receipt['duplicate_paths']:
                    receipt[counter] += 1
        receipt['extra_paths'].extend(set(hashes) - expected)
        ancestors = set()
        for path in expected:
            parts = path.split('/')
            ancestors.update('/'.join(parts[:i]) + '/' for i in range(1, len(parts)))
        receipt['extra_paths'].extend(directories - ancestors)
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        receipt['errors'].append('invalid manifest: %s' % exc)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--out', type=Path, help='write compact JSON receipt instead of stdout')
    args = parser.parse_args(argv)
    if args.out and args.out.resolve() == args.archive.resolve():
        parser.error('--out must not overwrite the archive')
    result = verify(args.archive)
    output = canonical(result).decode('utf-8') + '\n'
    if args.out:
        try:
            # Exclusive creation also prevents overwriting the archive via a hard link.
            with args.out.open('x', encoding='utf-8') as target:
                target.write(output)
        except OSError as exc:
            print('cannot write receipt: %s' % exc, file=sys.stderr)
            return 2
    else:
        sys.stdout.write(output)
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
