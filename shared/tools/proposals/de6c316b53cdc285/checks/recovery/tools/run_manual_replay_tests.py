#!/usr/bin/env python3
"""Run focused pytest against an authenticated manual replay, retaining provenance.

Invoke with the new replay venv's Python. This is not the official task_tests
stage: it reuses a separately supplied Racket installation as a toolchain.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay', type=Path, required=True)
    parser.add_argument('--racket', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    replay_root = args.replay.resolve(strict=True)
    replay = json.loads((replay_root / 'replay.json').read_text())
    work = Path(replay['work_root']).resolve(strict=True)
    if work != replay_root / 'checkout/WORK':
        raise ValueError('Unexpected replay root')
    if Path(sys.prefix).resolve() != replay_root / 'venv':
        raise ValueError('Use the independent replay venv')
    if replay['status'] != 'manual_patch_replay_passed_tests_pending':
        raise ValueError('An authenticated successful manual replay is required')
    expected = {item['path']: item['sha256'] for item in replay['changed_files']}
    before = {path: digest(work / path) for path in expected}
    if before != expected:
        raise ValueError('Fresh changed-file hashes differ before tests')
    repo = work / 'repo'
    racket = args.racket.resolve(strict=True)
    os.chdir(repo)
    os.environ.update(
        ARCPUZZLES_HOME=str(repo), RACKET_PATH=str(racket),
        PYTHONDONTWRITEBYTECODE='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
        PYTHONPATH=str(repo / 'src') + os.pathsep + str(repo / 'shared/runtime'),
        TMPDIR=str(replay_root / 'pip-tmp'),
    )
    sys.dont_write_bytecode = True
    sys.pycache_prefix = str(replay_root / 'never-created-pytest-cache')
    # Retain interpreter dependency paths, with fresh project source first.
    sys.path[:0] = [str(repo / 'src'), str(repo / 'shared/runtime')]
    import importlib.metadata
    import pytest

    captured = {}

    class ReceiptPlugin:
        def pytest_sessionfinish(self, session, exitstatus):
            captured.update(tests_collected=session.testscollected,
                            pytest_exit_status=int(exitstatus))

    pytest_argv = ['-q', '-p', 'no:cacheprovider', '--basetemp',
                   str(replay_root / 'pytest-tmp'),
                   'generators/' + replay['task_id'] + '/tests']
    exit_code = int(pytest.main(pytest_argv, plugins=[ReceiptPlugin()]))
    after = {path: digest(work / path) for path in expected}
    origins = {}
    for name, module in tuple(sys.modules.items()):
        value = getattr(module, '__file__', None)
        if value and (name == 'reviewer_support' or name.startswith((
                'arcpuzzles', 'arc_repl', 'puzzle_generators'))
                or '/generators/' + replay['task_id'] + '/' in str(value)):
            origins[name] = str(Path(value).resolve())
    external_origins = {name: path for name, path in origins.items()
                        if not Path(path).is_relative_to(repo)}
    ok = exit_code == 0 and after == expected and not external_origins
    receipt = {
        'schema': 'arcpuzzles-manual-fresh-focused-tests-v1',
        'status': 'passed' if ok else 'failed',
        'scope': 'Direct selected-task tests on freshly applied source only.',
        'official_runtime_closure': False,
        'official_task_test_stage_satisfied': False,
        'training_admitted': False,
        'argv': [sys.executable, *sys.argv],
        'pytest_argv': pytest_argv, 'cwd': str(repo),
        'python': sys.version, 'sys_executable': sys.executable,
        'sys_prefix': sys.prefix,
        'dependency_versions': {name: importlib.metadata.version(name) for name in
            ['pytest', 'pluggy', 'iniconfig', 'pygments', 'packaging']},
        'pytest_module': pytest.__file__,
        'racket_executable': str(racket), 'racket_sha256': digest(racket),
        'racket_toolchain_reused_from_reviewed_workspace': True,
        'project_source_origins': origins,
        'unexpected_external_project_origins': external_origins,
        'changed_file_sha256_before': before, 'changed_file_sha256_after': after,
        'patch_sha256': replay['patch_sha256'],
        'generator_sha256': replay['generator_sha256'],
        'exit_code': exit_code, **captured,
    }
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: receipt[k] for k in [
        'status', 'tests_collected', 'exit_code', 'official_task_test_stage_satisfied']}))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
