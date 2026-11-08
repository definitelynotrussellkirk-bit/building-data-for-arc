"""Run this task's tests from a fresh public runtime snapshot, without pytest."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time

from arcpuzzles import Catalog
from arcpuzzles.runtime import prepare_runtime, _task_test_snapshot, _task_test_import_diagnostics
from reviewer_support import find_root

TASK = 'cbf77aa253ac'
repository = find_root(__file__)
evidence = Path(__file__).resolve().parent / 'relocated-final'
evidence.mkdir()
started = time.monotonic()
with tempfile.TemporaryDirectory(prefix='cbf77-final-relocated-') as temporary:
    runtime = Path(temporary)
    catalog = Catalog(repository)
    manifest = prepare_runtime(catalog, runtime, TASK)
    selected = _task_test_snapshot(catalog, runtime, manifest, TASK)
    diagnostics = _task_test_import_diagnostics(runtime, selected)
    command = [sys.executable, '-m', 'unittest', 'discover', '-s',
               f'generators/{TASK}/tests', '-p', 'test_*.py', '-v']
    env = os.environ.copy()
    env.pop('PYTHONPATH', None)
    env.pop('PYTHONHOME', None)
    env['PYTHONNOUSERSITE'] = '1'
    env['ARCPUZZLES_HOME'] = str(runtime)
    result = subprocess.run(command, cwd=runtime, env=env, capture_output=True, text=True, timeout=120)
    output = result.stdout + result.stderr
    (evidence / 'output.txt').write_text(output)
    ran = re.search(r'Ran (\d+) tests? in', output)
    counts = {'tests': int(ran.group(1)) if ran else 0, 'failures': 0, 'errors': 0, 'skipped': 0}
    trailer = re.search(r'FAILED \(([^)]*)\)', output)
    if trailer:
        counts.update({k: int(v) for k, v in re.findall(r'(failures|errors|skipped)=(\d+)', trailer.group(1))})
    counts['passed'] = counts['tests'] - counts['failures'] - counts['errors'] - counts['skipped']
    receipt = {'command': command, 'cwd': str(runtime), 'exit_code': result.returncode,
               'seconds': time.monotonic() - started, 'counts': counts,
               'import_diagnostics': diagnostics, 'pythonpath': None,
               'python_no_user_site': True, 'arcpuzzles_home': str(runtime),
               'source_bindings': [row for row in manifest['files']
                                   if row['library_path'].startswith(f'generators/{TASK}/')],
               'log_sha256': hashlib.sha256(output.encode()).hexdigest(),
               'scope': 'selected task unittest suite in a relocated public runtime; not the pytest aggregate stage'}
    (evidence / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: receipt[k] for k in ('exit_code', 'seconds', 'counts', 'import_diagnostics')}))
    print(output)
    raise SystemExit(result.returncode)
