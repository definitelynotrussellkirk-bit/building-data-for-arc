#!/usr/bin/env python3
"""Replay an exact review ZIP, then test its fresh checkout inside private TMPDIR.

Run through run_with_private_tmpfs.py. Retained output must be a new directory
outside TMPDIR. The official replay receipt is copied byte-for-byte and remains
separate from this driver's subsequent test evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def run_command(argv, *, cwd, env, out, name, timeout=None):
    """Retain full logs, including failed/timed-out subprocesses."""
    record = {'argv': argv, 'cwd': str(cwd), 'timeout_seconds': timeout,
              'stdout': str(out / f'{name}.stdout.log'),
              'stderr': str(out / f'{name}.stderr.log')}
    started = time.monotonic()
    with Path(record['stdout']).open('xb') as stdout, Path(record['stderr']).open('xb') as stderr:
        process = subprocess.Popen(argv, cwd=cwd, env=env, stdout=stdout,
                                   stderr=stderr, start_new_session=True)
        try:
            record['exit_code'] = process.wait(timeout=timeout)
            record['status'] = 'passed' if record['exit_code'] == 0 else 'failed'
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            record.update(status='timed_out', exit_code=process.returncode)
        except BaseException:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            raise
    record['elapsed_seconds'] = round(time.monotonic() - started, 3)
    return record


def junit_counts(path):
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == 'testsuite' else root.findall('testsuite')
    if not suites:
        raise ValueError('JUnit output contains no test suite')
    return {key: sum(int(suite.get(key, '0')) for suite in suites)
            for key in ('tests', 'failures', 'errors', 'skipped')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-zip', type=Path, required=True)
    parser.add_argument('--return-zip', type=Path, required=True)
    parser.add_argument('--compare-work', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--test-timeout', type=int, default=600)
    args = parser.parse_args()
    if args.test_timeout <= 0:
        parser.error('--test-timeout must be positive')
    tmp_text = os.environ.get('TMPDIR')
    if not tmp_text or not Path(tmp_text).is_absolute() or not Path(tmp_text).is_dir():
        parser.error('run through run_with_private_tmpfs.py with an existing absolute TMPDIR')
    tmpdir = Path(tmp_text).resolve()
    if args.out.exists() or args.out.is_symlink():
        parser.error('--out must be a new directory; overwrites are forbidden')
    out = args.out.resolve()
    if out == tmpdir or tmpdir in out.parents:
        parser.error('--out must be persistent and outside TMPDIR')
    if out.exists():
        parser.error('--out must be a new directory; overwrites are forbidden')
    owner = args.compare_work.resolve(strict=True)
    source_zip = args.source_zip.resolve(strict=True)
    return_zip = args.return_zip.resolve(strict=True)
    if not source_zip.is_file() or not return_zip.is_file() or not (owner / 'repo/src').is_dir():
        parser.error('expected source/return ZIP files and compare-work/repo/src')
    assignment = json.loads((owner / 'ASSIGNMENT.json').read_text())
    task = assignment['task_id']
    if not isinstance(task, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', task):
        parser.error('invalid task_id in ASSIGNMENT.json')
    out.mkdir(parents=True, exist_ok=False)
    receipt_path = out / 'driver-receipt.json'
    receipt = {'schema': 'arcpuzzles-replay-and-test-driver-v1', 'status': 'running',
               'task_id': task, 'interpreter': sys.executable,
               'source_zip': str(source_zip), 'source_zip_sha256': sha256(source_zip),
               'return_zip': str(return_zip), 'return_zip_sha256': sha256(return_zip),
               'compare_work': str(owner), 'checkout_retention': 'temporary_under_TMPDIR',
               'official_receipt_modified': False, 'training_admitted': False}

    def save():
        receipt_path.write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')

    save()
    try:
        with tempfile.TemporaryDirectory(prefix='return-replay-', dir=tmpdir) as private:
            private = Path(private)
            replay_out = private / 'new-replay'
            replay_cache = private / 'official-pycache'
            test_cache = private / 'fresh-test-pycache'
            replay_cache.mkdir()
            test_cache.mkdir()
            environment = os.environ.copy()
            environment.pop('ARCPUZZLES_HOME', None)
            environment.update(PYTHONPATH=str(owner / 'repo/src'), PYTHONNOUSERSITE='1',
                               PYTHONDONTWRITEBYTECODE='1')
            replay_argv = [sys.executable, '-B', '-X', f'pycache_prefix={replay_cache}',
                           '-m', 'arcpuzzles', 'review', 'replay-return', '--runtime-closure',
                           '--source-zip', str(source_zip), '--return-zip', str(return_zip),
                           '--compare-work', str(owner), '--out', str(replay_out)]
            receipt['replay_environment'] = {
                key: environment[key] for key in ('PYTHONPATH', 'PYTHONNOUSERSITE', 'PYTHONDONTWRITEBYTECODE')}
            receipt['replay'] = run_command(replay_argv, cwd=owner / 'repo', env=environment,
                                            out=out, name='replay')
            official = None
            for name in ('replay.json', 'extraction-manifest.json.gz'):
                original = replay_out / name
                if original.is_file():
                    shutil.copyfile(original, out / name)
                    receipt.setdefault('retained_official_files', {})[name] = sha256(out / name)
            if (out / 'replay.json').is_file():
                official = json.loads((out / 'replay.json').read_text())
                receipt['official_replay_status'] = official.get('status')
            save()
            if receipt['replay']['exit_code'] != 0:
                raise RuntimeError('official replay failed; see retained logs and any original receipt')
            if not (out / 'extraction-manifest.json.gz').is_file():
                raise RuntimeError('official replay extraction inventory was not retained')
            if official is None or official.get('status') != 'patch_replay_passed_tests_pending':
                raise RuntimeError('official replay did not report patch replay success')
            if official.get('task_id') != task:
                raise RuntimeError('official replay task differs from ASSIGNMENT.json')
            fresh_work = Path(official['work_root']).resolve(strict=True)
            if not fresh_work.is_relative_to(replay_out.resolve()):
                raise RuntimeError('official fresh checkout is outside private replay output')
            fresh_repo = fresh_work / 'repo'
            receipt['official_source_binding'] = {
                key: official[key] for key in ('generator_sha256', 'changed_files', 'patch_sha256')}
            environment.update(PYTHONPATH=os.pathsep.join([str(fresh_repo / 'shared/runtime'),
                                                          str(fresh_repo / 'src')]),
                               ARCPUZZLES_TEST_SRC=str(fresh_repo / 'src'),
                               PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
            environment.pop('PYTEST_ADDOPTS', None)
            environment.pop('PYTEST_PLUGINS', None)
            tests_argv = [sys.executable, '-B', '-X', f'pycache_prefix={test_cache}',
                          '-m', 'pytest', '-q', f'generators/{task}/tests',
                          f'generators/{task}/workspace/review_tools/test_zip_readonly_overlay.py',
                          '--import-mode=importlib', f'--junitxml={out / "fresh-tests.xml"}']
            receipt['test_environment'] = {key: environment[key] for key in
                ('PYTHONPATH', 'PYTHONNOUSERSITE', 'PYTHONDONTWRITEBYTECODE',
                 'ARCPUZZLES_TEST_SRC', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD')}
            receipt['tests'] = run_command(tests_argv, cwd=fresh_repo, env=environment,
                                           out=out, name='fresh-tests', timeout=args.test_timeout)
            if (out / 'fresh-tests.xml').is_file():
                receipt['test_counts'] = junit_counts(out / 'fresh-tests.xml')
            receipt['fresh_generator_sha256_after_tests'] = sha256(
                fresh_repo / f'generators/{task}/generator.py')
            receipt['fresh_changed_files_sha256_after_tests'] = {
                row['path']: sha256(fresh_work / row['path']) for row in official['changed_files']}
            receipt['source_identity_matches_after_tests'] = (
                receipt['fresh_generator_sha256_after_tests'] == official['generator_sha256']
                and all(receipt['fresh_changed_files_sha256_after_tests'][row['path']] == row['sha256']
                        for row in official['changed_files']))
            save()
            counts = receipt.get('test_counts', {})
            if (receipt['tests']['status'] != 'passed' or not counts.get('tests')
                    or counts.get('failures') or counts.get('errors')):
                raise RuntimeError('fresh focused tests did not pass; see retained logs and JUnit output')
            if not receipt['source_identity_matches_after_tests']:
                raise RuntimeError('fresh source changed during testing')
            receipt['status'] = 'replay_and_fresh_tests_passed'
            save()
    except BaseException as exc:
        receipt.update(status='failed', error=f'{type(exc).__name__}: {exc}')
        save()
        raise
    print(json.dumps({'status': receipt['status'], 'receipt': str(receipt_path),
                      'test_counts': receipt['test_counts']}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
