#!/usr/bin/env python3
"""Safely classify a stored prepare error or materialize a reporter-only patch."""
from pathlib import Path
import argparse
import difflib
import hashlib
import json

from prepare_diagnostics import classify_private_error, instrument_source

parser = argparse.ArgumentParser(description=__doc__)
commands = parser.add_subparsers(dest='action', required=True)
classify = commands.add_parser('classify')
classify.add_argument('--error-record', type=Path, required=True)
classify.add_argument('--out', type=Path, required=True)
patch = commands.add_parser('patch')
patch.add_argument('--generic-source', type=Path, required=True)
patch.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
if args.out.exists():
    raise SystemExit('Output already exists; select a new path')
if args.action == 'classify':
    raw = args.error_record.read_bytes()
    record = json.loads(raw)
    result = classify_private_error(record.get('error', ''), record.get('type', ''))
    result.update({'schema': 'review-prepare-safe-diagnostic-v1',
                   'error_record_sha256': hashlib.sha256(raw).hexdigest(),
                   'record_path': str(args.error_record),
                   'blind_lane_retried': False})
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, sort_keys=True))
else:
    source = args.generic_source.read_text()
    proposed = instrument_source(source)
    delta = ''.join(difflib.unified_diff(source.splitlines(True), proposed.splitlines(True),
                fromfile='a/src/arcpuzzles/review_solve.py',
                tofile='b/src/arcpuzzles/review_solve.py'))
    args.out.write_text(delta)
    print(json.dumps({'status': 'optional_patch_written',
                      'generic_source_sha256': hashlib.sha256(source.encode()).hexdigest(),
                      'patch_sha256': hashlib.sha256(delta.encode()).hexdigest(),
                      'shared_source_modified': False}, sort_keys=True))
