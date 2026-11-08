#!/usr/bin/env python3
"""Lossless indexed gzip evidence. Stop all evidence writers before compressing."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import sys

SCHEMA = 'arc-review-evidence-archive-v1'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def relative(name):
    if not isinstance(name, str) or not name or any(c in name for c in ('\\', '\0', ':')):
        raise ValueError(f'unsafe evidence path: {name!r}')
    p = PurePosixPath(name)
    if (p.is_absolute() or p.as_posix() != name or '..' in p.parts
            or len(p.parts) < 2 or p.parts[0] != 'checks'
            or p.name == 'RUNTIME_MANIFEST.json'
            or any(c in {'src', 'repo', 'lib', 'site-packages', 'puzzle_generators', 'arc_repl', '__pycache__'}
                   or c.startswith(('runtime', '.venv')) for c in p.parts[:-1])):
        raise ValueError(f'unsafe or runtime evidence path: {name!r}')
    return p


def checked(path):
    """Reject symlinks in the destination and every existing ancestor."""
    path = Path(path).absolute()
    if '..' in path.parts:
        raise ValueError(f'parent traversal forbidden: {path}')
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError(f'symlink forbidden: {part}')
    return path


def member(root, name):
    return checked(root / relative(name))


def packed_name(name):
    return 'checks/compressed/' + str(relative(name).relative_to('checks')) + '.gz'


def write_new(path, raw):
    path = checked(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as handle:
        handle.write(raw)


def load_index(root, manifest):
    index = json.loads(member(root, manifest).read_bytes())
    if not isinstance(index, dict) or index.get('schema') != SCHEMA:
        raise ValueError('invalid compression index schema')
    rows = index.get('entries')
    if not isinstance(rows, list) or not rows:
        raise ValueError('index entries must be a nonempty list')
    originals, compressed = set(), set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('index entry must be an object')
        original = str(relative(row.get('original_path')))
        packed = str(relative(row.get('compressed_path')))
        if original.startswith('checks/compressed/') or packed != packed_name(original):
            raise ValueError('compressed path must preserve the original hierarchy')
        for name, seen in ((original, originals), (packed, compressed)):
            if name.casefold() in seen:
                raise ValueError('duplicate evidence path')
            seen.add(name.casefold())
        for prefix in ('original', 'compressed'):
            if type(row.get(prefix + '_bytes')) is not int or row[prefix + '_bytes'] < 0:
                raise ValueError('invalid byte count')
            if not isinstance(row.get(prefix + '_sha256'), str) or not re.fullmatch('[0-9a-f]{64}', row[prefix + '_sha256']):
                raise ValueError('invalid SHA-256')
    all_paths = originals | compressed | {manifest.casefold()}
    for name in all_paths:
        if any(str(p).casefold() in all_paths for p in PurePosixPath(name).parents):
            raise ValueError('file/directory collision in index')
    if manifest.casefold() in originals | compressed:
        raise ValueError('index collides with evidence')
    return rows


def unpack(root, row):
    packed = member(root, row['compressed_path']).read_bytes()
    if len(packed) != row['compressed_bytes'] or sha(packed) != row['compressed_sha256']:
        raise ValueError(f"compressed bytes differ: {row['compressed_path']}")
    with gzip.GzipFile(fileobj=io.BytesIO(packed)) as stream:
        raw = stream.read(row['original_bytes'] + 1)
    if len(raw) != row['original_bytes'] or sha(raw) != row['original_sha256']:
        raise ValueError(f"original bytes differ: {row['original_path']}")
    return raw


def compress(args):
    root, backup = checked(args.root), checked(args.backup_root)
    manifest = str(relative(args.manifest))
    if backup == root or root in backup.parents:
        raise ValueError('backup-root must be outside root')
    if backup.exists() or member(root, manifest).exists():
        raise FileExistsError('backup-root and manifest must be new')
    names = [str(relative(name)) for name in args.paths]
    all_names = [manifest, *names, *(packed_name(name) for name in names)]
    seen = {name.casefold() for name in all_names}
    if len(seen) != len(all_names):
        raise ValueError('duplicate or colliding input/output/index path')
    if any(str(parent).casefold() in seen for name in all_names for parent in PurePosixPath(name).parents):
        raise ValueError('file/directory collision in input/output/index paths')
    for name in names:
        if name.startswith('checks/compressed/') or name == manifest:
            raise ValueError('cannot compress the index or compressed evidence')
        source, target = member(root, name), member(root, packed_name(name))
        if not source.is_file() or target.exists():
            raise ValueError(f'input missing or compressed output exists: {name}')
    backup.mkdir(parents=True, exist_ok=False)
    rows = []
    for name in names:
        raw = member(root, name).read_bytes()
        packed = gzip.compress(raw, mtime=0)
        row = dict(original_path=name, compressed_path=packed_name(name),
                   original_bytes=len(raw), original_sha256=sha(raw),
                   compressed_bytes=len(packed), compressed_sha256=sha(packed))
        write_new(backup / name, raw)
        write_new(member(root, row['compressed_path']), packed)
        if unpack(root, row) != raw or (backup / name).read_bytes() != raw:
            raise ValueError('roundtrip or backup verification failed')
        rows.append(row)
    write_new(member(root, manifest), (json.dumps({'schema': SCHEMA, 'entries': rows}, indent=2) + '\n').encode())
    # All representations and the published index are verified before removal.
    for row in load_index(root, manifest):
        raw = unpack(root, row)
        if member(root, row['original_path']).read_bytes() != raw or (backup / row['original_path']).read_bytes() != raw:
            raise ValueError('original or backup changed; originals retained')
    for row in rows:
        path = member(root, row['original_path'])
        raw = path.read_bytes()
        if len(raw) != row['original_bytes'] or sha(raw) != row['original_sha256']:
            raise ValueError('original changed during removal; remaining originals retained')
        path.unlink()
    return {'compressed': len(rows), 'manifest': manifest, 'backup_root': str(backup)}


def restore(args):
    root, out = checked(args.root), checked(args.out)
    if out.exists():
        raise FileExistsError('restore destination must be new')
    rows = load_index(root, str(relative(args.manifest)))
    for row in rows:
        unpack(root, row)  # Verify the entire input before creating output.
    out.mkdir(parents=True, exist_ok=False)
    for row in rows:
        write_new(member(out, row['original_path']), unpack(root, row))
    return {'restored': len(rows), 'out': str(out)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('compress', 'restore'):
        command = commands.add_parser(name)
        command.add_argument('--root', type=Path, required=True)
        command.add_argument('--manifest', required=True)
        if name == 'compress':
            command.add_argument('--backup-root', type=Path, required=True)
            command.add_argument('paths', nargs='+')
        else:
            command.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(compress(args) if args.command == 'compress' else restore(args)))
        return 0
    except (OSError, ValueError, EOFError) as error:
        print(f'evidence operation rejected: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
