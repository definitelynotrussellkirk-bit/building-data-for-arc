"""Capture one bounded test run in the copied proposal workspace."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
WORKSPACE = Path('/workspace/scratch/df8d9659f825/process-liveness-work')
SOURCE = Path('/workspace/scratch/df8d9659f825/review/WORK/repo')
label = sys.argv[1]
if label not in {'before', 'after', 'final'}:
    raise SystemExit('label must be before, after, or final')
argv = [str(WORKSPACE / '.venv/bin/python'), '-B', '-m', 'pytest', '-q',
        'tests/test_check_jobs.py', 'tests/test_check_resume.py',
        'tests/test_check_jobs_liveness.py', '--junitxml=' + str(HERE / f'{label}.xml')]
env = os.environ.copy()
env.update(PYTHONPATH=str(WORKSPACE / 'src'), PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1',
           PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
env.pop('PYTHONHOME', None)


def hashes():
    paths = {
        'copied_check_jobs': WORKSPACE / 'src/arcpuzzles/check_jobs.py',
        'regressions': WORKSPACE / 'tests/test_check_jobs_liveness.py',
        'main_check_jobs': SOURCE / 'src/arcpuzzles/check_jobs.py',
        'main_selected_generator': SOURCE / 'generators/48bda9528e71/generator.py',
    }
    return {key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in paths.items()}


receipt = {'started_at': datetime.now(timezone.utc).isoformat(), 'argv': argv,
           'cwd': str(WORKSPACE), 'timeout_seconds': 120,
           'environment_overrides': {key: env[key] for key in
               ('PYTHONPATH', 'PYTHONNOUSERSITE', 'PYTHONDONTWRITEBYTECODE', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD')},
           'source_sha256_before': hashes(), 'evidence_paths': [f'{label}.log', f'{label}.xml']}
started = time.monotonic()
with (HERE / f'{label}.log').open('w') as log:
    try:
        result = subprocess.run(argv, cwd=WORKSPACE, env=env, stdout=log,
                                stderr=subprocess.STDOUT, timeout=120)
        receipt.update(exit_code=result.returncode, timed_out=False)
    except subprocess.TimeoutExpired:
        receipt.update(exit_code=None, timed_out=True)
receipt.update(elapsed_seconds=round(time.monotonic()-started, 3), source_sha256_after=hashes())
(HERE / f'{label}-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
