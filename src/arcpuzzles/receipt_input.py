"""Read exact JSON or one native hash-bound gzip receipt without executing code."""
from __future__ import annotations

import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import zlib

SCHEMA = 'arcpuzzles-evidence-gzip-v1'


def _relative(name):
    if (not isinstance(name, str) or not name or '\\' in name or '\0' in name
            or name.startswith('/') or any(p in ('', '.', '..') for p in name.split('/'))):
        raise ValueError(f'Invalid compressed receipt path: {name!r}')
    return PurePosixPath(name)


def _regular(path):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (*path.parents, path)) or not path.is_file():
        raise ValueError(f'Compressed receipt needs a regular file without symlinks: {path}')
    return path


def read_receipt(path):
    """Return verified decoded bytes, transport identity and retained transport bytes.

    A .json.gz input must have the writer's neighboring .compression.json.
    An explicit native manifest must describe exactly one receipt. No new
    decompressed file is written; expansion stops at its declared size plus one.
    Plain JSON keeps its original bytes and has no compression identity.
    """
    path = Path(path)
    gzip_input = path.name.endswith('.json.gz')
    manifest_path = path.with_suffix('').with_suffix('.compression.json') if gzip_input else path
    try:
        manifest_raw = manifest_path.read_bytes()
        document = json.loads(manifest_raw)
    except (OSError, ValueError, UnicodeError) as exc:
        raise ValueError(f'Cannot read schedule receipt/manifest: {manifest_path}') from exc
    if not gzip_input and (not isinstance(document, dict) or document.get('schema') != SCHEMA):
        return {'raw': manifest_raw, 'transport': None, 'transport_files': {}}
    _regular(manifest_path)
    if (not isinstance(document, dict) or document.get('schema') != SCHEMA
            or document.get('compression', 'gzip') != 'gzip'):
        raise ValueError('Invalid compressed receipt manifest schema/compression')
    rows = document.get('files')
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise ValueError('Compressed schedule receipt manifest requires exactly one file')
    row = rows[0]
    original, packed_name = _relative(row.get('path')), _relative(row.get('compressed_path'))
    if str(packed_name) != str(original) + '.gz':
        raise ValueError('Compressed receipt path must be original path plus .gz')
    for key in ('raw_size', 'compressed_size'):
        if type(row.get(key)) is not int or row[key] < 0:
            raise ValueError(f'Invalid compressed receipt {key}')
    for key in ('raw_sha256', 'compressed_sha256'):
        if not isinstance(row.get(key), str) or not re.fullmatch('[0-9a-f]{64}', row[key]):
            raise ValueError(f'Invalid compressed receipt {key}')
    packed_path = _regular(manifest_path.parent / packed_name)
    if gzip_input and packed_path != path.absolute():
        raise ValueError('Compressed receipt manifest does not bind the requested gzip file')
    if packed_name.parts[0] == 'MANIFEST.json':
        raise ValueError('Compressed receipt path collides with retained manifest')
    packed = packed_path.read_bytes()
    if len(packed) != row['compressed_size'] or hashlib.sha256(packed).hexdigest() != row['compressed_sha256']:
        raise ValueError('Compressed receipt size/hash mismatch')
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(packed)) as stream:
            raw = stream.read(row['raw_size'] + 1)
    except (OSError, EOFError, zlib.error) as exc:
        raise ValueError('Compressed receipt has invalid or truncated gzip') from exc
    if len(raw) != row['raw_size'] or hashlib.sha256(raw).hexdigest() != row['raw_sha256']:
        raise ValueError('Compressed receipt raw size/hash mismatch')
    try:
        json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise ValueError('Compressed receipt is not valid JSON') from exc
    return {'raw': raw,
            'transport': {'format': SCHEMA, 'manifest_sha256': hashlib.sha256(manifest_raw).hexdigest(),
                          **{k: row[k] for k in ('raw_size', 'raw_sha256', 'compressed_size', 'compressed_sha256')}},
            'transport_files': {'MANIFEST.json': manifest_raw, str(packed_name): packed}}
