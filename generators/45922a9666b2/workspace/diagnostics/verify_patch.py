#!/usr/bin/env python3
"""Verify optional diagnostic delta in an isolated generic-source checkout."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import tempfile

from prepare_diagnostics import instrument_source

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--generic-source', type=Path, required=True)
parser.add_argument('--patch', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
if args.out.exists():
    raise SystemExit('Output exists')
source = args.generic_source.read_bytes()
patch = args.patch.resolve()
with tempfile.TemporaryDirectory(prefix='prepare-reporter-patch-') as directory:
    root = Path(directory)
    candidate = root / 'src/arcpuzzles/review_solve.py'
    candidate.parent.mkdir(parents=True)
    candidate.write_bytes(source)
    commands = []
    for command in (['git', 'init', '-q'], ['git', 'apply', '--check', str(patch)], ['git', 'apply', str(patch)]):
        process = subprocess.run(command, cwd=root, text=True, capture_output=True)
        commands.append({'argv': command, 'exit_code': process.returncode})
        if process.returncode:
            raise SystemExit('Generic proposal patch check failed')
    actual = candidate.read_text()
    if actual != instrument_source(source.decode()):
        raise SystemExit('Applied bytes differ from the regression-tested proposal')
    compile(actual, str(candidate), 'exec')
result = {'schema': 'prepare-reporter-patch-verification-v1',
          'source_sha256': hashlib.sha256(source).hexdigest(),
          'patch_sha256': hashlib.sha256(patch.read_bytes()).hexdigest(),
          'patched_source_sha256': hashlib.sha256(actual.encode()).hexdigest(),
          'patch_applies_and_matches_tested_proposal': True,
          'shared_files_modified': False, 'commands': commands}
args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps(result, sort_keys=True))
