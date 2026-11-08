#!/usr/bin/env python3
"""Verify this task from a relocated, independently copied runtime.

Use --repo-root on the library, set RACKET_PATH to an installed Racket, and
retain --out. New task-local tests/workspace files are copied explicitly because
the repository's frozen runtime mapping predates this review's new files.
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
import time

TASK = '664a918eb273'


def probe_passed(report: dict | None) -> bool:
    """Require the complete 600/90 semantic probe, not merely exit code zero.

    path_probe is a census tool: it intentionally exits zero even when its
    report contains old-generator defects. This acceptance adapter fails closed.
    The task's first canonical record contains five labeled pairs.
    """
    if not isinstance(report, dict):
        return False
    counts, racket = report.get('counts'), report.get('racket')
    if not isinstance(counts, dict) or not isinstance(racket, dict):
        return False
    return (report.get('samples_requested') == 600
            and report.get('samples_generated') == 600
            and report.get('generation_errors') == []
            and counts.get('invalid_geometry') == 0
            and counts.get('selfcheck_rejects') == 0
            and racket.get('checked') == 90
            and racket.get('pixel_loss') == 0
            and racket.get('geometric_mismatches') == 0
            and racket.get('errors') == []
            and racket.get('canonical_matches') == 5)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo-root', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    root, out = args.repo_root.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(root / 'src'))
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import prepare_runtime
    records = []
    with tempfile.TemporaryDirectory(prefix='arcpuzzles-path-portable-') as temporary:
        temp = Path(temporary)
        staged = temp / 'staging'
        manifest = prepare_runtime(Catalog(root), staged, TASK)
        task_dir = Path('puzzle_generators/per_puzzle') / TASK
        for name in ('tests', 'workspace'):
            shutil.copytree(root / 'generators' / TASK / name, staged / task_dir / name,
                            dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        runtime = temp / 'relocated'
        staged.rename(runtime)
        env = dict(os.environ)
        env.pop('PYTHONHOME', None)
        env['PYTHONPATH'] = str(runtime)
        env['PYTHONNOUSERSITE'] = '1'
        commands = [
            [sys.executable, '-E', '-s', '-m', 'pytest', '-q', str(task_dir / 'tests/test_path_contract.py')],
            [sys.executable, '-E', '-s', str(task_dir / 'workspace/path_probe.py'),
             '--repo-root', '.', '--generator', str(task_dir / 'generator.py'),
             '--samples', '600', '--racket-samples', '90', '--out', 'portable-probe.json'],
        ]
        for index, argv in enumerate(commands):
            start = time.monotonic()
            try:
                completed = subprocess.run(argv, cwd=runtime, env=env, capture_output=True,
                                           text=True, timeout=120)
                code, stdout, stderr, timed_out = completed.returncode, completed.stdout, completed.stderr, False
            except subprocess.TimeoutExpired as exc:
                code, stdout, stderr, timed_out = None, str(exc.stdout or ''), str(exc.stderr or ''), True
            (out / f'command-{index}.stdout.log').write_text(stdout)
            (out / f'command-{index}.stderr.log').write_text(stderr)
            records.append({'cwd':str(runtime), 'argv':argv, 'exit_code':code, 'timed_out':timed_out,
                            'seconds':round(time.monotonic()-start,3),
                            'stdout':f'command-{index}.stdout.log','stderr':f'command-{index}.stderr.log'})
        probe_report, probe_error = None, None
        if (runtime / 'portable-probe.json').exists():
            shutil.copy2(runtime / 'portable-probe.json', out / 'portable-probe.json')
            try:
                probe_report = json.loads((out / 'portable-probe.json').read_text())
            except (OSError, ValueError) as exc:
                probe_error = str(exc)
        semantic_passed = probe_passed(probe_report)
        summary = {'schema':'path-portability-check-v1', 'runtime_directory':str(runtime),
                   'relocated_before_execution':True, 'child_pythonpath':str(runtime),
                   'racket_path':env.get('RACKET_PATH'),
                   'generator_sha256':hashlib.sha256((runtime/task_dir/'generator.py').read_bytes()).hexdigest(),
                   'copied_manifest_files':len(manifest['files']), 'commands':records,
                   'semantic_probe_passed':semantic_passed, 'probe_report_error':probe_error,
                   'passed':semantic_passed and all(r['exit_code']==0 and not r['timed_out'] for r in records),
                   'isolation_scope':'Copied runtime; clean child import path, -E/-s. No OS filesystem-deny claim.'}
        (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        print(json.dumps(summary,indent=2))
    return 0 if summary['passed'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
