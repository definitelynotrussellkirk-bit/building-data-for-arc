#!/usr/bin/env python3
"""Stage the selected task in an independent runtime and run its review checks.

From packet_root: python3 run_with_racket.py python3 \
  generators/d9d4f0ebb48b/workspace/review_checks.py test --out ../checks/task-tests

No edits to catalog mappings are needed for new task-local tests. The source
identity, exact temporary runtime cwd, invocation, stdout and return code are
retained; the large copied runtime is removed afterward.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

TASK_ID = 'd9d4f0ebb48b'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('test', 'palette'))
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--samples', type=int, default=32, help='seeds per band, each with four profiles')
    parser.add_argument('--phase', default='final')
    parser.add_argument('--generator-file', type=Path, help='explicit immutable comparison source; copied only into the disposable runtime')
    args = parser.parse_args()
    if args.samples < 1:
        parser.error('--samples must be positive')
    repo = Path(__file__).resolve().parents[3]
    home = repo / 'generators' / TASK_ID
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(repo / 'src'))
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import prepare_runtime

    with tempfile.TemporaryDirectory(prefix='arcpuzzles-palette-') as temporary:
        runtime = Path(temporary)
        prepare_runtime(Catalog(repo), runtime, task_id=TASK_ID)
        staged_generator = runtime / 'puzzle_generators' / 'per_puzzle' / TASK_ID / 'generator.py'
        if args.generator_file is not None:
            shutil.copy2(args.generator_file.resolve(), staged_generator)
        # Bind to bytes that will actually execute, not the mutable source
        # tree after the child finishes. Parallel review edits can race it.
        generator_hash = hashlib.sha256(staged_generator.read_bytes()).hexdigest()
        # Runtime mappings are immutable packet-wide scope. Explicitly stage
        # new local test files too rather than silently testing only old ones.
        for path in sorted((home / 'tests').glob('test_*.py')):
            shutil.copy2(path, runtime / 'tests' / path.name)
        if args.mode == 'test':
            command = [sys.executable, '-m', 'pytest', '-q',
                       *['tests/' + p.name for p in sorted((home / 'tests').glob('test_*.py'))]]
        else:
            shutil.copy2(home / 'workspace' / 'palette_probe.py', runtime / 'palette_probe.py')
            command = [sys.executable, 'palette_probe.py', '--samples', str(args.samples),
                       '--phase', args.phase, '--out', str(out / 'palette.json')]
        env = dict(os.environ)
        env.pop('PYTHONPATH', None)
        env['PYTHONNOUSERSITE'] = '1'
        env['TERM'] = 'dumb'
        env['NO_COLOR'] = '1'
        with (out / 'run.log').open('w') as log:
            result = subprocess.run(command, cwd=runtime, env=env, stdout=log,
                                    stderr=subprocess.STDOUT, timeout=600, check=False)
        receipt = {
            'task_id': TASK_ID, 'phase': args.phase, 'mode': args.mode,
            'generator_sha256': generator_hash,
            'generator_source': str(args.generator_file) if args.generator_file else 'selected task',
            'runtime_cwd': str(runtime), 'runtime_removed_after_run': True,
            'command': command, 'exit_code': result.returncode,
            'test_files': [p.name for p in sorted((home / 'tests').glob('test_*.py'))],
        }
        (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print((out / 'run.log').read_text())
        print(json.dumps(receipt, indent=2))
        return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
