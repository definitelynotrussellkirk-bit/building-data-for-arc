#!/usr/bin/env python3
"""Verify and restore the two full source-bound lesson census reports."""
from __future__ import annotations
import argparse, gzip, hashlib, json
from pathlib import Path

HERE=Path(__file__).resolve().parent

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',type=Path,default=HERE/'restored')
    args=ap.parse_args()
    manifest=json.loads((HERE/'compressed-evidence-manifest.json').read_text())
    args.out.mkdir(parents=True,exist_ok=True)
    for row in manifest['files']:
        source=HERE/Path(row['path']).name
        compressed=source.read_bytes()
        if sha(compressed)!=row['compressed_sha256']:
            raise SystemExit(f'compressed hash mismatch: {source}')
        raw=gzip.decompress(compressed)
        if len(raw)!=row['restored_bytes'] or sha(raw)!=row['restored_sha256']:
            raise SystemExit(f'restored hash/size mismatch: {source}')
        target=args.out/Path(row['restores_to']).name
        target.write_bytes(raw)
        print(f'{source.name} -> {target} ({len(raw)} bytes, sha256 {sha(raw)})')
    return 0
if __name__=='__main__':
    raise SystemExit(main())
