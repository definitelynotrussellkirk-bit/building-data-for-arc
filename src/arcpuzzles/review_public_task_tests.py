"""Reviewer-only tests for assigned public homes without catalog registration."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import stat
from pathlib import Path
import sys
import tempfile

from .review_public_creation import PUBLIC_WORK_SCHEMA, SOURCE, SOLUTIONS, generator_id
from .review_targets import assignment_targets, validate_work_policy


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _regular(root, path):
    if (not path.is_file() or not path.resolve().is_relative_to(root)
            or any(p.is_symlink() for p in (path, *path.parents) if p.is_relative_to(root))):
        raise ValueError('Task-test source must be a regular same-checkout file: ' + str(path))
    return path


def assigned_home(packet, tid):
    from .review_full_draw import repair_selection_for_seed
    from .review_full_packet import canonical_json
    packet = Path(packet).resolve(); root = packet/'repo'
    manifest = json.loads(_regular(packet, packet/'PACKET-MANIFEST.json').read_bytes())
    contract = json.loads(_regular(packet, packet/'ASSIGNMENT.json').read_bytes())
    validate_work_policy(contract, manifest)
    if (contract.get('work_policy', {}).get('schema') != PUBLIC_WORK_SCHEMA
            or contract.get('packet_id') != _sha(canonical_json(manifest))):
        raise ValueError('Task tests require the frozen public-creation assignment')
    rows = assignment_targets(contract)
    if rows != repair_selection_for_seed(manifest, bytes.fromhex(contract['seed'])):
        raise ValueError('Task-test assignment draw cannot be reproduced')
    selected = next((r for r in rows if r['task_id'] == tid), None)
    if selected is None:
        raise ValueError('Task tests require one assigned public task home')
    item = selected['generator']['public_creation']
    if tid != generator_id(item['public_task_id']):
        raise ValueError('Task-test public parent namespace differs')
    home = root/'generators'/tid
    parent = _regular(root, home/'workspace/public-parent.json')
    relative = parent.relative_to(packet).as_posix()
    if _sha(parent.read_bytes()) != manifest['files'].get(relative):
        raise ValueError('Immutable assigned public-parent.json changed')
    saved = json.loads(parent.read_bytes())
    if any(saved.get(k) != v for k, v in item.items()):
        raise ValueError('Assigned public parent differs from task home')
    return packet, root, home, manifest, contract


def run_tests(packet, tid, out, *, timeout=180, phase='after'):
    """Snapshot exact source and run one target; never create approval metadata."""
    from .runtime import run_process, _task_test_counts
    if not math.isfinite(timeout) or not 0 < timeout <= 1800:
        raise ValueError('Task-test timeout must be >0 and <=1800 seconds')
    packet, root, home, manifest, contract = assigned_home(packet, tid)
    out = Path(out).absolute()
    if out.exists() or out.resolve().is_relative_to(root) or root.is_relative_to(out.resolve()):
        raise ValueError('Use a new evidence directory outside repo, such as ../checks/TASK-tests')
    if any(p.is_symlink() for p in (out, *out.parents)):
        raise ValueError('Task-test evidence destination cannot contain symlinks')
    # Use library layout so task-private fixtures, adjacent helpers and runtime
    # imports keep their paths. No fabricated catalog rows or reference authority.
    sources = []
    for directory in (home, root/'shared/runtime', root/'src/arcpuzzles'):
        if not directory.is_dir():
            raise ValueError('Missing task-test source directory: ' + str(directory))
        for path in sorted(directory.rglob('*')):
            if any(part in {'__pycache__', '.pytest_cache', '.git'} for part in path.relative_to(directory).parts):
                continue
            if path.is_symlink():
                raise ValueError('Task-test source cannot contain symlinks: ' + str(path))
            if path.is_file():
                sources.append(path)
            elif not path.is_dir():
                raise ValueError('Task-test source contains a special file: ' + str(path))
    sources.append(root/'shared/tools/comment_solutions.py')
    sources.extend(root/name for name in (SOURCE, SOLUTIONS) if (root/name).exists())
    for path in sources:
        _regular(root, path)
    tests = [home/'tests'] if any((home/'tests').rglob('test*.py')) else []
    legacy = home/f'test_generator_{tid}.py'
    if legacy.is_file():
        tests.append(legacy)
    if not tests:
        raise ValueError('Assigned public home has no task-local tests')
    # Bind copied bytes before running, with immutable shared source checks.
    files = []; payloads = []
    for path in sorted(set(sources)):
        name = path.relative_to(root).as_posix(); raw = path.read_bytes(); sha = _sha(raw)
        if not path.is_relative_to(home) and manifest['files'].get('repo/'+name) != sha:
            raise ValueError('Shared packet source changed or is unbound: ' + name)
        files.append({'path': name, 'sha256': sha}); payloads.append((name, raw, stat.S_IMODE(path.stat().st_mode)))
    out.mkdir(parents=True)
    binding = {'task_id': tid, 'files': files}
    write = lambda name, value: (out/name).write_text(json.dumps(value, sort_keys=True, indent=2)+'\n')
    write('source-binding.json', binding)
    # The copied runtime is owned scratch, never part of returned delta evidence.
    with tempfile.TemporaryDirectory(prefix='arcpuzzles-public-task-runtime-') as temporary:
        stage = Path(temporary)
        for name, raw, mode in payloads:
            target = stage/name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw); target.chmod(mode)
        command = [sys.executable, '-m', 'pytest', '--import-mode=importlib',
                   *[p.relative_to(root).as_posix() for p in tests], '-q',
                   '--junitxml='+str(out/'task_tests.xml')]
        env = {'PYTHONPATH': os.pathsep.join(str(stage/p) for p in ('src', 'shared/runtime')),
               'ARCPUZZLES_HOME': str(stage), 'PYTHONDONTWRITEBYTECODE': '1',
               'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1', 'PYTEST_ADDOPTS': '', 'PYTEST_PLUGINS': ''}
        result = run_process(command, stage, timeout=timeout, extra_env=env)
        (out/'task-tests.log').write_text(result.pop('stdout') + result.pop('stderr'))
        drift = [r['path'] for r in files if (stage/r['path']).is_symlink() or not (stage/r['path']).is_file()
                 or _sha((stage/r['path']).read_bytes()) != r['sha256']]
        result.update(schema='arcpuzzles-public-task-tests-v1', task_id=tid, phase=phase,
                      stage='task_tests', timeout=timeout, source_binding=binding,
                      packet_id=contract['packet_id'], assignment_id=contract['assignment_id'],
                      test_counts=_task_test_counts(out/'task_tests.xml'), staged_source_drift=drift,
                      owner_accepted=False, verification_status='reviewer_task_tests_not_owner_qualification')
        result['status'] = 'passed' if result['exit_code'] == 0 and not result['timed_out'] and not drift else 'failed'
    result['staged_runtime_retained'] = False
    write('result.json', result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task_id')
    parser.add_argument('--packet', type=Path, default=Path('..'))
    parser.add_argument('--out', type=Path, required=True,
                        help='New evidence directory; review.py resolves this from WORK/repo. Use ../checks/TASK-tests for WORK/checks/TASK-tests')
    parser.add_argument('--phase', choices=['before', 'after', 'audit'], default='after')
    parser.add_argument('--timeout', type=float, default=180)
    parser.add_argument('--full-json', action='store_true', help='Print the full receipt; the default prints a compact summary')
    args = parser.parse_args(argv)
    result = run_tests(args.packet, args.task_id, args.out, timeout=args.timeout, phase=args.phase)
    summary = {key: result[key] for key in ('status', 'task_id', 'exit_code', 'timed_out', 'test_counts', 'verification_status')}
    summary.update(result_path=str((args.out/'result.json').resolve()), log_path=str((args.out/'task-tests.log').resolve()))
    print(json.dumps(result if args.full_json else summary, sort_keys=True, indent=2))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
