"""Restore the exact large JSON reports described by COMPRESSION-MANIFEST.json.

After extracting the official evidence bundle, run this file with Python 3.
Existing identical files are accepted; differing files are never overwritten.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import tempfile


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.work_root.resolve()
    manifest = json.loads((root/'checks/COMPRESSION-MANIFEST.json').read_text())
    restored = []
    for row in manifest['files']:
        original, packed = root/row['original_path'], root/row['compressed_path']
        if not original.resolve().is_relative_to(root) or not packed.resolve().is_relative_to(root):
            raise ValueError('Manifest path escapes work root')
        if original.exists():
            if original.stat().st_size != row['original_size'] or sha(original) != row['original_sha256']:
                raise ValueError(f'Refusing to overwrite different file: {original}')
            restored.append(row['original_path']); continue
        if sha(packed) != row['compressed_sha256']:
            raise ValueError(f'Compressed checksum mismatch: {packed}')
        original.parent.mkdir(parents=True, exist_ok=True)
        temp = None
        try:
            with tempfile.NamedTemporaryFile(dir=original.parent, prefix='restore-', delete=False) as output:
                temp = Path(output.name)
                with gzip.open(packed, 'rb') as source:
                    for chunk in iter(lambda: source.read(1 << 20), b''):
                        output.write(chunk)
            if temp.stat().st_size != row['original_size'] or sha(temp) != row['original_sha256']:
                raise ValueError(f'Restored checksum mismatch: {original}')
            os.link(temp, original)  # atomic creation; cannot overwrite an existing path
            restored.append(row['original_path'])
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)
    print(json.dumps({'restored_exact_files': restored, 'count': len(restored)}))


if __name__ == '__main__':
    main()
