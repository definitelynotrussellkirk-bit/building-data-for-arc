"""Recreate a relocated, source-copied runtime and verify this review's additions.

The catalog maps inherited files only; explicitly copy this review's new tests
and probe before exercising them. Never delete or reuse an existing runtime.
Run through packet-root run_with_racket.py so the pinned Racket is available.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

TASK = 'ecd1f88fc6d3'
HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
sys.path.insert(0, str(REPO/'src'))
from arcpuzzles.catalog import Catalog
from arcpuzzles.runtime import prepare_runtime, run_process


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    runtime, out = args.runtime.resolve(), args.out.resolve()
    if runtime.exists() or out.exists():
        parser.error('--runtime and --out must both be new paths')
    manifest = prepare_runtime(Catalog(REPO), runtime, TASK)
    tests = runtime/'tests'/('review_'+TASK)
    shutil.copytree(HOME/'tests', tests, ignore=shutil.ignore_patterns('__pycache__'))
    probe = runtime/'puzzle_generators/per_puzzle'/TASK/'workspace/probe_distribution.py'
    probe.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(HOME/'workspace/probe_distribution.py', probe)
    out.mkdir(parents=True)
    command_specs = [
        ('pytest', [sys.executable, '-m', 'pytest', '-q', str(tests.relative_to(runtime))]),
        ('racket_probe', [sys.executable, str(probe.relative_to(runtime)),
                          '--out', str(out/'probe.json'), '--racket']),
    ]
    results = []
    for name, command in command_specs:
        result = run_process(command, runtime, timeout=120)
        (out/f'{name}.log').write_text(result['stdout'] + result['stderr'])
        results.append({'name': name, 'cwd': str(runtime), **result})
    generated = runtime/'puzzle_generators/per_puzzle'/TASK/'generator.py'
    report = {'schema': 'review-portable-verification-v1',
              'runtime_directory': str(runtime),
              'generator_sha256': hashlib.sha256(generated.read_bytes()).hexdigest(),
              'copied_generator_matches_source': generated.read_bytes() == (HOME/'generator.py').read_bytes(),
              'runtime_files': len(manifest['files']),
              'copied_new_tests_explicitly': True,
              'contains_symlinks': any(p.is_symlink() for p in runtime.rglob('*')),
              'results': results}
    (out/'result.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'results'}, indent=2))
    print('\n'.join(f"{r['name']}: exit={r['exit_code']} timed_out={r['timed_out']}" for r in results))
    return 0 if report['copied_generator_matches_source'] and not report['contains_symlinks'] and all(
        r['exit_code'] == 0 and not r['timed_out'] for r in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
