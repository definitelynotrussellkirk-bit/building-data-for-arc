"""Relocate the task, deny source-tree reads, then run task tests and Racket census.

Run from the source repo through run_with_racket.py. The runtime and pinned
Racket installation are copied, never symlinked. Landlock is the default.
An explicit --isolation python-audit tests Python source-read/import isolation
when Landlock is unavailable; it is NOT an OS-level subprocess sandbox.
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

TASK = 'dc91f4798e24'
HOME = Path(__file__).resolve().parents[1]
ROOT = next(p for p in HOME.parents if (p / 'catalog/runtime_files.json').is_file())
sys.path.insert(0, str(ROOT / 'src'))
from arcpuzzles import Catalog
from arcpuzzles.runtime import prepare_runtime


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--isolation', choices=['landlock', 'python-audit'], default='landlock')
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = {'task_id': TASK, 'generator_sha256': sha(HOME / 'generator.py'),
              'parent_cwd': str(Path.cwd()), 'steps': [], 'failures': [],
              'isolation_mode': args.isolation, 'os_sandbox_verified': False}
    try:
        with tempfile.TemporaryDirectory(prefix='arcpuzzles-relocated-proof-') as directory:
            stage = Path(directory)
            report['actual_runtime_directory'] = str(stage)
            prepare_runtime(Catalog(ROOT), stage, TASK)
            task = stage / 'puzzle_generators/per_puzzle' / TASK
            for name in ['tests', 'workspace']:
                shutil.copytree(HOME / name, task / name, dirs_exist_ok=True,
                                ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))
            guard = stage / 'deny_predecessor_reads.py'
            shutil.copy2(ROOT / 'tools/deny_predecessor_reads.py', guard)
            racket = Path(os.environ['RACKET_PATH']).resolve()
            shutil.copytree(racket.parent.parent, stage / 'verified-racket')
            child_env = os.environ.copy()
            for key in ('PYTHONPATH', 'PYTHONHOME'):
                child_env.pop(key, None)
            child_env['PYTHONNOUSERSITE'] = '1'
            child_env['RACKET_PATH'] = str(stage / 'verified-racket/bin/racket')
            child_env['PATH'] = str(stage / 'verified-racket/bin') + os.pathsep + child_env.get('PATH', '')
            source = str(HOME / 'generator.py')
            python_guard = (
                "import os,sys\n"
                "original_root=" + repr(str(ROOT)) + "\n"
                "assert all(not os.path.abspath(p or os.curdir).startswith(original_root + os.sep) "
                "and os.path.abspath(p or os.curdir) != original_root for p in sys.path)\n"
                "def deny_original(event, args):\n"
                " if event in ('open','os.listdir','os.scandir') and args "
                "and isinstance(args[0],(str,bytes,os.PathLike)):\n"
                "  target=os.path.abspath(os.fsdecode(args[0]))\n"
                "  if target == original_root or target.startswith(original_root + os.sep):\n"
                "   raise PermissionError('Original source tree read denied: ' + target)\n"
                "sys.addaudithook(deny_original)\n"
                "print('PYTHON_AUDIT_ONLY: subprocess filesystem is not sandboxed',flush=True)\n")
            # Check the actual source path, not merely a generic sibling path.
            denial = ("from pathlib import Path\n"
                      "try:\n Path(" + repr(source) + ").read_bytes()\n"
                      "except PermissionError:\n print('SOURCE_READ_DENIED', flush=True)\n"
                      "else:\n raise AssertionError('original source still readable')\n")
            relative = 'puzzle_generators/per_puzzle/' + TASK
            programs = [
                ('tests', denial + "import pytest\nraise SystemExit(pytest.main(['-q', "
                 + repr(relative + '/tests/test_component_curriculum.py') + "]))\n"),
                ('census', denial + "import runpy,sys\nsys.argv=" + repr([
                    relative + '/workspace/review_probe.py', 'census', '--phase', 'portable',
                    '--per-band', '25', '--out', str(stage / 'portable-census.json')])
                 + "\nrunpy.run_path(sys.argv[0], run_name='__main__')\n")]
            for name, code in programs:
                command = ([sys.executable, str(guard), sys.executable, '-c', code]
                           if args.isolation == 'landlock' else
                           [sys.executable, '-c', python_guard + code])
                result = subprocess.run(command, cwd=stage, env=child_env,
                                        capture_output=True, text=True, timeout=180)
                (out / (name + '.stdout')).write_text(result.stdout)
                (out / (name + '.stderr')).write_text(result.stderr)
                report['steps'].append({'name': name, 'argv': command, 'cwd': str(stage),
                                        'exit_code': result.returncode,
                                        'source_denial_confirmed': 'SOURCE_READ_DENIED' in result.stdout})
                if result.returncode or 'SOURCE_READ_DENIED' not in result.stdout:
                    report['failures'].append(name)
            for name in ['RUNTIME_MANIFEST.json', 'portable-census.json', 'portable-census.rows.jsonl']:
                if (stage / name).exists():
                    shutil.copy2(stage / name, out / name)
            report['runtime_manifest_sha256'] = sha(stage / 'RUNTIME_MANIFEST.json')
            report['os_sandbox_verified'] = args.isolation == 'landlock' and not report['failures']
    except Exception as exc:
        report['failures'].append({'exception': type(exc).__name__, 'message': str(exc)})
    (out / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return int(bool(report['failures']))


if __name__ == '__main__':
    raise SystemExit(main())
